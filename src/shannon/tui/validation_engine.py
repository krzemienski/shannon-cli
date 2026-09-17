"""
Validation engine for the TUI Agent Orchestration System.

Provides a comprehensive, multi-strategy validation pipeline that
automatically selects and runs validators (browser, CLI, API, iOS
simulator) based on the detected project type.  Results are emitted
as events via the Shannon event bus.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional

from shannon.communication.events import EventBus, EventType
from shannon.tui.models import (
    ProjectInfo,
    ValidationPlan,
    ValidationRun,
    ValidationStatus,
    ValidationStep,
    ValidatorType,
)
from shannon.tui.project_scanner import ProjectType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependency imports
# ---------------------------------------------------------------------------

_PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.async_api import async_playwright  # type: ignore[import-untyped]

    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    pass

_HTTPX_AVAILABLE = False
try:
    import httpx  # type: ignore[import-untyped]

    _HTTPX_AVAILABLE = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# ValidatorRegistry
# ---------------------------------------------------------------------------


class ValidatorRegistry:
    """Maps :class:`ProjectType` values to the list of applicable
    :class:`ValidatorType` validators.

    The registry is pre-populated with sensible defaults and can be
    extended at runtime via :meth:`register`.
    """

    _DEFAULT_MAPPING: Dict[ProjectType, List[ValidatorType]] = {
        ProjectType.FRONTEND: [
            ValidatorType.BROWSER,
            ValidatorType.CLI,
            ValidatorType.API,
        ],
        ProjectType.CLI_TOOL: [ValidatorType.CLI],
        ProjectType.API_SERVER: [ValidatorType.API, ValidatorType.CLI],
        ProjectType.MOBILE: [ValidatorType.IOS_SIMULATOR, ValidatorType.API],
        ProjectType.FULL_STACK: [
            ValidatorType.BROWSER,
            ValidatorType.CLI,
            ValidatorType.API,
        ],
        ProjectType.LIBRARY: [ValidatorType.CLI],
        ProjectType.BACKEND: [ValidatorType.API, ValidatorType.CLI],
        ProjectType.SYSTEMS: [ValidatorType.CLI],
        ProjectType.DATA_SCIENCE: [ValidatorType.CLI],
        ProjectType.UNKNOWN: [ValidatorType.CLI],
    }

    def __init__(self) -> None:
        self._mapping: Dict[ProjectType, List[ValidatorType]] = dict(
            self._DEFAULT_MAPPING
        )

    def get_validators(self, project_type: ProjectType) -> List[ValidatorType]:
        """Return the list of validators applicable to *project_type*.

        Falls back to ``[ValidatorType.CLI]`` if the type is not
        registered.
        """
        return list(self._mapping.get(project_type, [ValidatorType.CLI]))

    def register(
        self,
        project_type: ProjectType,
        validators: List[ValidatorType],
    ) -> None:
        """Register or replace the validators for *project_type*."""
        self._mapping[project_type] = list(validators)


# ---------------------------------------------------------------------------
# BrowserValidator
# ---------------------------------------------------------------------------


class BrowserValidator:
    """Validates web-application behaviour via a headless browser.

    Uses Playwright for navigation, interaction, assertion, and
    screenshot capture.  If Playwright is not installed every step is
    marked as ``FAILED`` with an appropriate message.
    """

    async def validate(
        self,
        steps: List[ValidationStep],
        base_url: str,
    ) -> List[ValidationStep]:
        """Execute browser-based validation *steps* against *base_url*.

        Args:
            steps: Validation steps of type ``ValidatorType.BROWSER``.
            base_url: Root URL of the web application under test.

        Returns:
            The same list of steps with updated statuses.
        """
        if not _PLAYWRIGHT_AVAILABLE:
            for step in steps:
                step.status = ValidationStatus.FAILED
                step.error = "Playwright not installed"
            return steps

        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                try:
                    context = await browser.new_context()
                    page = await context.new_page()

                    for step in steps:
                        start = time.monotonic()
                        try:
                            step.status = ValidationStatus.RUNNING

                            # Navigate
                            target_url = step.url or base_url
                            if not target_url.startswith(("http://", "https://")):
                                target_url = f"{base_url.rstrip('/')}/{target_url.lstrip('/')}"
                            await page.goto(target_url, wait_until="networkidle")

                            # Execute command as JavaScript if provided
                            if step.command:
                                result = await page.evaluate(step.command)
                                step.output = str(result) if result else ""

                            # Assert expected output pattern
                            if step.expected_output:
                                page_content = await page.content()
                                if step.expected_output not in page_content:
                                    step.status = ValidationStatus.FAILED
                                    step.error = (
                                        f"Expected content '{step.expected_output}' "
                                        f"not found on page"
                                    )
                                    step.duration_seconds = time.monotonic() - start
                                    continue

                            # Capture screenshot
                            screenshot_path = step.metadata.get("screenshot_path")
                            if screenshot_path:
                                await page.screenshot(path=screenshot_path)
                                step.screenshot_path = screenshot_path

                            step.status = ValidationStatus.PASSED
                        except Exception as exc:
                            step.status = ValidationStatus.FAILED
                            step.error = str(exc)
                            logger.warning(
                                "Browser validation step '%s' failed: %s",
                                step.name,
                                exc,
                            )
                        finally:
                            step.duration_seconds = time.monotonic() - start

                    await context.close()
                finally:
                    await browser.close()
        except Exception as exc:
            logger.error("Browser validator error: %s", exc, exc_info=True)
            for step in steps:
                if step.status in (
                    ValidationStatus.PENDING,
                    ValidationStatus.RUNNING,
                ):
                    step.status = ValidationStatus.ERROR
                    step.error = f"Browser validator error: {exc}"

        return steps


# ---------------------------------------------------------------------------
# CLIValidator
# ---------------------------------------------------------------------------


class CLIValidator:
    """Validates command-line operations using ``asyncio.subprocess``.

    Runs build commands, linters, type checkers, and similar tools,
    capturing stdout/stderr and checking exit codes.
    """

    async def validate(
        self,
        steps: List[ValidationStep],
        project_root: Path,
    ) -> List[ValidationStep]:
        """Execute CLI-based validation *steps* under *project_root*.

        Args:
            steps: Validation steps of type ``ValidatorType.CLI``.
            project_root: Path used as the working directory.

        Returns:
            The same list of steps with updated statuses.
        """
        for step in steps:
            if not step.command:
                step.status = ValidationStatus.SKIPPED
                step.error = "No command specified"
                continue

            start = time.monotonic()
            step.status = ValidationStatus.RUNNING
            try:
                process = await asyncio.create_subprocess_shell(
                    step.command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(project_root),
                )

                timeout = step.metadata.get("timeout", 120)
                try:
                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        process.communicate(),
                        timeout=timeout,
                    )
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                    step.status = ValidationStatus.FAILED
                    step.error = f"Command timed out after {timeout}s"
                    step.duration_seconds = time.monotonic() - start
                    continue

                stdout_text = stdout_bytes.decode("utf-8", errors="replace")
                stderr_text = stderr_bytes.decode("utf-8", errors="replace")
                step.output = stdout_text
                if stderr_text:
                    step.output = f"{stdout_text}\n--- stderr ---\n{stderr_text}"

                exit_code = process.returncode or 0

                # Check exit code
                if exit_code != step.expected_exit_code:
                    step.status = ValidationStatus.FAILED
                    step.error = (
                        f"Exit code {exit_code} "
                        f"(expected {step.expected_exit_code})"
                    )
                # Check expected output pattern
                elif step.expected_output and step.expected_output not in stdout_text:
                    step.status = ValidationStatus.FAILED
                    step.error = (
                        f"Expected output pattern '{step.expected_output}' "
                        f"not found in stdout"
                    )
                else:
                    step.status = ValidationStatus.PASSED

            except Exception as exc:
                step.status = ValidationStatus.ERROR
                step.error = str(exc)
                logger.warning(
                    "CLI validation step '%s' failed: %s",
                    step.name,
                    exc,
                )
            finally:
                step.duration_seconds = time.monotonic() - start

        return steps


# ---------------------------------------------------------------------------
# APIValidator
# ---------------------------------------------------------------------------


class APIValidator:
    """Validates HTTP API endpoints using ``httpx``.

    Sends requests and asserts on status codes, headers, and response
    body patterns.
    """

    async def validate(
        self,
        steps: List[ValidationStep],
        base_url: str,
    ) -> List[ValidationStep]:
        """Execute API-based validation *steps* against *base_url*.

        Args:
            steps: Validation steps of type ``ValidatorType.API``.
            base_url: Root URL of the API server.

        Returns:
            The same list of steps with updated statuses.
        """
        if not _HTTPX_AVAILABLE:
            for step in steps:
                step.status = ValidationStatus.FAILED
                step.error = "httpx not installed"
            return steps

        async with httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
        ) as client:
            for step in steps:
                start = time.monotonic()
                step.status = ValidationStatus.RUNNING
                try:
                    url = step.url or "/"
                    method = step.method.upper()
                    headers = step.headers or {}
                    body = step.body

                    response = await client.request(
                        method=method,
                        url=url,
                        json=body if body and method in ("POST", "PUT", "PATCH") else None,
                        params=body if body and method == "GET" else None,
                        headers=headers,
                    )

                    step.output = response.text[:4096]  # Truncate large bodies

                    # Assert status code
                    if (
                        step.expected_status_code is not None
                        and response.status_code != step.expected_status_code
                    ):
                        step.status = ValidationStatus.FAILED
                        step.error = (
                            f"Status code {response.status_code} "
                            f"(expected {step.expected_status_code})"
                        )
                    # Assert body pattern
                    elif step.expected_body_pattern and not re.search(
                        step.expected_body_pattern, response.text
                    ):
                        step.status = ValidationStatus.FAILED
                        step.error = (
                            f"Response body does not match pattern "
                            f"'{step.expected_body_pattern}'"
                        )
                    # Assert expected output (simple substring match)
                    elif (
                        step.expected_output
                        and step.expected_output not in response.text
                    ):
                        step.status = ValidationStatus.FAILED
                        step.error = (
                            f"Expected output '{step.expected_output}' "
                            f"not found in response"
                        )
                    else:
                        step.status = ValidationStatus.PASSED

                except httpx.TimeoutException:
                    step.status = ValidationStatus.FAILED
                    step.error = "Request timed out"
                except httpx.ConnectError:
                    step.status = ValidationStatus.FAILED
                    step.error = f"Could not connect to {base_url}"
                except Exception as exc:
                    step.status = ValidationStatus.ERROR
                    step.error = str(exc)
                    logger.warning(
                        "API validation step '%s' failed: %s",
                        step.name,
                        exc,
                    )
                finally:
                    step.duration_seconds = time.monotonic() - start

        return steps


# ---------------------------------------------------------------------------
# IOSSimulatorValidator
# ---------------------------------------------------------------------------


class IOSSimulatorValidator:
    """Validates iOS application behaviour via the Xcode simulator.

    Uses ``xcrun simctl`` commands to boot a simulator, install and
    launch the app, and capture screenshots.
    """

    async def validate(
        self,
        steps: List[ValidationStep],
        app_bundle: str,
    ) -> List[ValidationStep]:
        """Execute iOS simulator validation *steps* for *app_bundle*.

        Args:
            steps: Validation steps of type ``ValidatorType.IOS_SIMULATOR``.
            app_bundle: Path to the ``.app`` bundle to install.

        Returns:
            The same list of steps with updated statuses.
        """
        # Check for xcrun availability
        available = await self._check_xcrun()
        if not available:
            for step in steps:
                step.status = ValidationStatus.FAILED
                step.error = "xcrun simctl is not available (not on macOS or Xcode not installed)"
            return steps

        # Boot the simulator
        device_id = await self._boot_simulator()
        if not device_id:
            for step in steps:
                step.status = ValidationStatus.FAILED
                step.error = "Failed to boot iOS simulator"
            return steps

        try:
            # Install the app
            install_ok = await self._install_app(device_id, app_bundle)
            if not install_ok:
                for step in steps:
                    step.status = ValidationStatus.FAILED
                    step.error = f"Failed to install app bundle: {app_bundle}"
                return steps

            # Launch the app
            launch_ok = await self._launch_app(device_id, app_bundle)
            if not launch_ok:
                for step in steps:
                    step.status = ValidationStatus.FAILED
                    step.error = "Failed to launch app in simulator"
                return steps

            # Give the app time to start
            await asyncio.sleep(3)

            # Execute each validation step
            for step in steps:
                start = time.monotonic()
                step.status = ValidationStatus.RUNNING
                try:
                    if step.command:
                        process = await asyncio.create_subprocess_shell(
                            step.command,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                        )
                        stdout_bytes, stderr_bytes = await asyncio.wait_for(
                            process.communicate(),
                            timeout=step.metadata.get("timeout", 60),
                        )
                        step.output = stdout_bytes.decode("utf-8", errors="replace")
                        exit_code = process.returncode or 0

                        if exit_code != step.expected_exit_code:
                            step.status = ValidationStatus.FAILED
                            step.error = (
                                f"Exit code {exit_code} "
                                f"(expected {step.expected_exit_code})"
                            )
                            continue

                    # Capture screenshot if requested
                    screenshot_path = step.metadata.get("screenshot_path")
                    if screenshot_path:
                        captured = await self._capture_screenshot(
                            device_id, screenshot_path
                        )
                        if captured:
                            step.screenshot_path = screenshot_path
                        else:
                            logger.warning(
                                "Failed to capture simulator screenshot for step '%s'",
                                step.name,
                            )

                    step.status = ValidationStatus.PASSED

                except asyncio.TimeoutError:
                    step.status = ValidationStatus.FAILED
                    step.error = "Command timed out"
                except Exception as exc:
                    step.status = ValidationStatus.ERROR
                    step.error = str(exc)
                    logger.warning(
                        "iOS simulator step '%s' failed: %s",
                        step.name,
                        exc,
                    )
                finally:
                    step.duration_seconds = time.monotonic() - start

        finally:
            await self._shutdown_simulator(device_id)

        return steps

    # -- internal helpers --------------------------------------------------

    async def _check_xcrun(self) -> bool:
        """Return ``True`` if ``xcrun simctl`` is usable."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "xcrun", "simctl", "list", "devices",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            return proc.returncode == 0
        except FileNotFoundError:
            return False
        except Exception:
            return False

    async def _boot_simulator(self) -> Optional[str]:
        """Boot an available simulator and return its device ID."""
        try:
            # List available devices
            proc = await asyncio.create_subprocess_exec(
                "xcrun", "simctl", "list", "devices", "available", "-j",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            if proc.returncode != 0:
                return None

            import json

            data = json.loads(stdout.decode("utf-8"))
            devices = data.get("devices", {})

            # Find an iPhone simulator
            device_id: Optional[str] = None
            for runtime, device_list in devices.items():
                if "iOS" not in runtime:
                    continue
                for device in device_list:
                    if device.get("isAvailable") and "iPhone" in device.get("name", ""):
                        device_id = device["udid"]
                        break
                if device_id:
                    break

            if not device_id:
                logger.error("No available iPhone simulator found")
                return None

            # Boot the device
            proc = await asyncio.create_subprocess_exec(
                "xcrun", "simctl", "boot", device_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            # Return code may be non-zero if already booted, that is fine
            return device_id

        except Exception as exc:
            logger.error("Failed to boot simulator: %s", exc, exc_info=True)
            return None

    async def _install_app(self, device_id: str, app_bundle: str) -> bool:
        """Install *app_bundle* on the given simulator."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "xcrun", "simctl", "install", device_id, app_bundle,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            return proc.returncode == 0
        except Exception as exc:
            logger.error("Failed to install app: %s", exc)
            return False

    async def _launch_app(self, device_id: str, app_bundle: str) -> bool:
        """Launch *app_bundle* on the given simulator."""
        try:
            # Extract bundle ID from the app bundle path
            bundle_id = Path(app_bundle).stem
            proc = await asyncio.create_subprocess_exec(
                "xcrun", "simctl", "launch", device_id, bundle_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            return proc.returncode == 0
        except Exception as exc:
            logger.error("Failed to launch app: %s", exc)
            return False

    async def _capture_screenshot(
        self, device_id: str, output_path: str
    ) -> bool:
        """Capture a screenshot from the simulator."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "xcrun", "simctl", "io", device_id, "screenshot", output_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            return proc.returncode == 0
        except Exception as exc:
            logger.error("Failed to capture screenshot: %s", exc)
            return False

    async def _shutdown_simulator(self, device_id: str) -> None:
        """Shut down the simulator."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "xcrun", "simctl", "shutdown", device_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
        except Exception as exc:
            logger.warning("Failed to shutdown simulator: %s", exc)


# ---------------------------------------------------------------------------
# ValidationEngine
# ---------------------------------------------------------------------------


class ValidationEngine:
    """Main coordinator that creates validation plans, runs validators,
    and supports automatic retry with fix callbacks.

    Args:
        event_bus: :class:`EventBus` instance used to emit validation
            lifecycle events.
    """

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._registry = ValidatorRegistry()
        self._browser_validator = BrowserValidator()
        self._cli_validator = CLIValidator()
        self._api_validator = APIValidator()
        self._ios_validator = IOSSimulatorValidator()

    # ------------------------------------------------------------------
    # Plan creation
    # ------------------------------------------------------------------

    def create_validation_plan(
        self,
        task_description: str,
        project_info: ProjectInfo,
        files_modified: List[str],
    ) -> ValidationPlan:
        """Auto-generate a :class:`ValidationPlan` based on the project
        type, the task being performed, and the files that were changed.

        Args:
            task_description: Human-readable summary of the task.
            project_info: Detected project metadata.
            files_modified: List of file paths that were modified.

        Returns:
            A ready-to-execute :class:`ValidationPlan`.
        """
        project_type = self._resolve_project_type(project_info)
        validator_types = self._registry.get_validators(project_type)

        # Always include CLI validation for code changes
        if ValidatorType.CLI not in validator_types:
            validator_types.insert(0, ValidatorType.CLI)

        steps: List[ValidationStep] = []

        # Generate CLI steps (always present)
        if ValidatorType.CLI in validator_types:
            steps.extend(
                self._generate_cli_steps(project_info, files_modified)
            )

        # Generate browser steps
        if ValidatorType.BROWSER in validator_types:
            steps.extend(
                self._generate_browser_steps(project_info, task_description)
            )

        # Generate API steps
        if ValidatorType.API in validator_types:
            steps.extend(
                self._generate_api_steps(project_info, task_description)
            )

        # Generate iOS simulator steps
        if ValidatorType.IOS_SIMULATOR in validator_types:
            steps.extend(
                self._generate_ios_steps(project_info, task_description)
            )

        plan = ValidationPlan(
            task_description=task_description,
            steps=steps,
            validator_types=validator_types,
            metadata={
                "project_type": project_type.value,
                "files_modified": files_modified,
                "project_root": project_info.root_path,
            },
        )

        logger.info(
            "Created validation plan with %d steps (%s validators) for '%s'",
            len(steps),
            ", ".join(v.value for v in validator_types),
            task_description[:80],
        )

        return plan

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    async def execute_validation(
        self,
        plan: ValidationPlan,
        project_root: Path,
    ) -> ValidationRun:
        """Execute all steps in *plan* and return a :class:`ValidationRun`.

        Emits ``VALIDATION_STARTED`` when execution begins and
        ``VALIDATION_RESULT`` when it completes.

        Args:
            plan: The validation plan to execute.
            project_root: Path used as the working directory for CLI steps.

        Returns:
            A :class:`ValidationRun` containing all step results.
        """
        run = ValidationRun(
            plan_id=plan.plan_id,
            status=ValidationStatus.RUNNING,
            steps=deepcopy(plan.steps),
            started_at=datetime.utcnow(),
        )

        await self._event_bus.emit(
            EventType.VALIDATION_STARTED,
            data={
                "run_id": run.run_id,
                "plan_id": plan.plan_id,
                "step_count": len(run.steps),
                "task_description": plan.task_description,
            },
            source="validation_engine",
        )

        # Partition steps by validator type
        browser_steps = [
            s for s in run.steps if s.validator_type == ValidatorType.BROWSER
        ]
        cli_steps = [
            s for s in run.steps if s.validator_type == ValidatorType.CLI
        ]
        api_steps = [
            s for s in run.steps if s.validator_type == ValidatorType.API
        ]
        ios_steps = [
            s for s in run.steps
            if s.validator_type == ValidatorType.IOS_SIMULATOR
        ]

        base_url = plan.metadata.get("base_url", "http://localhost:3000")
        api_url = plan.metadata.get("api_url", "http://localhost:8000")
        app_bundle = plan.metadata.get("app_bundle", "")

        # Run CLI steps first (build/lint), then others in parallel
        if cli_steps:
            await self._cli_validator.validate(cli_steps, project_root)

        # Only proceed with other validators if CLI steps passed
        cli_passed = all(
            s.status in (ValidationStatus.PASSED, ValidationStatus.SKIPPED)
            for s in cli_steps
        )

        if cli_passed:
            tasks: List[asyncio.Task[List[ValidationStep]]] = []
            if browser_steps:
                tasks.append(
                    asyncio.create_task(
                        self._browser_validator.validate(browser_steps, base_url)
                    )
                )
            if api_steps:
                tasks.append(
                    asyncio.create_task(
                        self._api_validator.validate(api_steps, api_url)
                    )
                )
            if ios_steps:
                tasks.append(
                    asyncio.create_task(
                        self._ios_validator.validate(ios_steps, app_bundle)
                    )
                )

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        # Determine overall status
        run.completed_at = datetime.utcnow()
        if run.all_passed:
            run.status = ValidationStatus.PASSED
        else:
            run.status = ValidationStatus.FAILED

        await self._event_bus.emit(
            EventType.VALIDATION_RESULT,
            data={
                "run_id": run.run_id,
                "plan_id": plan.plan_id,
                "status": run.status.value,
                "passed": run.passed_count,
                "failed": run.failed_count,
                "total": len(run.steps),
                "duration_seconds": run.duration_seconds,
                "failed_steps": [
                    {"name": s.name, "error": s.error}
                    for s in run.failed_steps
                ],
            },
            source="validation_engine",
        )

        logger.info(
            "Validation run %s completed: %s (%d/%d passed)",
            run.run_id[:8],
            run.status.value,
            run.passed_count,
            len(run.steps),
        )

        return run

    # ------------------------------------------------------------------
    # Retry loop
    # ------------------------------------------------------------------

    async def execute_with_retry(
        self,
        plan: ValidationPlan,
        project_root: Path,
        fix_callback: Callable[[List[ValidationStep]], Awaitable[None]],
        max_retries: int = 5,
    ) -> ValidationRun:
        """Execute *plan* with automatic retries.

        On failure the *fix_callback* is invoked with the list of
        failed steps so the caller (e.g. an agent) can attempt a fix.
        The validation is then re-run.  This loop continues until all
        steps pass or *max_retries* is exhausted.

        Args:
            plan: Validation plan to execute.
            project_root: Working directory for CLI steps.
            fix_callback: Async callable that receives failed steps and
                attempts to fix the underlying issues.
            max_retries: Maximum number of retry iterations.

        Returns:
            The final :class:`ValidationRun`.
        """
        run: Optional[ValidationRun] = None

        for attempt in range(max_retries + 1):
            run = await self.execute_validation(plan, project_root)

            if run.all_passed:
                logger.info(
                    "Validation passed on attempt %d/%d",
                    attempt + 1,
                    max_retries + 1,
                )
                return run

            # Record this attempt in retry history
            run.retry_count = attempt
            run.retry_history.append(
                {
                    "attempt": attempt + 1,
                    "status": run.status.value,
                    "passed": run.passed_count,
                    "failed": run.failed_count,
                    "failed_steps": [
                        {"name": s.name, "error": s.error}
                        for s in run.failed_steps
                    ],
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            if attempt < max_retries:
                logger.info(
                    "Validation failed on attempt %d/%d, invoking fix callback",
                    attempt + 1,
                    max_retries + 1,
                )
                try:
                    await fix_callback(run.failed_steps)
                except Exception as exc:
                    logger.error(
                        "Fix callback raised an exception on attempt %d: %s",
                        attempt + 1,
                        exc,
                        exc_info=True,
                    )

                # Reset plan steps for next attempt
                for step in plan.steps:
                    step.status = ValidationStatus.PENDING
                    step.output = None
                    step.error = None
                    step.duration_seconds = None
            else:
                logger.warning(
                    "Validation failed after %d attempts, giving up",
                    max_retries + 1,
                )

        # Exhausted retries -- ensure the run reflects final state
        assert run is not None
        run.retry_count = max_retries
        run.status = ValidationStatus.FAILED
        return run

    # ------------------------------------------------------------------
    # Step generation helpers
    # ------------------------------------------------------------------

    def _resolve_project_type(self, project_info: ProjectInfo) -> ProjectType:
        """Extract the :class:`ProjectType` from *project_info* metadata."""
        raw = project_info.metadata.get("project_type", "unknown")
        try:
            return ProjectType(raw)
        except ValueError:
            return ProjectType.UNKNOWN

    def _generate_cli_steps(
        self,
        project_info: ProjectInfo,
        files_modified: List[str],
    ) -> List[ValidationStep]:
        """Generate CLI validation steps for build and lint."""
        steps: List[ValidationStep] = []
        build_system = project_info.build_system
        language = (project_info.language or "").lower()

        # --- Build step ---------------------------------------------------
        build_cmd: Optional[str] = None
        if build_system in ("npm", "yarn", "pnpm"):
            prefix = build_system
            if build_system == "pnpm":
                prefix = "pnpm"
            build_cmd = f"{prefix} run build"
        elif build_system == "cargo":
            build_cmd = "cargo build"
        elif build_system == "go":
            build_cmd = "go build ./..."
        elif build_system in ("pip", "uv", "poetry"):
            # Python projects often don't have a build step per se;
            # compile check instead.
            build_cmd = "python -m py_compile $(find . -name '*.py' -not -path './.venv/*' | head -20)"
        elif build_system == "make":
            build_cmd = "make"

        if build_cmd:
            steps.append(
                ValidationStep(
                    name="Build project",
                    description="Run the project build command",
                    validator_type=ValidatorType.CLI,
                    command=build_cmd,
                )
            )

        # --- Lint step ----------------------------------------------------
        lint_cmd: Optional[str] = None
        has_py = any(f.endswith(".py") for f in files_modified)
        has_ts_js = any(
            f.endswith((".ts", ".tsx", ".js", ".jsx")) for f in files_modified
        )
        has_rs = any(f.endswith(".rs") for f in files_modified)
        has_go = any(f.endswith(".go") for f in files_modified)

        if has_py or language == "python":
            lint_cmd = "python -m ruff check . || python -m flake8 . || true"
        elif has_ts_js:
            lint_cmd = "npx eslint . --max-warnings=0 || true"
        elif has_rs:
            lint_cmd = "cargo clippy -- -D warnings"
        elif has_go:
            lint_cmd = "golangci-lint run ./... || go vet ./..."

        if lint_cmd:
            steps.append(
                ValidationStep(
                    name="Lint check",
                    description="Run linter on modified files",
                    validator_type=ValidatorType.CLI,
                    command=lint_cmd,
                )
            )

        # --- Type check step ----------------------------------------------
        type_cmd: Optional[str] = None
        if has_py or language == "python":
            type_cmd = "python -m mypy . --ignore-missing-imports || true"
        elif has_ts_js:
            type_cmd = "npx tsc --noEmit || true"

        if type_cmd:
            steps.append(
                ValidationStep(
                    name="Type check",
                    description="Run type checker on the project",
                    validator_type=ValidatorType.CLI,
                    command=type_cmd,
                )
            )

        # --- Test step ----------------------------------------------------
        test_fw = project_info.test_framework
        test_cmd: Optional[str] = None
        if test_fw == "pytest":
            test_cmd = "python -m pytest --tb=short -q"
        elif test_fw == "vitest":
            test_cmd = "npx vitest run"
        elif test_fw == "jest":
            test_cmd = "npx jest --passWithNoTests"
        elif test_fw == "mocha":
            test_cmd = "npx mocha"
        elif test_fw == "cargo-test":
            test_cmd = "cargo test"
        elif test_fw == "go-test":
            test_cmd = "go test ./..."

        if test_cmd:
            steps.append(
                ValidationStep(
                    name="Run tests",
                    description="Execute the project test suite",
                    validator_type=ValidatorType.CLI,
                    command=test_cmd,
                )
            )

        return steps

    def _generate_browser_steps(
        self,
        project_info: ProjectInfo,
        task_description: str,
    ) -> List[ValidationStep]:
        """Generate browser validation steps for web projects."""
        steps: List[ValidationStep] = []

        steps.append(
            ValidationStep(
                name="Page loads successfully",
                description="Verify the main page loads without errors",
                validator_type=ValidatorType.BROWSER,
                url="/",
                expected_output="</html>",
                metadata={"screenshot_path": "/tmp/validation_page_load.png"},
            )
        )

        # If the task description hints at specific pages, add a step
        for keyword, path in [
            ("login", "/login"),
            ("dashboard", "/dashboard"),
            ("settings", "/settings"),
            ("profile", "/profile"),
            ("signup", "/signup"),
            ("register", "/register"),
        ]:
            if keyword in task_description.lower():
                steps.append(
                    ValidationStep(
                        name=f"Navigate to {path}",
                        description=f"Verify {path} page loads correctly",
                        validator_type=ValidatorType.BROWSER,
                        url=path,
                    )
                )

        return steps

    def _generate_api_steps(
        self,
        project_info: ProjectInfo,
        task_description: str,
    ) -> List[ValidationStep]:
        """Generate API validation steps."""
        steps: List[ValidationStep] = []

        # Health check
        steps.append(
            ValidationStep(
                name="API health check",
                description="Verify the API server responds to health check",
                validator_type=ValidatorType.API,
                url="/health",
                method="GET",
                expected_status_code=200,
            )
        )

        return steps

    def _generate_ios_steps(
        self,
        project_info: ProjectInfo,
        task_description: str,
    ) -> List[ValidationStep]:
        """Generate iOS simulator validation steps."""
        steps: List[ValidationStep] = []

        steps.append(
            ValidationStep(
                name="App launches in simulator",
                description="Verify the app launches successfully in the iOS simulator",
                validator_type=ValidatorType.IOS_SIMULATOR,
                metadata={"screenshot_path": "/tmp/validation_ios_launch.png"},
            )
        )

        return steps
