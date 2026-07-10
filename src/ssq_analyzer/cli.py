from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ssq_analyzer.backtest import backtest_rows, compare_strategies, run_backtest
from ssq_analyzer.data import DEFAULT_HISTORY_PATH, DataFetchError, fetch_draws, load_draws, save_draws
from ssq_analyzer.exporters import export_rows
from ssq_analyzer.generator import DEFAULT_TICKET_COUNT, STRATEGIES, generate_advanced_liuyao_tickets, generate_liuyao_tickets, generate_tickets
from ssq_analyzer.schedule import format_next_draw_time
from ssq_analyzer.stats import analysis_rows, analyze_draws


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs"
DISCLAIMER = "娱乐参考：双色球开奖结果具有随机性，本工具不提供可靠预测或中奖保证。"
EXPERIMENTAL_WARNING = "实验策略：deep-learning 使用轻量神经打分器，仅供研究和娱乐，不代表预测优势。"
LIUYAO_WARNING = "六爻灵感娱乐策略：不属于传统六爻断卦或科学预测，不代表中奖优势。"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ssq", description="双色球历史分析、娱乐选号和回测工具")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser("fetch", help="刷新历史开奖数据")
    fetch_parser.add_argument("--output", type=Path, default=DEFAULT_HISTORY_PATH)
    fetch_parser.set_defaults(handler=_handle_fetch)

    analyze_parser = subparsers.add_parser("analyze", help="分析历史开奖数据")
    _add_export_options(analyze_parser, "analysis")
    analyze_parser.set_defaults(handler=_handle_analyze)

    generate_parser = subparsers.add_parser("generate", help="生成娱乐参考号码")
    generate_parser.add_argument("--strategy", choices=sorted(STRATEGIES), default="balanced")
    generate_parser.add_argument("--count", type=int, default=DEFAULT_TICKET_COUNT)
    generate_parser.add_argument("--seed", type=int)
    _add_export_options(generate_parser, "tickets")
    generate_parser.set_defaults(handler=_handle_generate)

    backtest_parser = subparsers.add_parser("backtest", help="回测选号策略")
    backtest_parser.add_argument("--strategy", choices=sorted(STRATEGIES | {"all"}), default="balanced")
    backtest_parser.add_argument("--count", type=int, default=DEFAULT_TICKET_COUNT)
    backtest_parser.add_argument("--seed", type=int)
    backtest_parser.add_argument("--window", type=int, default=20)
    _add_export_options(backtest_parser, "backtest")
    backtest_parser.set_defaults(handler=_handle_backtest)

    compare_parser = subparsers.add_parser("compare", help="对比多种选号策略")
    compare_parser.add_argument("--count", type=int, default=DEFAULT_TICKET_COUNT)
    compare_parser.add_argument("--seed", type=int)
    compare_parser.add_argument("--window", type=int, default=20)
    _add_export_options(compare_parser, "compare")
    compare_parser.set_defaults(handler=_handle_compare)

    return parser


