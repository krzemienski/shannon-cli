#!/bin/bash
# Clean up redundant documentation files
# Keep only essential docs

echo "Cleaning up redundant documentation..."

# Keep these essential files:
# - README.md (main)
# - CHANGELOG.md (version history)
# - SHANNON_V3.1_INTERACTIVE_DASHBOARD_SPEC.md (V3.1 spec)
# - SHANNON_V3.5_REVISED_SPEC.md (V3.5 spec)
# - HONEST_REFLECTION.md (honest assessment)
# - FINAL_DELIVERY.md (final summary)

# Delete redundant status/delivery docs
rm -f ANALYTICS_PERFORMANCE_REPORT.md
rm -f ARCHITECTURE_COMPLETE.md
rm -f CACHE_IMPLEMENTATION_SUMMARY.md
rm -f COMPLETE_FUNCTIONAL_VALIDATION.md
rm -f COMPLETE_SESSION_DELIVERY.md
rm -f COMPLETION_PLAN_V3.md
rm -f COMPREHENSIVE_COMMAND_TEST.md
rm -f CONTEXT_SYSTEM_IMPLEMENTATION.md
rm -f DELIVERABLES_SUMMARY.md
rm -f DEMO_SCRIPT.md
rm -f FINAL_DELIVERY_STATUS.md
rm -f FINAL_DELIVERY_V3.1_AND_V3.5_REVISED.md
rm -f FINAL_HONEST_STATUS.md
rm -f FINAL_STATUS.md
rm -f FINAL_V3.1_STATUS.md
rm -f FINAL_VERIFICATION_V3.1.md
rm -f FUNCTIONAL_TEST_RESULTS.md
rm -f HONEST_STATUS_SUMMARY.md
rm -f IMPLEMENTATION_COMPLETE.md
rm -f MCP_AUTOMATION_COMPLETE.md
rm -f NO_MOCKS_CERTIFICATE.md
rm -f PR_DESCRIPTION.md
rm -f PR_READY.md
rm -f QUICK_START_V3.1.md
rm -f README_DELIVERY.md
rm -f README_FINAL.md
rm -f README_V3.1.md
rm -f SDK_INTEGRATION_ARCHITECTURE.md
rm -f SETUP_SYSTEM.md
rm -f SHANNON_CLI_V2_COMPLETE.md
rm -f SHANNON_CLI_V3_ARCHITECTURE.md
rm -f SHANNON_CLI_V3_DELIVERY_COMPLETE.md
rm -f SHANNON_CLI_V3_DETAILED_SPEC.md
rm -f SHANNON_CLI_V3_FINAL_STATUS.md
rm -f SHANNON_CLI_V3_PROPOSAL.md
rm -f SHANNON_V3_CLI_FUNCTIONAL_TESTING.md
rm -f SHANNON_V3_FUNCTIONAL_TESTING_AND_VALIDATION_GATES.md
rm -f SHANNON_V3_MASTER_IMPLEMENTATION_PLAN.md
rm -f SHANNON_V3_OPERATIONAL_DASHBOARD_COMPLETE.md
rm -f SHANNON_V3.1_AND_V3.5_STATUS.md
rm -f SHANNON_V3.1_COMPLETE.md
rm -f SHANNON_V3.1_DELIVERY_SUMMARY.md
rm -f SHANNON_V3.1_EXECUTIVE_SUMMARY.md
rm -f STREAMING_VISIBILITY.md
rm -f TECHNICAL_SPEC_V2.md
rm -f V2_IMPLEMENTATION_COMPLETE.md
rm -f V3_FUNCTIONAL_TEST_RESULTS.md
rm -f V3.1_DELIVERABLES.md
rm -f V3.5_COMPLETION_PLAN.md
rm -f V3.5_FINAL_TRUTH.md
rm -f V3.5_ORIGINAL_VS_REVISED.md
rm -f WAVE_3_CACHE_SYSTEM.md
rm -f WAVE_7_INTEGRATION_TESTING.md
rm -f WAVE1_AGENT1_COMPLETION_REPORT.md
rm -f WAVE1_AGENT2_COMPLETION_REPORT.md
rm -f WAVE2_AGENT1_COMPLETION_REPORT.md
rm -f WAVE3_AGENT2_COMPLETION_REPORT.md
rm -f WAVE4_INTEGRATION_TESTING_REPORT.md
rm -f WAVE4_SUMMARY.md
rm -f YOUR_QUESTIONS_ANSWERED.md
rm -f START_HERE.md
rm -f SESSION_COMPLETE.md
rm -f SHANNON_V3.5_AUTONOMOUS_EXECUTOR_SPEC.md
rm -f SHANNON_V3.5_IMPLEMENTATION_STATUS.md

echo "Removed redundant documentation files"

# Remove backup files
rm -f src/shannon/ui/dashboard_v31/*.bak*
echo "Removed backup files"

# Remove test cache
rm -rf .shannon_cache
echo "Removed test cache"

# Remove old test files
rm -f test_spec.md
rm -f actual_test.log
rm -f debug_output.log
rm -f test_output.log
echo "Removed old test/log files"

echo ""
echo "Cleanup complete!"
echo ""
echo "Kept essential files:"
echo "  - README.md"
echo "  - CHANGELOG.md"
echo "  - SHANNON_V3.1_INTERACTIVE_DASHBOARD_SPEC.md"
echo "  - SHANNON_V3.5_REVISED_SPEC.md"
echo "  - HONEST_REFLECTION.md"
echo "  - FINAL_DELIVERY.md"

