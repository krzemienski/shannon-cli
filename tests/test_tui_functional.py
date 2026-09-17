"""
Comprehensive functional test suite for the TUI Agent Orchestration System.

Exercises every subsystem end-to-end: models, complexity assessment,
task decomposition, memory CRUD, skill loading, project scanning,
agent adapter (mock mode), validation engine, orchestration engine,
controller integration, screen instantiation, and app state lifecycle.

Run with: python tests/test_tui_functional.py
"""

from __future__ import annotations

import asyncio
import json
import sys
import tempfile
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Prevent the heavy shannon.__init__ from pulling in CLI dependencies.
# We only need the TUI subpackage and the EventBus.
import types as _types
_shannon_stub = _types.ModuleType("shannon")
_shannon_stub.__path__ = [str(PROJECT_ROOT / "src" / "shannon")]
sys.modules.setdefault("shannon", _shannon_stub)
# Stub out heavy sub-packages we don't need
for _mod_name in [
    "shannon.cli", "shannon.cli.commands",
    "shannon.core", "shannon.core.session_manager",
    "shannon.sdk", "shannon.sdk.client", "shannon.sdk.message_parser",
    "shannon.ui", "shannon.ui.progress",
    "shannon.setup", "shannon.setup.framework_detector", "shannon.setup.wizard",
    "shannon.config",
]:
    sys.modules.setdefault(_mod_name, _types.ModuleType(_mod_name))

# ---------------------------------------------------------------------------
# Imports under test
# ---------------------------------------------------------------------------
from shannon.communication.events import EventBus, EventType, get_event_bus
from shannon.tui.models import (
    AgentConfig,
    AgentState,
    AgentStatus,
    ContextItem,
    MemoryEntry,
    MemoryType,
    ModelConfig,
    ModelTier,
    ProjectInfo,
    TaskComplexity,
    TaskGraph,
    TaskNode,
    TaskStatus,
    TaskType,
    ValidationPlan,
    ValidationRun,
    ValidationStatus,
    ValidationStep,
    ValidatorType,
)
from shannon.tui.orchestration_engine import (
    ComplexityAssessor,
    OrchestrationEngine,
    TaskDecomposer,
)
from shannon.tui.memory_system import MemorySystem
from shannon.tui.skill_loader import SkillLoader, SkillDefinition, PluginPhase
from shannon.tui.project_scanner import ProjectScanner
from shannon.tui.agent_adapter import AgentAdapter
from shannon.tui.validation_engine import ValidationEngine
from shannon.tui.app import AppState, OrchestrationController


# ---------------------------------------------------------------------------
# Test harness
# ---------------------------------------------------------------------------

_PASSED = 0
_FAILED = 0
_ERRORS: List[str] = []


def _run_test(name: str, fn):
    global _PASSED, _FAILED
    try:
        result = fn()
        if asyncio.iscoroutine(result):
            asyncio.get_event_loop().run_until_complete(result)
        _PASSED += 1
        print(f"  PASS  {name}")
    except Exception as exc:
        _FAILED += 1
        tb = traceback.format_exc()
        _ERRORS.append(f"{name}: {exc}\n{tb}")
        print(f"  FAIL  {name}: {exc}")


def assert_eq(actual, expected, msg=""):
    if actual != expected:
        raise AssertionError(f"{msg}: expected {expected!r}, got {actual!r}")


def assert_true(val, msg=""):
    if not val:
        raise AssertionError(f"Expected truthy: {msg}")


def assert_in(item, container, msg=""):
    if item not in container:
        raise AssertionError(f"{msg}: {item!r} not in {container!r}")


def assert_gt(a, b, msg=""):
    if not (a > b):
        raise AssertionError(f"{msg}: {a!r} not > {b!r}")


def assert_ge(a, b, msg=""):
    if not (a >= b):
        raise AssertionError(f"{msg}: {a!r} not >= {b!r}")


def assert_isinstance(obj, cls, msg=""):
    if not isinstance(obj, cls):
        raise AssertionError(f"{msg}: {type(obj).__name__} is not {cls.__name__}")


# ===================================================================
# 1. DATA MODEL TESTS
# ===================================================================

def test_project_info_defaults():
    info = ProjectInfo(root_path="/tmp/test")
    assert_eq(info.root_path, "/tmp/test")
    assert_eq(info.language, None)
    assert_eq(info.framework, None)
    assert_eq(info.file_count, 0)


def test_task_node_creation():
    node = TaskNode(
        title="Test task",
        description="A test",
        task_type=TaskType.IMPLEMENTATION,
        model_tier=ModelTier.STANDARD,
    )
    assert_true(node.node_id, "node_id should be set")
    assert_eq(node.status, TaskStatus.PENDING)
    assert_eq(node.task_type, TaskType.IMPLEMENTATION)
    assert_eq(node.model_tier, ModelTier.STANDARD)
    assert_eq(node.retry_count, 0)


def test_task_graph_operations():
    graph = TaskGraph(prompt="test", complexity=TaskComplexity.SIMPLE)
    n1 = TaskNode(title="A", task_type=TaskType.RESEARCH)
    n2 = TaskNode(title="B", task_type=TaskType.IMPLEMENTATION)
    graph.add_node(n1)
    graph.add_node(n2)
    assert_eq(graph.total_count, 2)
    assert_eq(graph.completed_count, 0)
    assert_eq(graph.failed_count, 0)
    assert_eq(graph.progress_percent, 0.0)

    graph.mark_completed(n1.node_id, {"output": "done"})
    assert_eq(graph.completed_count, 1)
    assert_eq(n1.status, TaskStatus.COMPLETED)
    assert_gt(graph.progress_percent, 0.0)

    graph.mark_failed(n2.node_id, "error occurred")
    assert_eq(graph.failed_count, 1)
    assert_eq(n2.status, TaskStatus.FAILED)


