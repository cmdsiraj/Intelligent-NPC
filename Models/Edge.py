from __future__ import annotations

from GameClock import get_gametime_obj
from datetime import datetime
from Models.Enums import EventType, Polarity

class Edge:
    
    TIME_DECAY_CONSTANT = 0.05
    HOP_DECAY_CONSTANT = 0.2
    CONFORMATION_BOOST = 0.1
    
    def __init__(self, 
                 subject_npc: NPC, object_npc: NPC, relation_type: EventType, 
                 event_timestamp: datetime, belief_timestamp: datetime, hop_count: int, 
                 conformations: int, source_credibility: float, is_direct: bool):
        
        self.subject_npc = subject_npc
        self.object_npc = object_npc
        self.relation_type = relation_type
        self.belief_type = self.relation_type.get_belief_type()
        self.polarity = self.relation_type.get_polarity()
        self.base_belief = self.relation_type.get_base_belief()
        self.event_timestamp = event_timestamp # when the event actually happened
        self.belief_timestamp = belief_timestamp # when the NPC came to know about this event.
        self.hop_count = hop_count
        self.confirmations = conformations
        self.source_credibility = source_credibility
        self.is_direct = is_direct
        
        self._sim_time = get_gametime_obj()
    
    
    def _calculate_timedecay(self):
        time_diff = (self._sim_time.time - self.event_timestamp).days
        decay = min(1, max(0, (1-(time_diff*self.TIME_DECAY_CONSTANT))))
        return decay
    
    def _calculate_hopdecay(self):
        return min(1, max(0, 1-(self.hop_count*self.HOP_DECAY_CONSTANT)))
    
    def _calculate_conformationboost(self):
        return min(2.0, 1.0 + (self.confirmations * self.CONFORMATION_BOOST))
    
    @property
    def strength(self):
        return self.base_belief * self._calculate_timedecay() * self._calculate_hopdecay() * self._calculate_conformationboost() * self.source_credibility
    
    def to_str(self, for_prompt: bool = False) -> str:
        subject = self.subject_npc.name
        obj = self.object_npc.name if self.object_npc else "none"
        if for_prompt:
            return (
                f"{subject} -[{self.relation_type.name}]-> {obj} "
                f"(strength={self.strength:.2f} hops={self.hop_count})"
            )
        return (
            f"  Subject:         {subject}\n"
            f"  Object:          {obj}\n"
            f"  Relation:        {self.relation_type.name}\n"
            f"  Strength:        {self.strength:.3f}\n"
            f"  Hops:            {self.hop_count}\n"
            f"  Event time:      {self.event_timestamp}\n"
            f"  Belief time:     {self.belief_timestamp}\n"
            f"  Confirmations:   {self.confirmations}\n"
            f"  Direct:          {self.is_direct}"
        )

    def __str__(self):
        return self.to_str(for_prompt=False)