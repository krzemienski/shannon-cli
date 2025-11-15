# Shannon V3.1 Interactive Dashboard - Demo Script

## For Live Demonstrations

This script guides you through a complete demonstration of all V3.1 dashboard features.

---

## Setup (30 seconds)

```bash
cd /path/to/shannon-cli
python test_dashboard_v31_live.py
```

Wait for:
```
📊 Dashboard is running! Use keyboard to navigate:
   Layer 1 (Session) → Press [Enter] to see agents
```

---

## Demo Flow (3 minutes)

### Act 1: Session Overview (30 seconds)

**What you see:**
```
╭──────────────────────── Shannon V3.1 Dashboard ──────────────────────────╮
│  🎯 Build full-stack SaaS application                                    │
│  Wave 1/5: Wave 1: Core Implementation                                   │
│  ░░░░░░░░░░ 0%                                                           │
│  Agents: 2 active, 1 complete                                            │
│  $0.00 | 0 tokens | 0s | 0 msgs                                          │
│  ⚙ Processing...                                                         │
│  [↵] Agents | [q] Quit | [h] Help                                        │
╰──────────────────────────────────────────────────────────────────────────╯
```

**Say:**
> "This is Layer 1 - the session overview. It shows our north star goal, current wave, overall progress, agent summary, and real-time metrics. Everything updates at 4 Hz."

**Press:** `h` (show help)

**Say:**
> "Pressing 'h' shows context-aware help. Notice it only shows shortcuts relevant to Layer 1."

**Press:** `h` (close help)

---

### Act 2: Agent List (30 seconds)

**Press:** `Enter` (navigate to Layer 2)

**What you see:**
```
╭───────────────────────────── Agent List ─────────────────────────────╮
│  ┏━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━┓ │
│  ┃ ┃ Type           ┃ Progress  ┃ State    ┃ Time  ┃ Blocking     ┃ │
│  ┡━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━┩ │
│  │ │ backend-build… │ ░░░░░ 0%  │ ACTIVE   │ 5m 0s │ -            │ │
│  │ │ frontend-buil… │ ░░░░░ 0%  │ ACTIVE   │ 3m 0s │ -            │ │
│  │ │ database-buil… │ ░░░░░ 1%  │ COMPLETE │ 6m 0s │ -            │ │
│  └─┴────────────────┴───────────┴──────────┴───────┴──────────────┘ │
│  Selected: Agent #1 | [1-9] Select | [↵] Detail | [Esc] Back        │
╰──────────────────────────────────────────────────────────────────────╯
```

**Say:**
> "This is Layer 2 - the agent list. We can see all 3 agents running in this wave, their progress, states, and timing."