def test_task_graph_phases():
    graph = TaskGraph(prompt="multi-phase", complexity=TaskComplexity.MEDIUM)
    n1 = TaskNode(title="Phase0", phase=0)
    n2 = TaskNode(title="Phase1", phase=1)
    n3 = TaskNode(title="Phase1b", phase=1)
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_node(n3)
    graph.total_phases = 2
    p0 = graph.get_nodes_by_phase(0)
    p1 = graph.get_nodes_by_phase(1)
    assert_eq(len(p0), 1)
    assert_eq(len(p1), 2)


def test_agent_config_serialization():
    cfg = AgentConfig(name="test-agent", model_tier=ModelTier.COMPLEX)
    d = cfg.to_dict()
    assert_eq(d["name"], "test-agent")
    assert_eq(d["model_tier"], "complex")


def test_agent_state_lifecycle():
    state = AgentState(
        agent_id="agt-1",
        config=AgentConfig(name="worker"),
        status=AgentStatus.SPAWNING,
    )
    assert_eq(state.status, AgentStatus.SPAWNING)
    state.status = AgentStatus.ACTIVE
    state.started_at = datetime.utcnow()
    state.thoughts.append("thinking...")
    state.actions.append({"tool": "read", "input": {}})
    state.text_output.append("result text")
    assert_eq(len(state.thoughts), 1)
    assert_eq(len(state.actions), 1)
    state.status = AgentStatus.COMPLETED
    state.completed_at = datetime.utcnow()
    assert_true(state.duration_seconds is not None or state.duration_seconds == 0)


def test_memory_entry_serialization():
    entry = MemoryEntry(
        memory_type=MemoryType.DECISION,
        content="Use React for frontend",
        tags=["frontend", "react"],
    )
    d = entry.to_dict()
    assert_eq(d["memory_type"], "decision")
    assert_in("react", d["tags"])
    restored = MemoryEntry.from_dict(d)
    assert_eq(restored.content, entry.content)
    assert_eq(restored.memory_type, MemoryType.DECISION)


def test_context_item_serialization():
    item = ContextItem(
        content="some context",
        source="test",
        context_type="active",
        relevance_score=0.8,
        token_estimate=10,
    )
    d = item.to_dict()
    assert_eq(d["source"], "test")
    restored = ContextItem.from_dict(d)
    assert_eq(restored.content, "some context")
    assert_eq(restored.relevance_score, 0.8)


def test_validation_models():
    step = ValidationStep(
        name="lint",
        validator_type=ValidatorType.CLI,
        command="echo ok",
        status=ValidationStatus.PENDING,
    )
    assert_eq(step.status, ValidationStatus.PENDING)
    plan = ValidationPlan(
        task_description="validate code",
        steps=[step],
        validator_types=[ValidatorType.CLI],
    )
    assert_eq(len(plan.steps), 1)
    run = ValidationRun(plan_id=plan.plan_id, steps=[step])
    assert_eq(run.passed_count, 0)
    assert_eq(run.failed_count, 0)
    assert_eq(run.all_passed, False)  # PENDING != PASSED
    step.status = ValidationStatus.PASSED
    assert_eq(run.passed_count, 1)
    assert_true(run.all_passed)


def test_memory_type_agent_output():
    assert_true(hasattr(MemoryType, "AGENT_OUTPUT"))
    assert_eq(MemoryType.AGENT_OUTPUT.value, "agent_output")


def test_all_enums_complete():
    assert_ge(len(TaskComplexity), 4, "TaskComplexity members")
    assert_ge(len(TaskType), 5, "TaskType members")
    assert_ge(len(TaskStatus), 4, "TaskStatus members")
    assert_ge(len(ModelTier), 3, "ModelTier members")
    assert_ge(len(AgentStatus), 4, "AgentStatus members")
    assert_ge(len(MemoryType), 8, "MemoryType members")
    assert_ge(len(ValidatorType), 3, "ValidatorType members")
    assert_ge(len(ValidationStatus), 4, "ValidationStatus members")


# ===================================================================
# 2. COMPLEXITY ASSESSOR TESTS
# ===================================================================

def test_simple_prompt():
    a = ComplexityAssessor()
    assert_eq(a.assess("fix a typo"), TaskComplexity.SIMPLE)


def test_medium_prompt():
    a = ComplexityAssessor()
    result = a.assess("implement a new authentication feature with API endpoints and database schema")
    assert_in(result, [TaskComplexity.MEDIUM, TaskComplexity.HIGH])


def test_high_prompt():
    a = ComplexityAssessor()
    result = a.assess(
        "migrate the entire system to microservices architecture, "
        "redesign the infrastructure pipeline, rewrite the distributed "
        "deployment system across all services"
    )
    assert_in(result, [TaskComplexity.HIGH, TaskComplexity.CRITICAL])


def test_critical_prompt():
    a = ComplexityAssessor()
    result = a.assess(
        "complete system-wide migration and overhaul of the entire "
        "distributed platform infrastructure across all 50+ files, "
        "redesign every microservice, refactor the global architecture, "
        "integrate CI/CD pipeline and deploy scalable services end-to-end"
    )
    assert_eq(result, TaskComplexity.CRITICAL)


def test_score_breakdown():
    a = ComplexityAssessor()
    bd = a.score_breakdown("implement a new feature")
    assert_in("action_verbs", bd)
    assert_in("complexity", bd)
    assert_in("word_count", bd)


# ===================================================================
# 3. TASK DECOMPOSER TESTS
# ===================================================================

def test_decompose_simple():
    d = TaskDecomposer()
    graph = d.decompose("fix a bug", TaskComplexity.SIMPLE)
    assert_gt(graph.total_count, 0, "should have at least one node")
    assert_true(any(n.task_type == TaskType.VALIDATION for n in graph.nodes.values()),
                "should end with validation")


def test_decompose_medium_adds_research():
    d = TaskDecomposer()
    graph = d.decompose("implement authentication module", TaskComplexity.MEDIUM)
    types = {n.task_type for n in graph.nodes.values()}
    assert_in(TaskType.RESEARCH, types, "MEDIUM should add research")
    assert_in(TaskType.ANALYSIS, types, "MEDIUM should add analysis")


