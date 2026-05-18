"""
SimulationManager — singleton that owns the active simulation.
Thread-safe load/step interface for the WebSocket handler.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio
from dataclasses import dataclass, field
from typing import Callable

from GameClock import reset_clock
from ScenarioLoader import ScenarioLoader
from BeliefGraph import BeliefGraph
from Models.Simulator import Simulator
from api.observable_simulator import ObservableSimulator
from api.serializers import serialize_npc, serialize_belief_graph, serialize_event


@dataclass
class ActiveSim:
    simulator:     ObservableSimulator
    scenario_name: str
    current_tick:  int = 0
    max_ticks:     int = 10
    is_running:    bool = False


class SimulationManager:
    def __init__(self):
        self._sim: ActiveSim | None = None

    @property
    def active(self) -> ActiveSim | None:
        return self._sim

    def load(
        self,
        scenario_name: str,
        *,
        scenario_content: str = None,
        prompt_path_override: str = None,
        prompt_content: str = None,
    ) -> dict:
        """
        Load a scenario by filename or raw YAML content.

        Parameters
        ----------
        scenario_name       : filename shown in the UI (e.g. 'grad_students.yaml').
                              Used as the display name.  Ignored when scenario_content
                              is supplied — the scenario is loaded from content instead.
        scenario_content    : raw scenario YAML string (browser file-upload path).
        prompt_path_override: server-side path to a prompt YAML (overrides scenario default).
        prompt_content      : raw prompt YAML string (browser file-upload path).
        """
        root = os.path.dirname(os.path.dirname(__file__))

        # Reset the global game clock before loading a new scenario
        reset_clock()

        if scenario_content:
            base_sim = ScenarioLoader.load(
                scenario_content=scenario_content,
                prompt_path_override=prompt_path_override,
                prompt_content=prompt_content,
            )
        else:
            path = os.path.join(root, "scenarios", scenario_name)
            if not os.path.exists(path):
                raise FileNotFoundError(f"Scenario not found: {path}")
            base_sim = ScenarioLoader.load(
                path,
                prompt_path_override=prompt_path_override,
                prompt_content=prompt_content,
            )

        obs = ObservableSimulator(world=base_sim.world, belief_graph=base_sim.belief_graph)
        obs._default_ticks = base_sim._default_ticks
        obs.pending_events = base_sim.pending_events

        self._sim = ActiveSim(
            simulator=obs,
            scenario_name=scenario_name,
            current_tick=0,
            max_ticks=base_sim._default_ticks,
        )

        return self.get_initial_state()

    def run_tick(self) -> dict:
        """Run one tick synchronously. Call via asyncio.to_thread()."""
        if not self._sim:
            raise RuntimeError("No simulation loaded")
        self._sim.current_tick += 1
        return self._sim.simulator.run_single_tick(self._sim.current_tick)

    def set_action_callback(self, cb: Callable[[dict], None]) -> None:
        if self._sim:
            self._sim.simulator.set_action_callback(cb)

    def save(self, path: str) -> None:
        if not self._sim:
            raise RuntimeError("No simulation loaded")
        os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
        self._sim.simulator.save(path)

    def load_state(self, path: str) -> None:
        if not self._sim:
            raise RuntimeError("No simulation loaded")
        self._sim.simulator.load(path)

    def get_initial_state(self) -> dict:
        sim = self._sim
        if not sim:
            return {}
        return {
            "scenario":  sim.scenario_name,
            "max_ticks": sim.max_ticks,
            "npcs":      [serialize_npc(npc) for npc in sim.simulator.world.npcs],
            "locations": {k: list(v) for k, v in sim.simulator.world.locations.items()},
            "belief_graph": serialize_belief_graph(
                sim.simulator.belief_graph,
                sim.simulator.world.npcs,
            ),
            "event_log": [serialize_event(e) for e in sim.simulator.world.event_log],
        }

    def get_full_state(self) -> dict:
        return self.get_initial_state()


# Module-level singleton — one active simulation per process
manager = SimulationManager()
