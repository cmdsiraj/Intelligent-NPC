from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass
from Models.Enums import EventType, EventRole, BeliefType
from Models.Event import Event

if TYPE_CHECKING:
    from Models.NPC import NPC

@dataclass
class Action:
    name: str
    actor: NPC
    action_type: EventType
    target_npc: NPC | None
    location: tuple[float, float]
    description: str
    
    def to_event(self) -> Event:
        whoInvolved: dict[NPC, EventRole] = {
            self.actor: EventRole.ACTOR,
        }
        if self.target_npc:
            whoInvolved[self.target_npc] = EventRole.TARGET
        return Event(name=self.name, event_type=self.action_type, location=self.location, whoInvolved=whoInvolved, description=self.description)
    
    def to_str(self, for_prompt: bool = False) -> str:
        target = self.target_npc.name if self.target_npc else "none"
        if for_prompt:
            return (
                f"{self.name} | {self.action_type.name} | target={target} "
                f"| @ {self.location} | {self.description}"
            )
        return (
            f"  Name:        {self.name}\n"
            f"  Actor:       {self.actor.name}\n"
            f"  Action Type: {self.action_type.name}\n"
            f"  Target:      {target}\n"
            f"  Location:    {self.location}\n"
            f"  Description: {self.description}"
        )

    def __str__(self):
        return self.to_str(for_prompt=False)
    
    @staticmethod
    def generate_schema_instructinos():
        all_types = [m.name for m in EventType]
        schema = {
            "name": "str - short name for this action (two to four words)",
            "target_npc": "str | null - required for RELATIONAL types; the entity being characterized for ATTRIBUTE types",
            "action_type": f"str - MUST be exactly one of: {all_types}",
            "location": "[x, y] - coordinates as a JSON array of two integers",
            "description": "str - one sentence describing what you are doing and why"
        }
        return schema
    