def test_decompose_high_adds_architecture():
    d = TaskDecomposer()
    graph = d.decompose("build API server", TaskComplexity.HIGH)
    types = {n.task_type for n in graph.nodes.values()}
    assert_in(TaskType.ARCHITECTURE, types, "HIGH should add architecture")


def test_decompose_critical_fan_out():
    d = TaskDecomposer()
    graph = d.decompose("rewrite platform", TaskComplexity.CRITICAL)
    impl_nodes = [n for n in graph.nodes.values() if n.task_type == TaskType.IMPLEMENTATION]
    assert_eq(len(impl_nodes), 6, "CRITICAL should fan out to 6 impl agents")


def test_decompose_phases_wired():
    d = TaskDecomposer()
    graph = d.decompose("implement feature", TaskComplexity.MEDIUM)
    assert_gt(graph.total_phases, 1, "should have multiple phases")
    for node in graph.nodes.values():
        if node.phase > 0:
            assert_gt(len(node.dependencies), 0,
                      f"phase {node.phase} node should have dependencies")


def test_decompose_with_project_info():
    d = TaskDecomposer()
    info = ProjectInfo(root_path="/tmp", language="Python", framework="fastapi")
    graph = d.decompose("add endpoint", TaskComplexity.SIMPLE, info)
    assert_gt(graph.total_count, 0)


# ===================================================================
# 4. MEMORY SYSTEM TESTS
# ===================================================================

def test_memory_create_and_search():
    ms = MemorySystem(session_id="test-1")
    entry = ms.create_memory(
        memory_type=MemoryType.DECISION,
        content="Use PostgreSQL for the database layer",
        tags=["database", "postgres"],
    )
    assert_true(entry.memory_id)
    results = ms.search_memories("PostgreSQL")
    assert_gt(len(results), 0, "should find the entry")
    assert_eq(results[0].content, entry.content)


def test_memory_search_no_match():
    ms = MemorySystem(session_id="test-2")
    ms.create_memory(MemoryType.INSIGHT, content="React hooks are useful")
    results = ms.search_memories("quantum computing")
    assert_eq(len(results), 0)


def test_memory_type_routing():
    ms = MemorySystem(session_id="test-3")
    ms.create_memory(MemoryType.DECISION, content="Use REST not GraphQL")
    ms.create_memory(MemoryType.INSIGHT, content="Users prefer dark mode")
    stats = ms.get_stats()
    assert_gt(stats["memory_counts"]["total_indexed"], 0)


def test_memory_delete():
    ms = MemorySystem(session_id="test-4")
    entry = ms.create_memory(MemoryType.CODE_PATTERN, content="singleton pattern")
    assert_true(ms.delete_memory(entry.memory_id))
    assert_eq(ms.delete_memory(entry.memory_id), False, "double delete")


def test_memory_update():
    ms = MemorySystem(session_id="test-5")
    entry = ms.create_memory(MemoryType.DECISION, content="original")
    updated = ms.update_memory(entry.memory_id, "modified")
    assert_eq(updated.content, "modified")


def test_memory_context_tiers():
    ms = MemorySystem(session_id="test-6")
    ms.set_active_context(task="current task", files=["main.py"])
    ms.add_session_context(ContextItem(
        content="session info", source="test", context_type="session",
    ))
    ctx = ms.get_relevant_context("current task")
    assert_gt(len(ctx), 0, "should return context items")


def test_memory_context_utilization():
    ms = MemorySystem(session_id="test-7")
    util = ms.get_context_utilization()
    assert_in("l1", util)
    assert_in("l2", util)
    assert_in("l3", util)
    assert_in("l4", util)


def test_memory_session_persistence():
    ms = MemorySystem(session_id="test-8")
    ms.create_memory(MemoryType.DECISION, content="persist me")
    ms.set_active_context(task="active task")

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = Path(f.name)

    ms.save_session(path)
    assert_true(path.exists())

    ms2 = MemorySystem(session_id="test-8-restored")
    ms2.load_session(path)
    assert_eq(ms2.session_id, "test-8")
    results = ms2.search_memories("persist")
    assert_gt(len(results), 0)
    path.unlink()


def test_memory_checkpoint_restore():
    ms = MemorySystem(session_id="test-9")
    ms.create_memory(MemoryType.INSIGHT, content="before checkpoint")
    cp_id = ms.create_checkpoint()

    ms.create_memory(MemoryType.INSIGHT, content="after checkpoint")
    assert_eq(ms.get_stats()["memory_counts"]["total_indexed"], 2)

    ms.restore_checkpoint(cp_id)
    assert_eq(ms.get_stats()["memory_counts"]["total_indexed"], 1)


def test_memory_l2_pruning():
    ms = MemorySystem(session_id="test-10", l2_max_size=3)
    for i in range(5):
        ms.add_session_context(ContextItem(
            content=f"item {i}", source="test", context_type="session",
        ))
    stats = ms.get_stats()
    assert_eq(stats["memory_counts"]["l2_session"], 3, "should prune to max")


# ===================================================================
# 5. SKILL LOADER TESTS
# ===================================================================

def test_skill_loader_empty_dirs():
    with tempfile.TemporaryDirectory() as td:
        sl = SkillLoader(
            skills_dir=Path(td) / "skills",
            plugins_dir=Path(td) / "plugins",
        )
        skills = sl.discover_skills()
        assert_eq(len(skills), 0)
        plugins = sl.discover_plugins()
        assert_eq(len(plugins), 0)


def test_skill_loader_yaml_discovery():
    with tempfile.TemporaryDirectory() as td:
        skills_dir = Path(td) / "skills"
        skills_dir.mkdir()
        (skills_dir / "code-quality.yaml").write_text(
            "name: code-quality\n"
            "description: Code quality checks\n"
            "trigger_conditions: [code, quality, lint]\n"
            "directives:\n"
            "  - Always run linter before committing\n"
            "  - Follow style guide\n"
        )
        sl = SkillLoader(skills_dir=skills_dir, plugins_dir=Path(td) / "plugins")
        skills = sl.discover_skills()
        assert_eq(len(skills), 1)
        assert_eq(skills[0].name, "code-quality")


