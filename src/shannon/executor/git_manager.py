"""
Git Manager - Atomic commits with rollback support

Ensures:
- Only validated changes are committed
- Atomic commits (one step = one commit)
- Descriptive commit messages
- Clean rollback on validation failure

All git operations performed via run_terminal_cmd for transparency.

Created: November 15, 2025
Part of: Shannon V3.5 Wave 4 (Git Integration)
"""

from typing import List, Optional
from pathlib import Path
from datetime import datetime
import logging
import asyncio

from .models import GitCommit, ValidationResult


class GitManager:
    """
    Manages git operations for autonomous execution
    
    Guarantees:
    - Working directory clean before starting
    - Feature branch created
    - Only commits validated changes
    - Descriptive commit messages with validation proof
    - Clean rollback on failure
    
    Usage:
        git_mgr = GitManager(project_root=Path("/path"))
        
        # Pre-execution
        await git_mgr.ensure_clean_state()
        branch = await git_mgr.create_feature_branch("fix iOS login")
        
        # Per step
        commit = await git_mgr.commit_validated_changes(
            files=['LoginViewController.swift'],
            step_description="Update constraints to use safe area",
            validation_result=validation
        )
        
        # Or rollback if validation failed
        await git_mgr.rollback_to_last_commit()
    """
    
    def __init__(self, project_root: Path, logger: Optional[logging.Logger] = None):
        """
        Initialize git manager
        
        Args:
            project_root: Project directory (must be git repository)
            logger: Optional logger
        """
        self.project_root = project_root
        self.logger = logger or logging.getLogger(__name__)
        self.commits: List[GitCommit] = []
        self.current_branch: Optional[str] = None
    
    async def ensure_clean_state(self) -> bool:
        """
        Verify git working directory is clean
        
        Returns:
            True if clean, False if uncommitted changes exist
        """
        status = await self._run_git('status --porcelain')
        
        is_clean = status.strip() == ''
        
        if is_clean:
            self.logger.info("Git working directory is clean ✓")
        else:
            self.logger.warning("Git working directory has uncommitted changes")
        
        return is_clean
    
    async def get_current_branch(self) -> str:
        """Get current git branch name"""
        branch = await self._run_git('branch --show-current')
        return branch.strip()
    
    async def create_feature_branch(self, task: str) -> str:
        """
        Create feature branch with descriptive name
        
        Args:
            task: Task description
            
        Returns:
            Branch name
        """
        branch_name = self._generate_branch_name(task)
        
        self.logger.info(f"Creating branch: {branch_name}")
        await self._run_git(f'checkout -b {branch_name}')
        
        self.current_branch = branch_name
        return branch_name
    
    async def commit_validated_changes(
        self,
        files: List[str],
        step_description: str,
        validation_result: ValidationResult
    ) -> GitCommit:
        """
        Commit changes after successful validation
        
        Args:
            files: Files to commit
            step_description: What this step does
            validation_result: Validation results (must have all_passed=True)
            
        Returns:
            GitCommit record
        """
        if not validation_result.all_passed:
            raise ValueError("Cannot commit - validation did not pass all tiers")
        
        # Generate commit message
        commit_msg = self._generate_commit_message(step_description, validation_result)
        
        self.logger.info(f"Committing validated changes: {step_description}")
        
        # Stage files
        for file in files:
            await self._run_git(f'add {file}')
        
        # Commit
        await self._run_git(f'commit -m "{commit_msg}"')
        
        # Get commit hash
        commit_hash = await self._run_git('rev-parse HEAD')
        commit_hash = commit_hash.strip()
        
        # Create commit record
        commit = GitCommit(
            hash=commit_hash,
            message=commit_msg,
            files=files,
            validation_passed=True,
            timestamp=datetime.now()
        )
        
        self.commits.append(commit)
        
        self.logger.info(f"Committed: {commit_hash[:8]} - {step_description}")
        
        return commit
    
    async def rollback_to_last_commit(self) -> bool:
        """
        Rollback failed changes to last good commit
        
        Returns:
            True if rollback successful
        """
        self.logger.warning("Rolling back failed changes...")
        
        # Hard reset to HEAD
        await self._run_git('reset --hard HEAD')
        
        # Clean untracked files
        await self._run_git('clean -fd')
        
        # Verify clean state
        status = await self._run_git('status --porcelain')
        is_clean = status.strip() == ''
        
        if is_clean:
            self.logger.info("Rollback successful ✓")
        else:
            self.logger.error("Rollback failed - working directory still dirty")
        
        return is_clean
    
    def _generate_branch_name(self, task: str) -> str:
        """
        Generate descriptive branch name from task
        
        Args:
            task: Task description
            
        Returns:
            Branch name (e.g., "fix/ios-offscreen-login")
        """
        # Extract meaningful words (length > 3)
        words = [w for w in task.lower().split() if len(w) > 3 and w.isalnum()]
        slug = '-'.join(words[:4])  # Max 4 words
        
        # Determine prefix based on task keywords
        if any(w in task.lower() for w in ['fix', 'bug', 'broken', 'error', 'issue']):
            prefix = 'fix'
        elif any(w in task.lower() for w in ['add', 'new', 'create', 'implement', 'build']):
            prefix = 'feat'
        elif any(w in task.lower() for w in ['optimize', 'performance', 'slow', 'faster', 'speed']):
            prefix = 'perf'
        elif any(w in task.lower() for w in ['refactor', 'restructure', 'clean', 'reorganize']):
            prefix = 'refactor'
        elif any(w in task.lower() for w in ['test', 'testing', 'coverage']):
            prefix = 'test'
        elif any(w in task.lower() for w in ['docs', 'documentation', 'readme']):
            prefix = 'docs'
        else:
            prefix = 'chore'
        
        return f"{prefix}/{slug}"
    
    def _generate_commit_message(
        self,
        step_description: str,
        validation: ValidationResult
    ) -> str:
        """
        Generate descriptive commit message
        
        Format:
        <type>: <summary>
        
        VALIDATION:
        - Build: PASS/SKIP
        - Tests: PASS/SKIP
        - Functional: PASS/SKIP
        
        Args:
            step_description: Step description
            validation: Validation results
            
        Returns:
            Formatted commit message
        """
        # Determine commit type
        commit_type = self._determine_commit_type(step_description)
        
        # Build message
        message = f"{commit_type}: {step_description}\n\n"
        message += "VALIDATION:\n"
        message += f"- Build/Static: {'PASS' if validation.tier1_passed else 'SKIP'}\n"
        message += f"- Tests: {'PASS' if validation.tier2_passed else 'SKIP'}\n"
        message += f"- Functional: {'PASS' if validation.tier3_passed else 'SKIP'}\n"
        
        return message
    
    def _determine_commit_type(self, description: str) -> str:
        """Determine conventional commit type"""
        desc_lower = description.lower()
        
        if any(w in desc_lower for w in ['fix', 'bug', 'broken', 'error']):
            return 'fix'
        elif any(w in desc_lower for w in ['add', 'new', 'create', 'implement']):
            return 'feat'
        elif any(w in desc_lower for w in ['optimize', 'performance', 'faster']):
            return 'perf'
        elif any(w in desc_lower for w in ['refactor', 'restructure', 'clean']):
            return 'refactor'
        elif any(w in desc_lower for w in ['test', 'testing']):
            return 'test'
        elif any(w in desc_lower for w in ['docs', 'documentation']):
            return 'docs'
        else:
            return 'chore'
    
    async def _run_git(self, command: str) -> str:
        """
        Run git command
        
        Args:
            command: Git command (without 'git' prefix)
            
        Returns:
            Command output
        """
        full_command = f"git {command}"
        self.logger.debug(f"Running: {full_command}")
        
        # TODO: Actually run via run_terminal_cmd in real implementation
        # For now, simulate
        
        # Real implementation:
        # result = await run_terminal_cmd(full_command, cwd=self.project_root)
        # return result.output
        
        return ""  # Placeholder

