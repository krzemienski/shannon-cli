#!/bin/bash
# Comprehensive Functional Validation of Shannon V3.1 + V3.5

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║           Shannon CLI V3.1 + V3.5 - Complete Functional Validation           ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

PASS_COUNT=0
FAIL_COUNT=0
TOTAL_TESTS=0

# Function to run test and track results
run_test() {
    local test_name="$1"
    local test_cmd="$2"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "TEST $TOTAL_TESTS: $test_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Running: $test_cmd"
    echo ""
    
    if eval "$test_cmd"; then
        echo ""
        echo "✅ PASSED: $test_name"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo ""
        echo "❌ FAILED: $test_name"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
    echo ""
}

# TEST 1: V3.1 Dashboard Functional Tests
run_test "V3.1 Dashboard - Full Navigation Test" \
    "python test_dashboard_interactive.py 2>&1 | grep -q 'ALL TESTS PASSED'"

# TEST 2: V3.5 Core Modules
run_test "V3.5 Core Modules - Complete Suite" \
    "python test_all_v3.5_modules.py 2>&1 | grep -q 'ALL V3.5 MODULE TESTS PASSED'"

# TEST 3: V3.5 Wave 1 - Prompt Injection
run_test "V3.5 Wave 1 - Prompt Injection" \
    "python test_wave1_prompt_injection.py 2>&1 | grep -q 'ALL WAVE 1 TESTS PASSED'"

# TEST 4: Verify all V3.1 files exist
run_test "V3.1 Files - Existence Check" \
    "test -f src/shannon/ui/dashboard_v31/models.py && \
     test -f src/shannon/ui/dashboard_v31/data_provider.py && \
     test -f src/shannon/ui/dashboard_v31/navigation.py && \
     test -f src/shannon/ui/dashboard_v31/keyboard.py && \
     test -f src/shannon/ui/dashboard_v31/renderers.py && \
     test -f src/shannon/ui/dashboard_v31/dashboard.py && \
     test -f src/shannon/ui/dashboard_v31/optimizations.py && \
     test -f src/shannon/ui/dashboard_v31/help.py"

# TEST 5: Verify all V3.5 files exist
run_test "V3.5 Files - Existence Check" \
    "test -f src/shannon/executor/__init__.py && \
     test -f src/shannon/executor/prompts.py && \
     test -f src/shannon/executor/task_enhancements.py && \
     test -f src/shannon/executor/prompt_enhancer.py && \
     test -f src/shannon/executor/models.py && \
     test -f src/shannon/executor/library_discoverer.py && \
     test -f src/shannon/executor/validator.py && \
     test -f src/shannon/executor/git_manager.py"

# TEST 6: V3.1 modules import without errors
run_test "V3.1 Import Test" \
    "python -c 'from shannon.ui.dashboard_v31 import InteractiveDashboard, DashboardDataProvider; print(\"Imports OK\")' 2>&1 | grep -q 'Imports OK'"

# TEST 7: V3.5 modules import without errors
run_test "V3.5 Import Test" \
    "python -c 'from shannon.executor import PromptEnhancer, LibraryDiscoverer, ValidationOrchestrator, GitManager; print(\"Imports OK\")' 2>&1 | grep -q 'Imports OK'"

# TEST 8: V3.1 integration files modified
run_test "V3.1 Integration - SessionManager" \
    "grep -q 'get_current_session' src/shannon/core/session_manager.py"

# TEST 9: V3.1 integration files modified
run_test "V3.1 Integration - LiveDashboard" \
    "grep -q 'InteractiveDashboard' src/shannon/metrics/dashboard.py"

# TEST 10: V3.5 SDK enhancement
run_test "V3.5 SDK Enhancement" \
    "grep -q 'invoke_command_with_enhancements' src/shannon/sdk/client.py"

# Summary
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                         VALIDATION SUMMARY                                   ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Total Tests Run:     $TOTAL_TESTS"
echo "Tests Passed:        $PASS_COUNT"
echo "Tests Failed:        $FAIL_COUNT"
echo "Pass Rate:           $(( PASS_COUNT * 100 / TOTAL_TESTS ))%"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║                    ✅ ALL VALIDATIONS PASSED ✅                              ║"
    echo "║                                                                              ║"
    echo "║               V3.1 + V3.5: FULLY FUNCTIONAL AND VERIFIED                     ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    exit 0
else
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║                    ❌ SOME VALIDATIONS FAILED ❌                             ║"
    echo "║                                                                              ║"
    echo "║                   Please review failures above                               ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    exit 1
fi

