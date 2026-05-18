import yaml
from BeliefGraph import BeliefGraph
from Models.World import World
from Models.Simulator import Simulator
from LLMClient import LLM
from Models.Enums import CharacterRole, EventType, EventRole
from Models.NPC import NPC, Personality, Goal
from Models.Event import Event


class ScenarioLoader:

    @staticmethod
    def load(
        path: str = None,
        llm: LLM = None,
        *,
        scenario_content: str = None,
        prompt_path_override: str = None,
        prompt_content: str = None,
    ) -> Simulator:
        """
        Load a scenario from either a file path or raw YAML content.

        Parameters
        ----------
        path               : path to a scenario YAML file on the server
        llm                : optional pre-built LLM instance
        scenario_content   : raw YAML string sent directly (e.g. from browser upload)
        prompt_path_override: server-side path that overrides the scenario's 'prompt' key
        prompt_content     : raw prompt YAML string sent directly (overrides everything)
        """
        if scenario_content:
            config = yaml.safe_load(scenario_content)
        else:
            with open(path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

        llm = llm or LLM(max_tokens=config.get("max_tokens", 600))
        beliefs = BeliefGraph()

        # Resolve effective prompt path (content wins over path override wins over config)
        effective_prompt_path = (
            prompt_path_override
            or config.get("prompt", "prompts/system_prompt_main.yaml")
        )

        # ── Build NPCs ─────────────────────────────────────────────────────────
        npc_map: dict[str, NPC] = {}
        for nc in config["npcs"]:
            p = nc["personality"]
            npc = NPC(
                name=nc["name"],
                role=CharacterRole[nc["role"]],
                llmReason=llm,
                beliefGraph=beliefs,
                location=tuple(nc["location"]),
                prompt_path=effective_prompt_path,
                prompt_content=prompt_content,   # None unless browser sent content
                personality=Personality(
                    bravery=p["bravery"],
                    trust=p["trust"],
                    aggression=p["aggression"],
                    cleverness=p["cleverness"],
                ),
                goals=[
                    Goal(
                        description=g["description"],
                        priority=g["priority"],
                        is_complete=g.get("is_complete", False),
                    )
                    for g in nc["goals"]
                ],
            )
            npc_map[npc.name] = npc

        # ── Build World ────────────────────────────────────────────────────────
        locations = {k: tuple(v) for k, v in config["locations"].items()}
        world = World(npcs=list(npc_map.values()), locations=locations)

        # ── Build Simulator ────────────────────────────────────────────────────
        sim = Simulator(world=world, belief_graph=beliefs)
        sim._default_ticks = config.get("ticks", 10)

        # ── Queue seed events ──────────────────────────────────────────────────
        for ec in config.get("events", []):
            involved = {
                npc_map[inv["npc"]]: EventRole[inv["role"]]
                for inv in ec["involved"]
                if inv["npc"] in npc_map
            }
            sim.queue_event(Event(
                name=ec["name"],
                event_type=EventType[ec["type"]],
                location=tuple(ec["location"]),
                whoInvolved=involved,
                description=ec.get("description", ""),
            ))

        return sim
