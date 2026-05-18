"""
ObservableSimulator — wraps Simulator to expose structured per-tick data.
Lives in the API layer. Framework (Models/) is untouched.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio
from typing import Callable

from Models.Simulator import Simulator
from Models.NPC import NPC
from api.serializers import serialize_action, serialize_npc_state, serialize_belief_graph, serialize_event


class ObservableSimulator(Simulator):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Called synchronously from the worker thread for each NPC action.
        # Must be thread-safe — use loop.call_soon_threadsafe().
        self._on_action: Callable[[dict], None] | None = None
        self._current_tick: int = 0

    def set_action_callback(self, cb: Callable[[dict], None]) -> None:
        self._on_action = cb

    def run_single_tick(self, tick_num: int) -> dict:
        """
        Runs one full tick and returns structured results.
        Blocking — must be called via asyncio.to_thread().
        """
        self._current_tick = tick_num
        self._tick_decisions = []

        # Capture the events about to be processed so we can return them to the frontend.
        # (After _process_events() clears pending_events, they're moved into world.event_log —
        #  but the current tick's NPC decisions are queued at the END and won't be in event_log
        #  until the NEXT tick.  Snapshotting here gives the frontend exactly what fired this tick.)
        events_this_tick = list(self.pending_events)

        self._process_events()
        self._propogate_all()
        self._decide_all_observable()
        self.clock.tick()

        return {
            "decisions":    self._tick_decisions,
            "npc_states":   [serialize_npc_state(npc) for npc in self.world.npcs],
            "belief_graph": serialize_belief_graph(self.belief_graph, self.world.npcs),
            "new_events":   [serialize_event(e) for e in events_this_tick],
            "game_time":    self.clock.time.isoformat(),
        }

    def _decide_all_observable(self) -> None:
        """Drop-in replacement for Simulator._decide_all() — captures results."""
        from Models.Enums import EventType
        self._tick_decisions = []

        for npc in self.world.npcs:
            decision = npc.decide(self.world)
            if not decision:
                continue
            action = self._build_action(npc, decision)
            if action is None:
                continue

            npc.last_action = action
            action_data = serialize_action(action)
            decision_entry = {"npc": npc.name, "action": action_data}

            self._tick_decisions.append(decision_entry)

            # Fire callback (thread-safe enqueue to the async event loop)
            if self._on_action:
                try:
                    self._on_action(decision_entry)
                except Exception:
                    pass

            self.queue_event(action.to_event())