def test_skill_loader_markdown_discovery():
    with tempfile.TemporaryDirectory() as td:
        skills_dir = Path(td) / "skills"
        skill_sub = skills_dir / "my-skill"
        skill_sub.mkdir(parents=True)
        (skill_sub / "SKILL.md").write_text("# My Custom Skill\nDo great things.\n")
        sl = SkillLoader(skills_dir=skills_dir, plugins_dir=Path(td) / "plugins")
        skills = sl.discover_skills()
        assert_eq(len(skills), 1)
        assert_eq(skills[0].name, "my-skill")


def test_skill_activation_by_keywords():
    with tempfile.TemporaryDirectory() as td:
        skills_dir = Path(td) / "skills"
        skills_dir.mkdir()
        (skills_dir / "testing.yaml").write_text(
            "name: testing\ntrigger_conditions: [test, testing, spec]\n"
            "directives: [Write thorough tests]\n"
        )
        (skills_dir / "docs.yaml").write_text(
            "name: docs\ntrigger_conditions: [document, readme, docs]\n"
            "directives: [Update documentation]\n"
        )
        sl = SkillLoader(skills_dir=skills_dir, plugins_dir=Path(td) / "plugins")
        active = sl.activate_skills("write unit tests for the module")
        names = {s.name for s in active}
        assert_in("testing", names, "should match 'test' keyword")
        assert_true("docs" not in names, "should not match docs")


def test_skill_always_active():
    with tempfile.TemporaryDirectory() as td:
        skills_dir = Path(td) / "skills"
        skills_dir.mkdir()
        (skills_dir / "code-quality.yaml").write_text(
            "name: code-quality\ntrigger_conditions: []\ndirectives: [lint]\n"
        )
        sl = SkillLoader(skills_dir=skills_dir, plugins_dir=Path(td) / "plugins")
        active = sl.activate_skills("unrelated task xyz")
        names = {s.name for s in active}
        assert_in("code-quality", names, "code-quality is always active")


def test_skill_directive_generation():
    with tempfile.TemporaryDirectory() as td:
        sl = SkillLoader(Path(td), Path(td))
        skills = [
            SkillDefinition(name="s1", description="Skill 1", directives=["Do A", "Do B"]),
            SkillDefinition(name="s2", description="Skill 2", directives=["Do C"]),
        ]
        text = sl.generate_skill_directives(skills)
        assert_in("Skill 1", text)
        assert_in("Do A", text)
        assert_in("Do C", text)


def test_skill_reload():
    with tempfile.TemporaryDirectory() as td:
        skills_dir = Path(td) / "skills"
        plugins_dir = Path(td) / "plugins"
        skills_dir.mkdir()
        plugins_dir.mkdir()
        sl = SkillLoader(skills_dir=skills_dir, plugins_dir=plugins_dir)
        sl.reload()  # should not error even with empty dirs


def test_plugin_yaml_discovery():
    with tempfile.TemporaryDirectory() as td:
        plugins_dir = Path(td) / "plugins"
        plugins_dir.mkdir()
        (plugins_dir / "formatter.yaml").write_text(
            "name: formatter\nphase: post_execution\npriority: 10\n"
            "description: Format output\nhandler_path: fmt.run\n"
        )
        sl = SkillLoader(skills_dir=Path(td) / "skills", plugins_dir=plugins_dir)
        plugins = sl.discover_plugins()
        assert_eq(len(plugins), 1)
        assert_eq(plugins[0].name, "formatter")
        assert_eq(plugins[0].phase, PluginPhase.POST_EXECUTION)


def test_plugin_pipeline_filtering():
    with tempfile.TemporaryDirectory() as td:
        plugins_dir = Path(td) / "plugins"
        plugins_dir.mkdir()
        (plugins_dir / "pre.yaml").write_text(
            "name: pre-hook\nphase: pre_execution\npriority: 1\n"
        )
        (plugins_dir / "post.yaml").write_text(
            "name: post-hook\nphase: post_execution\npriority: 1\n"
        )
        sl = SkillLoader(skills_dir=Path(td) / "skills", plugins_dir=plugins_dir)
        pre = sl.get_plugin_pipeline(PluginPhase.PRE_EXECUTION)
        post = sl.get_plugin_pipeline(PluginPhase.POST_EXECUTION)
        assert_eq(len(pre), 1)
        assert_eq(len(post), 1)
        assert_eq(pre[0].name, "pre-hook")


# ===================================================================
# 6. PROJECT SCANNER TESTS
# ===================================================================

def test_scanner_python_project():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "main.py").write_text("print('hello')\n")
        (root / "utils.py").write_text("def helper(): pass\n")
        (root / "pyproject.toml").write_text(
            '[project]\nname = "test"\n[project.scripts]\nmycli = "main:main"\n'
        )

        bus = get_event_bus()
        scanner = ProjectScanner(project_root=root, event_bus=bus)

        async def run():
            info = await scanner.scan()
            assert_eq(info.language, "Python")
            assert_in("pip", info.metadata.get("build_tools", []))
            assert_in("cli_tool", info.metadata.get("project_type", ""))
            assert_gt(info.file_count, 0)

        asyncio.get_event_loop().run_until_complete(run())


def test_scanner_js_project():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "index.js").write_text("console.log('hi')\n")
        (root / "app.tsx").write_text("export default App\n")
        (root / "package.json").write_text(json.dumps({
            "name": "test",
            "dependencies": {"react": "^18.0.0", "react-dom": "^18.0.0"},
            "scripts": {"start": "react-scripts start"},
        }))
        bus = get_event_bus()
        scanner = ProjectScanner(project_root=root, event_bus=bus)

        async def run():
            info = await scanner.scan()
            assert_in("react", info.metadata.get("frameworks", []))

        asyncio.get_event_loop().run_until_complete(run())


def test_scanner_language_detection():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for name in ["a.py", "b.py", "c.py", "d.ts", "e.go"]:
            (root / name).write_text("// code\n")

        bus = get_event_bus()
        scanner = ProjectScanner(project_root=root, event_bus=bus)
        langs = scanner.detect_languages()
        assert_in("Python", langs)
        assert_gt(langs["Python"], 50.0, "Python should be dominant")