**Press:** `2` (select Agent #2)

**Say:**
> "Watch the highlighting change as I select different agents. Agent #2 is now selected - the frontend builder."

**Press:** `3` (select Agent #3)

**Say:**
> "Agent #3 shows COMPLETE status - it finished 6 minutes ago."

**Press:** `1` (select Agent #1)

---

### Act 3: Agent Detail (45 seconds)

**Press:** `Enter` (navigate to Layer 3)

**What you see:**
```
╭────────────────────── Agent #1: backend-builder ──────────────────────╮
│  Task: Build REST API with authentication                             │
│  Status: ACTIVE | Progress: ░░░░░ 0%                                  │
├────────────────────┬───────────────────────────────────────────────────┤
│ Context            │ Tool History                                     │
│                    │                                                  │
│ 📁 Codebase:       │ Total tool calls: 0                              │
│   5 files          │                                                  │
│   src/api/...      │ Files Created:                                   │
│                    │   ✓ api/routes.py                                │
│ 🧠 Memory:         │   ✓ api/auth.py                                  │
│   2 active         │                                                  │
│                    │ Files Modified:                                  │
│ 🔧 Tools:          │   ✎ api/__init__.py                              │
│   5 available      │                                                  │
│                    │                                                  │
│ 🔌 MCP:            │                                                  │
│   2 connected      │                                                  │
├────────────────────────────────────────────────────────────────────────┤
│ Current Operation: Processing...                                      │
│ [↵] Messages | [Esc] Back | [1-3] Switch | [t] Tools | [c] Context   │
╰────────────────────────────────────────────────────────────────────────╯
```

**Say:**
> "Layer 3 shows deep agent details with 4 panels. On the left, we see the context this agent has loaded - 5 codebase files, 2 active memories, 5 available tools, and 2 MCP servers connected."

**Say:**
> "On the right, the tool history shows what files this agent has created and modified. This agent created routes.py and auth.py, and modified __init__.py."

**Press:** `t` (toggle tool history off)

**Say:**
> "I can toggle panels. Pressing 't' hides the tool history..."

**Press:** `t` (toggle tool history on)

**Say:**
> "...and brings it back."

**Press:** `3` (switch to Agent #3)

**Say:**
> "I can switch between agents without leaving Layer 3. Now we're viewing the database builder that already completed."

**Press:** `2` (switch back to Agent #2)

---

### Act 4: Message Stream (45 seconds)

**Press:** `Enter` (navigate to Layer 4)

**What you see:**
```
╭─────────────── Agent #2: frontend-builder - Message Stream ───────────╮
│                                                                        │
│  → USER: Build React UI components for dashboard                      │
│           Include: Chart, Table, Filters                               │
│                                                                        │
│  ← ASSISTANT: I'll create 7 React components...                        │
│    [thinking] Planning component hierarchy... (12 lines)               │
│                                                                        │
│  → TOOL_USE: write_file                                                │
│    { "file_path": "src/components/Dashboard.tsx", ... }                │
│                                                                        │
│  ← TOOL_RESULT: Successfully wrote Dashboard.tsx (245 bytes)          │
│                                                                        │
│  [Message 1-4 of 4] | [↑↓] Scroll | [Enter] Expand | [Esc] Back      │
╰────────────────────────────────────────────────────────────────────────╯
```

**Say:**
> "Layer 4 is the message stream - this is the raw SDK conversation. We can see the full chain of USER prompts, ASSISTANT responses, and TOOL calls."

**Press:** `↓` (scroll down)

**Say:**
> "The stream is scrollable with arrow keys. For sessions with hundreds of messages, virtual scrolling keeps it smooth - only rendering what's visible."

**Press:** `Space` (on a thinking block)

**Say:**
> "Thinking blocks can be expanded with Space to see the full internal reasoning."

**Press:** `↑` (scroll up)

---

### Act 5: Navigation (30 seconds)

**Press:** `Esc` (back to Layer 3)

**Say:**
> "Escape key navigates back through the layers."

**Press:** `Esc` (back to Layer 2)

**Say:**
> "Back to the agent list."

**Press:** `Esc` (back to Layer 1)

**Say:**
> "And back to the session overview. The navigation is hierarchical and reversible."

---

### Act 6: Help System (15 seconds)

**Press:** `h` (show help)

**Say:**
> "The help system is context-aware. At Layer 1, it shows session-level shortcuts."

**Press:** `Enter` (go to Layer 2)
**Press:** `h` (show help)

**Say:**
> "At Layer 2, it shows agent selection shortcuts. Each layer has its own help."

**Press:** `h` (close help)

---

### Finale (10 seconds)

**Press:** `q` (quit)

**Say:**
> "And pressing 'q' from any layer quits the dashboard cleanly, restoring the terminal to normal state."

**Wait for clean exit**

**Say:**
> "Shannon V3.1 Interactive Dashboard - bringing htop-level visibility to AI agent execution."

---

## Demo Variations

### Variation 1: Performance Demo

Focus on Layer 4 virtual scrolling:
1. Use modified test with 1000 messages
2. Navigate to Layer 4
3. Scroll rapidly with Page Up/Down
4. Show smooth performance

### Variation 2: Multi-Agent Focus

Focus on agent selection:
1. Navigate to Layer 2
2. Rapidly switch between agents (1, 2, 3, 2, 1)
3. Show how state persists per agent
4. Drill into different agents

### Variation 3: Context Exploration

Focus on Layer 3 context:
1. Navigate to Layer 3
2. Show codebase files loaded
3. Show active memories
4. Show available tools
5. Show MCP server connections
6. Toggle panels with 't' and 'c'

---

## Recording the Demo

### With asciinema

```bash
# Start recording
asciinema rec shannon-v3.1-demo.cast

# Run dashboard
python test_dashboard_v31_live.py

# Follow demo script above

# Stop recording (quit dashboard with 'q')

# Play it back
asciinema play shannon-v3.1-demo.cast

# Upload to share
asciinema upload shannon-v3.1-demo.cast
# Get shareable URL
```

### With screen recording

```bash
# macOS - use built-in screen recording
# 1. Press Cmd+Shift+5
# 2. Select "Record Selected Portion"
# 3. Frame your terminal
# 4. Click Record
# 5. Run demo
# 6. Stop recording (menu bar)
```

---

## Talking Points

### For Technical Audience

- "Built with immutable data architecture for thread safety"
- "4 Hz refresh rate with <50ms render time"
- "Virtual scrolling provides 33x speedup for message streams"
- "Pure functional renderers - no side effects"
- "Integrates with all Shannon subsystems"

### For Product Audience

- "htop-level visibility into AI agent execution"
- "Navigate through layers of detail - session, agents, operations, messages"
- "Select and focus individual agents in multi-agent execution"
- "See exactly what context each agent has and what tools it's using"
- "Inspect the full conversation - every prompt and response"

### For Users

- "Press Enter to drill down, Escape to go back"
- "Press numbers to select different agents"
- "Press 'h' anytime for help"
- "Everything updates in real-time"

---

**Last Updated**: 2025-11-14

