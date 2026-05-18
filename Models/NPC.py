from __future__ import annotations
from typing import TYPE_CHECKING
from Models.Enums import CharacterRole, EventRole, Polarity, EventType, BeliefType
from dataclasses import dataclass
from Models.Event import Event
from Models.Edge import Edge
from GameClock import get_gametime_obj
from Models.World import World
from utilities import load_prompt, parse_prompt, DEFAULT_PROMPT_PATH
from LLMClient import LLM
import json
from Models.Action import Action

if TYPE_CHECKING:
    from BeliefGraph import BeliefGraph, BeliefGraphNode

@dataclass
class Personality:
    bravery: float
    trust: float
    aggression: float
    cleverness: float

    def to_str(self, for_prompt: bool = False) -> str:
        if for_prompt:
            return f"bravery={self.bravery} trust={self.trust} aggression={self.aggression} cleverness={self.cleverness}"
        return (
            f"  Bravery:    {self.bravery}\n"
            f"  Trust:      {self.trust}\n"
            f"  Aggression: {self.aggression}\n"
            f"  Cleverness: {self.cleverness}"
        )

    def __str__(self):
        return self.to_str(for_prompt=False)
        

@dataclass
class Goal:
    description: str
    priority: float
    is_complete: bool

    def to_str(self, for_prompt: bool = False) -> str:
        if for_prompt:
            status = "done" if self.is_complete else "active"
            return f"[priority={self.priority} {status}] {self.description}"
        return (
            f"  Description: {self.description}\n"
            f"  Priority:    {self.priority}\n"
            f"  Complete:    {self.is_complete}"
        )

    def __str__(self):
        return self.to_str(for_prompt=False)
        
    

class NPC:
    
    def __init__(self, name: str, role: CharacterRole, llmReason: LLM, location: tuple[float, float],
                 beliefGraph: BeliefGraph, personality: Personality, goals: list[Goal],
                 prompt_path: str = None, prompt_content: str = None):
        self.name = name
        self.role = role
        self.personality = personality
        self.goals = goals
        self.location = location
        self.beliefGraph = beliefGraph
        self.llmReason = llmReason
        self.prompt_path = prompt_path or DEFAULT_PROMPT_PATH
        # prompt_content (raw YAML string) takes precedence over prompt_path when set
        self.prompt_content: str | None = prompt_content
        self.last_action: Action = None

        self.clock = get_gametime_obj()
    
    
    def percive(self, event: Event):
        if self in event.whoInvolved:
            actor_npc = None
            target_npc = None
            for k, v in event.whoInvolved.items():
                if v is EventRole.ACTOR:
                    actor_npc = k
                elif v is EventRole.TARGET:
                    target_npc = k

            role_type = event.whoInvolved[self]
            hop_count = 0 if role_type in (EventRole.ACTOR, EventRole.TARGET) else 1

            # For ATTRIBUTE beliefs (IS_THIEF, IS_GOOD, etc.) the belief is *about*
            # the target — subject is the target, object is null.
            # For RELATIONAL beliefs the subject is the actor and object is the target.
            if event.event_type.get_belief_type() == BeliefType.ATTRIBUTE:
                subject_npc = target_npc
                object_npc = None
            else:
                subject_npc = actor_npc
                object_npc = target_npc

            edge = Edge(subject_npc=subject_npc, object_npc=object_npc, relation_type=event.event_type,
                        event_timestamp=event.timestamp, belief_timestamp=self.clock.time, hop_count=hop_count,
                        conformations=0, source_credibility=1, is_direct=True)

            self.beliefGraph.add_or_confirm(self, None, edge=edge)
    
    def propogate(self, world):
        # get nearby NPCs from world
        nearby_npcs = world.get_nearby_npc(self, radius=10)
        # filter own beliefs worth sharing:
        belifes = self.beliefGraph.get_beliefs(self)
        if not belifes:
            return
        belifes_to_share: list[BeliefGraphNode] = []
        for belife in belifes:
            if self.personality.aggression > 0.6:
                if belife.edge.polarity == Polarity.NEGATIVE and belife.edge.strength >= 0.3:
                    belifes_to_share.append(belife)
                elif belife.edge.strength >= 0.8:
                    belifes_to_share.append(belife)
            else:
                if belife.edge.strength >= 0.5:
                    belifes_to_share.append(belife)
        
        for npc in nearby_npcs:
            for belief in belifes_to_share:
                edge = belief.edge
                new_edge = Edge(
                    subject_npc=edge.subject_npc,
                    object_npc=edge.object_npc,
                    relation_type=edge.relation_type,
                    event_timestamp=edge.event_timestamp,
                    belief_timestamp=self.clock.time,
                    hop_count=edge.hop_count + 1,
                    conformations=edge.confirmations,
                    source_credibility=edge.source_credibility,
                    is_direct=False,
                )
                self.beliefGraph.add_or_confirm(npc, self, edge=new_edge)
    
    def decide(self, world: World) -> dict | None:
        from Models.Action import Action
        subs = {}
        
        subs["current_time"]=str(self.clock.time)
        subs["location"] = str(self.location)
        subs["recent_events"] = "\n".join(         
            str(e) for e in world.get_recent_events(self, limit=5)
        )
        subs["name"] = self.name
        subs["role"] = f"{self.role.name} — {self.role.get_description()}"
        subs["goals"] = "\n".join(g.to_str(for_prompt=True) for g in self.goals)
        subs["beliefs"] = "\n".join(b.edge.to_str(for_prompt=True) for b in self.beliefGraph.get_beliefs(self) or [])
        subs["nearby_npcs"] = "\n".join(n.to_str(for_prompt=True) for n in world.get_nearby_npc(self, 10))
        subs["personality"] = self.personality.to_str(for_prompt=True)
        relational = [m.name for m in EventType if m.get_belief_type() == BeliefType.RELATIONAL]
        attribute  = [m.name for m in EventType if m.get_belief_type() == BeliefType.ATTRIBUTE]
        subs["action_types"] = (
            f"RELATIONAL (requires target_npc): {', '.join(relational)}\n"
            f"  ATTRIBUTE (target_npc must be the entity being characterized): {', '.join(attribute)}"
        )
        subs["schema"] = json.dumps(Action.generate_schema_instructinos(), indent=2)
        subs["last_action"] = self.last_action.to_str(for_prompt=True) if self.last_action else "None"
        
        if self.prompt_content:
            prompt = parse_prompt(self.prompt_content, subs)
        else:
            prompt = load_prompt(self.prompt_path, subs)

        res = self.llmReason.run(prompt)
        
        return res
    
    
    def to_str(self, for_prompt: bool = False) -> str:
        if for_prompt:
            return f"{self.name} ({self.role.name}) @ {self.location}"
        return (
            f"  Name:     {self.name}\n"
            f"  Role:     {self.role.name}\n"
            f"  Location: {self.location}"
        )

    def __str__(self):
        return self.to_str(for_prompt=False)
    
    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, NPC) and self.name == other.name
            