def test_scanner_respects_gitignore():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ".gitignore").write_text("node_modules\n__pycache__\n")
        nm = root / "node_modules"
        nm.mkdir()
        (nm / "dep.js").write_text("module.exports = {}\n")
        (root / "app.py").write_text("print('hi')\n")

        bus = get_event_bus()
        scanner = ProjectScanner(project_root=root, event_bus=bus)

        async def run():
            info = await scanner.scan()
            files = [str(f) for f in scanner._file_paths]
            assert_true(not any("node_modules" in f for f in files),
                        "node_modules should be ignored")

        asyncio.get_event_loop().run_until_complete(run())


def test_scanner_progress_callback():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for i in range(5):
            (root / f"file{i}.py").write_text(f"# file {i}\n")

        bus = get_event_bus()
        scanner = ProjectScanner(project_root=root, event_bus=bus)
        progress_calls = []

        async def run():
            await scanner.scan(progress_callback=lambda c, t, f: progress_calls.append((c, t)))

        asyncio.get_event_loop().run_until_complete(run())
        assert_gt(len(progress_calls), 0, "progress callback should be called")


# ===================================================================
# 7. AGENT ADAPTER TESTS (mock mode)
# ===================================================================

def test_agent_adapter_mock_execution():
    async def run():
        bus = get_event_bus()
        adapter = AgentAdapter(
            model_registry=AgentAdapter.get_default_registry(),
            event_bus=bus,
        )

        config = AgentConfig(name="test-agent", model_tier=ModelTier.STANDARD)
        node = TaskNode(title="Test", description="Run a test task")

        state = await adapter.spawn_agent(config=config, task_node=node, context_items=[])
        assert_eq(state.status, AgentStatus.SPAWNING)

        state = await adapter.execute_agent(state)
        assert_eq(state.status, AgentStatus.COMPLETED)
        assert_gt(len(state.thoughts), 0, "should have thoughts")
        assert_gt(len(state.actions), 0, "should have actions")
        assert_gt(len(state.text_output), 0, "should have text output")
        assert_gt(state.tokens_in, 0, "should track input tokens")
        assert_gt(state.tokens_out, 0, "should track output tokens")

    asyncio.get_event_loop().run_until_complete(run())


def test_agent_adapter_model_selection():
    bus = get_event_bus()
    adapter = AgentAdapter(
        model_registry=AgentAdapter.get_default_registry(),
        event_bus=bus,
    )
    assert_eq(adapter._select_model(ModelTier.COMPLEX), "claude-opus-4-6")
    assert_eq(adapter._select_model(ModelTier.STANDARD), "claude-sonnet-4-6")
    assert_eq(adapter._select_model(ModelTier.FAST), "claude-haiku-4-5-20251001")


def test_agent_adapter_events_emitted():
    async def run():
        bus = EventBus()
        events_captured = []

        async def capture(event):
            events_captured.append(event.event_type)

        await bus.subscribe(EventType.AGENT_SPAWNED, capture)
        await bus.subscribe(EventType.AGENT_COMPLETED, capture)
        await bus.subscribe(EventType.AGENT_PROGRESS, capture)

        adapter = AgentAdapter(
            model_registry=AgentAdapter.get_default_registry(),
            event_bus=bus,
        )
        config = AgentConfig(name="evt-test", model_tier=ModelTier.FAST)
        node = TaskNode(title="Events", description="event test")
        state = await adapter.spawn_agent(config=config, task_node=node, context_items=[])
        await adapter.execute_agent(state)
        # Let background tasks (create_task) complete
        await asyncio.sleep(0.1)

        assert_in(EventType.AGENT_SPAWNED, events_captured)
        assert_in(EventType.AGENT_COMPLETED, events_captured)
        assert_in(EventType.AGENT_PROGRESS, events_captured)

    asyncio.get_event_loop().run_until_complete(run())


def test_agent_adapter_system_prompt_building():
    bus = get_event_bus()
    adapter = AgentAdapter(
        model_registry=AgentAdapter.get_default_registry(),
        event_bus=bus,
    )
    node = TaskNode(title="Build API", description="Create a REST API")
    ctx = [ContextItem(content="Use FastAPI", source="test", context_type="project")]
    prompt = adapter._build_system_prompt(node, ctx)
    assert_in("Build API", prompt)
    assert_in("REST API", prompt)
    assert_in("FastAPI", prompt)
    assert_in("Shannon orchestration", prompt)


# ===================================================================
# 8. VALIDATION ENGINE TESTS
# ===================================================================

def test_validation_plan_creation():
    async def run():
        bus = get_event_bus()
        engine = ValidationEngine(event_bus=bus)
        info = ProjectInfo(root_path="/tmp", language="Python", framework="fastapi")
        plan = engine.create_validation_plan(
            task_description="add new endpoint",
            project_info=info,
            files_modified=["api/routes.py"],
        )
        assert_gt(len(plan.steps), 0, "should generate steps")
        types = {s.validator_type for s in plan.steps}
        assert_in(ValidatorType.CLI, types, "should include CLI validation")

    asyncio.get_event_loop().run_until_complete(run())


def test_validation_execution():
    async def run():
        bus = get_event_bus()
        engine = ValidationEngine(event_bus=bus)

        step = ValidationStep(
            name="echo test",
            validator_type=ValidatorType.CLI,
            command="echo hello",
            expected_exit_code=0,
        )
        plan = ValidationPlan(
            task_description="test validation",
            steps=[step],
            validator_types=[ValidatorType.CLI],
        )

        run_result = await engine.execute_validation(plan, Path.cwd())
        assert_isinstance(run_result, ValidationRun)
        assert_eq(len(run_result.steps), 1)
        assert_eq(run_result.steps[0].status, ValidationStatus.PASSED)
        assert_true(run_result.all_passed)

    asyncio.get_event_loop().run_until_complete(run())


