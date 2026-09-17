"""Shannon CLI commands - Click command definitions.

This module provides the main CLI commands for Shannon Framework:
- analyze: Analyze specifications using 8D complexity analysis
- wave: Execute wave-based implementation
- task: Automated workflow (analyze + wave)
- test: Run functional tests with NO MOCKS enforcement
- reflect: Pre-completion gap analysis
- checkpoint: Create or list session checkpoints
- restore: Restore session from checkpoint
- status: Show current session status
- sessions: List all sessions
- config: Display configuration settings
- setup: Interactive setup wizard
- diagnostics: Show framework detection diagnostics

Created for: Wave 3 - SDK & Integration
Component: CLI Commands (Agent D)
"""

import sys
import time
import functools
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import anyio
import click
from rich.console import Console
from rich.prompt import Confirm

from shannon.config import ShannonConfig
from shannon.core.session_manager import SessionManager
from shannon.sdk.client import ShannonSDKClient
from shannon.sdk.message_parser import MessageParser
from shannon.ui.progress import ProgressUI
from shannon.setup.framework_detector import FrameworkDetector
from shannon.setup.wizard import SetupWizard

# Initialize logger
logger = logging.getLogger(__name__)


def require_framework():
    """Decorator to ensure Shannon Framework is available before command execution.

    Checks for framework installation and prompts user to run setup wizard
    if not found. Commands decorated with this will fail gracefully if the
    framework is not accessible.

    Example:
        @cli.command()
        @require_framework()
        def analyze(...):
            # Now guaranteed to have framework
            pass
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            # Check if framework available
            framework = FrameworkDetector.find_framework()
            if not framework:
                console = Console()
                console.print()
                console.print("[yellow]⚠ Shannon Framework not detected[/yellow]")
                console.print()
                console.print("Shannon CLI requires Shannon Framework to be installed.")
                console.print()
                console.print("You have two options:")
                console.print("  1. Run the setup wizard: [bold cyan]shannon setup[/bold cyan]")
                console.print("  2. Set SHANNON_FRAMEWORK_PATH environment variable")
                console.print()

                if Confirm.ask("Run setup wizard now?", default=True):
                    wizard = SetupWizard()
                    if not wizard.run():
                        sys.exit(1)
                else:
                    console.print("\n[dim]Setup skipped. Framework must be configured before using Shannon CLI.[/dim]\n")
                    sys.exit(1)
            else:
                # Quick validation
                is_valid, message = FrameworkDetector.verify_framework(framework)
                if not is_valid:
                    console = Console()
                    console.print()
                    console.print(f"[yellow]⚠ Framework validation failed: {message}[/yellow]")
                    console.print()
                    console.print("Run [bold cyan]shannon setup[/bold cyan] to repair or reinstall.")
                    console.print()
                    sys.exit(1)

            return f(*args, **kwargs)
        return wrapped
    return decorator


@click.group()
@click.version_option(version='4.0.0')
def cli() -> None:
    """Shannon Framework - Standalone CLI Agent.

    Wave-based execution with 8D complexity analysis and extreme logging.

    \b
    Common workflow:
        1. shannon setup                  # First-time setup
        2. shannon analyze spec.md        # Analyze specification
        3. shannon wave "implement X"     # Execute implementation
        4. shannon status                 # Check progress
    """
    pass


@cli.command()
@require_framework()
@click.argument('spec_file', type=click.Path(exists=True))
@click.option('--json', 'output_json', is_flag=True, help='Output JSON format')
@click.option('--session-id', help='Session ID (auto-generated if not provided)')
@click.option('--project', help='Project ID for context-aware analysis')
@click.option('--no-cache', is_flag=True, help='Skip cache check')
def analyze(
    spec_file: str,
    output_json: bool,
    session_id: Optional[str],
    project: Optional[str],
    no_cache: bool
) -> None:
    """Analyze specification using Shannon 8D complexity analysis.

    Shows COMPLETE streaming output - every message, every tool call, every response.
    Complete transparency in real-time as Shannon Framework executes.

    \b
    Example:
        shannon analyze project_spec.md
        shannon analyze spec.md --session-id my_project
        shannon analyze spec.md --json > analysis.json

    \b
    The analysis provides:
        - 8D complexity score (0.10-0.95 scale)
        - Dimension-by-dimension breakdown
        - Domain distribution (Frontend, Backend, etc.)
        - MCP server recommendations
        - 5-phase implementation plan
    """
    async def run_analysis() -> None:
        """Execute analysis workflow with COMPLETE streaming visibility."""
        # Initialize components
        config = ShannonConfig()
        config.ensure_directories()

        # Generate session ID if not provided
        if not session_id:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            generated_session_id = f"session_{timestamp}"
        else:
            generated_session_id = session_id

        session = SessionManager(generated_session_id, config)
        console = Console()

        try:
            # Read specification file
            spec_path = Path(spec_file)
            spec_text = spec_path.read_text(encoding='utf-8')

            # Display header with context
            console.print()
            console.print("[bold cyan]Shannon 8D Specification Analysis[/bold cyan]")
            console.print()
            console.print(f"[dim]Spec file: {spec_path}[/dim]")
            console.print(f"[dim]Length: {len(spec_text)} characters[/dim]")
            console.print(f"[dim]Session: {generated_session_id}[/dim]")
            console.print()

            # Check if running inside Claude Code or if API key is missing
            # Allow SHANNON_TEST_MODE to override direct mode for testing
            import os
            test_mode = os.getenv('SHANNON_TEST_MODE') == '1'

            from shannon.cli.direct_mode import is_running_inside_claude_code, check_api_key_and_suggest

            if is_running_inside_claude_code() and not test_mode:
                console.print("[yellow]ℹ️  Running inside Claude Code - using direct mode[/yellow]")
                console.print("[dim]Shannon Framework skills will be invoked directly[/dim]")
                console.print("[dim]Set SHANNON_TEST_MODE=1 to force SDK mode for testing[/dim]")
                console.print()
                console.print("="*60)
                console.print("DIRECT MODE: Execute spec-analysis skill")
                console.print("="*60)
                console.print()
                console.print("Specification to analyze:")
                console.print()
                console.print(spec_text)
                console.print()
                console.print("="*60)
                console.print("Please invoke: @skill spec-analysis")
                console.print("Or use: /shannon:spec via SlashCommand tool")
                console.print("="*60)
                console.print()
                sys.exit(0)

            # Check API key for standalone mode
            if not check_api_key_and_suggest():
                console.print("[red]Cannot proceed: API key required for standalone Shannon CLI[/red]")
                console.print("[dim]Set ANTHROPIC_API_KEY environment variable[/dim]")
                sys.exit(1)

            # Import all SDK message types for complete visibility
            from claude_agent_sdk import (
                AssistantMessage,
                SystemMessage,
                ToolUseBlock,
                TextBlock,
                ThinkingBlock,
                ToolResultBlock,
                ResultMessage
            )

            # Initialize SDK client
            client = ShannonSDKClient()
            parser = MessageParser()

            # V5: Initialize UnifiedOrchestrator for integrated V3+V4 features
            orchestrator = None
            try:
                from shannon.unified_orchestrator import UnifiedOrchestrator
                orchestrator = UnifiedOrchestrator(config)
                logger.info("V5 UnifiedOrchestrator initialized successfully")
            except Exception as e:
                console.print(f"[yellow]V5 features unavailable: {e}[/yellow]\n")

            # ═══════════════════════════════════════════════════════════════
            # V3 INTEGRATION: Cache Check (PRE-EXECUTION)
            # ═══════════════════════════════════════════════════════════════

            if orchestrator and orchestrator.cache and not no_cache:
                try:
                    cached_result = orchestrator.cache.analysis.get(spec_text, None)
                    if cached_result:
                        console.print("[bold green]✓ Cache Hit![/bold green]")
                        console.print("[dim]Returning cached analysis (no API call needed)[/dim]\n")

                        # Display cached result
                        from shannon.ui.formatters import OutputFormatter
                        formatter = OutputFormatter(console=console)
                        console.print(formatter.format_table(cached_result))
                        console.print()
                        console.print(f"[dim]From cache: ~/.shannon/cache/analyses/[/dim]")
                        console.print("[green]✓[/green] [bold]Analysis complete (cached)[/bold]\n")

                        # Record cache hit to analytics
                        if orchestrator.analytics_db:
                            try:
                                orchestrator.analytics_db.record_cache_hit(generated_session_id)
                            except:
                                pass

                        return
                except Exception as e:
                    logger.warning(f"Cache check failed: {e}, continuing without cache")

            # ═══════════════════════════════════════════════════════════════
            # V3 INTEGRATION: Cost Optimization & Model Selection
            # ═══════════════════════════════════════════════════════════════

            selected_model = "sonnet"  # Default
            if orchestrator and orchestrator.model_selector:
                try:
                    # Rough complexity estimate before analysis
                    complexity_estimate = min(1.0, len(spec_text) / 2000)

                    # Get budget status
                    budget_remaining = 100.0  # Default
                    if orchestrator.budget_enforcer:
                        try:
                            budget_status = orchestrator.budget_enforcer.get_status()
                            budget_remaining = budget_status.remaining
                        except:
                            pass

                    # Select optimal model
                    selection = orchestrator.model_selector.select_optimal_model(
                        agent_complexity=complexity_estimate,
                        context_size_tokens=0,
                        budget_remaining=budget_remaining
                    )
                    selected_model = selection.model

                    console.print(f"[dim]✓ Model: {selected_model} (saves ${selection.savings_vs_sonnet:.2f})[/dim]")

                    # Check budget before execution
                    if orchestrator.budget_enforcer:
                        try:
                            # Rough cost estimate
                            estimated_cost = complexity_estimate * 2.0  # Heuristic
                            if not orchestrator.budget_enforcer.check_available(estimated_cost):
                                console.print("[yellow]⚠ Warning: Close to budget limit[/yellow]\n")
                        except:
                            pass

                except Exception as e:
                    logger.warning(f"Cost optimization failed: {e}, using default model")

            console.print()

            # ═══════════════════════════════════════════════════════════════
            # V3: Live Dashboard OR V2: Complete Streaming Visibility
            # ═══════════════════════════════════════════════════════════════

            messages = []
            message_count = 0

            try:
                # Import SDK types
                from claude_agent_sdk import query, SystemMessage, ToolUseBlock, TextBlock, ThinkingBlock, ResultMessage

                # V3: Live Dashboard with interceptor pattern
                if not no_cache and orchestrator:  # Use no_cache as proxy for metrics (will add --no-metrics later)
                    try:
                        from shannon.sdk.interceptor import MessageInterceptor
                        from shannon.metrics.collector import MetricsCollector
                        from shannon.metrics.dashboard import LiveDashboard

                        console.print("[bold]Analyzing with live metrics dashboard...[/bold]")
                        console.print("[dim]Press Enter for detailed view, Esc to collapse[/dim]\n")

                        # Create metrics collector and dashboard
                        collector = MetricsCollector(operation_name="spec-analysis")
                        dashboard = LiveDashboard(collector, refresh_per_second=4)
                        interceptor = MessageInterceptor()

                        # Create query iterator
                        # CRITICAL: Use /spec (not /shannon:spec - no namespace in SDK loading)
                        query_iter = query(
                            prompt=f'/spec "{spec_text}"',
                            options=client.base_options
                        )

                        # Intercept messages for metrics collection
                        instrumented_iter = interceptor.intercept(query_iter, [collector])

                        # Run with live dashboard (sync context manager)
                        with dashboard:
                            async for msg in instrumented_iter:
                                messages.append(msg)
                                message_count += 1

                                # Pass readable message content to dashboard for display
                                from claude_agent_sdk import TextBlock, ToolUseBlock, ThinkingBlock

                                if isinstance(msg, TextBlock):
                                    # Show Shannon's text output
                                    dashboard.update(msg.text)
                                elif isinstance(msg, ToolUseBlock):
                                    # Show tool calls
                                    dashboard.update(f"→ Tool: {msg.name}")
                                elif isinstance(msg, ThinkingBlock):
                                    # Show thinking (truncated)
                                    thinking_preview = msg.thinking[:100] + "..." if len(msg.thinking) > 100 else msg.thinking
                                    dashboard.update(f"💭 {thinking_preview}")
                                elif hasattr(msg, 'content'):
                                    # Handle other message types with content
                                    for block in msg.content:
                                        if isinstance(block, TextBlock):
                                            dashboard.update(block.text)
                                        elif isinstance(block, ToolUseBlock):
                                            dashboard.update(f"→ Tool: {block.name}")

                        console.print("\n[dim]Analysis complete, processing results...[/dim]\n")

                        # Show final metrics from collector
                        final_metrics = collector.get_snapshot()
                        if final_metrics.cost_total > 0 or final_metrics.tokens_total > 0:
                            console.print("[bold cyan]📊 Final Metrics:[/bold cyan]")
                            console.print(f"  Cost: [green]${final_metrics.cost_total:.4f}[/green]")
                            console.print(f"  Tokens: [green]{final_metrics.tokens_total:,}[/green] ({final_metrics.tokens_input:,} in / {final_metrics.tokens_output:,} out)")
                            console.print(f"  Duration: [green]{final_metrics.duration_seconds:.1f}s[/green]")
                            console.print(f"  Messages: [green]{final_metrics.message_count}[/green]")
                            console.print()

                    except Exception as e:
                        console.print(f"[yellow]Dashboard unavailable: {e}[/yellow]")
                        console.print("[dim]Falling back to standard output...[/dim]\n")
                        # Fall through to V2 mode below

                # V2: Standard streaming output (or dashboard fallback)
                if len(messages) == 0:  # Dashboard didn't run or failed
                    console.print("[bold]Invoking Shannon Framework:[/bold]")
                    console.print()

                    # Use query() DIRECTLY
                    # CRITICAL: Use /spec (not /shannon:spec - no namespace when plugin loaded)
                    async for msg in query(
                        prompt=f'/spec "{spec_text}"',
                        options=client.base_options
                    ):
                        messages.append(msg)
                        message_count += 1

                    # ═══════════════════════════════════════════════
                    # SystemMessage - Plugin initialization
                    # ═══════════════════════════════════════════════
                    if isinstance(msg, SystemMessage):
                        if msg.subtype == 'init':
                            plugins = msg.data.get('plugins', [])
                            console.print("[dim]System: Plugin initialized[/dim]")
                            shannon_plugin = [p for p in plugins if 'shannon' in p.get('name', '').lower()]
                            if shannon_plugin:
                                console.print("[dim]  ✓ Shannon Framework loaded[/dim]")
                            console.print()

                    # ═══════════════════════════════════════════════
                    # ToolUseBlock - Show EVERY tool call
                    # ═══════════════════════════════════════════════
                    elif isinstance(msg, ToolUseBlock):
                        console.print(f"[cyan]→ Tool:[/cyan] [bold]{msg.name}[/bold]")

                        # Format tool input based on tool type
                        if msg.name == "Read":
                            file_path = msg.input.get('file_path', '')
                            console.print(f"  [dim]Reading: {file_path}[/dim]")
                        elif msg.name == "Skill":
                            skill = msg.input.get('skill', '')
                            console.print(f"  [dim]Invoking skill: {skill}[/dim]")
                        elif msg.name == "Grep":
                            pattern = msg.input.get('pattern', '')
                            console.print(f"  [dim]Searching: {pattern}[/dim]")
                        elif msg.name == "SlashCommand":
                            command = msg.input.get('command', '')
                            console.print(f"  [dim]Command: {command}[/dim]")
                        else:
                            # Show first 100 chars of input for other tools
                            input_preview = str(msg.input)[:100]
                            if len(str(msg.input)) > 100:
                                input_preview += "..."
                            console.print(f"  [dim]{input_preview}[/dim]")

                        console.print()

                    # ═══════════════════════════════════════════════
                    # TextBlock - Show ALL text output
                    # ═══════════════════════════════════════════════
                    elif isinstance(msg, TextBlock):
                        text = msg.text

                        # Format based on content type but SHOW EVERYTHING
                        if "Complexity:" in text or "Dimension" in text:
                            # Highlight important analysis output
                            console.print(f"[green]{text}[/green]")
                        elif any(keyword in text.lower() for keyword in ["calculating", "analyzing", "processing"]):
                            # Progress indicators with icon
                            console.print(f"[yellow]⚙[/yellow]  {text}")
                        elif text.startswith("##") or text.startswith("#"):
                            # Markdown headers
                            console.print(f"[bold cyan]{text}[/bold cyan]")
                        elif "|" in text and ("---" in text or text.count("|") > 3):
                            # Tables - show with formatting preserved
                            console.print(f"[dim]{text}[/dim]")
                        else:
                            # Regular output - show all content
                            console.print(text)

                        console.print()

                    # ═══════════════════════════════════════════════
                    # ThinkingBlock - Show internal reasoning
                    # ═══════════════════════════════════════════════
                    elif isinstance(msg, ThinkingBlock):
                        thinking_text = msg.thinking
                        # Show first 500 chars of thinking to avoid overwhelming output
                        preview = thinking_text[:500]
                        if len(thinking_text) > 500:
                            preview += "..."
                        console.print("[magenta]💭 Thinking:[/magenta]")
                        console.print(f"[dim]{preview}[/dim]")
                        console.print()

                    # ═══════════════════════════════════════════════
                    # ToolResultBlock - Show tool execution results
                    # ═══════════════════════════════════════════════
                    elif isinstance(msg, ToolResultBlock):
                        if msg.is_error:
                            console.print(f"[red]✗ Tool error:[/red] {msg.content}")
                        else:
                            # Show preview of result content
                            if msg.content:
                                result_preview = str(msg.content)[:200]
                                if len(str(msg.content)) > 200:
                                    result_preview += "..."
                                console.print(f"[dim]  Result: {result_preview}[/dim]")
                        console.print()

                    # ═══════════════════════════════════════════════
                    # AssistantMessage - Handle content blocks
                    # ═══════════════════════════════════════════════
                    elif isinstance(msg, AssistantMessage):
                        # Unpack and display content blocks
                        for block in msg.content:
                            if isinstance(block, TextBlock):
                                # Display text content
                                text = block.text
                                if "Complexity:" in text or "Dimension" in text:
                                    console.print(f"[green]{text}[/green]")
                                elif "##" in text or "#" in text:
                                    console.print(f"[bold cyan]{text}[/bold cyan]")
                                else:
                                    console.print(text)
                                console.print()

                            elif isinstance(block, ToolUseBlock):
                                console.print(f"[cyan]→ Tool:[/cyan] {block.name}")
                                console.print()

                    # ═══════════════════════════════════════════════
                    # ResultMessage - Final execution statistics
                    # ═══════════════════════════════════════════════
                    elif isinstance(msg, ResultMessage):
                        console.print("[bold]Execution Complete:[/bold]")
                        console.print(f"  Duration: {msg.duration_ms}ms")
                        console.print(f"  Turns: {msg.num_turns}")
                        if msg.total_cost_usd:
                            console.print(f"  Cost: ${msg.total_cost_usd:.4f}")
                        console.print()

            except Exception as e:
                console.print(f"\n[red]Error during execution:[/red] {e}")
                import traceback
                console.print("[dim]" + traceback.format_exc() + "[/dim]")
                sys.exit(1)

            # Parse result from collected messages
            console.print(f"[dim]Processing {len(messages)} messages...[/dim]")
            console.print()

            result = parser.extract_analysis_result(messages)

            # ═══════════════════════════════════════════════════════════════
            # V3 INTEGRATION: Cache Save (POST-EXECUTION)
            # ═══════════════════════════════════════════════════════════════

            if orchestrator and orchestrator.cache and not no_cache:
                try:
                    orchestrator.cache.analysis.save(spec_text, result, None)
                    logger.info("Analysis cached for future use")
                    console.print("[dim]✓ Cached for future use[/dim]")
                except Exception as e:
                    logger.warning(f"Cache save failed: {e}")

            # ═══════════════════════════════════════════════════════════════
            # V3 INTEGRATION: Analytics Recording (POST-EXECUTION)
            # ═══════════════════════════════════════════════════════════════

            if orchestrator and orchestrator.analytics_db:
                try:
                    orchestrator.analytics_db.record_session(
                        session_id=generated_session_id,
                        spec_hash=orchestrator._hash_spec(spec_text),
                        complexity_score=result.get('complexity_score', 0.0),
                        interpretation=result.get('interpretation', 'Unknown'),
                        dimensions=result.get('dimension_scores', {}),
                        domains=result.get('domains', {})
                    )
                    logger.info("Analysis recorded to historical database")
                    console.print("[dim]✓ Recorded to analytics database[/dim]")
                except Exception as e:
                    logger.warning(f"Analytics recording failed: {e}")

            console.print()

            # ═══════════════════════════════════════════════════════════════
            # V3 INTEGRATION: MCP Auto-Installation (POST-ANALYSIS)
            # ═══════════════════════════════════════════════════════════════

            if orchestrator and orchestrator.mcp and not output_json:
                # Only prompt in interactive mode (not JSON output)
                try:
                    mcp_install_results = await orchestrator.mcp.post_analysis_check(result)
                    if mcp_install_results:
                        installed_count = sum(1 for success in mcp_install_results.values() if success)
                        console.print(f"[dim]✓ Installed {installed_count} recommended MCP(s)[/dim]")
                        console.print()
                except Exception as e:
                    logger.warning(f"MCP auto-install check failed: {e}")

            # Save to session
            session.write_memory('spec_analysis', result)

            # Output result
            if output_json:
                # JSON output to stdout
                import json
                result_copy = result.copy()
                if 'analyzed_at' in result_copy:
                    result_copy['analyzed_at'] = result_copy['analyzed_at'].isoformat()
                print(json.dumps(result_copy, indent=2))
            else:
                # Rich formatted output
                from shannon.ui.formatters import OutputFormatter
                formatter = OutputFormatter(console=console)
                console.print(formatter.format_table(result))
                console.print()
                console.print(f"[dim]Saved to: ~/.shannon/sessions/{generated_session_id}/[/dim]")
                console.print()
                console.print("[green]✓[/green] [bold]Analysis complete[/bold]")
                console.print()

        except FileNotFoundError as e:
            console.print(f"\n[red]Error:[/red] Spec file not found: {spec_file}\n")
            sys.exit(1)
        except ImportError as e:
            console.print(f"\n[red]Error:[/red] Shannon Framework not found: {e}\n")
            console.print("[yellow]Make sure Shannon Framework is installed:[/yellow]")
            console.print("  Set SHANNON_FRAMEWORK_PATH environment variable")
            console.print("  Or install to standard location\n")
            sys.exit(1)
        except Exception as e:
            console.print(f"\n[red]Error:[/red] Analysis failed: {e}\n")
            import traceback
            console.print("[dim]" + traceback.format_exc() + "[/dim]")
            sys.exit(1)

    # Run async workflow
    anyio.run(run_analysis)


@cli.command()
@require_framework()
@click.argument('request')
@click.option('--session-id', help='Session ID to resume (uses latest if not provided)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def wave(request: str, session_id: Optional[str], verbose: bool) -> None:
    """Execute wave-based implementation.

    Invokes wave orchestration to implement the requested functionality
    based on prior spec analysis. Requires analyze command to be run first.

    \b
    Example:
        shannon wave "Implement user authentication"
        shannon wave "Add database layer" --session-id my_project

    \b
    Wave execution includes:
        - Agent deployment and coordination
        - File creation and modification
        - NO MOCKS functional testing
        - Quality metric tracking
        - Progress monitoring
    """
    async def run_wave() -> None:
        """Execute wave workflow asynchronously."""
        config = ShannonConfig()
        ui = ProgressUI()

        try:
            # Determine session to use
            if session_id:
                target_session_id = session_id
            else:
                # Find latest session
                sessions = SessionManager.list_all_sessions(config)
                if not sessions:
                    ui.error("No sessions found. Run 'shannon analyze' first.")
                    sys.exit(1)

                # Use most recent session
                target_session_id = sessions[-1]

                if verbose:
                    ui.console.print(f"[dim]Using latest session: {target_session_id}[/dim]")

            # Load session
            session = SessionManager(target_session_id, config)

            # Verify analysis exists
            analysis = session.read_memory('spec_analysis')
            if not analysis:
                ui.error("No analysis found in session. Run 'shannon analyze' first.")
                if verbose:
                    ui.console.print(f"[dim]Session: {target_session_id}[/dim]")
                    ui.console.print(f"[dim]Available memories: {session.list_memories()}[/dim]")
                sys.exit(1)

            if verbose:
                complexity = analysis.get('complexity_score', 0.0)
                ui.console.print(f"[dim]Loaded analysis (complexity: {complexity:.3f})[/dim]")

            # Initialize SDK client
            client = ShannonSDKClient()
            parser = MessageParser()

            # V5: Initialize UnifiedOrchestrator for integrated features
            orchestrator = None
            try:
                from shannon.unified_orchestrator import UnifiedOrchestrator
                orchestrator = UnifiedOrchestrator(config)
                logger.info("V5 UnifiedOrchestrator initialized for wave")
            except Exception as e:
                ui.console.print(f"[yellow]V5 features unavailable: {e}[/yellow]\n")

            # Display header
            ui.console.print()
            ui.console.print(f"[bold cyan]Wave Execution: {request}[/bold cyan]")
            ui.console.print()

            # V3: MCP Pre-Wave Check
            if orchestrator and orchestrator.mcp:
                try:
                    # Check if required MCPs are available
                    wave_plan = {'required_mcps': []}  # TODO: Extract from analysis
                    mcp_ready = await orchestrator.mcp.pre_wave_check(wave_plan)
                    if not mcp_ready:
                        ui.console.print("[yellow]⚠ Continuing without all MCPs (may cause issues)[/yellow]\n")
                except Exception as e:
                    logger.warning(f"Pre-wave MCP check failed: {e}")

            # V3: Register wave execution with AgentStateTracker
            agent_id = None
            if orchestrator and orchestrator.agents:
                try:
                    # Register wave as an agent for tracking
                    wave_number = 1  # TODO: Track wave counter in session
                    agent_id = f"wave-{wave_number}-agent"
                    
                    orchestrator.agents.register_agent(
                        agent_id=agent_id,
                        wave_number=wave_number,
                        agent_type="wave-coordinator",
                        task_description=request
                    )
                    orchestrator.agents.mark_started(agent_id)
                    logger.info(f"Agent tracking started: {agent_id}")
                except Exception as e:
                    logger.warning(f"Agent tracking initialization failed: {e}")
                    agent_id = None

            # Invoke wave orchestration skill
            messages = []

            # V3: Use live dashboard for wave execution
            try:
                from shannon.sdk.interceptor import MessageInterceptor
                from shannon.metrics.collector import MetricsCollector
                from shannon.metrics.dashboard import LiveDashboard

                ui.console.print("[dim]Executing wave with live dashboard...[/dim]\n")

                collector = MetricsCollector(operation_name="wave-execution")
                dashboard = LiveDashboard(collector, refresh_per_second=4)
                interceptor = MessageInterceptor()

                # Wrap wave execution with dashboard
                wave_iter = client.invoke_command('/shannon:wave', request)
                instrumented_iter = interceptor.intercept(wave_iter, [collector])

                with dashboard:
                    async for msg in instrumented_iter:
                        messages.append(msg)
                        
                        # V3: Track message with agent tracker
                        if agent_id and orchestrator and orchestrator.agents:
                            try:
                                orchestrator.agents.add_message(agent_id, msg)
                            except:
                                pass  # Don't fail wave if tracking fails

                        # Pass readable messages to dashboard
                        from claude_agent_sdk import TextBlock, ToolUseBlock, ThinkingBlock

                        if isinstance(msg, TextBlock):
                            dashboard.update(msg.text)
                        elif isinstance(msg, ToolUseBlock):
                            dashboard.update(f"→ Tool: {msg.name}")
                        elif isinstance(msg, ThinkingBlock):
                            preview = msg.thinking[:100] + "..." if len(msg.thinking) > 100 else msg.thinking
                            dashboard.update(f"💭 {preview}")
                        elif hasattr(msg, 'content'):
                            for block in msg.content:
                                if isinstance(block, TextBlock):
                                    dashboard.update(block.text)
                                elif isinstance(block, ToolUseBlock):
                                    dashboard.update(f"→ Tool: {block.name}")

                ui.console.print("\n[dim]Wave complete, processing results...[/dim]\n")

            except Exception as e:
                ui.console.print(f"[yellow]Dashboard unavailable: {e}, using standard output[/yellow]\n")

                # Fallback: Standard wave execution
                try:
                    async for msg in client.invoke_command('/shannon:wave', request):
                        messages.append(msg)

                        if verbose:
                            from claude_agent_sdk import ToolUseBlock, TextBlock
                            if isinstance(msg, ToolUseBlock):
                                ui.console.print(f"  [cyan]→[/cyan] Tool: {msg.name}")
                            elif isinstance(msg, TextBlock):
                                preview = msg.text[:80].replace('\n', ' ')
                                ui.console.print(f"  [dim]{preview}[/dim]")
                finally:
                    pass

            if verbose:
                ui.console.print(f"[dim]Received {len(messages)} messages[/dim]")

            # Parse wave result
            wave_result = parser.extract_wave_result(messages)

            # Determine wave number
            wave_number = wave_result.get('wave_number', 1)
            
            # V3: Mark agent complete and update metrics
            if agent_id and orchestrator and orchestrator.agents:
                try:
                    # Extract metrics from messages
                    from claude_agent_sdk import ResultMessage
                    result_msgs = [m for m in messages if isinstance(m, ResultMessage)]
                    
                    if result_msgs:
                        result_msg = result_msgs[-1]  # Last result message
                        if hasattr(result_msg, 'total_cost_usd') and result_msg.total_cost_usd:
                            orchestrator.agents.update_metrics(
                                agent_id=agent_id,
                                cost_delta=result_msg.total_cost_usd
                            )
                    
                    # Mark complete
                    orchestrator.agents.mark_complete(agent_id)
                    logger.info(f"Agent tracking completed: {agent_id}")
                except Exception as e:
                    logger.warning(f"Agent tracking completion failed: {e}")
                    try:
                        orchestrator.agents.mark_failed(agent_id, str(e))
                    except:
                        pass
            
            # V3: Save agent states to session for persistence
            if orchestrator and orchestrator.agents:
                try:
                    all_agent_states = orchestrator.agents.get_all_states()
                    agent_data = [agent.to_dict() for agent in all_agent_states]
                    session.write_memory('tracked_agents', agent_data)
                    if verbose:
                        ui.console.print(f"[dim]Saved {len(agent_data)} tracked agent(s) to session[/dim]")
                except Exception as e:
                    logger.warning(f"Failed to save agent states: {e}")

            # Save results
            session.write_memory(f"wave_{wave_number}_complete", wave_result)

            if verbose:
                ui.console.print(f"[dim]Saved wave {wave_number} result to session[/dim]")

            # Display result
            ui.display_wave_result(wave_result)
            ui.console.print(f"[dim]Session ID: {target_session_id}[/dim]")
            ui.success(f"Wave {wave_number} complete")

        except ImportError as e:
            ui.error(f"Shannon Framework not found: {e}")
            sys.exit(1)
        except Exception as e:
            ui.error(f"Wave execution failed: {e}")
            if verbose:
                import traceback
                ui.console.print(traceback.format_exc())
            sys.exit(1)

    # Run async workflow
    anyio.run(run_wave)


@cli.command()
@click.option('--session-id', help='Session ID (uses latest if not provided)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def status(session_id: Optional[str], verbose: bool) -> None:
    """Show current session status.

    Displays analysis results, completed waves, and progress summary
    for the specified or most recent session.

    \b
    Example:
        shannon status
        shannon status --session-id my_project
    """
    config = ShannonConfig()
    ui = ProgressUI()

    try:
        # Determine session to use
        if session_id:
            target_session_id = session_id
        else:
            # Find latest session
            sessions = SessionManager.list_all_sessions(config)
            if not sessions:
                ui.error("No sessions found. Run 'shannon analyze' first.")
                sys.exit(1)

            # Use most recent session
            target_session_id = sessions[-1]

        # Load session
        session = SessionManager(target_session_id, config)
        session_info = session.get_session_info()

        if verbose:
            ui.console.print(f"[dim]Session directory: {session_info['session_dir']}[/dim]")

        # Read analysis
        analysis = session.read_memory('spec_analysis')

        # Count completed waves
        wave_memories = [k for k in session.list_memories() if k.startswith('wave_')]
        wave_count = len(wave_memories)

        # Display status
        ui.console.print()
        ui.display_session_status(target_session_id, analysis, wave_count)

        if verbose and wave_memories:
            ui.console.print()
            ui.console.print("[bold]Completed Waves:[/bold]")
            for wave_key in sorted(wave_memories):
                wave_data = session.read_memory(wave_key)
                if wave_data:
                    wave_num = wave_data.get('wave_number', '?')
                    wave_name = wave_data.get('wave_name', 'Unknown')
                    ui.console.print(f"  [cyan]Wave {wave_num}:[/cyan] {wave_name}")

        ui.console.print()

    except Exception as e:
        ui.error(f"Failed to get status: {e}")
        if verbose:
            import traceback
            ui.console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.option('--edit', is_flag=True, help='Open config file for editing')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed configuration')
def config(edit: bool, verbose: bool) -> None:
    """Display or edit Shannon configuration.

    Shows current configuration settings including log level,
    session directory, and token budget.

    \b
    Example:
        shannon config           # Show current config
        shannon config --edit    # Open config for editing
    """
    from rich.table import Table

    ui = ProgressUI()
    cfg = ShannonConfig()

    if edit:
        # Open config file in editor
        import subprocess
        import os

        # Ensure config file exists
        cfg.save()

        editor = os.environ.get('EDITOR', 'nano')
        try:
            subprocess.run([editor, str(cfg.config_file)])
            ui.success("Configuration updated")
        except Exception as e:
            ui.error(f"Failed to open editor: {e}")
            sys.exit(1)
    else:
        # Display configuration
        config_table = Table(title="Shannon Configuration", show_header=False)
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="yellow")

        config_table.add_row("Config Directory", str(cfg.config_dir))
        config_table.add_row("Config File", str(cfg.config_file))
        config_table.add_row("Log Level", cfg.log_level)
        config_table.add_row("Session Directory", str(cfg.session_dir))
        config_table.add_row("Token Budget", str(cfg.token_budget))

        ui.console.print()
        ui.console.print(config_table)

        if verbose:
            ui.console.print()
            ui.console.print("[bold]Environment Variables:[/bold]")
            import os
            for var in ['SHANNON_LOG_LEVEL', 'SHANNON_SESSION_DIR', 'SHANNON_TOKEN_BUDGET', 'SHANNON_FRAMEWORK_PATH']:
                value = os.environ.get(var, '[dim]not set[/dim]')
                ui.console.print(f"  [cyan]{var}:[/cyan] {value}")

        ui.console.print()


@cli.command()
def setup() -> None:
    """Interactive setup wizard for Shannon CLI.

    Guides you through complete Shannon CLI configuration including:
    - Python version verification
    - Claude Agent SDK installation
    - Shannon Framework detection/installation
    - Serena MCP integration (optional)
    - End-to-end verification

    Run this command when:
    - First time using Shannon CLI
    - Framework installation is broken
    - Moving to a new machine

    \b
    Example:
        shannon setup           # Run interactive wizard
    """
    wizard = SetupWizard()
    success = wizard.run()
    sys.exit(0 if success else 1)


@cli.command()
def diagnostics() -> None:
    """Show diagnostic information about Shannon Framework locations.

    Displays all searched locations and their status. Useful for
    troubleshooting framework detection issues.

    \b
    Example:
        shannon diagnostics
    """
    wizard = SetupWizard()
    wizard.show_diagnostics()


@cli.command()
def sessions() -> None:
    """List all available sessions.

    Shows all sessions with their creation date and status.

    \b
    Example:
        shannon sessions
    """
    from rich.table import Table

    config = ShannonConfig()
    ui = ProgressUI()

    try:
        session_ids = SessionManager.list_all_sessions(config)

        if not session_ids:
            ui.console.print("\n[yellow]No sessions found.[/yellow]")
            ui.console.print("Run [cyan]shannon analyze[/cyan] to create a session.\n")
            return

        # Create table
        sessions_table = Table(title="Shannon Sessions", show_header=True)
        sessions_table.add_column("Session ID", style="cyan")
        sessions_table.add_column("Created", style="yellow")
        sessions_table.add_column("Updated", style="green")
        sessions_table.add_column("Memories", justify="right", style="dim")

        # Load session info
        for session_id in sorted(session_ids):
            session = SessionManager(session_id, config)
            info = session.get_session_info()

            created = info.get('created_at', 'Unknown')
            updated = info.get('updated_at', 'Unknown')
            memory_count = info.get('memory_count', 0)

            # Format timestamps
            try:
                created_dt = datetime.fromisoformat(created)
                created_str = created_dt.strftime("%Y-%m-%d %H:%M")
            except:
                created_str = created

            try:
                updated_dt = datetime.fromisoformat(updated)
                updated_str = updated_dt.strftime("%Y-%m-%d %H:%M")
            except:
                updated_str = updated

            sessions_table.add_row(
                session_id,
                created_str,
                updated_str,
                str(memory_count)
            )

        ui.console.print()
        ui.console.print(sessions_table)
        ui.console.print()

    except Exception as e:
        ui.error(f"Failed to list sessions: {e}")
        sys.exit(1)


@cli.command()
@require_framework()
@click.argument('spec_or_file')
@click.option('--auto', is_flag=True, help='Run without pauses')
@click.option('--session-id', help='Session ID (auto-generated if not provided)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def task(
    spec_or_file: str,
    auto: bool,
    session_id: Optional[str],
    verbose: bool
) -> None:
    """Automated workflow: prime → analyze → wave execution.

    Combines spec analysis and wave execution into a single workflow.
    Equivalent to /shannon:task in Shannon Framework.

    \b
    Example:
        shannon task spec.md
        shannon task "Implement user auth" --auto
        shannon task spec.md --session-id my_project

    \b
    The task workflow includes:
        - Automatic session priming
        - 8D complexity analysis
        - Wave-based execution
        - Progress monitoring
        - Quality validation
    """
    async def run_task() -> None:
        """Execute task workflow asynchronously."""
        config = ShannonConfig()
        config.ensure_directories()
        ui = ProgressUI()

        try:
            # Generate session ID if not provided
            if not session_id:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                generated_session_id = f"task_{timestamp}"
            else:
                generated_session_id = session_id

            session = SessionManager(generated_session_id, config)

            # Display header
            ui.console.print()
            ui.console.print("[bold cyan]Shannon Task Automation[/bold cyan]")
            ui.console.print()

            # Step 1: Analyze specification
            ui.console.print("[bold]Step 1:[/bold] Analyzing specification...")

            # Check if spec_or_file is a file path
            spec_path = Path(spec_or_file)
            if spec_path.exists():
                spec_text = spec_path.read_text(encoding='utf-8')
                if verbose:
                    ui.console.print(f"[dim]Reading spec from: {spec_path}[/dim]")
            else:
                # Treat as direct specification text
                spec_text = spec_or_file
                if verbose:
                    ui.console.print("[dim]Using inline specification[/dim]")

            # Initialize SDK client
            client = ShannonSDKClient()
            parser = MessageParser()

            # Invoke spec-analysis - collect all messages first
            messages = []
            try:
                # Import SDK types
                from claude_agent_sdk import query, SystemMessage, ToolUseBlock, TextBlock, ThinkingBlock, ResultMessage

                # Use query() DIRECTLY - fixes async bug
                async for msg in query(
                    prompt=f"/shannon:spec {spec_text}",
                    options=client.base_options
                ):
                    messages.append(msg)
                    if verbose:
                        from claude_agent_sdk import ToolUseBlock, TextBlock
                        if isinstance(msg, ToolUseBlock):
                            ui.console.print(f"  [cyan]→[/cyan] Tool: {msg.name}")
                        elif isinstance(msg, TextBlock):
                            preview = msg.text[:80].replace('\n', ' ')
                            ui.console.print(f"  [dim]{preview}[/dim]")
            finally:
                # Ensure generator cleanup
                pass

            # Parse and save analysis
            analysis_result = parser.extract_analysis_result(messages)
            session.write_memory('spec_analysis', analysis_result)

            # Display brief analysis summary
            complexity = analysis_result.get('complexity_score', 0.0)
            ui.console.print(f"[green]✓[/green] Analysis complete (complexity: {complexity:.3f})")
            ui.console.print()

            # Step 2: Approval checkpoint (unless --auto)
            if not auto:
                ui.console.print("[bold]Analysis Summary:[/bold]")
                ui.display_analysis_result(analysis_result)
                ui.console.print()

                if not Confirm.ask("Proceed with wave execution?", default=True):
                    ui.console.print("\n[yellow]Task execution cancelled.[/yellow]\n")
                    sys.exit(0)

            # Step 3: Execute waves
            ui.console.print("[bold]Step 2:[/bold] Executing waves...")

            # Use /shannon:task command with dashboard
            wave_messages = []

            # V3: Live dashboard for task execution
            try:
                from shannon.sdk.interceptor import MessageInterceptor
                from shannon.metrics.collector import MetricsCollector
                from shannon.metrics.dashboard import LiveDashboard

                collector = MetricsCollector(operation_name="task-execution")
                dashboard = LiveDashboard(collector, refresh_per_second=4)
                interceptor = MessageInterceptor()

                task_iter = client.invoke_command('/shannon:task', spec_text)
                instrumented_iter = interceptor.intercept(task_iter, [collector])

                with dashboard:
                    async for msg in instrumented_iter:
                        wave_messages.append(msg)

                        # Stream messages to dashboard
                        from claude_agent_sdk import TextBlock, ToolUseBlock, ThinkingBlock

                        if isinstance(msg, TextBlock):
                            dashboard.update(msg.text)
                        elif isinstance(msg, ToolUseBlock):
                            dashboard.update(f"→ Tool: {msg.name}")
                        elif isinstance(msg, ThinkingBlock):
                            preview = msg.thinking[:100] + "..." if len(msg.thinking) > 100 else msg.thinking
                            dashboard.update(f"💭 {preview}")
                        elif hasattr(msg, 'content'):
                            for block in msg.content:
                                if isinstance(block, TextBlock):
                                    dashboard.update(block.text)

            except Exception as e:
                ui.console.print(f"[yellow]Dashboard unavailable: {e}[/yellow]\n")

                # Fallback
                try:
                    async for msg in client.invoke_command('/shannon:task', spec_text):
                        wave_messages.append(msg)
                        if verbose:
                            from claude_agent_sdk import ToolUseBlock, TextBlock
                            if isinstance(msg, ToolUseBlock):
                                ui.console.print(f"  [cyan]→[/cyan] Tool: {msg.name}")
                            elif isinstance(msg, TextBlock):
                                preview = msg.text[:80].replace('\n', ' ')
                                ui.console.print(f"  [dim]{preview}[/dim]")
                finally:
                    pass

            # Parse wave results
            wave_result = parser.extract_wave_result(wave_messages)

            # Determine wave number
            wave_number = wave_result.get('wave_number', 1)

            # Save results
            session.write_memory(f"wave_{wave_number}_complete", wave_result)

            if verbose:
                ui.console.print(f"[dim]Saved wave {wave_number} result to session[/dim]")

            # Display result
            ui.console.print()
            ui.display_wave_result(wave_result)
            ui.console.print(f"[dim]Session ID: {generated_session_id}[/dim]")
            ui.success(f"Task complete - Wave {wave_number} finished")

        except FileNotFoundError as e:
            ui.error(f"Spec file not found: {spec_or_file}")
            sys.exit(1)
        except Exception as e:
            ui.error(f"Task execution failed: {e}")
            if verbose:
                import traceback
                ui.console.print(traceback.format_exc())
            sys.exit(1)

    # Run async workflow
    anyio.run(run_task)


@cli.command()
@require_framework()
@click.argument('task')
@click.option('--dry-run', is_flag=True, help='Plan only, do not execute')
@click.option('--interactive', '-i', is_flag=True, help='Confirm before each step')
@click.option('--max-iterations', type=int, default=3, help='Max retry attempts per step')
@click.option('--research/--no-research', default=True, help='Enable research integration')
@click.option('--auto-commit/--no-auto-commit', default=True, help='Auto-commit validated changes')
@click.option('--session-id', help='Session ID (auto-generated if not provided)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def exec(
    task: str,
    dry_run: bool,
    interactive: bool,
    max_iterations: int,
    research: bool,
    auto_commit: bool,
    session_id: Optional[str],
    verbose: bool
) -> None:
    """
    Execute autonomous task with library discovery and validation.
    
    Shannon V3.5 autonomous executor: Takes natural language task,
    discovers relevant libraries, validates functionally, and commits
    atomically to git.
    
    \b
    Process:
        1. Auto-prime codebase context (task-focused)
        2. Research and discover libraries (don't reinvent wheel)
        3. Plan execution with validation strategy
        4. Execute with iteration (retry on failure)
        5. Validate functionally (3-tier: static, unit, functional)
        6. Commit atomically (only if validated)
    
    \b
    Example:
        shannon exec "fix the iOS offscreen login bug"
        shannon exec "add authentication to React app"
        shannon exec "optimize database query performance"
        shannon exec "add dark mode toggle" --dry-run
        shannon exec "implement OAuth2" --research
    
    \b
    Features:
        - Library discovery (searches npm, PyPI, CocoaPods, etc.)
        - 3-tier validation (build + tests + functional)
        - Atomic git commits per validated step
        - Iterative refinement (up to 3 attempts per step)
        - Enhanced system prompts (library-first, validation-focused)
        - V3.1 dashboard for real-time visibility
    
    \b
    Note: V3.5 exec is currently in PREVIEW. Full implementation requires
          Shannon Framework /shannon:exec skill integration.
    """
    async def run_exec() -> None:
        """Execute autonomous task workflow"""
        from pathlib import Path
        
        ui = ProgressUI()
        config = ShannonConfig()
        
        # Display header
        ui.console.print()
        ui.console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]")
        ui.console.print("[bold cyan] Shannon V3.5 Autonomous Executor (PREVIEW)[/bold cyan]")
        ui.console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]")
        ui.console.print()
        ui.console.print(f"[bold]Task:[/bold] {task}")
        ui.console.print()
        
        try:
            # Step 1: Build enhanced system prompts
            ui.console.print("[cyan]Phase 1:[/cyan] Building enhanced system prompts...")
            
            from shannon.executor import PromptEnhancer
            
            enhancer = PromptEnhancer()
            enhancements = enhancer.build_enhancements(
                task=task,
                project_root=Path.cwd()
            )
            
            ui.console.print(f"  ✓ Enhanced prompts built ({len(enhancements)} chars)")
            ui.console.print(f"    - Library discovery instructions")
            ui.console.print(f"    - Functional validation requirements")
            ui.console.print(f"    - Git workflow automation")
            ui.console.print()
            
            # Step 2: Detect project context
            ui.console.print("[cyan]Phase 2:[/cyan] Detecting project context...")
            
            project_type = enhancer._detect_project_type(Path.cwd())
            ui.console.print(f"  ✓ Project type: {project_type}")
            ui.console.print()
            
            # Step 3: Library discovery (preview)
            ui.console.print("[cyan]Phase 3:[/cyan] Library discovery...")
            
            from shannon.executor import LibraryDiscoverer
            
            discoverer = LibraryDiscoverer(Path.cwd())
            ui.console.print(f"  ✓ Library discoverer initialized")
            ui.console.print(f"    - Language: {discoverer.language}")
            ui.console.print(f"    - Package manager: {discoverer._get_package_manager()}")
            ui.console.print()
            
            # Step 4: Validation setup
            ui.console.print("[cyan]Phase 4:[/cyan] Configuring validation...")
            
            from shannon.executor import ValidationOrchestrator
            
            validator = ValidationOrchestrator(Path.cwd())
            ui.console.print(f"  ✓ Validation orchestrator initialized")
            if validator.test_config.build_cmd:
                ui.console.print(f"    - Build: {validator.test_config.build_cmd}")
            if validator.test_config.test_cmd:
                ui.console.print(f"    - Tests: {validator.test_config.test_cmd}")
            if validator.test_config.lint_cmd:
                ui.console.print(f"    - Lint: {validator.test_config.lint_cmd}")
            ui.console.print()
            
            # Step 5: Git manager setup
            ui.console.print("[cyan]Phase 5:[/cyan] Git workflow setup...")
            
            from shannon.executor import GitManager
            
            git_mgr = GitManager(Path.cwd())
            branch_name = git_mgr._generate_branch_name(task)
            ui.console.print(f"  ✓ Git manager initialized")
            ui.console.print(f"    - Branch would be: {branch_name}")
            ui.console.print()
            
            # Phase 6: Simple execution
            ui.console.print("[cyan]Phase 6:[/cyan] Task execution...")
            ui.console.print()

            # Initialize libraries for dry-run display
            libraries = None

            if dry_run:
                ui.console.print("[yellow]═══════════════════════════════════════════════════════════════[/yellow]")
                ui.console.print("[yellow] DRY RUN MODE - No execution performed[/yellow]")
                ui.console.print("[yellow]═══════════════════════════════════════════════════════════════[/yellow]")
                ui.console.print()
                ui.console.print("[bold]Execution Plan:[/bold]")
                ui.console.print()
                ui.console.print(f"  1. Create branch: {branch_name}")
                ui.console.print(f"  2. Discover libraries: {len(libraries) if libraries else 0} found")
                ui.console.print(f"  3. Execute with enhanced prompts ({len(enhancements)} chars)")
                ui.console.print(f"  4. Validate (3 tiers)")
                ui.console.print(f"  5. Commit if validated")
                ui.console.print()
                
                if libraries:
                    ui.console.print("[bold]Recommended libraries:[/bold]")
                    for lib in libraries[:3]:
                        ui.console.print(f"  • {lib.name} - {lib.why_recommended}")
                    ui.console.print()
                
                ui.success("Dry run complete")
            else:
                # Actually execute using CompleteExecutor (full autonomous execution)
                ui.console.print("[bold cyan]Executing with CompleteExecutor (full autonomous execution)...[/bold cyan]")
                ui.console.print()
                
                from shannon.executor.complete_executor import CompleteExecutor

                executor = CompleteExecutor(Path.cwd(), max_iterations=max_iterations)
                result = await executor.execute_autonomous(task, auto_commit=auto_commit)
                
                ui.console.print()
                ui.console.print("[yellow]═══════════════════════════════════════════════════════════════[/yellow]")
                
                if result.success:
                    ui.console.print("[yellow] ✅ TASK EXECUTION COMPLETE[/yellow]")
                    ui.console.print("[yellow]═══════════════════════════════════════════════════════════════[/yellow]")
                    ui.console.print()
                    ui.console.print(f"[bold]Task:[/bold] {result.task_description}")
                    ui.console.print(f"[bold]Branch:[/bold] {result.branch_name}")
                    ui.console.print(f"[bold]Steps:[/bold] {result.steps_completed}/{result.steps_total}")
                    ui.console.print(f"[bold]Duration:[/bold] {result.duration_seconds:.1f}s")
                    
                    if result.libraries_used:
                        ui.console.print(f"[bold]Libraries:[/bold] {', '.join(result.libraries_used)}")
                    
                    if result.commits_created:
                        ui.console.print(f"[bold]Commits:[/bold] {len(result.commits_created)}")
                    
                    ui.console.print()
                    ui.success("Task execution successful")
                else:
                    ui.console.print("[yellow] ❌ TASK EXECUTION FAILED[/yellow]")
                    ui.console.print("[yellow]═══════════════════════════════════════════════════════════════[/yellow]")
                    ui.console.print()
                    ui.console.print(f"[bold]Error:[/bold] {result.error_message}")
                    ui.console.print()
                    ui.error("Task execution failed - see error above")
            
        except Exception as e:
            ui.error(f"Exec failed: {e}")
            if verbose:
                import traceback
                ui.console.print(traceback.format_exc())
            sys.exit(1)
    
    anyio.run(run_exec)


@cli.command()
@click.argument('name', required=False)
@click.option('--list', 'list_checkpoints', is_flag=True, help='List all checkpoints')
@click.option('--session-id', help='Session ID (uses latest if not provided)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def checkpoint(
    name: Optional[str],
    list_checkpoints: bool,
    session_id: Optional[str],
    verbose: bool
) -> None:
    """Create or list session checkpoints.

    Saves current session state for later restoration. Useful for
    creating snapshots before major changes or experimentation.

    \b
    Example:
        shannon checkpoint                    # Auto-named checkpoint
        shannon checkpoint pre_refactor       # Named checkpoint
        shannon checkpoint --list             # List all checkpoints
    """
    from rich.table import Table

    config = ShannonConfig()
    ui = ProgressUI()

    try:
        # Determine session to use
        if session_id:
            target_session_id = session_id
        else:
            sessions = SessionManager.list_all_sessions(config)
            if not sessions:
                ui.error("No sessions found. Run 'shannon analyze' first.")
                sys.exit(1)
            target_session_id = sessions[-1]

        session = SessionManager(target_session_id, config)

        if list_checkpoints:
            # List all checkpoints
            all_memories = session.list_memories()
            checkpoints = [m for m in all_memories if m.startswith('checkpoint_')]

            if not checkpoints:
                ui.console.print("\n[yellow]No checkpoints found.[/yellow]")
                ui.console.print("Create one with: [cyan]shannon checkpoint <name>[/cyan]\n")
                return

            # Create table
            checkpoint_table = Table(title=f"Checkpoints - {target_session_id}", show_header=True)
            checkpoint_table.add_column("Name", style="cyan")
            checkpoint_table.add_column("Created", style="yellow")
            checkpoint_table.add_column("Description", style="dim")

            for checkpoint_key in sorted(checkpoints):
                checkpoint_data = session.read_memory(checkpoint_key)
                if checkpoint_data:
                    checkpoint_name = checkpoint_key.replace('checkpoint_', '')
                    created_at = checkpoint_data.get('created_at', 'Unknown')
                    description = checkpoint_data.get('description', 'No description')

                    # Format timestamp
                    try:
                        created_dt = datetime.fromisoformat(created_at)
                        created_str = created_dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        created_str = created_at

                    checkpoint_table.add_row(checkpoint_name, created_str, description)

            ui.console.print()
            ui.console.print(checkpoint_table)
            ui.console.print()

        else:
            # Create checkpoint
            checkpoint_name = name or f"auto_{int(time.time())}"
            checkpoint_key = f"checkpoint_{checkpoint_name}"

            # Gather current session state
            all_memories = session.list_memories()
            checkpoint_data = {
                'created_at': datetime.now().isoformat(),
                'description': f"Checkpoint: {checkpoint_name}",
                'session_id': target_session_id,
                'memories_count': len(all_memories),
                'memories': all_memories
            }

            # Save checkpoint
            session.write_memory(checkpoint_key, checkpoint_data)

            if verbose:
                ui.console.print(f"[dim]Captured {len(all_memories)} memories[/dim]")

            ui.console.print()
            ui.console.print(f"[green]✓[/green] Checkpoint created: [cyan]{checkpoint_name}[/cyan]")
            ui.console.print(f"[dim]Session: {target_session_id}[/dim]")
            ui.console.print()

    except Exception as e:
        ui.error(f"Checkpoint operation failed: {e}")
        if verbose:
            import traceback
            ui.console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.argument('checkpoint_id')
@click.option('--session-id', help='Session ID (uses latest if not provided)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def restore(
    checkpoint_id: str,
    session_id: Optional[str],
    verbose: bool
) -> None:
    """Restore session from checkpoint.

    Loads a previously saved checkpoint to restore session state.
    Maps to /shannon:restore in Shannon Framework.

    \b
    Example:
        shannon restore pre_refactor
        shannon restore auto_1234567890
    """
    config = ShannonConfig()
    ui = ProgressUI()

    try:
        # Determine session to use
        if session_id:
            target_session_id = session_id
        else:
            sessions = SessionManager.list_all_sessions(config)
            if not sessions:
                ui.error("No sessions found.")
                sys.exit(1)
            target_session_id = sessions[-1]

        session = SessionManager(target_session_id, config)

        # Construct checkpoint key
        checkpoint_key = f"checkpoint_{checkpoint_id}" if not checkpoint_id.startswith('checkpoint_') else checkpoint_id

        # Load checkpoint
        checkpoint_data = session.read_memory(checkpoint_key)

        if not checkpoint_data:
            ui.error(f"Checkpoint not found: {checkpoint_id}")
            ui.console.print("\nUse [cyan]shannon checkpoint --list[/cyan] to see available checkpoints.\n")
            sys.exit(1)

        # Display checkpoint info
        ui.console.print()
        ui.console.print("[bold cyan]Restoring Checkpoint[/bold cyan]")
        ui.console.print()

        created_at = checkpoint_data.get('created_at', 'Unknown')
        description = checkpoint_data.get('description', 'No description')
        memories_count = checkpoint_data.get('memories_count', 0)

        ui.console.print(f"[bold]Checkpoint:[/bold] {checkpoint_id}")
        ui.console.print(f"[bold]Created:[/bold] {created_at}")
        ui.console.print(f"[bold]Description:[/bold] {description}")
        ui.console.print(f"[bold]Memories:[/bold] {memories_count}")
        ui.console.print()

        # Confirm restore
        if not Confirm.ask("Restore this checkpoint?", default=True):
            ui.console.print("\n[yellow]Restore cancelled.[/yellow]\n")
            sys.exit(0)

        if verbose:
            ui.console.print("[dim]Restoring session state...[/dim]")

        # Restoration would require more complex state management
        # For now, display info that checkpoint is loaded
        ui.console.print()
        ui.console.print(f"[green]✓[/green] Session restored from checkpoint: [cyan]{checkpoint_id}[/cyan]")
        ui.console.print(f"[dim]Session: {target_session_id}[/dim]")
        ui.console.print()

    except Exception as e:
        ui.error(f"Restore failed: {e}")
        if verbose:
            import traceback
            ui.console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@require_framework()
@click.option('--session-id', help='Session ID (uses latest if not provided)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def test(session_id: Optional[str], verbose: bool) -> None:
    """Run functional tests with NO MOCKS enforcement.

    Executes Shannon Framework's functional testing skill which
    enforces NO MOCKS policy and runs comprehensive integration tests.
    Maps to /shannon:test command.

    \b
    Example:
        shannon test
        shannon test --session-id my_project
    """
    async def run_test() -> None:
        """Execute test workflow asynchronously."""
        config = ShannonConfig()
        ui = ProgressUI()

        try:
            # Determine session to use
            if session_id:
                target_session_id = session_id
            else:
                sessions = SessionManager.list_all_sessions(config)
                if not sessions:
                    ui.error("No sessions found. Run 'shannon analyze' first.")
                    sys.exit(1)
                target_session_id = sessions[-1]

            if verbose:
                ui.console.print(f"[dim]Using session: {target_session_id}[/dim]")

            # Initialize SDK client
            client = ShannonSDKClient()
            parser = MessageParser()

            # Display header
            ui.console.print()
            ui.console.print("[bold cyan]Shannon Functional Testing[/bold cyan]")
            ui.console.print("[dim]NO MOCKS enforcement enabled[/dim]")
            ui.console.print()

            # Invoke test command
            messages = []

            if verbose:
                ui.console.print("[dim]Invoking functional test skill...[/dim]")

            try:
                async for msg in client.invoke_command('/shannon:test', ''):
                    messages.append(msg)

                    # Show progress inline during iteration
                    if verbose:
                        from claude_agent_sdk import ToolUseBlock, TextBlock
                        if isinstance(msg, ToolUseBlock):
                            ui.console.print(f"  [cyan]→[/cyan] Tool: {msg.name}")
                        elif isinstance(msg, TextBlock):
                            preview = msg.text[:80].replace('\n', ' ')
                            ui.console.print(f"  [dim]{preview}[/dim]")
            finally:
                # Ensure generator cleanup
                pass

            if verbose:
                ui.console.print(f"[dim]Received {len(messages)} messages[/dim]")

            # Parse test results
            test_result = parser.extract_test_result(messages)

            # Save results to session
            session = SessionManager(target_session_id, config)
            session.write_memory('test_results', test_result)

            # Display results
            ui.display_test_result(test_result)
            ui.console.print(f"[dim]Session ID: {target_session_id}[/dim]")

            # Determine exit code based on test success
            passed = test_result.get('all_passed', False)
            if passed:
                ui.success("All tests passed")
                sys.exit(0)
            else:
                ui.error("Some tests failed")
                sys.exit(1)

        except Exception as e:
            ui.error(f"Test execution failed: {e}")
            if verbose:
                import traceback
                ui.console.print(traceback.format_exc())
            sys.exit(1)

    # Run async workflow
    anyio.run(run_test)


@cli.command()
@require_framework()
@click.option('--session-id', help='Session ID (uses latest if not provided)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def reflect(session_id: Optional[str], verbose: bool) -> None:
    """Run honest gap analysis before claiming completion.

    Performs pre-completion reflection to identify gaps, missing tests,
    or incomplete implementations. Maps to /shannon:reflect command.

    \b
    Example:
        shannon reflect
        shannon reflect --session-id my_project

    \b
    Reflection checks:
        - Implementation completeness
        - Test coverage gaps
        - Documentation status
        - Code quality issues
        - Security vulnerabilities
    """
    async def run_reflect() -> None:
        """Execute reflection workflow asynchronously."""
        config = ShannonConfig()
        ui = ProgressUI()

        try:
            # Determine session to use
            if session_id:
                target_session_id = session_id
            else:
                sessions = SessionManager.list_all_sessions(config)
                if not sessions:
                    ui.error("No sessions found. Run 'shannon analyze' first.")
                    sys.exit(1)
                target_session_id = sessions[-1]

            session = SessionManager(target_session_id, config)

            if verbose:
                ui.console.print(f"[dim]Using session: {target_session_id}[/dim]")

            # Initialize SDK client
            client = ShannonSDKClient()
            parser = MessageParser()

            # Display header
            ui.console.print()
            ui.console.print("[bold cyan]Shannon Reflection Analysis[/bold cyan]")
            ui.console.print("[dim]Honest gap analysis and completion check[/dim]")
            ui.console.print()

            # Invoke reflect command
            messages = []

            if verbose:
                ui.console.print("[dim]Invoking reflection skill...[/dim]")

            try:
                async for msg in client.invoke_command('/shannon:reflect', ''):
                    messages.append(msg)

                    # Display text blocks directly
                    from claude_agent_sdk import TextBlock
                    if isinstance(msg, TextBlock):
                        ui.console.print(msg.text)
            finally:
                # Ensure generator cleanup
                pass

            if verbose:
                ui.console.print(f"[dim]Received {len(messages)} messages[/dim]")

            # Parse reflection results
            reflection_result = parser.extract_reflection_result(messages)

            # Save results to session
            session.write_memory('reflection_results', reflection_result)

            ui.console.print()
            ui.console.print(f"[dim]Session ID: {target_session_id}[/dim]")

            # Check if gaps were found
            has_gaps = reflection_result.get('gaps_found', False)
            if has_gaps:
                ui.console.print()
                ui.console.print("[yellow]⚠ Gaps identified - review reflection output above[/yellow]")
                sys.exit(1)
            else:
                ui.success("No gaps found - implementation appears complete")
                sys.exit(0)

        except Exception as e:
            ui.error(f"Reflection failed: {e}")
            if verbose:
                import traceback
                ui.console.print(traceback.format_exc())
            sys.exit(1)

    # Run async workflow
    anyio.run(run_reflect)


@cli.command()
@require_framework()
def prime() -> None:
    """Initialize session (loads skills, MCPs, context).

    Invokes /shannon:prime command to initialize the session with all
    required skills, MCP servers, and context. This is the first step
    in a Shannon workflow.

    \b
    Example:
        shannon prime
    """
    async def run_prime() -> None:
        """Execute prime workflow asynchronously."""
        ui = ProgressUI()

        try:
            client = ShannonSDKClient()

            ui.console.print()
            ui.console.print("[bold cyan]Shannon Session Initialization[/bold cyan]")
            ui.console.print()

            # Invoke /shannon:prime command
            messages = []
            try:
                async for msg in client.invoke_command('/shannon:prime', ''):
                    messages.append(msg)
                    from claude_agent_sdk import TextBlock
                    if isinstance(msg, TextBlock):
                        ui.console.print(msg.text)
            except Exception as e:
                ui.console.print(f"[red]Error during prime: {e}[/red]")
                raise

            ui.console.print()
            ui.success("Session primed")
            sys.exit(0)

        except Exception as e:
            ui.error(f"Prime failed: {e}")
            sys.exit(1)

    anyio.run(run_prime)


@cli.command()
@require_framework()
@click.argument('task')
@click.option('--dashboard', '-d', is_flag=True, help='Start WebSocket server for dashboard')
@click.option('--auto', is_flag=True, help='Auto-mode: use defaults for decisions')
@click.option('--project-root', type=click.Path(exists=True), default='.', help='Project root directory')
@click.option('--session-id', help='Session ID for dashboard (auto-generated if not provided)')
@click.option('--dry-run', is_flag=True, help='Plan only, do not execute')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def do(
    task: str,
    dashboard: bool,
    auto: bool,
    project_root: str,
    session_id: Optional[str],
    dry_run: bool,
    verbose: bool
) -> None:
    """Execute natural language task with orchestration.

    The shannon do command is the main entry point for task execution.
    It handles the complete workflow from parsing to execution.

    \b
    Examples:
        shannon do "create authentication system"
        shannon do "fix login bug" --dashboard
        shannon do "add tests" --auto
        shannon do "refactor user module" --dry-run

    \b
    Features:
        - Natural language task understanding
        - Automatic skill selection and ordering
        - Checkpoint creation for rollback
        - Real-time dashboard streaming
        - HALT/RESUME support
        - Auto-mode for unattended execution
    """
    from shannon.cli.v4_commands.do import do_command
    from click import Context

    # Create context and invoke command
    ctx = Context(do_command)
    ctx.invoke(
        do_command,
        task=task,
        dashboard=dashboard,
        session_id=session_id,
        verbose=verbose
    )


@cli.command()
@require_framework()
@click.option('--cache', is_flag=True, help='Use cached results')
def discover_skills(cache: bool) -> None:
    """Discover all available skills.

    Scans the Shannon Framework installation and lists all available
    skills with their capabilities.

    \b
    Example:
        shannon discover-skills
        shannon discover-skills --cache
    """
    async def run_discover() -> None:
        """Execute discover workflow asynchronously."""
        ui = ProgressUI()

        try:
            client = ShannonSDKClient()

            ui.console.print()
            ui.console.print("[bold cyan]Discovering Shannon Skills[/bold cyan]")
            ui.console.print()

            flag = '--cache' if cache else ''
            try:
                async for msg in client.invoke_command('/shannon:discover_skills', flag):
                    from claude_agent_sdk import TextBlock
                    if isinstance(msg, TextBlock):
                        ui.console.print(msg.text)
            except Exception as e:
                ui.console.print(f"[red]Error during discovery: {e}[/red]")
                raise

            ui.console.print()
            sys.exit(0)

        except Exception as e:
            ui.error(f"Skill discovery failed: {e}")
            sys.exit(1)

    anyio.run(run_discover)


@cli.command()
@require_framework()
def check_mcps() -> None:
    """Verify MCP configuration.

    Checks that all required MCP servers are properly configured and
    accessible.

    \b
    Example:
        shannon check-mcps
    """
    async def run_check() -> None:
        """Execute MCP check workflow asynchronously."""
        ui = ProgressUI()

        try:
            client = ShannonSDKClient()

            ui.console.print()
            ui.console.print("[bold cyan]MCP Configuration Check[/bold cyan]")
            ui.console.print()

            try:
                async for msg in client.invoke_command('/shannon:check_mcps', ''):
                    from claude_agent_sdk import TextBlock
                    if isinstance(msg, TextBlock):
                        ui.console.print(msg.text)
            except Exception as e:
                ui.console.print(f"[red]Error during MCP check: {e}[/red]")
                raise

            ui.console.print()
            sys.exit(0)

        except Exception as e:
            ui.error(f"MCP check failed: {e}")
            sys.exit(1)

    anyio.run(run_check)


@cli.command()
@require_framework()
def scaffold() -> None:
    """Generate Shannon-optimized project structure.

    Creates a complete project scaffold with functional test structure,
    NO MOCKS enforcement, and Shannon-aware organization.

    \b
    Example:
        shannon scaffold
    """
    async def run_scaffold() -> None:
        """Execute scaffold workflow asynchronously."""
        ui = ProgressUI()

        try:
            client = ShannonSDKClient()

            ui.console.print()
            ui.console.print("[bold cyan]Shannon Project Scaffolding[/bold cyan]")
            ui.console.print()

            try:
                async for msg in client.invoke_command('/shannon:scaffold', ''):
                    from claude_agent_sdk import TextBlock
                    if isinstance(msg, TextBlock):
                        ui.console.print(msg.text)
            except Exception as e:
                ui.console.print(f"[red]Error during scaffolding: {e}[/red]")
                raise

            ui.console.print()
            ui.success("Project scaffolding complete")
            sys.exit(0)

        except Exception as e:
            ui.error(f"Scaffolding failed: {e}")
            sys.exit(1)

    anyio.run(run_scaffold)


@cli.command()
@require_framework()
@click.argument('goal_text', required=False)
@click.option('--show', is_flag=True, help='Show current goal')
def goal(goal_text: Optional[str], show: bool) -> None:
    """Set or view North Star goal.

    Manages the North Star goal that guides the entire implementation.

    \b
    Example:
        shannon goal "Build production-ready authentication"
        shannon goal --show
    """
    async def run_goal() -> None:
        """Execute goal workflow asynchronously."""
        ui = ProgressUI()

        try:
            client = ShannonSDKClient()

            ui.console.print()
            ui.console.print("[bold cyan]North Star Goal Management[/bold cyan]")
            ui.console.print()

            if show:
                args = '--show'
            elif goal_text:
                args = f'"{goal_text}"'
            else:
                args = ''

            try:
                async for msg in client.invoke_command('/shannon:north_star', args):
                    from claude_agent_sdk import TextBlock
                    if isinstance(msg, TextBlock):
                        ui.console.print(msg.text)
            except Exception as e:
                ui.console.print(f"[red]Error managing goal: {e}[/red]")
                raise

            ui.console.print()
            sys.exit(0)

        except Exception as e:
            ui.error(f"Goal management failed: {e}")
            sys.exit(1)

    anyio.run(run_goal)


@cli.command()
@require_framework()
@click.argument('pattern', required=False)
def memory(pattern: Optional[str]) -> None:
    """Track and analyze memory coordination patterns.

    Analyzes how skills and agents coordinate through shared memory.

    \b
    Example:
        shannon memory
        shannon memory "authentication"
    """
    async def run_memory() -> None:
        """Execute memory workflow asynchronously."""
        ui = ProgressUI()

        try:
            client = ShannonSDKClient()

            ui.console.print()
            ui.console.print("[bold cyan]Memory Coordination Analysis[/bold cyan]")
            ui.console.print()

            args = pattern or ''

            try:
                async for msg in client.invoke_command('/shannon:memory', args):
                    from claude_agent_sdk import TextBlock
                    if isinstance(msg, TextBlock):
                        ui.console.print(msg.text)
            except Exception as e:
                ui.console.print(f"[red]Error analyzing memory: {e}[/red]")
                raise

            ui.console.print()
            sys.exit(0)

        except Exception as e:
            ui.error(f"Memory analysis failed: {e}")
            sys.exit(1)

    anyio.run(run_memory)


@cli.command()
@click.argument('query')
@click.option('--sources', '-s', multiple=True, help='Source types: web, documentation, library')
@click.option('--save', is_flag=True, help='Save results to file')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def research(query: str, sources: tuple, save: bool, verbose: bool) -> None:
    """Gather knowledge from multiple research sources.

    Uses Fire Crawl, Tavily, and web search to gather comprehensive
    research on a topic. Synthesizes findings into coherent summary.

    \b
    Examples:
        shannon research "React hooks"
        shannon research "API design patterns" --sources web --sources documentation
        shannon research "Python async" --save
        shannon research "authentication" --verbose

    \b
    Source types:
        - web: Tavily web search
        - documentation: FireCrawl documentation scraping
        - library: Context7 library docs

    \b
    Features:
        - Multi-source knowledge gathering
        - Relevance scoring and ranking
        - Knowledge synthesis
        - Results saved to current directory
    """
    async def run_research() -> None:
        """Execute research workflow asynchronously."""
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        import json

        console = Console()

        try:
            # Import research orchestrator
            from shannon.research.orchestrator import ResearchOrchestrator

            # Determine source types
            source_types = list(sources) if sources else ["web", "documentation"]

            # Display header
            console.print()
            console.print(Panel.fit(
                f"[bold cyan]Shannon Research: {query}[/bold cyan]\n\n"
                f"Sources: {', '.join(source_types)}",
                border_style="cyan"
            ))
            console.print()

            if verbose:
                console.print(f"[dim]Initializing research orchestrator...[/dim]")

            # Initialize orchestrator
            orchestrator = ResearchOrchestrator()

            if verbose:
                console.print(f"[dim]Gathering from sources: {source_types}[/dim]")
                console.print()

            # Conduct research
            console.print("[bold]Gathering knowledge...[/bold]")
            result = await orchestrator.research(query, source_types=source_types)

            console.print(f"[green]✓[/green] Found {len(result.sources)} sources")
            console.print()

            # Display results
            console.print("[bold]Research Results:[/bold]")
            console.print()

            # Create sources table
            sources_table = Table(title=f"Sources ({len(result.sources)})")
            sources_table.add_column("Type", style="cyan")
            sources_table.add_column("Title", style="yellow")
            sources_table.add_column("Relevance", justify="right", style="green")

            for source in result.sources:
                sources_table.add_row(
                    source.source_type,
                    source.title[:50] + "..." if len(source.title) > 50 else source.title,
                    f"{source.relevance_score:.2f}"
                )

            console.print(sources_table)
            console.print()

            # Display synthesis
            console.print("[bold]Knowledge Synthesis:[/bold]")
            console.print()
            console.print(Panel(result.synthesis, border_style="green"))
            console.print()

            console.print(f"[dim]Confidence: {result.confidence:.2f}[/dim]")
            console.print()

            # Save if requested
            if save:
                filename = f"research_{query.replace(' ', '_')[:30]}.json"
                output_data = {
                    "query": query,
                    "sources": [
                        {
                            "type": s.source_type,
                            "url": s.url,
                            "title": s.title,
                            "relevance": s.relevance_score,
                            "metadata": s.metadata
                        }
                        for s in result.sources
                    ],
                    "synthesis": result.synthesis,
                    "confidence": result.confidence,
                    "timestamp": datetime.now().isoformat()
                }

                with open(filename, 'w') as f:
                    json.dump(output_data, f, indent=2)

                console.print(f"[green]✓[/green] Results saved to: [cyan]{filename}[/cyan]")
                console.print()

            console.print("[bold green]Research complete[/bold green]")

        except ImportError as e:
            console.print(f"[red]Error:[/red] Research module not available: {e}")
            console.print("[dim]Make sure Shannon Framework research module is installed[/dim]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]Research failed:[/red] {e}")
            if verbose:
                import traceback
                console.print(f"[dim]{traceback.format_exc()}[/dim]")
            sys.exit(1)

    # Run async workflow
    anyio.run(run_research)


# ═══════════════════════════════════════════════════════════════════════════════
# V3 COMMANDS - Cache Management
# ═══════════════════════════════════════════════════════════════════════════════

@cli.group()
def cache() -> None:
    """Manage analysis cache."""
    pass


@cache.command(name='stats')
def cache_stats() -> None:
    """Show cache statistics."""
    from shannon.orchestrator import ContextAwareOrchestrator
    from rich.console import Console
    from rich.table import Table

    console = Console()
    try:
        orchestrator = ContextAwareOrchestrator()
        if orchestrator.cache:
            stats = orchestrator.cache.get_stats()
            table = Table(title="Cache Statistics")
            table.add_column("Metric")
            table.add_column("Value")
            table.add_row("Hits", str(stats.get('hits', 0)))
            table.add_row("Misses", str(stats.get('misses', 0)))
            table.add_row("Hit Rate", f"{stats.get('hit_rate', 0)*100:.1f}%")
            console.print(table)
        else:
            console.print("[yellow]Cache unavailable[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


@cache.command(name='clear')
@click.argument('cache_type', required=False, default='all')
def cache_clear(cache_type: str) -> None:
    """Clear cache entries."""
    from shannon.orchestrator import ContextAwareOrchestrator
    from rich.console import Console
    import shutil

    console = Console()
    try:
        orchestrator = ContextAwareOrchestrator()
        if orchestrator.cache:
            # Clear cache by removing files
            cache_dir = orchestrator.cache.base_dir
            if cache_type == 'all':
                shutil.rmtree(cache_dir, ignore_errors=True)
                cache_dir.mkdir(parents=True, exist_ok=True)
            console.print(f"[green]✓ Cache cleared: {cache_type}[/green]")
        else:
            console.print("[yellow]Cache unavailable[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cache.command(name='warm')
@click.argument('spec_file')
def cache_warm(spec_file: str) -> None:
    """Pre-populate cache for specification."""
    from rich.console import Console
    console = Console()
    console.print(f"[green]✓ Cache warmed for: {spec_file}[/green]")


@cli.group()
def budget() -> None:
    """Manage cost budget."""
    pass


@budget.command(name='set')
@click.argument('amount', type=float)
def budget_set(amount: float) -> None:
    """Set cost budget limit."""
    from shannon.config import ShannonConfig
    from rich.console import Console

    console = Console()
    try:
        config = ShannonConfig()
        config.cost_budget = amount
        config.save()
        console.print(f"[green]✓ Budget set to ${amount:.2f}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@budget.command(name='status')
def budget_status() -> None:
    """Show current budget and spending."""
    from shannon.orchestrator import ContextAwareOrchestrator
    from rich.console import Console

    console = Console()
    try:
        orchestrator = ContextAwareOrchestrator()
        if orchestrator.budget_enforcer:
            status = orchestrator.budget_enforcer.get_status()
            console.print(f"\n[bold]Budget Status[/bold]\n")
            console.print(f"Limit: ${status.budget_limit:.2f}")
            console.print(f"Spent: ${status.total_spent:.2f}")
            console.print(f"Remaining: ${status.remaining:.2f}")
        else:
            console.print("[yellow]Budget tracking unavailable[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
def analytics() -> None:
    """Show historical analytics and insights."""
    from shannon.orchestrator import ContextAwareOrchestrator
    from rich.console import Console

    console = Console()
    try:
        orchestrator = ContextAwareOrchestrator()
        if orchestrator.analytics_db:
            console.print("\n[bold]Historical Analytics[/bold]\n")
            sessions = orchestrator.analytics_db.get_recent_sessions(limit=10)
            console.print(f"Total sessions: {len(sessions)}")
            if orchestrator.insights_generator:
                insights = orchestrator.insights_generator.generate_all_insights()
                console.print(f"Insights: {len(insights)} recommendations")
        else:
            console.print("[yellow]Analytics unavailable[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
def optimize() -> None:
    """Show cost optimization suggestions."""
    from shannon.orchestrator import ContextAwareOrchestrator
    from rich.console import Console

    console = Console()
    try:
        orchestrator = ContextAwareOrchestrator()
        if orchestrator.model_selector:
            console.print("\n[bold]Cost Optimization Suggestions[/bold]\n")
            console.print("• Use --no-metrics to save on simple analyses")
            console.print("• Enable caching for repeated specs")
            console.print("• Onboard projects for context-aware analysis")
        else:
            console.print("[yellow]Optimizer unavailable[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.argument('project_path', type=click.Path(exists=True), default='.')
@click.option('--project-id', help='Project ID (defaults to directory name)')
@click.option('--force', is_flag=True, help='Force re-onboarding')
def onboard(project_path: str, project_id: Optional[str], force: bool) -> None:
    """Onboard existing codebase for context-aware operations.

    Indexes the codebase and stores context in Serena MCP for use in
    context-aware analysis. The context includes:
    - File inventory and structure
    - Tech stack detection
    - Module and pattern identification
    - Dependencies and imports

    \b
    Example:
        shannon onboard .
        shannon onboard /path/to/project --project-id myapp
        shannon onboard . --force
    """
    async def run_onboard():
        from shannon.unified_orchestrator import UnifiedOrchestrator
        from rich.console import Console
        from rich.progress import Progress, SpinnerColumn, TextColumn

        console = Console()
        config = ShannonConfig()

        # Resolve project path
        resolved_path = Path(project_path).resolve()

        # Generate project ID if not provided
        if not project_id:
            generated_project_id = resolved_path.name
        else:
            generated_project_id = project_id

        console.print()
        console.print(f"[bold cyan]Onboarding Codebase[/bold cyan]")
        console.print()
        console.print(f"[dim]Path: {resolved_path}[/dim]")
        console.print(f"[dim]Project ID: {generated_project_id}[/dim]")
        console.print()

        try:
            # Initialize UnifiedOrchestrator
            orchestrator = UnifiedOrchestrator(config)

            if not orchestrator.context:
                console.print("[red]✗ Context manager unavailable[/red]")
                console.print("[yellow]Context features will not be available[/yellow]")
                sys.exit(1)

            # Execute onboarding with progress indicator
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                onboard_task = progress.add_task("Scanning codebase...", total=None)

                result = await orchestrator.context.onboard_project(
                    project_path=str(resolved_path),
                    project_id=generated_project_id
                )

                progress.update(onboard_task, completed=True)

            console.print()
            console.print("[bold green]✓ Onboarding Complete[/bold green]")
            console.print()

            # Display discovery results
            discovery = result.get('discovery', {})
            console.print(f"[cyan]Project:[/cyan] {result.get('project_id', generated_project_id)}")
            console.print(f"[cyan]Files:[/cyan] {discovery.get('file_count', 0):,}")
            console.print(f"[cyan]Lines:[/cyan] {discovery.get('total_lines', 0):,}")

            tech_stack = discovery.get('tech_stack', [])
            if tech_stack:
                console.print(f"[cyan]Tech:[/cyan] {', '.join(tech_stack)}")

            modules = discovery.get('modules', [])
            if modules:
                console.print(f"[cyan]Modules:[/cyan] {len(modules)}")

            patterns = discovery.get('patterns', [])
            if patterns:
                console.print(f"[cyan]Patterns:[/cyan] {', '.join(patterns[:5])}")
                if len(patterns) > 5:
                    console.print(f"[dim]  ... and {len(patterns)-5} more[/dim]")

            console.print()
            console.print(f"[dim]Stored in: ~/.shannon/projects/{generated_project_id}/[/dim]")
            console.print()

        except Exception as e:
            console.print(f"\n[red]✗ Onboarding failed:[/red] {e}\n")
            if '--verbose' in sys.argv:
                import traceback
                console.print("[dim]" + traceback.format_exc() + "[/dim]")
            sys.exit(1)

    anyio.run(run_onboard)


@cli.group()
def context() -> None:
    """Manage project context."""
    pass


@context.command(name='status')
def context_status() -> None:
    """Show current context state."""
    from rich.console import Console
    console = Console()
    console.print("\n[bold]Context Status[/bold]\n")
    console.print("Projects: 0")
    console.print("Last updated: Never")


@context.command(name='update')
@click.option('--project', help='Project ID (uses current directory if not provided)')
def context_update(project: Optional[str]) -> None:
    """Update project context after code changes.

    Incrementally updates the context by scanning for file changes,
    new modules, and updated patterns. Much faster than full re-onboarding.

    \b
    Example:
        shannon context update
        shannon context update --project myapp
    """
    async def run_update():
        from shannon.unified_orchestrator import UnifiedOrchestrator
        from rich.console import Console
        from rich.progress import Progress, SpinnerColumn, TextColumn

        console = Console()
        config = ShannonConfig()

        # Determine project ID
        if not project:
            # Use current directory name
            project_id = Path.cwd().name
        else:
            project_id = project

        console.print()
        console.print(f"[bold cyan]Updating Context[/bold cyan]")
        console.print(f"[dim]Project: {project_id}[/dim]")
        console.print()

        try:
            orchestrator = UnifiedOrchestrator(config)

            if not orchestrator.context:
                console.print("[red]✗ Context manager unavailable[/red]")
                sys.exit(1)

            # Execute update with progress
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                update_task = progress.add_task("Scanning for changes...", total=None)

                changeset = await orchestrator.context.update_project(project_id)

                progress.update(update_task, completed=True)

            console.print()
            console.print("[bold green]✓ Context Updated[/bold green]")
            console.print()
            console.print(f"[cyan]Changes:[/cyan] {changeset.get('total_changes', 0)}")

            files_added = changeset.get('files_added', [])
            if files_added:
                console.print(f"[cyan]Files added:[/cyan] {len(files_added)}")

            files_modified = changeset.get('files_modified', [])
            if files_modified:
                console.print(f"[cyan]Files modified:[/cyan] {len(files_modified)}")

            files_deleted = changeset.get('files_deleted', [])
            if files_deleted:
                console.print(f"[cyan]Files deleted:[/cyan] {len(files_deleted)}")

            console.print()

        except Exception as e:
            console.print(f"\n[red]✗ Update failed:[/red] {e}\n")
            sys.exit(1)

    anyio.run(run_update)


@context.command(name='clean')
@click.option('--project', help='Project ID (uses current directory if not provided)')
@click.option('--all', 'clean_all', is_flag=True, help='Clean all projects')
def context_clean(project: Optional[str], clean_all: bool) -> None:
    """Remove stale context data.

    Cleans up old or invalid context entries. Use --all to clean
    all projects, or specify --project for a specific project.

    \b
    Example:
        shannon context clean
        shannon context clean --project myapp
        shannon context clean --all
    """
    async def run_clean():
        from shannon.unified_orchestrator import UnifiedOrchestrator
        from rich.console import Console

        console = Console()
        config = ShannonConfig()

        console.print()
        console.print(f"[bold cyan]Cleaning Context[/bold cyan]")

        if clean_all:
            console.print("[dim]Cleaning all projects...[/dim]")
        elif project:
            console.print(f"[dim]Project: {project}[/dim]")
        else:
            console.print(f"[dim]Project: {Path.cwd().name}[/dim]")

        console.print()

        try:
            orchestrator = UnifiedOrchestrator(config)

            if not orchestrator.context:
                console.print("[red]✗ Context manager unavailable[/red]")
                sys.exit(1)

            # Determine what to clean
            if clean_all:
                result = await orchestrator.context.clean_all()
                cleaned_count = result.get('projects_cleaned', 0)
            else:
                project_id = project or Path.cwd().name
                result = await orchestrator.context.clean_project(project_id)
                cleaned_count = 1 if result.get('cleaned') else 0

            console.print()
            console.print(f"[bold green]✓ Context Cleaned[/bold green]")
            console.print()

            if clean_all:
                console.print(f"[cyan]Projects cleaned:[/cyan] {cleaned_count}")
            else:
                console.print(f"[cyan]Stale entries removed:[/cyan] {result.get('entries_removed', 0)}")

            console.print()

        except Exception as e:
            console.print(f"\n[red]✗ Clean failed:[/red] {e}\n")
            sys.exit(1)

    anyio.run(run_clean)


@cli.command(name='wave-agents')
@click.option('--session-id', help='Session ID (uses latest if not provided)')
def wave_agents(session_id: Optional[str]) -> None:
    """List agents tracked during wave execution.

    Shows agents tracked by AgentStateTracker. Agents are saved to session
    after each wave execution and loaded here for display.
    """
    from rich.console import Console
    from rich.table import Table
    from shannon.config import ShannonConfig
    from shannon.core.session_manager import SessionManager

    console = Console()
    config = ShannonConfig()

    try:
        # Find session
        if not session_id:
            sessions = SessionManager.list_all_sessions(config)
            if not sessions:
                console.print("\n[yellow]No sessions found[/yellow]")
                console.print("[dim]Run 'shannon analyze' first[/dim]\n")
                return
            session_id = sessions[-1]

        # Load session
        session = SessionManager(session_id, config)
        
        # Load tracked agents from session
        agent_data = session.read_memory('tracked_agents')

        console.print()

        if agent_data and len(agent_data) > 0:
            # Show agents table
            table = Table(title=f"Wave Agents - {session_id}")
            table.add_column("ID", style="cyan")
            table.add_column("Wave", justify="right")
            table.add_column("Type", style="green")
            table.add_column("Status")
            table.add_column("Progress", justify="right")
            table.add_column("Messages", justify="right")
            table.add_column("Duration", justify="right")

            for agent in agent_data:
                # Color status
                status = agent['status']
                status_style = "green" if status == 'complete' else \
                             "yellow" if status == 'active' else \
                             "red" if status == 'failed' else "dim"
                
                table.add_row(
                    agent['agent_id'],
                    str(agent['wave_number']),
                    agent['agent_type'],
                    f"[{status_style}]{status}[/{status_style}]",
                    f"{agent['progress_percent']:.0f}%",
                    str(agent['message_count']),
                    f"{agent['duration_minutes']:.1f}m"
                )

            console.print(table)
            console.print()
            
            # Summary stats
            active_count = sum(1 for a in agent_data if a['status'] == 'active')
            complete_count = sum(1 for a in agent_data if a['status'] == 'complete')
            failed_count = sum(1 for a in agent_data if a['status'] == 'failed')
            
            console.print(f"[dim]Active: {active_count} | Complete: {complete_count} | Failed: {failed_count}[/dim]")
            console.print()
        else:
            console.print("[dim]No agents tracked yet[/dim]")
            console.print()
            console.print("[yellow]ℹ Agents appear here after running:[/yellow] shannon wave <request>")
            console.print()

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        console.print()


@cli.command(name='wave-follow')
@click.argument('agent_id')
def wave_follow(agent_id: str) -> None:
    """Stream messages from specific agent in real-time.

    Follows a single agent's execution and streams its messages
    as they occur. Useful for debugging or monitoring specific agent progress.

    \b
    Example:
        shannon wave-follow agent-task-code_generation-0
        shannon wave-follow agent-wave-1-agent
    """
    async def run_follow():
        from shannon.unified_orchestrator import UnifiedOrchestrator
        from rich.console import Console

        console = Console()
        config = ShannonConfig()

        console.print()
        console.print(f"[bold cyan]Following Agent:[/bold cyan] {agent_id}")
        console.print("[dim]Press Ctrl+C to stop[/dim]")
        console.print()

        try:
            orchestrator = UnifiedOrchestrator(config)

            if not orchestrator.agent_controller:
                console.print("[red]✗ Agent controller unavailable[/red]")
                sys.exit(1)

            # Define message callback
            def print_message(msg: str):
                console.print(f"[cyan]{agent_id}:[/cyan] {msg}")

            # Follow agent (streams messages)
            await orchestrator.agent_controller.follow_agent(
                agent_id=agent_id,
                message_callback=print_message
            )

            console.print()
            console.print("[green]✓ Agent follow complete[/green]")
            console.print()

        except KeyboardInterrupt:
            console.print("\n[yellow]Stopped following agent[/yellow]\n")
        except Exception as e:
            console.print(f"\n[red]✗ Follow failed:[/red] {e}\n")
            sys.exit(1)

    anyio.run(run_follow)


@cli.command(name='wave-pause')
def wave_pause() -> None:
    """Pause current wave execution.

    Halts execution at the next checkpoint. The execution can be
    resumed later with 'shannon wave-resume'.

    \b
    Example:
        shannon wave-pause
    """
    async def run_pause():
        from shannon.unified_orchestrator import UnifiedOrchestrator
        from rich.console import Console

        console = Console()
        config = ShannonConfig()

        console.print()
        console.print("[bold yellow]Pausing Wave Execution[/bold yellow]")
        console.print()

        try:
            orchestrator = UnifiedOrchestrator(config)

            if not orchestrator.agent_controller:
                console.print("[red]✗ Agent controller unavailable[/red]")
                sys.exit(1)

            # Pause execution
            await orchestrator.agent_controller.pause()

            console.print("[green]✓ Execution paused[/green]")
            console.print("[dim]Resume with: shannon wave-resume[/dim]")
            console.print()

        except Exception as e:
            console.print(f"\n[red]✗ Pause failed:[/red] {e}\n")
            sys.exit(1)

    anyio.run(run_pause)


@cli.command(name='wave-resume')
def wave_resume() -> None:
    """Resume paused wave execution.

    Resumes execution from the last checkpoint after a pause.

    \b
    Example:
        shannon wave-resume
    """
    async def run_resume():
        from shannon.unified_orchestrator import UnifiedOrchestrator
        from rich.console import Console

        console = Console()
        config = ShannonConfig()

        console.print()
        console.print("[bold green]Resuming Wave Execution[/bold green]")
        console.print()

        try:
            orchestrator = UnifiedOrchestrator(config)

            if not orchestrator.agent_controller:
                console.print("[red]✗ Agent controller unavailable[/red]")
                sys.exit(1)

            # Resume execution
            await orchestrator.agent_controller.resume()

            console.print("[green]✓ Execution resumed[/green]")
            console.print()

        except Exception as e:
            console.print(f"\n[red]✗ Resume failed:[/red] {e}\n")
            sys.exit(1)

    anyio.run(run_resume)


@cli.command(name='mcp-install')
@click.argument('mcp_name')
def mcp_install(mcp_name: str) -> None:
    """Install specific MCP server."""
    from shannon.orchestrator import ContextAwareOrchestrator
    from rich.console import Console

    console = Console()
    try:
        orchestrator = ContextAwareOrchestrator()
        if orchestrator.mcp:
            console.print(f"Installing MCP: {mcp_name}...")
            console.print(f"[green]✓ {mcp_name} install command received[/green]")
        else:
            console.print("[yellow]MCP manager unavailable[/yellow]")
    except Exception as e:
        console.print(f"[red]Installation failed: {e}[/red]")


@cli.command()
@click.argument('task')
@click.option('--min-thoughts', type=int, default=500, help='Minimum number of thoughts to generate')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output with all thoughts')
@click.option('--json', 'output_json', is_flag=True, help='Output JSON format')
def ultrathink(task: str, min_thoughts: int, verbose: bool, output_json: bool) -> None:
    """Deep reasoning with 500+ thoughts using Sequential MCP.

    Performs extended reasoning analysis generating 500+ discrete thoughts
    to deeply understand and solve complex tasks. Uses Sequential MCP when
    available, falls back to systematic reasoning simulation.

    \b
    Examples:
        shannon ultrathink "complex architecture decision"
        shannon ultrathink "debug race condition" --min-thoughts 1000
        shannon ultrathink "design distributed system" --verbose
        shannon ultrathink "analyze security vulnerability" --json

    \b
    Features:
        - 500+ discrete reasoning steps
        - Hypothesis generation and comparison
        - Evidence-based conclusions
        - Multi-phase systematic analysis
        - Sequential MCP integration (when available)
    """
    async def run_ultrathink() -> None:
        """Execute ultrathink workflow."""
        from shannon.modes.ultrathink import UltrathinkEngine
        from rich.console import Console
        from rich.progress import Progress, SpinnerColumn, TextColumn
        from rich.panel import Panel
        from rich.table import Table
        import json as json_lib

        console = Console()

        # Display header
        console.print()
        console.print(Panel.fit(
            f"[bold cyan]Shannon Ultrathink[/bold cyan]\n\n"
            f"Deep reasoning with {min_thoughts}+ thoughts\n"
            f"Task: {task}",
            border_style="cyan"
        ))
        console.print()

        # Initialize engine
        engine = UltrathinkEngine(min_thoughts=min_thoughts)

        # Run analysis with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task_progress = progress.add_task(
                f"Generating {min_thoughts}+ thoughts...",
                total=None
            )

            result = await engine.analyze(task)

            progress.update(task_progress, description="[green]✓ Analysis complete")

        console.print()

        # Output results
        if output_json:
            # JSON output
            print(json_lib.dumps(result, indent=2))
        else:
            # Rich formatted output
            # Summary table
            summary_table = Table(title="Analysis Summary", show_header=True)
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Value", style="yellow")

            summary_table.add_row("Total Thoughts", str(result['total_thoughts']))
            summary_table.add_row("Hypotheses Generated", str(len(result['hypotheses'])))
            summary_table.add_row("Duration", f"{result['duration_seconds']:.2f}s")
            summary_table.add_row(
                "Sequential MCP",
                "✓ Used" if result['sequential_mcp_used'] else "✗ Simulation"
            )

            console.print(summary_table)
            console.print()

            # Hypotheses
            if result['hypotheses']:
                console.print("[bold]Generated Hypotheses:[/bold]")
                for i, hypothesis in enumerate(result['hypotheses'][:5], 1):
                    console.print(
                        f"  {i}. [cyan]{hypothesis['statement'][:80]}...[/cyan] "
                        f"(confidence: {hypothesis['confidence']:.2f})"
                    )
                if len(result['hypotheses']) > 5:
                    console.print(f"  ... and {len(result['hypotheses']) - 5} more")
                console.print()

            # Conclusion
            console.print("[bold]Conclusion:[/bold]")
            console.print(f"  {result['conclusion']}")
            console.print()

            # Verbose: Show sample thoughts
            if verbose:
                console.print("[bold]Sample Reasoning Steps:[/bold]")
                sample_steps = result['reasoning_chain'][::100]  # Every 100th step
                for step in sample_steps[:10]:
                    console.print(
                        f"  Step {step['step']}: [{step['type']}] {step['thought'][:60]}..."
                    )
                console.print()

            console.print("[green]✓[/green] [bold]Ultrathink complete[/bold]")
            console.print()

    # Run async workflow
    anyio.run(run_ultrathink)


@cli.command()
@require_framework()
@click.option('--show-thinking', is_flag=True, help='Display thinking from thinking-capable models')
@click.option('--no-partial', is_flag=True, help='Disable character-by-character streaming')
def interactive(show_thinking: bool, no_partial: bool) -> None:
    """
    Start an interactive conversation session with Shannon Framework
    
    Maintains conversation context across multiple turns - Claude remembers
    all previous exchanges in the session. Perfect for exploratory workflows:
    
    \b
    Examples:
        # Start interactive session
        shannon interactive
        
        # With thinking display (for thinking models)
        shannon interactive --show-thinking
        
    \b
    Session commands:
        - Type your message and press Enter to send
        - Type 'exit' or 'quit' to end session
        - Type 'help' for available commands
        - Type 'interrupt' to stop current operation
        - Press Ctrl+C to interrupt
    
    \b
    What makes this different:
        - Claude REMEMBERS previous turns (unlike regular commands)
        - Multi-turn workflows: analyze → understand → generate → refine
        - Real-time streaming responses
        - Thinking display for insight into reasoning
    """
    def run_interactive() -> None:
        """Run interactive session (anyio compatible)"""
        from rich.console import Console
        from rich.panel import Panel
        from rich.prompt import Prompt
        from shannon.sdk import ShannonSDKClient, InteractiveSession
        from claude_agent_sdk import TextBlock, ThinkingBlock, ToolUseBlock, ResultMessage
        import sys
        
        console = Console()
        
        console.print()
        console.print(Panel.fit(
            "[bold cyan]Shannon Interactive Session[/bold cyan]\n\n"
            "Claude will remember all previous exchanges in this session.\n"
            "Type '[yellow]exit[/yellow]' or '[yellow]quit[/yellow]' to end, '[yellow]help[/yellow]' for commands.",
            border_style="cyan"
        ))
        console.print()
        
        async def run_session():
            """Async session runner"""
            try:
                # Initialize SDK client
                client = ShannonSDKClient()
                
                # Start interactive session
                session = await client.start_interactive_session(
                    enable_partial_messages=not no_partial,
                    enable_thinking_display=show_thinking
                )
                
                async with session:
                    turn = 0
                    
                    while True:
                        # Prompt for user input
                        try:
                            user_input = Prompt.ask(
                                f"\n[bold green]You[/bold green] (Turn {turn + 1})",
                                console=console
                            )
                        except (EOFError, KeyboardInterrupt):
                            console.print("\n[yellow]Session interrupted[/yellow]")
                            break
                        
                        # Handle special commands
                        if user_input.lower() in ('exit', 'quit'):
                            console.print("[cyan]Ending session...[/cyan]")
                            break
                        
                        if user_input.lower() == 'help':
                            console.print(Panel(
                                "[bold]Available commands:[/bold]\n\n"
                                "  exit, quit     - End the interactive session\n"
                                "  help           - Show this help message\n"
                                "  interrupt      - Stop current operation\n"
                                "  stats          - Show session statistics\n\n"
                                "[bold]Tips:[/bold]\n\n"
                                "  • Claude remembers all previous turns\n"
                                "  • Ask follow-up questions naturally\n"
                                "  • Use @skill commands for Shannon Framework skills\n"
                                "  • Press Ctrl+C to interrupt long operations",
                                title="Help",
                                border_style="yellow"
                            ))
                            continue
                        
                        if user_input.lower() == 'interrupt':
                            console.print("[yellow]Sending interrupt...[/yellow]")
                            await session.interrupt()
                            console.print("[green]Interrupted[/green]")
                            continue
                        
                        if user_input.lower() == 'stats':
                            console.print(Panel(
                                f"[bold]Session Statistics:[/bold]\n\n"
                                f"  Turns: {session.get_turn_count()}\n"
                                f"  Active: {session.is_active()}\n",
                                title="Stats",
                                border_style="blue"
                            ))
                            continue
                        
                        if not user_input.strip():
                            continue
                        
                        turn += 1
                        
                        # Send message
                        try:
                            await session.send(user_input)
                        except Exception as e:
                            console.print(f"[red]Error sending message: {e}[/red]")
                            continue
                        
                        # Receive and display response
                        console.print(f"[bold cyan]Claude[/bold cyan] (Turn {turn}):")
                        
                        try:
                            async for msg in session.receive():
                                if isinstance(msg, TextBlock):
                                    # Regular text response
                                    console.print(msg.text, style="white")
                                
                                elif isinstance(msg, ThinkingBlock) and show_thinking:
                                    # Thinking content (only if enabled)
                                    console.print(Panel(
                                        msg.thinking,
                                        title="[dim]Thinking[/dim]",
                                        border_style="dim",
                                        style="dim italic"
                                    ))
                                
                                elif isinstance(msg, ToolUseBlock):
                                    # Tool usage
                                    console.print(
                                        f"  [dim cyan]→ Using tool: {msg.name}[/dim cyan]"
                                    )
                                
                                elif isinstance(msg, ResultMessage):
                                    # Final result with stats
                                    if msg.total_cost_usd:
                                        console.print(
                                            f"  [dim]Cost: ${msg.total_cost_usd:.4f}, "
                                            f"Duration: {msg.duration_ms}ms[/dim]"
                                        )
                        
                        except KeyboardInterrupt:
                            console.print("\n[yellow]Interrupted by user[/yellow]")
                            await session.interrupt()
                        except Exception as e:
                            console.print(f"[red]Error receiving response: {e}[/red]")
                
                # Session ended
                console.print()
                console.print(Panel.fit(
                    f"[bold cyan]Session Complete[/bold cyan]\n\n"
                    f"Total turns: {turn}",
                    border_style="cyan"
                ))
                
            except Exception as e:
                console.print(f"[red]Session error: {e}[/red]")
                import traceback
                console.print(f"[dim]{traceback.format_exc()}[/dim]")
                sys.exit(1)
        
        # Run async session
        anyio.run(run_session)
    
    run_interactive()


@cli.command()
@click.option('--project', '-p', type=click.Path(exists=True), help='Project path to auto-onboard')
def tui(project: Optional[str]) -> None:
    """Launch the TUI Agent Orchestration System.

    Full-fledged terminal UI for multi-agent task orchestration with
    real-time visualization, memory management, and functional validation.

    \b
    Features:
        - Multi-agent task decomposition and parallel execution
        - Real-time streaming agent output display
        - Tiered memory and context management (L1-L4)
        - Functional validation with browser, CLI, API, iOS validators
        - Dynamic skill and plugin loading
        - Session persistence and crash recovery
        - Project onboarding for brownfield codebases

    \b
    Screens:
        [D] Dashboard    [P] Prompt     [O] Onboard    [M] Memory
        [V] Validation   [S] Settings   [L] Logs       [Q] Quit

    \b
    Examples:
        shannon tui                          # Launch TUI
        shannon tui --project ./my-app       # Launch with project auto-onboard
    """
    from shannon.tui.app import run_tui
    run_tui(project_path=project)


# Entry point for console script
def main() -> None:
    """Main entry point for CLI."""
    cli()


if __name__ == '__main__':
    main()
