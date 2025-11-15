# Shannon V3.1 Dashboard - Testing Guide

## Quick Start

```bash
# Method 1: Automated functional test (recommended)
python test_dashboard_interactive.py

# Method 2: Manual interactive test
./test_dashboard_manual.sh

# Method 3: tmux automation (if tmux installed)
./test_dashboard_tmux.sh
```

---

## Method 1: Automated Functional Testing (pexpect)

### What It Does

The `test_dashboard_interactive.py` script:
1. Spawns the dashboard in a pseudo-terminal
2. Sends actual keyboard commands (Enter, Esc, numbers, arrows)
3. Verifies dashboard responds correctly
4. Tests all 4 layers of navigation
5. Captures and displays output

### Running the Test

```bash
cd /Users/nick/.cursor/worktrees/shannon-cli/8L0vT
python test_dashboard_interactive.py
```

### Expected Output

```
🧪 Shannon V3.1 Interactive Dashboard Test
============================================================

This test will:
  1. Launch the dashboard with mock data
  2. Simulate keyboard inputs to test navigation
  3. Verify all 4 layers are accessible
  4. Capture output for verification

🚀 Launching dashboard...
⏳ Waiting for dashboard to start...
✅ Dashboard started successfully!

============================================================
TEST 1: Navigate Layer 1 → Layer 2 (press Enter)
============================================================
✓ PASSED

[... 7 more tests ...]

============================================================
✅ ALL TESTS PASSED!
============================================================

Dashboard successfully:
  ✓ Launched with mock data
  ✓ Navigated Layer 1 → Layer 2 → Layer 3 → Layer 4
  ✓ Selected different agents
  ✓ Scrolled message stream
  ✓ Navigated backwards
  ✓ Toggled help overlay
  ✓ Quit cleanly
```

### What Gets Tested

| Test | Keyboard Input | What It Verifies |
|------|----------------|------------------|
| 1 | Enter | Layer 1 → Layer 2 navigation |
| 2 | '2' | Agent #2 selection |
| 3 | Enter | Layer 2 → Layer 3 navigation |
| 4 | Enter | Layer 3 → Layer 4 navigation |
| 5 | ↓↓ | Message scrolling |
| 6 | Esc | Layer 4 → Layer 3 back navigation |
| 7 | 'h' twice | Help overlay toggle |
| 8 | 'q' | Clean dashboard exit |

### Requirements

- Python 3.7+
- pexpect library (auto-installed if missing)
- Unix/macOS (uses termios)

---

## Method 2: Manual Interactive Testing

### Running Manual Test

```bash
./test_dashboard_manual.sh
```

### Testing Checklist

The script displays a comprehensive checklist. Work through each item:

#### Layer 1 (Session Overview)
- [ ] Goal displays: "Build full-stack SaaS application"
- [ ] Wave shows: "Wave 1/5: Wave 1: Core Implementation"
- [ ] Progress bar renders with ▓░ characters
- [ ] Agent summary: "2 active, 1 complete"
- [ ] Metrics show: $0.00 | 0 tokens | 0s | 0 msgs
- [ ] Press [Enter] to navigate

#### Layer 2 (Agent List)
- [ ] Table displays with 3 agents
- [ ] Columns: #, Type, Progress, State, Time, Blocking
- [ ] Press [1] - Agent #1 highlighted
- [ ] Press [2] - Agent #2 highlighted
- [ ] Press [3] - Agent #3 highlighted
- [ ] Footer shows: "Selected: Agent #agent-X"
- [ ] Press [Enter] to view details

#### Layer 3 (Agent Detail)
- [ ] Top panel shows agent info and task
- [ ] Left panel shows context (codebase, memory, tools, MCP)
- [ ] Right panel shows tool history (file operations)
- [ ] Bottom panel shows current operation
- [ ] Press [t] - tool history toggles off/on
- [ ] Press [c] - context panel toggles off/on
- [ ] Press [1-3] - switches agents (stays on Layer 3)
- [ ] Press [Enter] to view messages

#### Layer 4 (Message Stream)
- [ ] Messages displayed with syntax highlighting
- [ ] USER messages shown in blue with →
- [ ] ASSISTANT messages shown in green with ←
- [ ] TOOL_USE messages shown in yellow
- [ ] Press [↑] - scrolls up
- [ ] Press [↓] - scrolls down
- [ ] Press [Esc] - back to Layer 3

#### Help System
- [ ] Press [h] - help overlay appears
- [ ] Help shows current layer
- [ ] Help shows relevant shortcuts
- [ ] Press [h] again - help closes

