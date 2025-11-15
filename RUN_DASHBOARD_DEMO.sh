#!/bin/bash
# Shannon V3.1 Interactive Dashboard - Quick Demo
# 
# This script runs the dashboard with mock data so you can see it in action.
# Press 'q' to quit at any time.

echo "═══════════════════════════════════════════════════════════════"
echo "  Shannon V3.1 Interactive Dashboard Demo"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📊 What you'll see:"
echo "   • Layer 1: Session overview with goal and progress"
echo "   • Layer 2: List of 3 agents (press Enter to see)"
echo "   • Layer 3: Agent details with context and tools"
echo "   • Layer 4: Full message stream with scrolling"
echo ""
echo "⌨️  Keyboard shortcuts:"
echo "   • [Enter]  - Drill down into layers"
echo "   • [Esc]    - Navigate back"
echo "   • [1-3]    - Select agents (on Layer 2)"
echo "   • [↑↓]     - Scroll messages (on Layer 4)"
echo "   • [h]      - Toggle help overlay"
echo "   • [q]      - Quit dashboard"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Starting dashboard in 3 seconds..."
sleep 3

# Run the dashboard
python test_dashboard_v31_live.py

