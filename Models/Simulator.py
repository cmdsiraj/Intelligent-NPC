from Models.World import World
from BeliefGraph import BeliefGraph, BeliefGraphNode
from GameClock import get_gametime_obj
from Models.Event import Event
from Models.NPC import NPC
from Models.Action import Action
from Models.Edge import Edge
from Models.Enums import EventRole, EventType
from datetime import datetime
import json
import os

class Simulator:
    
    def __init__(self, world: World, belief_graph: BeliefGraph):
        self.world = world
        self.belief_graph = belief_graph
        
        self.clock = get_gametime_obj()
        self.pending_events: list[Event] = list()
        
    def run(self, ticks: int) -> None:
        for tick in range(1, ticks + 1):
            print(f"\n{'='*60}")
            print(f"  TICK {tick}")
            print(f"{'='*60}")
            self._process_events()
            self._propogate_all()
            self._decide_all(tick)
            self.clock.tick()
        self._print_belief_summary()
    
    def queue_event(self, event: Event) -> None:
        self.pending_events.append(event)
    
    def _process_events(self) -> None:
        for event in self.pending_events:
            self._enrich_with_witness(event=event)
            self.world.log_event(event=event)
            for npc in event.whoInvolved:
                npc.percive(event=event)
        self.pending_events.clear()
    
    def _get_npc_from_who_involved(self, whoInvolved: {NPC, EventRole}) -> NPC | None:
        for key, value in whoInvolved.items():
            if value ==  EventRole.ACTOR:
                return key
        return None
    
    def _enrich_with_witness(self, event: Event) -> None:
        actor_npc = self._get_npc_from_who_involved(event.whoInvolved)
        nearby_npc = self.world.get_nearby_npc(actor_npc, 15)
        for npc in nearby_npc:
            if npc not in event.whoInvolved:
                event.whoInvolved[npc] = EventRole.WITNESS
    
    def _propogate_all(self) -> None:
        for npc in self.world.npcs:
            npc.propogate(world=self.world)
    
    def _decide_all(self, tick: int) -> None:
        for npc in self.world.npcs:
            decision = npc.decide(self.world)
            if decision:
                action = self._build_action(npc, decision)
                if action is None:
                    continue
                npc.last_action = action
                print(f"\n  [{npc.name}] -> {action.name} ({action.action_type.name})")
                print(f"    {action.description}")
                event = action.to_event()
                self.queue_event(event=event)

    def _print_belief_summary(self) -> None:
        print(f"\n{'='*60}")
        print("  FINAL BELIEF STATE")
        print(f"{'='*60}")
        for npc in self.world.npcs:
            beliefs = self.belief_graph.get_beliefs(npc)
            print(f"\n  {npc.name} ({npc.role.name})")
            if not beliefs:
                print("    (no beliefs)")
                continue
            for node in beliefs:
                source = node.source_npc.name if node.source_npc else "direct"
                print(f"    {node.edge.to_str(for_prompt=True)}  [via {source}]")
    
    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
        npc_map = {npc.name: npc for npc in self.world.npcs}

        state = {
            "clock_time": self.clock.time.isoformat(),
            "npc_locations": {npc.name: list(npc.location) for npc in self.world.npcs},
            "event_log": [
                {
                    "name": e.name,
                    "type": e.event_type.name,
                    "location": e.location if isinstance(e.location, list) else list(e.location) if hasattr(e.location, '__iter__') else e.location,
                    "description": e.description,
                    "timestamp": e.timestamp.isoformat(),
                    "involved": {n.name: r.name for n, r in e.whoInvolved.items()},
                }
                for e in self.world.event_log
            ],
            "beliefs": {
                npc.name: [
                    {
                        "source_npc":        node.source_npc.name if node.source_npc else None,
                        "subject_npc":       node.edge.subject_npc.name if node.edge.subject_npc else None,
                        "object_npc":        node.edge.object_npc.name if node.edge.object_npc else None,
                        "relation_type":     node.edge.relation_type.name,
                        "event_timestamp":   node.edge.event_timestamp.isoformat(),
                        "belief_timestamp":  node.edge.belief_timestamp.isoformat(),
                        "hop_count":         node.edge.hop_count,
                        "confirmations":     node.edge.confirmations,
                        "source_credibility":node.edge.source_credibility,
                        "is_direct":         node.edge.is_direct,
                    }
                    for node in nodes
                ]
                for npc, nodes in self.belief_graph._beliefs.items()
            },
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        print(f"State saved to {path}")

    def load(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)

        npc_map = {npc.name: npc for npc in self.world.npcs}

        # Restore clock
        self.clock.set_time(datetime.fromisoformat(state["clock_time"]))

        # Restore NPC locations
        for name, loc in state["npc_locations"].items():
            if name in npc_map:
                npc_map[name].location = tuple(loc)

        # Restore beliefs
        self.belief_graph._beliefs = {}
        for holder_name, nodes in state["beliefs"].items():
            holder = npc_map.get(holder_name)
            if not holder:
                continue
            self.belief_graph._beliefs[holder] = []
            for nd in nodes:
                edge = Edge(
                    subject_npc=npc_map.get(nd["subject_npc"]),
                    object_npc=npc_map.get(nd["object_npc"]) if nd["object_npc"] else None,
                    relation_type=EventType[nd["relation_type"]],
                    event_timestamp=datetime.fromisoformat(nd["event_timestamp"]),
                    belief_timestamp=datetime.fromisoformat(nd["belief_timestamp"]),
                    hop_count=nd["hop_count"],
                    conformations=nd["confirmations"],
                    source_credibility=nd["source_credibility"],
                    is_direct=nd["is_direct"],
                )
                self.belief_graph._beliefs[holder].append(
                    BeliefGraphNode(source_npc=npc_map.get(nd["source_npc"]) if nd["source_npc"] else None, edge=edge)
                )

        # Restore event log
        self.world.event_log = []
        for ed in state["event_log"]:
            involved = {
                npc_map[n]: EventRole[r]
                for n, r in ed["involved"].items()
                if n in npc_map
            }
            event = Event(
                name=ed["name"],
                event_type=EventType[ed["type"]],
                location=ed["location"],
                whoInvolved=involved,
                description=ed["description"],
            )
            event.timestamp = datetime.fromisoformat(ed["timestamp"])
            self.world.event_log.append(event)

        print(f"State loaded from {path}")

    def _build_action(self, npc: NPC, raw_dict: dict) -> Action | None:
        try:
            action_type = EventType[raw_dict["action_type"]]
        except KeyError:
            print(f"Invalid action_type: {raw_dict.get('action_type')}")
            return None
        
        target_npc = self.world.get_npc_by_name(raw_dict["target_npc"])
        return Action(
            name=raw_dict["name"], 
            actor=npc, 
            action_type=action_type, 
            target_npc=target_npc, 
            location=raw_dict["location"], 
            description=raw_dict["description"]
            )