"""
Pure serialization functions — framework objects → JSON-safe dicts.
No side effects. No framework imports beyond data models.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Models.NPC import NPC
    from Models.Action import Action
    from Models.Event import Event
    from BeliefGraph import BeliefGraph


def serialize_npc(npc: "NPC") -> dict:
    return {
        "name": npc.name,
        "role": npc.role.name,
        "role_description": npc.role.get_description(),
        "location": list(npc.location),
        "personality": {
            "bravery":    npc.personality.bravery,
            "trust":      npc.personality.trust,
            "aggression": npc.personality.aggression,
            "cleverness": npc.personality.cleverness,
        },
        "goals": [
            {
                "description": g.description,
                "priority":    g.priority,
                "is_complete": g.is_complete,
            }
            for g in npc.goals
        ],
        "last_action": npc.last_action.to_str(for_prompt=True) if npc.last_action else None,
    }


def serialize_npc_state(npc: "NPC") -> dict:
    """Lightweight per-tick NPC state update."""
    return {
        "name":        npc.name,
        "location":    list(npc.location),
        "last_action": npc.last_action.to_str(for_prompt=True) if npc.last_action else None,
    }


def serialize_action(action: "Action") -> dict:
    return {
        "name":        action.name,
        "action_type": action.action_type.name,
        "target_npc":  action.target_npc.name if action.target_npc else None,
        "location":    list(action.location) if hasattr(action.location, "__iter__") and not isinstance(action.location, str) else action.location,
        "description": action.description,
    }


def serialize_event(event: "Event") -> dict:
    return {
        "name":        event.name,
        "event_type":  event.event_type.name,
        "polarity":    event.event_type.get_polarity().name,
        "location":    event.location,
        "description": event.description,
        "timestamp":   event.timestamp.isoformat(),
        "involved":    {n.name: r.name for n, r in event.whoInvolved.items()},
    }


def serialize_belief_graph(belief_graph: "BeliefGraph", npcs: list["NPC"]) -> dict:
    """
    Returns Cytoscape-ready { nodes, edges }.
    Edges are aggregated per (subject, relation, object) — max strength across holders.
    """
    nodes = [
        {
            "data": {
                "id":               npc.name,
                "label":            npc.name,
                "role":             npc.role.name,
                "role_description": npc.role.get_description(),
            }
        }
        for npc in npcs
    ]

    # Aggregate beliefs: key → best edge data
    aggregated: dict[str, dict] = {}

    for holder_npc, nodes_list in belief_graph._beliefs.items():
        for node in nodes_list:
            e = node.edge
            if not e.subject_npc:
                continue
            obj_name = e.object_npc.name if e.object_npc else "__self__"
            key = f"{e.subject_npc.name}|{e.relation_type.name}|{obj_name}"

            existing = aggregated.get(key)
            strength = round(e.strength, 3)

            if existing is None or strength > existing["data"]["strength"]:
                aggregated[key] = {
                    "data": {
                        "id":            key,
                        "source":        e.subject_npc.name,
                        "target":        e.object_npc.name if e.object_npc else e.subject_npc.name,
                        "relation":      e.relation_type.name,
                        "strength":      strength,
                        "polarity":      e.polarity.name,
                        "hops":          e.hop_count,
                        "confirmations": e.confirmations,
                        "holders":       [holder_npc.name],
                        "source_npc":    node.source_npc.name if node.source_npc else "direct",
                    }
                }
            else:
                if holder_npc.name not in existing["data"]["holders"]:
                    existing["data"]["holders"].append(holder_npc.name)

    return {"nodes": nodes, "edges": list(aggregated.values())}
