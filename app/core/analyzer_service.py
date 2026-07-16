from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from ssq_analyzer.backtest import backtest_rows, compare_strategies, run_backtest
from ssq_analyzer.cli import DISCLAIMER, EXPERIMENTAL_WARNING, LIUYAO_WARNING, _top_items
from ssq_analyzer.data import DEFAULT_HISTORY_PATH, DataFetchError, fetch_draws, load_draws, save_draws
from ssq_analyzer.generator import DEFAULT_TICKET_COUNT, STRATEGIES, generate_advanced_liuyao_tickets, generate_liuyao_tickets, generate_tickets
from ssq_analyzer.models import Draw, Ticket
from ssq_analyzer.personal import with_long_term_fixed_first
from ssq_analyzer.schedule import format_next_draw_time, history_staleness_warning
from ssq_analyzer.stats import analysis_rows, analyze_draws


@dataclass(frozen=True)
class AnalyzerConfig:
    command: str = "generate"
    strategy: str = "balanced"
    count: int = DEFAULT_TICKET_COUNT
    seed: int | None = None
    liuyao_input: str = ""
    window: int = 20
    history_limit: int = 0
    use_hot: bool = False
    use_cold: bool = False
    use_sum_analysis: bool = True
    use_parity_ratio: bool = True
    use_range_ratio: bool = True
    use_consecutive: bool = True
    filter_duplicates: bool = True
    output_path: Path | None = None


@dataclass(frozen=True)
class AnalyzerResult:
    command: str
    title: str
    rows: list[dict[str, object]]
    logs: list[str] = field(default_factory=list)
    summary_text: str = ""
    metadata: dict[str, object] = field(default_factory=dict)


LogEmitter = Callable[[str], None]