def _add_export_options(parser: argparse.ArgumentParser, default_name: str) -> None:
    parser.add_argument("--format", choices=["csv", "xlsx"], default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.set_defaults(default_name=default_name)


def _handle_fetch(args: argparse.Namespace) -> int:
    try:
        draws = fetch_draws()
    except DataFetchError as error:
        print(f"历史数据更新失败：{error}", file=sys.stderr)
        return 1
    save_draws(draws, args.output)
    print(f"已保存 {len(draws)} 期历史数据：{args.output}")
    return 0


def _handle_analyze(args: argparse.Namespace) -> int:
    draws = load_draws()
    result = analyze_draws(draws)
    rows = analysis_rows(result)
    print(format_next_draw_time())
    print(f"共加载 {len(draws)} 期数据")
    print(f"红球最高频：{_top_items(result.red_frequency, 6)}")
    print(f"蓝球最高频：{_top_items(result.blue_frequency, 3)}")
    _export_if_requested(rows, args)
    return 0


def _handle_generate(args: argparse.Namespace) -> int:
    draws = load_draws()
    reading = None
    if args.strategy == "liuyao":
        reading, tickets = generate_liuyao_tickets(count=args.count, seed=args.seed)
    elif args.strategy == "liuyao-advanced":
        reading, tickets = generate_advanced_liuyao_tickets(count=args.count, seed=args.seed)
    else:
        tickets = generate_tickets(draws, strategy=args.strategy, count=args.count, seed=args.seed)
    print(DISCLAIMER)
    print(format_next_draw_time())
    if args.strategy == "deep-learning":
        print(EXPERIMENTAL_WARNING)
    if reading is not None:
        print(LIUYAO_WARNING)
        print(f"本卦：{reading.primary_number} {reading.primary_hexagram}")
        print(f"动爻：{reading.moving_lines_text}")
        print(f"变卦：{reading.changed_number} {reading.changed_hexagram}")
        if reading.use_god:
            print(f"世应：世爻 {reading.world_line}，应爻 {reading.responding_line}")
            print(f"用神：{reading.use_god}")
            print(f"互卦：{reading.hidden_hexagram}")
            print(f"错卦：{reading.opposite_hexagram}")
            print("纳甲六亲：" + "；".join(f"{index + 1}:{line}/{relative}" for index, (line, relative) in enumerate(zip(reading.najia_lines, reading.six_relatives))))
    rows = []
    for index, ticket in enumerate(tickets, start=1):
        print(f"{index}. 红球 {ticket.red_text()}  蓝球 {ticket.blue_text()}")
        rows.append(
            {
                "index": index,
                "strategy": args.strategy,
                "seed": "" if args.seed is None else args.seed,
                "red": ticket.red_text(),
                "blue": ticket.blue_text(),
                "disclaimer": DISCLAIMER,
                "primary_hexagram": "" if reading is None else reading.primary_hexagram,
                "changed_hexagram": "" if reading is None else reading.changed_hexagram,
                "moving_lines": "" if reading is None else reading.moving_lines_text,
                "line_values": "" if reading is None else reading.line_values_text,
                "use_god": "" if reading is None else reading.use_god,
                "world_line": "" if reading is None else reading.world_line,
                "responding_line": "" if reading is None else reading.responding_line,
            }
        )
    _export_if_requested(rows, args)
    return 0


def _handle_backtest(args: argparse.Namespace) -> int:
    draws = load_draws()
    if args.strategy == "all":
        rows = compare_strategies(draws, strategies=sorted(STRATEGIES), count=args.count, seed=args.seed, window=args.window)
        print(DISCLAIMER)
        print(format_next_draw_time())
        print(EXPERIMENTAL_WARNING)
        print(LIUYAO_WARNING)
        print(f"策略对比：{len(rows)} 个策略，每期生成 {args.count} 组")
        _print_strategy_summaries(rows)
        _export_if_requested(rows, args)
        return 0

    results = run_backtest(draws, strategy=args.strategy, count=args.count, seed=args.seed, window=args.window)
    rows = backtest_rows(results, strategy=args.strategy)
    print(DISCLAIMER)
    print(format_next_draw_time())
    if args.strategy == "deep-learning":
        print(EXPERIMENTAL_WARNING)
    if args.strategy == "liuyao":
        print(LIUYAO_WARNING)
    print(f"回测期数：{len(results)}，每期生成 {args.count} 组")
    if rows:
        wins = sum(1 for row in rows if row["tier"] != "none")
        print(f"命中奖项记录：{wins}")
    _export_if_requested(rows, args)
    return 0


def _handle_compare(args: argparse.Namespace) -> int:
    draws = load_draws()
    strategies = ["balanced", "hot", "cold", "omission", "recent", "ensemble", "deep-learning", "liuyao", "liuyao-advanced"]
    rows = compare_strategies(draws, strategies=strategies, count=args.count, seed=args.seed, window=args.window)
    print(DISCLAIMER)
    print(format_next_draw_time())
    print(EXPERIMENTAL_WARNING)
    print(LIUYAO_WARNING)
    print(f"策略对比：{len(rows)} 个策略，每期生成 {args.count} 组")
    _print_strategy_summaries(rows)
    _export_if_requested(rows, args)
    return 0


def _export_if_requested(rows: list[dict[str, object]], args: argparse.Namespace) -> None:
    if args.output is None and args.format is None:
        return
    suffix = args.format or "csv"
    output = args.output or OUTPUT_DIR / f"{args.default_name}.{suffix}"
    if output.suffix.lower() not in {".csv", ".xlsx"}:
        output = output.with_suffix(f".{suffix}")
    export_rows(rows, output)
    print(f"已导出：{output}")


def _top_items(values: dict[int, int], count: int) -> str:
    top = sorted(values.items(), key=lambda item: (-item[1], item[0]))[:count]
    return ", ".join(f"{ball:02d}({frequency})" for ball, frequency in top)


def _print_strategy_summaries(rows: list[dict[str, object]]) -> None:
    for row in rows:
        print(
            f"{row['strategy']}: 票数 {row['total_tickets']}，"
            f"蓝球命中率 {row['blue_hit_rate']}，中奖记录 {sum(int(row[f'tier_{tier}']) for tier in ['first', 'second', 'third', 'fourth', 'fifth', 'sixth'])}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
