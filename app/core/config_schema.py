from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ssq_analyzer.generator import DEFAULT_TICKET_COUNT, STRATEGIES


@dataclass(frozen=True)
class ConfigField:
    name: str
    label: str
    field_type: str
    default: Any
    description: str = ""
    choices: tuple[str, ...] = ()
    choice_labels: dict[str, str] | None = None
    minimum: int | None = None
    maximum: int | None = None

    def choice_label(self, value: str) -> str:
        if self.choice_labels is None:
            return value
        return self.choice_labels.get(value, value)


@dataclass(frozen=True)
class ConfigSchema:
    fields: tuple[ConfigField, ...]

    def field(self, name: str) -> ConfigField:
        for field in self.fields:
            if field.name == name:
                return field
        raise KeyError(name)


def default_schema() -> ConfigSchema:
    return ConfigSchema(
        fields=(
            ConfigField(
                name="command",
                label="执行类型",
                field_type="choice",
                default="generate",
                choices=("generate", "analyze", "backtest", "compare", "fetch"),
                choice_labels={
                    "generate": "生成推荐号码",
                    "analyze": "历史数据分析",
                    "backtest": "策略回测",
                    "compare": "策略对比",
                    "fetch": "刷新历史数据",
                },
                description="选择生成号码、历史分析、回测、策略对比或刷新数据。",
            ),
            ConfigField(
                name="history_limit",
                label="历史期数",
                field_type="int",
                default=0,
                minimum=0,
                description="使用最近多少期历史数据；0 表示全部历史。",
            ),
            ConfigField(
                name="strategy",
                label="分析模型/算法",
                field_type="choice",
                default="balanced",
                choices=tuple(sorted(STRATEGIES | {"all"})),
                choice_labels={
                    "all": "全部策略",
                    "balanced": "均衡模型",
                    "cold": "冷号模型",
                    "deep-learning": "实验神经打分模型",
                    "ensemble": "综合模型",
                    "hot": "热号模型",
                    "liuyao": "六爻娱乐模型",
                    "omission": "遗漏模型",
                    "random": "随机模型",
                    "recent": "近期活跃模型",
                    "weighted": "频率遗漏加权模型",
                },
                description="对应原命令行 --strategy 参数。",
            ),
            ConfigField(
                name="count",
                label="生成几组号码",
                field_type="int",
                default=DEFAULT_TICKET_COUNT,
                minimum=1,
                maximum=100,
                description="对应原命令行 --count 参数。",
            ),
            ConfigField(
                name="seed",
                label="随机种子",
                field_type="optional_int",
                default=None,
                description="对应原命令行 --seed 参数；留空则每次随机。",
            ),
            ConfigField(
                name="window",
                label="回测窗口",
                field_type="int",
                default=20,
                minimum=1,
                maximum=500,
                description="对应原命令行 --window 参数。",
            ),
            ConfigField("use_hot", "使用热号", "bool", False, "把热号信息作为结果依据展示。"),
            ConfigField("use_cold", "使用冷号", "bool", False, "把冷号信息作为结果依据展示。"),
            ConfigField("use_sum_analysis", "和值分析", "bool", True, "为每组号码展示红球和值。"),
            ConfigField("use_parity_ratio", "奇偶比", "bool", True, "为每组号码展示奇偶比例。"),
            ConfigField("use_range_ratio", "区间比", "bool", True, "为每组号码展示低中高区间比例。"),
            ConfigField("use_consecutive", "连号分析", "bool", True, "为每组号码展示连号数量。"),
            ConfigField("filter_duplicates", "过滤重复结果", "bool", True, "去掉完全重复的推荐号码。"),
        )
    )
