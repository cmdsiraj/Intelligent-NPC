import { create } from 'zustand'
import type {
  NPC, NpcState, BeliefGraph, SimEvent, NpcActionEntry,
  SimReadyMsg, TickCompleteMsg, NpcActionMsg, TickStartMsg,
} from '../types/ws'

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected'

export interface TickEntry {
  tick:       number
  game_time:  string
  decisions:  NpcActionEntry[]
  streaming:  boolean   // true while tick is in progress
}

interface SimStore {
  // connection
  connectionStatus: ConnectionStatus
  setConnectionStatus: (s: ConnectionStatus) => void

  // scenario meta
  scenarioName:  string | null
  maxTicks:      number
  currentTick:   number
  isRunning:     boolean
  setRunning:    (v: boolean) => void

  // data
  npcs:         NPC[]
  beliefGraph:  BeliefGraph
  eventLog:     SimEvent[]
  tickFeed:     TickEntry[]
  selectedNpc:  string | null
  setSelectedNpc: (name: string | null) => void

  // handlers (called by useWebSocket)
  handleSimReady:     (msg: SimReadyMsg) => void
  handleTickStart:    (msg: TickStartMsg) => void
  handleNpcAction:    (msg: NpcActionMsg) => void
  handleTickComplete: (msg: TickCompleteMsg) => void
  handleRunComplete:  () => void
  handlePaused:       () => void
}

export const useSimStore = create<SimStore>((set, get) => ({
  connectionStatus: 'disconnected',
  setConnectionStatus: s => set({ connectionStatus: s }),

  scenarioName: null,
  maxTicks:     10,
  currentTick:  0,
  isRunning:    false,
  setRunning:   v => set({ isRunning: v }),

  npcs:        [],
  beliefGraph: { nodes: [], edges: [] },
  eventLog:    [],
  tickFeed:    [],
  selectedNpc: null,
  setSelectedNpc: name => set({ selectedNpc: name }),

  handleSimReady: msg => set({
    scenarioName:  msg.scenario,
    maxTicks:      msg.max_ticks,
    currentTick:   0,
    isRunning:     false,
    npcs:          msg.npcs,
    beliefGraph:   msg.belief_graph,
    eventLog:      msg.event_log,
    tickFeed:      [],
    selectedNpc:   null,
  }),

  handleTickStart: msg => set(state => ({
    currentTick: msg.tick,
    isRunning:   true,
    tickFeed: [
      { tick: msg.tick, game_time: msg.game_time, decisions: [], streaming: true },
      ...state.tickFeed,
    ],
  })),

  handleNpcAction: msg => set(state => {
    if (state.tickFeed.length === 0) return {}
    const [head, ...rest] = state.tickFeed
    return {
      tickFeed: [
        { ...head, decisions: [...head.decisions, { npc: msg.npc, action: msg.action }] },
        ...rest,
      ],
    }
  }),

  handleTickComplete: msg => set(state => {
    // update npc states (location, last_action)
    const npcMap = new Map(state.npcs.map(n => [n.name, n]))
    msg.npc_states.forEach((ns: NpcState) => {
      const npc = npcMap.get(ns.name)
      if (npc) npcMap.set(ns.name, { ...npc, location: ns.location, last_action: ns.last_action })
    })

    // close the streaming tick entry
    const [head, ...rest] = state.tickFeed
    const closed = head ? { ...head, streaming: false, decisions: msg.decisions } : null

    return {
      npcs:        Array.from(npcMap.values()),
      beliefGraph: msg.belief_graph,
      eventLog:    [...state.eventLog, ...msg.new_events],
      tickFeed:    closed ? [closed, ...rest] : rest,
    }
  }),

  handleRunComplete: () => set({ isRunning: false }),
  handlePaused:      () => set({ isRunning: false }),
}))
