from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from app.core.analyzer_service import AnalyzerConfig, AnalyzerResult, AnalyzerService
from app.core.config_schema import ConfigSchema, default_schema


ScriptExecute = Callable[[dict[str, Any], Callable[[str], None]], AnalyzerResult | dict[str, Any]]


@dataclass(frozen=True)
class ScriptDefinition:
    script_id: str
    name: str
    description: str
    schema: ConfigSchema
    execute: ScriptExecute


class ScriptRegistry:
    def __init__(self) -> None:
        self._scripts: dict[str, ScriptDefinition] = {}

    def register(self, definition: ScriptDefinition) -> None:
        if not definition.script_id:
            raise ValueError("script_id is required")
        if definition.script_id in self._scripts:
            raise ValueError(f"script already registered: {definition.script_id}")
        self._scripts[definition.script_id] = definition

    def list(self) -> list[ScriptDefinition]:
        return list(self._scripts.values())

    def get(self, script_id: str) -> ScriptDefinition:
        try:
            return self._scripts[script_id]
        except KeyError as error:
            raise KeyError(f"unknown script: {script_id}") from error

    def discover(self, directory: Path | str) -> None:
        root = Path(directory)
        if not root.exists():
            return
        for path in sorted(root.glob("*.py")):
            if path.name.startswith("_"):
                continue
            module_name = f"ssq_app_script_{path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "register"):
                module.register(self)
            elif hasattr(module, "SCRIPT"):
                if module.SCRIPT.script_id not in self._scripts:
                    self.register(module.SCRIPT)

    def run(self, script_id: str, params: dict[str, Any]) -> AnalyzerResult:
        logs: list[str] = []

        def emit_log(message: str) -> None:
            logs.append(message)

        raw = self.get(script_id).execute(params, emit_log)
        if isinstance(raw, AnalyzerResult):
            return AnalyzerResult(
                command=raw.command,
                title=raw.title,
                rows=raw.rows,
                logs=logs + raw.logs,
                summary_text=raw.summary_text,
                metadata=raw.metadata,
            )
        return AnalyzerResult(
            command=script_id,
            title=str(raw.get("title", self.get(script_id).name)),
            rows=list(raw.get("rows", [])),
            logs=logs + list(raw.get("logs", [])),
            summary_text=str(raw.get("summary_text", "")),
            metadata=dict(raw.get("metadata", {})),
        )


def create_default_registry(service: AnalyzerService | None = None) -> ScriptRegistry:
    service = service or AnalyzerService()
    registry = ScriptRegistry()

    def run_ssq(params: dict[str, Any], emit_log: Callable[[str], None]) -> AnalyzerResult:
        config = AnalyzerConfig(
            command=str(params.get("command", "generate")),
            strategy=str(params.get("strategy", "balanced")),
            count=int(params.get("count", 5)),
            seed=_optional_int(params.get("seed")),
            window=int(params.get("window", 20)),
            history_limit=int(params.get("history_limit", 0)),
            use_hot=bool(params.get("use_hot", False)),
            use_cold=bool(params.get("use_cold", False)),
            use_sum_analysis=bool(params.get("use_sum_analysis", True)),
            use_parity_ratio=bool(params.get("use_parity_ratio", True)),
            use_range_ratio=bool(params.get("use_range_ratio", True)),
            use_consecutive=bool(params.get("use_consecutive", True)),
            filter_duplicates=bool(params.get("filter_duplicates", True)),
        )
        return service.run(config, emit_log=emit_log)

    registry.register(
        ScriptDefinition(
            script_id="ssq",
            name="双色球分析/预测",
            description="内置双色球历史分析、娱乐选号、回测和策略对比。",
            schema=default_schema(),
            execute=run_ssq,
        )
    )
    project_root = Path(__file__).resolve().parents[2]
    registry.discover(project_root / "app" / "scripts" / "plugins")
    registry.discover(project_root / "scripts")
    return registry


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)
