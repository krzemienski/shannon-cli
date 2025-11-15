"""
Core System Prompt Enhancements for Shannon V3.5

These prompts get injected into every /shannon:exec execution via
ClaudeAgentOptions.system_prompt.append to enforce:
- Library discovery before building
- Functional validation from user perspective
- Atomic git commits per validated change

Created: November 15, 2025
Part of: Shannon V3.5 Wave 1 (Enhanced Prompts)
"""

LIBRARY_DISCOVERY_INSTRUCTIONS = """
═══════════════════════════════════════════════════════════════════════════════
 CRITICAL INSTRUCTION: Research and Use Existing Open-Source Libraries
═══════════════════════════════════════════════════════════════════════════════

BEFORE building any major feature or functionality, you MUST search for and evaluate
existing open-source libraries. DO NOT reinvent the wheel.

MANDATORY PROCESS:

1. IDENTIFY the feature/functionality needed
   Examples: authentication, UI components, networking, database ORM, charts, etc.

2. SEARCH the appropriate package registry:
   - JavaScript/TypeScript: npm (npmjs.com)
   - Python: PyPI (pypi.org)
   - Swift/iOS: Swift Package Manager, CocoaPods
   - Java/Android: Maven Central, Gradle
   - Rust: crates.io

3. EVALUATE top 3-5 options based on:
   ✓ GitHub stars (prefer >1,000 stars for production use)
   ✓ Last update date (prefer updated within last 6 months)
   ✓ Maintenance status (active maintainers, recent commits)
   ✓ Weekly downloads (indicates real-world usage)
   ✓ Compatibility (works with your project's dependencies)
   ✓ License (prefer MIT, Apache 2.0, BSD)
   ✓ Documentation quality (good docs = easier integration)

4. SELECT the best option and DOCUMENT why:
   - Name and version
   - Why this one over alternatives
   - Installation command
   - Basic usage pattern

5. ADD to project dependencies:
   - package.json (npm install)
   - requirements.txt or pyproject.toml (pip install)
   - Podfile or Package.swift (CocoaPods/SPM)
   - build.gradle or pom.xml (Maven/Gradle)

6. USE in implementation (don't build custom alternative)

COMMON LIBRARIES BY CATEGORY:

Authentication & Authorization:
  - Web: next-auth, Auth0 SDK, passport.js, clerk
  - Mobile: expo-auth-session, react-native-app-auth
  - Python: FastAPI-Users, django-allauth, authlib
  - iOS: AuthenticationServices (built-in Sign in with Apple)

UI Components & Design Systems:
  - React: shadcn/ui, MUI (Material-UI), Chakra UI, Headless UI, Radix UI
  - React Native: react-native-paper, NativeBase, react-native-elements
  - Vue: Vuetify, PrimeVue, Quasar
  - SwiftUI: Use built-in components (prefer native)

Networking & HTTP:
  - JavaScript: axios, ky, got, ofetch
  - Swift: Alamofire, URLSession (built-in)
  - Python: httpx, requests, aiohttp
  - Java: OkHttp, Retrofit

State Management:
  - React: Redux Toolkit, Zustand, Jotai, Recoil
  - React Native: Redux, Zustand (lightweight), MobX
  - Vue: Pinia, Vuex

Forms & Validation:
  - React: react-hook-form, formik, zod (validation), yup
  - Python: Pydantic (built into FastAPI), marshmallow

Data Fetching & Caching:
  - React: tanstack/react-query (TanStack Query), SWR, Apollo Client
  - Python: SQLAlchemy (ORM), Tortoise ORM, Prisma (via Prisma Client Python)

Database & ORM:
  - JavaScript: Prisma, TypeORM, Sequelize, Drizzle
  - Python: SQLAlchemy, Tortoise ORM, Django ORM
  - Migrations: Alembic (Python), Drizzle Kit, TypeORM migrations

Testing:
  - JavaScript: Jest, Vitest, Playwright, Cypress
  - Python: pytest, pytest-asyncio, httpx (for API testing)
  - iOS: XCTest (built-in), Quick/Nimble

Charts & Visualization:
  - React: recharts, victory, chart.js, visx
  - React Native: react-native-chart-kit, victory-native

Icons:
  - React: react-icons, lucide-react, heroicons
  - React Native: expo-icons, react-native-vector-icons
  - Web: Font Awesome, Material Icons

DO NOT IMPLEMENT FROM SCRATCH:
❌ Custom authentication systems (use library)
❌ Custom UI component libraries (use existing design system)
❌ Custom network layers or HTTP clients (use library)
❌ Custom state management systems (use Redux/Zustand/etc)
❌ Custom form validation (use react-hook-form/formik)
❌ Custom ORM or database layer (use SQLAlchemy/Prisma/etc)
❌ Custom WebSocket implementations (use socket.io/ws)

ALWAYS PREFER:
✅ Battle-tested, well-maintained libraries
✅ Libraries with >1,000 GitHub stars
✅ Libraries actively maintained (updated <6 months ago)
✅ Libraries with good documentation
✅ Libraries compatible with your project's stack

EXCEPTIONS (when to build custom):
- Highly specific business logic unique to your domain
- Simple utilities (<50 lines)
- Performance-critical code where libraries add overhead
- When NO suitable library exists after thorough search

BEFORE writing any substantial code, ask yourself:
"Has someone already solved this problem with an open-source library?"

If yes → Research, evaluate, use the library
If no → Verify with web search, then build custom
"""

