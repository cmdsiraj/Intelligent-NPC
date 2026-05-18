from __future__ import annotations
from typing import TYPE_CHECKING
from Models.Enums import EventType, EventRole
from GameClock import get_gametime_obj


if TYPE_CHECKING:
    from Models.NPC import NPC

class Event:

    def __init__(self, name: str, event_type: EventType, location: str, whoInvolved: dict[NPC, EventRole], description: str = ""):
        self.name = name
        self.event_type = event_type
        self.location = location
        self.timestamp = get_gametime_obj().time
        self.whoInvolved = whoInvolved
        self.description = description
    
    def to_str(self, for_prompt: bool = False) -> str:
        actors = ", ".join(
            f"{n.name}={role.name}" for n, role in self.whoInvolved.items()
        )
        if for_prompt:
            return f"[{self.event_type.name}] {self.name} | {actors} | @ {self.location} | {self.description}"
        return (
            f"  Name:        {self.name}\n"
            f"  Type:        {self.event_type.name}\n"
            f"  Location:    {self.location}\n"
            f"  Time:        {self.timestamp}\n"
            f"  Involved:    {actors}\n"
            f"  Description: {self.description}"
        )

    def __str__(self):
        return self.to_str(for_prompt=False)