class AnalyzerService:
    def __init__(
        self,
        draw_loader: Callable[[], list[Draw]] = load_draws,
        draw_fetcher: Callable[[], list[Draw]] = fetch_draws,
        draw_saver: Callable[[list[Draw], Path], Path] = save_draws,
    ) -> None:
        self._draw_loader = draw_loader
        self._draw_fetcher = draw_fetcher
        self._draw_saver = draw_saver

    def run(self, config: AnalyzerConfig, emit_log: LogEmitter | None = None) -> AnalyzerResult:
        logs: list[str] = []

        def log(message: str) -> None:
            logs.append(message)
            if emit_log is not None:
                emit_log(message)

        try:
            if config.command == "fetch":
                return self._fetch(config, logs, log)

            draws = self._draws_for_config(config)
            log(f"加载历史数据：{len(draws)} 期")
            log(format_next_draw_time())

            if config.command == "analyze":
                return self._analyze(draws, logs)
            if config.command == "generate":
                return self._generate(draws, config, logs)
            if config.command == "backtest":
                return self._backtest(draws, config, logs)
            if config.command == "compare":
                return self._compare(draws, config, logs)
            raise ValueError(f"不支持的执行类型：{config.command}")
        except Exception as error:
            log(f"执行失败：{error}")
            raise

    def _draws_for_config(self, config: AnalyzerConfig) -> list[Draw]:
        draws = sorted(self._draw_loader(), key=lambda draw: draw.issue)
        if config.command in {"backtest", "compare"}:
            return draws
        if config.history_limit and config.history_limit > 0:
            return draws[-config.history_limit :]
        return draws

    def _fetch(self, config: AnalyzerConfig, logs: list[str], log: LogEmitter) -> AnalyzerResult:
        output = config.output_path or DEFAULT_HISTORY_PATH
        try:
            draws = self._draw_fetcher()
        except DataFetchError:
            raise
        saved_path = self._draw_saver(draws, output)
        log(f"已保存 {len(draws)} 期历史数据：{saved_path}")
        return AnalyzerResult(
            command="fetch",
            title="刷新历史数据",
            rows=[{"draw_count": len(draws), "output": str(saved_path)}],
            logs=logs,
            summary_text=f"已保存 {len(draws)} 期历史数据：{saved_path}",
            metadata={"output": str(saved_path)},
        )

    def _analyze(self, draws: list[Draw], logs: list[str]) -> AnalyzerResult:
        result = analyze_draws(draws)
        rows = analysis_rows(result)
        summary_lines = [
            DISCLAIMER,
            f"共加载 {len(draws)} 期数据",
            f"红球最高频：{_top_items(result.red_frequency, 6)}",
            f"蓝球最高频：{_top_items(result.blue_frequency, 3)}",
        ]
        return AnalyzerResult(
            command="analyze",
            title="历史数据分析",
            rows=rows,
            logs=logs,
            summary_text="\n".join(summary_lines),
            metadata={
                "draw_count": len(draws),
                "parity_counts": result.parity_counts,
                "range_counts": result.range_counts,
                "consecutive_counts": result.consecutive_counts,
            },
        )

    def _generate(self, draws: list[Draw], config: AnalyzerConfig, logs: list[str]) -> AnalyzerResult:
        if config.strategy not in STRATEGIES:
            raise ValueError(f"生成号码不支持策略：{config.strategy}")

        reading = None
        cast_input = config.liuyao_input.strip()
        if config.strategy == "liuyao":
            reading, tickets = generate_liuyao_tickets(count=config.count, seed=config.seed, cast_input=cast_input)
        elif config.strategy == "liuyao-advanced":
            reading, tickets = generate_advanced_liuyao_tickets(count=config.count, seed=config.seed, cast_input=cast_input)
        else:
            tickets = generate_tickets(draws, strategy=config.strategy, count=config.count, seed=config.seed)
        tickets = with_long_term_fixed_first(tickets)
        if config.filter_duplicates:
            tickets = _dedupe_tickets(tickets)

        rows: list[dict[str, object]] = []
        summary_lines = [DISCLAIMER]
        if draws:
            latest = sorted(draws, key=lambda draw: draw.issue)[-1]
            summary_lines.append(f"上一期开奖结果：{latest.issue} 红球 {latest.ticket.red_text()}  蓝球 {latest.ticket.blue_text()}")
            warning = history_staleness_warning(latest.draw_date)
            if warning:
                summary_lines.append(warning)
            summary_lines.extend(_previous_prediction_lines(draws, config))
        if config.strategy == "deep-learning":
            summary_lines.append(EXPERIMENTAL_WARNING)
        metadata: dict[str, object] = {"strategy": config.strategy, "seed": config.seed}
        if reading is not None:
            summary_lines.extend(
                [
                    LIUYAO_WARNING,
                    *([f"起卦输入：{cast_input}"] if cast_input else []),
                    f"本卦：{reading.primary_number} {reading.primary_hexagram}",
                    f"动爻：{reading.moving_lines_text}",
                    f"变卦：{reading.changed_number} {reading.changed_hexagram}",
                    *_advanced_liuyao_lines(reading),
                ]
            )
            metadata.update(
                {
                    "primary_hexagram": reading.primary_hexagram,
                    "changed_hexagram": reading.changed_hexagram,
                    "moving_lines": reading.moving_lines_text,
                    "line_values": reading.line_values_text,
                    "use_god": reading.use_god,
                    "world_line": reading.world_line,
                    "responding_line": reading.responding_line,
                    "cast_input": cast_input,
                }
            )

        summary_lines.append("本期预测号码：")
        for index, ticket in enumerate(tickets, start=1):
            basis = _ticket_basis(ticket, config)
            summary_lines.append(f"{index}. 红球 {ticket.red_text()}  蓝球 {ticket.blue_text()}  依据：{basis}")
            rows.append(
                {
                    "index": index,
                    "strategy": config.strategy,
                    "seed": "" if config.seed is None else config.seed,
                    "cast_input": cast_input if reading is not None else "",
                    "red": ticket.red_text(),
                    "blue": ticket.blue_text(),
                    "basis": basis,
                    "primary_hexagram": "" if reading is None else reading.primary_hexagram,
                    "changed_hexagram": "" if reading is None else reading.changed_hexagram,
                    "moving_lines": "" if reading is None else reading.moving_lines_text,
                    "line_values": "" if reading is None else reading.line_values_text,
                    "use_god": "" if reading is None else reading.use_god,
                    "world_line": "" if reading is None else reading.world_line,
                    "responding_line": "" if reading is None else reading.responding_line,
                }
            )
        return AnalyzerResult(
            command="generate",
            title="生成推荐号码",
            rows=rows,
            logs=logs,
            summary_text="\n".join(summary_lines),
            metadata=metadata,
        )

    def _backtest(self, draws: list[Draw], config: AnalyzerConfig, logs: list[str]) -> AnalyzerResult:
        if config.strategy == "all":
            rows = compare_strategies(draws, strategies=sorted(STRATEGIES), count=config.count, seed=config.seed, window=config.window)
            summary = _strategy_summary_text(rows, config.count)
            return AnalyzerResult("backtest", "全部策略回测", rows, logs, summary, {"strategy": "all"})

        results = run_backtest(draws, strategy=config.strategy, count=config.count, seed=config.seed, window=config.window)
        rows = backtest_rows(results, strategy=config.strategy)
        wins = sum(1 for row in rows if row["tier"] != "none")
        summary = "\n".join([DISCLAIMER, f"回测期数：{len(results)}，每期生成 {config.count} 组", *_backtest_detail_lines(results), f"命中奖项记录：{wins}"])
        return AnalyzerResult("backtest", "策略回测", rows, logs, summary, {"strategy": config.strategy, "wins": wins})

    def _compare(self, draws: list[Draw], config: AnalyzerConfig, logs: list[str]) -> AnalyzerResult:
        strategies = ["balanced", "hot", "cold", "omission", "recent", "ensemble", "deep-learning", "liuyao", "liuyao-advanced"]
        rows = compare_strategies(draws, strategies=strategies, count=config.count, seed=config.seed, window=config.window)
        return AnalyzerResult("compare", "策略对比", rows, logs, _strategy_summary_text(rows, config.count), {"strategies": strategies})


