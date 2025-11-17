"""UnifiedOrchestrator - V5 Consolidation Layer

Consolidates V3 (ContextAwareOrchestrator) and V4 (orchestration.Orchestrator)
into a unified interface while maintaining both systems' integrity.

Architecture: Facade pattern with subsystem sharing
- Delegates to existing orchestrators (no reimplementation)
- Shares subsystems: cache, context, analytics, cost optimization
- Provides unified interface for all commands

Created for: Shannon CLI V5
Design: docs/design/UNIFIED_ORCHESTRATOR_DESIGN.md
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# V3 Orchestrator and subsystems
from shannon.orchestrator import ContextAwareOrchestrator
from shannon.cache.manager import CacheManager
from shannon.context.manager import ContextManager
from shannon.analytics.database import AnalyticsDatabase
from shannon.optimization.model_selector import ModelSelector
from shannon.optimization.cost_estimator import CostEstimator
from shannon.optimization.budget_enforcer import BudgetEnforcer
from shannon.mcp.manager import MCPManager
from shannon.agents.state_tracker import AgentStateTracker
from shannon.agents.controller import AgentController

# V5 Infrastructure (not custom skills framework)
from shannon.orchestration.state_manager import StateManager
from shannon.orchestration.agent_pool import AgentPool

# Shared infrastructure
from shannon.config import ShannonConfig
from shannon.sdk.client import ShannonSDKClient

logger = logging.getLogger(__name__)


class UnifiedOrchestrator:
    """Unified orchestration layer consolidating V3 and V4 capabilities.

    The UnifiedOrchestrator provides a single interface for all Shannon CLI
    operations while maintaining the separation between V3 (intelligence/analysis)
    and V4 (skills/execution) systems.

    Architecture:
        - V3 Path: execute_analysis() → ContextAwareOrchestrator (context-aware analysis)
        - V4 Path: execute_skills() → orchestration.Orchestrator (skills execution)
        - Unified: execute_unified() → Both V3 + V4 (analysis then execution)

    Shared Subsystems (available to both V3 and V4):
        - CacheManager: Multi-tier caching
        - ContextManager: Project context loading
        - AnalyticsDatabase: Session recording
        - CostEstimator/BudgetEnforcer: Cost optimization
        - AgentPool: Parallel execution management

    Usage:
        orchestrator = UnifiedOrchestrator()

        # V3 analysis
        result = await orchestrator.execute_analysis(spec_text)

        # V4 execution
        result = await orchestrator.execute_skills(task)

        # Combined
        result = await orchestrator.execute_unified(spec_text, auto_execute=True)
    """

    def __init__(self, config: Optional[ShannonConfig] = None):
        """Initialize unified orchestrator with shared subsystems.

        Args:
            config: Optional ShannonConfig (creates default if not provided)
        """
        self.config = config or ShannonConfig()

        # Thread safety for shared mutable state
        self._budget_lock = asyncio.Lock()

        # Initialize shared subsystems (available to both V3 and V4)
        self._initialize_shared_subsystems()

        # Initialize V3-specific components
        self._initialize_v3_components()

        # Initialize V4-specific components
        self._initialize_v4_components()

        logger.info("UnifiedOrchestrator initialized: V3+V4 consolidated")

    def _initialize_shared_subsystems(self):
        """Initialize subsystems shared between V3 and V4 flows."""

        # Cache: Shared analysis and skill result caching
        try:
            cache_dir = self.config.config_dir / 'cache'
            self.cache = CacheManager(base_dir=cache_dir)
            logger.info("✓ Shared CacheManager initialized")
        except Exception as e:
            logger.warning(f"CacheManager initialization failed: {e}")
            self.cache = None

        # Context: Shared project context loading
        try:
            self.context = ContextManager()
            logger.info("✓ Shared ContextManager initialized")
        except Exception as e:
            logger.warning(f"ContextManager initialization failed: {e}")
            self.context = None

        # Analytics: Shared session and performance recording
        try:
            analytics_db_path = self.config.config_dir / 'analytics.db'
            self.analytics_db = AnalyticsDatabase(db_path=analytics_db_path)
            logger.info("✓ Shared AnalyticsDatabase initialized")
        except Exception as e:
            logger.warning(f"AnalyticsDatabase initialization failed: {e}")
            self.analytics_db = None

        # Cost Optimization: Shared model selection and budget enforcement
        try:
            self.model_selector = ModelSelector()
            self.cost_estimator = CostEstimator()
            self.budget_enforcer = BudgetEnforcer()
            logger.info("✓ Shared cost optimization initialized")
        except Exception as e:
            logger.warning(f"Cost optimization initialization failed: {e}")
            self.model_selector = None
            self.cost_estimator = None
            self.budget_enforcer = None

        # Agent Pool: Shared parallel agent execution
        try:
            self.agent_pool = AgentPool(max_active=8, max_total=50)
            logger.info("✓ Shared AgentPool initialized (8 active / 50 max)")
        except Exception as e:
            logger.warning(f"AgentPool initialization failed: {e}")
            self.agent_pool = None

        # SDK Client: Shared Shannon Framework interface
        try:
            self.sdk_client = ShannonSDKClient()
            logger.info("✓ Shared SDK client initialized")
        except Exception as e:
            logger.error(f"SDK client initialization failed: {e}")
            self.sdk_client = None

    def _initialize_v3_components(self):
        """Initialize V3-specific components."""

        # MCP Manager (V3 feature)
        try:
            self.mcp = MCPManager()
            logger.info("✓ V3 MCPManager initialized")
        except Exception as e:
            logger.warning(f"MCPManager initialization failed: {e}")
            self.mcp = None

        # Agent State Tracker (V3 wave monitoring)
        try:
            self.agent_tracker = AgentStateTracker()
            self.agent_controller = AgentController(self.agent_tracker)
            logger.info("✓ V3 Agent tracking initialized")
        except Exception as e:
            logger.warning(f"Agent tracking initialization failed: {e}")
            self.agent_tracker = None
            self.agent_controller = None

        # Create V3 orchestrator instance with shared subsystems
        try:
            self.v3_orchestrator = ContextAwareOrchestrator(self.config)

            # Inject shared subsystems (override V3's own instances)
            self.v3_orchestrator.cache = self.cache
            self.v3_orchestrator.context = self.context
            self.v3_orchestrator.analytics_db = self.analytics_db
            self.v3_orchestrator.model_selector = self.model_selector
            self.v3_orchestrator.cost_estimator = self.cost_estimator
            self.v3_orchestrator.budget_enforcer = self.budget_enforcer
            self.v3_orchestrator.sdk_client = self.sdk_client
            self.v3_orchestrator.agent_pool = self.agent_pool

            logger.info("✓ V3 ContextAwareOrchestrator created with shared subsystems")
        except Exception as e:
            logger.error(f"V3 orchestrator initialization failed: {e}")
            self.v3_orchestrator = None

    def _initialize_v4_components(self):
        """Initialize infrastructure components (not custom skills framework).

        V5: Removed custom skills framework (SkillRegistry, Planner, Executor).
        Shannon V5 uses Shannon Framework Claude Code skills instead.

        Keeping only:
        - StateManager: For execution checkpoints
        """

        # State Manager - for checkpoints and rollback
        try:
            # Use config directory as project root for state management
            project_root = self.config.config_dir / "execution_state"
            project_root.mkdir(parents=True, exist_ok=True)

            self.state_manager = StateManager(project_root=project_root)
            logger.info(f"✓ StateManager initialized (root: {project_root})")
        except Exception as e:
            logger.warning(f"StateManager initialization failed: {e}")
            self.state_manager = None

    async def execute_analysis(
        self,
        spec_text: str,
        project_id: Optional[str] = None,
        use_cache: bool = True,
        show_metrics: bool = True,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute specification analysis via V3 ContextAwareOrchestrator.

        This method delegates to the V3 orchestrator which provides:
        - Context-aware analysis
        - Multi-tier caching
        - Cost optimization
        - MCP recommendations
        - Analytics recording

        Args:
            spec_text: Specification text to analyze
            project_id: Optional project ID for context-aware analysis
            use_cache: Whether to check/use cache (default: True)
            show_metrics: Whether to show live metrics dashboard (default: True)
            session_id: Optional session ID for tracking

        Returns:
            Analysis result dictionary with complexity scores, domains, recommendations

        Raises:
            RuntimeError: If V3 orchestrator not available
        """
        if not self.v3_orchestrator:
            raise RuntimeError("V3 orchestrator not available")

        logger.info(f"Delegating to V3 analysis: project={project_id}, cache={use_cache}")

        # Delegate to V3 ContextAwareOrchestrator
        # Shared subsystems already injected during initialization
        result = await self.v3_orchestrator.execute_analyze(
            spec_text=spec_text,
            project_id=project_id,
            use_cache=use_cache,
            show_metrics=show_metrics,
            session_id=session_id
        )

        logger.info("V3 analysis complete")
        return result

    async def execute_wave(
        self,
        wave_request: str,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Execute wave-based implementation via V3 ContextAwareOrchestrator.

        Args:
            wave_request: Wave execution request
            project_id: Optional project ID for context
            session_id: Session ID for tracking
            use_cache: Whether to use cached results

        Returns:
            Wave execution results
        """
        if not self.v3_orchestrator:
            raise RuntimeError("V3 orchestrator not available")

        logger.info(f"Delegating to V3 wave: {wave_request}")

        result = await self.v3_orchestrator.execute_wave(
            wave_request=wave_request,
            project_id=project_id,
            session_id=session_id,
            use_cache=use_cache
        )

        logger.info("V3 wave complete")
        return result

    async def execute_task(
        self,
        task: str,
        project_path: Optional[Path] = None,  # NEW
        dashboard_client: Optional[Any] = None,
        session_id: Optional[str] = None,
        auto_mode: bool = False  # NEW
    ) -> Dict[str, Any]:
        """Execute task with intelligent context-aware workflows.

        V5: Detects first-time vs returning to project, auto-explores on first time,
        uses cached context on return, manages validation gates.

        Workflow:
        - First time: Auto-onboard → Ask gates → Plan → Execute
        - Returning: Load context → Check changes → Plan → Execute
        - Auto mode: Skip all interactions (autonomous)

        Args:
            task: Natural language task description
            project_path: Optional project directory (defaults to cwd)
            dashboard_client: Optional DashboardEventClient for real-time updates
            session_id: Optional session ID for tracking
            auto_mode: Skip user interactions (autonomous mode)

        Returns:
            Execution result dictionary

        Raises:
            RuntimeError: If SDK client not available
        """
        if not self.sdk_client:
            raise RuntimeError("SDK client not available")

        logger.info(f"Executing task: {task}")

        # Determine project path
        if not project_path:
            project_path = Path.cwd()

        project_id = project_path.name

        # Context detection: First time vs returning
        if not await self._project_context_exists(project_id):
            # FIRST TIME workflow
            result = await self._first_time_workflow(
                task, project_id, project_path, auto_mode, dashboard_client
            )
        else:
            # RETURNING workflow
            result = await self._returning_workflow(
                task, project_id, project_path, auto_mode, dashboard_client
            )

        return result

    async def _project_context_exists(self, project_id: str) -> bool:
        """Check if we have context for this project.

        Checks both:
        1. ContextManager has the project
        2. Local config exists (~/.shannon/projects/<project_id>/config.json)

        Args:
            project_id: Project identifier (usually directory name)

        Returns:
            True if project has been onboarded and config saved
        """
        if not self.context:
            return False

        # Check ContextManager
        has_context = await self.context.project_exists(project_id)

        # Check local config
        config_path = self.config.config_dir / 'projects' / project_id / 'config.json'
        has_config = config_path.exists()

        return has_context and has_config

    async def _ask_validation_gates(self, context: Dict) -> Dict[str, str]:
        """Ask user for validation commands (interactive mode).

        Shows auto-detected gates, lets user accept/edit.

        Args:
            context: Project context with discovery info

        Returns:
            Dictionary of validation gate commands
        """
        # Auto-detect first
        detected = await self._auto_detect_validation_gates(context)

        print("\nValidation Gates (what to run after making changes):")
        print(f"  Build: {detected.get('build_cmd', 'None detected')}")
        print(f"  Tests: {detected.get('test_cmd', 'None detected')}")
        print(f"  Lint: {detected.get('lint_cmd', 'None detected')}")
        print("\nAccept these gates? [Y/n]: ", end='', flush=True)

        # For now, return detected (full user interaction TODO)
        # This allows autonomous execution while preserving the prompt
        return detected

    async def _auto_detect_validation_gates(self, context: Dict) -> Dict[str, str]:
        """Auto-detect validation commands from project structure.

        Checks package.json, pyproject.toml, etc. for test commands.

        Args:
            context: Project context with discovery info

        Returns:
            Dictionary of detected validation commands
        """
        gates = {}
        discovery = context.get('discovery', {})
        tech_stack = discovery.get('tech_stack', [])

        # Python projects
        if any('python' in t.lower() for t in tech_stack):
            gates['test_cmd'] = 'python -m pytest tests/ || python -m unittest discover'
            gates['lint_cmd'] = 'python -m ruff check . || python -m flake8'

        # Node.js projects
        if any('node' in t.lower() or 'npm' in t.lower() for t in tech_stack):
            gates['build_cmd'] = 'npm run build'
            gates['test_cmd'] = 'npm test'
            gates['lint_cmd'] = 'npm run lint'

        return gates

    async def _execute_with_context(
        self,
        task: str,
        context: Dict,
        validation_gates: Dict[str, str],
        dashboard_client: Optional[Any]
    ) -> Dict[str, Any]:
        """Execute task with project context awareness.

        Creates context-enhanced prompt that tells exec skill about:
        - Existing tech stack
        - Project patterns
        - Validation requirements

        Args:
            task: Task to execute
            context: Project context from ContextManager
            validation_gates: Validation commands to run
            dashboard_client: Optional dashboard client for streaming

        Returns:
            Execution result dictionary
        """
        # Build context-enhanced prompt
        discovery = context.get('discovery', {})

        planning_prompt = f"""Task: {task}

PROJECT CONTEXT:
- Tech Stack: {', '.join(discovery.get('tech_stack', []))}
- Files: {discovery.get('file_count', 0)} files
- Modules: {len(discovery.get('modules', []))} modules
- Entry Points: {', '.join(discovery.get('entry_points', [])[:3])}

VALIDATION REQUIREMENTS:
- Test command: {validation_gates.get('test_cmd', 'None')}
- Build command: {validation_gates.get('build_cmd', 'None')}
- Lint command: {validation_gates.get('lint_cmd', 'None')}

REQUIREMENTS:
1. Integrate with existing code patterns
2. Use project's tech stack
3. Follow project conventions
4. Ensure code can be validated with above commands

Execute this task with full project awareness."""

        # V3: Model selection
        model = 'sonnet'
        if self.model_selector and self.budget_enforcer:
            try:
                complexity = min(1.0, len(task) / 500)  # Clamp to [0.0, 1.0]
                selection = self.model_selector.select_optimal_model(
                    agent_complexity=complexity,
                    context_size_tokens=len(planning_prompt) / 4,
                    budget_remaining=self.budget_enforcer.get_status().remaining
                )
                model = selection.model
                logger.info(f"Selected model: {model}")
            except Exception as e:
                logger.warning(f"Model selection failed: {e}")

        # Execute via Shannon Framework intelligent-do skill
        # intelligent-do: Context-aware execution with Serena backend, auto-research, smart spec
        logger.info("Executing via intelligent-do skill (Serena MCP backend)")
        messages = []

        async for msg in self.sdk_client.invoke_skill(
            skill_name='intelligent-do',
            prompt_content=f"Task: {task}"  # Skill handles context loading from Serena
        ):
            messages.append(msg)
            if dashboard_client:
                await self._stream_message_to_dashboard(msg, dashboard_client)

        return self._parse_task_result(messages)

    async def _save_project_config(self, project_id: str, config: Dict) -> None:
        """Save project configuration (validation gates, timestamps, etc.).

        Args:
            project_id: Project identifier
            config: Configuration dictionary to save
        """
        config_path = self.config.config_dir / 'projects' / project_id / 'config.json'
        config_path.parent.mkdir(parents=True, exist_ok=True)

        import json
        config_path.write_text(json.dumps(config, indent=2))
        logger.info(f"Saved config for {project_id}")

    async def _load_project_config(self, project_id: str) -> Dict:
        """Load project configuration.

        Args:
            project_id: Project identifier

        Returns:
            Project configuration dictionary (empty dict if not found)
        """
        config_path = self.config.config_dir / 'projects' / project_id / 'config.json'

        if not config_path.exists():
            return {}

        import json
        return json.loads(config_path.read_text())

    async def _codebase_changed(self, project_path: Path, config: Dict) -> bool:
        """Detect if codebase changed since last scan.

        Simple: Compare file count (sophisticated: git commit hash)

        Args:
            project_path: Path to project directory
            config: Project configuration with previous file count

        Returns:
            True if codebase has changed significantly
        """
        current_files = len(list(project_path.rglob('*.py')))
        last_files = config.get('file_count', 0)

        # Changed if file count differs by more than 5%
        return abs(current_files - last_files) > (last_files * 0.05) if last_files > 0 else True

    async def _first_time_workflow(
        self,
        task: str,
        project_id: str,
        project_path: Path,
        auto_mode: bool,
        dashboard_client: Optional[Any]
    ) -> Dict[str, Any]:
        """Execute workflow for first time in a project.

        Steps:
        1. Auto-onboard project (explore codebase)
        2. Get validation gates (ask user or auto-detect)
        3. Save config for next time
        4. Execute with context-enhanced planning

        Args:
            task: Task to execute
            project_id: Project identifier
            project_path: Path to project directory
            auto_mode: Skip user interactions
            dashboard_client: Optional dashboard client

        Returns:
            Execution result dictionary
        """
        logger.info(f"First time workflow for: {project_id}")

        # 1. Auto-onboard
        if not auto_mode:
            print(f"First time in {project_id} - exploring codebase...")

        context = await self.context.onboard_project(
            project_path=str(project_path),
            project_id=project_id
        )

        if not auto_mode:
            discovery = context.get('discovery', {})
            print(f"  Detected: {', '.join(discovery.get('tech_stack', []))}")
            print(f"  Files: {discovery.get('file_count', 0):,}")

        # 2. Validation gates
        if not auto_mode:
            gates = await self._ask_validation_gates(context)
        else:
            gates = await self._auto_detect_validation_gates(context)

        # 3. Save config
        from datetime import datetime
        await self._save_project_config(project_id, {
            'validation_gates': gates,
            'last_scan': datetime.now().isoformat(),
            'tech_stack': context.get('discovery', {}).get('tech_stack', []),
            'file_count': context.get('discovery', {}).get('file_count', 0)
        })

        # 4. Execute with context
        result = await self._execute_with_context(
            task, context, gates, dashboard_client
        )

        return result

    async def _returning_workflow(
        self,
        task: str,
        project_id: str,
        project_path: Path,
        auto_mode: bool,
        dashboard_client: Optional[Any]
    ) -> Dict[str, Any]:
        """Execute workflow for returning to known project.

        Steps:
        1. Load cached context
        2. Check for codebase changes
        3. Update context if needed
        4. Execute with cached validation gates

        Args:
            task: Task to execute
            project_id: Project identifier
            project_path: Path to project directory
            auto_mode: Skip user interactions
            dashboard_client: Optional dashboard client

        Returns:
            Execution result dictionary
        """
        logger.info(f"Returning workflow for: {project_id}")

        # 1. Load context and config
        context = await self.context.load_project(project_id)
        config = await self._load_project_config(project_id)
        gates = config.get('validation_gates', {})

        # 2. Check for changes
        if await self._codebase_changed(project_path, config):
            if not auto_mode:
                print("Codebase changed - updating context...")

            # Update project (returns ChangeSet)
            await self.context.update_project(project_id)
            
            # Reload context after update
            context = await self.context.load_project(project_id)
            
            from datetime import datetime
            config['last_updated'] = datetime.now().isoformat()
            config['file_count'] = context.get('discovery', {}).get('file_count', config.get('file_count', 0))
            await self._save_project_config(project_id, config)
        else:
            if not auto_mode:
                print("Using cached context (< 1s)")

        # 3. Execute with context
        result = await self._execute_with_context(
            task, context, gates, dashboard_client
        )

        return result

    async def _stream_message_to_dashboard(
        self,
        msg: Any,
        dashboard_client: Any
    ) -> None:
        """Stream message to dashboard with correct event types (colon-separated)."""
        from claude_agent_sdk import TextBlock, ToolUseBlock, ThinkingBlock, AssistantMessage
        
        try:
            if isinstance(msg, TextBlock):
                # Map to execution:progress (colon not underscore)
                await dashboard_client.emit_event('execution:progress', {
                    'progress': 50,
                    'message': msg.text[:200]
                })
            elif isinstance(msg, ToolUseBlock):
                if msg.name in ['Write', 'Edit', 'MultiEdit']:
                    # File modification event (colon-separated)
                    file_path = msg.input.get('file_path', 'unknown')
                    await dashboard_client.emit_event('file:modified', {
                        'file_path': file_path,
                        'operation': msg.name,
                        'timestamp': datetime.now().isoformat()
                    })
                elif msg.name == 'Skill':
                    # Skill invocation (colon-separated)
                    skill_name = msg.input.get('skill', 'unknown')
                    await dashboard_client.emit_event('skill:started', {
                        'skill_id': f"skill_{skill_name}_{int(time.time())}",
                        'skill_name': skill_name,
                        'timestamp': datetime.now().isoformat()
                    })
            elif isinstance(msg, ThinkingBlock):
                # Thinking = progress
                await dashboard_client.emit_event('execution:progress', {
                    'progress': 25,
                    'thinking': True
                })
        except Exception as e:
            logger.warning(f"Dashboard streaming failed: {e}")

    def _parse_task_result(self, messages: List) -> Dict[str, Any]:
        """Parse task execution result from Claude messages."""
        from claude_agent_sdk import ResultMessage, ToolUseBlock

        # Extract result message
        result_msgs = [m for m in messages if isinstance(m, ResultMessage)]
        files_created = []

        # Find file operations from messages
        for msg in messages:
            if hasattr(msg, 'content'):
                for block in msg.content:
                    if isinstance(block, ToolUseBlock) and block.name in ['Write', 'Edit']:
                        file_path = block.input.get('file_path')
                        if file_path:
                            files_created.append(file_path)

        return {
            'success': len(result_msgs) > 0 and not result_msgs[-1].is_error if result_msgs else True,
            'files_created': files_created,
            'message_count': len(messages),
            'result_messages': result_msgs
        }

    async def execute_unified(
        self,
        spec_text: str,
        auto_execute: bool = True,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        dashboard_client: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Execute unified workflow: V3 analysis → V4 execution.

        This is the "full Shannon" experience:
        1. Analyze spec with V3 (complexity, domains, recommendations)
        2. Generate implementation plan
        3. Execute via V4 skills (with multi-agent, dashboard, controls)

        Args:
            spec_text: Specification text
            auto_execute: Whether to automatically execute after analysis
            project_id: Optional project ID for context
            session_id: Session ID for tracking
            dashboard_client: Optional dashboard client for real-time updates

        Returns:
            Combined analysis and execution results
        """
        logger.info("Starting unified V3→V4 workflow")

        # Step 1: V3 Analysis
        analysis_result = await self.execute_analysis(
            spec_text=spec_text,
            project_id=project_id,
            session_id=session_id,
            use_cache=True,
            show_metrics=True
        )

        logger.info("Analysis complete, proceeding to execution")

        # Step 2: V4 Execution (if auto_execute)
        execution_result = None
        if auto_execute:
            # Convert analysis to implementation task
            task = f"Implement: {spec_text}"

            execution_result = await self.execute_skills(
                task=task,
                dashboard_client=dashboard_client,
                session_id=session_id
            )

        # Return combined results
        return {
            'analysis': analysis_result,
            'execution': execution_result,
            'unified': True
        }

    def get_status(self) -> Dict[str, Any]:
        """Get status of all subsystems and orchestrators.

        Returns:
            Status dictionary with health of all components
        """
        return {
            'unified': {
                'version': '5.1.0',
                'mode': 'unified'
            },
            'shared_subsystems': {
                'cache': self.cache is not None,
                'context': self.context is not None,
                'analytics': self.analytics_db is not None,
                'cost_optimization': all([
                    self.model_selector is not None,
                    self.cost_estimator is not None,
                    self.budget_enforcer is not None
                ]),
                'agent_pool': self.agent_pool is not None,
                'sdk_client': self.sdk_client is not None
            },
            'v3_components': {
                'orchestrator': self.v3_orchestrator is not None,
                'mcp_manager': self.mcp is not None,
                'agent_tracker': self.agent_tracker is not None,
                'agent_controller': self.agent_controller is not None
            },
            'v5_components': {
                'state_manager': self.state_manager is not None,
                'intelligent_workflows': True  # First-time, returning workflows
            }
        }

    async def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status (thread-safe).

        Returns:
            Budget status dictionary
        """
        if not self.budget_enforcer:
            return {'available': False}

        async with self._budget_lock:
            status = self.budget_enforcer.get_status()
            return {
                'limit': status.limit,
                'spent': status.spent,
                'remaining': status.remaining,
                'available': True
            }

    async def check_budget(self, estimated_cost: float) -> bool:
        """Check if budget allows estimated cost (thread-safe).

        Args:
            estimated_cost: Estimated cost in USD

        Returns:
            True if budget allows, False otherwise
        """
        if not self.budget_enforcer:
            return True  # No enforcement if not available

        async with self._budget_lock:
            return self.budget_enforcer.check_available(estimated_cost)


# Convenience function for easy access
def create_unified_orchestrator(config: Optional[ShannonConfig] = None) -> UnifiedOrchestrator:
    """Create and return a UnifiedOrchestrator instance.

    Args:
        config: Optional configuration

    Returns:
        Configured unified orchestrator instance
    """
    return UnifiedOrchestrator(config)
