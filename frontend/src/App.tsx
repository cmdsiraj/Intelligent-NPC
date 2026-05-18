import { useWebSocket } from './hooks/useWebSocket'
import { ControlBar } from './components/layout/ControlBar'
import { NpcRoster } from './components/npc/NpcRoster'
import { BeliefGraph } from './components/graph/BeliefGraph'
import { TickFeed } from './components/feed/TickFeed'

export default function App() {
  const { send } = useWebSocket()

  return (
    <div className="flex flex-col h-screen bg-surface text-white overflow-hidden">
      <ControlBar send={send} />

      {/* 3-panel layout */}
      <div className="flex flex-1 overflow-hidden">

        {/* Left — NPC Roster */}
        <div className="w-72 shrink-0 border-r border-border overflow-hidden flex flex-col">
          <NpcRoster />
        </div>

        {/* Centre — Belief Graph */}
        <div className="flex-1 overflow-hidden flex flex-col">
          <BeliefGraph />
        </div>

        {/* Right — Tick Feed */}
        <div className="w-80 shrink-0 border-l border-border overflow-hidden flex flex-col">
          <TickFeed />
        </div>

      </div>
    </div>
  )
}
