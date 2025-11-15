#!/bin/bash
# Run ALL Shannon V3.1 + V3.5 Tests

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║          Shannon CLI V3.1 + V3.5 - Complete Test Suite                       ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

TOTAL=0
PASSED=0

run_test() {
    local name="$1"
    local cmd="$2"
    
    TOTAL=$((TOTAL + 1))
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "TEST $TOTAL: $name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if eval "$cmd" > /dev/null 2>&1; then
        echo "✅ PASS: $name"
        PASSED=$((PASSED + 1))
    else
        echo "❌ FAIL: $name"
        eval "$cmd"  # Run again to show error
    fi
    echo ""
}

# V3.1 Tests
run_test "V3.1 Dashboard - Interactive Navigation" \
    "python test_dashboard_interactive.py 2>&1 | grep -q 'ALL TESTS PASSED'"

# V3.5 Tests
run_test "V3.5 Core Modules - All 6 Modules" \
    "python test_all_v3.5_modules.py 2>&1 | grep -q 'ALL V3.5 MODULE TESTS PASSED'"

run_test "V3.5 Wave 1 - Prompt Injection" \
    "python test_wave1_prompt_injection.py 2>&1 | grep -q 'ALL WAVE 1 TESTS PASSED'"

run_test "V3.5 End-to-End - Complete Workflow" \
    "python test_v3.5_end_to_end.py 2>&1 | grep -q 'END-TO-END TEST PASSED'"

# Module Import Tests
run_test "V3.1 Module Imports" \
    "python -c 'import sys; sys.path.insert(0, \"src\"); from shannon.ui.dashboard_v31 import InteractiveDashboard' 2>&1"

run_test "V3.5 Module Imports" \
    "python -c 'import sys; sys.path.insert(0, \"src\"); from shannon.executor import SimpleTaskExecutor' 2>&1"

# Summary
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                            TEST SUMMARY                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Total Tests:  $TOTAL"
echo "Passed:       $PASSED"
echo "Failed:       $((TOTAL - PASSED))"
echo "Pass Rate:    $((PASSED * 100 / TOTAL))%"
echo ""

if [ $PASSED -eq $TOTAL ]; then
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║                      ✅ ALL TESTS PASSING ✅                                 ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    exit 0
else
    echo "❌ SOME TESTS FAILED"
    exit 1
fi

