export interface Personality {
  bravery:    number
  trust:      number
  aggression: number
  cleverness: number
}

export interface Goal {
  description: string
  priority:    number
  is_complete: boolean
}

export interface NPC {
  name:             string
  role:             string
  role_description: string
  location:         [number, number]
  personality:      Personality
  goals:            Goal[]
  last_action:      string | null
}

export interface NpcState {
  name:        string
  location:    [number, number]
  last_action: string | null
}

export interface Action {
  name:        string
  action_type: string
  target_npc:  string | null
  location:    unknown
  description: string
}

export interface NpcActionEntry {
  npc:    string
  action: Action
}

export interface CyNode {
  data: { id: string; label: string; role: string; role_description: string }
}

export interface CyEdge {
  data: {
    id:            string
    source:        string
    target:        string
    relation:      string
    strength:      number
    polarity:      'POSITIVE' | 'NEGATIVE'
    hops:          number
    confirmations: number
    holders:       string[]
    source_npc:    string
  }
}

export interface BeliefGraph {
  nodes: CyNode[]
  edges: CyEdge[]
}

export interface SimEvent {
  name:       string
  event_type: string
  polarity:   'POSITIVE' | 'NEGATIVE'
  location:   unknown
  description:string
  timestamp:  string
  involved:   Record<string, string>
}

// ── WebSocket message types ────────────────────────────────────────────────────

export type WsMessage =
  | SimReadyMsg
  | TickStartMsg
  | NpcActionMsg
  | TickCompleteMsg
  | RunCompleteMsg
  | PausedMsg
  | ErrorMsg

export interface SimReadyMsg {
  type:         'sim_ready'
  scenario:     string
  max_ticks:    number
  npcs:         NPC[]
  locations:    Record<string, [number, number]>
  belief_graph: BeliefGraph
  event_log:    SimEvent[]
}

export interface TickStartMsg {
  type:      'tick_start'
  tick:      number
  game_time: string
}

export interface NpcActionMsg {
  type:   'npc_action'
  npc:    string
  action: Action
}

export interface TickCompleteMsg {
  type:         'tick_complete'
  tick:         number
  game_time:    string
  decisions:    NpcActionEntry[]
  npc_states:   NpcState[]
  belief_graph: BeliefGraph
  new_events:   SimEvent[]
}

export interface RunCompleteMsg {
  type:         'run_complete'
  total_ticks:  number
}

export interface PausedMsg {
  type: 'paused'
  tick: number
}

export interface ErrorMsg {
  type:    'error'
  message: string
}
