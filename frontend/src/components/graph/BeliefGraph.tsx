import { useEffect, useRef } from 'react'
import cytoscape from 'cytoscape'
import { useSimStore } from '../../store/useSimStore'
import { Network } from 'lucide-react'

const ROLE_NODE_COLOR: Record<string, string> = {
  LEADER:     '#eab308',
  MEDIATOR:   '#3b82f6',
  COMPETITOR: '#f97316',
  HELPER:     '#22c55e',
  ANALYST:    '#a855f7',
  NEWCOMER:   '#06b6d4',
  WORKER:     '#6b7280',
  INSTIGATOR: '#ef4444',
}

export function BeliefGraph() {
  const containerRef = useRef<HTMLDivElement>(null)
  const cyRef        = useRef<cytoscape.Core | null>(null)
  const { beliefGraph, selectedNpc, npcs } = useSimStore()

  // Initialise Cytoscape once
  useEffect(() => {
    if (!containerRef.current) return

    cyRef.current = cytoscape({
      container: containerRef.current,
      elements:  [],
      style: [
        {
          selector: 'node',
          style: {
            'background-color':    'data(color)',
            'label':               'data(label)',
            'color':               '#ffffff',
            'font-size':           11,
            'font-family':         'JetBrains Mono, monospace',
            'text-valign':         'center',
            'text-halign':         'center',
            'width':               48,
            'height':              48,
            'border-width':        2,
            'border-color':        '#2a2a2a',
            'text-outline-width':  2,
            'text-outline-color':  '#111111',
          },
        },
        {
          selector: 'node.faded',
          style: { opacity: 0.2 },
        },
        {
          selector: 'node.highlighted',
          style: { 'border-color': '#6366f1', 'border-width': 3 },
        },
        {
          selector: 'edge',
          style: {
            'width':              'mapData(strength, 0, 1, 1, 6)',
            'line-color':         'data(color)',
            'target-arrow-color': 'data(color)',
            'target-arrow-shape': 'triangle',
            'curve-style':        'bezier',
            'label':              'data(relation)',
            'font-size':          9,
            'font-family':        'JetBrains Mono, monospace',
            'color':              '#999999',
            'text-background-color': '#111111',
            'text-background-opacity': 0.7,
            'text-background-padding': '2px',
            'opacity':            0.8,
          },
        },
        {
          selector: 'edge.faded',
          style: { opacity: 0.1 },
        },
      ],
      layout: { name: 'cose', animate: false } as cytoscape.LayoutOptions,
      userZoomingEnabled:   true,
      userPanningEnabled:   true,
      boxSelectionEnabled:  false,
    })

    return () => { cyRef.current?.destroy(); cyRef.current = null }
  }, [])

  // Update graph data when beliefGraph changes
  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return

    const npcColorMap = new Map(npcs.map(n => [n.name, ROLE_NODE_COLOR[n.role] ?? '#888888']))

    cy.batch(() => {
      // Nodes
      const existingNodes = new Set(cy.nodes().map(n => n.id()))
      beliefGraph.nodes.forEach(n => {
        if (existingNodes.has(n.data.id)) {
          cy.getElementById(n.data.id).data({ ...n.data, color: npcColorMap.get(n.data.id) ?? '#888' })
        } else {
          cy.add({ group: 'nodes', data: { ...n.data, color: npcColorMap.get(n.data.id) ?? '#888' } })
        }
      })
      // Remove stale nodes
      cy.nodes().forEach(node => {
        if (!beliefGraph.nodes.find(n => n.data.id === node.id())) node.remove()
      })

      // Edges
      const existingEdges = new Set(cy.edges().map(e => e.id()))
      beliefGraph.edges.forEach(e => {
        const color = e.data.polarity === 'POSITIVE' ? '#22c55e' : '#ef4444'
        if (existingEdges.has(e.data.id)) {
          cy.getElementById(e.data.id).data({ ...e.data, color })
        } else {
          cy.add({ group: 'edges', data: { ...e.data, color } })
        }
      })
      cy.edges().forEach(edge => {
        if (!beliefGraph.edges.find(e => e.data.id === edge.id())) edge.remove()
      })
    })

    if (beliefGraph.nodes.length > 0) {
      cy.layout({ name: 'cose', animate: false, randomize: false } as cytoscape.LayoutOptions).run()
    }
  }, [beliefGraph, npcs])

  // Filter by selectedNpc
  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return

    cy.elements().removeClass('faded highlighted')

    if (selectedNpc) {
      const node = cy.getElementById(selectedNpc)
      const connected = node.neighborhood().add(node)
      cy.elements().not(connected).addClass('faded')
      node.addClass('highlighted')
    }
  }, [selectedNpc])

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-border shrink-0">
        <Network size={14} className="text-muted" />
        <span className="text-xs font-mono text-muted uppercase tracking-wider">Belief Graph</span>
        <span className="ml-auto text-xs text-muted font-mono">
          {beliefGraph.nodes.length} nodes · {beliefGraph.edges.length} edges
        </span>
      </div>

      {/* Container must always be in the DOM so Cytoscape can mount to it on init.
          Hide it via CSS (not conditional rendering) when there is nothing to show. */}
      <div className="flex-1 relative overflow-hidden">
        <div
          ref={containerRef}
          className="absolute inset-0"
          style={{ background: '#111111' }}
        />
        {beliefGraph.nodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center
            text-muted text-xs font-mono pointer-events-none">
            Beliefs will appear here as the simulation runs
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 px-3 py-1.5 border-t border-border text-[10px] text-muted font-mono shrink-0">
        <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-positive inline-block" /> positive belief</span>
        <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-negative inline-block" /> negative belief</span>
        <span className="ml-auto">edge width = strength · click NPC to filter</span>
      </div>
    </div>
  )
}
