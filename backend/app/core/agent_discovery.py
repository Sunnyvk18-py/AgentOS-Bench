import ast
import importlib
import importlib.util
import inspect
import logging
import re
from pathlib import Path
from typing import Any

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)

AGENTS_DIR = Path(__file__).resolve().parent.parent / "agents"
SKIP_FILES = frozenset({"__init__.py", "base.py", "TEMPLATE.py"})
BUILTIN_MODULES = (
    ("mock", "app.agents.mock_agent", "MockAgent"),
    ("langgraph", "app.agents.langgraph_agent", "LangGraphAgent"),
)
BUILTIN_NAMES = frozenset(name for name, _, _ in BUILTIN_MODULES)
SAFE_FILENAME = re.compile(r"^[a-z][a-z0-9_]*\.py$")


def _extract_metadata(cls: type[BaseAgent], fallback_name: str) -> dict[str, Any]:
    return {
        "name": getattr(cls, "__agent_name__", fallback_name),
        "description": getattr(cls, "__agent_description__", cls.__doc__ or ""),
        "config_schema": getattr(cls, "__agent_config_schema__", {}),
        "is_built_in": fallback_name in BUILTIN_NAMES
        or getattr(cls, "__agent_name__", fallback_name) in BUILTIN_NAMES,
    }


def validate_agent_source(source: str) -> dict[str, Any]:
    errors: list[str] = []
    agent_name: str | None = None
    description: str | None = None

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return {
            "valid": False,
            "errors": [f"Syntax error: {exc.msg} (line {exc.lineno})"],
            "agent_name": None,
            "description": None,
        }

    agent_classes: list[ast.ClassDef] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(base.attr)
        if "BaseAgent" in bases:
            agent_classes.append(node)

    if not agent_classes:
        errors.append("No class inheriting from BaseAgent found.")
    elif len(agent_classes) > 1:
        errors.append("Multiple BaseAgent subclasses found; only one is allowed per file.")

    if agent_classes:
        cls_node = agent_classes[0]
        execute_methods = [
            n
            for n in cls_node.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "execute"
        ]
        if not execute_methods:
            errors.append("BaseAgent subclass must implement async execute(self, task: str).")
        elif not isinstance(execute_methods[0], ast.AsyncFunctionDef):
            errors.append("execute() must be declared async.")

        for node in cls_node.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id == "__agent_name__" and isinstance(node.value, ast.Constant):
                            agent_name = str(node.value.value)
                        if target.id == "__agent_description__" and isinstance(
                            node.value, ast.Constant
                        ):
                            description = str(node.value.value)

        if not agent_name:
            agent_name = cls_node.name.replace("Agent", "").lower() or cls_node.name.lower()

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "agent_name": agent_name,
        "description": description,
    }


def _load_module_from_file(path: Path):
    module_name = f"agent_plugin_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def discover_agents() -> tuple[dict[str, type[BaseAgent]], dict[str, dict[str, Any]]]:
    registry: dict[str, type[BaseAgent]] = {}
    metadata: dict[str, dict[str, Any]] = {}

    for name, module_path, class_name in BUILTIN_MODULES:
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            if not inspect.isclass(cls) or not issubclass(cls, BaseAgent):
                continue
            registry[name] = cls
            meta = _extract_metadata(cls, name)
            meta["is_built_in"] = True
            metadata[name] = meta
        except Exception as exc:
            logger.warning("Failed to load built-in agent %s: %s", name, exc)

    for path in sorted(AGENTS_DIR.glob("*.py")):
        if path.name in SKIP_FILES:
            continue
        if path.stem in {"mock_agent", "langgraph_agent"}:
            continue
        try:
            module = _load_module_from_file(path)
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if obj is BaseAgent or not issubclass(obj, BaseAgent):
                    continue
                agent_name = getattr(obj, "__agent_name__", path.stem)
                if agent_name in registry:
                    logger.warning("Skipping duplicate agent name '%s' in %s", agent_name, path)
                    continue
                registry[agent_name] = obj
                meta = _extract_metadata(obj, agent_name)
                meta["is_built_in"] = False
                metadata[agent_name] = meta
                break
        except Exception as exc:
            logger.warning("Auto-discovery skipped %s: %s", path.name, exc)

    return registry, metadata


def safe_agent_filename(filename: str) -> str:
    name = Path(filename).name
    if not SAFE_FILENAME.match(name):
        raise ValueError(
            "Filename must be lowercase snake_case ending in .py (e.g. my_agent.py)"
        )
    return name
