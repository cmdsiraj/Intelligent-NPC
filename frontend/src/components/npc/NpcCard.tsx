import type { NPC } from '../../types/ws'
import { useSimStore } from '../../store/useSimStore'

const ROLE_COLOR: Record<string, string> = {
  LEADER:     'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  MEDIATOR:   'bg-blue-500/20 text-blue-300 border-blue-500/30',
  COMPETITOR: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
  HELPER:     'bg-green-500/20 text-green-300 border-green-500/30',
  ANALYST:    'bg-purple-500/20 text-purple-300 border-purple-500/30',
  NEWCOMER:   'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
  WORKER:     'bg-gray-500/20 text-gray-300 border-gray-500/30',
  INSTIGATOR: 'bg-red-500/20 text-red-300 border-red-500/30',
}

const TRAIT_COLOR: Record<string, string> = {
  bravery:    'bg-yellow-400',
  trust:      'bg-blue-400',
  aggression: 'bg-red-400',
  cleverness: 'bg-purple-400',
}

interface Props { npc: NPC }

export function NpcCard({ npc }: Props) {
  const { selectedNpc, setSelectedNpc } = useSimStore()
  const isSelected = selectedNpc === npc.name

  return (
    <div
      onClick={() => setSelectedNpc(isSelected ? null : npc.name)}
      className={`p-3 rounded-lg border cursor-pointer transition-all select-none
        ${isSelected
          ? 'border-accent bg-accent/10'
          : 'border-border bg-card hover:border-white/20'
        }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono font-semibold text-sm text-white">{npc.name}</span>
        <span className={`text-[10px] px-1.5 py-0.5 rounded border font-mono ${ROLE_COLOR[npc.role] ?? 'bg-white/10 text-white border-white/20'}`}>
          {npc.role}
        </span>
      </div>

      {/* Role description */}
      <p className="text-[10px] text-muted mb-2 leading-snug">{npc.role_description}</p>

      {/* Personality bars */}
      <div className="space-y-1 mb-2">
        {Object.entries(npc.personality).map(([trait, value]) => (
          <div key={trait} className="flex items-center gap-2">
            <span className="text-[10px] text-muted w-16 font-mono">{trait}</span>
            <div className="flex-1 h-1 bg-surface rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${TRAIT_COLOR[trait] ?? 'bg-white'}`}
                style={{ width: `${value * 100}%` }}
              />
            </div>
            <span className="text-[10px] text-muted font-mono w-6 text-right">{value.toFixed(1)}</span>
          </div>
        ))}
      </div>

      {/* Goals */}
      <div className="space-y-0.5 mb-2">
        {npc.goals.map((g, i) => (
          <div key={i} className={`text-[10px] leading-snug ${g.is_complete ? 'line-through text-muted' : 'text-white/70'}`}>
            <span className="text-muted mr-1">●</span>{g.description}
          </div>
        ))}
      </div>

      {/* Last action */}
      {npc.last_action && (
        <div className="mt-1 px-1.5 py-1 rounded bg-surface text-[10px] text-accent font-mono truncate">
          → {npc.last_action}
        </div>
      )}
    </div>
  )
}
