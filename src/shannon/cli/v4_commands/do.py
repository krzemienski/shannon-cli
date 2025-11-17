"""Shannon CLI - shannon do command (V5 - Claude Code Skills)

V5: Uses Shannon Framework task-automation Claude Code skill.
Wraps with V3 intelligence (cache, analytics, context, cost optimization).

This is the CORRECT architecture leveraging Claude Code skills.

Example:
    shannon do "create authentication system with JWT"
    shannon do "fix the login bug" --dashboard
    shannon do "add tests for user API"
"""

import sys
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
import uuid

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from shannon.config import ShannonConfig
from shannon.unified_orchestrator import UnifiedOrchestrator

logger = logging.getLogger(__name__)


@click.command(name='do')
@click.argument('task')
@click.option('--dashboard', '-d', is_flag=True, help='Enable real-time dashboard')
@click.option('--session-id', help='Session ID (auto-generated if not provided)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--auto', is_flag=True, help='Autonomous mode (no questions)')
def do_command(
    task: str,
    dashboard: bool,
    session_id: Optional[str],
    verbose: bool,
    auto: bool
):
    """Execute task via Shannon Framework task-automation skill.

    V5 Integration:
    - Uses Claude Code task-automation skill from Shannon Framework
    - Wraps with V3 intelligence: cache, analytics, context, cost optimization
    - Real-time dashboard streaming
    - Simple, clean delegation pattern

    \b
    Examples:
        shannon do "create authentication system"
        shannon do "fix login bug" --dashboard
        shannon do "create REST API with users and posts"

    \b
    What Happens:
        1. Shannon CLI calls Claude via Anthropic SDK
        2. Shannon Framework plugin loaded (has 19 Claude Code skills)
        3. Claude uses task-automation skill to execute task
        4. V3 features wrap execution (cache, analytics, cost)
        5. Results stream to dashboard if enabled
    """
    async def run_do():
        console = Console()
        config = ShannonConfig()

        # Generate session ID
        if not session_id:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            generated_session_id = f"do_{timestamp}_{unique_id}"
        else:
            generated_session_id = session_id

        console.print()
        console.print(Panel.fit(
            "[bold cyan]Shannon V5 - Task Execution[/bold cyan]\n\n"
            f"Task: {task}\n"
            f"Session: {generated_session_id}",
            border_style="cyan"
        ))
        console.print()

        try:
            # Initialize UnifiedOrchestrator (V3+V4 integrated)
            console.print("[dim]Initializing UnifiedOrchestrator...[/dim]")
            orchestrator = UnifiedOrchestrator(config)

            if verbose:
                status = orchestrator.get_status()
                console.print(f"[dim]✓ V3 components: {sum(status['v3_components'].values())}/4[/dim]")
                console.print(f"[dim]✓ Shared subsystems: {sum(status['shared_subsystems'].values())}/6[/dim]")

            console.print()

            # Setup dashboard if enabled
            dashboard_client = None
            if dashboard:
                console.print("[dim]Connecting to dashboard...[/dim]")
                from shannon.communication.dashboard_client import DashboardEventClient
                dashboard_client = DashboardEventClient('http://localhost:8000', generated_session_id)

                connected = await dashboard_client.connect()
                if connected:
                    console.print("[dim]✓ Dashboard connected[/dim]")
                    console.print(f"[dim]  Open: http://localhost:5173 (session: {generated_session_id})[/dim]")
                    
                    # Emit execution:started event (colon-separated)
                    await dashboard_client.emit_event('execution:started', {
                        'task': task,  # Dashboard expects 'task' not 'task_name'
                        'session_id': generated_session_id,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    console.print("[yellow]⚠ Dashboard connection failed[/yellow]")
                    console.print("[dim]  Continuing without real-time updates[/dim]")
                    dashboard_client = None

                console.print()

            # Execute task via UnifiedOrchestrator
            # This invokes Shannon Framework task-automation skill
            console.print("[bold]Executing task via Shannon Framework skill...[/bold]")
            console.print()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                exec_task = progress.add_task("Invoking task-automation skill...", total=None)

                # Get project path (defaults to cwd)
                from pathlib import Path
                project_path = Path.cwd()

                # V5: Execute via intelligent context-aware workflow
                result = await orchestrator.execute_task(
                    task=task,
                    project_path=project_path,
                    dashboard_client=dashboard_client,
                    session_id=generated_session_id,
                    auto_mode=auto
                )

                progress.update(exec_task, completed=True)

            console.print()

            # Display results
            success = result.get('success', False)

            if success:
                console.print(Panel.fit(
                    "[bold green]✓ Task Complete[/bold green]",
                    border_style="green"
                ))

                # Show files created
                files = result.get('files_created', [])
                if files:
                    console.print()
                    console.print(f"[cyan]Files created:[/cyan] {len(files)}")
                    for f in files[:10]:
                        console.print(f"  ✓ {f}")
                    if len(files) > 10:
                        console.print(f"  ... and {len(files)-10} more")

                # Show message count
                msg_count = result.get('message_count', 0)
                if msg_count > 0:
                    console.print()
                    console.print(f"[dim]Messages: {msg_count}[/dim]")

            else:
                console.print(Panel.fit(
                    "[bold red]✗ Task Failed[/bold red]",
                    border_style="red"
                ))

            console.print()

            # Emit completion event before disconnect
            if dashboard_client:
                if success:
                    await dashboard_client.emit_event('execution:completed', {
                        'success': True,
                        'files_created': files,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    await dashboard_client.emit_event('execution:failed', {
                        'success': False,
                        'timestamp': datetime.now().isoformat()
                    })
                
                await dashboard_client.disconnect()

            sys.exit(0 if success else 1)

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/yellow]\n")
            sys.exit(130)

        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]\n")
            if verbose:
                import traceback
                console.print("[dim]" + traceback.format_exc() + "[/dim]")
            sys.exit(1)

    # Run async workflow
    import anyio
    anyio.run(run_do)


# Register command
def register(cli_group):
    """Register V5 do command with CLI group"""
    cli_group.add_command(do_command)