def _dedupe_tickets(tickets: list[Ticket]) -> list[Ticket]:
    seen: set[tuple[tuple[int, ...], int]] = set()
    unique: list[Ticket] = []
    for ticket in tickets:
        key = (ticket.red, ticket.blue)
        if key in seen:
            continue
        seen.add(key)
        unique.append(ticket)
    return unique


def _ticket_basis(ticket: Ticket, config: AnalyzerConfig) -> str:
    parts = [f"策略 {config.strategy}"]
    if config.use_sum_analysis:
        parts.append(f"和值 {sum(ticket.red)}")
    if config.use_parity_ratio:
        odd = sum(1 for ball in ticket.red if ball % 2)
        parts.append(f"奇偶 {odd}:{6 - odd}")
    if config.use_range_ratio:
        low = sum(1 for ball in ticket.red if ball <= 11)
        mid = sum(1 for ball in ticket.red if 12 <= ball <= 22)
        high = sum(1 for ball in ticket.red if ball >= 23)
        parts.append(f"区间 {low}:{mid}:{high}")
    if config.use_consecutive:
        consecutive = sum(1 for left, right in zip(ticket.red, ticket.red[1:]) if right == left + 1)
        parts.append(f"连号 {consecutive}")
    if config.use_hot:
        parts.append("参考热号权重")
    if config.use_cold:
        parts.append("参考冷号权重")
    return "；".join(parts)


def _previous_prediction_lines(draws: list[Draw], config: AnalyzerConfig) -> list[str]:
    ordered = sorted(draws, key=lambda draw: draw.issue)
    if len(ordered) < 2:
        return []
    latest = ordered[-1]
    if config.strategy == "liuyao":
        _, tickets = generate_liuyao_tickets(count=config.count, seed=config.seed, cast_input=config.liuyao_input)
    elif config.strategy == "liuyao-advanced":
        _, tickets = generate_advanced_liuyao_tickets(count=config.count, seed=config.seed, cast_input=config.liuyao_input)
    else:
        tickets = generate_tickets(ordered[:-1], strategy=config.strategy, count=config.count, seed=config.seed)
    tickets = with_long_term_fixed_first(tickets)
    if config.filter_duplicates:
        tickets = _dedupe_tickets(tickets)

    lines = ["上一期预测号码："]
    for index, ticket in enumerate(tickets, start=1):
        red_hits = _red_hit_text(ticket, latest.ticket)
        blue_hit = latest.ticket.blue_text() if ticket.blue == latest.ticket.blue else "无"
        lines.append(
            f"  预测 {index}：红球 {ticket.red_text()}  蓝球 {ticket.blue_text()}；"
            f"命中红球 {red_hits or '无'}；命中蓝球 {blue_hit}"
        )
    return lines


def _advanced_liuyao_lines(reading) -> list[str]:
    if not reading.use_god:
        return []
    najia = "；".join(
        f"{index + 1}:{line}/{element}/{relative}"
        for index, (line, element, relative) in enumerate(zip(reading.najia_lines, reading.line_elements, reading.six_relatives))
    )
    return [
        f"世应：世爻 {reading.world_line}，应爻 {reading.responding_line}",
        f"用神：{reading.use_god}",
        f"互卦：{reading.hidden_hexagram}",
        f"错卦：{reading.opposite_hexagram}",
        f"纳甲六亲：{najia}",
    ]


def _backtest_detail_lines(results) -> list[str]:
    lines: list[str] = []
    for result in results:
        lines.append(f"{result.issue} 开奖：红球 {result.actual.red_text()}  蓝球 {result.actual.blue_text()}")
        for index, ticket_result in enumerate(result.generated_tickets, start=1):
            red_hits = _red_hit_text(ticket_result.ticket, result.actual)
            blue_hit = result.actual.blue_text() if ticket_result.blue_hit else "无"
            lines.append(
                f"  预测 {index}：红球 {ticket_result.ticket.red_text()}  蓝球 {ticket_result.ticket.blue_text()}；"
                f"命中红球 {red_hits or '无'}；命中蓝球 {blue_hit}"
            )
    return lines


def _red_hit_text(ticket: Ticket, actual: Ticket) -> str:
    hits = sorted(set(ticket.red) & set(actual.red))
    return " ".join(f"{ball:02d}" for ball in hits)


def _strategy_summary_text(rows: list[dict[str, object]], count: int) -> str:
    lines = [DISCLAIMER, EXPERIMENTAL_WARNING, LIUYAO_WARNING, f"策略对比：{len(rows)} 个策略，每期生成 {count} 组"]
    for row in rows:
        wins = sum(int(row[f"tier_{tier}"]) for tier in ["first", "second", "third", "fourth", "fifth", "sixth"])
        lines.append(f"{row['strategy']}: 票数 {row['total_tickets']}，蓝球命中率 {row['blue_hit_rate']}，中奖记录 {wins}")
    return "\n".join(lines)
