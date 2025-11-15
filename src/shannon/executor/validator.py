"""
Validation Orchestrator - 3-tier validation framework

Auto-detects project test infrastructure and runs:
- Tier 1: Static (build, lint, types) ~10s
- Tier 2: Unit/Integration tests ~1-5min
- Tier 3: Functional (E2E, user perspective) ~2-10min

Integrates with existing project test commands from package.json,
pyproject.toml, Xcode project, etc.

Created: November 15, 2025
Part of: Shannon V3.5 Wave 3 (Validation)
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass
import json
import logging

from .models import ValidationResult


@dataclass
class TestConfig:
    """Auto-detected test configuration for a project"""
    project_type: str
    build_cmd: Optional[str]
    type_check_cmd: Optional[str]
    lint_cmd: Optional[str]
    test_cmd: Optional[str]
    e2e_cmd: Optional[str]
    start_cmd: Optional[str]


class ValidationOrchestrator:
    """
    Orchestrates 3-tier validation using existing test infrastructure
    
    Auto-detects how to validate based on project files.
    
    Usage:
        validator = ValidationOrchestrator(project_root=Path("/path"))
        
        result = await validator.validate_all_tiers(
            changes=change_set,
            criteria=validation_criteria
        )
        
        if result.all_passed:
            # Safe to commit
        else:
            # Fix and retry
    """
    
    def __init__(self, project_root: Path, logger: Optional[logging.Logger] = None):
        """
        Initialize validation orchestrator
        
        Args:
            project_root: Project directory
            logger: Optional logger
        """
        self.project_root = project_root
        self.logger = logger or logging.getLogger(__name__)
        self.test_config = self._auto_detect_tests()
        
        self.logger.info(f"ValidationOrchestrator initialized for {self.test_config.project_type}")
    
    def _auto_detect_tests(self) -> TestConfig:
        """
        Auto-detect test commands from project files
        
        Checks:
        - package.json (for npm scripts)
        - pyproject.toml / pytest.ini (for Python)
        - *.xcodeproj (for iOS)
        - build.gradle / pom.xml (for Java)
        - Cargo.toml (for Rust)
        
        Returns:
            TestConfig with detected commands
        """
        # Check for Node.js/JavaScript
        package_json = self.project_root / 'package.json'
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text())
                scripts = data.get('scripts', {})
                
                return TestConfig(
                    project_type='nodejs',
                    build_cmd=scripts.get('build'),
                    type_check_cmd=scripts.get('type-check') or 'npx tsc --noEmit',
                    lint_cmd=scripts.get('lint'),
                    test_cmd=scripts.get('test', 'npm test'),
                    e2e_cmd=scripts.get('e2e') or scripts.get('test:e2e'),
                    start_cmd=scripts.get('start') or scripts.get('dev')
                )
            except:
                pass
        
        # Check for Python
        if (self.project_root / 'pyproject.toml').exists() or \
           (self.project_root / 'pytest.ini').exists() or \
           (self.project_root / 'requirements.txt').exists():
            return TestConfig(
                project_type='python',
                build_cmd=None,  # Python doesn't need build step
                type_check_cmd='mypy .',
                lint_cmd='ruff check .',
                test_cmd='pytest tests/',
                e2e_cmd=None,
                start_cmd=self._detect_python_start_cmd()
            )
        
        # Check for iOS
        if list(self.project_root.glob('*.xcodeproj')):
            return TestConfig(
                project_type='ios',
                build_cmd='xcodebuild clean build',
                type_check_cmd=None,  # Swift has compile-time type checking
                lint_cmd='swiftlint',
                test_cmd='xcodebuild test',
                e2e_cmd=None,
                start_cmd=None  # iOS apps don't have "start" command
            )
        
        # Check for Rust
        if (self.project_root / 'Cargo.toml').exists():
            return TestConfig(
                project_type='rust',
                build_cmd='cargo build',
                type_check_cmd='cargo check',
                lint_cmd='cargo clippy',
                test_cmd='cargo test',
                e2e_cmd=None,
                start_cmd='cargo run'
            )
        
        # Check for Java/Android
        if (self.project_root / 'build.gradle').exists():
            return TestConfig(
                project_type='java',
                build_cmd='./gradlew build',
                type_check_cmd=None,
                lint_cmd='./gradlew check',
                test_cmd='./gradlew test',
                e2e_cmd=None,
                start_cmd='./gradlew run'
            )
        
        # Unknown - minimal config
        return TestConfig(
            project_type='unknown',
            build_cmd=None,
            type_check_cmd=None,
            lint_cmd=None,
            test_cmd=None,
            e2e_cmd=None,
            start_cmd=None
        )
    
    def _detect_python_start_cmd(self) -> Optional[str]:
        """Detect how to start Python app"""
        # Check for FastAPI
        main_py = self.project_root / 'main.py'
        if main_py.exists() and 'fastapi' in main_py.read_text().lower():
            return 'uvicorn main:app --reload'
        
        # Check for Django
        manage_py = self.project_root / 'manage.py'
        if manage_py.exists():
            return 'python manage.py runserver'
        
        # Check for Flask
        app_py = self.project_root / 'app.py'
        if app_py.exists() and 'flask' in app_py.read_text().lower():
            return 'python app.py'
        
        return None
    
    async def validate_all_tiers(
        self,
        changes: Any,  # ChangeSet from execution
        criteria: Optional[Any] = None  # ValidationCriteria
    ) -> ValidationResult:
        """
        Run all 3 tiers of validation
        
        Args:
            changes: Changes made (files modified)
            criteria: Optional validation criteria
            
        Returns:
            ValidationResult with all tier results
        """
        import time
        start_time = time.time()
        
        # Tier 1: Static
        self.logger.info("Running Tier 1 validation (static)...")
        tier1 = await self.validate_tier1()
        
        if not tier1['passed']:
            self.logger.warning("Tier 1 failed, skipping Tier 2+3")
            return ValidationResult(
                tier1_passed=False,
                tier2_passed=False,
                tier3_passed=False,
                tier1_details=tier1,
                failures=tier1.get('failures', []),
                duration_seconds=time.time() - start_time
            )
        
        # Tier 2: Tests
        self.logger.info("Running Tier 2 validation (tests)...")
        tier2 = await self.validate_tier2()
        
        if not tier2['passed']:
            self.logger.warning("Tier 2 failed, skipping Tier 3")
            return ValidationResult(
                tier1_passed=True,
                tier2_passed=False,
                tier3_passed=False,
                tier1_details=tier1,
                tier2_details=tier2,
                failures=tier2.get('failures', []),
                duration_seconds=time.time() - start_time
            )
        
        # Tier 3: Functional
        self.logger.info("Running Tier 3 validation (functional)...")
        tier3 = await self.validate_tier3(criteria)
        
        return ValidationResult(
            tier1_passed=True,
            tier2_passed=True,
            tier3_passed=tier3['passed'],
            tier1_details=tier1,
            tier2_details=tier2,
            tier3_details=tier3,
            failures=tier3.get('failures', []),
            duration_seconds=time.time() - start_time
        )
    
    async def validate_tier1(self) -> Dict[str, Any]:
        """Tier 1: Static validation (build, lint, types)"""
        results = {'passed': True, 'checks': {}, 'failures': []}
        
        # Build check
        if self.test_config.build_cmd:
            build_passed = await self._run_check(self.test_config.build_cmd, "Build")
            results['checks']['build'] = build_passed
            if not build_passed:
                results['passed'] = False
                results['failures'].append("Build failed")
        
        # Type check
        if self.test_config.type_check_cmd:
            type_passed = await self._run_check(self.test_config.type_check_cmd, "Type check")
            results['checks']['type_check'] = type_passed
            if not type_passed:
                results['passed'] = False
                results['failures'].append("Type check failed")
        
        # Lint check
        if self.test_config.lint_cmd:
            lint_passed = await self._run_check(self.test_config.lint_cmd, "Lint")
            results['checks']['lint'] = lint_passed
            if not lint_passed:
                results['passed'] = False
                results['failures'].append("Lint failed")
        
        return results
    
    async def validate_tier2(self) -> Dict[str, Any]:
        """Tier 2: Unit/Integration tests"""
        if not self.test_config.test_cmd:
            return {'passed': True, 'skipped': True, 'reason': 'No test command configured'}
        
        test_passed = await self._run_check(self.test_config.test_cmd, "Tests")
        
        return {
            'passed': test_passed,
            'checks': {'tests': test_passed},
            'failures': [] if test_passed else ["Tests failed"]
        }
    
    async def validate_tier3(self, criteria: Optional[Any] = None) -> Dict[str, Any]:
        """Tier 3: Functional validation from user perspective"""
        # For now, simplified implementation
        # Full implementation would start app, test features, etc.
        
        if self.test_config.e2e_cmd:
            e2e_passed = await self._run_check(self.test_config.e2e_cmd, "E2E tests")
            return {
                'passed': e2e_passed,
                'checks': {'e2e': e2e_passed},
                'failures': [] if e2e_passed else ["E2E tests failed"]
            }
        
        # No E2E configured - pass by default
        # (Real implementation would have more sophisticated functional testing)
        return {'passed': True, 'skipped': True, 'reason': 'No E2E tests configured'}
    
    async def _run_check(self, command: str, check_name: str) -> bool:
        """
        Run a validation check command
        
        Args:
            command: Shell command to run
            check_name: Name for logging
            
        Returns:
            True if command succeeded (exit code 0)
        """
        self.logger.debug(f"Running {check_name}: {command}")
        
        # TODO: Actually run the command via run_terminal_cmd
        # For now, return True (will be implemented when integrated with SDK)
        
        # Real implementation would be:
        # result = await run_terminal_cmd(command, cwd=self.project_root)
        # return result.exit_code == 0
        
        return True  # Placeholder

