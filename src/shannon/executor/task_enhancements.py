"""
Project-Specific System Prompt Enhancements

Provides best practices and library recommendations specific to:
- iOS/Swift (SwiftUI and UIKit)
- React Native/Expo
- React/Next.js (Web)
- Python/FastAPI
- And other common project types

These get injected based on auto-detected project type.

Created: November 15, 2025
Part of: Shannon V3.5 Wave 1 (Enhanced Prompts)
"""

IOS_SWIFT_ENHANCEMENTS = """
═══════════════════════════════════════════════════════════════════════════════
 iOS/Swift Development Best Practices
═══════════════════════════════════════════════════════════════════════════════

Framework Preferences:
  - Use SwiftUI for NEW UI code (modern, declarative, Apple's direction)
  - Use UIKit only for legacy code or specific UIKit-only features
  - Use Combine for reactive programming (built-in, integrates with SwiftUI)
  - Use Swift Concurrency (async/await) for asynchronous operations

Layout & UI:
  - ALWAYS handle safe area constraints for modern iPhones (iPhone X+)
  - Use safeAreaLayoutGuide.topAnchor, not view.topAnchor
  - Use GeometryReader in SwiftUI for dynamic sizing
  - Prefer Stack views (VStack, HStack) over manual positioning

Dependency Management:
  - Prefer Swift Package Manager (SPM) over CocoaPods (Apple's official)
  - Add packages via Xcode: File → Add Packages
  - Or Package.swift for library projects

Common Swift Libraries (research first, prefer built-in):
  Networking:
    - Alamofire (if you need advanced features)
    - URLSession (built-in, prefer for simple cases)
  
  Image Loading/Caching:
    - Kingfisher (async image loading, caching)
    - SDWebImage (alternative, both good)
  
  Auto Layout (if using UIKit):
    - SnapKit (DSL for constraints, cleaner than NSLayoutConstraint)
    - TinyConstraints (alternative, lighter)
  
  Networking/GraphQL:
    - Apollo iOS (GraphQL client)
  
  Database/Persistence:
    - Core Data (built-in, complex but powerful)
    - Realm (simpler, good for mobile)
    - SQLite.swift (lightweight SQL wrapper)
  
  Authentication:
    - AuthenticationServices (built-in Sign in with Apple)
    - Firebase Auth (if using Firebase)
  
  Security/Keychain:
    - KeychainAccess (simplifies Keychain API)

DO NOT build from scratch:
  ❌ Custom HTTP networking layer (use URLSession or Alamofire)
  ❌ Custom image caching (use Kingfisher)
  ❌ Custom constraint DSL (use SnapKit if needed)

Validation for iOS:
  - Build: xcodebuild clean build
  - Lint: swiftlint (if configured)
  - Tests: xcodebuild test -scheme <YourApp>
  - Functional: Launch in simulator
    * xcrun simctl boot "iPhone 14"
    * xcodebuild test -scheme <YourApp> -destination 'platform=iOS Simulator,name=iPhone 14'
  - Verify UI elements visible and tappable
  - Test actual user flows (login, navigation, data entry, etc.)

iOS Deployment Targets:
  - Check minimum iOS version in project
  - Use features appropriate for deployment target
  - Test on multiple simulator devices (iPhone SE, iPhone 14, iPad)
"""