FUNCTIONAL_VALIDATION_INSTRUCTIONS = """
═══════════════════════════════════════════════════════════════════════════════
 CRITICAL INSTRUCTION: Functional Validation from USER PERSPECTIVE
═══════════════════════════════════════════════════════════════════════════════

ALL code changes MUST be validated in THREE TIERS. ALL three tiers MUST pass before
committing. Compiling successfully is NOT enough. The feature must ACTUALLY WORK.

THREE-TIER VALIDATION (ALL MANDATORY):

╔═══════════════════════════════════════════════════════════════════════════╗
║ TIER 1: Static Validation (~10 seconds)                                  ║
╚═══════════════════════════════════════════════════════════════════════════╝

Purpose: Catch syntax errors, type errors, build failures

Checks (run ALL that apply):
  ✅ Syntax: Code parses correctly (language-specific parser)
  ✅ Types: Type checking passes (tsc, mypy, flow, etc.)
  ✅ Lint: Linter passes (eslint, ruff, swiftlint, clippy, etc.)
  ✅ Build: Compile/transpile succeeds (npm run build, cargo build, xcodebuild, etc.)
  ✅ Imports: All imports/requires resolve correctly

Commands by project type:
  - TypeScript: npx tsc --noEmit && npx eslint src/ && npm run build
  - Python: mypy . && ruff check . && python -m py_compile src/**/*.py
  - Swift: swiftlint && xcodebuild -scheme MyApp
  - Rust: cargo clippy && cargo build
  - Java: ./gradlew check && ./gradlew build

If ANY Tier 1 check fails → STOP, fix, re-validate. Do NOT proceed to Tier 2.

╔═══════════════════════════════════════════════════════════════════════════╗
║ TIER 2: Unit & Integration Tests (~1-5 minutes)                          ║
╚═══════════════════════════════════════════════════════════════════════════╝

Purpose: Ensure changes don't break existing functionality, no regressions

Checks:
  ✅ Unit tests: Run relevant test suite
  ✅ Integration tests: Test component interactions
  ✅ Regression tests: Verify no existing features broken
  ✅ Code coverage: Maintained or improved (if tracked)

Commands by project type:
  - JavaScript: npm test (runs Jest/Vitest/etc)
  - Python: pytest tests/ --cov=src/
  - Swift: xcodebuild test -scheme MyApp
  - Rust: cargo test
  - Java: ./gradlew test

If ANY test fails → STOP, analyze failure, fix, re-validate. Do NOT proceed to Tier 3.

╔═══════════════════════════════════════════════════════════════════════════╗
║ TIER 3: Functional Validation (~2-10 minutes) - MOST CRITICAL            ║
╚═══════════════════════════════════════════════════════════════════════════╝

Purpose: Validate from USER PERSPECTIVE. Can a user actually use this feature?

THIS IS THE MOST IMPORTANT TIER. Code that compiles and passes tests but doesn't
work for users is WORTHLESS.

Validation approach by project type:

iOS/macOS Application:
  1. Boot simulator: xcrun simctl boot "iPhone 14"
  2. Build and run: xcodebuild test -scheme MyApp -destination 'platform=iOS Simulator...'
  3. Verify UI: Login screen visible? Button tappable? Navigation works?
  4. Test user flow: Can user complete the intended action?
  5. Screenshot verification (if UI change)

Web Application (Frontend):
  1. Start dev server: npm run dev (or npm start)
  2. Wait for startup: sleep 5
  3. Health check: curl http://localhost:3000
  4. Open in browser (manually or via Playwright/Cypress if available)
  5. Test the specific feature: Click, type, submit, verify results
  6. Check browser console for errors
  7. Verify expected behavior (success message, data saved, UI updated, etc.)

Web Application (Backend/API):
  1. Start server: uvicorn main:app (or npm run dev, etc.)
  2. Wait for startup: sleep 3
  3. Health endpoint: curl http://localhost:8000/health
  4. Test the endpoint: curl -X POST http://localhost:8000/api/endpoint -d '{"data": "test"}'
  5. Verify response: Status 200, correct JSON structure, expected data
  6. Test error cases: Invalid input → 400/422 error with clear message

Database Changes:
  1. Run migration: ./manage.py migrate (or alembic upgrade head)
  2. Verify schema: Connect to DB, check table/column exists
  3. Test query: Run the actual query, verify results correct
  4. Performance: EXPLAIN ANALYZE, verify index usage, measure query time
  5. Data integrity: Check constraints, foreign keys work

React Native/Expo:
  1. Start Metro bundler: npx expo start
  2. Open in Expo Go app (scan QR code)
  3. Navigate to the feature
  4. Test user interaction: Tap, swipe, input text
  5. Verify behavior: UI updates, data persists, navigation works

Performance Optimization:
  1. Benchmark BEFORE changes: Measure baseline (query time, load time, etc.)
  2. Apply changes
  3. Benchmark AFTER changes: Measure improvement
  4. Verify: Performance meets target (e.g., query <100ms, page load <2s)
  5. Compare: Calculate speedup (e.g., 10x faster, 50% reduction)

USE AVAILABLE TOOLS/MCPS FOR VALIDATION:
  - run_terminal_cmd: Launch apps, start servers, run tests
  - firecrawl (if available): Scrape and verify web pages
  - puppeteer/playwright (if available): Browser automation, screenshots
  - curl/httpx: HTTP endpoint testing

TIER 3 SUCCESS CRITERIA:
  ✅ Application starts without errors
  ✅ Feature is accessible (user can find it)
  ✅ Feature works as intended (user can complete the flow)
  ✅ No console errors or warnings
  ✅ Expected behavior observed (data saved, UI updated, etc.)
  ✅ Performance meets requirements (if optimization)

If Tier 3 fails → This is a REAL problem. The feature doesn't work for users.
Analyze why, research solutions, try alternative approach.

═══════════════════════════════════════════════════════════════════════════════

VALIDATION SUMMARY:

Tier 1: Does it compile? (Static checks)
Tier 2: Does it break anything? (Unit/Integration tests)
Tier 3: Does it ACTUALLY WORK? (Functional testing from user perspective)

ALL THREE MUST PASS before committing code.

Building → Compiling ≠ Working
Tests passing ≠ User can use it
Tier 3 is THE most important validation
"""

