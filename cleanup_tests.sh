#!/bin/bash
# Clean up redundant test files
# Keep only functional working tests

echo "Cleaning up redundant test files..."

# Remove old/redundant test files
rm -f test_dashboard_e2e.py
rm -f test_dashboard_standalone.py
rm -f test_dashboard_with_updates.py
rm -f demo_agent_control.py
rm -f test_dashboard_manual.sh
rm -f validate_v3_1.sh
rm -f VALIDATE.sh
rm -f test_all_v3_commands.sh
rm -f test_setup_system.py

echo "Removed redundant test files"

# Keep these essential tests:
# - test_dashboard_v31_live.py (demo with mocks)
# - test_dashboard_interactive.py (pexpect automation)
# - test_dashboard_tmux.sh (tmux testing)
# - test_all_v3.5_modules.py (V3.5 module tests)
# - test_wave1_prompt_injection.py (prompt tests)
# - test_v3.5_end_to_end.py (E2E test)
# - test_v3.5_exec_command.py (exec command test)
# - test_complete_v3.5.py (complete executor test)
# - RUN_DASHBOARD_DEMO.sh (easy demo)
# - RUN_ALL_TESTS.sh (run all tests)

echo ""
echo "Kept essential test files:"
ls test*.py test*.sh RUN*.sh 2>/dev/null | head -15

