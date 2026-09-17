"""
Project scanning and onboarding system for the TUI Agent Orchestration System.

Analyses a project's directory tree to detect languages, frameworks,
build tools, entry points, and overall project type.  Results are
packaged into a :class:`~shannon.tui.models.ProjectInfo` instance for
consumption by the orchestration engine.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from shannon.communication.events import EventBus, EventType
from shannon.tui.models import ProjectInfo

logger = logging.getLogger(__name__)

# Attempt to import toml parsing (stdlib from 3.11+, fallback to tomli).
try:
    import tomllib  # type: ignore[import-not-found]  # Python 3.11+
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore[no-redef,import-untyped]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]

# Attempt to import json (always available, but keep consistent style).
import json


# ---------------------------------------------------------------------------
# Project type enumeration
# ---------------------------------------------------------------------------


class ProjectType(Enum):
    """High-level project type inferred from languages and frameworks."""

    FRONTEND = "frontend"
    BACKEND = "backend"
    API_SERVER = "api_server"
    FULL_STACK = "full_stack"
    CLI_TOOL = "cli_tool"
    LIBRARY = "library"
    MOBILE = "mobile"
    SYSTEMS = "systems"
    DATA_SCIENCE = "data_science"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Extension -> language mapping
# ---------------------------------------------------------------------------

_EXTENSION_LANGUAGE_MAP: Dict[str, str] = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".rs": "Rust",
    ".go": "Go",
    ".java": "Java",
    ".swift": "Swift",
    ".rb": "Ruby",
    ".css": "CSS",
    ".html": "HTML",
}

# ---------------------------------------------------------------------------
# Default gitignore patterns (used when no .gitignore is present)
# ---------------------------------------------------------------------------

_DEFAULT_IGNORE_DIRS: Set[str] = {
    ".git",
    "__pycache__",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    ".venv",
    "venv",
    ".env",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "target",
    ".idea",
    ".vscode",
    "coverage",
    ".shannon",
    ".shannon_cache",
}

# ---------------------------------------------------------------------------
# Gitignore helpers
# ---------------------------------------------------------------------------


def _parse_gitignore(project_root: Path) -> Set[str]:
    """Parse ``.gitignore`` at *project_root* and return ignored directory names.

    This is a simplified parser that handles the most common patterns
    (bare directory names, trailing slashes, negation lines are skipped).
    """
    gitignore_path = project_root / ".gitignore"
    ignored: Set[str] = set(_DEFAULT_IGNORE_DIRS)

    if not gitignore_path.is_file():
        return ignored

    try:
        text = gitignore_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        logger.warning("Failed to read .gitignore at %s", gitignore_path)
        return ignored

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        # Strip trailing slash.
        entry = line.rstrip("/")
        # We only handle simple directory/file names and single-level globs.
        if "/" not in entry and "*" not in entry:
            ignored.add(entry)

    return ignored


def _should_skip_dir(dirname: str, ignored_dirs: Set[str]) -> bool:
    """Return ``True`` if *dirname* should be skipped during scanning."""
    return dirname in ignored_dirs or dirname.startswith(".")


# ---------------------------------------------------------------------------
# JSON / TOML helpers
# ---------------------------------------------------------------------------


def _read_json(path: Path) -> Dict[str, Any]:
    """Read and return a JSON file as a dict, or empty dict on error."""
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except Exception:
        logger.debug("Failed to read JSON: %s", path, exc_info=True)
        return {}


def _read_toml(path: Path) -> Dict[str, Any]:
    """Read and return a TOML file as a dict, or empty dict on error."""
    if tomllib is None:
        logger.debug("TOML parser unavailable; skipping %s", path)
        return {}
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception:
        logger.debug("Failed to read TOML: %s", path, exc_info=True)
        return {}


# ---------------------------------------------------------------------------
# ProjectScanner
# ---------------------------------------------------------------------------


class ProjectScanner:
    """Analyse a project directory to produce a :class:`ProjectInfo` summary.

    The scanner walks the project tree (respecting ``.gitignore``), detects
    languages, frameworks, build tools, and entry points, and emits events
    via the supplied :class:`EventBus` during the process.

    Args:
        project_root: Path to the project root directory.
        event_bus: EventBus instance used to emit scanning events.
    """

    def __init__(self, project_root: Path, event_bus: EventBus) -> None:
        self._root = project_root.resolve()
        self._event_bus = event_bus

        # Cached results.
        self._file_paths: List[Path] = []
        self._ignored_dirs: Set[str] = set()
        self._scanned = False

    # ------------------------------------------------------------------
    # Full tree scan
    # ------------------------------------------------------------------

    async def scan(
        self,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> ProjectInfo:
        """Walk the entire project tree and build a :class:`ProjectInfo`.

        Args:
            progress_callback: Optional callback invoked as
                ``(current_index, total_files, current_file_path)`` during
                the scan.

        Returns:
            Populated :class:`ProjectInfo` dataclass.
        """
        await self._event_bus.emit(
            EventType.SKILL_STARTED,
            data={"action": "project_scan", "root": str(self._root)},
            source="project_scanner",
        )

        self._ignored_dirs = _parse_gitignore(self._root)
        self._file_paths = []

        # First pass: collect all file paths.
        try:
            all_files = self._collect_files()
        except Exception as exc:
            logger.error("Error scanning project tree: %s", exc, exc_info=True)
            await self._event_bus.emit(
                EventType.SKILL_FAILED,
                data={"action": "project_scan", "error": str(exc)},
                source="project_scanner",
            )
            raise

        total = len(all_files)
        self._file_paths = all_files

        # Second pass: invoke progress callback.
        if progress_callback is not None:
            for idx, fpath in enumerate(all_files, start=1):
                try:
                    progress_callback(idx, total, str(fpath))
                except Exception:
                    logger.debug(
                        "Progress callback error at file %d/%d",
                        idx,
                        total,
                        exc_info=True,
                    )

        await self._event_bus.emit(
            EventType.SKILL_PROGRESS,
            data={
                "action": "project_scan",
                "files_found": total,
            },
            source="project_scanner",
        )

        self._scanned = True
        project_info = await self.build_project_info()

        await self._event_bus.emit(
            EventType.SKILL_COMPLETED,
            data={
                "action": "project_scan",
                "file_count": total,
                "language": project_info.language,
                "framework": project_info.framework,
            },
            source="project_scanner",
        )

        return project_info

    # ------------------------------------------------------------------
    # Language detection
    # ------------------------------------------------------------------

    def detect_languages(self) -> Dict[str, float]:
        """Count files by extension and return language percentage mapping.

        Returns:
            Mapping of language name to its percentage of known-language
            files (values sum to ~100).
        """
        if not self._file_paths:
            self._file_paths = self._collect_files()

        counts: Dict[str, int] = {}
        for fpath in self._file_paths:
            lang = _EXTENSION_LANGUAGE_MAP.get(fpath.suffix.lower())
            if lang:
                counts[lang] = counts.get(lang, 0) + 1

        total = sum(counts.values())
        if total == 0:
            return {}

        return {lang: round((count / total) * 100, 2) for lang, count in counts.items()}

    # ------------------------------------------------------------------
    # Framework detection
    # ------------------------------------------------------------------

    def detect_frameworks(self, project_root: Optional[Path] = None) -> List[str]:
        """Detect frameworks from manifest files.

        Checks ``package.json``, ``pyproject.toml``, ``Cargo.toml``, and
        ``go.mod`` for known framework identifiers.

        Args:
            project_root: Root directory to inspect.  Defaults to the
                scanner's configured root.

        Returns:
            List of detected framework names (lowercase).
        """
        root = (project_root or self._root).resolve()
        frameworks: List[str] = []

        # -- JavaScript / TypeScript frameworks via package.json -----------
        pkg_json_path = root / "package.json"
        if pkg_json_path.is_file():
            pkg = _read_json(pkg_json_path)
            all_deps: Dict[str, Any] = {}
            all_deps.update(pkg.get("dependencies", {}))
            all_deps.update(pkg.get("devDependencies", {}))

            js_framework_markers = {
                "react": "react",
                "react-dom": "react",
                "next": "next",
                "vue": "vue",
                "nuxt": "nuxt",
                "@angular/core": "angular",
                "express": "express",
                "fastify": "fastify",
                "svelte": "svelte",
            }
            for dep, name in js_framework_markers.items():
                if dep in all_deps and name not in frameworks:
                    frameworks.append(name)

        # -- Python frameworks via pyproject.toml --------------------------
        pyproject_path = root / "pyproject.toml"
        if pyproject_path.is_file():
            pyproject = _read_toml(pyproject_path)
            # Check [project].dependencies and [tool.poetry].dependencies
            py_deps: List[str] = []
            project_section = pyproject.get("project", {})
            if isinstance(project_section.get("dependencies"), list):
                py_deps.extend(project_section["dependencies"])
            poetry_deps = (
                pyproject.get("tool", {}).get("poetry", {}).get("dependencies", {})
            )
            if isinstance(poetry_deps, dict):
                py_deps.extend(poetry_deps.keys())

            py_framework_markers = {
                "fastapi": "fastapi",
                "flask": "flask",
                "django": "django",
                "starlette": "starlette",
                "tornado": "tornado",
                "sanic": "sanic",
            }
            deps_lower = " ".join(py_deps).lower()
            for marker, name in py_framework_markers.items():
                if marker in deps_lower and name not in frameworks:
                    frameworks.append(name)

        # -- Rust frameworks via Cargo.toml --------------------------------
        cargo_path = root / "Cargo.toml"
        if cargo_path.is_file():
            cargo = _read_toml(cargo_path)
            cargo_deps: Dict[str, Any] = {}
            cargo_deps.update(cargo.get("dependencies", {}))
            cargo_deps.update(cargo.get("dev-dependencies", {}))

            rust_markers = {
                "actix-web": "actix-web",
                "axum": "axum",
                "rocket": "rocket",
                "tokio": "tokio",
                "warp": "warp",
            }
            for dep, name in rust_markers.items():
                if dep in cargo_deps and name not in frameworks:
                    frameworks.append(name)

        # -- Go frameworks via go.mod --------------------------------------
        go_mod_path = root / "go.mod"
        if go_mod_path.is_file():
            try:
                go_mod_text = go_mod_path.read_text(encoding="utf-8")
            except OSError:
                go_mod_text = ""

            go_markers = {
                "gin-gonic/gin": "gin",
                "labstack/echo": "echo",
                "gorilla/mux": "gorilla-mux",
                "gofiber/fiber": "fiber",
            }
            for marker, name in go_markers.items():
                if marker in go_mod_text and name not in frameworks:
                    frameworks.append(name)

        logger.debug("Detected frameworks: %s", frameworks)
        return frameworks

    # ------------------------------------------------------------------
    # Project type detection
    # ------------------------------------------------------------------

    def detect_project_type(
        self,
        languages: Dict[str, float],
        frameworks: List[str],
    ) -> ProjectType:
        """Infer the high-level project type from languages and frameworks.

        Args:
            languages: Language percentage mapping from :meth:`detect_languages`.
            frameworks: Framework list from :meth:`detect_frameworks`.

        Returns:
            Inferred :class:`ProjectType`.
        """
        fw_set = {f.lower() for f in frameworks}
        lang_set = set(languages.keys())

        has_frontend_fw = bool(fw_set & {"react", "vue", "angular", "svelte", "next", "nuxt"})
        has_backend_fw = bool(
            fw_set & {"express", "fastapi", "flask", "django", "gin", "actix-web", "axum", "fastify"}
        )

        has_frontend_lang = bool(lang_set & {"TypeScript", "JavaScript"})
        has_backend_lang = bool(lang_set & {"Python", "Go", "Java", "Ruby", "Rust"})

        # Full-stack: both frontend framework + backend framework.
        if has_frontend_fw and has_backend_fw:
            return ProjectType.FULL_STACK

        # Frontend only.
        if has_frontend_fw:
            return ProjectType.FRONTEND

        # API / backend server.
        if has_backend_fw:
            return ProjectType.API_SERVER

        # Mobile.
        if "Swift" in lang_set:
            return ProjectType.MOBILE

        # Systems programming.
        if "Rust" in lang_set and not has_backend_fw:
            return ProjectType.SYSTEMS

        # CLI tool heuristic: Python-dominant with entry points but no web fw.
        if "Python" in lang_set and not has_backend_fw and not has_frontend_fw:
            # Check for CLI indicators.
            pyproject_path = self._root / "pyproject.toml"
            if pyproject_path.is_file():
                pyproject = _read_toml(pyproject_path)
                scripts = pyproject.get("project", {}).get("scripts", {})
                if scripts:
                    return ProjectType.CLI_TOOL

        # Library heuristic.
        if has_backend_lang and not has_frontend_lang and not has_backend_fw:
            return ProjectType.LIBRARY

        # Frontend language only (no framework).
        if has_frontend_lang and not has_backend_lang:
            return ProjectType.FRONTEND

        return ProjectType.UNKNOWN

    # ------------------------------------------------------------------
    # Entry points
    # ------------------------------------------------------------------

    def find_entry_points(self) -> List[str]:
        """Locate common entry point files in the project.

        Checks for well-known filenames (``main.py``, ``app.py``,
        ``index.ts``, etc.) and inspects manifest files for declared
        entry points.

        Returns:
            List of relative entry point paths as strings.
        """
        entry_points: List[str] = []

        well_known = [
            "main.py",
            "app.py",
            "__main__.py",
            "cli.py",
            "index.ts",
            "index.tsx",
            "index.js",
            "index.jsx",
            "main.ts",
            "main.tsx",
            "main.js",
            "main.go",
            "main.rs",
            "Main.java",
        ]

        # Search well-known names in collected files.
        for fpath in self._file_paths:
            if fpath.name in well_known:
                try:
                    rel = str(fpath.relative_to(self._root))
                except ValueError:
                    rel = str(fpath)
                if rel not in entry_points:
                    entry_points.append(rel)

        # Check pyproject.toml [project.scripts].
        pyproject_path = self._root / "pyproject.toml"
        if pyproject_path.is_file():
            pyproject = _read_toml(pyproject_path)
            scripts = pyproject.get("project", {}).get("scripts", {})
            for name, target in scripts.items():
                entry = f"[pyproject.toml] {name} = {target}"
                if entry not in entry_points:
                    entry_points.append(entry)

        # Check package.json main and scripts.
        pkg_json_path = self._root / "package.json"
        if pkg_json_path.is_file():
            pkg = _read_json(pkg_json_path)
            main_field = pkg.get("main")
            if main_field and str(main_field) not in entry_points:
                entry_points.append(str(main_field))
            for script_name in ("start", "dev", "serve"):
                script_cmd = pkg.get("scripts", {}).get(script_name)
                if script_cmd:
                    entry = f"[package.json] {script_name}: {script_cmd}"
                    if entry not in entry_points:
                        entry_points.append(entry)

        logger.debug("Found %d entry point(s)", len(entry_points))
        return entry_points

    # ------------------------------------------------------------------
    # Build tools
    # ------------------------------------------------------------------

    def detect_build_tools(self) -> List[str]:
        """Detect build tools based on lock files and config files.

        Returns:
            List of detected build tool names.
        """
        tools: List[str] = []

        indicators: Dict[str, List[str]] = {
            "npm": ["package-lock.json"],
            "yarn": ["yarn.lock"],
            "pnpm": ["pnpm-lock.yaml"],
            "uv": ["uv.lock"],
            "poetry": ["poetry.lock"],
            "pip": ["requirements.txt", "requirements.in"],
            "cargo": ["Cargo.lock", "Cargo.toml"],
            "go": ["go.sum", "go.mod"],
            "make": ["Makefile", "makefile", "GNUmakefile"],
        }

        for tool, filenames in indicators.items():
            for fname in filenames:
                if (self._root / fname).exists():
                    if tool not in tools:
                        tools.append(tool)
                    break

        # Additional heuristic: pyproject.toml without poetry -> pip/uv.
        pyproject = self._root / "pyproject.toml"
        if pyproject.is_file() and "poetry" not in tools:
            if "pip" not in tools and "uv" not in tools:
                tools.append("pip")

        logger.debug("Detected build tools: %s", tools)
        return tools

    # ------------------------------------------------------------------
    # Orchestrator
    # ------------------------------------------------------------------

    async def build_project_info(self) -> ProjectInfo:
        """Orchestrate all detection methods and return a complete
        :class:`ProjectInfo`.

        If the project has not yet been scanned (i.e. :meth:`scan` was
        not called), files are collected first.

        Returns:
            Fully populated :class:`ProjectInfo`.
        """
        if not self._scanned and not self._file_paths:
            self._ignored_dirs = _parse_gitignore(self._root)
            self._file_paths = self._collect_files()

        languages = self.detect_languages()
        frameworks = self.detect_frameworks()
        project_type = self.detect_project_type(languages, frameworks)
        entry_points = self.find_entry_points()
        build_tools = self.detect_build_tools()

        # Determine primary language (highest percentage).
        primary_language: Optional[str] = None
        if languages:
            primary_language = max(languages, key=languages.get)  # type: ignore[arg-type]

        # Determine primary framework.
        primary_framework: Optional[str] = None
        if frameworks:
            primary_framework = frameworks[0]

        # Determine primary build system.
        primary_build_system: Optional[str] = None
        if build_tools:
            primary_build_system = build_tools[0]

        # Detect test framework heuristically.
        test_framework = self._detect_test_framework()

        info = ProjectInfo(
            root_path=str(self._root),
            language=primary_language,
            framework=primary_framework,
            build_system=primary_build_system,
            test_framework=test_framework,
            file_count=len(self._file_paths),
            metadata={
                "languages": languages,
                "frameworks": frameworks,
                "project_type": project_type.value,
                "entry_points": entry_points,
                "build_tools": build_tools,
            },
        )

        logger.info(
            "Project info built: lang=%s, fw=%s, type=%s, files=%d",
            info.language,
            info.framework,
            project_type.value,
            info.file_count,
        )
        return info

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _collect_files(self) -> List[Path]:
        """Recursively collect all files under *project_root*, respecting
        ignore rules.

        Returns:
            Sorted list of file :class:`Path` objects.
        """
        files: List[Path] = []

        if not self._root.is_dir():
            logger.error("Project root is not a directory: %s", self._root)
            return files

        if not self._ignored_dirs:
            self._ignored_dirs = _parse_gitignore(self._root)

        for item in sorted(self._root.rglob("*")):
            # Skip ignored directories.
            skip = False
            for part in item.parts:
                if _should_skip_dir(part, self._ignored_dirs):
                    skip = True
                    break
            if skip:
                continue

            if item.is_file():
                files.append(item)

        logger.debug("Collected %d files from %s", len(files), self._root)
        return files

    def _detect_test_framework(self) -> Optional[str]:
        """Heuristically detect the test framework in use."""
        # Python test frameworks.
        pyproject_path = self._root / "pyproject.toml"
        if pyproject_path.is_file():
            pyproject = _read_toml(pyproject_path)
            tool_section = pyproject.get("tool", {})
            if "pytest" in tool_section:
                return "pytest"

        if (self._root / "pytest.ini").is_file() or (self._root / "setup.cfg").is_file():
            return "pytest"

        if (self._root / "conftest.py").is_file():
            return "pytest"

        # JavaScript test frameworks.
        pkg_json_path = self._root / "package.json"
        if pkg_json_path.is_file():
            pkg = _read_json(pkg_json_path)
            dev_deps = pkg.get("devDependencies", {})
            all_deps = {**pkg.get("dependencies", {}), **dev_deps}

            if "vitest" in all_deps:
                return "vitest"
            if "jest" in all_deps:
                return "jest"
            if "mocha" in all_deps:
                return "mocha"

        # Rust tests are built-in.
        if (self._root / "Cargo.toml").is_file():
            return "cargo-test"

        # Go tests are built-in.
        if (self._root / "go.mod").is_file():
            return "go-test"

        return None
