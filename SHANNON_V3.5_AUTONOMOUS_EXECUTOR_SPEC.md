# Shannon CLI V3.5 - Autonomous Executor Specification

**Version**: 3.5.0
**Date**: November 15, 2025
**Status**: Design Specification
**Document Size**: ~3,000 lines
**Philosophy**: Natural language → Working code with zero manual intervention

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Part 1: User Experience](#part-1-user-experience)
3. [Part 2: System Architecture](#part-2-system-architecture)
4. [Part 3: Auto-Priming System](#part-3-auto-priming-system)
5. [Part 4: Research-Informed Planning](#part-4-research-informed-planning)
6. [Part 5: Execution Engine](#part-5-execution-engine)
7. [Part 6: Validation Framework](#part-6-validation-framework)
8. [Part 7: Iteration & Recovery](#part-7-iteration--recovery)
9. [Part 8: Git Integration](#part-8-git-integration)
10. [Part 9: Dashboard Integration](#part-9-dashboard-integration)
11. [Part 10: Implementation Roadmap](#part-10-implementation-roadmap)

---

## Executive Summary

Shannon V3.5 introduces **autonomous execution** - a single command that takes natural language input and delivers functionally-validated, committed code changes.

### The Gap V3.5 Addresses

**V3.0 Reality**:
- Users must run `analyze` then `wave` separately ❌
- No automatic validation of changes ❌
- No automatic git commits ❌
- No research during execution ❌
- No iteration if validation fails ❌
- Manual intervention required at every step ❌

**V3.5 Delivers**:
- **One command** for everything: `shannon exec "fix the bug"` ✅
- **Auto-priming** of codebase context ✅
- **Research-informed** planning and execution ✅
- **Functional validation** from user perspective ✅
- **Iterative refinement** until all tests pass ✅
- **Atomic git commits** for each validated change ✅
- **Real-time visibility** via V3.1 dashboard ✅

### The Transformation

**V3.0** (Multi-Step Manual):
```bash
$ shannon analyze spec.md          # Step 1: Manual analyze
$ cat analysis.json                # Step 2: Review manually
$ shannon wave build-auth           # Step 3: Execute waves
# Step 4: Manually test changes
# Step 5: Manually commit
# Step 6: Manually validate
```

**V3.5** (Single Command Autonomous):
```bash
$ shannon exec "fix the iOS offscreen login"
# AUTO: Primes context
# AUTO: Plans execution
# AUTO: Executes changes
# AUTO: Validates functionally
# AUTO: Commits to git
# DONE: Working code, ready for PR
```

### Core Innovation

Shannon V3.5 is the first AI coding tool that:

1. **Understands ANY natural language task** (no structured input required)
2. **Auto-discovers project context** (no manual setup)
3. **Researches solutions** before and during execution
4. **Validates functionally** (not just "does it compile")
5. **Iterates automatically** until validation passes
6. **Commits atomically** with descriptive messages
7. **Shows everything** in real-time dashboard

---

## Part 1: User Experience

### The Dream Workflow

```bash
# Scenario: User has iOS app with login bug
$ cd my-ios-app
$ shannon exec "fix the iOS offscreen login bug"

🎯 Shannon V3.5 Autonomous Executor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Task: fix the iOS offscreen login bug

🔍 Phase 1/5: Context Preparation (auto-priming)
   ⚙️  Scanning codebase...
   ✓ Project type: iOS (Swift 5.9, UIKit)
   ✓ Files indexed: 245 files, 42K lines
   ✓ Test framework: XCTest detected
   ✓ Git status: Clean working tree
   ✓ Context ready (5.2s)

🧠 Phase 2/5: Research & Analysis
   ⚙️  Researching iOS login screen issues...
   ✓ Found 8 relevant Stack Overflow threads
   ✓ Found 3 Apple HIG guidelines
   ✓ Common cause: Safe area constraints on iPhone X+
   ⚙️  Analyzing codebase for login implementation...
   ✓ Located: LoginViewController.swift
   ✓ Issue identified: Using view.bounds instead of safeAreaLayoutGuide
   ✓ Research complete (12.3s)

📋 Phase 3/5: Execution Planning
   ⚙️  Creating execution plan with validation strategy...
   ✓ Plan created: 3 steps, 4min estimated

   Step 1: Update layout constraints
   Step 2: Test in iOS Simulator
   Step 3: Run integration tests

   Validation: Build + XCTest + Simulator UI check
   ✓ Plan ready (4.1s)

🚀 Phase 4/5: Execution (press Enter for live dashboard)

   [V3.1 Dashboard opens, showing Layer 3: Current step detail]

   Step 1/3: Update layout constraints
   ├─ 📝 Modified: LoginViewController.swift (lines 45-52)
   ├─ 🔨 Building: xcodebuild...
   ├─ ✅ Build: SUCCESS (0 errors, 0 warnings)
   ├─ 🧪 Tests: Running XCTest suite...
   ├─ ✅ Tests: 12/12 PASSED
   ├─ 💾 Committed: e4f2a1c "Update login constraints to use safeAreaLayoutGuide"
   └─ ⏱️  Completed in 45s

   Step 2/3: Test in iOS Simulator
   ├─ 📱 Launching: iPhone 14 simulator...
   ├─ 🎬 Running app...
   ├─ 📸 Screenshot: login_screen.png
   ├─ ✅ UI Validation: Login screen visible ✓
   ├─ ✅ UI Validation: Login button tappable ✓
   ├─ 💾 Committed: a3b9c2d "Validate safe area constraints in simulator"
   └─ ⏱️  Completed in 2m 15s

   Step 3/3: Integration tests
   ├─ 🧪 Running: xcodebuild test -scheme Login...
   ├─ ✅ Integration: 5/5 PASSED
   ├─ ✅ All validations passed!
   └─ ⏱️  Completed in 1m 22s

✅ Phase 5/5: Completion

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Task Complete: fix the iOS offscreen login bug
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Changes:
  📝 LoginViewController.swift (8 lines modified)

Commits:
  • e4f2a1c Update login constraints to use safeAreaLayoutGuide
  • a3b9c2d Validate safe area constraints in simulator

Validations:
  ✅ Build (0 errors, 0 warnings)
  ✅ Unit tests (12/12 passed)
  ✅ Simulator test (login visible, button tappable)
  ✅ Integration tests (5/5 passed)

Branch: fix/ios-offscreen-login
Time: 4m 22s
Cost: $0.23

Next steps:
  $ git push origin fix/ios-offscreen-login
  $ gh pr create  # Create pull request
```

User types ONE command, gets working code with full validation.

### 1.1 Command Interface

#### Basic Usage

```bash
# Simple execution - Shannon figures out everything
shannon exec "fix the iOS offscreen login"

# With auto-commit enabled (default)
shannon exec "add dark mode to settings"

# Interactive mode (asks before each commit)
shannon exec "refactor auth module" --interactive

# With specific validation command
shannon exec "optimize database queries" --validate-with "pytest tests/db/"

# Research-backed mode (more thorough planning)
shannon exec "implement OAuth2" --research

# Set max iterations
shannon exec "fix flaky test" --max-iterations 5

# Dry run (plan only, don't execute)
shannon exec "migrate to TypeScript" --dry-run

# With specific model
shannon exec "implement complex algorithm" --model claude-3-opus-20240229
```

#### Options Reference

| Option | Description | Default |
|--------|-------------|---------|
| `--auto-commit` | Auto-commit validated changes | `true` |
| `--interactive` | Confirm before each step | `false` |
| `--max-iterations` | Max retry attempts per step | `3` |
| `--validate-with` | Custom validation command | Auto-detect |
| `--research` | Enable deep research | `auto` |
| `--dry-run` | Plan only, don't execute | `false` |
| `--model` | Specific Claude model | `claude-3-5-sonnet` |
| `--branch` | Custom branch name | Auto-generate |
| `--session-id` | Resume existing session | New |

### 1.2 Example Scenarios

#### Scenario 1: Bug Fix (Simple)

```bash
$ shannon exec "fix the React hydration error in Header component"

🎯 Shannon V3.5 Autonomous Executor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Task: fix the React hydration error in Header component

🔍 Context Preparation
   ✓ Project: Next.js 14 (React 18)
   ✓ Primed: 156 files
   ✓ Located: components/Header.tsx

🧠 Research & Planning
   ✓ Researched: React hydration errors
   ✓ Common cause: Server/client mismatch
   ✓ Plan: 2 steps, ~2min

🚀 Execution
   Step 1/2: Fix timestamp rendering
   ├─ Modified: Header.tsx (line 23: use useEffect for client-only)
   ├─ Build: ✅ PASS
   ├─ Tests: ✅ 8/8 PASS
   └─ Committed: abc123f "Fix hydration: Move timestamp to useEffect"

   Step 2/2: Validate in browser
   ├─ Running: npm run dev
   ├─ Testing: http://localhost:3000
   ├─ Validation: ✅ No hydration errors
   └─ Committed: def456a "Validate hydration fix"

✅ Complete! (1m 42s, $0.08)

Changes: components/Header.tsx (3 lines)
Branch: fix/react-hydration-header
All validations passed ✅
```

#### Scenario 2: Feature Addition (Medium)

```bash
$ shannon exec "add user avatar upload with image resizing"

🎯 Shannon V3.5 Autonomous Executor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Task: add user avatar upload with image resizing

🔍 Context Preparation
   ✓ Project: Django REST + React frontend
   ✓ Primed: 423 files
   ✓ Auth system: Django User model found

🧠 Research & Planning
   ⚙️  Researching image upload best practices...
   ✓ Found: Pillow for resizing, S3 for storage
   ✓ Security: File type validation, size limits
   ✓ Plan: 5 steps, ~12min

   1. Add avatar field to User model
   2. Create upload endpoint (Django)
   3. Add image resizing logic
   4. Create upload UI (React)
   5. E2E test upload flow

🚀 Execution
   Step 1/5: Add avatar field
   ├─ Modified: models.py (add ImageField)
   ├─ Created: migrations/0012_user_avatar.py
   ├─ Build: ✅ PASS
   ├─ Migration: ✅ PASS (./manage.py migrate)
   ├─ Tests: ✅ 45/45 PASS
   └─ Committed: a1b2c3d "Add avatar field to User model"

   Step 2/5: Create upload endpoint
   ├─ Created: api/views/avatar_upload.py
   ├─ Modified: api/urls.py
   ├─ Build: ✅ PASS
   ├─ Tests: ✅ 47/47 PASS (2 new tests)
   └─ Committed: e4f5g6h "Add avatar upload endpoint with validation"

   Step 3/5: Add image resizing
   ├─ Modified: api/views/avatar_upload.py
   ├─ Dependencies: Added Pillow==10.1.0
   ├─ Build: ✅ PASS
   ├─ Unit tests: ✅ PASS (resize creates 3 sizes)
   ├─ Integration: ✅ PASS (upload + resize works)
   └─ Committed: i7j8k9l "Implement image resizing (thumbnail, medium, large)"

   Step 4/5: Create upload UI
   ├─ Created: components/AvatarUpload.tsx
   ├─ Modified: components/Profile.tsx
   ├─ Build: ✅ PASS (npm run build)
   ├─ Type check: ✅ PASS (tsc)
   └─ Committed: m1n2o3p "Add avatar upload UI component"

   Step 5/5: E2E test
   ├─ Running: Full stack (Django + React)
   ├─ Test: Upload test.jpg via UI
   ├─ Validation: ✅ Image uploaded
   ├─ Validation: ✅ 3 sizes created (thumbnail, medium, large)
   ├─ Validation: ✅ Avatar displayed in profile
   └─ Committed: q4r5s6t "E2E test: Avatar upload flow complete"

✅ Complete! (11m 23s, $0.67)

Changes:
  • models.py (5 lines added)
  • migrations/0012_user_avatar.py (23 lines)
  • api/views/avatar_upload.py (87 lines created)
  • api/urls.py (2 lines)
  • components/AvatarUpload.tsx (145 lines created)
  • components/Profile.tsx (12 lines)
  • requirements.txt (1 line)

Commits: 5 atomic commits
Branch: feat/avatar-upload-with-resizing
All validations passed ✅
Ready for PR!
```

#### Scenario 3: Iteration Example (Failure → Research → Success)

```bash
$ shannon exec "fix the slow PostgreSQL query in /api/users/search"

🎯 Shannon V3.5 Autonomous Executor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Task: fix the slow PostgreSQL query in /api/users/search

🔍 Context Preparation
   ✓ Project: FastAPI + PostgreSQL
   ✓ Located: api/routes/users.py (search endpoint)
   ✓ Current query: Full table scan (SLOW)

🧠 Research & Planning
   ⚙️  Researching PostgreSQL query optimization...
   ✓ Found: Index best practices, EXPLAIN ANALYZE
   ✓ Plan: Add index, test performance

🚀 Execution

   [ITERATION 1]
   Step 1: Add index on username column
   ├─ Created: migrations/add_username_index.sql
   ├─ Validation: ✅ Build PASS
   ├─ Performance test: ❌ FAIL (still 800ms, target <100ms)
   ├─ Analysis: Index not being used, query has ILIKE
   └─ Rolling back...

   [ITERATION 2 - After Research]
   ⚙️  Researching: "PostgreSQL ILIKE not using index"
   ✓ Found: Need trigram index for ILIKE

   Step 1 (retry): Add trigram index
   ├─ Modified: migrations/add_username_index.sql (use gin_trgm_ops)
   ├─ Validation: ✅ Build PASS
   ├─ Performance test: ✅ PASS (45ms, target <100ms) ✅
   ├─ EXPLAIN ANALYZE: Using trigram index ✅
   └─ Committed: xyz789 "Add trigram index for fast ILIKE search"

✅ Complete! (3m 12s, $0.15)

Iterations: 2 (first approach failed, researched, second succeeded)
Performance: 800ms → 45ms (17.8x faster) ✅
Branch: perf/optimize-user-search-query
```

### 1.3 Command Behavior

#### Auto-Detection

Shannon V3.5 automatically detects:

- **Project type**: iOS, Android, Web (React/Vue/Angular), Backend (Django/FastAPI/Express), Database, Desktop, etc.
- **Language**: Swift, TypeScript, Python, Java, Go, Rust, etc.
- **Test framework**: XCTest, Jest, Pytest, JUnit, etc.
- **Build system**: Xcode, npm, cargo, maven, gradle, etc.
- **Git state**: Current branch, uncommitted changes, remote status

#### Context Priming

Shannon V3.5 uses **intelligent task-focused priming**:

**Traditional approach** (V3.0):
- Analyze entire codebase (slow, ~5min for large projects)
- Load everything into context

**V3.5 approach** (Smart):
- Analyze only relevant parts based on task
- For "fix iOS login": Prime auth files, login views, related tests
- For "optimize database": Prime query files, migrations, DB config
- Expand scope only if needed during execution
- Time: <30s for targeted priming vs 5min for full scan

#### Validation Strategy Selection

Shannon auto-selects validation based on project:

| Project Type | Static | Unit/Integration | Functional |
|--------------|--------|------------------|------------|
| iOS/macOS | xcodebuild | XCTest | iOS Simulator |
| Android | gradle build | JUnit/Espresso | Android Emulator |
| Web Frontend | npm build, tsc | Jest/Vitest | Playwright/Cypress |
| Web Backend | Build | pytest/jest | API endpoint tests |
| Database | SQL syntax | Migration test | Query performance |
| Desktop | Build | Unit tests | App launch test |

If custom validation is configured (e.g., `test:` script in package.json), Shannon uses that.

---

## Part 2: System Architecture

### 2.1 Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│                    Shannon V3.5 Architecture                   │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─── INPUT LAYER ───────────────────────────────────┐        │
│  │                                                    │        │
│  │  CLI: shannon exec "natural language task"        │        │
│  │  Parser: Extract task, options, context           │        │
│  │                                                    │        │
│  └────────────────────────────────────────────────────┘        │
│                         ↓                                      │
│  ┌─── CONTEXT LAYER ─────────────────────────────────┐        │
│  │                                                    │        │
│  │  AutoPrimer:                                      │        │
│  │    - Detect project type                          │        │
│  │    - Load relevant context (task-focused)         │        │
│  │    - Check Serena MCP for cached knowledge        │        │
│  │    - Build dependency graph                        │        │
│  │                                                    │        │
│  └────────────────────────────────────────────────────┘        │
│                         ↓                                      │
│  ┌─── RESEARCH LAYER ────────────────────────────────┐        │
│  │                                                    │        │
│  │  ResearchAssistant:                               │        │
│  │    - Web search for solutions                     │        │
│  │    - Stack Overflow/docs lookup                   │        │
│  │    - Best practices research                       │        │
│  │    - Error message research (when failures occur) │        │
│  │                                                    │        │
│  └────────────────────────────────────────────────────┘        │
│                         ↓                                      │
│  ┌─── PLANNING LAYER ────────────────────────────────┐        │
│  │                                                    │        │
│  │  TaskPlanner (with Sequential Thinking):          │        │
│  │    - Break down task into steps                   │        │
│  │    - Identify files to modify                     │        │
│  │    - Plan validation strategy                     │        │
│  │    - Estimate duration                            │        │
│  │    - Generate fallback approaches                 │        │
│  │                                                    │        │
│  └────────────────────────────────────────────────────┘        │
│                         ↓                                      │
│  ┌─── EXECUTION LAYER ───────────────────────────────┐        │
│  │                                                    │        │
│  │  ExecutionEngine:                                 │        │
│  │    ┌─ For each step ────────────────┐            │        │
│  │    │                                 │            │        │
│  │    │  1. Execute changes             │            │        │
│  │    │  2. Run validations (3 tiers)   │            │        │
│  │    │  3. If PASS → Git commit        │            │        │
│  │    │  4. If FAIL → Research + retry  │            │        │
│  │    │                                 │            │        │
│  │    └─────────────────────────────────┘            │        │
│  │                                                    │        │
│  └────────────────────────────────────────────────────┘        │
│                         ↓                                      │
│  ┌─── VALIDATION LAYER ──────────────────────────────┐        │
│  │                                                    │        │
│  │  ValidationOrchestrator:                          │        │
│  │    Tier 1: Static (build, lint, type check)       │        │
│  │    Tier 2: Unit/Integration (test suites)         │        │
│  │    Tier 3: Functional (E2E, user perspective)     │        │
│  │                                                    │        │
│  │  Uses MCPs for user-perspective validation        │        │
│  │                                                    │        │
│  └────────────────────────────────────────────────────┘        │
│                         ↓                                      │
│  ┌─── GIT LAYER ─────────────────────────────────────┐        │
│  │                                                    │        │
│  │  GitManager:                                      │        │
│  │    - Create feature branch                        │        │
│  │    - Atomic commits per validated step            │        │
│  │    - Descriptive commit messages                  │        │
│  │    - Rollback on failure                          │        │
│  │                                                    │        │
│  └────────────────────────────────────────────────────┘        │
│                         ↓                                      │
│  ┌─── DASHBOARD LAYER ───────────────────────────────┐        │
│  │                                                    │        │
│  │  V3.1 Interactive Dashboard:                      │        │
│  │    - Layer 1: Execution overview                  │        │
│  │    - Layer 2: Step breakdown                      │        │
│  │    - Layer 3: Current step detail                 │        │
│  │    - Layer 4: Message stream                      │        │
│  │                                                    │        │
│  │  Real-time visibility of EVERYTHING               │        │
│  │                                                    │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 2.2 Core Components

#### AutoExecutor (Main Orchestrator)

**File**: `src/shannon/executor/auto_executor.py` (300 lines)

**Responsibilities**:
- Coordinate all phases (prime → research → plan → execute → validate)
- Manage execution state
- Handle errors and escalation
- Track progress for dashboard
- Generate final report

**Key Methods**:
```python
class AutoExecutor:
    async def execute(
        self,
        task: str,
        options: ExecOptions
    ) -> ExecutionResult:
        """Main execution entry point"""

    async def ensure_context_primed(self) -> ProjectContext:
        """Ensure codebase context is ready"""

    async def create_execution_plan(
        self,
        task: str,
        context: ProjectContext,
        research: ResearchResults
    ) -> ExecutionPlan:
        """Create detailed execution plan"""

    async def execute_with_iteration(
        self,
        plan: ExecutionPlan
    ) -> ExecutionResult:
        """Execute plan with retry logic"""
```

#### TaskPlanner (Intelligent Planning)

**File**: `src/shannon/executor/task_planner.py` (400 lines)

**Responsibilities**:
- Convert natural language to structured plan
- Use sequential thinking for reasoning
- Identify validation strategies
- Generate fallback approaches
- Estimate durations

**Planning Algorithm**:
```python
async def create_plan(
    task: str,
    context: ProjectContext,
    research: ResearchResults
) -> ExecutionPlan:
    # 1. Use sequential thinking to understand task
    understanding = await self.think_through_task(task, context)

    # 2. Identify affected files
    files = await self.identify_relevant_files(understanding, context)

    # 3. Break into atomic steps
    steps = await self.break_into_steps(understanding, files, research)

    # 4. Define validation for each step
    for step in steps:
        step.validation = await self.define_validation(step, context)

    # 5. Generate alternatives
    for step in steps:
        step.fallbacks = await self.generate_alternatives(step, research)

    return ExecutionPlan(steps=steps, ...)
```


#### ValidationOrchestrator (3-Tier Validation)

**File**: `src/shannon/executor/validator.py` (350 lines)

**Responsibilities**:
- Run 3 tiers of validation (static, unit, functional)
- Aggregate results
- Determine if changes are safe to commit
- Provide detailed failure reports
- Suggest fixes for failures

**Validation Flow**:
```python
async def validate_changes(
    changes: ChangeSet,
    criteria: ValidationCriteria
) -> ValidationResult:
    result = ValidationResult()

    # Tier 1: Static validation (fast)
    tier1 = await self.validate_static(changes)
    result.tier1_passed = tier1.all_passed()

    if not tier1.all_passed():
        # No point continuing if build fails
        return result

    # Tier 2: Unit/Integration tests
    tier2 = await self.validate_tests(changes, criteria.test_commands)
    result.tier2_passed = tier2.all_passed()

    if not tier2.all_passed():
        # Functional tests won't help if unit tests fail
        return result

    # Tier 3: Functional validation
    tier3 = await self.validate_functional(changes, criteria.functional_checks)
    result.tier3_passed = tier3.all_passed()

    # All tiers must pass
    result.all_passed = result.tier1_passed and result.tier2_passed and result.tier3_passed

    return result
```

#### ResearchAssistant (On-Demand Research)

**File**: `src/shannon/executor/research_assistant.py` (250 lines)

**Responsibilities**:
- Conduct research before planning
- Research failures during execution
- Cache research results
- Suggest alternative approaches

**Research Triggers**:
1. **Before planning**: Research task best practices
2. **After failure**: Research error messages and solutions
3. **When stuck**: Research alternative implementations
4. **For unfamiliar tech**: Research APIs and patterns

**Example**:
```python
async def research_failure(
    failure: ValidationFailure
) -> ResearchResults:
    # Extract key error message
    error_msg = failure.error_message

    # Search for solutions
    query = f"{failure.context.language} {error_msg} solution"
    web_results = await self.web_search(query)

    # Find relevant Stack Overflow
    stackoverflow = await self.search_stackoverflow(error_msg)

    # Check official docs
    docs = await self.search_docs(failure.context.framework, error_msg)

    # Synthesize findings
    return ResearchResults(
        summary="Common cause is X, solution is Y",
        sources=[web_results, stackoverflow, docs],
        suggested_approaches=["Try approach A", "Try approach B"]
    )
```

#### GitManager (Atomic Commits)

**File**: `src/shannon/executor/git_manager.py` (200 lines)

**Responsibilities**:
- Create feature branches
- Commit validated changes
- Generate descriptive commit messages
- Rollback on failure
- Track commit history

**Git Workflow**:
```python
async def execute_with_git(plan: ExecutionPlan) -> GitResult:
    # 1. Check clean state
    if not git_status_clean():
        raise Exception("Working directory must be clean")

    # 2. Create branch
    branch_name = generate_branch_name(plan.task_description)
    git_checkout_new_branch(branch_name)

    # 3. Execute steps with commits
    for step in plan.steps:
        changes = await execute_step(step)
        validation = await validate(changes)

        if validation.passed:
            # Commit immediately
            commit_msg = generate_commit_message(step, validation)
            git_commit(changes.files, commit_msg)
        else:
            # Rollback and retry
            git_reset_hard()
            # Try alternative approach...

    # 4. Return summary
    return GitResult(
        branch=branch_name,
        commits=get_commit_list(),
        ready_for_pr=True
    )
```

---

## Part 3: Auto-Priming System

### 3.1 Intelligent Context Loading

**Problem**: Loading entire codebase is slow and unnecessary.

**Solution**: Task-focused incremental priming.

#### Priming Strategy

```python
class AutoPrimer:
    async def prime_for_task(
        self,
        task: str,
        project_root: Path
    ) -> ProjectContext:
        # 1. Check if project already primed (Serena MCP cache)
        cached = await self.check_serena_cache(project_root)
        if cached and cached.is_recent():
            return cached.load_minimal_context(task)

        # 2. Detect project type
        project_type = await self.detect_project_type(project_root)

        # 3. Extract task keywords
        keywords = self.extract_keywords(task)
        # "fix iOS offscreen login" → ["iOS", "login", "offscreen", "UI", "layout"]

        # 4. Find relevant files
        relevant_files = await self.find_relevant_files(
            keywords,
            project_type,
            project_root
        )
        # Result: LoginViewController.swift, AuthManager.swift, LoginTests.swift

        # 5. Load those files + immediate dependencies
        context = await self.load_context(relevant_files, depth=2)

        # 6. Cache for future
        await self.save_to_serena(project_root, context)

        return context
```

#### Time Comparison

| Project Size | Full Prime (V3.0) | Smart Prime (V3.5) | Speedup |
|--------------|-------------------|-------------------|---------|
| Small (50 files) | 15s | 5s | 3x |
| Medium (500 files) | 2min | 12s | 10x |
| Large (2000 files) | 8min | 25s | 19x |
| Huge (10k files) | 30min | 45s | 40x |

### 3.2 Serena MCP Integration

Shannon V3.5 uses Serena MCP as a **knowledge cache**:

**First run** (cold cache):
```
$ shannon exec "optimize search query"
🔍 Priming codebase... (analyzing 500 files)
   → Takes 2min, builds knowledge graph
   → Stores in Serena MCP
```

**Second run** (warm cache):
```
$ shannon exec "add pagination to search"
🔍 Loading context... (from Serena)
   → Takes 5s, reuses knowledge graph
   → Only analyzes files related to "search" + "pagination"
```

**Knowledge Graph Structure** (in Serena):
```
Project: my-app
├─ Files
│  ├─ api/search.py → [dependencies, imports, functions]
│  ├─ db/queries.py → [queries, indexes, performance notes]
│  └─ tests/test_search.py → [test cases, coverage]
├─ Patterns
│  ├─ API style: FastAPI with Pydantic
│  ├─ DB: PostgreSQL with SQLAlchemy
│  └─ Testing: pytest with fixtures
└─ Last updated: 2025-11-15
```

---

## Part 4: Research-Informed Planning

### 4.1 Research Integration

Shannon V3.5 does research at TWO points:

**Point 1: During Planning** (proactive)
- Research task best practices BEFORE coding
- Understand common pitfalls
- Learn recommended approaches

**Point 2: During Execution** (reactive)
- Research failures and errors
- Find solutions to unexpected problems
- Discover alternative approaches

### 4.2 Research Sources

Shannon V3.5 uses multiple research sources:

1. **Web Search** (via firecrawl MCP)
   - General solutions and patterns
   - Recent blog posts and articles

2. **Stack Overflow** (via web search + scraping)
   - Specific error solutions
   - Community-vetted approaches

3. **Official Documentation** (via web search)
   - API references
   - Best practices guides

4. **Research MCPs** (if available)
   - Perplexity for technical questions
   - Academic papers for algorithms

### 4.3 Research Examples

#### Example 1: Before Planning

```
Task: "implement real-time notifications"

Research Query: "real-time notifications best practices web app"

Findings:
- WebSockets vs Server-Sent Events vs Long Polling
- WebSockets recommended for bi-directional
- Libraries: Socket.io (Node.js), channels (Django), ActionCable (Rails)
- Security: Auth before WS upgrade, rate limiting

Planning Impact:
- Chooses WebSocket approach
- Plans authentication step
- Plans rate limiting
- Plans graceful degradation
```

#### Example 2: After Failure

```
Task: "fix database migration"

Execution: Run migration
Result: ERROR: "column already exists"

Research Query: "PostgreSQL column already exists migration error fix"

Findings:
- Use IF NOT EXISTS clause
- Or check column existence first
- Or use ALTER TABLE ... ADD COLUMN IF NOT EXISTS

Planning Impact:
- Modify migration to use IF NOT EXISTS
- Retry migration
- Success!
```

---

## Part 5: Execution Engine

### 5.1 Atomic Execution Model

Every step follows this pattern:

```
┌─ Execute Step ─────────────────────────────────────────┐
│                                                        │
│  1. Make changes (modify files)                       │
│     ↓                                                  │
│  2. Run Tier 1 validation (build, lint)              │
│     ↓                                                  │
│  3. If Tier 1 fails → rollback, research, retry      │
│     ↓                                                  │
│  4. Run Tier 2 validation (unit tests)                │
│     ↓                                                  │
│  5. If Tier 2 fails → rollback, research, retry      │
│     ↓                                                  │
│  6. Run Tier 3 validation (functional)                │
│     ↓                                                  │
│  7. If Tier 3 fails → rollback, research, retry      │
│     ↓                                                  │
│  8. All validations PASS → Git commit                 │
│     ↓                                                  │
│  9. Move to next step                                 │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**Key principle**: Never leave uncommitted changes. Either commit (success) or rollback (failure).

### 5.2 Iteration Strategy

Shannon tries multiple approaches when validation fails:

```python
max_iterations_per_step = 3

for attempt in range(max_iterations_per_step):
    # Execute
    changes = await execute_step(step)

    # Validate
    validation = await validate(changes)

    if validation.passed:
        await git_commit(changes)
        break  # Success!

    else:
        # Failure - analyze and retry
        failure_analysis = analyze_failure(validation)

        if attempt < max_iterations_per_step - 1:
            # Research solution
            research = await research_assistant.find_solution(
                failure_analysis.error_message,
                failure_analysis.context
            )

            # Generate alternative approach
            alternative_step = await replan_with_research(
                step,
                research,
                previous_failures=[validation]
            )

            # Rollback
            await git_reset_hard()

            # Retry with alternative
            step = alternative_step

        else:
            # Max iterations reached
            raise ExecutionFailure(
                step=step,
                attempts=max_iterations_per_step,
                last_failure=validation,
                suggestion=failure_analysis.user_intervention_suggestion
            )
```

### 5.3 Progress Tracking

Execution progress is tracked for dashboard display:

```python
@dataclass
class ExecutionProgress:
    """Real-time execution progress"""
    phase: str  # "Priming", "Planning", "Executing", "Validating"
    current_step: int
    total_steps: int
    current_operation: str  # "Running unit tests"
    elapsed_seconds: float
    estimated_remaining_seconds: float

    # For dashboard Layer 2
    steps_status: List[StepStatus]

@dataclass
class StepStatus:
    """Status of individual step"""
    step_number: int
    description: str
    status: Literal['pending', 'executing', 'validating', 'complete', 'failed']
    progress_percent: float
    validation_results: Optional[ValidationResult]
    commit_hash: Optional[str]
```

This feeds directly into V3.1 dashboard Layer 2 (step breakdown view).

---

## Part 6: Validation Framework

### 6.1 Three-Tier Validation

#### Tier 1: Static Validation (Fast ~10s)

**Purpose**: Catch syntax errors, type errors, build failures

**Checks**:
1. **Syntax**: Language parser validates syntax
2. **Types**: TypeScript tsc, Python mypy, etc.
3. **Lint**: ESLint, ruff, clippy, etc.
4. **Build**: Compile/transpile successfully
5. **Imports**: All imports resolve

**Example** (TypeScript project):
```bash
# Tier 1 validation commands
npx tsc --noEmit                    # Type check
npx eslint src/                     # Lint
npm run build                       # Build
```

If any fail → rollback and retry with fixes.

#### Tier 2: Unit/Integration Tests (Medium ~1-5min)

**Purpose**: Ensure changes don't break existing functionality

**Checks**:
1. **Unit tests**: Run test suite
2. **Integration tests**: Test interactions
3. **Regression tests**: Ensure no regressions
4. **Coverage**: Check code coverage if available

**Example** (Python project):
```bash
# Tier 2 validation commands
pytest tests/ --cov=src/           # Unit tests with coverage
pytest tests/integration/          # Integration tests
```

If any fail → analyze failure, research solution, retry.

#### Tier 3: Functional Validation (Slow ~2-10min)

**Purpose**: Validate from USER PERSPECTIVE using actual app

**Checks**:
1. **Application startup**: App runs without crashing
2. **Feature testing**: The specific feature works
3. **UI validation**: Visual/screenshot comparison (if UI change)
4. **Performance**: Meets performance criteria (if optimization)
5. **E2E flows**: Complete user flows work

**Example** (Web app):
```bash
# Tier 3 validation commands
npm start &                        # Start app
sleep 5                            # Wait for startup
curl http://localhost:3000/health  # Health check
npx playwright test e2e/login.spec.ts  # E2E test
```

**Example** (iOS app):
```bash
# Tier 3 validation commands
xcrun simctl boot "iPhone 14"      # Boot simulator
xcodebuild test -scheme MyApp -destination 'platform=iOS Simulator,name=iPhone 14'
# Captures: UI tests + screenshots
```

### 6.2 MCP-Based Validation

Shannon V3.5 uses available MCPs for functional validation:

**Available MCPs** (auto-detected):
- `filesystem`: File existence, content checks
- `terminal`: Run commands, capture output
- `firecrawl`: Scrape deployed page, verify content
- `puppeteer`: Browser automation, screenshots
- `sequential-thinking`: Reason about validation results

**Example Validation Plan**:
```python
{
    "task": "fix login form styling",
    "validations": [
        # Tier 1
        {"type": "static", "command": "npm run build"},
        {"type": "static", "command": "npm run type-check"},

        # Tier 2
        {"type": "unit", "command": "npm test src/components/LoginForm.test.tsx"},

        # Tier 3
        {"type": "functional", "mcp": "puppeteer", "script": "e2e/login.js"},
        {"type": "functional", "mcp": "firecrawl", "url": "http://localhost:3000/login", "check": "Login form visible"}
    ]
}
```

### 6.3 Success Criteria Matching

Each validation has **explicit success criteria**:

```python
@dataclass
class ValidationCriteria:
    static_checks: List[StaticCheck]
    unit_tests: List[TestCommand]
    functional_checks: List[FunctionalCheck]
    success_indicators: List[SuccessIndicator]

@dataclass
class SuccessIndicator:
    """Explicit success criteria"""
    description: str  # "Login screen visible"
    validation_method: str  # "screenshot_comparison" or "element_exists"
    expected_value: Any  # Expected result
    tolerance: Optional[float] = None  # For numeric comparisons

# Example for "fix slow query"
SuccessIndicator(
    description="Query executes in < 100ms",
    validation_method="performance_timing",
    expected_value=100,  # milliseconds
    tolerance=10  # Allow 90-110ms
)

# Example for "fix login screen"
SuccessIndicator(
    description="Login button visible and tappable",
    validation_method="ui_element_check",
    expected_value={"exists": True, "tappable": True}
)
```

---

## Part 7: Iteration & Recovery

### 7.1 Failure Analysis

When validation fails, Shannon analyzes WHY:

```python
async def analyze_failure(
    validation_result: ValidationResult
) -> FailureAnalysis:
    # Extract failures
    failures = validation_result.failures

    # Categorize
    categories = categorize_failures(failures)
    # Result: {'build_error': 2, 'test_failure': 1}

    # Identify root cause
    root_cause = identify_root_cause(failures)
    # "TypeScript error: Property 'username' does not exist on type 'User'"

    # Determine if research needed
    needs_research = should_research(root_cause)
    # True if: unfamiliar error, no obvious fix

    # Suggest intervention
    user_intervention = None
    if is_environment_issue(root_cause):
        user_intervention = "This looks like an environment issue. Please check: ..."

    return FailureAnalysis(
        root_cause=root_cause,
        category=categories,
        needs_research=needs_research,
        suggested_fixes=["Try X", "Try Y"],
        user_intervention_suggestion=user_intervention
    )
```

### 7.2 Retry Logic

Shannon retries up to 3 times per step with DIFFERENT approaches:

```
Iteration 1: Original planned approach
  └─ Fails → analyze

Iteration 2: Alternative approach based on failure analysis
  └─ Fails → research + analyze

Iteration 3: Completely different approach based on research
  └─ Fails → escalate to user

If iteration 3 fails: Report partial progress and ask for help
```

### 7.3 Example Iteration Sequence

```
Task: "fix memory leak in WebSocket handler"

ITERATION 1: Add cleanup in onClose
├─ Modified: ws_handler.py
├─ Validation: Tests PASS ✅ but memory still leaking ❌
└─ Failure: Cleanup not called on server shutdown

ITERATION 2 (after analysis): Add cleanup in shutdown hook
├─ Research: "Python WebSocket cleanup on shutdown"
├─ Found: Need atexit handler
├─ Modified: ws_handler.py + app.py
├─ Validation: Tests PASS ✅ but still leaking ❌
└─ Failure: Event loop keeps references

ITERATION 3 (after deeper research): Use weak references
├─ Research: "Python asyncio WebSocket memory leak"
├─ Found: Use weakref.WeakSet for client tracking
├─ Modified: ws_handler.py (use WeakSet instead of list)
├─ Validation: Tests PASS ✅
├─ Memory test: PASS ✅ (no leak after 1000 connections)
└─ SUCCESS! Commit and continue

Result: 3 iterations, 3rd succeeded with research insights
```

---

## Part 8: Git Integration

### 8.1 Branch Strategy

Shannon creates descriptive feature branches:

```python
def generate_branch_name(task: str) -> str:
    # Extract key words
    words = extract_keywords(task)

    # Determine type
    if is_bug_fix(task):
        prefix = "fix"
    elif is_feature(task):
        prefix = "feat"
    elif is_optimization(task):
        prefix = "perf"
    elif is_refactor(task):
        prefix = "refactor"
    else:
        prefix = "chore"

    # Generate name
    slug = "-".join(words[:4])  # Max 4 words
    return f"{prefix}/{slug}"

# Examples:
"fix the iOS offscreen login" → "fix/ios-offscreen-login"
"add dark mode to settings" → "feat/dark-mode-settings"
"optimize search query" → "perf/optimize-search-query"
"refactor auth module" → "refactor/auth-module"
```

### 8.2 Commit Message Format

Shannon generates descriptive commit messages:

```
Format:
[type]: <summary>

WHY: <reasoning>
WHAT: <changes made>
VALIDATION: <what passed>

Example commit:
───────────────────────────────────────
fix: Update login constraints to use safeAreaLayoutGuide

WHY: Login screen was rendering offscreen on iPhone X+ devices
     due to ignoring safe area insets

WHAT: Updated LoginViewController.swift lines 45-52 to use
      view.safeAreaLayoutGuide instead of view.bounds for
      constraint anchoring

VALIDATION:
- Build: 0 errors, 0 warnings
- Tests: 12/12 XCTest passed
- Simulator: Login screen visible on iPhone 14
───────────────────────────────────────
```

### 8.3 Safety Guarantees

**Pre-execution checks**:
- ✅ Working directory is clean (no uncommitted changes)
- ✅ Not on main/master branch (creates new branch)
- ✅ Git available and configured
- ✅ Can create commits

**During execution**:
- ✅ Each change is isolated (atomic)
- ✅ Validation before commit (never commit broken code)
- ✅ Rollback on failure (git reset --hard)
- ✅ Descriptive commit messages

**Post-execution**:
- ✅ All commits have passing validations
- ✅ Branch ready for push
- ✅ Original branch unchanged

### 8.4 Rollback Strategy

When a step fails:

```python
async def rollback_failed_step(step: ExecutionStep):
    # 1. Git reset to last good commit
    await run_terminal_cmd("git reset --hard HEAD")

    # 2. Clean any untracked files
    await run_terminal_cmd("git clean -fd")

    # 3. Verify clean state
    status = await run_terminal_cmd("git status --porcelain")
    assert status == "", "Failed to rollback cleanly"

    # 4. Ready for retry
    return RollbackResult(success=True)
```

---

## Part 9: Dashboard Integration

### 9.1 V3.1 Dashboard Adaptation

Shannon V3.5 uses V3.1 dashboard but adapts layer meanings:

**Layer 1: Execution Overview**
- Shows: Task description, current phase, overall progress
- Example: "fix iOS login - Phase 4/5: Execution - 60%"

**Layer 2: Step Breakdown** (NEW for V3.5)
- Shows: All execution steps with status
- Example table:
```
# │ Step                    │ Status      │ Validation │ Commit
──┼─────────────────────────┼─────────────┼────────────┼─────────
1 │ Update constraints      │ ✅ Complete │ ✅ Pass    │ abc123f
2 │ Test in simulator       │ 🔄 Active   │ ⏳ Running │ -
3 │ Integration tests       │ ⏸️ Pending  │ -          │ -
```

**Layer 3: Current Step Detail**
- Shows: Current step execution detail
- Example:
```
Step 2/3: Test in simulator

EXECUTION:
  ⚙️  Running: iOS Simulator (iPhone 14)
  📱 App launched: MyApp.app
  🔍 Checking: Login screen visibility

VALIDATION (Tier 3: Functional):
  ⏳ Running UI test...
  - Launch app: ✅ Success
  - Navigate to login: ✅ Success
  - Check screen visible: 🔄 In progress...

FILES MODIFIED:
  • LoginViewController.swift

TOOLS USED:
  → run_terminal_cmd("xcrun simctl boot ...")
  → run_terminal_cmd("xcodebuild test ...")
```

**Layer 4: Message Stream** (Same as V3.1)
- Shows: Full SDK conversation
- All thinking, tool calls, responses

### 9.2 Progress Indicators

V3.5 adds execution-specific progress:

```
Overall: ▓▓▓▓▓▓░░░░ 60% (Phase 4/5: Execution)

Per-step:
Step 1: ▓▓▓▓▓▓▓▓▓▓ 100% ✅ (Complete)
Step 2: ▓▓▓▓▓▓░░░░  60% 🔄 (Validating)
Step 3: ░░░░░░░░░░   0% ⏸️ (Pending)

Current: Running Tier 3 validation (functional test)
```

---

## Part 10: Implementation Roadmap

### 10.1 Wave Structure

**Total Scope**: ~2,350 lines new code + ~150 lines modifications

#### Wave 1: Auto-Priming Engine (2 days, 400 lines)

**Goal**: Intelligent, task-focused codebase context loading

**Deliverables**:
1. `src/shannon/executor/__init__.py`
2. `src/shannon/executor/auto_primer.py` (250 lines)
   - Task keyword extraction
   - Relevant file discovery
   - Incremental context loading
   - Serena MCP caching
3. `src/shannon/executor/project_detector.py` (150 lines)
   - Auto-detect project type (iOS, web, backend, etc.)
   - Auto-detect test framework
   - Auto-detect build system
   - Auto-detect validation tools

**Entry Gate**: V3.1 complete, Serena MCP available

**Exit Gate**:
- Auto-priming works for 5 project types
- Context loading <30s for medium projects
- Serena caching reduces subsequent priming to <5s
- Functional test: Prime React project, verify files loaded

#### Wave 2: TaskPlanner + Research (3 days, 600 lines)

**Goal**: Research-informed planning with validation strategies

**Deliverables**:
1. `src/shannon/executor/task_planner.py` (300 lines)
   - Natural language → structured plan
   - Sequential thinking integration
   - Step breakdown with estimates
   - Validation strategy per step
2. `src/shannon/executor/research_assistant.py` (250 lines)
   - Proactive research (before planning)
   - Reactive research (after failures)
   - Multi-source research (web, Stack Overflow, docs)
   - Research caching
3. `src/shannon/executor/models.py` (50 lines)
   - ExecutionPlan, ExecutionStep, ValidationCriteria, etc.

**Entry Gate**: Wave 1 complete

**Exit Gate**:
- Planner creates detailed plan from natural language
- Research finds relevant best practices
- Validation strategies match project type
- Functional test: Plan "add OAuth", verify sensible steps

#### Wave 3: Execution + Iteration (2 days, 500 lines)

**Goal**: Step execution with retry logic

**Deliverables**:
1. `src/shannon/executor/execution_engine.py` (300 lines)
   - Step-by-step execution
   - Progress tracking
   - Failure detection
   - Alternative generation
2. `src/shannon/executor/iteration_manager.py` (200 lines)
   - Retry logic (max 3 per step)
   - Failure analysis
   - Alternative approach selection
   - Escalation handling

**Entry Gate**: Wave 2 complete

**Exit Gate**:
- Execution engine runs steps sequentially
- Failures trigger analysis and retry
- Max iterations enforced
- Functional test: Execute plan with forced failure, verify retry

#### Wave 4: Validation Framework (2 days, 450 lines)

**Goal**: 3-tier validation with MCP integration

**Deliverables**:
1. `src/shannon/executor/validator.py` (350 lines)
   - ValidationOrchestrator class
   - Tier 1: Static validation
   - Tier 2: Test validation
   - Tier 3: Functional validation
   - Result aggregation
2. `src/shannon/executor/mcp_validators.py` (100 lines)
   - MCP discovery for validation
   - MCP-based functional tests
   - Screenshot comparison
   - Performance measurement

**Entry Gate**: Wave 3 complete

**Exit Gate**:
- All 3 tiers work independently
- MCP validators discovered automatically
- Validation results detailed and actionable
- Functional test: Run validation on sample project, all tiers execute

#### Wave 5: Git + CLI Integration (2 days, 400 lines)

**Goal**: Git workflow and CLI command

**Deliverables**:
1. `src/shannon/executor/git_manager.py` (200 lines)
   - Branch creation
   - Atomic commits
   - Commit message generation
   - Rollback handling
2. `src/shannon/cli/commands.py` (150 lines modification)
   - Add `exec` command
   - Options parsing
   - Dashboard integration
   - Error handling
3. `src/shannon/executor/auto_executor.py` (200 lines)
   - Main AutoExecutor class
   - Orchestrates all phases
   - Generates final report

**Entry Gate**: Waves 1-4 complete

**Exit Gate**:
- `shannon exec` command works
- Creates branch, commits, ready for PR
- Dashboard shows real-time progress
- All 5 phases functional
- Functional test: Run `shannon exec "add feature"` end-to-end

### 10.2 Testing Strategy

**Functional Tests** (Live execution, no mocks):

1. **Test 1**: Auto-priming
   - Run: `shannon exec "test task"` in fresh project
   - Verify: Context primed, project type detected

2. **Test 2**: Simple fix (1 file, build validation)
   - Run: `shannon exec "fix typo in README"`
   - Verify: File modified, committed

3. **Test 3**: Medium feature (multiple files, tests)
   - Run: `shannon exec "add logging to API"`
   - Verify: Files created/modified, tests pass, committed

4. **Test 4**: Failure + iteration
   - Run: `shannon exec "task designed to fail initially"`
   - Verify: First attempt fails, retry succeeds

5. **Test 5**: Research integration
   - Run: `shannon exec "implement obscure algorithm"`
   - Verify: Research conducted, correct approach chosen

6. **Test 6**: Full validation (all 3 tiers)
   - Run: `shannon exec "add new API endpoint"`
   - Verify: Static + unit + functional validation

7. **Test 7**: Git workflow
   - Run: `shannon exec "refactor module"`
   - Verify: Branch created, atomic commits, descriptive messages

8. **Test 8**: Dashboard visibility
   - Run: `shannon exec "complex task"` with dashboard
   - Verify: All 4 layers show correct info, navigation works

**Total functional tests**: 8
**No unit tests**: Functional only per user requirement

### 10.3 Timeline & Milestones

| Wave | Duration | Deliverables | Tests |
|------|----------|--------------|-------|
| Wave 1: Auto-Priming | 2 days | AutoPrimer, ProjectDetector | 1 test |
| Wave 2: Planning + Research | 3 days | TaskPlanner, ResearchAssistant | 1 test |
| Wave 3: Execution | 2 days | ExecutionEngine, IterationManager | 2 tests |
| Wave 4: Validation | 2 days | ValidationOrchestrator, MCPValidators | 1 test |
| Wave 5: Git + CLI | 2 days | GitManager, CLI integration | 3 tests |
| **Total** | **11 days** | **~2,350 lines** | **8 tests** |

### 10.4 Success Metrics

Shannon V3.5 is successful if:

✅ **Ease of Use**: One command handles any task
✅ **Accuracy**: >80% of tasks complete without user intervention
✅ **Speed**: Average task completion <10 minutes
✅ **Quality**: All commits pass validation
✅ **Transparency**: Dashboard shows everything in real-time
✅ **Reliability**: Graceful handling of failures

---

## Part 11: Comparison to Alternatives

### Shannon V3.5 vs Other AI Coding Tools

| Feature | Shannon V3.5 | Cursor | Aider | GitHub Copilot |
|---------|--------------|--------|-------|----------------|
| Natural language tasks | ✅ Yes | ⚠️ Partial | ⚠️ Partial | ❌ No |
| Auto context discovery | ✅ Yes | ❌ No | ❌ No | ❌ No |
| Research during exec | ✅ Yes | ❌ No | ❌ No | ❌ No |
| Functional validation | ✅ Yes | ❌ No | ❌ No | ❌ No |
| Auto iteration | ✅ Yes | ❌ No | ⚠️ Manual | ❌ No |
| Auto git commits | ✅ Yes | ❌ No | ✅ Yes | ❌ No |
| Real-time dashboard | ✅ Yes (4-layer) | ❌ No | ❌ No | ❌ No |
| MCP integration | ✅ Yes | ⚠️ Limited | ❌ No | ❌ No |
| Full transparency | ✅ Yes | ⚠️ Partial | ⚠️ Partial | ❌ No |

**Shannon's unique advantage**: Combines ALL features into one autonomous system.

---

## Part 12: Future Enhancements (Post-V3.5)

Ideas for V3.6, V3.7:

### V3.6: Multi-Agent Autonomous Execution

- Parallel step execution (when steps independent)
- Agent specialization (frontend agent, backend agent, test agent)
- Agent collaboration on complex tasks
- Conflict resolution between agents

### V3.7: Learning & Improvement

- Learn from successful executions
- Build project-specific best practices
- Remember failure patterns
- Suggest proactive improvements
- "Shannon, what should I improve in this codebase?"

### V3.8: Pull Request Automation

- Auto-create PR with description
- Auto-add reviewers based on CODEOWNERS
- Auto-respond to review comments
- Auto-fix issues found in review

### V3.9: Continuous Execution

- Watch mode: `shannon exec --watch "maintain test coverage >80%"`
- Runs continuously, fixes issues as they arise
- Auto-commits fixes
- Reports daily summary

---

## Appendix A: Complete Example Execution

```bash
$ shannon exec "fix the slow database query in user search API"

╔══════════════════════════════════════════════════════════════╗
║         Shannon V3.5 Autonomous Executor                     ║
╚══════════════════════════════════════════════════════════════╝

📝 Task: fix the slow database query in user search API

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Phase 1/5: Context Preparation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚙️  Checking for existing context...
✓ Found: Serena MCP cache (last updated 2h ago)
✓ Loading cached knowledge graph...

⚙️  Scanning for task-relevant files...
✓ Keywords extracted: ["database", "query", "user", "search", "API"]
✓ Files found:
   - api/routes/users.py (search endpoint)
   - db/models/user.py (User model)
   - db/queries.py (query builders)
   - tests/test_user_search.py (existing tests)

⚙️  Loading file contents and dependencies...
✓ Loaded: 12 files (8 direct, 4 dependencies)
✓ Project type: FastAPI + PostgreSQL + SQLAlchemy
✓ Test framework: pytest
✓ Build: Python 3.11

✅ Context ready (4.2s)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Phase 2/5: Research & Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚙️  Researching PostgreSQL query optimization...
✓ Web search: "PostgreSQL slow query optimization"
✓ Found: 12 relevant articles
✓ Key insights:
   - Use EXPLAIN ANALYZE to identify bottleneck
   - Check for missing indexes
   - Avoid SELECT * when possible
   - Use covering indexes for common queries

⚙️  Analyzing current query implementation...
✓ Located: api/routes/users.py line 45
✓ Current query:
   SELECT * FROM users
   WHERE username ILIKE '%search_term%'
   OR email ILIKE '%search_term%'
✓ Problem identified:
   - Full table scan (no index)
   - ILIKE with leading wildcard (can't use B-tree index)
   - SELECT * (unnecessary columns)

⚙️  Researching: "PostgreSQL ILIKE wildcard index optimization"
✓ Found: Use GIN trigram index for ILIKE patterns
✓ Found: Use ts_vector for full-text search (faster)

✅ Research complete (8.7s)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Phase 3/5: Execution Planning
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚙️  Creating execution plan...

✓ Plan created with validation strategy

Execution Plan:
  Step 1: Enable pg_trgm extension
  Step 2: Create GIN trigram index on username + email
  Step 3: Optimize SELECT clause (only needed columns)
  Step 4: Update query to leverage index
  Step 5: Run EXPLAIN ANALYZE to verify index usage
  Step 6: Performance test (target: <100ms)

Validation Strategy:
  • Tier 1: Build (pytest syntax check)
  • Tier 2: Unit tests (test_user_search.py)
  • Tier 3: Performance test (measure query time)

Success Criteria:
  ✓ Build passes
  ✓ All tests pass
  ✓ Query time < 100ms (currently ~850ms)
  ✓ EXPLAIN ANALYZE shows index usage

Estimated duration: 5-7 minutes
Branch: perf/optimize-user-search-query

✅ Plan ready (3.4s)

[Press Enter to continue, or Ctrl+C to abort]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Phase 4/5: Execution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[V3.1 Interactive Dashboard opens]

⚙️  Creating branch: perf/optimize-user-search-query
✓ Branch created

┌─ Step 1/6: Enable pg_trgm extension ─────────────────┐
│                                                      │
│ 📝 Creating: migrations/enable_pg_trgm.sql           │
│                                                      │
│ VALIDATION (Tier 1: Static)                         │
│ ⚙️  Running: pytest --collect-only                   │
│ ✅ Syntax check: PASS                                │
│                                                      │
│ VALIDATION (Tier 2: Unit Tests)                     │
│ ⚙️  Running: pytest tests/test_migrations.py        │
│ ✅ Migration test: PASS                              │
│                                                      │
│ VALIDATION (Tier 3: Functional)                     │
│ ⚙️  Running: ./manage.py migrate                     │
│ ✅ Migration applied: PASS                           │
│ ✅ Extension enabled: pg_trgm                        │
│                                                      │
│ 💾 Committed: e1a2b3c "Enable pg_trgm extension for │
│    ILIKE optimization"                               │
│                                                      │
│ ⏱️  Completed in 22s                                 │
└──────────────────────────────────────────────────────┘

┌─ Step 2/6: Create GIN trigram index ────────────────┐
│                                                      │
│ 📝 Creating: migrations/add_trigram_index.sql        │
│    CREATE INDEX idx_users_search                     │
│    ON users USING gin(username gin_trgm_ops,         │
│                      email gin_trgm_ops);            │
│                                                      │
│ VALIDATION (Tier 1: Static)                         │
│ ✅ SQL syntax: PASS                                  │
│                                                      │
│ VALIDATION (Tier 2: Unit Tests)                     │
│ ⚙️  Running: pytest tests/                           │
│ ✅ Tests: 45/45 PASS                                 │
│                                                      │
│ VALIDATION (Tier 3: Functional)                     │
│ ⚙️  Running: ./manage.py migrate                     │
│ ✅ Index created: PASS                               │
│ ✅ Index exists: idx_users_search                    │
│                                                      │
│ 💾 Committed: f4g5h6i "Add GIN trigram index for     │
│    username/email ILIKE searches"                    │
│                                                      │
│ ⏱️  Completed in 18s                                 │
└──────────────────────────────────────────────────────┘

┌─ Step 3/6: Optimize SELECT clause ───────────────────┐
│                                                      │
│ 📝 Modified: api/routes/users.py (line 47)           │
│    Changed: SELECT * → SELECT id, username, email    │
│                                                      │
│ VALIDATION (Tier 1: Static)                         │
│ ✅ Type check: PASS (mypy)                           │
│ ✅ Lint: PASS (ruff)                                 │
│                                                      │
│ VALIDATION (Tier 2: Unit Tests)                     │
│ ⚙️  Running: pytest tests/test_user_search.py        │
│ ✅ Tests: 8/8 PASS                                   │
│                                                      │
│ 💾 Committed: j7k8l9m "Optimize SELECT clause in     │
│    user search (reduce data transfer)"               │
│                                                      │
│ ⏱️  Completed in 12s                                 │
└──────────────────────────────────────────────────────┘

┌─ Step 4/6: Update query to leverage index ───────────┐
│                                                      │
│ 📝 Modified: api/routes/users.py (line 45-52)        │
│    Updated query to use trigram similarity           │
│                                                      │
│ VALIDATION (Tier 1: Static)                         │
│ ✅ Build: PASS                                       │
│                                                      │
│ VALIDATION (Tier 2: Unit Tests)                     │
│ ✅ Tests: 8/8 PASS                                   │
│ ✅ Results: Correct (same results as before)         │
│                                                      │
│ 💾 Committed: n1o2p3q "Use trigram index in search   │
│    query"                                            │
│                                                      │
│ ⏱️  Completed in 15s                                 │
└──────────────────────────────────────────────────────┘

┌─ Step 5/6: Verify index usage ───────────────────────┐
│                                                      │
│ 📝 Running: EXPLAIN ANALYZE on query                 │
│                                                      │
│ Results:                                             │
│ ```                                                  │
│ Bitmap Index Scan on idx_users_search               │
│   Index Cond: (username %> 'search_term')           │
│   Rows: 12                                           │
│   Planning Time: 0.125 ms                            │
│   Execution Time: 2.341 ms                           │
│ ```                                                  │
│                                                      │
│ ✅ Index used: PASS                                  │
│ ✅ Query time: 2.3ms (target < 100ms) ✅             │
│                                                      │
│ 💾 Committed: r4s5t6u "Verify index usage with       │
│    EXPLAIN ANALYZE"                                  │
│                                                      │
│ ⏱️  Completed in 8s                                  │
└──────────────────────────────────────────────────────┘

┌─ Step 6/6: Performance test ──────────────────────────┐
│                                                      │
│ 📝 Running: Performance benchmark (1000 queries)      │
│                                                      │
│ BEFORE:                                              │
│   Avg: 847ms                                         │
│   p95: 1203ms                                        │
│   p99: 1456ms                                        │
│                                                      │
│ AFTER:                                               │
│   Avg: 2.8ms  ✅ (302x faster)                       │
│   p95: 4.2ms  ✅                                     │
│   p99: 6.1ms  ✅                                     │
│                                                      │
│ ✅ Performance target met: <100ms ✅                 │
│                                                      │
│ 💾 Committed: w7x8y9z "Performance test: 302x faster │
│    with trigram index"                               │
│                                                      │
│ ⏱️  Completed in 45s                                 │
└──────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Phase 5/5: Completion & Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Task Complete: fix the slow database query in user search API

CHANGES MADE:
  📝 migrations/enable_pg_trgm.sql (3 lines created)
  📝 migrations/add_trigram_index.sql (5 lines created)
  📝 api/routes/users.py (8 lines modified)

COMMITS (6 atomic commits):
  • e1a2b3c Enable pg_trgm extension for ILIKE optimization
  • f4g5h6i Add GIN trigram index for username/email ILIKE searches
  • j7k8l9m Optimize SELECT clause in user search
  • n1o2p3q Use trigram index in search query
  • r4s5t6u Verify index usage with EXPLAIN ANALYZE
  • w7x8y9z Performance test: 302x faster with trigram index

VALIDATIONS (ALL PASSED):
  ✅ Build: 0 errors
  ✅ Type check: PASS (mypy)
  ✅ Lint: PASS (ruff)
  ✅ Unit tests: 45/45 PASS
  ✅ Integration tests: 8/8 PASS
  ✅ Performance: 847ms → 2.8ms (302x faster) ✅
  ✅ Index usage: Verified with EXPLAIN ANALYZE ✅

BRANCH: perf/optimize-user-search-query
STATUS: Ready for push and PR

STATS:
  ⏱️  Total time: 2m 0s
  💰 Total cost: $0.34
  🔄 Iterations: 0 (succeeded on first try)
  📚 Research queries: 2

NEXT STEPS:
  $ git push origin perf/optimize-user-search-query
  $ gh pr create --title "Optimize user search query (302x faster)" \
                  --body "See commit messages for details"

Thank you for using Shannon V3.5! 🎉

