#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FETCH_COMMAND="${SSQ_FETCH_COMMAND:-ssq fetch}"
GENERATE_COMMAND="${SSQ_GENERATE_COMMAND:-ssq generate}"
COUNT="${SSQ_COUNT:-5}"
SEED="${SSQ_SEED:-}"
HISTORY_PATH="${SSQ_HISTORY_PATH:-$PROJECT_DIR/data/ssq_history.csv}"

cd "$PROJECT_DIR"

echo "正在更新双色球历史数据..."
if ! $FETCH_COMMAND; then
  if [[ -s "$HISTORY_PATH" ]]; then
    echo "更新失败，将使用已有缓存：$HISTORY_PATH"
  else
    echo "历史数据更新失败。请检查网络或数据源后重试。" >&2
    exit 1
  fi
fi

echo
echo "请选择生成策略："
echo "1) ensemble       推荐：综合 balanced/hot/cold/omission/recent"
echo "2) balanced       均衡：奇偶、区间、连号约束"
echo "3) hot            热号：偏向历史高频号"
echo "4) cold           冷号：偏向历史低频号"
echo "5) omission       遗漏：偏向当前遗漏较高的号码"
echo "6) recent         近期：偏向最近开奖更活跃的号码"
echo "7) deep-learning  实验：轻量神经打分器"
echo "8) liuyao         玄学：一次起卦生成 5 组娱乐号码"
echo "9) random         随机：纯随机"
echo
read -r -p "输入编号，直接回车默认 1： " choice

case "${choice:-1}" in
  1) strategy="ensemble" ;;
  2) strategy="balanced" ;;
  3) strategy="hot" ;;
  4) strategy="cold" ;;
  5) strategy="omission" ;;
  6) strategy="recent" ;;
  7) strategy="deep-learning" ;;
  8) strategy="liuyao" ;;
  9) strategy="random" ;;
  *)
    echo "无效选择：$choice" >&2
    exit 2
    ;;
esac

echo
read -r -p "是否导出 Excel 文件？输入 y 导出，直接回车不导出： " export_xlsx

args=(--strategy "$strategy" --count "$COUNT")
if [[ -n "$SEED" ]]; then
  args+=(--seed "$SEED")
fi
if [[ "$export_xlsx" == "y" || "$export_xlsx" == "Y" ]]; then
  args+=(--format xlsx)
fi

echo
echo "已选择策略：$strategy"
echo "生成组数：$COUNT"
echo

if ! $GENERATE_COMMAND "${args[@]}"; then
  if [[ "$GENERATE_COMMAND" == ssq* ]]; then
    PYTHONPATH="$PROJECT_DIR/src" python3 -m ssq_analyzer.cli generate "${args[@]}"
  else
    exit 1
  fi
fi
