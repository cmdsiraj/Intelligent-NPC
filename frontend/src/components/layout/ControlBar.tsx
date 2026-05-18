import { useEffect, useRef, useState } from 'react'
import {
  Play, Pause, SkipForward, RotateCcw, Save,
  Wifi, WifiOff, Loader, FolderOpen, Settings, X, FileText,
} from 'lucide-react'
import { useSimStore } from '../../store/useSimStore'

interface Props { send: (msg: object) => void }

/* ─── small helpers ─────────────────────────────────────────────────────── */

function StatusDot({ status }: { status: string }) {
  const color =
    status === 'connected'    ? 'bg-positive' :
    status === 'connecting'   ? 'bg-yellow-400 animate-pulse' :
                                'bg-negative'
  return <span className={`w-2 h-2 rounded-full shrink-0 ${color}`} />
}

function IconBtn({
  onClick, disabled = false, title, children, className = '',
}: {
  onClick: () => void; disabled?: boolean; title?: string
  children: React.ReactNode; className?: string
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={`p-1.5 rounded hover:bg-white/10 disabled:opacity-35
        disabled:cursor-not-allowed transition ${className}`}
    >
      {children}
    </button>
  )
}

/* ─── custom-file badge ──────────────────────────────────────────────────── */

function FileBadge({ name, onClear }: { name: string; onClear: () => void }) {
  return (
    <span className="flex items-center gap-1 px-1.5 py-0.5 bg-accent/20
      border border-accent/40 rounded text-[10px] font-mono text-accent max-w-[140px]">
      <FileText size={9} className="shrink-0" />
      <span className="truncate">{name}</span>
      <button
        onClick={onClear}
        className="shrink-0 hover:text-white transition"
        title="Clear custom file"
      >
        <X size={9} />
      </button>
    </span>
  )
}

/* ─── main component ─────────────────────────────────────────────────────── */

