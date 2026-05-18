# Intelligent NPC Framework

A scenario-agnostic AI simulation framework where NPCs reason, form beliefs, and make decisions using a large language model. Behaviour emerges purely from personality numbers and goals — no scripted dialogue, no hardcoded outcomes.

---

## What it does

- Each NPC has a **personality** (bravery, trust, aggression, cleverness) and a set of **goals**
- NPCs witness events, form **beliefs** about one another, and propagate those beliefs to nearby characters
- Every tick, each NPC calls an LLM to decide their next action based on what they know
- Beliefs decay over time, weaken with each gossip hop, and strengthen through confirmation
- The entire scenario — characters, locations, seed events, prompt path — is defined in a single **YAML file**

---

## Stack

| Layer | Technology |
|---|---|
| NPC reasoning | AWS Bedrock (Amazon Nova Lite) via `boto3` |
| Backend API | FastAPI + WebSockets |
| Frontend | React 18 · TypeScript · Vite · Tailwind CSS |
| Graph view | Cytoscape.js |
| State management | Zustand |

---

## Project structure

```
intelligent-npc/
├── Models/               # Core framework (no API or UI dependencies)
│   ├── NPC.py            # NPC class — perceive, propagate, decide
│   ├── Edge.py           # Belief edge with decay + strength formula
│   ├── Event.py          # An event in the world
│   ├── Action.py         # An NPC's decision → becomes an Event
│   ├── Simulator.py      # Tick loop, event queue, belief summary
│   ├── World.py          # Spatial queries, event log
│   └── Enums.py          # EventType, CharacterRole, Polarity, …
├── BeliefGraph.py        # Directed belief graph (add, confirm, query)
├── GameClock.py          # Singleton simulation clock
├── ScenarioLoader.py     # YAML → World + NPCs + Simulator
├── LLMClient.py          # AWS Bedrock wrapper with JSON retry logic
├── utilities.py          # load_prompt / parse_prompt helpers
│
├── scenarios/            # Scenario YAML files
│   └── grad_students.yaml
├── prompts/              # System prompt YAML templates
│   └── system_prompt_main.yaml
├── saves/                # Runtime save files (git-ignored)
│
├── api/                  # FastAPI layer (framework untouched)
│   ├── app.py            # Entry point, CORS, routes, WebSocket
│   ├── observable_simulator.py  # Simulator subclass with streaming callback
│   ├── state.py          # SimulationManager singleton
│   ├── serializers.py    # Framework objects → JSON
│   ├── routes/
│   │   ├── scenarios.py  # GET /scenarios, GET /scenarios/{name}
│   │   └── simulation.py # GET /state, POST /save, POST /load-state
│   └── ws/
│       └── handler.py    # WebSocket command dispatcher
│
├── frontend/             # React + Vite frontend
│   └── src/
│       ├── components/
│       │   ├── layout/ControlBar.tsx   # Load · Run · Pause · Step · Reset
│       │   ├── npc/NpcRoster.tsx       # Left panel — character cards
│       │   ├── graph/BeliefGraph.tsx   # Centre — live Cytoscape graph
│       │   └── feed/TickFeed.tsx       # Right panel — streaming decisions
│       ├── store/useSimStore.ts        # Zustand global state
│       ├── hooks/useWebSocket.ts       # WS connection + auto-reconnect
│       └── types/ws.ts                 # TypeScript message interfaces
│
├── run.py                # CLI entry point
└── main.py               # Minimal one-liner runner
```

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- AWS credentials configured (`~/.aws/credentials` or environment variables)
- An AWS Bedrock model ARN for Amazon Nova Lite

### 1. Python environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install fastapi uvicorn[standard] boto3 python-dotenv pyyaml
```

### 2. Environment variables

Create a `.env` file in the project root:

```env
AWS_MODEL_ARN=arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-lite-v1:0
AWS_DEFAULT_REGION=us-east-1
```

### 3. Frontend dependencies

```bash
cd frontend
npm install
```

---

## Running

### Full stack (API + UI)

```bash
# Terminal 1 — API server (from project root)
uvicorn api.app:app --reload --port 8000

# Terminal 2 — Frontend dev server
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

