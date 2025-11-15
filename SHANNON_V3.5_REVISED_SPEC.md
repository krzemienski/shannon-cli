# Shannon V3.5 - Autonomous Executor (REVISED SPECIFICATION)

**Version**: 3.5.0
**Date**: November 15, 2025
**Status**: Revised Design - Builds on Existing Shannon Infrastructure
**Ultra-Thinking**: 30 sequential thoughts completed
**Philosophy**: Enhance what exists, don't rebuild

---

## 🎯 Critical Revision

**Original V3.5**: Standalone autonomous system (~2,350 lines, 11 days)
**Revised V3.5**: Enhancement layer on existing Shannon (~1,850 lines, 8 days)

### Key Realization

Shannon V3.5 should **BUILD ON** the existing Shannon Framework architecture:
- ✅ REUSE existing `/shannon:analyze`, `/shannon:wave`, `/shannon:prime` skills
- ✅ REUSE existing AgentController, ContextManager, SessionManager
- ✅ REUSE existing Serena MCP, analytics DB, V3.1 dashboard
- ✅ ADD enhanced system prompts, library discovery, validation, git automation

**NOT a separate system** - an ORCHESTRATION LAYER that enhances existing infrastructure.

---

## Part 1: Architecture Integration

### 1.1 Current Shannon Architecture (What Exists)

```
Shannon CLI
  ↓
ShannonSDKClient (src/shannon/sdk/client.py)
  ↓
Claude Agent SDK
  ↓
Shannon Framework Plugin (.claude-plugin/)
  ├─ 18 Skills:
  │  ├─ /shannon:analyze - 8D complexity analysis
  │  ├─ /shannon:wave - Wave-based implementation
  │  ├─ /shannon:task - Automated workflow
  │  ├─ /shannon:prime - Context priming
  │  └─ ... (14 more)
  │
  ├─ Systems:
  │  ├─ AgentController - Multi-agent orchestration
  │  ├─ ContextManager - Codebase context management
  │  ├─ SessionManager - Session storage
  │  └─ Analytics DB - Execution tracking
  │
  └─ MCPs:
     ├─ Serena - Knowledge graph and memory
     ├─ sequential-thinking - Planning and reasoning
     └─ filesystem - File operations
```

### 1.2 V3.5 Enhancement Layer (What We're Adding)

```
Shannon V3.5 = Existing Infrastructure + Enhancement Layer

Enhancement Layer:
  ┌─────────────────────────────────────────────┐
  │ NEW: /shannon:exec skill (400 lines)        │
  │   ├─ Orchestrates existing skills           │
  │   ├─ Adds library discovery                 │
  │   ├─ Adds validation loop                   │
  │   └─ Adds git automation                    │
  └─────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────┐
  │ NEW: Enhanced System Prompts (200 lines)    │
  │   ├─ Library discovery instructions         │
  │   ├─ Functional validation instructions     │
  │   └─ Git workflow instructions              │
  └─────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────┐
  │ NEW: Shannon CLI Modules (1,050 lines)      │
  │   ├─ library_discoverer.py (250 lines)      │
  │   ├─ validator.py (300 lines)               │
  │   ├─ git_manager.py (200 lines)             │
  │   ├─ prompt_enhancer.py (150 lines)         │
  │   └─ exec command in CLI (150 lines)        │
  └─────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────┐
  │ NEW: Analytics Tracking (200 lines)         │
  │   ├─ executions table                       │
  │   ├─ execution_steps table                  │
  │   └─ library_usage table                    │
  └─────────────────────────────────────────────┘

Total NEW code: ~1,850 lines
REUSED existing: ~15,000+ lines
```

---

## Part 2: System Prompt Enhancement

### 2.1 How It Works

Shannon CLI injects enhanced prompts using `ClaudeAgentOptions.system_prompt.append`:

```python
# In src/shannon/cli/commands.py

@cli.command()
@require_framework()
@click.argument('task')
def exec(task: str):
    """Execute autonomous task with validation"""

    async def run_exec():
        # Create SDK client
        client = ShannonSDKClient()

        # Build enhanced instructions
        from shannon.executor.prompt_enhancer import PromptEnhancer
        enhancer = PromptEnhancer()

        # Detect project type
        project_type = detect_project_type(os.getcwd())

        # Generate enhancements
        enhancements = enhancer.build_enhancements(
            task=task,
            project_type=project_type
        )
        # Returns: "LIBRARY DISCOVERY...\n\nFUNCTIONAL VALIDATION...\n\nGIT WORKFLOW..."

        # Create options with enhanced prompt
        options = ClaudeAgentOptions(
            plugins=[{"type": "local", "path": str(framework_path)}],
            system_prompt={
                "type": "preset",
                "preset": "claude_code",
                "append": enhancements  # <-- INJECT HERE
            },
            setting_sources=["user", "project"],
            permission_mode="bypassPermissions"
        )

        # Invoke /shannon:exec with enhanced prompts
        async for msg in client.query(
            prompt=f"/shannon:exec {task}",
            options=options
        ):
            # Process messages with dashboard...
```

### 2.2 Enhancement Templates

**File**: `src/shannon/executor/prompts.py` (150 lines)

```python
LIBRARY_DISCOVERY_INSTRUCTIONS = """
═══════════════════════════════════════════════════════════════
 CRITICAL: Research and Use Existing Libraries
═══════════════════════════════════════════════════════════════

BEFORE building any major feature, you MUST search for and evaluate existing open-source libraries.

Process:
1. Identify the feature/functionality needed
2. Search package registry (npm, PyPI, CocoaPods, etc.)
3. Evaluate top 3-5 options:
   - GitHub stars (prefer >1000)
   - Last update (prefer <6 months ago)
   - Maintenance status (active maintainers)
   - Compatibility (check with project dependencies)
   - License (prefer MIT/Apache/BSD)
   - Documentation quality

4. SELECT best option and document why
5. Add to project dependencies
6. USE in implementation (don't build custom)

Common Libraries by Category:

Authentication:
  - Web: passport.js, next-auth, Auth0 SDK
  - Mobile: expo-auth-session, react-native-app-auth
  - Python: django-allauth, FastAPI-Users

UI Components:
  - React: shadcn/ui, MUI, Chakra UI, Headless UI
  - React Native: react-native-paper, NativeBase, react-native-elements
  - SwiftUI: Use built-in components

Networking:
  - JavaScript: axios, ky, got
  - Swift: Alamofire, URLSession (built-in)
  - Python: httpx, requests

Data Management:
  - React: tanstack/react-query, SWR, Redux Toolkit
  - Mobile: Redux, Zustand, Jotai
  - Python: SQLAlchemy, Tortoise ORM

Forms & Validation:
  - React: react-hook-form, formik, zod
  - Python: Pydantic, marshmallow

DO NOT implement custom versions of these. ALWAYS use libraries.

Example:
  Task: "Add authentication to React app"
  ❌ WRONG: Build custom auth system
  ✅ RIGHT: Use next-auth library
"""

FUNCTIONAL_VALIDATION_INSTRUCTIONS = """
═══════════════════════════════════════════════════════════════
 CRITICAL: Functional Validation from User Perspective
═══════════════════════════════════════════════════════════════

ALL changes must be validated in THREE TIERS. ALL must pass.

TIER 1 - Static Validation (~10s):
  ✅ Build/compile succeeds
  ✅ Type checking passes (tsc, mypy, etc.)
  ✅ Linter passes (eslint, ruff, swiftlint, etc.)
  ✅ No syntax errors

TIER 2 - Unit/Integration Tests (~1-5min):
  ✅ Run test suite (npm test, pytest, xcodebuild test)
  ✅ All existing tests pass (no regressions)
  ✅ New tests pass (if added)
  ✅ Code coverage maintained or improved

TIER 3 - Functional/E2E (~2-10min):
  ✅ Run the actual application
  ✅ Test the specific feature from USER PERSPECTIVE
  ✅ Verify: "Can a user actually use this feature?"

Examples of Tier 3 validation:

iOS App:
  1. Launch in simulator: xcrun simctl boot "iPhone 14"
  2. Build and run: xcodebuild test -scheme MyApp
  3. Verify UI element visible and tappable
  4. Test actual user flow (tap login → see success)

Web App:
  1. Start dev server: npm run dev
  2. Open browser: http://localhost:3000
  3. Navigate to feature
  4. Test user interaction (click, type, submit)
  5. Verify expected behavior (success message, data saved, etc.)

API:
  1. Start server: uvicorn main:app
  2. Hit endpoint: curl -X POST http://localhost:8000/api/users
  3. Verify response: status 200, correct data structure
  4. Test error cases: invalid input → 400 error

Database:
  1. Run migration: ./manage.py migrate
  2. Verify schema: Check table exists
  3. Test query: Run actual query, verify results
  4. Performance: EXPLAIN ANALYZE, verify index usage

Use available MCPs for validation:
  - firecrawl: Scrape and verify web pages
  - puppeteer: Browser automation and screenshots
  - run_terminal_cmd: Launch apps, run tests

NEVER skip Tier 3. Compiling ≠ Working.
"""

GIT_WORKFLOW_INSTRUCTIONS = """
═══════════════════════════════════════════════════════════════
 CRITICAL: Atomic Git Commits per Validated Change
═══════════════════════════════════════════════════════════════

Git workflow (MANDATORY):

Pre-execution:
  1. Verify: git status is clean (no uncommitted changes)
  2. Verify: Not on main/master branch
  3. Create branch: git checkout -b <type>/<description>
     Types: fix/, feat/, perf/, refactor/, chore/

For EACH step:
  1. Make the change (modify files)
  2. Run Tier 1 validation (build, lint, types)
  3. If Tier 1 fails → git reset --hard, research, retry
  4. Run Tier 2 validation (tests)
  5. If Tier 2 fails → git reset --hard, research, retry
  6. Run Tier 3 validation (functional)
  7. If Tier 3 fails → git reset --hard, research, retry
  8. ALL pass → git add + git commit

Commit message format:
```
<type>: <one-line summary>