def test_validation_failure_detection():
    async def run():
        bus = get_event_bus()
        engine = ValidationEngine(event_bus=bus)

        step = ValidationStep(
            name="bad command",
            validator_type=ValidatorType.CLI,
            command="exit 1",
            expected_exit_code=0,
        )
        plan = ValidationPlan(
            task_description="failing test",
            steps=[step],
            validator_types=[ValidatorType.CLI],
        )

        run_result = await engine.execute_validation(plan, Path.cwd())
        assert_eq(run_result.steps[0].status, ValidationStatus.FAILED)
        assert_eq(run_result.all_passed, False)

    asyncio.get_event_loop().run_until_complete(run())


def test_validation_events_emitted():
    async def run():
        bus = EventBus()
        events = []

        async def capture(event):
            events.append(event.event_type)

        await bus.subscribe(EventType.VALIDATION_STARTED, capture)
        await bus.subscribe(EventType.VALIDATION_RESULT, capture)

        engine = ValidationEngine(event_bus=bus)
        step = ValidationStep(
            name="test", validator_type=ValidatorType.CLI,
            command="echo ok", expected_exit_code=0,
        )
        plan = ValidationPlan(steps=[step], validator_types=[ValidatorType.CLI])
        await engine.execute_validation(plan, Path.cwd())
        await asyncio.sleep(0.1)

        assert_in(EventType.VALIDATION_STARTED, events)
        assert_in(EventType.VALIDATION_RESULT, events)

    asyncio.get_event_loop().run_until_complete(run())


# ===================================================================
# 9. APP STATE TESTS
# ===================================================================

def test_app_state_initialization():
    state = AppState()
    assert_true(state.session_id)
    assert_isinstance(state.session_start, datetime)
    assert_eq(len(state.memories), 0)
    assert_eq(len(state.task_history), 0)
    assert_eq(len(state.log_entries), 0)
    assert_in("L1", state.context_utilization)


def test_app_state_logging():
    state = AppState()
    state.add_log("TEST", "hello world")
    state.add_log("TEST", "error msg", level="ERROR", agent_id="a1")
    assert_eq(len(state.log_entries), 2)
    assert_eq(state.log_entries[0]["source"], "TEST")
    assert_eq(state.log_entries[1]["level"], "ERROR")
    assert_eq(state.log_entries[1]["agent_id"], "a1")


def test_app_state_task_history():
    state = AppState()
    state.add_task_to_history("task one", "completed")
    state.add_task_to_history("task two", "failed")
    assert_eq(len(state.task_history), 2)
    assert_eq(state.task_history[0]["title"], "task two")  # inserted at front


def test_app_state_duration():
    state = AppState()
    dur = state.session_duration_str
    assert_true("m" in dur or "h" in dur, "should contain time unit")


# ===================================================================
# 10. ORCHESTRATION CONTROLLER TESTS
# ===================================================================

def test_controller_lazy_init():
    bus = get_event_bus()
    state = AppState()
    ctrl = OrchestrationController(state, bus)
    assert_true(ctrl._engine is None)
    assert_true(ctrl._adapter is None)
    assert_true(ctrl._memory is None)
    engine = ctrl.engine
    assert_true(engine is not None)
    assert_true(ctrl._engine is not None)


def test_controller_decompose_task():
    async def run():
        bus = get_event_bus()
        state = AppState()
        ctrl = OrchestrationController(state, bus)
        graph = await ctrl.decompose_task("implement a new feature")
        assert_isinstance(graph, TaskGraph)
        assert_gt(graph.total_count, 0)
        assert_true(state.current_graph is not None)

    asyncio.get_event_loop().run_until_complete(run())


def test_controller_memory_operations():
    async def run():
        bus = get_event_bus()
        state = AppState()
        ctrl = OrchestrationController(state, bus)
        entry = await ctrl.create_memory(
            content="test memory",
            memory_type=MemoryType.DECISION,
            tags=["test"],
        )
        assert_isinstance(entry, MemoryEntry)
        assert_eq(len(state.memories), 1)

        results = await ctrl.search_memories("test")
        assert_gt(len(results), 0)

    asyncio.get_event_loop().run_until_complete(run())


def test_controller_onboard_project():
    async def run():
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "main.py").write_text("print('hello')\n")
            (root / "pyproject.toml").write_text('[project]\nname = "test"\n')

            bus = get_event_bus()
            state = AppState()
            ctrl = OrchestrationController(state, bus)
            info = await ctrl.onboard_project(str(root))
            assert_isinstance(info, ProjectInfo)
            assert_eq(state.project_info, info)
            assert_eq(state.project_path, str(root))

    asyncio.get_event_loop().run_until_complete(run())


# ===================================================================
# 11. SCREEN INSTANTIATION TESTS
# ===================================================================

def test_dashboard_screen_instantiation():
    from shannon.tui.screens.dashboard import DashboardScreen
    state_dict = {
        "session_id": "abc",
        "project_info": None,
        "context_utilization": {"L1": 0, "L2": 0, "L3": 0, "L4": 0},
        "memories": [],
        "task_history": [],
        "active_skills": [],
        "active_plugins": [],
        "total_skills": 0,
        "total_plugins": 0,
        "session_start": datetime.utcnow(),
    }
    screen = DashboardScreen(state_dict)
    assert_true(screen is not None)


def test_prompt_screen_instantiation():
    from shannon.tui.screens.dashboard import PromptScreen
    state_dict = {"session_id": "abc", "project_info": None}
    screen = PromptScreen(state_dict)
    assert_true(screen is not None)


def test_execution_screen_instantiation():
    from shannon.tui.screens.execution import ExecutionScreen, TEXTUAL_AVAILABLE
    if not TEXTUAL_AVAILABLE:
        # Stub Screen doesn't accept kwargs — verify the class exists
        assert_true(ExecutionScreen is not None, "ExecutionScreen class exists")
        return
    screen = ExecutionScreen(task_graph=None)
    assert_true(screen is not None)


def test_onboarding_screen_instantiation():
    from shannon.tui.screens.execution import OnboardingScreen, TEXTUAL_AVAILABLE
    if not TEXTUAL_AVAILABLE:
        assert_true(OnboardingScreen is not None, "OnboardingScreen class exists")
        return
    screen = OnboardingScreen()
    assert_true(screen is not None)