REACT_NATIVE_ENHANCEMENTS = """
═══════════════════════════════════════════════════════════════════════════════
 React Native / Expo Development Best Practices
═══════════════════════════════════════════════════════════════════════════════

Expo Preference:
  - Use Expo SDK when possible (simplifies native features)
  - Expo Go for quick testing (no need to build native)
  - EAS Build for production builds
  - Prefer Expo modules over bare React Native modules

Code Style:
  - TypeScript in STRICT mode (tsconfig.json: strict: true)
  - Functional components with hooks (no class components)
  - Proper TypeScript types for props and state

Navigation:
  - Use @react-navigation/native (industry standard)
  - Or expo-router (newer, file-based routing for Expo)

Common React Native Libraries (research and use, DON'T build custom):

  UI Component Libraries (ALWAYS use one, don't build custom):
    - react-native-paper (Material Design, 10k+ stars, excellent)
    - NativeBase (19k stars, cross-platform components)
    - react-native-elements (25k stars, customizable)
    - Prefer Paper for Material Design, NativeBase for general use
  
  State Management:
    - Zustand (lightweight, simple, recommended)
    - Jotai (atomic state, good for complex apps)
    - Redux Toolkit (heavyweight, use if needed)
    - DON'T use plain Redux (use Redux Toolkit if going Redux route)
  
  Forms:
    - react-hook-form (performant, good DX)
    - formik (alternative, more features)
  
  Navigation:
    - @react-navigation/native (stack, tab, drawer navigation)
    - expo-router (file-based, Expo only)
  
  Icons:
    - @expo/vector-icons (built into Expo)
    - react-native-vector-icons (if not using Expo)
  
  Storage:
    - @react-native-async-storage/async-storage (key-value)
    - expo-secure-store (secure storage)
    - realm (for complex data models)
  
  Animation:
    - react-native-reanimated (high performance)
    - Animated API (built-in, simpler)
  
  Gestures:
    - react-native-gesture-handler (smooth gestures)

DO NOT build from scratch:
  ❌ Custom Button/Input/Card/Text components (use UI kit library)
  ❌ Custom navigation system (use React Navigation or expo-router)
  ❌ Custom form handling (use react-hook-form)
  ❌ Custom state management (use Zustand/Redux Toolkit)

Validation for React Native/Expo:
  - Type check: npx tsc --noEmit
  - Lint: npx eslint .
  - Build: expo build (or npx react-native bundle)
  - Tests: npm test (Jest)
  - Functional: Start Metro, open in Expo Go
    * npx expo start
    * Scan QR code with Expo Go app
    * Navigate to feature
    * Test user interaction (tap, swipe, input)
    * Verify behavior (UI updates, data persists, navigation works)

Platform Considerations:
  - Test on both iOS and Android simulators
  - Handle platform-specific code with Platform.select()
  - Use Expo's platform-specific files (.ios.tsx, .android.tsx) if needed
"""

REACT_WEB_ENHANCEMENTS = """
═══════════════════════════════════════════════════════════════════════════════
 React / Next.js Web Development Best Practices
═══════════════════════════════════════════════════════════════════════════════

Framework Specifics:
  Next.js 14+:
    - Use App Router (app/) not Pages Router (pages/)
    - Prefer Server Components (default in app/)
    - Use Client Components only when needed ('use client')
    - Leverage Server Actions for mutations

Code Style:
  - TypeScript in STRICT mode
  - Functional components with hooks
  - Proper error boundaries
  - Suspense for async components

Common React/Next.js Libraries (use these, don't build custom):

  UI Components/Design Systems:
    - shadcn/ui (recommended: Radix + Tailwind, copy-paste components)
    - MUI (Material-UI, comprehensive, 87k stars)
    - Chakra UI (accessible, themeable)
    - Headless UI (unstyled, accessible primitives)
    - Radix UI (primitives, use with Tailwind)
  
  Styling:
    - Tailwind CSS (utility-first, recommended)
    - CSS Modules (built into Next.js)
    - styled-components (CSS-in-JS if needed)
  
  Forms:
    - react-hook-form (performant, great DX, recommended)
    - formik (alternative, more opinionated)
    - zod (validation schemas, works with react-hook-form)
  
  State Management:
    - Zustand (lightweight, simple, recommended for most cases)
    - Jotai (atomic, good for complex state)
    - Redux Toolkit (only if really needed)
    - React Context (built-in, good for simple global state)
  
  Data Fetching:
    - TanStack Query (@tanstack/react-query, recommended)
    - SWR (alternative from Vercel)
    - tRPC (if building type-safe API)
  
  Authentication:
    - NextAuth.js (next-auth, best for Next.js)
    - Clerk (modern, good DX, paid service)
    - Auth0 SDK (enterprise)
    - Supabase Auth (if using Supabase)
  
  Database/ORM (if full-stack):
    - Prisma (best DX, recommended)
    - Drizzle (type-safe, lighter than Prisma)
    - TypeORM (alternative)
  
  Icons:
    - lucide-react (clean, modern)
    - react-icons (many icon sets)
    - heroicons (Tailwind team)
  
  Charts:
    - recharts (composable, good DX)
    - visx (Airbnb, low-level)
    - chart.js with react-chartjs-2

DO NOT build from scratch:
  ❌ Custom authentication system (use NextAuth/Clerk/Auth0)
  ❌ Custom UI component library (use shadcn/MUI/Chakra)
  ❌ Custom form handling (use react-hook-form)
  ❌ Custom data fetching (use TanStack Query)

Validation for React/Next.js:
  - Type check: npx tsc --noEmit
  - Lint: npx eslint .
  - Build: npm run build (or next build)
  - Tests: npm test (Jest/Vitest)
  - Functional: Start dev server and test in browser
    * npm run dev
    * Open http://localhost:3000
    * Navigate to feature
    * Test user interaction
    * Verify no console errors
    * Check Network tab for API calls
    * Verify expected behavior

SSR/SSG Considerations (Next.js):
  - Check for hydration errors (server HTML ≠ client HTML)
  - Use useEffect for client-only code (timestamps, localStorage, etc.)
  - Test both server-rendered and client-rendered scenarios
"""