export function ControlBar({ send }: Props) {
  const { connectionStatus, scenarioName, currentTick, maxTicks, isRunning } =
    useSimStore()

  /* server-side scenario list */
  const [scenarios, setScenarios] = useState<{ filename: string; name: string }[]>([])
  const [selected,  setSelected]  = useState('')

  /* custom scenario (browser file or path) */
  const [customScenario, setCustomScenario] =
    useState<{ name: string; content: string } | null>(null)

  /* custom prompt (browser file or path) */
  const [customPrompt, setCustomPrompt] =
    useState<{ name: string; content: string } | null>(null)
  const [promptPath, setPromptPath] = useState('')

  /* settings row visibility */
  const [showSettings, setShowSettings] = useState(false)

  /* hidden file inputs */
  const scenarioFileRef = useRef<HTMLInputElement>(null)
  const promptFileRef   = useRef<HTMLInputElement>(null)

  /* fetch server scenarios on mount */
  useEffect(() => {
    fetch('/api/scenarios')
      .then(r => r.json())
      .then(d => {
        setScenarios(d.scenarios ?? [])
        if (d.scenarios?.length > 0) setSelected(d.scenarios[0].filename)
      })
      .catch(() => {})
  }, [])

  /* read a local file → store content */
  function readFile(
    file: File,
    onDone: (result: { name: string; content: string }) => void,
  ) {
    const reader = new FileReader()
    reader.onload = e => {
      const content = e.target?.result as string
      if (content) onDone({ name: file.name, content })
    }
    reader.readAsText(file, 'utf-8')
  }

  /* handle scenario file pick */
  function onScenarioFilePick(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    readFile(file, result => setCustomScenario(result))
    e.target.value = ''   // reset so same file can be re-picked
  }

  /* handle prompt file pick */
  function onPromptFilePick(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    readFile(file, result => {
      setCustomPrompt(result)
      setPromptPath('')   // file wins over typed path
    })
    e.target.value = ''
  }

  /* build and send the load message */
  function handleLoad() {
    const msg: Record<string, unknown> = { type: 'load' }

    if (customScenario) {
      msg.scenario         = customScenario.name   // display name only
      msg.scenario_content = customScenario.content
    } else {
      msg.scenario = selected
    }

    if (customPrompt) {
      msg.prompt_content = customPrompt.content
    } else if (promptPath.trim()) {
      msg.prompt_path = promptPath.trim()
    }

    send(msg)
  }

  const progress  = maxTicks > 0 ? (currentTick / maxTicks) * 100 : 0
  const canLoad   = (!!customScenario || !!selected) &&
                    connectionStatus === 'connected' && !isRunning
  const canRun    = !!scenarioName && !isRunning && currentTick < maxTicks
  const canStep   = canRun
  const canReset  = !!scenarioName && !isRunning

  const promptActive = !!(customPrompt || promptPath.trim())

  return (
    <div className="bg-card border-b border-border shrink-0">

      {/* ── Main row ─────────────────────────────────────────────────────── */}
      <div className="h-14 flex items-center px-4 gap-3">

        {/* Connection indicator */}
        <div className="flex items-center gap-1.5">
          <StatusDot status={connectionStatus} />
          {connectionStatus === 'connecting'
            ? <Loader size={13} className="text-muted animate-spin" />
            : connectionStatus === 'connected'
              ? <Wifi size={13} className="text-positive" />
              : <WifiOff size={13} className="text-negative" />
          }
        </div>

        <div className="w-px h-6 bg-border" />

        {/* ── Scenario selector ────────────────────────────────────────── */}
        {customScenario ? (
          /* custom file is active — show badge instead of dropdown */
          <FileBadge
            name={customScenario.name}
            onClear={() => setCustomScenario(null)}
          />
        ) : (
          <select
            className="bg-surface border border-border text-white text-xs
              font-mono rounded px-2 py-1 outline-none focus:border-accent
              max-w-[180px] disabled:opacity-40"
            value={selected}
            onChange={e => setSelected(e.target.value)}
            disabled={isRunning}
          >
            {scenarios.map(s => (
              <option key={s.filename} value={s.filename}>{s.name}</option>
            ))}
            {scenarios.length === 0 && (
              <option value="">No scenarios found</option>
            )}
          </select>
        )}

        {/* Browse scenario file */}
        <IconBtn
          onClick={() => scenarioFileRef.current?.click()}
          disabled={isRunning}
          title="Load scenario from local file"
        >
          <FolderOpen size={14} className="text-muted" />
        </IconBtn>
        <input
          ref={scenarioFileRef}
          type="file"
          accept=".yaml,.yml"
          className="hidden"
          onChange={onScenarioFilePick}
        />

        <button
          onClick={handleLoad}
          disabled={!canLoad}
          className="px-3 py-1 text-xs bg-accent rounded hover:bg-indigo-500
            disabled:opacity-35 disabled:cursor-not-allowed transition font-mono"
        >
          Load
        </button>

        <div className="w-px h-6 bg-border" />

        {/* ── Simulation controls ───────────────────────────────────────── */}
        <IconBtn onClick={() => send({ type: 'run', ticks: maxTicks - currentTick })}
          disabled={!canRun} title="Run all remaining ticks">
          <Play size={15} className="text-positive" />
        </IconBtn>

        <IconBtn onClick={() => send({ type: 'pause' })}
          disabled={!isRunning} title="Pause">
          <Pause size={15} className="text-yellow-400" />
        </IconBtn>

        <IconBtn onClick={() => send({ type: 'step' })}
          disabled={!canStep} title="Step one tick">
          <SkipForward size={15} className="text-white" />
        </IconBtn>

        <IconBtn onClick={() => send({ type: 'reset' })}
          disabled={!canReset} title="Reset simulation">
          <RotateCcw size={15} className="text-muted" />
        </IconBtn>

        <div className="w-px h-6 bg-border" />

        {/* ── Progress ─────────────────────────────────────────────────── */}
        <div className="flex items-center gap-2 flex-1 min-w-0 max-w-xs">
          <span className="text-[10px] text-muted whitespace-nowrap font-mono">
            {currentTick}/{maxTicks}
          </span>
          <div className="flex-1 h-1 bg-surface rounded-full overflow-hidden">
            <div
              className="h-full bg-accent transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <div className="flex-1" />

        {/* ── Settings toggle ───────────────────────────────────────────── */}
        <IconBtn
          onClick={() => setShowSettings(v => !v)}
          title="System prompt settings"
          className={showSettings || promptActive ? 'text-accent' : ''}
        >
          <div className="relative">
            <Settings size={14} className={showSettings || promptActive ? 'text-accent' : 'text-muted'} />
            {promptActive && (
              <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5
                rounded-full bg-accent" />
            )}
          </div>
        </IconBtn>

        {/* Save */}
        <button
          onClick={async () => {
            const name = prompt('Save filename (no extension):')
            if (!name) return
            await fetch('/api/simulation/save', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ filename: name }),
            })
          }}
          disabled={!scenarioName}
          className="flex items-center gap-1.5 px-2.5 py-1 text-xs border
            border-border rounded hover:border-accent disabled:opacity-35
            disabled:cursor-not-allowed transition font-mono"
          title="Save simulation state"
        >
          <Save size={13} />
          Save
        </button>
      </div>

      {/* ── Settings row (system prompt) ──────────────────────────────────── */}
      {showSettings && (
        <div className="flex items-center gap-2 px-4 py-2
          border-t border-border bg-surface/50">

          <span className="text-[10px] text-muted font-mono uppercase
            tracking-wider whitespace-nowrap">
            System Prompt
          </span>

          {/* path text input */}
          <input
            type="text"
            value={promptPath}
            onChange={e => {
              setPromptPath(e.target.value)
              setCustomPrompt(null)   // clear file if path is being typed
            }}
            placeholder="prompts/system_prompt_main.yaml  (server-side path)"
            disabled={!!customPrompt}
            className="flex-1 bg-surface border border-border text-white
              text-[11px] font-mono rounded px-2 py-1 outline-none
              focus:border-accent placeholder:text-muted/40
              disabled:opacity-40 min-w-0"
          />

          {/* browse local file */}
          <button
            onClick={() => promptFileRef.current?.click()}
            className="flex items-center gap-1 px-2 py-1 text-[11px] font-mono
              border border-border rounded hover:border-accent transition
              text-muted hover:text-white whitespace-nowrap"
            title="Load prompt from local file"
          >
            <FolderOpen size={11} />
            Browse
          </button>
          <input
            ref={promptFileRef}
            type="file"
            accept=".yaml,.yml"
            className="hidden"
            onChange={onPromptFilePick}
          />

          {/* active file badge / clear */}
          {customPrompt && (
            <FileBadge
              name={customPrompt.name}
              onClear={() => setCustomPrompt(null)}
            />
          )}

          {/* clear path */}
          {promptPath && !customPrompt && (
            <button
              onClick={() => setPromptPath('')}
              className="text-muted hover:text-white transition"
              title="Clear path"
            >
              <X size={13} />
            </button>
          )}

          {/* status hint */}
          <span className="text-[10px] text-muted font-mono whitespace-nowrap ml-1">
            {customPrompt
              ? `using: ${customPrompt.name}`
              : promptPath.trim()
                ? `using: ${promptPath.trim()}`
                : 'using: scenario default'
            }
          </span>
        </div>
      )}
    </div>
  )
}
