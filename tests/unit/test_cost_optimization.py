"""Unit Tests for Cost Optimization Pure Functions

Tests pure mathematical and logical functions in cost optimization subsystem.

Philosophy: NO MOCKS (but these are unit tests of pure functions)
- Mathematical calculations
- Model selection logic
- Cost estimation formulas
- Budget calculations

Architecture Reference: SHANNON_CLI_V3_ARCHITECTURE.md Section 2.5
"""

import pytest
from shannon.optimization.model_selector import ModelSelector, ModelSelection
from shannon.optimization.cost_estimator import CostEstimator, CostEstimate
from shannon.optimization.budget_enforcer import BudgetEnforcer, BudgetStatus


# ============================================================================
# MODEL SELECTOR UNIT TESTS
# ============================================================================

@pytest.mark.unit
def test_model_selector_simple_task():
    """
    Test model selection for simple tasks (complexity < 0.30)

    Expected: haiku (cheapest model)
    """
    selector = ModelSelector()

    selection = selector.select_optimal_model(
        complexity_score=0.25,  # Simple
        context_size=10000,     # Small context
        budget_remaining=100.0   # Ample budget
    )

    assert selection.selected_model == "haiku", \
        "Simple tasks should use haiku model"
    assert selection.savings_vs_baseline > 0, \
        "Haiku should save money vs sonnet baseline"


@pytest.mark.unit
def test_model_selector_complex_task():
    """
    Test model selection for complex tasks (complexity >= 0.60)

    Expected: sonnet or sonnet[1m] (depending on context size)
    """
    selector = ModelSelector()

    # Complex task with small context
    selection1 = selector.select_optimal_model(
        complexity_score=0.70,
        context_size=50000,      # Small context
        budget_remaining=100.0
    )

    assert selection1.selected_model in ["sonnet", "sonnet[1m]"], \
        "Complex tasks should use sonnet"

    # Complex task with large context
    selection2 = selector.select_optimal_model(
        complexity_score=0.70,
        context_size=500000,     # Large context (500K tokens)
        budget_remaining=100.0
    )

    assert selection2.selected_model == "sonnet[1m]", \
        "Large context should require sonnet[1m]"


@pytest.mark.unit
def test_model_selector_large_context_forces_1m():
    """
    Test that large context (>200K tokens) forces sonnet[1m]

    Hard constraint: Only sonnet[1m] supports >200K context
    """
    selector = ModelSelector()

    selection = selector.select_optimal_model(
        complexity_score=0.30,   # Even moderate complexity
        context_size=300000,     # 300K tokens (requires 1M model)
        budget_remaining=100.0
    )

    assert selection.selected_model == "sonnet[1m]", \
        "Context >200K must use sonnet[1m]"


@pytest.mark.unit
def test_model_selector_budget_constraint():
    """
    Test that low budget forces cheaper model

    Expected: haiku when budget < $1
    """
    selector = ModelSelector()

    selection = selector.select_optimal_model(
        complexity_score=0.50,   # Would normally use sonnet
        context_size=50000,
        budget_remaining=0.50    # Low budget forces downgrade
    )

    assert selection.selected_model == "haiku", \
        "Low budget should force haiku model"


@pytest.mark.unit
def test_model_selector_moderate_complexity():
    """
    Test model selection for moderate complexity (0.30-0.60)

    Expected: Depends on context size and budget
    """
    selector = ModelSelector()

    # Moderate + small context = haiku
    selection1 = selector.select_optimal_model(
        complexity_score=0.45,
        context_size=30000,
        budget_remaining=100.0
    )

    assert selection1.selected_model in ["haiku", "sonnet"], \
        "Moderate complexity with small context can be haiku or sonnet"

    # Moderate + large context + good budget = sonnet
    selection2 = selector.select_optimal_model(
        complexity_score=0.45,
        context_size=150000,
        budget_remaining=50.0
    )

    # Should prefer sonnet for quality with large context
    assert selection2.selected_model in ["sonnet", "sonnet[1m]"]


# ============================================================================
# COST ESTIMATOR UNIT TESTS
# ============================================================================

@pytest.mark.unit
def test_cost_estimator_haiku_pricing():
    """
    Test cost calculation for haiku model

    Haiku pricing: ~$0.00025 input, ~$0.00125 output (per 1K tokens)
    """
    estimator = CostEstimator()

    estimate = estimator.estimate_cost(
        input_tokens=10000,   # 10K tokens
        output_tokens=5000,   # 5K tokens
        model="haiku"
    )

    # Expected:
    # Input: 10 * 0.00025 = $0.0025
    # Output: 5 * 0.00125 = $0.00625
    # Total: $0.00875
    expected = (10 * 0.00025) + (5 * 0.00125)

    assert abs(estimate.total_cost - expected) < 0.0001, \
        f"Haiku cost ${estimate.total_cost:.5f} should be ~${expected:.5f}"


