"""
Dynamic skill and plugin loader for the TUI Agent Orchestration System.

Discovers, loads, and manages skills and plugins from the filesystem.
Skills define behavioral directives injected into agent system prompts.
Plugins define processing hooks that execute at specific pipeline phases.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Attempt to import yaml; fall back gracefully if unavailable.
try:
    import yaml  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


class PluginPhase(Enum):
    """Pipeline phases where plugins can hook in."""

    PRE_PLANNING = "pre_planning"
    POST_PLANNING = "post_planning"
    PRE_EXECUTION = "pre_execution"
    POST_EXECUTION = "post_execution"
    PRE_VALIDATION = "pre_validation"
    POST_VALIDATION = "post_validation"
    ON_ERROR = "on_error"
    ON_COMPLETE = "on_complete"


@dataclass
class SkillDefinition:
    """
    Represents a discovered skill.

    Attributes:
        name: Unique skill identifier (e.g. ``"code-quality"``).
        description: Human-readable description of the skill.
        trigger_conditions: Keywords or patterns that activate this skill.
        directives: List of directive strings injected into agent prompts.
        source_path: Filesystem path from which the skill was loaded.
        metadata: Arbitrary extra data parsed from the skill file.
    """

    name: str
    description: str = ""
    trigger_conditions: List[str] = field(default_factory=list)
    directives: List[str] = field(default_factory=list)
    source_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginDefinition:
    """
    Represents a discovered plugin.

    Attributes:
        name: Unique plugin identifier.
        phase: Pipeline phase at which this plugin executes.
        description: Human-readable description.
        handler_path: Dotted Python import path to the handler callable.
        priority: Execution priority within the phase (lower runs first).
        source_path: Filesystem path from which the plugin was loaded.
        enabled: Whether the plugin is currently active.
        config: Extra plugin-specific configuration.
    """

    name: str
    phase: PluginPhase = PluginPhase.POST_EXECUTION
    description: str = ""
    handler_path: str = ""
    priority: int = 100
    source_path: Optional[str] = None
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_YAML_EXTENSIONS = {".yaml", ".yml"}
_ALWAYS_ACTIVE_SKILLS = {"prompt-engineering", "code-quality"}

# Simple keyword normalisation pattern (strip non-alphanumeric, lowercase)
_KEYWORD_RE = re.compile(r"[^a-z0-9]+")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> Dict[str, Any]:
    """Load a YAML file and return its contents as a dict.

    Falls back to a minimal manual parser when PyYAML is unavailable so the
    loader can still function in environments without the dependency.
    """
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(text)
        return data if isinstance(data, dict) else {}
    # Very basic fallback: treat each ``key: value`` line as a string entry.
    result: Dict[str, Any] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()
    return result


def _normalise(text: str) -> str:
    """Lowercase and strip non-alphanumeric characters for fuzzy matching."""
    return _KEYWORD_RE.sub("", text.lower())


def _parse_skill_from_yaml(path: Path) -> Optional[SkillDefinition]:
    """Parse a YAML file into a ``SkillDefinition``."""
    try:
        data = _load_yaml(path)
    except Exception:
        logger.warning("Failed to parse skill YAML: %s", path, exc_info=True)
        return None

    if not data:
        return None

    name = data.get("name", path.stem)
    description = data.get("description", "")
    triggers = data.get("trigger_conditions", data.get("triggers", []))
    if isinstance(triggers, str):
        triggers = [t.strip() for t in triggers.split(",") if t.strip()]
    directives = data.get("directives", [])
    if isinstance(directives, str):
        directives = [d.strip() for d in directives.split("\n") if d.strip()]

    # Everything else goes into metadata.
    reserved_keys = {"name", "description", "trigger_conditions", "triggers", "directives"}
    metadata = {k: v for k, v in data.items() if k not in reserved_keys}

    return SkillDefinition(
        name=str(name),
        description=str(description),
        trigger_conditions=[str(t) for t in triggers],
        directives=[str(d) for d in directives],
        source_path=str(path),
        metadata=metadata,
    )


def _parse_skill_from_markdown(path: Path) -> Optional[SkillDefinition]:
    """Parse a Markdown SKILL.md file into a ``SkillDefinition``.

    This supports the existing ``.claude/skills/<name>/SKILL.md`` convention
    where the file content serves as the directive text.
    """
    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        logger.warning("Failed to read skill markdown: %s", path, exc_info=True)
        return None

    # Derive skill name from parent directory.
    name = path.parent.name if path.parent.name else path.stem

    # Extract a description from the first non-empty line.
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    description = lines[0].lstrip("#").strip() if lines else name

    # The entire file content acts as a single directive block.
    directives = [content] if content.strip() else []

    # Derive trigger conditions from directory name tokens.
    trigger_tokens = [t for t in name.replace("-", " ").replace("_", " ").split() if t]

    return SkillDefinition(
        name=name,
        description=description,
        trigger_conditions=trigger_tokens,
        directives=directives,
        source_path=str(path),
    )


def _parse_plugin_from_yaml(path: Path) -> Optional[PluginDefinition]:
    """Parse a YAML file into a ``PluginDefinition``."""
    try:
        data = _load_yaml(path)
    except Exception:
        logger.warning("Failed to parse plugin YAML: %s", path, exc_info=True)
        return None

    if not data:
        return None

    phase_str = data.get("phase", PluginPhase.POST_EXECUTION.value)
    try:
        phase = PluginPhase(phase_str)
    except ValueError:
        logger.warning(
            "Unknown plugin phase '%s' in %s, defaulting to POST_EXECUTION",
            phase_str,
            path,
        )
        phase = PluginPhase.POST_EXECUTION

    priority_raw = data.get("priority", 100)
    try:
        priority = int(priority_raw)
    except (TypeError, ValueError):
        priority = 100

    reserved_keys = {"name", "phase", "description", "handler_path", "priority", "enabled"}
    config = {k: v for k, v in data.items() if k not in reserved_keys}

    return PluginDefinition(
        name=str(data.get("name", path.stem)),
        phase=phase,
        description=str(data.get("description", "")),
        handler_path=str(data.get("handler_path", "")),
        priority=priority,
        source_path=str(path),
        enabled=bool(data.get("enabled", True)),
        config=config,
    )


def _parse_plugin_from_python(path: Path) -> Optional[PluginDefinition]:
    """Extract plugin metadata from a Python plugin file.

    Looks for module-level constants ``PLUGIN_NAME``, ``PLUGIN_PHASE``, etc.
    Falls back to sane defaults derived from the filename.
    """
    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        logger.warning("Failed to read plugin Python file: %s", path, exc_info=True)
        return None

    def _extract(constant: str, default: str = "") -> str:
        pattern = rf'^{constant}\s*=\s*["\'](.+?)["\']'
        match = re.search(pattern, content, re.MULTILINE)
        return match.group(1) if match else default

    name = _extract("PLUGIN_NAME", path.stem)
    phase_str = _extract("PLUGIN_PHASE", PluginPhase.POST_EXECUTION.value)
    description = _extract("PLUGIN_DESCRIPTION", "")
    handler_path = _extract("PLUGIN_HANDLER", "")
    priority_str = _extract("PLUGIN_PRIORITY", "100")

    try:
        phase = PluginPhase(phase_str)
    except ValueError:
        phase = PluginPhase.POST_EXECUTION

    try:
        priority = int(priority_str)
    except ValueError:
        priority = 100

    # If no explicit handler path, derive from module path.
    if not handler_path:
        handler_path = str(path)

    return PluginDefinition(
        name=name,
        phase=phase,
        description=description,
        handler_path=handler_path,
        priority=priority,
        source_path=str(path),
    )


# ---------------------------------------------------------------------------
# SkillLoader
# ---------------------------------------------------------------------------


class SkillLoader:
    """Dynamic skill and plugin loader.

    Scans designated directories for skill definitions (YAML or Markdown)
    and plugin definitions (YAML or Python), caches the results, and
    provides activation/filtering helpers used by the orchestration engine.

    Args:
        skills_dir: Root directory containing skill definition files.
        plugins_dir: Root directory containing plugin definition files.
    """

    def __init__(self, skills_dir: Path, plugins_dir: Path) -> None:
        self._skills_dir = skills_dir
        self._plugins_dir = plugins_dir

        self._skills: List[SkillDefinition] = []
        self._plugins: List[PluginDefinition] = []
        self._loaded = False

        logger.info(
            "SkillLoader initialised (skills=%s, plugins=%s)",
            skills_dir,
            plugins_dir,
        )

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def discover_skills(self) -> List[SkillDefinition]:
        """Scan *skills_dir* for skill definitions.

        Supports:
        - ``.yaml`` / ``.yml`` files at any depth.
        - ``SKILL.md`` files following the ``.claude/skills/<name>/SKILL.md``
          convention.

        Returns:
            All successfully parsed :class:`SkillDefinition` objects.
        """
        skills: List[SkillDefinition] = []

        if not self._skills_dir.is_dir():
            logger.warning("Skills directory does not exist: %s", self._skills_dir)
            return skills

        # Discover YAML skill files.
        for ext in ("*.yaml", "*.yml"):
            for path in self._skills_dir.rglob(ext):
                skill = _parse_skill_from_yaml(path)
                if skill is not None:
                    skills.append(skill)
                    logger.debug("Discovered YAML skill: %s (%s)", skill.name, path)

        # Discover Markdown-based skills (SKILL.md convention).
        for path in self._skills_dir.rglob("SKILL.md"):
            skill = _parse_skill_from_markdown(path)
            if skill is not None:
                # Avoid duplicates if a YAML and SKILL.md coexist.
                if not any(s.name == skill.name for s in skills):
                    skills.append(skill)
                    logger.debug("Discovered Markdown skill: %s (%s)", skill.name, path)

        self._skills = skills
        logger.info("Discovered %d skill(s)", len(skills))
        return list(skills)

    def discover_plugins(self) -> List[PluginDefinition]:
        """Scan *plugins_dir* for plugin definitions.

        Supports ``.yaml``/``.yml`` and ``.py`` files.  Returns plugins
        sorted by phase name then priority (ascending).
        """
        plugins: List[PluginDefinition] = []

        if not self._plugins_dir.is_dir():
            logger.warning("Plugins directory does not exist: %s", self._plugins_dir)
            return plugins

        # YAML plugins.
        for ext in ("*.yaml", "*.yml"):
            for path in self._plugins_dir.rglob(ext):
                plugin = _parse_plugin_from_yaml(path)
                if plugin is not None:
                    plugins.append(plugin)
                    logger.debug("Discovered YAML plugin: %s (%s)", plugin.name, path)

        # Python plugins.
        for path in self._plugins_dir.rglob("*.py"):
            if path.name.startswith("_"):
                continue
            plugin = _parse_plugin_from_python(path)
            if plugin is not None:
                plugins.append(plugin)
                logger.debug("Discovered Python plugin: %s (%s)", plugin.name, path)

        # Sort by phase name then priority.
        plugins.sort(key=lambda p: (p.phase.value, p.priority))

        self._plugins = plugins
        logger.info("Discovered %d plugin(s)", len(plugins))
        return list(plugins)

    # ------------------------------------------------------------------
    # Activation & filtering
    # ------------------------------------------------------------------

    def activate_skills(
        self,
        task_description: str,
        project_type: Optional[str] = None,
    ) -> List[SkillDefinition]:
        """Identify which skills should be active for a given task.

        Matching logic:
        1. Skills whose *trigger_conditions* overlap with keywords in the
           task description or project type are activated.
        2. Skills named ``"prompt-engineering"`` or ``"code-quality"`` are
           **always** activated when present.

        Args:
            task_description: Free-text description of the current task.
            project_type: Optional project type hint (e.g. ``"api_server"``).

        Returns:
            List of activated :class:`SkillDefinition` objects.
        """
        if not self._skills:
            self.discover_skills()

        normalised_task = _normalise(task_description)
        normalised_project = _normalise(project_type) if project_type else ""

        activated: List[SkillDefinition] = []
        seen_names: set[str] = set()

        for skill in self._skills:
            if skill.name in seen_names:
                continue

            # Always-on skills.
            if skill.name in _ALWAYS_ACTIVE_SKILLS:
                activated.append(skill)
                seen_names.add(skill.name)
                logger.debug("Always-active skill activated: %s", skill.name)
                continue

            # Keyword matching against trigger conditions.
            matched = False
            for trigger in skill.trigger_conditions:
                normalised_trigger = _normalise(trigger)
                if not normalised_trigger:
                    continue
                if normalised_trigger in normalised_task:
                    matched = True
                    break
                if normalised_project and normalised_trigger in normalised_project:
                    matched = True
                    break

            if matched:
                activated.append(skill)
                seen_names.add(skill.name)
                logger.debug("Skill activated by trigger match: %s", skill.name)

        logger.info(
            "Activated %d skill(s) for task (total available: %d)",
            len(activated),
            len(self._skills),
        )
        return activated

    def get_plugin_pipeline(self, phase: PluginPhase) -> List[PluginDefinition]:
        """Return enabled plugins for *phase*, sorted by priority.

        Args:
            phase: The pipeline phase to retrieve plugins for.

        Returns:
            List of enabled :class:`PluginDefinition` objects for the phase.
        """
        if not self._plugins:
            self.discover_plugins()

        pipeline = [
            p
            for p in self._plugins
            if p.phase == phase and p.enabled
        ]
        pipeline.sort(key=lambda p: p.priority)

        logger.debug(
            "Plugin pipeline for phase %s: %d plugin(s)",
            phase.value,
            len(pipeline),
        )
        return pipeline

    # ------------------------------------------------------------------
    # Directive generation
    # ------------------------------------------------------------------

    def generate_skill_directives(
        self,
        active_skills: List[SkillDefinition],
    ) -> str:
        """Compile all directives from *active_skills* into a single string.

        Each skill's directives are grouped under a header for clarity in
        the resulting system prompt.

        Args:
            active_skills: Skills whose directives should be compiled.

        Returns:
            Combined directive text ready for injection into an agent
            system prompt.
        """
        if not active_skills:
            return ""

        sections: List[str] = []
        for skill in active_skills:
            if not skill.directives:
                continue
            header = f"## Skill: {skill.name}"
            if skill.description:
                header += f" - {skill.description}"
            body = "\n".join(skill.directives)
            sections.append(f"{header}\n{body}")

        combined = "\n\n".join(sections)
        logger.debug(
            "Generated directives from %d skill(s) (%d chars)",
            len(active_skills),
            len(combined),
        )
        return combined

    # ------------------------------------------------------------------
    # Hot reload
    # ------------------------------------------------------------------

    def reload(self) -> None:
        """Re-scan skills and plugins directories for changes.

        This clears internal caches and rediscovers all definitions,
        enabling hot-reload workflows during development.
        """
        logger.info("Reloading skills and plugins")
        self._skills.clear()
        self._plugins.clear()
        self._loaded = False
        self.discover_skills()
        self.discover_plugins()
        self._loaded = True
        logger.info(
            "Reload complete: %d skill(s), %d plugin(s)",
            len(self._skills),
            len(self._plugins),
        )