WHY: <reasoning for this change>
WHAT: <specific changes made>
VALIDATION:
  - Build: PASS
  - Tests: X/X PASS
  - Functional: <what was tested>
```

Rules:
  ❌ NEVER leave uncommitted changes
  ❌ NEVER commit unvalidated code
  ❌ NEVER make multiple changes before validating
  ✅ ALWAYS validate before committing
  ✅ ALWAYS rollback failed changes (git reset --hard)
  ✅ ALWAYS create descriptive commit messages

Post-execution:
  - All commits have passing validations
  - Branch ready for: git push origin <branch>
  - Ready for PR creation
"""
```

### 2.3 Task-Specific Enhancements

**File**: `src/shannon/executor/task_enhancements.py` (100 lines)

Project-specific instructions injected based on detection:

**iOS/Swift**:
```python
IOS_SWIFT_ENHANCEMENTS = """
iOS/Swift Development:
- Use SwiftUI for new UI (modern, declarative)
- Use Combine for reactive patterns
- ALWAYS handle safe area (especially for iPhone X+)
- Use Swift Package Manager for dependencies

Common Swift libraries:
  - Alamofire (HTTP networking)
  - Kingfisher (image loading/caching)
  - SnapKit (Auto Layout DSL, if using UIKit)
  - SwiftNIO-SSH (SSH connections)
  - KeychainAccess (secure storage)

Search: "Swift <feature> library GitHub" or SwiftPackageIndex.com

Validation:
  - Build: xcodebuild
  - Test: xcodebuild test -scheme <MyApp>
  - Simulator: xcrun simctl boot + launch app
  - Verify UI: Screenshot + element checks
"""
```

**React Native/Expo**:
```python
REACT_NATIVE_ENHANCEMENTS = """
React Native/Expo Development:
- Use Expo SDK when possible (simplifies native features)
- TypeScript strict mode
- Prefer function components with hooks

Common React Native libraries:
  - UI: react-native-paper, NativeBase, react-native-elements
  - Navigation: @react-navigation/native (standard)
  - Forms: react-hook-form
  - State: Zustand, Jotai (lighter than Redux)
  - Icons: expo-icons, react-native-vector-icons

Search: "React Native <feature> Expo compatible"

Validation:
  - Build: expo build or eas build
  - Type check: npx tsc --noEmit
  - Test: jest
  - Functional: Run in Expo Go app, test feature

DO NOT build custom UI components - use UI kit library.
"""
```

**Python/FastAPI**:
```python
PYTHON_FASTAPI_ENHANCEMENTS = """
Python/FastAPI Development:
- Type hints everywhere (use mypy)
- Pydantic models for validation
- Async/await for I/O operations

Common Python libraries:
  - ORM: SQLAlchemy, Tortoise ORM
  - Migrations: Alembic
  - Testing: pytest, pytest-async
  - Validation: Pydantic (built into FastAPI)
  - HTTP client: httpx

Search: "Python <feature> library PyPI"

Validation:
  - Type check: mypy src/
  - Lint: ruff check .
  - Tests: pytest tests/ --cov
  - Functional: uvicorn main:app + curl endpoints
"""
```

These get injected based on `detect_project_type()`.

---

## Part 2: The `/shannon:exec` Skill

### 2.1 Skill Implementation

**Location**: Shannon Framework `.claude-skills/exec.ts` (NEW, 400 lines)

```typescript
// Shannon Framework: .claude-skills/exec.ts

import { skill, invokeSkill, useTool } from '@claude-code/sdk';
import { sequential_thinking, serena } from '@mcp';

export const exec = skill({
  name: 'exec',
  description: 'Autonomous execution: research libraries, validate functionally, commit atomically',

  async execute(task: string, options?: ExecOptions) {
    console.log(`🎯 Shannon V3.5 Autonomous Executor`);
    console.log(`📝 Task: ${task}\n`);

    //═══════════════════════════════════════════════════════════
    // PHASE 1: Context Preparation (REUSES /shannon:prime)
    //═══════════════════════════════════════════════════════════

    console.log("🔍 Phase 1/5: Context Preparation");

    // Invoke existing prime skill
    await invokeSkill('/shannon:prime', {
      project: process.cwd(),
      task_focused: true,  // Only prime relevant files
      keywords: await extractKeywords(task)
    });

    console.log("✓ Context primed\n");

    //═══════════════════════════════════════════════════════════
    // PHASE 2: Library Discovery (NEW functionality)
    //═══════════════════════════════════════════════════════════

    console.log("🔍 Phase 2/5: Library Discovery");

    // Detect project type
    const projectType = await detectProjectType();
    const language = await detectLanguage();

    // Discover relevant libraries
    const libraries = await discoverLibraries(task, projectType, language);

    // Cache in Serena
    await serena.write_memory(`libraries_${task}`, libraries);

    console.log(`✓ Found ${libraries.length} relevant libraries`);
    if (libraries.length > 0) {
      console.log(`✓ Recommended: ${libraries[0].name}`);
    }
    console.log("");

    //═══════════════════════════════════════════════════════════
    // PHASE 3: Task Analysis (REUSES /shannon:analyze)
    //═══════════════════════════════════════════════════════════

    console.log("🔍 Phase 3/5: Task Analysis");

    // Invoke existing analyze skill
    const analysis = await invokeSkill('/shannon:analyze', task);

    console.log("✓ Analysis complete\n");

    //═══════════════════════════════════════════════════════════
    // PHASE 4: Execution Planning (Enhanced with libraries)
    //═══════════════════════════════════════════════════════════

    console.log("📋 Phase 4/5: Execution Planning");

    // Use sequential thinking to create plan
    const plan = await createExecutionPlan(task, analysis, libraries);

    // Save plan to session
    await serena.write_memory('exec_plan', plan);

    console.log(`✓ Plan created: ${plan.steps.length} steps`);
    console.log(`✓ Estimated duration: ${plan.estimated_minutes}min\n`);

    //═══════════════════════════════════════════════════════════
    // PHASE 5: Execution with Validation (Wraps /shannon:wave)
    //═══════════════════════════════════════════════════════════

    console.log("🚀 Phase 5/5: Execution");

    // Create git branch
    const branchName = generateBranchName(task);
    await useTool('run_terminal_cmd', `git checkout -b ${branchName}`);

    // Execute each step with validation
    for (const step of plan.steps) {
      console.log(`\nStep ${step.number}/${plan.steps.length}: ${step.description}`);

      let success = false;

      // Try up to 3 times
      for (let attempt = 0; attempt < 3; attempt++) {
        // Execute step using existing wave system
        const result = await executeStepViaWave(step);

        // Validate using Shannon CLI ValidationOrchestrator
        const validation = await validateStep(result, step.validation);

        if (validation.allPassed) {
          // Success! Commit
          const commitMsg = generateCommitMessage(step, validation);
          await useTool('run_terminal_cmd', `git add -A`);
          await useTool('run_terminal_cmd', `git commit -m "${commitMsg}"`);

          console.log(`✅ Step complete, committed`);
          success = true;
          break;
        } else {
          // Failed - analyze and retry
          console.log(`❌ Validation failed (attempt ${attempt + 1}/3)`);

          if (attempt < 2) {
            // Research solution
            const research = await researchFailure(validation.failures);

            // Create alternative approach
            step = await replanWithResearch(step, research);

            // Rollback
            await useTool('run_terminal_cmd', 'git reset --hard');

            console.log(`🔄 Retrying with alternative approach...`);
          }
        }
      }

      if (!success) {
        throw new Error(`Step ${step.number} failed after 3 attempts`);
      }
    }

    //═══════════════════════════════════════════════════════════
    // PHASE 6: Completion Report
    //═══════════════════════════════════════════════════════════

    return generateExecutionReport(plan, commits, validations);
  }
});

// Helper functions

async function executeStepViaWave(step: ExecutionStep) {
  // Convert step to WaveTask
  const waveTask = {
    task_id: `exec_step_${step.number}`,
    name: step.description,
    agent_type: selectAgentType(step.description),
    description: step.description,
    deliverables: step.expected_outputs
  };

  // Create minimal wave plan
  const wavePlan = {
    waves: [{
      number: 1,
      focus: step.description,
      tasks: [waveTask]
    }]
  };

  // Invoke existing /shannon:wave skill
  return await invokeSkill('/shannon:wave', JSON.stringify(wavePlan));
}

async function discoverLibraries(task, projectType, language) {
  // This calls out to Shannon CLI's LibraryDiscoverer
  // via custom tool or direct invocation

  // Use firecrawl MCP to search
  const query = `${language} ${task} library package`;
  const searchResults = await useTool('firecrawl_search', { query, limit: 10 });

  // Parse and rank
  const libraries = parseLibraryResults(searchResults, projectType);

  return libraries;
}

async function validateStep(result, validationCriteria) {
  // This calls Shannon CLI's ValidationOrchestrator
  // Shannon CLI has the validation logic, skill just invokes it

  // Via custom tool or skill invocation
  return await callCLIValidator(result, validationCriteria);
}
```