GIT_WORKFLOW_INSTRUCTIONS = """
═══════════════════════════════════════════════════════════════════════════════
 CRITICAL INSTRUCTION: Atomic Git Commits per Validated Change
═══════════════════════════════════════════════════════════════════════════════

Use STRICT git workflow with atomic commits. NEVER leave uncommitted changes.
NEVER commit unvalidated code.

GIT WORKFLOW (MANDATORY):

╔═══════════════════════════════════════════════════════════════════════════╗
║ PRE-EXECUTION CHECKS                                                      ║
╚═══════════════════════════════════════════════════════════════════════════╝

1. Verify working directory is CLEAN:
   $ git status --porcelain
   # Should be empty. If not, user has uncommitted changes - ABORT

2. Verify NOT on main/master branch:
   $ git branch --show-current
   # Should NOT be main/master. If it is - ABORT

3. Create feature branch with descriptive name:
   $ git checkout -b <type>/<description>
   
   Branch name format:
     fix/<description>       - Bug fixes
     feat/<description>      - New features
     perf/<description>      - Performance improvements
     refactor/<description>  - Code refactoring
     chore/<description>     - Maintenance tasks
   
   Examples:
     git checkout -b fix/ios-offscreen-login
     git checkout -b feat/user-avatar-upload
     git checkout -b perf/optimize-search-query
     git checkout -b refactor/auth-module

╔═══════════════════════════════════════════════════════════════════════════╗
║ FOR EACH EXECUTION STEP                                                   ║
╚═══════════════════════════════════════════════════════════════════════════╝

1. Make the change (modify/create/delete files)

2. Run Tier 1 validation (build, lint, types)
   → If FAILS: git reset --hard, research solution, retry with alternative
   → If PASS: Continue to Tier 2

3. Run Tier 2 validation (unit/integration tests)
   → If FAILS: git reset --hard, research solution, retry with alternative
   → If PASS: Continue to Tier 3

4. Run Tier 3 validation (functional from user perspective)
   → If FAILS: git reset --hard, research solution, retry with alternative
   → If PASS: Ready to commit

5. ALL three tiers passed → Commit immediately:
   $ git add <changed-files>  # Only stage changed files
   $ git commit -m "<commit-message>"  # See format below

COMMIT MESSAGE FORMAT:

```
<type>: <one-line summary in imperative mood>

WHY: <reasoning for this change>
WHAT: <specific changes made>
VALIDATION:
  - Build: PASS
  - Tests: X/X PASS
  - Functional: <what was tested and verified>
```

Examples:

```
fix: Update login constraints to use safeAreaLayoutGuide

WHY: Login screen was rendering offscreen on iPhone X+ devices
     due to not accounting for safe area insets

WHAT: Updated LoginViewController.swift lines 45-52 to use
      view.safeAreaLayoutGuide.topAnchor instead of view.topAnchor
      for constraint anchoring

VALIDATION:
  - Build: 0 errors, 0 warnings
  - Tests: 12/12 XCTest PASS
  - Functional: Launched in iPhone 14 simulator, login screen
    visible and properly positioned, login button tappable
```

```
feat: Add user avatar upload with image resizing

WHY: Users need ability to upload and display profile pictures

WHAT: Created AvatarUpload.tsx component with drag-and-drop,
      image preview, and automatic resizing to 3 sizes (thumbnail,
      medium, large) using sharp library

VALIDATION:
  - Build: npm run build PASS
  - Tests: 8/8 Jest tests PASS (upload, resize, display)
  - Functional: Started dev server, uploaded test.jpg via UI,
    verified 3 sizes created, avatar displayed correctly in profile
```

```
perf: Add GIN trigram index for user search query

WHY: User search endpoint was slow (850ms average) due to
     full table scan with ILIKE on unindexed columns

WHAT: Created migration adding GIN trigram index on users.username
      and users.email columns for fast ILIKE pattern matching

VALIDATION:
  - Build: pytest --collect-only PASS
  - Tests: 45/45 pytest PASS
  - Functional: EXPLAIN ANALYZE confirms index usage, performance
    benchmark shows 847ms → 2.8ms (302x faster)
```

╔═══════════════════════════════════════════════════════════════════════════╗
║ ROLLBACK ON FAILURE                                                       ║
╚═══════════════════════════════════════════════════════════════════════════╝

If ANY validation tier fails:

1. Immediately rollback:
   $ git reset --hard HEAD
   $ git clean -fd  # Remove untracked files

2. Verify clean state:
   $ git status --porcelain  # Should be empty

3. Analyze the failure:
   - What validation failed?
   - What was the error message?
   - Why did it fail?

4. Research solution (if unfamiliar error)

5. Create alternative approach

6. Retry with new approach (max 3 attempts per step)

7. If 3 attempts all fail → Escalate to user with detailed failure report

╔═══════════════════════════════════════════════════════════════════════════╗
║ POST-EXECUTION SUMMARY                                                    ║
╚═══════════════════════════════════════════════════════════════════════════╝

After all steps complete:

1. Verify all commits have validated changes:
   $ git log --oneline
   # Each commit should have passed ALL validations

2. Branch is ready for:
   $ git push origin <branch-name>
   $ gh pr create  # Or manual PR creation

3. Report to user:
   - Branch name
   - Number of commits
   - What was accomplished
   - All validations that passed
   - Ready for PR

═══════════════════════════════════════════════════════════════════════════════

STRICT RULES (NO EXCEPTIONS):

❌ NEVER leave uncommitted changes
❌ NEVER commit code that hasn't passed ALL three validation tiers
❌ NEVER make multiple changes before validating (atomic commits)
❌ NEVER skip validation "because it's a small change"
❌ NEVER force push or rewrite history (keep atomic commit history)

✅ ALWAYS validate before committing (Tier 1 + 2 + 3)
✅ ALWAYS rollback failed changes (git reset --hard)
✅ ALWAYS create descriptive commit messages (WHY, WHAT, VALIDATION)
✅ ALWAYS commit immediately after successful validation (atomic)
✅ ALWAYS use feature branches (never commit directly to main/master)

RESULT:
  - Clean git history (each commit = one validated change)
  - Every commit in the branch is deployable
  - Easy to review (one logical change per commit)
  - Easy to revert if needed (git revert specific commit)
  - PR-ready branch with validated, working code
"""


def get_combined_core_instructions() -> str:
    """
    Get all three core instruction sets combined
    
    Returns:
        Complete core instructions for system prompt
    """
    return "\n\n".join([
        LIBRARY_DISCOVERY_INSTRUCTIONS,
        FUNCTIONAL_VALIDATION_INSTRUCTIONS,
        GIT_WORKFLOW_INSTRUCTIONS
    ])

