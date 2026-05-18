from Models.Edge import Edge
from Models.NPC import NPC
from dataclasses import dataclass
from Models.Enums import EventType, Polarity
from datetime import datetime

@dataclass
class BeliefGraphNode:
    source_npc: NPC
    edge: Edge

class BeliefGraph:
    
    def __init__(self):
        self._beliefs: dict[NPC, list[BeliefGraphNode]] = {}
        
    
    def _get_edge_key(self, edge: Edge) -> tuple[NPC, EventType, NPC, datetime]:
        return (edge.subject_npc, edge.relation_type, edge.object_npc, edge.event_timestamp)
    
    def find_duplicate_edge(self, edge: Edge, candidates: list[BeliefGraphNode]) -> BeliefGraphNode | None:
        edge_key = self._get_edge_key(edge=edge)
        for e in candidates:
            e_key = self._get_edge_key(e.edge)
            if e_key == edge_key:
                return e
        return None
    
    def add_or_confirm(self, holder_npc: NPC, source_npc: NPC, edge: Edge):
        if holder_npc not in self._beliefs:
            self._beliefs[holder_npc] = []
        
        holder_nodes = self._beliefs[holder_npc]
        
        duplicate = self.find_duplicate_edge(edge=edge, candidates=holder_nodes)
        if duplicate:
            duplicate.edge.confirmations+=1
        else:
            holder_nodes.append(BeliefGraphNode(source_npc=source_npc, edge=edge))
    
    def get_beliefs(self, holder_npc: NPC):
        return self._beliefs.get(holder_npc)
    
    def get_beliefs_about(self, holder_npc: NPC, subject_npc: NPC) -> list[BeliefGraphNode] | None:
        # what 'holder_npc' thinks or believes about 'subject_npc'
        holder_nodes = self._beliefs.get(holder_npc, None)
        if holder_nodes:
            beliefs = list()
            for node in holder_nodes:
                if node.edge.subject_npc == subject_npc:
                    beliefs.append(node)
            return beliefs
        return None
        
    
    def get_net_score(self, holder_npc: NPC, subject_npc: NPC) -> float:
        beliefs = self.get_beliefs_about(holder_npc=holder_npc, subject_npc=subject_npc)
        if beliefs:
            pos_sum = 0
            neg_sum = 0
            for belief in beliefs:
                strength = belief.edge.strength
                if belief.edge.polarity == Polarity.POSITIVE:
                    pos_sum += strength
                else:
                    neg_sum += strength
            return pos_sum - neg_sum
        return 0.0