**Key Point**: The skill is ~400 lines because it ORCHESTRATES existing skills and delegates heavy lifting to Shannon CLI modules.

---

## Part 3: Library Discovery Module

### 3.1 LibraryDiscoverer Implementation

**File**: `src/shannon/executor/library_discoverer.py` (250 lines)

```python
"""
Library Discovery Module - Find open-source libraries instead of building from scratch

Integrates with:
- Firecrawl MCP (web search)
- Serena MCP (caching)
- Package registries (npm, PyPI, CocoaPods, etc.)
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json


@dataclass
class LibraryOption:
    """Single library option"""
    name: str
    description: str
    repository_url: str
    stars: int
    last_updated: datetime
    weekly_downloads: Optional[int]
    license: str
    compatibility_score: float  # 0-1
    overall_score: float  # 0-100


class LibraryDiscoverer:
    """
    Discover and recommend open-source libraries for features

    Uses firecrawl MCP for search, Serena MCP for caching.
    Integrates with package registries (npm, PyPI, CocoaPods, Maven, crates.io).
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.project_type = self._detect_project_type()
        self.language = self._detect_language()

    async def discover_for_feature(
        self,
        feature_description: str,
        category: str = "general"  # ui, auth, networking, data, etc.
    ) -> List[LibraryOption]:
        """
        Discover libraries for a specific feature

        Args:
            feature_description: "authentication", "UI components", "SSH client", etc.
            category: Feature category for better search

        Returns:
            Ranked list of library options (best first)
        """
        # 1. Check Serena cache
        cache_key = f"libraries_{self.language}_{feature_description}"
        cached = await self._check_serena_cache(cache_key)

        if cached:
            return cached

        # 2. Search package registry
        if self.language in ["javascript", "typescript"]:
            results = await self._search_npm(feature_description)
        elif self.language == "python":
            results = await self._search_pypi(feature_description)
        elif self.language == "swift":
            results = await self._search_swift_packages(feature_description)
        elif self.language == "java":
            results = await self._search_maven(feature_description)
        else:
            results = await self._generic_search(feature_description)

        # 3. Rank by quality
        ranked = self._rank_libraries(results)

        # 4. Cache in Serena
        await self._cache_in_serena(cache_key, ranked)

        return ranked[:5]  # Top 5

    async def _search_npm(self, feature: str) -> List[Dict]:
        """Search npm registry using firecrawl MCP"""

        # Check if firecrawl MCP available
        try:
            from shannon.mcp.manager import MCPManager
            mcp_mgr = MCPManager()

            if mcp_mgr.is_available('firecrawl'):
                # Use firecrawl to search npm
                query = f"npm {feature} package"
                results = await mcp_mgr.invoke(
                    'firecrawl',
                    'search',
                    {
                        'query': query,
                        'limit': 10,
                        'scrapeOptions': {'formats': ['markdown']}
                    }
                )

                return self._parse_npm_results(results)
        except:
            pass

        # Fallback: Direct npm API or web search
        return await self._fallback_npm_search(feature)

    async def _search_swift_packages(self, feature: str) -> List[Dict]:
        """Search Swift packages using GitHub + SwiftPackageIndex"""

        query = f"Swift {feature} library site:github.com OR site:swiftpackageindex.com"

        # Use firecrawl MCP
        results = await self._web_search(query)

        # Parse GitHub repos
        packages = []
        for result in results:
            if 'github.com' in result['url']:
                pkg = await self._fetch_github_metadata(result['url'])
                packages.append(pkg)

        return packages

    def _rank_libraries(self, libraries: List[Dict]) -> List[LibraryOption]:
        """Rank libraries by quality metrics"""

        ranked = []

        for lib in libraries:
            score = self._calculate_score(lib)

            ranked.append(LibraryOption(
                name=lib['name'],
                description=lib['description'],
                repository_url=lib['repository_url'],
                stars=lib.get('stars', 0),
                last_updated=lib.get('last_updated', datetime.now()),
                weekly_downloads=lib.get('downloads'),
                license=lib.get('license', 'Unknown'),
                compatibility_score=self._check_compatibility(lib),
                overall_score=score
            ))

        return sorted(ranked, key=lambda x: x.overall_score, reverse=True)

    def _calculate_score(self, lib: Dict) -> float:
        """Calculate overall quality score (0-100)"""

        score = 0.0

        # Stars weight: 40%
        stars = lib.get('stars', 0)
        if stars > 10000:
            score += 40
        elif stars > 1000:
            score += 30
        elif stars > 100:
            score += 20
        else:
            score += 10

        # Maintenance weight: 30%
        last_updated = lib.get('last_updated')
        if last_updated:
            days_ago = (datetime.now() - last_updated).days
            if days_ago < 30:
                score += 30  # Very active
            elif days_ago < 180:
                score += 20  # Active
            elif days_ago < 365:
                score += 10  # Maintained
            # else: 0 points (abandoned)

        # Downloads weight: 20%
        downloads = lib.get('downloads', 0)
        if downloads > 100000:
            score += 20
        elif downloads > 10000:
            score += 15
        elif downloads > 1000:
            score += 10

        # License weight: 10%
        license = lib.get('license', '').lower()
        if any(l in license for l in ['mit', 'apache', 'bsd']):
            score += 10
        elif 'isc' in license:
            score += 8

        return score

    def _check_compatibility(self, lib: Dict) -> float:
        """Check compatibility with current project (0-1)"""

        # Check if library works with current framework versions
        # Check peer dependencies
        # Check platform compatibility (iOS version, React version, etc.)

        # Simplified for now
        return 1.0  # Assume compatible, actual check would parse package.json/Podfile

    async def _check_serena_cache(self, key: str) -> Optional[List[LibraryOption]]:
        """Check if we've already discovered libraries for this feature"""

        try:
            from shannon.mcp.manager import MCPManager
            mcp = MCPManager()

            cached = await mcp.invoke('serena', 'read_memory', {'key': key})

            if cached:
                # Check if cache is recent (< 7 days)
                cached_at = datetime.fromisoformat(cached.get('cached_at'))
                if (datetime.now() - cached_at) < timedelta(days=7):
                    return cached['libraries']
        except:
            pass

        return None

    async def _cache_in_serena(self, key: str, libraries: List[LibraryOption]):
        """Cache discovered libraries in Serena MCP"""

        try:
            from shannon.mcp.manager import MCPManager
            mcp = MCPManager()

            await mcp.invoke('serena', 'write_memory', {
                'key': key,
                'data': {
                    'libraries': [lib.__dict__ for lib in libraries],
                    'cached_at': datetime.now().isoformat()
                }
            })
        except:
            pass  # Cache failure is non-fatal
```

**Key Integration Points**:
- Uses existing `MCPManager` to access firecrawl and Serena
- Caches discoveries in Serena MCP (existing system)
- Auto-detects project type using existing detection logic
- Returns structured recommendations for planning phase

---

## Part 3: Validation Orchestrator

### 3.1 ValidationOrchestrator Implementation

**File**: `src/shannon/executor/validator.py` (300 lines)

