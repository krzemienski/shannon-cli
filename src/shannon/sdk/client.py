"""Shannon Framework SDK Client

Thin wrapper over Claude Agent SDK for invoking Shannon Framework skills.
All algorithm logic (8D analysis, wave orchestration) lives in Shannon Framework.
"""

from pathlib import Path
from typing import AsyncIterator, Optional, Callable, Any, List
import os
import logging

try:
    from claude_agent_sdk import (
        query,
        ClaudeAgentOptions,
        AssistantMessage,
        TextBlock,
        ToolUseBlock,
        SystemMessage,
        ResultMessage
    )
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

# V3 Imports
from .interceptor import MessageInterceptor, MessageCollector
from .stream_handler import StreamHandler


class ShannonSDKClient:
    """
    Client for invoking Shannon Framework via Claude Agent SDK

    Loads Shannon Framework as plugin and delegates all algorithm logic
    to framework's 18 skills via @skill commands.

    Architecture:
        Shannon CLI → ShannonSDKClient → Claude Agent SDK → Shannon Framework Plugin → Skills
    """

    def __init__(
        self,
        framework_path: Optional[Path] = None,
        logger: Optional[logging.Logger] = None,
        enable_v3_features: bool = False,
        message_collectors: Optional[List[MessageCollector]] = None
    ):
        """
        Initialize SDK client with Shannon Framework plugin

        Args:
            framework_path: Path to shannon-framework directory
                          (default: auto-detect from environment or standard locations)
            logger: Optional logger instance
            enable_v3_features: Enable V3 message interception and streaming (default: False)
            message_collectors: Optional collectors for V3 message interception

        Raises:
            ImportError: If claude_agent_sdk not installed
            FileNotFoundError: If Shannon Framework not found
        """
        if not SDK_AVAILABLE:
            raise ImportError(
                "claude_agent_sdk not installed. Install with: pip install claude-agent-sdk"
            )

        self.logger = logger or self._default_logger()

        # Locate Shannon Framework
        self.framework_path = framework_path or self._find_shannon_framework()

        self.logger.debug(f"Shannon Framework path: {self.framework_path}")

        # Verify framework exists
        if not self.framework_path.exists():
            raise FileNotFoundError(
                f"Shannon Framework not found at: {self.framework_path}"
            )

        # Verify plugin structure
        plugin_json = self.framework_path / ".claude-plugin" / "plugin.json"
        if not plugin_json.exists():
            raise FileNotFoundError(
                f"Invalid Shannon Framework: missing {plugin_json}"
            )

        # Base options for all SDK calls
        # Note: plugins parameter expects list of dicts with "type" and "path"
        self.base_options = ClaudeAgentOptions(
            plugins=[{
                "type": "local",
                "path": str(self.framework_path)
            }],
            setting_sources=["user", "project"],  # CRITICAL: Load skills from filesystem
            permission_mode="bypassPermissions",  # Auto-approve for CLI usage
            allowed_tools=[
                "Skill", "Read", "Write", "Bash", "SlashCommand", "Grep", "Glob", "TodoWrite",
                # Serena MCP tools (required by spec-analysis skill)
                "mcp__serena__write_memory",
                "mcp__serena__read_memory",
                "mcp__serena__list_memories",
                "mcp__serena__get_current_config",
                # Sequential thinking (optional but recommended)
                "mcp__sequential-thinking__sequentialthinking"
            ]
            # model defaults to latest sonnet with extended context
        )

        # V3 Features
        self.enable_v3_features = enable_v3_features
        self.message_collectors = message_collectors or []

        if enable_v3_features:
            self.interceptor = MessageInterceptor(logger=self.logger)
            self.stream_handler = StreamHandler(
                enable_buffering=False,  # Buffering optional, disabled by default
                logger=self.logger
            )
            self.logger.info("V3 features enabled: message interception and stream handling")
        else:
            self.interceptor = None
            self.stream_handler = None

        self.logger.info("ShannonSDKClient initialized")
        self.logger.debug(f"  Plugin: {self.framework_path}")
        self.logger.debug(f"  Setting sources: user, project")
        self.logger.debug(f"  Model: sonnet[1m]")
        self.logger.debug(f"  V3 features: {enable_v3_features}")

    async def invoke_skill(
        self,
        skill_name: str,
        prompt_content: str,
        progress_callback: Optional[Callable[[Any], None]] = None
    ) -> AsyncIterator[Any]:
        """
        Invoke a Shannon Framework skill

        Args:
            skill_name: Skill name (e.g., 'spec-analysis', 'wave-orchestration')
            prompt_content: Content to pass to skill
            progress_callback: Optional callback(message) for progress updates

        Yields:
            SDK messages (AssistantMessage, ToolUseBlock, SystemMessage, etc.)

        Example:
            async for msg in client.invoke_skill('spec-analysis', spec_text):
                if isinstance(msg, AssistantMessage):
                    print(f"Response: {msg.content}")
        """
        self.logger.info(f"Invoking skill: {skill_name}")
        self.logger.debug(f"  Content length: {len(prompt_content)} chars")

        # Format prompt for skill invocation
        # Skills are invoked with @skill command syntax
        prompt = f"@skill {skill_name}\n\n{prompt_content}"

        self.logger.debug(f"  Prompt preview: {prompt[:200]}...")

        # Query SDK with Shannon Framework plugin loaded
        message_count = 0
        try:
            # Get base query iterator
            query_iterator = query(prompt=prompt, options=self.base_options)

            # V3 Enhancement: Wrap with interceptor if enabled
            if self.enable_v3_features and self.interceptor:
                # Apply message interception
                query_iterator = self.interceptor.intercept(
                    query_iterator,
                    self.message_collectors
                )

                # Apply stream handling if configured
                if self.stream_handler:
                    query_iterator = self.stream_handler.handle(query_iterator)

            # Iterate messages (V2 behavior or V3 enhanced)
            async for msg in query_iterator:
                message_count += 1
                msg_type = type(msg).__name__
                self.logger.debug(f"  Message {message_count}: {msg_type}")

                # Call progress callback if provided
                if progress_callback:
                    try:
                        progress_callback(msg)
                    except Exception as e:
                        self.logger.warning(f"Progress callback error: {e}")

                yield msg

            self.logger.info(f"Skill {skill_name} complete ({message_count} messages)")

        except Exception as e:
            self.logger.error(f"Skill invocation failed: {e}")
            raise

    async def invoke_command(
        self,
        command: str,
        args: str = "",
        progress_callback: Optional[Callable[[Any], None]] = None
    ) -> AsyncIterator[Any]:
        """
        Invoke a Shannon Framework slash command

        Args:
            command: Command name (e.g., '/shannon:spec', '/shannon:wave')
            args: Command arguments
            progress_callback: Optional callback for progress

        Yields:
            SDK messages

        Example:
            async for msg in client.invoke_command('/shannon:spec', 'analyze todo.md'):
                print(msg)
        """
        self.logger.info(f"Invoking command: {command} {args}")

        # Format command with args
        prompt = f"{command} {args}".strip()

        self.logger.debug(f"  Command: {prompt}")

        try:
            async for msg in query(prompt=prompt, options=self.base_options):
                if progress_callback:
                    try:
                        progress_callback(msg)
                    except Exception as e:
                        self.logger.warning(f"Progress callback error: {e}")

                yield msg

        except Exception as e:
            self.logger.error(f"Command invocation failed: {e}")
            raise

    async def invoke_command_with_enhancements(
        self,
        command: str,
        args: str = "",
        system_prompt_enhancements: str = "",
        progress_callback: Optional[Callable[[Any], None]] = None
    ) -> AsyncIterator[Any]:
        """
        Invoke Shannon command with enhanced system prompts (V3.5)
        
        This method allows injecting custom system prompt instructions
        via ClaudeAgentOptions.system_prompt.append. Used by V3.5
        autonomous executor to inject library discovery, validation,
        and git workflow instructions.
        
        Args:
            command: Command name (e.g., '/shannon:exec')
            args: Command arguments
            system_prompt_enhancements: Additional system prompt text to inject
            progress_callback: Optional callback for progress
            
        Yields:
            SDK messages
            
        Example:
            enhancements = build_exec_enhancements(task, project_type)
            async for msg in client.invoke_command_with_enhancements(
                '/shannon:exec',
                'fix iOS login',
                enhancements
            ):
                print(msg)
        """
        self.logger.info(f"Invoking command with enhancements: {command} {args}")
        self.logger.debug(f"  System prompt enhancements: {len(system_prompt_enhancements)} chars")
        
        # Format command with args
        prompt = f"{command} {args}".strip()
        
        # Create enhanced options
        enhanced_options = ClaudeAgentOptions(
            plugins=self.base_options.plugins,
            setting_sources=self.base_options.setting_sources,
            permission_mode=self.base_options.permission_mode,
            allowed_tools=self.base_options.allowed_tools,
            system_prompt={
                "type": "preset",
                "preset": "claude_code",
                "append": system_prompt_enhancements
            } if system_prompt_enhancements else self.base_options.system_prompt
        )
        
        try:
            # Query with enhanced options
            query_iterator = query(prompt=prompt, options=enhanced_options)
            
            # V3 Enhancement: Wrap with interceptor if enabled
            if self.enable_v3_features and self.interceptor:
                query_iterator = self.interceptor.intercept(
                    query_iterator,
                    self.message_collectors
                )
                if self.stream_handler:
                    query_iterator = self.stream_handler.handle(query_iterator)
            
            # Iterate messages
            async for msg in query_iterator:
                if progress_callback:
                    try:
                        progress_callback(msg)
                    except Exception as e:
                        self.logger.warning(f"Progress callback error: {e}")
                
                yield msg
        
        except Exception as e:
            self.logger.error(f"Enhanced command invocation failed: {e}")
            raise

    def _find_shannon_framework(self) -> Path:
        """
        Locate Shannon Framework directory

        Checks (in order):
        1. SHANNON_FRAMEWORK_PATH environment variable
        2. /Users/nick/Desktop/shannon-framework (development)
        3. ~/.shannon/shannon-framework (user install)
        4. /usr/local/shannon/shannon-framework (system install)

        Returns:
            Path to shannon-framework directory

        Raises:
            FileNotFoundError: If framework not found
        """
        # Check env var
        env_path = os.getenv('SHANNON_FRAMEWORK_PATH')
        if env_path:
            path = Path(env_path)
            if path.exists():
                self.logger.debug(f"Found via SHANNON_FRAMEWORK_PATH: {path}")
                return path

        # Check common locations
        candidates = [
            Path("/Users/nick/Desktop/shannon-framework"),
            Path.home() / ".shannon" / "shannon-framework",
            Path("/usr/local/shannon/shannon-framework")
        ]

        for candidate in candidates:
            plugin_json = candidate / ".claude-plugin" / "plugin.json"
            if candidate.exists() and plugin_json.exists():
                self.logger.debug(f"Found Shannon Framework at: {candidate}")
                return candidate

        # Framework not found
        raise FileNotFoundError(
            "Shannon Framework not found. Tried:\n"
            f"  - SHANNON_FRAMEWORK_PATH env var\n"
            f"  - {candidates[0]}\n"
            f"  - {candidates[1]}\n"
            f"  - {candidates[2]}\n"
            "\n"
            "Set SHANNON_FRAMEWORK_PATH or install Shannon Framework to one of the above locations."
        )

    def _default_logger(self) -> logging.Logger:
        """Create default logger if none provided"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    # V3 Feature Management Methods

    def add_collector(self, collector: MessageCollector) -> None:
        """
        Add a message collector for V3 interception

        Args:
            collector: MessageCollector instance to add

        Example:
            client = ShannonSDKClient(enable_v3_features=True)
            client.add_collector(MetricsCollector())
            client.add_collector(ContextCollector())
        """
        if not self.enable_v3_features:
            self.logger.warning("V3 features not enabled - collector will have no effect")

        self.message_collectors.append(collector)
        self.logger.debug(f"Added collector: {collector.__class__.__name__}")

    def remove_collector(self, collector: MessageCollector) -> None:
        """
        Remove a message collector

        Args:
            collector: Collector instance to remove
        """
        if collector in self.message_collectors:
            self.message_collectors.remove(collector)
            self.logger.debug(f"Removed collector: {collector.__class__.__name__}")

    def clear_collectors(self) -> None:
        """Clear all message collectors"""
        self.message_collectors.clear()
        self.logger.debug("Cleared all collectors")

    def get_stream_stats(self) -> Optional[dict[str, Any]]:
        """
        Get stream handler statistics (if V3 enabled)

        Returns:
            Dictionary with stream stats, or None if V3 disabled
        """
        if self.stream_handler:
            return self.stream_handler.get_stats()
        return None
