#!/bin/bash
# Shannon V3.1 Dashboard - tmux-based Interactive Test
#
# Uses tmux to create a session, run the dashboard, and send keyboard commands.
# Captures output for verification.

set -e

echo "🧪 Shannon V3.1 Dashboard - tmux Interactive Test"
echo "================================================================"
echo ""

# Session name
SESSION="shannon-dashboard-test"

# Check if tmux is available
if ! command -v tmux &> /dev/null; then
    echo "❌ tmux not installed. Install with: brew install tmux"
    exit 1
fi

# Kill any existing session
tmux kill-session -t "$SESSION" 2>/dev/null || true

echo "🚀 Creating tmux session and launching dashboard..."

# Create new session and run dashboard
tmux new-session -d -s "$SESSION" -x 120 -y 40

# Run the dashboard in the session
tmux send-keys -t "$SESSION" "cd $(pwd) && python test_dashboard_v31_live.py" C-m

# Wait for dashboard to start
echo "⏳ Waiting for dashboard to initialize (5 seconds)..."
sleep 5

echo ""
echo "================================================================"
echo "TEST 1: Navigate Layer 1 → Layer 2 (press Enter)"
echo "================================================================"
tmux send-keys -t "$SESSION" "" C-m  # Send Enter
sleep 1

echo ""
echo "================================================================"
echo "TEST 2: Select Agent #2 (press '2')"
echo "================================================================"
tmux send-keys -t "$SESSION" "2"
sleep 1

echo ""
echo "================================================================"
echo "TEST 3: Navigate Layer 2 → Layer 3 (press Enter)"
echo "================================================================"
tmux send-keys -t "$SESSION" "" C-m
sleep 1

echo ""
echo "================================================================"
echo "TEST 4: Navigate Layer 3 → Layer 4 (press Enter)"
echo "================================================================"
tmux send-keys -t "$SESSION" "" C-m
sleep 1

echo ""
echo "================================================================"
echo "TEST 5: Scroll messages (press Down arrow 3 times)"
echo "================================================================"
tmux send-keys -t "$SESSION" Down Down Down
sleep 1

echo ""
echo "================================================================"
echo "TEST 6: Navigate back Layer 4 → Layer 3 (press Esc)"
echo "================================================================"
tmux send-keys -t "$SESSION" Escape
sleep 1

echo ""
echo "================================================================"
echo "TEST 7: Toggle help overlay (press 'h' twice)"
echo "================================================================"
tmux send-keys -t "$SESSION" "h"
sleep 1
tmux send-keys -t "$SESSION" "h"
sleep 1

echo ""
echo "================================================================"
echo "TEST 8: Quit dashboard (press 'q')"
echo "================================================================"
tmux send-keys -t "$SESSION" "q"
sleep 2

# Capture final output
echo ""
echo "================================================================"
echo "📸 Capturing dashboard output..."
echo "================================================================"
tmux capture-pane -t "$SESSION" -p > dashboard_test_output.txt

echo ""
echo "✅ Test complete!"
echo "Dashboard output saved to: dashboard_test_output.txt"
echo ""
echo "To view the output:"
echo "  cat dashboard_test_output.txt"
echo ""
echo "To manually inspect the session:"
echo "  tmux attach -t $SESSION"
echo ""
echo "To kill the session:"
echo "  tmux kill-session -t $SESSION"
echo ""

# Kill session
tmux kill-session -t "$SESSION"

echo "✅ Session cleaned up"