PYTHON_FASTAPI_ENHANCEMENTS = """
═══════════════════════════════════════════════════════════════════════════════
 Python / FastAPI Development Best Practices
═══════════════════════════════════════════════════════════════════════════════

Code Style:
  - Type hints EVERYWHERE (PEP 484)
  - Use mypy for type checking
  - Async/await for I/O operations
  - Pydantic models for request/response validation (built into FastAPI)

Common Python/FastAPI Libraries (use these, don't reinvent):

  Web Framework:
    - FastAPI (modern, async, automatic docs)
    - Django REST Framework (if Django ecosystem)
  
  Database/ORM:
    - SQLAlchemy (most popular, feature-rich)
    - Tortoise ORM (async-native, good for FastAPI)
    - Django ORM (if using Django)
  
  Migrations:
    - Alembic (for SQLAlchemy, standard)
    - Django migrations (built into Django)
  
  Authentication/Security:
    - FastAPI-Users (complete auth solution for FastAPI)
    - python-jose (JWT tokens)
    - passlib (password hashing)
  
  Validation:
    - Pydantic (built into FastAPI, use it)
    - marshmallow (alternative, Django-friendly)
  
  HTTP Client:
    - httpx (async, modern, recommended)
    - requests (sync, widely used)
    - aiohttp (async alternative)
  
  Background Jobs:
    - arq (Redis-based, async-native, good for FastAPI)
    - Celery (battle-tested, heavyweight)
    - Dramatiq (simpler than Celery)
  
  Testing:
    - pytest (standard)
    - pytest-asyncio (for async tests)
    - httpx (for testing FastAPI endpoints)
  
  Caching:
    - redis (via redis-py or aioredis)
    - aiocache (async caching)

DO NOT build from scratch:
  ❌ Custom authentication/JWT handling (use FastAPI-Users)
  ❌ Custom ORM (use SQLAlchemy/Tortoise)
  ❌ Custom validation (use Pydantic)
  ❌ Custom HTTP client (use httpx)

Validation for Python/FastAPI:
  - Type check: mypy src/
  - Lint: ruff check .
  - Format check: ruff format --check .
  - Tests: pytest tests/ --cov=src/
  - Functional: Start server and hit endpoints
    * uvicorn main:app --reload &
    * sleep 3
    * curl http://localhost:8000/health
    * curl -X POST http://localhost:8000/api/endpoint -H "Content-Type: application/json" -d '{"test": "data"}'
    * Verify response status and JSON structure

Database Migrations:
  - Always create migrations for schema changes
  - Test migrations: alembic upgrade head
  - Test rollback: alembic downgrade -1
  - Verify schema with SQL client
"""