```python
"""
Validation Orchestrator - 3-tier validation framework

Integrates with:
- Existing project test infrastructure (auto-detected)
- Available MCPs (firecrawl, puppeteer for functional testing)
- Shannon analytics DB (for tracking)
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from pathlib import Path
import json


@dataclass
class ValidationResult:
    """Results from 3-tier validation"""
    tier1_passed: bool  # Static (build, lint, types)
    tier2_passed: bool  # Unit/Integration tests
    tier3_passed: bool  # Functional (E2E, user perspective)

    tier1_details: Dict[str, Any]
    tier2_details: Dict[str, Any]
    tier3_details: Dict[str, Any]

    failures: List[str]
    duration_seconds: float

    @property
    def all_passed(self) -> bool:
        return self.tier1_passed and self.tier2_passed and self.tier3_passed


class ValidationOrchestrator:
    """
    Orchestrates 3-tier validation using existing test infrastructure

    Auto-detects test commands from:
    - package.json scripts (npm test, npm run e2e)
    - pyproject.toml (pytest config)
    - Xcode project (xcodebuild test)
    - Maven/Gradle files
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_config = self._auto_detect_tests()

    def _auto_detect_tests(self) -> Dict[str, Any]:
        """Auto-detect how to test this project"""

        config = {
            'project_type': None,
            'build_cmd': None,
            'type_check_cmd': None,
            'lint_cmd': None,
            'test_cmd': None,
            'e2e_cmd': None,
            'start_cmd': None
        }

        # Check for Node.js project
        package_json = self.project_root / 'package.json'
        if package_json.exists():
            data = json.loads(package_json.read_text())
            scripts = data.get('scripts', {})

            config['project_type'] = 'nodejs'
            config['build_cmd'] = scripts.get('build', 'npm run build')
            config['type_check_cmd'] = scripts.get('type-check', 'npx tsc --noEmit')
            config['lint_cmd'] = scripts.get('lint')
            config['test_cmd'] = scripts.get('test', 'npm test')
            config['e2e_cmd'] = scripts.get('e2e') or scripts.get('test:e2e')
            config['start_cmd'] = scripts.get('start') or scripts.get('dev')

        # Check for Python project
        elif (self.project_root / 'pyproject.toml').exists() or \
             (self.project_root / 'pytest.ini').exists():
            config['project_type'] = 'python'
            config['type_check_cmd'] = 'mypy .'
            config['lint_cmd'] = 'ruff check .'
            config['test_cmd'] = 'pytest tests/'
            config['start_cmd'] = self._detect_python_start()

        # Check for iOS project
        elif list(self.project_root.glob('*.xcodeproj')):
            config['project_type'] = 'ios'
            config['build_cmd'] = 'xcodebuild'
            config['test_cmd'] = 'xcodebuild test'
            config['lint_cmd'] = 'swiftlint'

        return config

    async def validate_tier1(self, changes: ChangeSet) -> TierResult:
        """Tier 1: Static validation (build, lint, types)"""

        results = {}
        failures = []

        # Build
        if self.test_config['build_cmd']:
            build_result = await run_command(self.test_config['build_cmd'])
            results['build'] = build_result.success
            if not build_result.success:
                failures.append(f"Build failed: {build_result.error}")

        # Type check
        if self.test_config['type_check_cmd']:
            type_result = await run_command(self.test_config['type_check_cmd'])
            results['type_check'] = type_result.success
            if not type_result.success:
                failures.append(f"Type check failed: {type_result.error}")

        # Lint
        if self.test_config['lint_cmd']:
            lint_result = await run_command(self.test_config['lint_cmd'])
            results['lint'] = lint_result.success
            if not lint_result.success:
                failures.append(f"Lint failed: {lint_result.error}")

        return TierResult(
            passed=len(failures) == 0,
            details=results,
            failures=failures
        )

    async def validate_tier2(self, changes: ChangeSet) -> TierResult:
        """Tier 2: Unit/Integration tests"""

        if not self.test_config['test_cmd']:
            return TierResult(passed=True, details={'skipped': True}, failures=[])

        # Run test suite
        test_result = await run_command(self.test_config['test_cmd'])

        if test_result.success:
            return TierResult(
                passed=True,
                details={'test_output': test_result.output},
                failures=[]
            )
        else:
            return TierResult(
                passed=False,
                details={'test_output': test_result.output},
                failures=[f"Tests failed: {test_result.error}"]
            )

    async def validate_tier3(
        self,
        changes: ChangeSet,
        functional_criteria: List[str]
    ) -> TierResult:
        """Tier 3: Functional validation from user perspective"""

        results = {}
        failures = []

        # Strategy depends on project type
        if self.test_config['project_type'] == 'nodejs':
            result = await self._validate_nodejs_functional(functional_criteria)
        elif self.test_config['project_type'] == 'python':
            result = await self._validate_python_functional(functional_criteria)
        elif self.test_config['project_type'] == 'ios':
            result = await self._validate_ios_functional(functional_criteria)
        else:
            result = TierResult(passed=True, details={'skipped': True}, failures=[])

        return result

    async def _validate_nodejs_functional(self, criteria: List[str]) -> TierResult:
        """Functional validation for Node.js apps"""

        # 1. Start app
        if self.test_config['start_cmd']:
            # Start in background
            await run_command_bg(self.test_config['start_cmd'])
            await asyncio.sleep(5)  # Wait for startup

        # 2. Run E2E tests if available
        if self.test_config['e2e_cmd']:
            e2e_result = await run_command(self.test_config['e2e_cmd'])
            if not e2e_result.success:
                return TierResult(
                    passed=False,
                    details={'e2e': e2e_result.output},
                    failures=["E2E tests failed"]
                )

        # 3. Check health endpoint
        health_check = await run_command("curl http://localhost:3000/health")

        return TierResult(
            passed=health_check.success,
            details={'health_check': health_check.output},
            failures=[] if health_check.success else ["Health check failed"]
        )

    async def _validate_ios_functional(self, criteria: List[str]) -> TierResult:
        """Functional validation for iOS apps"""

        # 1. Boot simulator
        await run_command('xcrun simctl boot "iPhone 14"')

        # 2. Run UI tests
        test_result = await run_command(
            'xcodebuild test -scheme MyApp -destination "platform=iOS Simulator,name=iPhone 14"'
        )

        return TierResult(
            passed=test_result.success,
            details={'ui_tests': test_result.output},
            failures=[] if test_result.success else ["UI tests failed"]
        )
```

**Key Integration Points**:
- Auto-detects tests from project files (package.json, pyproject.toml, etc.)
- Uses existing `run_terminal_cmd` via SDK
- Integrates with available MCPs (firecrawl for web validation, puppeteer if available)
- Returns structured results for decision making

---

## Part 4: Git Manager

### 4.1 GitManager Implementation

**File**: `src/shannon/executor/git_manager.py` (200 lines)

```python
"""
Git Manager - Atomic commits with rollback

All git operations via run_terminal_cmd for transparency.
Uses Shannon analytics DB to track commit history.
"""

from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path


@dataclass
class GitCommit:
    """Single git commit"""
    hash: str
    message: str
    files: List[str]
    validation_passed: bool
    timestamp: str


class GitManager:
    """
    Manages git operations for autonomous execution

    Guarantees:
    - Only commits validated changes
    - Atomic commits (one step = one commit)
    - Descriptive messages
    - Clean rollback on failure
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.commits: List[GitCommit] = []

    async def ensure_clean_state(self) -> bool:
        """Verify git working directory is clean"""

        status = await self._run_git('status --porcelain')

        if status.strip():
            # Uncommitted changes exist
            return False

        return True

    async def create_feature_branch(self, task: str) -> str:
        """Create feature branch with descriptive name"""

        branch_name = self._generate_branch_name(task)

        await self._run_git(f'checkout -b {branch_name}')

        return branch_name

    async def commit_validated_changes(
        self,
        files: List[str],
        step_description: str,
        validation_result: ValidationResult
    ) -> GitCommit:
        """Commit changes after successful validation"""

        # Generate commit message
        commit_msg = self._generate_commit_message(
            step_description,
            validation_result
        )

        # Stage files
        for file in files:
            await self._run_git(f'add {file}')

        # Commit
        await self._run_git(f'commit -m "{commit_msg}"')

        # Get commit hash
        commit_hash = await self._run_git('rev-parse HEAD')

        # Track commit
        commit = GitCommit(
            hash=commit_hash.strip(),
            message=commit_msg,
            files=files,
            validation_passed=True,
            timestamp=datetime.now().isoformat()
        )

        self.commits.append(commit)

        # Store in analytics DB
        await self._track_commit(commit)

        return commit

    async def rollback_to_last_commit(self) -> bool:
        """Rollback failed changes to last good state"""

        await self._run_git('reset --hard HEAD')
        await self._run_git('clean -fd')

        # Verify clean
        status = await self._run_git('status --porcelain')
        return status.strip() == ''

    def _generate_branch_name(self, task: str) -> str:
        """Generate descriptive branch name"""

        # Extract keywords
        words = [w for w in task.lower().split() if len(w) > 3][:4]
        slug = '-'.join(words)

        # Determine prefix
        if any(w in task.lower() for w in ['fix', 'bug', 'broken', 'error']):
            prefix = 'fix'
        elif any(w in task.lower() for w in ['add', 'new', 'create', 'implement']):
            prefix = 'feat'
        elif any(w in task.lower() for w in ['optimize', 'performance', 'slow', 'faster']):
            prefix = 'perf'
        elif any(w in task.lower() for w in ['refactor', 'restructure', 'clean']):
            prefix = 'refactor'
        else:
            prefix = 'chore'

        return f"{prefix}/{slug}"

    def _generate_commit_message(
        self,
        step_description: str,
        validation: ValidationResult
    ) -> str:
        """Generate descriptive commit message"""

        # Format:
        # <type>: <summary>
        #
        # WHY: <reasoning>
        # WHAT: <changes>
        # VALIDATION: <results>

        commit_type = self._determine_commit_type(step_description)

        message = f"{commit_type}: {step_description}\n\n"
        message += f"VALIDATION:\n"
        message += f"- Build: {'PASS' if validation.tier1_passed else 'SKIP'}\n"
        message += f"- Tests: {'PASS' if validation.tier2_passed else 'SKIP'}\n"
        message += f"- Functional: {'PASS' if validation.tier3_passed else 'SKIP'}\n"

        return message

    async def _run_git(self, command: str) -> str:
        """Run git command via run_terminal_cmd"""

        from shannon.sdk.client import ShannonSDKClient

        # Use SDK's run_terminal_cmd
        # (Would need helper method, simplified here)
        result = await run_terminal_cmd(f'git {command}', cwd=self.project_root)
        return result.output
```

**Key Integration Points**:
- Uses `run_terminal_cmd` for all git operations (transparent in dashboard)
- Stores commits in Shannon analytics DB
- Generates semantic commit messages
- Clean rollback using git reset

---

## Part 5: Implementation Roadmap (REVISED)

### 5.1 What We're Actually Building

**Shannon Framework** (separate repo):
```
shannon-framework/
└── .claude-skills/
    ├── exec.ts                    (400 lines) NEW SKILL
    └── prompts/
        └── exec-enhancements.md   (200 lines) ENHANCED PROMPTS
```

