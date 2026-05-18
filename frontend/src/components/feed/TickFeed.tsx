import { useSimStore, type TickEntry } from '../../store/useSimStore'
import { Activity, Loader } from 'lucide-react'

const TYPE_COLOR: Record<string, string> = {
  THEFT:    'text-red-400',
  MURDER:   'text-red-600',
  RESCUE:   'text-green-400',
  DONATE:   'text-green-300',
  TRADE:    'text-blue-400',
  ACCUSE:   'text-orange-400',
  REPORT:   'text-yellow-400',
  PATROL:   'text-gray-400',
  BETRAY:   'text-red-500',
  PRAISE:   'text-green-400',
  GOSSIP:   'text-purple-400',
  IS_THIEF: 'text-red-400',
  IS_GOOD:  'text-green-400',
  IS_TRUSTWORTHY: 'text-blue-300',
  IS_DANGEROUS:   'text-red-500',
  IS_LOYAL:       'text-blue-400',
  IS_DISHONEST:   'text-orange-400',
  IS_HARDWORKING: 'text-green-300',
  IS_MANIPULATIVE:'text-purple-400',
}

function TickBlock({ entry }: { entry: TickEntry }) {
  return (
    <div className="border border-border rounded-lg overflow-hidden">
      {/* Tick header */}
      <div className="flex items-center gap-2 px-3 py-1.5 bg-surface border-b border-border">
        {entry.streaming
          ? <Loader size={11} className="text-accent animate-spin" />
          : <span className="w-2 h-2 rounded-full bg-accent" />
        }
        <span className="text-xs font-mono text-white font-semibold">Tick {entry.tick}</span>
        <span className="text-[10px] text-muted font-mono ml-auto">{entry.game_time.split('T')[0]}</span>
      </div>

      {/* Decisions */}
      <div className="divide-y divide-border/50">
        {entry.decisions.map((d, i) => (
          <div key={i} className="px-3 py-2">
            <div className="flex items-baseline gap-2 flex-wrap">
              <span className="text-xs font-mono font-semibold text-white">{d.npc}</span>
              <span className="text-[10px] text-muted">→</span>
              <span className="text-xs font-mono text-white/80">{d.action.name}</span>
              <span className={`text-[10px] font-mono ${TYPE_COLOR[d.action.action_type] ?? 'text-muted'}`}>
                ({d.action.action_type})
              </span>
              {d.action.target_npc && (
                <span className="text-[10px] text-muted font-mono">@ {d.action.target_npc}</span>
              )}
            </div>
            <p className="text-[10px] text-muted mt-0.5 leading-snug">{d.action.description}</p>
          </div>
        ))}

        {entry.streaming && entry.decisions.length === 0 && (
          <div className="px-3 py-2 text-[10px] text-muted font-mono animate-pulse">
            Waiting for NPC decisions…
          </div>
        )}
      </div>
    </div>
  )
}

export function TickFeed() {
  const tickFeed = useSimStore(s => s.tickFeed)

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-border shrink-0">
        <Activity size={14} className="text-muted" />
        <span className="text-xs font-mono text-muted uppercase tracking-wider">Tick Feed</span>
        <span className="ml-auto text-xs text-muted">{tickFeed.length} ticks</span>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {tickFeed.length === 0 ? (
          <div className="text-center text-muted text-xs py-8 font-mono">
            Run the simulation to see decisions
          </div>
        ) : (
          tickFeed.map(entry => <TickBlock key={entry.tick} entry={entry} />)
        )}
      </div>
    </div>
  )
}
