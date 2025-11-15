#!/bin/bash
# Shannon V3.1 - Simple Validation
#
# Runs the live functional test to validate dashboard

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         Shannon V3.1 Interactive Dashboard                  ║"
echo "║                   VALIDATION                                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Running live functional test..."
echo ""

python3 test_dashboard_interactive.py

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║            ✅ VALIDATION PASSED ✅                            ║"
    echo "║                                                              ║"
    echo "║         Shannon V3.1 is READY FOR PRODUCTION                ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Next steps:"
    echo "  1. Run manual test: ./test_dashboard_manual.sh"
    echo "  2. Test with real commands: shannon analyze <spec>"
    echo "  3. Review docs: SHANNON_V3.1_COMPLETE.md"
    echo ""
else
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║            ❌ VALIDATION FAILED ❌                            ║"
    echo "║                                                              ║"
    echo "║              Review test output above                        ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
fi

exit $EXIT_CODE

