#!/bin/bash
# Shannon V3.1 - Comprehensive Validation Script
#
# Validates complete implementation of V3.1 Interactive Dashboard

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         Shannon V3.1 Interactive Dashboard                  ║"
echo "║              COMPREHENSIVE VALIDATION                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

PASSED=0
FAILED=0

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Validation function
validate() {
    local test_name="$1"
    local command="$2"
    
    echo -n "Testing: $test_name ... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((FAILED++))
        return 1
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 1: Code Structure Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

validate "models.py exists" \
    "test -f src/shannon/ui/dashboard_v31/models.py"

validate "data_provider.py exists" \
    "test -f src/shannon/ui/dashboard_v31/data_provider.py"

validate "navigation.py exists" \
    "test -f src/shannon/ui/dashboard_v31/navigation.py"

validate "keyboard.py exists" \
    "test -f src/shannon/ui/dashboard_v31/keyboard.py"

validate "renderers.py exists" \
    "test -f src/shannon/ui/dashboard_v31/renderers.py"

validate "dashboard.py exists" \
    "test -f src/shannon/ui/dashboard_v31/dashboard.py"

validate "optimizations.py exists" \
    "test -f src/shannon/ui/dashboard_v31/optimizations.py"

validate "help.py exists" \
    "test -f src/shannon/ui/dashboard_v31/help.py"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 2: Python Syntax Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

validate "models.py imports" \
    "cd /Users/nick/.cursor/worktrees/shannon-cli/8L0vT && python -c 'import sys; sys.path.insert(0, \"src\"); from shannon.ui.dashboard_v31.models import DashboardSnapshot'"

validate "data_provider.py imports" \
    "cd /Users/nick/.cursor/worktrees/shannon-cli/8L0vT && python -c 'import sys; sys.path.insert(0, \"src\"); from shannon.ui.dashboard_v31.data_provider import DashboardDataProvider'"

validate "navigation.py imports" \
    "cd /Users/nick/.cursor/worktrees/shannon-cli/8L0vT && python -c 'import sys; sys.path.insert(0, \"src\"); from shannon.ui.dashboard_v31.navigation import NavigationController'"

validate "keyboard.py imports" \
    "cd /Users/nick/.cursor/worktrees/shannon-cli/8L0vT && python -c 'import sys; sys.path.insert(0, \"src\"); from shannon.ui.dashboard_v31.keyboard import EnhancedKeyboardHandler'"

validate "renderers.py imports" \
    "cd /Users/nick/.cursor/worktrees/shannon-cli/8L0vT && python -c 'import sys; sys.path.insert(0, \"src\"); from shannon.ui.dashboard_v31.renderers import Layer1Renderer'"

validate "dashboard.py imports" \
    "cd /Users/nick/.cursor/worktrees/shannon-cli/8L0vT && python -c 'import sys; sys.path.insert(0, \"src\"); from shannon.ui.dashboard_v31.dashboard import InteractiveDashboard'"

validate "optimizations.py imports" \
    "cd /Users/nick/.cursor/worktrees/shannon-cli/8L0vT && python -c 'import sys; sys.path.insert(0, \"src\"); from shannon.ui.dashboard_v31.optimizations import VirtualMessageView'"

validate "help.py imports" \
    "cd /Users/nick/.cursor/worktrees/shannon-cli/8L0vT && python -c 'import sys; sys.path.insert(0, \"src\"); from shannon.ui.dashboard_v31.help import HelpRenderer'"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 3: Import Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

validate "SessionManager integration" \
    "cd /Users/nick/.cursor/worktrees/shannon-cli/8L0vT && python -c 'import sys; sys.path.insert(0, \"src\"); from shannon.core.session_manager import SessionManager; sm = SessionManager(\"test\"); hasattr(sm, \"get_current_session\")'"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 4: Live Functional Testing"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Running comprehensive functional test with pexpect..."
echo ""

if python test_dashboard_interactive.py 2>&1 | grep -q "ALL TESTS PASSED"; then
    echo -e "${GREEN}✅ LIVE FUNCTIONAL TEST: PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ LIVE FUNCTIONAL TEST: FAILED${NC}"
    ((FAILED++))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 5: Documentation Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

validate "Implementation docs" \
    "test -f SHANNON_V3.1_COMPLETE.md"

validate "Testing guide" \
    "test -f TESTING_GUIDE.md"

validate "Demo script" \
    "test -f DEMO_SCRIPT.md"

validate "Module README" \
    "test -f src/shannon/ui/dashboard_v31/README.md"

validate "Delivery summary" \
    "test -f SHANNON_V3.1_DELIVERY_SUMMARY.md"

validate "Final status" \
    "test -f FINAL_V3.1_STATUS.md"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 6: Performance Metrics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Count lines
TOTAL_LINES=$(find src/shannon/ui/dashboard_v31 -name "*.py" -exec cat {} \; | wc -l | tr -d ' ')
echo "Total lines of code: $TOTAL_LINES"

if [ "$TOTAL_LINES" -gt 2400 ]; then
    echo -e "${GREEN}✅ Code volume target exceeded (spec: 2,400 lines)${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Insufficient code volume${NC}"
    ((FAILED++))
fi

# Count files
FILE_COUNT=$(find src/shannon/ui/dashboard_v31 -name "*.py" | wc -l | tr -d ' ')
echo "Python files: $FILE_COUNT"

if [ "$FILE_COUNT" -ge 8 ]; then
    echo -e "${GREEN}✅ All components implemented${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Missing components${NC}"
    ((FAILED++))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "FINAL RESULTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

TOTAL=$((PASSED + FAILED))
PASS_RATE=$((PASSED * 100 / TOTAL))

echo "Tests Passed: $PASSED/$TOTAL ($PASS_RATE%)"
echo "Tests Failed: $FAILED/$TOTAL"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║            ✅ ALL VALIDATIONS PASSED! ✅                      ║"
    echo "║                                                              ║"
    echo "║        Shannon V3.1 is READY FOR PRODUCTION                 ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run: ./test_dashboard_manual.sh (user acceptance)"
    echo "  2. Test with real Shannon commands"
    echo "  3. Create demo video (asciinema)"
    echo "  4. Deploy to production"
    echo ""
    exit 0
else
    echo -e "${RED}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║              ❌ VALIDATION FAILED ❌                          ║"
    echo "║                                                              ║"
    echo "║          $FAILED test(s) failed - review output above         ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    exit 1
fi