PYTHON_DJANGO_ENHANCEMENTS = """
═══════════════════════════════════════════════════════════════════════════════
 Python / Django Development Best Practices
═══════════════════════════════════════════════════════════════════════════════

Django Conventions:
  - Follow Django project structure (apps, models, views, templates)
  - Use Django ORM (built-in, don't use raw SQL unless necessary)
  - Use Django forms for validation
  - Use Django admin for quick CRUD interfaces

Common Django Libraries:
  - django-allauth (authentication with social auth)
  - djangorestframework (DRF for APIs)
  - django-filter (filtering for DRF)
  - celery (background tasks)
  - channels (WebSockets)

Validation for Django:
  - Lint: ruff check .
  - Tests: python manage.py test
  - Migrations: python manage.py makemigrations && python manage.py migrate
  - Functional: python manage.py runserver
    * Open http://localhost:8000
    * Test feature in browser
    * Check Django admin if applicable
"""

NODEJS_BACKEND_ENHANCEMENTS = """
═══════════════════════════════════════════════════════════════════════════════
 Node.js Backend Development Best Practices
═══════════════════════════════════════════════════════════════════════════════

Framework Choice:
  - Express (minimalist, flexible)
  - Fastify (faster, modern)
  - NestJS (opinionated, TypeScript-first, enterprise)

Common Node.js Backend Libraries:
  - zod (validation)
  - Prisma (database ORM, recommended)
  - passport (authentication)
  - jsonwebtoken (JWT tokens)

Validation:
  - Type check: npx tsc --noEmit
  - Tests: npm test
  - Functional: npm start, curl endpoints
"""

VUE_ENHANCEMENTS = """
═══════════════════════════════════════════════════════════════════════════════
 Vue.js Development Best Practices
═══════════════════════════════════════════════════════════════════════════════

Vue Version:
  - Use Vue 3 Composition API (modern, better TypeScript support)
  - Use <script setup> syntax

Common Vue Libraries:
  - Pinia (state management, official)
  - Vuetify (Material Design components)
  - PrimeVue (comprehensive UI library)
  - VueUse (composition utilities)

Validation:
  - Type check: vue-tsc --noEmit
  - Build: npm run build
  - Tests: npm test (Vitest recommended)
  - Functional: npm run dev, test in browser
"""


# Mapping of project types to enhancements
PROJECT_TYPE_ENHANCEMENTS = {
    'ios-swiftui': IOS_SWIFT_ENHANCEMENTS,
    'ios-uikit': IOS_SWIFT_ENHANCEMENTS,
    'react-native': REACT_NATIVE_ENHANCEMENTS,
    'react-native-expo': REACT_NATIVE_ENHANCEMENTS,
    'react': REACT_WEB_ENHANCEMENTS,
    'next.js': REACT_WEB_ENHANCEMENTS,
    'python-fastapi': PYTHON_FASTAPI_ENHANCEMENTS,
    'python-django': PYTHON_DJANGO_ENHANCEMENTS,
    'nodejs': NODEJS_BACKEND_ENHANCEMENTS,
    'vue': VUE_ENHANCEMENTS
}


def get_enhancement_for_project(project_type: str) -> str:
    """
    Get project-specific enhancement prompt
    
    Args:
        project_type: Detected project type
        
    Returns:
        Enhancement prompt for this project type, or empty string if unknown
    """
    return PROJECT_TYPE_ENHANCEMENTS.get(project_type, "")


def get_all_project_types() -> list:
    """Get list of all supported project types"""
    return list(PROJECT_TYPE_ENHANCEMENTS.keys())