def test_memory_screen_instantiation():
    from shannon.tui.screens.panels import MemoryScreen, TEXTUAL_AVAILABLE
    if not TEXTUAL_AVAILABLE:
        assert_true(MemoryScreen is not None, "MemoryScreen class exists")
        return
    screen = MemoryScreen(memories=[], context_utilization={"L1": 0, "L2": 0, "L3": 0, "L4": 0})
    assert_true(screen is not None)


def test_validation_screen_instantiation():
    from shannon.tui.screens.panels import ValidationScreen, TEXTUAL_AVAILABLE
    if not TEXTUAL_AVAILABLE:
        assert_true(ValidationScreen is not None, "ValidationScreen class exists")
        return
    screen = ValidationScreen()
    assert_true(screen is not None)


def test_settings_screen_instantiation():
    from shannon.tui.screens.panels import SettingsScreen, TEXTUAL_AVAILABLE
    if not TEXTUAL_AVAILABLE:
        assert_true(SettingsScreen is not None, "SettingsScreen class exists")
        return
    screen = SettingsScreen()
    assert_true(screen is not None)


def test_log_screen_instantiation():
    from shannon.tui.screens.panels import LogScreen, TEXTUAL_AVAILABLE
    if not TEXTUAL_AVAILABLE:
        assert_true(LogScreen is not None, "LogScreen class exists")
        return
    screen = LogScreen()
    assert_true(screen is not None)


# ===================================================================
# 12. END-TO-END ORCHESTRATION TESTS
# ===================================================================

def test_e2e_full_task_lifecycle():
    """Full lifecycle: assess -> decompose -> execute (mock) -> validate."""
    async def run():
        bus = EventBus()
        events = []

        async def capture(event):
            events.append(event.event_type)

        await bus.subscribe(EventType.EXECUTION_STARTED, capture)
        await bus.subscribe(EventType.EXECUTION_COMPLETED, capture)
        await bus.subscribe(EventType.AGENT_SPAWNED, capture)
        await bus.subscribe(EventType.AGENT_COMPLETED, capture)

        adapter = AgentAdapter(
            model_registry=AgentAdapter.get_default_registry(),
            event_bus=bus,
        )
        memory = MemorySystem(session_id="e2e-test", event_bus=bus)

        with tempfile.TemporaryDirectory() as td:
            skills_dir = Path(td) / "skills"
            plugins_dir = Path(td) / "plugins"
            skills_dir.mkdir()
            plugins_dir.mkdir()

            skills = SkillLoader(skills_dir=skills_dir, plugins_dir=plugins_dir)
            validator = ValidationEngine(event_bus=bus)

            engine = OrchestrationEngine(
                event_bus=bus,
                agent_adapter=adapter,
                memory_system=memory,
                skill_loader=skills,
                validation_engine=validator,
            )

            graph = await engine.execute_task(prompt="fix a small bug")
            await asyncio.sleep(0.2)  # let background event tasks complete
            assert_isinstance(graph, TaskGraph)
            assert_gt(graph.completed_count, 0, "should complete nodes")
            assert_true(graph.completed_at is not None)

            assert_in(EventType.EXECUTION_STARTED, events)
            assert_in(EventType.EXECUTION_COMPLETED, events)
            assert_in(EventType.AGENT_SPAWNED, events)
            assert_in(EventType.AGENT_COMPLETED, events)

    asyncio.get_event_loop().run_until_complete(run())


def test_e2e_medium_complexity_pipeline():
    """Medium complexity: research -> analysis -> implementation -> validation."""
    async def run():
        bus = get_event_bus()
        adapter = AgentAdapter(
            model_registry=AgentAdapter.get_default_registry(),
            event_bus=bus,
        )
        memory = MemorySystem(session_id="e2e-medium", event_bus=bus)

        with tempfile.TemporaryDirectory() as td:
            skills = SkillLoader(Path(td) / "s", Path(td) / "p")
            validator = ValidationEngine(event_bus=bus)

            engine = OrchestrationEngine(
                event_bus=bus,
                agent_adapter=adapter,
                memory_system=memory,
                skill_loader=skills,
                validation_engine=validator,
            )

            graph = await engine.execute_task(
                prompt="implement a new authentication feature with API endpoints"
            )
            types_executed = {
                n.task_type for n in graph.nodes.values()
                if n.status == TaskStatus.COMPLETED
            }
            assert_in(TaskType.RESEARCH, types_executed, "should execute research")
            assert_in(TaskType.IMPLEMENTATION, types_executed, "should execute impl")

    asyncio.get_event_loop().run_until_complete(run())


def test_e2e_controller_submit_task():
    """Controller-level task submission with full wiring."""
    async def run():
        bus = get_event_bus()
        state = AppState()
        ctrl = OrchestrationController(state, bus)
        graph = await ctrl.submit_task("fix a typo")
        assert_isinstance(graph, TaskGraph)
        assert_gt(len(state.task_history), 0)
        assert_true(state.current_graph is not None)

    asyncio.get_event_loop().run_until_complete(run())


def test_e2e_memory_across_tasks():
    """Verify memories persist across task executions."""
    async def run():
        bus = get_event_bus()
        state = AppState()
        ctrl = OrchestrationController(state, bus)

        await ctrl.create_memory("decision 1", MemoryType.DECISION, ["arch"])
        await ctrl.submit_task("fix a bug")
        await ctrl.create_memory("decision 2", MemoryType.INSIGHT, ["perf"])

        results = await ctrl.search_memories("decision")
        assert_ge(len(results), 2, "both memories should persist")

    asyncio.get_event_loop().run_until_complete(run())


# ===================================================================
# 13. EVENT BUS INTEGRATION TESTS
# ===================================================================

