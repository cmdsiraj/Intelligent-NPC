from __future__ import annotations
from typing import TYPE_CHECKING
from Models.Event import Event
import math
from Models.Enums import EventRole

if TYPE_CHECKING:
    from Models.NPC import NPC
    
class World:
    
    def __init__(self, npcs: list[NPC], locations: dict[str, tuple[float, float]]):
        self.npcs = npcs
        self.locations = locations
        self.event_log: list[Event] = list()
        
        self._npc_name_map: dict[str, NPC] = {}
        
        for npc in self.npcs:
            self._npc_name_map[npc.name] = npc
            
    
    
    def _distance(self, p1: tuple[float, float], p2: tuple[float, float] ):
        return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
    
    def get_nearby_npc(self, target_npc: NPC, radius: float) -> list[NPC]:
        nearby_npcs = list()
        for npc in self.npcs:
            if npc == target_npc:
                continue
            if self._distance(target_npc.location, npc.location) <= radius:
                nearby_npcs.append(npc)
        return nearby_npcs
    
    def log_event(self, event: Event) -> None:
        self.event_log.append(event)
    
    def get_recent_events(self, npc: NPC, limit: int=5) -> list[Event]:
        recent_events = list()
        for event in self.event_log[::-1]:
            if event.whoInvolved.get(npc):
                recent_events.append(event)
            if len(recent_events) == limit:
                break
        return recent_events
    
    def get_npc_by_name(self, name: str) -> NPC | None:
        return self._npc_name_map.get(name)
            