#### Exit
- [ ] Press [q] - dashboard quits cleanly
- [ ] Terminal restored to normal state

---

## Method 3: tmux Automation

### Requirements

```bash
# Install tmux if not available
brew install tmux  # macOS
apt-get install tmux  # Linux
```

### Running tmux Test

```bash
./test_dashboard_tmux.sh
```

### What It Does

1. Creates a tmux session named `shannon-dashboard-test`
2. Launches dashboard in the session
3. Sends keyboard commands via `tmux send-keys`
4. Captures output to `dashboard_test_output.txt`
5. Cleans up session

### Viewing Results

```bash
# View captured output
cat dashboard_test_output.txt

# Manually attach to session (if you stopped it early)
tmux attach -t shannon-dashboard-test

# Kill session
tmux kill-session -t shannon-dashboard-test
```

---

## Troubleshooting

### Error: "Operation not supported by device"

**Problem**: Running in non-interactive environment (pipe, redirect, CI/CD)

**Solution**: Dashboard requires a real interactive terminal. Run directly in terminal, not piped.

```bash
# ❌ Won't work
python test_dashboard_v31_live.py | tee output.log

# ✅ Will work
python test_dashboard_v31_live.py
```

### Error: "pexpect not installed"

**Problem**: pexpect library missing

**Solution**: Script auto-installs, or install manually:

```bash
pip install pexpect
```

### Error: Dashboard doesn't respond to keyboard

**Problem**: Terminal not in raw mode

**Solution**: Ensure running in a proper terminal (iTerm2, Terminal.app, Alacritty, tmux)

### Dashboard crashes immediately

**Problem**: Missing required managers

**Solution**: The test script includes mock managers. If using real Shannon, ensure all managers are initialized:

```python
dashboard = InteractiveDashboard(
    metrics=metrics_collector,      # Required
    agents=agent_state_tracker,     # Optional (enables Layer 2)
    context=context_manager,         # Optional (enables context panel)
    session=session_manager          # Optional (enables goal display)
)
```

---

## Advanced Testing

### Test with Real Shannon Commands

```bash
# Run actual shannon command with V3.1 dashboard
shannon analyze complex_spec.md

# The dashboard will:
# - Show real metrics
# - Display actual agent execution
# - Show real message stream
# - Update in real-time at 4 Hz
```

### Recording Session with asciinema

```bash
# Install asciinema
brew install asciinema

# Record dashboard session
asciinema rec shannon-v3.1-demo.cast

# Run dashboard
python test_dashboard_v31_live.py

# Navigate through layers, then quit

# Play recording
asciinema play shannon-v3.1-demo.cast

# Share recording
asciinema upload shannon-v3.1-demo.cast
```

### Performance Testing

```bash
# Test with 1000 messages (Layer 4 virtual scrolling)
# Modify test_dashboard_v31_live.py to add 1000 messages to agent-1

# Run and verify:
# - Smooth scrolling
# - <50ms render time
# - No lag or stutter
```

---

## Acceptance Criteria

### Must Pass

- ✅ Dashboard launches without errors
- ✅ Layer 1 displays session overview
- ✅ Layer 2 shows agent table (multi-agent execution)
- ✅ Layer 3 shows agent details with 4 panels
- ✅ Layer 4 shows message stream (when messages available)
- ✅ Keyboard navigation works (Enter, Esc, 1-9, arrows)
- ✅ Help overlay displays (press 'h')
- ✅ Dashboard quits cleanly (press 'q')

### Performance Targets

- ✅ 4 Hz refresh rate maintained
- ✅ <50ms render time per frame
- ✅ Smooth scrolling in Layer 4
- ✅ <200MB memory usage
- ✅ No visible lag or stutter

---

## Continuous Testing

### Pre-Commit Hook

```bash
# Add to .git/hooks/pre-commit
#!/bin/bash
echo "Running dashboard functional tests..."
python test_dashboard_interactive.py

if [ $? -ne 0 ]; then
    echo "❌ Dashboard tests failed!"
    exit 1
fi

echo "✅ Dashboard tests passed"
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Test Dashboard (Headless)
  run: |
    # Dashboard requires interactive terminal
    # Use script to create pseudo-TTY
    script -q -c "AUTOMATED_TEST=1 python test_dashboard_v31_live.py" /dev/null
```

---

## Contact & Support

- **Documentation**: See `SHANNON_V3.1_COMPLETE.md`
- **Spec**: See `SHANNON_V3.1_INTERACTIVE_DASHBOARD_SPEC.md`
- **Issues**: File bugs with terminal output attached

---

**Last Updated**: 2025-11-14  
**Version**: 3.1.0