**Shannon CLI** (this repo):
```
src/shannon/
├── executor/                      NEW MODULE
│   ├── __init__.py
│   ├── library_discoverer.py      (250 lines)
│   ├── validator.py               (300 lines)
│   ├─ git_manager.py              (200 lines)
│   ├── prompt_enhancer.py         (150 lines)
│   └── models.py                  (100 lines)
│
├── cli/
│   └── commands.py                (+150 lines) - exec command
│
├── analytics/
│   ├── schema.sql                 (+100 lines) - exec tables
│   └── database.py                (+100 lines) - exec tracking
│
└── sdk/
    └── client.py                  (+50 lines) - custom prompt support
```

**TOTAL NEW CODE**:
- Shannon Framework: 600 lines (1 skill + prompts)
- Shannon CLI: 1,250 lines (executor module + modifications)
- **GRAND TOTAL: ~1,850 lines**

**REUSED EXISTING**:
- All 18 existing skills (~8,000 lines)
- AgentController, ContextManager (~2,000 lines)
- SessionManager, Analytics (~1,500 lines)
- V3.1 Dashboard (~3,000 lines)
- **TOTAL REUSED: ~15,000+ lines**

### 5.2 Revised Wave Plan

**Wave 1: Enhanced System Prompts** (1 day, 350 lines)
- Create `exec-enhancements.md` in Shannon Framework
- Create `prompt_enhancer.py` in Shannon CLI
- Add support for `system_prompt.append` in ShannonSDKClient
- Functional test: Verify prompts injected correctly

**Wave 2: Library Discovery** (2 days, 250 lines)
- Create `library_discoverer.py`
- Integration with firecrawl MCP (search)
- Integration with Serena MCP (caching)
- Functional test: Discover React Native UI library, verify recommendation

**Wave 3: Validation Orchestrator** (2 days, 400 lines)
- Create `validator.py`
- Auto-detection of project test infrastructure
- 3-tier validation implementation
- Functional test: Run all 3 tiers on sample project, verify results

**Wave 4: Git Manager** (1 day, 200 lines)
- Create `git_manager.py`
- Branch creation, atomic commits, rollback
- Commit message generation
- Functional test: Make change → validate → commit → verify

**Wave 5: Exec Skill + CLI Integration** (2 days, 750 lines)
- Create `exec.ts` skill in Shannon Framework
- Create `exec` CLI command
- Add analytics tracking (tables + Python models)
- Orchestrate all phases
- Functional test: Full end-to-end `shannon exec "task"`

| Wave | Duration | New Code | Reused | Tests |
|------|----------|----------|--------|-------|
| Wave 1 | 1 day | 350 lines | ShannonSDKClient | 1 |
| Wave 2 | 2 days | 250 lines | MCPManager, Serena | 1 |
| Wave 3 | 2 days | 400 lines | run_terminal_cmd | 1 |
| Wave 4 | 1 day | 200 lines | Analytics DB | 1 |
| Wave 5 | 2 days | 750 lines | All skills, V3.1 dashboard | 4 |
| **Total** | **8 days** | **1,950 lines** | **15,000+ lines** | **8** |

---

## Part 6: Integration with Existing Systems

### 6.1 How It Uses Existing Skills

```typescript
// In /shannon:exec skill

// PHASE 1: Context (uses /shannon:prime)
await invokeSkill('/shannon:prime', {
  project: process.cwd(),
  task_focused: true,  // NEW parameter
  keywords: extractKeywords(task)
});
// Existing prime skill handles codebase scanning

// PHASE 3: Analysis (uses /shannon:analyze)
const analysis = await invokeSkill('/shannon:analyze', task);
// Existing analyze skill does 8D complexity

// PHASE 5: Execution (uses /shannon:wave)
const waveResult = await invokeSkill('/shannon:wave', wavePlan);
// Existing wave skill handles agent orchestration
```

### 6.2 How It Uses Serena MCP

```typescript
// Cache library discoveries
await serena.write_memory('libraries_react_ui', {
  libraries: discoveredLibs,
  cached_at: new Date().toISOString()
});

// Cache project context
await serena.write_memory(`project_${projectHash}`, {
  type: 'react-native',
  files: relevantFiles,
  dependencies: packageJson.dependencies
});

// Cache research results
await serena.write_memory('research_ios_safe_area', {
  summary: "Use safeAreaLayoutGuide for iPhone X+",
  sources: [...],
  cached_at: new Date().toISOString()
});

// Next execution in same project: loads from cache (5s vs 30s)
```

### 6.3 How It Uses Analytics DB

```python
# After execution completes
from shannon.analytics.database import Database

db = Database()

# Store execution record
db.store_execution({
    'id': execution_id,
    'task': task_description,
    'status': 'complete',
    'steps_total': len(plan.steps),
    'steps_completed': completed_count,
    'commits_created': len(commits),
    'duration_seconds': total_duration,
    'cost_usd': total_cost,
    'libraries_used': [lib.name for lib in libraries]
})

# Shannon can LEARN from history:
# "Last time I fixed iOS login, I used SnapKit successfully"
# "React apps usually pass with these validation commands"
```

### 6.4 How It Uses V3.1 Dashboard

```python
# Dashboard shows execution in real-time

# Layer 1: Execution overview
# "Task: fix iOS login - Phase 4/5: Execution - 60%"

# Layer 2: Step breakdown (adapted for exec)
# Step 1: ✅ Complete (validated, committed)
# Step 2: 🔄 Active (validating)
# Step 3: ⏸️ Pending

# Layer 3: Current step detail
# "Running Tier 3 validation: iOS Simulator"

# Layer 4: Message stream
# All SDK messages from /shannon:exec skill execution
```

---

## Part 7: Concrete Example - How It All Works

### Example: "Build React Native Expo Todo App"

```bash
$ shannon exec "build React Native Expo todo app with Material Design"

🎯 Shannon V3.5 Autonomous Executor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CLI: Builds enhanced system prompts
  └─ Library discovery instructions
  └─ React Native best practices
  └─ Functional validation requirements
  └─ Git workflow requirements

SDK: Creates ClaudeAgentOptions
  └─ system_prompt.append = enhanced_instructions
  └─ Loads Shannon Framework plugin
  └─ Invokes /shannon:exec

SHANNON FRAMEWORK /shannon:exec SKILL:

Phase 1: Context (invokes /shannon:prime)
  → ContextManager scans for React Native files
  → Loads only relevant context (not entire codebase)
  → Serena MCP caches context
  ✓ Context ready (8s)

Phase 2: Library Discovery (NEW)
  → LibraryDiscoverer searches npm
  → Query: "React Native Material Design Expo"
  → Finds: react-native-paper (10k stars, actively maintained)
  → Finds: expo-router (official Expo navigation)
  → Recommends: react-native-paper for UI
  → Caches in Serena MCP
  ✓ Libraries discovered (12s)

Phase 3: Analysis (invokes /shannon:analyze)
  → Analyzes "todo app" complexity
  → Result: 0.3 (simple)
  → Domains: [Mobile, Frontend]
  ✓ Analysis complete (15s)

Phase 4: Planning (uses sequential-thinking MCP)
  → Creates plan with discovered libraries:
    Step 1: npx create-expo-app todo-app
    Step 2: npm install react-native-paper expo-router
    Step 3: Setup navigation (3 screens)
    Step 4: Build todo list screen (use react-native-paper components)
    Step 5: Build add todo screen (use react-native-paper form)
    Step 6: Implement AsyncStorage for persistence
    Step 7: Test in Expo Go
  → Each step has validation criteria
  ✓ Plan ready (20s)

Phase 5: Execution (invokes /shannon:wave per step)
  → Creates git branch: feat/expo-todo-app

  [For each step]

  Step 1: Create Expo app
    → Executes via /shannon:wave
    → Validation Tier 1: ✅ Project created
    → Validation Tier 2: ✅ Can run expo start
    → Validation Tier 3: ✅ App loads in Expo Go
    → GitManager commits: abc123 "Initialize Expo todo app"
    → Time: 45s

  Step 2: Install libraries
    → Executes: npm install react-native-paper expo-router
    → Validation Tier 1: ✅ Build succeeds
    → Validation Tier 2: ✅ Imports work
    → Validation Tier 3: ✅ App still runs
    → GitManager commits: def456 "Add react-native-paper and expo-router"
    → Time: 30s

  Step 3: Setup navigation
    → Executes via /shannon:wave (creates routes)
    → Uses expo-router (from discovered libraries)
    → Validation Tier 1: ✅ Type check passes
    → Validation Tier 2: ✅ Navigation tests pass
    → Validation Tier 3: ✅ Can navigate between screens in app
    → GitManager commits: ghi789 "Setup navigation with expo-router"
    → Time: 2m 15s

  Step 4: Build todo list screen
    → Executes via /shannon:wave
    → Uses react-native-paper List, Card components (NOT custom)
    → Validation Tier 1: ✅ Builds
    → Validation Tier 2: ✅ Component tests pass
    → Validation Tier 3: ✅ Screen renders, can see todos
    → GitManager commits: jkl012 "Implement todo list screen with react-native-paper"
    → Time: 3m 30s

  [Steps 5-7 continue similarly...]

  ✓ All steps complete (total: 11m 45s)

Phase 6: Report
  ✅ Task complete!

  Changes:
    • Created 12 new files
    • Modified 3 existing files

  Commits:
    • abc123 Initialize Expo todo app
    • def456 Add react-native-paper and expo-router
    • ghi789 Setup navigation with expo-router
    • jkl012 Implement todo list screen
    • mno345 Implement add todo screen
    • pqr678 Add AsyncStorage persistence
    • stu901 Test complete flow in Expo Go

  Libraries Used:
    ✓ expo (official framework)
    ✓ react-native-paper (Material Design UI)
    ✓ expo-router (navigation)

  Validations:
    ✅ Build: All steps passed
    ✅ Tests: All created tests passing
    ✅ Functional: App works in Expo Go

  Branch: feat/expo-todo-app-material
  Ready for: git push + PR

  Time: 11m 45s
  Cost: $0.89
```

