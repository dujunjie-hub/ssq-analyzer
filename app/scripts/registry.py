from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from app.core.analyzer_service import AnalyzerConfig, AnalyzerResult, AnalyzerService
from app.core.config_schema import ConfigField, ConfigSchema, default_schema
from ssq_analyzer.budget import BudgetPlan, calculate_budget_plan


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
            liuyao_input=str(params.get("liuyao_input", "")),
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
    registry.register(
        ScriptDefinition(
            script_id="ssq_budget",
            name="复式 / 胆拖预算计算器",
            description="按预算生成合法复式或胆拖覆盖方案，并展示费用和一等奖理论概率。",
            schema=ConfigSchema(
                fields=(
                    ConfigField(
                        "mode",
                        "玩法",
                        "choice",
                        "compound",
                        choices=("compound", "dantuo"),
                        choice_labels={"compound": "复式", "dantuo": "胆拖"},
                    ),
                    ConfigField("budget", "预算（元）", "int", 100, minimum=0, maximum=100_000_000),
                    ConfigField("red_dan_count", "红胆数量（仅胆拖）", "int", 1, "范围 1-5。", minimum=1, maximum=5),
                )
            ),
            execute=_run_budget_calculator,
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


def _run_budget_calculator(params: dict[str, Any], emit_log: Callable[[str], None]) -> dict[str, Any]:
    plan = calculate_budget_plan(
        mode=str(params.get("mode", "compound")),
        budget=int(params.get("budget", 0)),
        red_dan_count=int(params.get("red_dan_count", 1)),
    )
    emit_log(f"已按 {plan.budget} 元预算计算 {('复式' if plan.mode == 'compound' else '胆拖')}覆盖方案")
    scheme = f"红球 {plan.red_count} 个，蓝球 {plan.blue_count} 个"
    if plan.mode == "dantuo":
        scheme = f"红胆 {plan.red_dan_count} 个，红拖 {plan.red_tuo_count} 个，蓝球 {plan.blue_count} 个"
    probability = _first_prize_probability_text(plan)
    return {
        "title": "复式 / 胆拖预算计算器",
        "summary_text": "\n".join(
            [
                f"玩法：{'复式' if plan.mode == 'compound' else '胆拖'}",
                f"预算：{plan.budget} 元",
                f"推荐方案：{scheme}",
                f"可覆盖组合：{plan.combination_count} 注",
                f"实际费用：{plan.cost} 元，剩余预算：{plan.remaining_budget} 元",
                f"一等奖理论概率：{probability}",
                "说明：复式和胆拖不会改变单注概率；它们只是一次购买多个单式组合，避免手工漏掉组合。",
            ]
        ),
        "rows": [
            {
                "玩法": "复式" if plan.mode == "compound" else "胆拖",
                "预算（元）": plan.budget,
                "红球数量": plan.red_count,
                "红胆数量": plan.red_dan_count or "",
                "红拖数量": plan.red_tuo_count or "",
                "蓝球数量": plan.blue_count,
                "覆盖组合数（注）": plan.combination_count,
                "实际费用（元）": plan.cost,
                "剩余预算（元）": plan.remaining_budget,
                "一等奖理论概率": probability,
            }
        ],
        "metadata": {"first_prize_combinations": plan.first_prize_denominator},
    }


def _first_prize_probability_text(plan: BudgetPlan) -> str:
    if not plan.combination_count:
        return "预算不足 2 元，无法覆盖有效组合"
    return (
        f"{plan.combination_count} / {plan.first_prize_denominator}"
        f"（约 1 / {plan.first_prize_denominator / plan.combination_count:,.0f}，{plan.first_prize_probability:.6%}）"
    )
