import { useSimStore } from '../../store/useSimStore'
import { NpcCard } from './NpcCard'
import { Users } from 'lucide-react'

export function NpcRoster() {
  const npcs = useSimStore(s => s.npcs)

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-border shrink-0">
        <Users size={14} className="text-muted" />
        <span className="text-xs font-mono text-muted uppercase tracking-wider">Characters</span>
        <span className="ml-auto text-xs text-muted">{npcs.length}</span>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {npcs.length === 0 ? (
          <div className="text-center text-muted text-xs py-8 font-mono">
            Load a scenario to see characters
          </div>
        ) : (
          npcs.map(npc => <NpcCard key={npc.name} npc={npc} />)
        )}
      </div>
    </div>
  )
}