def test_event_bus_pub_sub():
    async def run():
        bus = EventBus()
        received = []

        async def handler(event):
            received.append(event.data)

        await bus.subscribe(EventType.AGENT_PROGRESS, handler)
        await bus.emit(
            EventType.AGENT_PROGRESS,
            data={"test": True},
            source="test",
        )
        await asyncio.sleep(0.1)
        assert_gt(len(received), 0)
        assert_eq(received[-1]["test"], True)

    asyncio.get_event_loop().run_until_complete(run())


# ===================================================================
# RUNNER
# ===================================================================

def main():
    global _PASSED, _FAILED

    sections = [
        ("DATA MODELS", [
            ("ProjectInfo defaults", test_project_info_defaults),
            ("TaskNode creation", test_task_node_creation),
            ("TaskGraph operations", test_task_graph_operations),
            ("TaskGraph phases", test_task_graph_phases),
            ("AgentConfig serialization", test_agent_config_serialization),
            ("AgentState lifecycle", test_agent_state_lifecycle),
            ("MemoryEntry serialization", test_memory_entry_serialization),
            ("ContextItem serialization", test_context_item_serialization),
            ("Validation models", test_validation_models),
            ("MemoryType AGENT_OUTPUT", test_memory_type_agent_output),
            ("All enums complete", test_all_enums_complete),
        ]),
        ("COMPLEXITY ASSESSOR", [
            ("Simple prompt", test_simple_prompt),
            ("Medium prompt", test_medium_prompt),
            ("High prompt", test_high_prompt),
            ("Critical prompt", test_critical_prompt),
            ("Score breakdown", test_score_breakdown),
        ]),
        ("TASK DECOMPOSER", [
            ("Decompose simple", test_decompose_simple),
            ("Medium adds research", test_decompose_medium_adds_research),
            ("High adds architecture", test_decompose_high_adds_architecture),
            ("Critical fan-out", test_decompose_critical_fan_out),
            ("Phases wired", test_decompose_phases_wired),
            ("With project info", test_decompose_with_project_info),
        ]),
        ("MEMORY SYSTEM", [
            ("Create and search", test_memory_create_and_search),
            ("Search no match", test_memory_search_no_match),
            ("Type routing", test_memory_type_routing),
            ("Delete", test_memory_delete),
            ("Update", test_memory_update),
            ("Context tiers", test_memory_context_tiers),
            ("Context utilization", test_memory_context_utilization),
            ("Session persistence", test_memory_session_persistence),
            ("Checkpoint restore", test_memory_checkpoint_restore),
            ("L2 pruning", test_memory_l2_pruning),
        ]),
        ("SKILL LOADER", [
            ("Empty directories", test_skill_loader_empty_dirs),
            ("YAML discovery", test_skill_loader_yaml_discovery),
            ("Markdown discovery", test_skill_loader_markdown_discovery),
            ("Activation by keywords", test_skill_activation_by_keywords),
            ("Always-active skills", test_skill_always_active),
            ("Directive generation", test_skill_directive_generation),
            ("Reload", test_skill_reload),
            ("Plugin YAML discovery", test_plugin_yaml_discovery),
            ("Plugin pipeline filtering", test_plugin_pipeline_filtering),
        ]),
        ("PROJECT SCANNER", [
            ("Python project", test_scanner_python_project),
            ("JS project", test_scanner_js_project),
            ("Language detection", test_scanner_language_detection),
            ("Respects gitignore", test_scanner_respects_gitignore),
            ("Progress callback", test_scanner_progress_callback),
        ]),
        ("AGENT ADAPTER", [
            ("Mock execution", test_agent_adapter_mock_execution),
            ("Model selection", test_agent_adapter_model_selection),
            ("Events emitted", test_agent_adapter_events_emitted),
            ("System prompt building", test_agent_adapter_system_prompt_building),
        ]),
        ("VALIDATION ENGINE", [
            ("Plan creation", test_validation_plan_creation),
            ("Execution pass", test_validation_execution),
            ("Failure detection", test_validation_failure_detection),
            ("Events emitted", test_validation_events_emitted),
        ]),
        ("APP STATE", [
            ("Initialization", test_app_state_initialization),
            ("Logging", test_app_state_logging),
            ("Task history", test_app_state_task_history),
            ("Duration string", test_app_state_duration),
        ]),
        ("ORCHESTRATION CONTROLLER", [
            ("Lazy init", test_controller_lazy_init),
            ("Decompose task", test_controller_decompose_task),
            ("Memory operations", test_controller_memory_operations),
            ("Onboard project", test_controller_onboard_project),
        ]),
        ("SCREEN INSTANTIATION", [
            ("DashboardScreen", test_dashboard_screen_instantiation),
            ("PromptScreen", test_prompt_screen_instantiation),
            ("ExecutionScreen", test_execution_screen_instantiation),
            ("OnboardingScreen", test_onboarding_screen_instantiation),
            ("MemoryScreen", test_memory_screen_instantiation),
            ("ValidationScreen", test_validation_screen_instantiation),
            ("SettingsScreen", test_settings_screen_instantiation),
            ("LogScreen", test_log_screen_instantiation),
        ]),
        ("END-TO-END ORCHESTRATION", [
            ("Full task lifecycle", test_e2e_full_task_lifecycle),
            ("Medium complexity pipeline", test_e2e_medium_complexity_pipeline),
            ("Controller submit task", test_e2e_controller_submit_task),
            ("Memory across tasks", test_e2e_memory_across_tasks),
        ]),
        ("EVENT BUS", [
            ("Pub/sub", test_event_bus_pub_sub),
        ]),
    ]

    print("=" * 66)
    print("  Shannon TUI Agent Orchestration — Functional Test Suite")
    print("=" * 66)

    for section_name, tests in sections:
        print(f"\n--- {section_name} ---")
        for test_name, test_fn in tests:
            _run_test(test_name, test_fn)

    print("\n" + "=" * 66)
    total = _PASSED + _FAILED
    print(f"  Results: {_PASSED}/{total} passed, {_FAILED} failed")
    print("=" * 66)

    if _ERRORS:
        print(f"\n--- {len(_ERRORS)} FAILURE(S) ---")
        for err in _ERRORS:
            print(f"\n{err}")

    return 0 if _FAILED == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
