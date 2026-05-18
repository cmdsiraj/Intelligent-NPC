"""
WebSocket handler — one long-lived connection drives the entire simulation.
"""
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from api.state import manager


async def handle_websocket(websocket: WebSocket) -> None:
    await websocket.accept()

    # Queue used to safely pass npc_action events from the worker thread
    # back into the async event loop.
    action_queue: asyncio.Queue[dict] = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def on_action(entry: dict) -> None:
        loop.call_soon_threadsafe(action_queue.put_nowait, entry)

    _run_task: asyncio.Task | None = None
    _paused = asyncio.Event()
    _paused.set()  # starts as "not paused" (Event is set = allowed to run)

    async def drain_actions() -> None:
        """Drain npc_action events while a tick is running."""
        while True:
            entry = await action_queue.get()
            if entry is None:  # sentinel — tick done
                break
            await websocket.send_json({"type": "npc_action", **entry})

    async def run_ticks(ticks: int) -> None:
        nonlocal _run_task
        if manager.active:
            manager.active.is_running = True
        manager.set_action_callback(on_action)

        try:
            remaining = ticks
            while remaining > 0:
                # Check for pause
                if not _paused.is_set():
                    await websocket.send_json({
                        "type": "paused",
                        "tick": manager.active.current_tick if manager.active else 0,
                    })
                    await _paused.wait()

                tick_num = (manager.active.current_tick + 1) if manager.active else 1
                await websocket.send_json({
                    "type":      "tick_start",
                    "tick":      tick_num,
                    "game_time": manager.active.simulator.clock.time.isoformat() if manager.active else "",
                })

                # Run one tick in a thread (blocks on LLM calls)
                drain_task = asyncio.create_task(drain_actions())
                result = await asyncio.to_thread(manager.run_tick)
                action_queue.put_nowait(None)   # sentinel to end drain
                await drain_task

                await websocket.send_json({"type": "tick_complete", "tick": tick_num, **result})
                remaining -= 1

            await websocket.send_json({
                "type":        "run_complete",
                "total_ticks": ticks,
            })
        finally:
            if manager.active:
                manager.active.is_running = False
            manager.set_action_callback(None)  # type: ignore

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            # ── load ──────────────────────────────────────────────────────────
            if msg_type == "load":
                scenario          = data.get("scenario")          # server-side filename
                scenario_content  = data.get("scenario_content")  # raw YAML from browser
                prompt_path       = data.get("prompt_path")       # server-side prompt path
                prompt_content    = data.get("prompt_content")    # raw prompt YAML from browser

                if not scenario and not scenario_content:
                    await websocket.send_json({"type": "error", "message": "Missing scenario"})
                    continue
                try:
                    state = manager.load(
                        scenario_name    = scenario or "custom",
                        scenario_content = scenario_content,
                        prompt_path_override = prompt_path,
                        prompt_content   = prompt_content,
                    )
                    await websocket.send_json({"type": "sim_ready", **state})
                except FileNotFoundError as e:
                    await websocket.send_json({"type": "error", "message": str(e)})

            # ── run ───────────────────────────────────────────────────────────
            elif msg_type == "run":
                if not manager.active:
                    await websocket.send_json({"type": "error", "message": "No scenario loaded"})
                    continue
                if manager.active.is_running:
                    await websocket.send_json({"type": "error", "message": "Already running"})
                    continue
                _paused.set()
                ticks = data.get("ticks", manager.active.max_ticks - manager.active.current_tick)
                _run_task = asyncio.create_task(run_ticks(ticks))

            # ── step ──────────────────────────────────────────────────────────
            elif msg_type == "step":
                if not manager.active:
                    await websocket.send_json({"type": "error", "message": "No scenario loaded"})
                    continue
                if manager.active.is_running:
                    await websocket.send_json({"type": "error", "message": "Already running"})
                    continue
                _paused.set()
                _run_task = asyncio.create_task(run_ticks(1))

            # ── pause ─────────────────────────────────────────────────────────
            elif msg_type == "pause":
                _paused.clear()

            # ── reset ─────────────────────────────────────────────────────────
            elif msg_type == "reset":
                if _run_task and not _run_task.done():
                    _run_task.cancel()
                if manager.active:
                    state = manager.load(manager.active.scenario_name)
                    await websocket.send_json({"type": "sim_ready", **state})

    except WebSocketDisconnect:
        if _run_task and not _run_task.done():
            _run_task.cancel()
