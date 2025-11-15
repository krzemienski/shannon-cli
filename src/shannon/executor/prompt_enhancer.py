"""
Prompt Enhancement Builder - Dynamically builds system prompt additions

Creates task-specific and project-specific prompt enhancements that get
injected via ClaudeAgentOptions.system_prompt.append

Created: November 15, 2025
Part of: Shannon V3.5 Wave 1 (Enhanced Prompts)
"""

from pathlib import Path
from typing import Optional
import json

from .prompts import (
    LIBRARY_DISCOVERY_INSTRUCTIONS,
    FUNCTIONAL_VALIDATION_INSTRUCTIONS,
    GIT_WORKFLOW_INSTRUCTIONS
)
from .task_enhancements import get_enhancement_for_project


class PromptEnhancer:
    """
    Builds enhanced system prompts for autonomous execution
    
    Combines:
    - Core instructions (library discovery, validation, git)
    - Project-specific guidelines (iOS, React, Python, etc.)
    - Task-specific hints (auth, UI, database, etc.)
    
    Usage:
        enhancer = PromptEnhancer()
        enhancements = enhancer.build_enhancements(
            task="add authentication to React app",
            project_root=Path("/path/to/project")
        )
        
        # enhancements is a string that gets injected via:
        # ClaudeAgentOptions(system_prompt={"append": enhancements})
    """
    
    def build_enhancements(
        self,
        task: str,
        project_root: Path
    ) -> str:
        """
        Build complete prompt enhancements for a task
        
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
        """
        Auto-detect project type from files
        
        Args:
            project_root: Project directory
            
        Returns:
            Project type string (ios-swiftui, react-native, python-fastapi, etc.)
        """
        # Check for Node.js/JavaScript projects
        package_json = project_root / 'package.json'
        if package_json.exists():
            try:
                pkg = json.loads(package_json.read_text())
                deps = pkg.get('dependencies', {})
                dev_deps = pkg.get('devDependencies', {})
                all_deps = {**deps, **dev_deps}
                
                # React Native/Expo
                if 'expo' in deps:
                    return 'react-native-expo'
                elif 'react-native' in deps:
                    return 'react-native'
                
                # Next.js
                elif 'next' in deps:
                    return 'next.js'
                
                # React (web)
                elif 'react' in deps:
                    return 'react'
                
                # Vue
                elif 'vue' in all_deps:
                    return 'vue'
                
                # Plain Node.js
                else:
                    return 'nodejs'
            except:
                return 'nodejs'  # Fallback if package.json is malformed
        
        # Check for iOS/macOS projects
        xcodeproj = list(project_root.glob('*.xcodeproj'))
        if xcodeproj:
            # Try to determine if SwiftUI or UIKit
            swift_files = list(project_root.rglob('*.swift'))
            if swift_files:
                # Check first 10 Swift files for SwiftUI import
                for swift_file in swift_files[:10]:
                    try:
                        content = swift_file.read_text()
                        if 'import SwiftUI' in content or 'SwiftUI' in content:
                            return 'ios-swiftui'
                    except:
                        continue
            return 'ios-uikit'  # Default to UIKit if can't determine
        
        # Check for Python projects
        pyproject_toml = project_root / 'pyproject.toml'
        if pyproject_toml.exists():
            try:
                toml_content = pyproject_toml.read_text()
                
                if 'fastapi' in toml_content.lower():
                    return 'python-fastapi'
                elif 'django' in toml_content.lower():
                    return 'python-django'
                else:
                    return 'python'
            except:
                return 'python'
        
        # Check for requirements.txt (older Python projects)
        requirements_txt = project_root / 'requirements.txt'
        if requirements_txt.exists():
            try:
                reqs = requirements_txt.read_text().lower()
                if 'fastapi' in reqs:
                    return 'python-fastapi'
                elif 'django' in reqs:
                    return 'python-django'
                else:
                    return 'python'
            except:
                return 'python'
        
        # Check for Rust
        if (project_root / 'Cargo.toml').exists():
            return 'rust'
        
        # Check for Java/Android
        if (project_root / 'build.gradle').exists() or (project_root / 'pom.xml').exists():
            # Check if Android
            if (project_root / 'app' / 'src' / 'main' / 'AndroidManifest.xml').exists():
                return 'android'
            else:
                return 'java'
        
        # Check for Go
        if (project_root / 'go.mod').exists():
            return 'go'
        
        return 'unknown'
    
    def _generate_task_hints(self, task: str, project_type: str) -> Optional[str]:
        """
        Generate task-specific hints based on keywords in task
        
        Args:
            task: User's task description
            project_type: Detected project type
            
        Returns:
            Task-specific hints or None
        """
        task_lower = task.lower()
        hints = []
        
        # Authentication/Login hints
        if any(word in task_lower for word in ['auth', 'login', 'signup', 'register', 'signin', 'session']):
            if project_type.startswith('react'):
                hints.append("🔐 Authentication: Consider next-auth (Next.js), Auth0 SDK, Clerk, or Supabase Auth")
                hints.append("    DO NOT build custom auth system from scratch")
            elif project_type == 'react-native-expo':
                hints.append("🔐 Authentication: Consider expo-auth-session (OAuth), Firebase Auth, or Supabase Auth")
            elif project_type.startswith('ios'):
                hints.append("🔐 Authentication: Use AuthenticationServices framework (Sign in with Apple built-in)")
                hints.append("    Or Firebase Auth SDK for iOS if multi-platform")
            elif project_type.startswith('python'):
                hints.append("🔐 Authentication: Consider FastAPI-Users, django-allauth, or authlib")
        
        # UI Component hints
        if any(word in task_lower for word in ['ui', 'component', 'screen', 'view', 'button', 'input', 'form']):
            if project_type == 'react-native-expo':
                hints.append("🎨 UI Components: Use react-native-paper (Material Design) or NativeBase")
                hints.append("    DO NOT build custom Button/Input/Card components")
            elif project_type.startswith('react'):
                hints.append("🎨 UI Components: Use shadcn/ui (recommended), MUI, or Chakra UI")
                hints.append("    For forms: use react-hook-form + zod")
            elif project_type == 'vue':
                hints.append("🎨 UI Components: Use Vuetify (Material), PrimeVue, or Quasar")
        
        # Database/Storage hints
        if any(word in task_lower for word in ['database', 'db', 'query', 'migration', 'storage', 'persist']):
            if project_type == 'python-fastapi':
                hints.append("💾 Database: Use SQLAlchemy (ORM) + Alembic (migrations)")
                hints.append("    Or Tortoise ORM if you prefer async-native")
            elif project_type.startswith('nodejs'):
                hints.append("💾 Database: Use Prisma (best DX), Drizzle, or TypeORM")
                hints.append("    Prisma recommended for TypeScript projects")
            elif project_type.startswith('react-native'):
                hints.append("💾 Storage: Use @react-native-async-storage/async-storage (key-value)")
                hints.append("    Or Realm if you need relational database")
        
        # Networking/API hints
        if any(word in task_lower for word in ['api', 'http', 'fetch', 'request', 'endpoint']):
            if project_type.startswith('react'):
                hints.append("🌐 API/Data Fetching: Use TanStack Query (@tanstack/react-query) or SWR")
                hints.append("    DO NOT build custom fetch wrappers")
            elif project_type.startswith('python'):
                hints.append("🌐 HTTP Client: Use httpx (async) or requests (sync)")
            elif project_type.startswith('ios'):
                hints.append("🌐 Networking: Use Alamofire or URLSession (built-in)")
        
        # State Management hints
        if any(word in task_lower for word in ['state', 'redux', 'context', 'global']):
            if project_type.startswith('react'):
                hints.append("📊 State Management: Use Zustand (recommended, lightweight) or Jotai")
                hints.append("    Use Redux Toolkit ONLY if you really need Redux")
                hints.append("    Use React Context for simple global state")
            elif project_type == 'vue':
                hints.append("📊 State Management: Use Pinia (official Vue 3 state library)")
        
        # Navigation/Routing hints
        if any(word in task_lower for word in ['navigation', 'routing', 'router', 'navigate']):
            if project_type == 'react-native-expo':
                hints.append("🧭 Navigation: Use expo-router (file-based) or @react-navigation/native")
            elif project_type == 'react-native':
                hints.append("🧭 Navigation: Use @react-navigation/native (industry standard)")
        
        # Charts/Visualization hints
        if any(word in task_lower for word in ['chart', 'graph', 'visualization', 'plot']):
            if project_type.startswith('react'):
                hints.append("📈 Charts: Use recharts (recommended), visx, or chart.js")
            elif project_type == 'react-native':
                hints.append("📈 Charts: Use react-native-chart-kit or victory-native")
        
        # Background Jobs/Tasks hints
        if any(word in task_lower for word in ['background', 'job', 'queue', 'task', 'worker', 'cron']):
            if project_type == 'python-fastapi':
                hints.append("⚙️ Background Jobs: Use arq (Redis-based, async-native, good for FastAPI)")
                hints.append("    Or Celery if you need advanced features (heavier)")
            elif project_type.startswith('nodejs'):
                hints.append("⚙️ Background Jobs: Use BullMQ (Redis), Agenda (MongoDB), or node-cron")
        
        # Real-time/WebSocket hints
        if any(word in task_lower for word in ['realtime', 'websocket', 'live', 'streaming', 'socket']):
            if project_type.startswith('nodejs'):
                hints.append("🔌 Real-time: Use socket.io (recommended) or ws (lower-level)")
            elif project_type == 'python-fastapi':
                hints.append("🔌 WebSockets: Use FastAPI's built-in WebSocket support")
            elif project_type == 'python-django':
                hints.append("🔌 Real-time: Use Django Channels (WebSocket support for Django)")
        
        if hints:
            header = f"═══════════════════════════════════════════════════════════════════════════════\n"
            header += f" TASK-SPECIFIC HINTS for '{task}'\n"
            header += f"═══════════════════════════════════════════════════════════════════════════════\n"
            
            hints_text = "\n".join(hints)
            
            return f"{header}\n{hints_text}\n"
        
        return None