@pytest.mark.unit
def test_cost_estimator_sonnet_pricing():
    """
    Test cost calculation for sonnet model

    Sonnet pricing: ~$0.003 input, ~$0.015 output (per 1K tokens)
    """
    estimator = CostEstimator()

    estimate = estimator.estimate_cost(
        input_tokens=10000,
        output_tokens=5000,
        model="sonnet"
    )

    # Expected:
    # Input: 10 * 0.003 = $0.03
    # Output: 5 * 0.015 = $0.075
    # Total: $0.105
    expected = (10 * 0.003) + (5 * 0.015)

    assert abs(estimate.total_cost - expected) < 0.001, \
        f"Sonnet cost ${estimate.total_cost:.3f} should be ~${expected:.3f}"


@pytest.mark.unit
def test_cost_estimator_savings_calculation():
    """
    Test savings calculation between models

    haiku vs sonnet should show significant savings
    """
    estimator = CostEstimator()

    tokens_input = 10000
    tokens_output = 5000

    haiku_cost = estimator.estimate_cost(tokens_input, tokens_output, "haiku")
    sonnet_cost = estimator.estimate_cost(tokens_input, tokens_output, "sonnet")

    savings = sonnet_cost.total_cost - haiku_cost.total_cost
    savings_percent = (savings / sonnet_cost.total_cost) * 100

    # haiku should be ~90% cheaper than sonnet
    assert savings > 0, "haiku should be cheaper than sonnet"
    assert savings_percent > 80, \
        f"haiku should save >80% vs sonnet, got {savings_percent:.0f}%"


@pytest.mark.unit
def test_cost_estimator_spec_analysis_estimation():
    """
    Test cost estimation for spec analysis

    Validates estimation logic for analysis operations
    """
    estimator = CostEstimator()

    # Simple spec
    estimate_simple = estimator.estimate_spec_analysis(
        spec_text="Add login button",
        has_context=False
    )

    assert estimate_simple.total_cost > 0
    assert estimate_simple.input_tokens > 0

    # Complex spec (more tokens)
    complex_spec = "Add authentication system" * 100  # Long spec
    estimate_complex = estimator.estimate_spec_analysis(
        spec_text=complex_spec,
        has_context=False
    )

    # Complex should cost more
    assert estimate_complex.total_cost > estimate_simple.total_cost


@pytest.mark.unit
def test_cost_estimator_context_overhead():
    """
    Test that context adds to cost estimation

    With context should have higher input tokens
    """
    estimator = CostEstimator()

    spec = "Add new feature"

    # Without context
    estimate_no_context = estimator.estimate_spec_analysis(
        spec_text=spec,
        has_context=False
    )

    # With context
    estimate_with_context = estimator.estimate_spec_analysis(
        spec_text=spec,
        has_context=True
    )

    # Context should add tokens (and cost)
    assert estimate_with_context.input_tokens >= estimate_no_context.input_tokens


# ============================================================================
# BUDGET ENFORCER UNIT TESTS
# ============================================================================

@pytest.mark.unit
def test_budget_enforcer_initialization(temp_config_dir):
    """
    Test BudgetEnforcer initialization

    Validates:
    - Budget loaded from config
    - Default values correct
    """
    enforcer = BudgetEnforcer(config_dir=temp_config_dir)

    # Should initialize with 0 spent
    status = enforcer.get_status()

    assert status.total_budget >= 0
    assert status.spent == 0.0
    assert status.remaining == status.total_budget


@pytest.mark.unit
def test_budget_enforcer_set_budget(temp_config_dir):
    """
    Test setting budget

    Validates:
    - Budget set correctly
    - Persisted to disk
    """
    enforcer = BudgetEnforcer(config_dir=temp_config_dir)

    enforcer.set_budget(50.0)

    status = enforcer.get_status()

    assert status.total_budget == 50.0
    assert status.remaining == 50.0


@pytest.mark.unit
def test_budget_enforcer_record_spending(temp_config_dir):
    """
    Test recording spending

    Validates:
    - Spent amount tracked
    - Remaining calculated correctly
    """
    enforcer = BudgetEnforcer(config_dir=temp_config_dir)

    enforcer.set_budget(10.0)

    # Record some spending
    enforcer.record_cost(2.50, "analysis")
    enforcer.record_cost(1.75, "wave")

    status = enforcer.get_status()

    assert status.spent == 4.25
    assert abs(status.remaining - 5.75) < 0.01