### Key Observations

✅ **Uses react-native-paper** (didn't build custom UI components)
✅ **Uses expo-router** (didn't build custom navigation)
✅ **Each step validated** before committing
✅ **Atomic commits** with descriptive messages
✅ **Functional testing** (app actually works in Expo Go)
✅ **Built on existing** `/shannon:wave` execution

---

## Part 8: Complete File Structure

### 8.1 Shannon Framework Changes

```
shannon-framework/ (separate repo)
└── .claude-skills/
    ├── exec.ts                          (400 lines) NEW
    └── prompts/
        ├── exec-enhancements.md         (200 lines) NEW
        ├── ios-guidelines.md            (100 lines) NEW
        ├── react-guidelines.md          (100 lines) NEW
        └── python-guidelines.md         (100 lines) NEW
```

### 8.2 Shannon CLI Changes

```
src/shannon/
├── executor/                            NEW MODULE
│   ├── __init__.py
│   ├── library_discoverer.py            (250 lines)
│   ├── validator.py                     (300 lines)
│   ├── git_manager.py                   (200 lines)
│   ├── prompt_enhancer.py               (150 lines)
│   ├── prompts.py                       (150 lines) - Prompt templates
│   ├── task_enhancements.py             (100 lines) - Project-specific prompts
│   └── models.py                        (100 lines) - Data models
│
├── cli/
│   └── commands.py                      (+150 lines) - exec command
│
├── analytics/
│   ├── schema.sql                       (+100 lines) - exec tables
│   └── database.py                      (+100 lines) - exec tracking
│
└── sdk/
    └── client.py                        (+50 lines) - custom prompt support
```

### 8.3 Lines of Code Breakdown

| Component | Lines | Type |
|-----------|-------|------|
| Shannon Framework: exec skill | 400 | NEW |
| Shannon Framework: prompts | 500 | NEW |
| Shannon CLI: executor module | 1,250 | NEW |
| Shannon CLI: CLI command | 150 | MODIFY |
| Shannon CLI: analytics | 200 | MODIFY |
| Shannon CLI: SDK | 50 | MODIFY |
| **Total NEW** | **1,850** | |
| **Total MODIFY** | **400** | |
| **Total REUSED** | **15,000+** | |

---

## Part 9: System Prompt Examples

### 9.1 Complete Enhanced Prompt (What Gets Injected)

When user runs: `shannon exec "add authentication to React app"`

The system prompt becomes:
```
[Claude Code base prompt]

[PLUS V3.5 enhancements:]

═══════════════════════════════════════════════════════════════
 CRITICAL: Research and Use Existing Libraries
═══════════════════════════════════════════════════════════════

[... library discovery instructions ...]

For this task (authentication), consider:
  - next-auth (if Next.js)
  - @auth0/nextjs-auth0 (if need Auth0)
  - clerk (modern auth, good DX)
  - supabase/auth-helpers (if using Supabase)

DO NOT build custom authentication system.

═══════════════════════════════════════════════════════════════
 CRITICAL: Functional Validation from User Perspective
═══════════════════════════════════════════════════════════════

[... functional validation instructions ...]

For React apps:
  Tier 1: npm run build + npm run type-check
  Tier 2: npm test
  Tier 3: npm run dev + test in browser

═══════════════════════════════════════════════════════════════
 CRITICAL: Atomic Git Commits
═══════════════════════════════════════════════════════════════

[... git workflow instructions ...]

═══════════════════════════════════════════════════════════════
 React/Next.js Best Practices (auto-detected)
═══════════════════════════════════════════════════════════════

- Use TypeScript strict mode
- Use functional components with hooks
- Prefer server components (Next.js 14+)
- Common libraries: shadcn/ui, react-hook-form, zod, tanstack/react-query

Validation: Build + Type check + Test + Run in browser
```

This complete prompt ensures the agent:
- Searches for next-auth (doesn't build custom auth)
- Validates functionally (actually runs the app)
- Commits atomically (each validated change)
- Follows React best practices

---

## Part 10: Why This Spec is Better

### 10.1 Comparison

| Aspect | Original V3.5 | Revised V3.5 |
|--------|---------------|--------------|
| New code | 2,350 lines | 1,850 lines |
| Reused code | Minimal | 15,000+ lines |
| Timeline | 11 days | 8 days |
| Integration | Separate system | Builds on existing |
| Skills | New implementation | Reuses existing 18 skills |
| Context | New system | Reuses ContextManager |
| Agents | New orchestration | Reuses AgentController |
| MCPs | New integration | Uses existing MCP system |
| Dashboard | Needs work | Uses V3.1 as-is |
| Realistic | Maybe | YES ✅ |

### 10.2 What Makes This Practical

✅ **Builds on existing Shannon Framework** - 18 skills already work
✅ **Reuses existing systems** - Context, agents, session, analytics, dashboard
✅ **Integrates existing MCPs** - Serena, sequential-thinking, firecrawl
✅ **Simple additions** - Just orchestration layer + validation + git
✅ **Realistic timeline** - 8 days because 90% already exists
✅ **Clear integration points** - System prompts, skill invocations, MCP calls

---

## Part 11: Addressing ALL User Requirements

### Requirement Checklist

✅ **"Leverage current Shannon framework"** - Reuses all 18 skills
✅ **"Build upon Claude Code"** - Uses ClaudeAgentOptions.system_prompt.append
✅ **"Utilize existing skills and commands"** - Invokes /shannon:prime, /shannon:analyze, /shannon:wave
✅ **"Use pod agent SDK"** - Existing AgentController, no changes needed
✅ **"Use our database"** - Analytics DB tracks executions
✅ **"Use JSON files"** - SessionManager stores plans/results
✅ **"Use Serena MCP"** - Caching for libraries, context, research
✅ **"Append to system prompt with custom instructions"** - Yes! ClaudeAgentOptions.system_prompt.append
✅ **"Research libraries, don't reinvent wheel"** - LibraryDiscoverer + enhanced prompts enforce this
✅ **"Functional validation from user endpoint"** - 3-tier validation with Tier 3 focused on user perspective
✅ **"Git integration"** - GitManager with atomic commits
✅ **"Automatically apply and systematically execute"** - Full orchestration loop

ALL requirements met with REALISTIC, BUILDABLE architecture.

---

## Conclusion: The Real V3.5

Shannon V3.5 is:

**NOT**: A separate autonomous system replacing Shannon
**IS**: An enhancement layer that makes Shannon autonomous

**Adds**: ~1,850 lines of orchestration, validation, and git automation
**Reuses**: ~15,000+ lines of existing Shannon infrastructure
**Timeline**: 8 days (realistic)
**Result**: `shannon exec "anything"` → working code with commits

**The Magic**: Enhanced system prompts + library discovery + validation loop + git automation wrapped around existing Shannon skills.

This is BUILDABLE, PRACTICAL, and POWERFUL.

---

**Status**: ✅ REVISED SPECIFICATION COMPLETE

Next: Review, approve, begin Wave 1 implementation


---

## APPENDIX A: Complete Library Discovery Examples

### A.1 React Native SSH Feature

**Task**: "Add SSH connection feature to React Native app"

**Library Discovery Process**:
```
1. Detect: React Native project (package.json has "react-native")
2. Search npm: "react native SSH client"
3. Results: NONE (React Native doesn't support raw sockets)
4. Pivot: Search for "React Native terminal/SSH solution"
5. Find: react-native-tcp-socket (low-level, complex)
6. Alternative: Search "SSH over HTTP React Native"
7. Find: Web-based SSH libraries (xterm.js + websocket proxy)
8. Recommendation:
   - Backend: Use existing SSH library (ssh2 for Node.js)
   - Frontend: Use xterm.js for terminal UI
   - Connection: WebSocket proxy between RN app and backend
9. Plan updated: Build SSH proxy backend, use xterm.js frontend
10. Libraries added:
    - ssh2 (backend, 5k stars)
    - xterm.js (terminal UI, 15k stars)
    - ws (WebSocket, 20k stars)
```

**Key**: Discovered that direct SSH in React Native isn't feasible, pivoted to realistic WebSocket-proxy architecture using existing libraries.

### A.2 Swift UI iOS App

**Task**: "Build SwiftUI iOS app with image picker and editing"

**Library Discovery Process**:
```
1. Detect: iOS project (.xcodeproj present)
2. Search Swift Package Index: "SwiftUI image picker"
3. Results:
   - Native: PhotosUI (built-in iOS 16+)
   - Third-party: ImagePicker (unmaintained)
4. Recommendation: Use built-in PhotosUI (no external dependency)
5. Search: "SwiftUI image editing library"
6. Results:
   - Mantis (image cropping, 1.2k stars, maintained)
   - TOCropViewController (UIKit-based, 4k stars)
7. Recommendation: Mantis (SwiftUI-native)
8. Plan updated:
   Step 1: Use PhotosUI for picking (built-in)
   Step 2: Add Mantis via SPM for editing
   Step 3: Combine in workflow
9. Libraries added:
   - Mantis (SPM, image editing)
```

**Key**: Discovered built-in solution (PhotosUI) for picking, only added external library (Mantis) for editing which isn't built-in.

### A.3 Python FastAPI Project

**Task**: "Add background job processing to FastAPI app"

**Library Discovery Process**:
```
1. Detect: Python/FastAPI project (pyproject.toml, main.py with FastAPI)
2. Search PyPI: "Python background jobs async"
3. Results:
   - Celery (13k stars, battle-tested, requires Redis/RabbitMQ)
   - Arq (1.5k stars, Redis-based, async-native)
   - Dramatiq (3k stars, simpler than Celery)
   - FastAPI-BackgroundTasks (built-in, limited)
4. Evaluate:
   - Celery: Heavyweight but feature-rich
   - Arq: Lightweight, async, good for FastAPI
   - Built-in: Too limited for complex jobs
5. Recommendation: Arq (best for async FastAPI)
6. Plan updated:
   Step 1: pip install arq redis
   Step 2: Setup Redis connection
   Step 3: Define worker functions
   Step 4: Integrate with FastAPI endpoints
   Step 5: Test job execution
7. Libraries added:
   - arq (job queue)
   - redis (backend)
```

**Key**: Evaluated multiple options, chose Arq as best fit for async FastAPI (not heavyweight Celery).

---

## APPENDIX B: System Prompt Injection Details

### B.1 ClaudeAgentOptions Enhancement

**File**: `src/shannon/sdk/client.py` (modification, +50 lines)

```python
class ShannonSDKClient:
    async def invoke_command_with_enhancements(
        self,
        command: str,
        content: str,
        enhancements: str  # Custom system prompt additions
    ) -> AsyncIterator[Any]:
        """
        Invoke Shannon command with enhanced system prompts

        Args:
            command: Shannon command (/shannon:exec, /shannon:wave, etc.)
            content: Command content
            enhancements: Additional system prompt instructions

        Yields:
            SDK messages
        """
        # Create options with prompt enhancement
        enhanced_options = ClaudeAgentOptions(
            plugins=self.base_options.plugins,
            setting_sources=self.base_options.setting_sources,
            permission_mode=self.base_options.permission_mode,
            allowed_tools=self.base_options.allowed_tools,
            system_prompt={
                "type": "preset",
                "preset": "claude_code",
                "append": enhancements  # <-- INJECT custom instructions
            }
        )

        # Query with enhanced prompts
        prompt = f"{command} {content}"

        query_iterator = query(prompt=prompt, options=enhanced_options)

        # Return iterator (possibly with interception if V3 enabled)
        if self.enable_v3_features:
            return self.interceptor.intercept(query_iterator, self.message_collectors)
        else:
            return query_iterator
```

### B.2 Prompt Enhancement Builder

**File**: `src/shannon/executor/prompt_enhancer.py` (150 lines)

```python
"""
Prompt Enhancement Builder - Dynamically builds system prompt additions

Creates task-specific and project-specific prompt enhancements.
"""

from pathlib import Path
from typing import Optional
from .prompts import (
    LIBRARY_DISCOVERY_INSTRUCTIONS,
    FUNCTIONAL_VALIDATION_INSTRUCTIONS,
    GIT_WORKFLOW_INSTRUCTIONS
)
from .task_enhancements import (
    IOS_SWIFT_ENHANCEMENTS,
    REACT_NATIVE_ENHANCEMENTS,
    REACT_WEB_ENHANCEMENTS,
    PYTHON_FASTAPI_ENHANCEMENTS,
    get_enhancement_for_project
)


class PromptEnhancer:
    """
    Builds enhanced system prompts for autonomous execution

    Combines:
    - Core instructions (library discovery, validation, git)
    - Project-specific guidelines (iOS, React, Python, etc.)
    - Task-specific hints
    """

    def build_enhancements(
        self,
        task: str,
        project_root: Path
    ) -> str:
        """
        Build complete prompt enhancements

        Args:
            task: User's task description
            project_root: Project directory

        Returns:
            Complete enhancement text to append to system prompt
        """
        enhancements = []

        # Always include core instructions
        enhancements.append(LIBRARY_DISCOVERY_INSTRUCTIONS)
        enhancements.append(FUNCTIONAL_VALIDATION_INSTRUCTIONS)
        enhancements.append(GIT_WORKFLOW_INSTRUCTIONS)

        # Add project-specific guidelines
        project_type = self._detect_project_type(project_root)
        project_enhancement = get_enhancement_for_project(project_type)

        if project_enhancement:
            enhancements.append(project_enhancement)

        # Add task-specific hints
        task_hints = self._generate_task_hints(task, project_type)
        if task_hints:
            enhancements.append(task_hints)

        return "\n\n".join(enhancements)

    def _detect_project_type(self, project_root: Path) -> str:
        """Auto-detect project type"""

        if (project_root / 'package.json').exists():
            pkg = json.loads((project_root / 'package.json').read_text())
            deps = pkg.get('dependencies', {})

            if 'expo' in deps:
                return 'react-native-expo'
            elif 'react-native' in deps:
                return 'react-native'
            elif 'next' in deps:
                return 'next.js'
            elif 'react' in deps:
                return 'react'
            else:
                return 'nodejs'

        elif list(project_root.glob('*.xcodeproj')):
            # Check if SwiftUI or UIKit
            swift_files = list(project_root.rglob('*.swift'))
            if any('SwiftUI' in f.read_text() for f in swift_files[:10]):
                return 'ios-swiftui'
            else:
                return 'ios-uikit'

        elif (project_root / 'pyproject.toml').exists():
            toml = (project_root / 'pyproject.toml').read_text()
            if 'fastapi' in toml.lower():
                return 'python-fastapi'
            elif 'django' in toml.lower():
                return 'python-django'
            else:
                return 'python'

        return 'unknown'

    def _generate_task_hints(self, task: str, project_type: str) -> Optional[str]:
        """Generate hints specific to this task"""

        task_lower = task.lower()
        hints = []

        # Authentication hints
        if 'auth' in task_lower or 'login' in task_lower:
            if project_type.startswith('react'):
                hints.append("For React auth, consider: next-auth, Auth0 SDK, Clerk")
            elif project_type == 'ios-swiftui':
                hints.append("For iOS auth, use: AuthenticationServices (built-in Sign in with Apple)")
            elif project_type.startswith('python'):
                hints.append("For Python auth, consider: FastAPI-Users, django-allauth")

        # UI component hints
        if any(w in task_lower for w in ['ui', 'component', 'screen', 'view']):
            if project_type == 'react-native-expo':
                hints.append("For RN UI, use existing kit: react-native-paper, NativeBase, react-native-elements")
                hints.append("DO NOT build custom Button/Input/Card components")
            elif project_type.startswith('react'):
                hints.append("For React UI, use: shadcn/ui, MUI, Chakra UI")

        # Database hints
        if any(w in task_lower for w in ['database', 'db', 'query', 'migration']):
            if project_type == 'python-fastapi':
                hints.append("For FastAPI DB, use: SQLAlchemy + Alembic (migrations)")
            elif project_type.startswith('nodejs'):
                hints.append("For Node.js DB, use: Prisma (best DX), TypeORM, or Sequelize")

        if hints:
            return "TASK-SPECIFIC HINTS:\n" + "\n".join(f"  - {h}" for h in hints)

        return None
```

### B.3 Example Enhanced Prompt Output

For task "add dark mode to React Native Expo app":

```
[Base Claude Code prompt]

═══════════════════════════════════════════════════════════════
 CRITICAL: Research and Use Existing Libraries
═══════════════════════════════════════════════════════════════
[... full library discovery instructions ...]

═══════════════════════════════════════════════════════════════
 CRITICAL: Functional Validation from User Perspective
═══════════════════════════════════════════════════════════════
[... full validation instructions ...]

═══════════════════════════════════════════════════════════════
 CRITICAL: Atomic Git Commits per Validated Change
═══════════════════════════════════════════════════════════════
[... full git workflow instructions ...]

═══════════════════════════════════════════════════════════════
 React Native/Expo Best Practices
═══════════════════════════════════════════════════════════════
- Use Expo SDK when possible
- TypeScript strict mode
- Function components with hooks
- Common libraries:
  * UI: react-native-paper, NativeBase
  * Navigation: expo-router
  * State: Zustand, Jotai
- Validation: expo build + jest + Expo Go testing
- DO NOT build custom UI components

═══════════════════════════════════════════════════════════════
 TASK-SPECIFIC HINTS
═══════════════════════════════════════════════════════════════
  - For dark mode in Expo, research: expo-system-ui, react-native-paper theming
  - Consider: React Context for theme state, AsyncStorage for persistence
```

Every instruction in this prompt guides the agent to:
- Search for expo dark mode solutions
- Use libraries (react-native-paper themes)
- Validate by running in Expo Go
- Commit after validation

---

## APPENDIX C: Complete Execution Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Shannon V3.5 Complete Flow                       │
└─────────────────────────────────────────────────────────────────────┘

User Command:
  $ shannon exec "fix slow database query"

↓

[CLI: src/shannon/cli/commands.py]
  • Detect project type: Python/FastAPI
  • Build enhanced prompts:
    - Library discovery
    - Python/FastAPI best practices
    - Functional validation
    - Git workflow
  • Create ClaudeAgentOptions with system_prompt.append
  • Invoke: ShannonSDKClient.invoke_command('/shannon:exec', task, enhancements)

↓

[SDK: src/shannon/sdk/client.py]
  • Load Shannon Framework plugin
  • Inject enhanced prompts into system
  • Call Claude Agent SDK query()
  • Return message stream

↓

[CLAUDE AGENT SDK]
  • Loads Shannon Framework from ~/.claude/plugins/shannon/
  • Applies enhanced system prompts
  • Makes Shannon Framework skills available
  • Streams messages back

↓

[SHANNON FRAMEWORK: /shannon:exec skill]

PHASE 1: Context
  → invokeSkill('/shannon:prime')
    → EXISTING ContextManager loads relevant files
    → Ser ena caches context
  → Result: Context ready

PHASE 2: Library Discovery
  → Call LibraryDiscoverer (Shannon CLI module)
  → Search PyPI: "Python database query optimization"
  → Find: sqlalchemy-utils, alembic-postgresql-enum, etc.
  → Serena caches results
  → Result: Library recommendations

PHASE 3: Analysis
  → invokeSkill('/shannon:analyze')
    → EXISTING analyze skill runs 8D analysis
  → Result: Complexity, domains, recommendations

PHASE 4: Planning
  → Use sequential-thinking MCP
  → Create plan incorporating:
    - Task understanding
    - Library recommendations
    - Validation strategy
  → Result: ExecutionPlan with steps

PHASE 5: Execution Loop
  FOR EACH STEP:

    A. Execute via /shannon:wave
       → Convert step to WaveTask
       → invokeSkill('/shannon:wave', wavePlan)
       → EXISTING AgentController executes
       → Agent makes changes using tools
       → Result: Code changes

    B. Validate (3 tiers)
       → ValidationOrchestrator (Shannon CLI module)
       → Tier 1: pytest --collect-only (syntax)
       → Tier 2: pytest tests/ (unit tests)
       → Tier 3: uvicorn + curl (functional)
       → Result: ValidationResult

    C. Decide
       IF validation.all_passed:
         → GitManager.commit(changes, validation)
         → Continue to next step
       ELSE:
         → Analyze failure
         → Research solution (firecrawl MCP)
         → Replan step with research
         → GitManager.rollback()
         → Retry (max 3x)

PHASE 6: Report
  → Generate execution report
  → Save to Serena MCP
  → Save to analytics DB
  → Return to CLI

↓

[CLI: Display Results]
  • Show execution summary
  • Show commits created
  • Show branch name
  • Prompt for next action (push? PR?)

↓

[V3.1 DASHBOARD]
  Throughout execution, shows:
  • Layer 1: Overall progress
  • Layer 2: Step-by-step status
  • Layer 3: Current validation results
  • Layer 4: Full message stream
```

This diagram shows how V3.5 is a COORDINATION LAYER that invokes existing systems.

---

## APPENDIX D: Implementation Priorities

### What to Build First

**Minimum Viable V3.5** (4 days, ~900 lines):
1. PromptEnhancer (150 lines) - System prompt injection
2. LibraryDiscoverer basic (150 lines) - npm search only
3. ValidationOrchestrator basic (200 lines) - Tier 1+2 only
4. GitManager (200 lines) - Basic commits
5. CLI exec command (100 lines) - Entry point
6. Shannon Framework exec skill (200 lines) - Basic orchestration

**Result**: `shannon exec` works for simple tasks with library discovery and git commits.

**Full V3.5** (8 days, ~1,850 lines):
- Add all package registries (PyPI, CocoaPods, Maven, etc.)
- Add Tier 3 functional validation
- Add research integration
- Add iteration/retry logic
- Add analytics tracking
- Add all project-type enhancements

---

## APPENDIX E: Testing Plan

### E.1 Functional Tests (No Unit Tests)

**Test 1: Library Discovery**
```bash
$ shannon exec "add UI components to React Native app" --dry-run

Expected:
✓ Discovers: react-native-paper, NativeBase
✓ Recommends: react-native-paper (higher score)
✓ Plan includes: npm install react-native-paper
✓ Plan uses: <Button>, <TextInput> from library (not custom)
```

**Test 2: Simple Execution**
```bash
$ shannon exec "fix typo in README.md"

Expected:
✓ Creates branch: fix/typo-readme
✓ Makes change
✓ Validates (Tier 1: file exists, Tier 2: skip, Tier 3: skip)
✓ Commits: "fix: Correct typo in README"
✓ Reports: 1 commit, ready for push
```

**Test 3: Multi-Step with Libraries**
```bash
$ shannon exec "add authentication to Next.js app"

Expected:
✓ Discovers: next-auth library
✓ Plan Step 1: npm install next-auth
✓ Plan Step 2: Configure next-auth
✓ Plan Step 3: Add login page
✓ Each step validated (build + tests + functional)
✓ Each step committed
✓ Final: 3 commits, auth works in browser
```

**Test 4: Iteration After Failure**
```bash
$ shannon exec "optimize database query" (with intentional failure point)

Expected:
✓ Iteration 1: Tries B-tree index → fails performance test
✓ Researches: "PostgreSQL ILIKE index optimization"
✓ Iteration 2: Tries GIN trigram index → passes
✓ Commits second iteration
✓ Reports: 1 failure, 1 research, 1 success
```

**Test 5: iOS with Simulator Validation**
```bash
$ shannon exec "fix iOS login screen layout"

Expected:
✓ Detects: iOS/SwiftUI project
✓ Discovers: No libraries needed (use built-in)
✓ Makes changes to constraints
✓ Tier 3: Boots simulator, runs UI tests
✓ Validates: Login screen visible
✓ Commits with simulator validation proof
```

**Test 6: Dashboard Visibility**
```bash
$ shannon exec "build feature" (watch in dashboard)

Expected:
✓ Dashboard Layer 1: Shows task, progress
✓ Dashboard Layer 2: Shows steps (some complete, one active, others pending)
✓ Dashboard Layer 3: Shows current validation running
✓ Dashboard Layer 4: Shows all SDK messages
✓ Can navigate while execution continues
```

**Test 7: Research Integration**
```bash
$ shannon exec "implement OAuth2 PKCE flow"

Expected:
✓ Phase 2: Researches "OAuth2 PKCE best practices"
✓ Finds: RFC 7636, library recommendations
✓ Plan incorporates research findings
✓ Uses oauth library (doesn't build from scratch)
```

**Test 8: Complete E2E**
```bash
$ shannon exec "add dark mode toggle to React app"

Expected:
✓ All 5 phases complete
✓ Library discovered and used
✓ All validations passed
✓ Multiple commits created
✓ Branch ready for PR
✓ Feature actually works
```

**Total: 8 functional tests (no mocks, no unit tests)**

---

## APPENDIX F: Data Models

### F.1 Core Models

**File**: `src/shannon/executor/models.py` (100 lines)

```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime


@dataclass
class LibraryRecommendation:
    """Recommended library option"""
    name: str
    description: str
    repository_url: str
    stars: int
    package_manager: str  # npm, pip, cocoapods, etc.
    install_command: str  # "npm install X", "pip install X"
    why_recommended: str
    score: float  # 0-100


@dataclass
class ExecutionStep:
    """Single step in execution plan"""
    number: int
    description: str
    files_to_modify: List[str]
    expected_changes: str
    validation_criteria: 'ValidationCriteria'
    estimated_duration_seconds: int
    libraries_needed: List[str] = field(default_factory=list)
    fallback_approaches: List[str] = field(default_factory=list)


@dataclass
class ValidationCriteria:
    """Validation requirements for a step"""
    tier1_commands: List[str]  # Build, lint, types
    tier2_commands: List[str]  # Test suite
    tier3_checks: List[str]  # Functional checks
    success_indicators: List[str]  # "Login screen visible", "Query <100ms"


@dataclass
class ExecutionPlan:
    """Complete execution plan"""
    task_description: str
    steps: List[ExecutionStep]
    libraries_discovered: List[LibraryRecommendation]
    research_summary: str
    total_estimated_minutes: int
    branch_name: str

    def to_json(self) -> Dict:
        """Serialize for storage in SessionManager"""
        return {
            'task': self.task_description,
            'steps': [step.__dict__ for step in self.steps],
            'libraries': [lib.__dict__ for lib in self.libraries_discovered],
            'research': self.research_summary,
            'estimated_minutes': self.total_estimated_minutes,
            'branch': self.branch_name
        }


@dataclass
class ExecutionResult:
    """Final execution result"""
    success: bool
    task_description: str
    steps_completed: int
    steps_total: int
    commits_created: List[str]  # Commit hashes
    branch_name: str
    duration_seconds: float
    cost_usd: float
    libraries_used: List[str]
    validations_passed: int
    validations_failed: int
```

---

**END OF REVISED SPECIFICATION**

**Status**: ✅ REALISTIC, BUILDABLE, INTEGRATED
**New Code**: ~1,850 lines (vs 2,350 original)
**Reused**: ~15,000+ lines existing Shannon
**Timeline**: 8 days (vs 11 original)

This specification BUILDS ON existing Shannon Framework infrastructure and is ready for implementation.