### CLI only

```bash
# Run the default scenario
python run.py

# Run a specific scenario
python run.py scenarios/grad_students.yaml

# Override tick count
python run.py scenarios/grad_students.yaml --ticks 5

# Save state after run
python run.py scenarios/grad_students.yaml --save saves/checkpoint.json

# Resume from a save
python run.py scenarios/grad_students.yaml --load saves/checkpoint.json
```

---

## Frontend walkthrough

| Control | What it does |
|---|---|
| **Scenario dropdown** | Lists all YAML files in `scenarios/` |
| **📂 (folder icon)** | Pick any local scenario YAML from your machine |
| **Load** | Sends the scenario to the API and populates all panels |
| **▶ Run** | Runs all remaining ticks; NPC decisions stream in real time |
| **⏸ Pause** | Pauses after the current tick finishes |
| **⏭ Step** | Runs exactly one tick |
| **↺ Reset** | Reloads the scenario from the beginning |
| **⚙️ Settings** | Reveals the System Prompt row — type a server-side path or browse a local file to override the default prompt |
| **💾 Save** | Saves the current simulation state to `saves/` |

**Belief Graph** — click any NPC card in the left panel to highlight only that character's belief neighbourhood. Edge width = belief strength; green = positive, red = negative.

---

## Writing a scenario

Create a new file in `scenarios/`. Everything is defined in YAML — no Python required.

```yaml
name: "My Scenario"
description: "Optional description"
ticks: 10
max_tokens: 600
prompt: "prompts/system_prompt_main.yaml"

npcs:
  - name: "Alice"
    role: "LEADER"           # see CharacterRole enum
    location: [10, 10]
    personality:
      bravery:    0.8
      trust:      0.5
      aggression: 0.3
      cleverness: 0.9
    goals:
      - description: "secure funding before the deadline"
        priority: 1.0

locations:
  office: [10, 10]
  boardroom: [20, 10]

events:
  - name: "Alice overhears the board meeting"
    type: "REPORT"           # see EventType enum
    location: [20, 10]
    description: "Alice learned the board is considering a budget cut."
    involved:
      - npc: "Alice"
        role: "ACTOR"        # ACTOR | TARGET | WITNESS
```

---

## Available enums

### EventType

| Relational (requires `target_npc`) | Attribute (characterises `target_npc`) |
|---|---|
| THEFT, MURDER, RESCUE, DONATE | IS_GOOD, IS_THIEF, IS_TRUSTWORTHY |
| TRADE, ACCUSE, REPORT, PATROL | IS_DANGEROUS, IS_LOYAL, IS_DISHONEST |
| BETRAY, PRAISE, GOSSIP | IS_HARDWORKING, IS_MANIPULATIVE |

### CharacterRole

| Behavioural | Occupational |
|---|---|
| LEADER, MEDIATOR, COMPETITOR, HELPER | GUARD, MERCHANT, BLACKSMITH |
| ANALYST, NEWCOMER, WORKER, INSTIGATOR | TEACHER, PRIEST, FARMER |

---

## Belief strength formula

```
strength = base_belief
         × time_decay        (−5 % per day)
         × hop_decay          (−20 % per gossip hop)
         × confirmation_boost (+10 % per confirmation, capped at 2×)
         × source_credibility
```

`base_belief` is determined by the `EventType` — high-impact events (MURDER, BETRAY) start at 0.8; rumours (GOSSIP, PATROL) start at 0.25.

---

## Writing a custom system prompt

The prompt is a YAML file with a single `prompt` key. Placeholders are filled in per-NPC each tick:

```yaml
prompt: |
  You are {name}, a {role}.

  ## Personality
  {personality}

  ## Goals
  {goals}

  ## Beliefs
  {beliefs}

  ## Nearby Entities
  {nearby_npcs}

  ## Available Action Types
  {action_types}

  Respond ONLY with a valid JSON block matching this schema:
  {schema}
```

**Available placeholders:** `{name}` `{role}` `{personality}` `{goals}` `{beliefs}` `{nearby_npcs}` `{action_types}` `{schema}` `{current_time}` `{location}` `{last_action}` `{recent_events}`