@pytest.mark.unit
def test_budget_enforcer_check_available(temp_config_dir):
    """
    Test checking budget availability

    Validates:
    - Returns True if budget available
    - Returns False if would exceed
    """
    enforcer = BudgetEnforcer(config_dir=temp_config_dir)

    enforcer.set_budget(10.0)
    enforcer.record_cost(8.0, "previous")

    # $2 remaining

    # Small operation should be OK
    assert enforcer.check_available(1.0) == True, \
        "$1 operation should be allowed with $2 remaining"

    # Large operation should be blocked
    assert enforcer.check_available(5.0) == False, \
        "$5 operation should be blocked with only $2 remaining"


@pytest.mark.unit
def test_budget_enforcer_percentage_used(temp_config_dir):
    """
    Test percentage used calculation

    Validates:
    - Percentage calculated correctly
    - Range 0-100%
    """
    enforcer = BudgetEnforcer(config_dir=temp_config_dir)

    enforcer.set_budget(100.0)
    enforcer.record_cost(25.0, "test")

    status = enforcer.get_status()

    assert status.percent_used == 25.0, \
        "Should be 25% used ($25 of $100)"

    # Record more
    enforcer.record_cost(50.0, "test2")

    status2 = enforcer.get_status()

    assert status2.percent_used == 75.0, \
        "Should be 75% used ($75 of $100)"


@pytest.mark.unit
def test_budget_enforcer_no_budget_set(temp_config_dir):
    """
    Test behavior when no budget set

    Expected: All operations allowed (unlimited budget)
    """
    enforcer = BudgetEnforcer(config_dir=temp_config_dir)

    # No budget set (default 0 or unlimited)

    # Should allow any amount
    assert enforcer.check_available(1000.0) == True, \
        "Should allow operation when no budget set"


@pytest.mark.unit
def test_budget_enforcer_persistence(temp_config_dir):
    """
    Test budget persistence across instances

    Validates:
    - Budget saved to disk
    - Spending saved to disk
    - Reloaded correctly
    """
    # First instance
    enforcer1 = BudgetEnforcer(config_dir=temp_config_dir)
    enforcer1.set_budget(50.0)
    enforcer1.record_cost(10.0, "test")

    # Second instance (should load from disk)
    enforcer2 = BudgetEnforcer(config_dir=temp_config_dir)

    status2 = enforcer2.get_status()

    assert status2.total_budget == 50.0, \
        "Budget should persist"
    assert status2.spent == 10.0, \
        "Spending should persist"


# ============================================================================
# INTEGRATION OF OPTIMIZATION COMPONENTS
# ============================================================================

@pytest.mark.unit
def test_cost_optimization_pipeline():
    """
    Test complete cost optimization pipeline

    Flow: Estimate → Select Model → Check Budget → Record Cost

    Validates:
    - Components work together
    - Decisions are optimal
    """
    estimator = CostEstimator()
    selector = ModelSelector()

    # Scenario: Moderate complexity task
    complexity = 0.45
    context_size = 50000
    budget_remaining = 10.0

    # Step 1: Select optimal model
    selection = selector.select_optimal_model(
        complexity_score=complexity,
        context_size=context_size,
        budget_remaining=budget_remaining
    )

    # Step 2: Estimate cost for selected model
    estimate = estimator.estimate_cost(
        input_tokens=50000,
        output_tokens=10000,
        model=selection.selected_model
    )

    # Step 3: Verify cost within budget
    assert estimate.total_cost <= budget_remaining, \
        "Selected model should be within budget"

    # Step 4: Verify savings if haiku selected
    if selection.selected_model == "haiku":
        assert selection.savings_vs_baseline > 0, \
            "haiku should show cost savings"


@pytest.mark.unit
def test_model_cost_ranking():
    """
    Test that models are correctly ranked by cost

    Expected: haiku < sonnet < opus
    """
    estimator = CostEstimator()

    tokens_in = 10000
    tokens_out = 5000

    haiku_cost = estimator.estimate_cost(tokens_in, tokens_out, "haiku").total_cost
    sonnet_cost = estimator.estimate_cost(tokens_in, tokens_out, "sonnet").total_cost

    # Cost ranking
    assert haiku_cost < sonnet_cost, \
        "haiku should be cheaper than sonnet"

    # Specific ratios
    ratio = sonnet_cost / haiku_cost
    assert ratio > 5, \
        f"sonnet should be >5x more expensive than haiku, got {ratio:.1f}x"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
