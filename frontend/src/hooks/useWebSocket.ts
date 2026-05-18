import { useEffect, useRef, useCallback } from 'react'
import { useSimStore } from '../store/useSimStore'
import type { WsMessage } from '../types/ws'

const WS_URL = 'ws://localhost:8000/ws'

export function useWebSocket() {
  const ws = useRef<WebSocket | null>(null)
  const {
    setConnectionStatus,
    handleSimReady,
    handleTickStart,
    handleNpcAction,
    handleTickComplete,
    handleRunComplete,
    handlePaused,
    setRunning,
  } = useSimStore()

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return

    setConnectionStatus('connecting')
    const socket = new WebSocket(WS_URL)

    socket.onopen = () => setConnectionStatus('connected')

    socket.onmessage = (e) => {
      const msg: WsMessage = JSON.parse(e.data)
      switch (msg.type) {
        case 'sim_ready':      handleSimReady(msg);     break
        case 'tick_start':     handleTickStart(msg);    break
        case 'npc_action':     handleNpcAction(msg);    break
        case 'tick_complete':  handleTickComplete(msg); break
        case 'run_complete':   handleRunComplete();     break
        case 'paused':         handlePaused();          break
        case 'error':          console.error('[WS]', msg.message); break
      }
    }

    socket.onclose = () => {
      setConnectionStatus('disconnected')
      setRunning(false)
      // Reconnect after 2s
      setTimeout(connect, 2000)
    }

    socket.onerror = () => socket.close()

    ws.current = socket
  }, []) // eslint-disable-line

  useEffect(() => {
    connect()
    return () => ws.current?.close()
  }, [connect])

  const send = useCallback((msg: object) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(msg))
    }
  }, [])

  return { send }
}
