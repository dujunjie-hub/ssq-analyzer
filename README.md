# SSQ Analyzer

`ssq-analyzer` 是一个本地命令行工具，用于双色球历史数据分析、娱乐选号、回测验证、策略对比和 CSV/XLSX 导出。

重要说明：双色球开奖结果具有随机性，本工具生成的号码只适合作为娱乐参考，不代表可靠预测能力，也不保证中奖。

## 运行方式

先进入项目目录：

```bash
cd /Users/xky/codex/ssq-analyzer
```

你已经安装了 `ssq` 命令，后续直接使用：

```bash
ssq <命令>
```

例如：

```bash
ssq generate --strategy deep-learning --seed 9
```

也可以使用一键更新并生成脚本：

```bash
./scripts/ssq_update_generate.sh
```

## 常用参数

- `--strategy`：选号策略。可选值包括 `random`、`weighted`、`balanced`、`hot`、`cold`、`omission`、`recent`、`ensemble`、`deep-learning`、`liuyao`、`liuyao-advanced`。
- `--count`：每次生成几组号码，默认是 `5`。
- `--seed`：随机种子。设置后，同样的数据和参数会生成相同结果，方便复现。
- `--format`：导出格式，可选 `csv` 或 `xlsx`。
- `--output`：指定导出文件路径。不指定时写入 `outputs/`。
- `--window`：回测最近多少期，默认是 `20`。

## 命令说明

### 一键更新并生成

```bash
./scripts/ssq_update_generate.sh
```

含义：

- 自动执行 `ssq fetch` 更新历史开奖数据。
- 显示策略菜单，让你选择生成策略。
- 默认生成 5 组号码。
- 可选择是否导出 Excel 文件。
- 默认推荐策略是 `ensemble`。

策略菜单：

```text
1) ensemble       推荐：综合 balanced/hot/cold/omission/recent
2) balanced       均衡：奇偶、区间、连号约束
3) hot            热号：偏向历史高频号
4) cold           冷号：偏向历史低频号
5) omission       遗漏：偏向当前遗漏较高的号码
6) recent         近期：偏向最近开奖更活跃的号码
7) deep-learning  实验：轻量神经打分器
8) liuyao         玄学：一次起卦生成 5 组娱乐号码
9) liuyao-advanced 高级六爻：纳甲、世应、六亲、用神
10) random        随机：纯随机
```

如果想固定随机种子或生成组数，可以这样运行：

```bash
SSQ_SEED=9 SSQ_COUNT=5 ./scripts/ssq_update_generate.sh
```

### `generate`

生成娱乐参考号码。默认生成 5 组，默认策略是 `balanced`。

示例：

```bash
ssq generate --seed 9
```

含义：

- 使用默认 `balanced` 策略。
- 生成 5 组号码。
- 第 1 组固定为长期跟踪号码：红球 `02 05 10 25 26 31`，蓝球 `16`。
- `--seed 9` 固定随机种子，便于复现。
- 终端会提示下一期开奖预计时间。

### `generate --strategy random --count 5 --format xlsx`

```bash
ssq generate --strategy random --count 5 --format xlsx
```

含义：

- 使用 `random` 纯随机策略。
- 生成 5 组号码。
- 导出 Excel 文件。
- 默认导出到 `outputs/tickets.xlsx`。

### `generate --strategy ensemble --seed 9`

```bash
ssq generate --strategy ensemble --seed 9
```

含义：

- 使用 `ensemble` 混合策略。
- 默认生成 5 组号码。
- 5 组号码会混合 `balanced`、`hot`、`cold`、`omission`、`recent` 的思路。
- `--seed 9` 固定输出，便于复现。

### `generate --strategy deep-learning --seed 9`

```bash
ssq generate --strategy deep-learning --seed 9
```

含义：

- 使用实验版 `deep-learning` 策略。
- 默认生成 5 组号码。
- 会打印实验策略提示。
- 当前实现是轻量纯 Python 神经打分器，不依赖 PyTorch/TensorFlow。
- 它只用于研究和娱乐，不代表预测优势。

### `generate --strategy liuyao --seed 9`

```bash
ssq generate --strategy liuyao --seed 9
```

含义：

- 使用六爻灵感娱乐策略。
- 每次命令只起一次卦，并显示本卦、动爻和变卦。
- 基于同一卦象权重生成 5 组合法号码。
- `--seed 9` 会固定卦象和号码，方便复现。
- 不传 `--seed` 时，每次运行会重新随机起卦。
- 它不属于传统六爻断卦或科学预测，不代表中奖优势。

输出示例：

```text
六爻灵感娱乐策略：不属于传统六爻断卦或科学预测，不代表中奖优势。
本卦：17 泽雷随
动爻：初爻、上爻
变卦：12 天地否

1. 红球 09 10 14 20 23 32  蓝球 12
...
5. 红球 01 02 10 13 23 31  蓝球 13
```

### `generate --strategy liuyao-advanced --seed 9`

```bash
ssq generate --strategy liuyao-advanced --seed 9
```

含义：

- 使用高级六爻娱乐模型。
- 在本卦、动爻、变卦之外，额外显示简化纳甲、五行、六亲、世应、用神、互卦和错卦。
- 默认用“妻财”为求财/中奖类用神，并把财爻、子孙爻、动爻、世应爻相关号码提高权重。
- 它仍然只是娱乐参考，不属于传统断卦服务，也不代表中奖优势。

### `analyze`

分析历史开奖数据，输出红球和蓝球的频率、遗漏等统计。

```bash
ssq analyze --format csv
```

含义：

- 加载本地历史数据；如果没有本地数据，会使用项目内置样本数据。
- 统计红球最高频、蓝球最高频、频率表、遗漏表。
- 导出 CSV 文件。
- 默认导出到 `outputs/analysis.csv`。

### `backtest`

对单个策略做历史回测。回测时，每一期只使用它之前的数据生成号码，不使用未来数据。

```bash
ssq backtest --count 5 --seed 9 --format csv
```

含义：

- 使用默认 `balanced` 策略。
- 每期生成 5 组号码。
- `--seed 9` 固定随机种子。
- 对最近默认 20 期做回测。
- 导出每一期、每一组号码的命中详情。
- 默认导出到 `outputs/backtest.csv`。

### `backtest --strategy all`

```bash
ssq backtest --strategy all --count 5 --seed 9 --format csv
```

含义：

- 对所有策略做回测汇总。
- 每个策略每期生成 5 组号码。
- 输出每种策略的票数、蓝球命中率和中奖记录数。
- 适合快速比较不同策略的历史表现。
- 默认导出到 `outputs/backtest.csv`。

### `compare`

对多种策略做策略对比汇总。它比 `backtest --strategy all` 更直接，主要用于看策略摘要。

```bash
ssq compare --seed 9 --format csv
```

含义：

- 对比 `balanced`、`hot`、`cold`、`omission`、`recent`、`ensemble`、`deep-learning`、`liuyao`、`liuyao-advanced`。
- 每个策略默认每期生成 5 组号码。
- 输出总票数、蓝球命中率、中奖等级分布和红球命中分布。
- 默认导出到 `outputs/compare.csv`。

### `fetch`

刷新历史开奖数据到本地 CSV。

```bash
ssq fetch
```

含义：

- 从数据源抓取双色球历史开奖数据。
- 保存到 `data/ssq_history.csv`。
- 如果网络或数据源不可用，其他命令仍可使用内置样本数据运行。

指定保存路径：

```bash
ssq fetch --output data/ssq_history.csv
```

## 策略说明

稳定策略：

- `random`：纯随机。
- `weighted`：历史频率和遗漏加权。
- `balanced`：奇偶、区间和连号约束。
- `hot`：偏向高频号。
- `cold`：偏向低频号。
- `omission`：偏向当前遗漏较高的号码。
- `recent`：偏向最近开奖中更活跃的号码。
- `ensemble`：混合 `balanced`、`hot`、`cold`、`omission`、`recent`。

实验策略：

- `deep-learning`：轻量纯 Python 神经打分器，不依赖 PyTorch/TensorFlow。它只用于研究和娱乐，不代表预测优势，也不是默认策略。

娱乐策略：

- `liuyao`：一次随机起卦，显示本卦、动爻和变卦，再由同一卦象生成 5 组号码。它不是传统断卦服务，也没有科学预测能力。
- `liuyao-advanced`：在六爻基础上增加简化纳甲、五行、六亲、世应、用神、互卦和错卦，再把相关爻位映射到号码权重。它仍然只是娱乐模型。

## 输出文件

默认导出目录是：

```text
/Users/xky/codex/ssq-analyzer/outputs
```

常见输出：

- `outputs/tickets.csv` 或 `outputs/tickets.xlsx`：生成号码。
- `outputs/analysis.csv` 或 `outputs/analysis.xlsx`：历史统计。
- `outputs/backtest.csv` 或 `outputs/backtest.xlsx`：回测详情或策略汇总。
- `outputs/compare.csv` 或 `outputs/compare.xlsx`：策略对比摘要。

## 下一期开奖时间提示

`generate`、`analyze`、`backtest`、`compare` 会在终端输出下一期开奖预计时间，例如：

```text
下期开奖预计：2026-06-14 周日 21:15（北京时间，按周二/周四/周日开奖规则估算）
```

这个时间按周二、周四、周日 21:15 的开奖规则估算。如果官方临时调整或延迟开奖，工具不会自动感知。

## 测试

运行全部测试：

```bash
pytest -q
```

## 桌面 GUI App

项目新增了 PySide6 桌面界面，GUI 只作为包装层，核心预测、分析、回测逻辑仍复用 `ssq_analyzer` 里的原有 Python 函数，不通过 subprocess 强行调用命令行。

安装 GUI 依赖：

```bash
cd /Users/xky/codex/ssq-analyzer
python3 -m pip install -r requirements.txt
```

启动 GUI：

```bash
cd /Users/xky/codex/ssq-analyzer
PYTHONPATH=src:. python3 -m app.main
```

如果使用可编辑安装，也可以运行：

```bash
cd /Users/xky/codex/ssq-analyzer
python3 -m pip install -e ".[gui]"
ssq-gui
```

GUI 入口自检：

```bash
cd /Users/xky/codex/ssq-analyzer
PYTHONPATH=src:. python3 -m app.main --check
```

GUI 主窗口包含：

- 脚本选择区：默认内置“双色球分析/预测”，后续可自动发现脚本插件。
- 参数区：执行类型、历史期数、分析模型/算法、生成组数、随机种子、回测窗口、热号、冷号、和值、奇偶比、区间比、连号、重复过滤。
- 操作区：开始分析/预测、停止执行、清空日志、导出结果、保存当前参数方案、加载参数方案。
- 输出区：推荐号码/结果、明细表、实时日志。

GUI 导出支持：

- `.txt`：导出窗口里的日志和结果文本。
- `.csv`：导出结构化明细行。
- `.json`：导出命令、日志、摘要、元数据和明细行。

## 继续使用终端版本

原命令行入口继续保留：

```bash
cd /Users/xky/codex/ssq-analyzer
ssq generate --strategy balanced --count 5 --seed 9
```

也可以通过新增的兼容入口运行：

```bash
cd /Users/xky/codex/ssq-analyzer
PYTHONPATH=src:. python3 -m cli.main generate --strategy balanced --count 5 --seed 9
```

## 脚本扩展机制

GUI 使用 `app/scripts/registry.py` 作为脚本注册中心。每个脚本定义自己的名称、描述、参数 schema 和执行函数，GUI 会根据 schema 自动生成表单。

推荐把新脚本放到：

```text
/Users/xky/codex/ssq-analyzer/app/scripts/plugins/
```

也支持扫描项目根目录下的 `scripts/*.py`。现有的 shell 脚本不会被加载。

最小插件示例：

```python
from app.core.config_schema import ConfigField, ConfigSchema
from app.scripts.registry import ScriptDefinition


def execute(params, emit_log):
    emit_log("开始执行自定义脚本")
    return {
        "title": "自定义脚本结果",
        "summary_text": f"输入参数：{params['name']}",
        "rows": [{"name": params["name"]}],
    }


SCRIPT = ScriptDefinition(
    script_id="hello",
    name="Hello Script",
    description="演示脚本",
    schema=ConfigSchema(
        fields=(
            ConfigField("name", "名称", "text", "world"),
        )
    ),
    execute=execute,
)
```

也可以用函数式注册：

```python
def register(registry):
    registry.register(ScriptDefinition(...))
```

脚本执行函数不要直接操作 GUI。需要显示进度时调用 `emit_log("日志内容")`，需要展示结果时返回 `summary_text` 和 `rows`。

## macOS 打包

使用 PyInstaller 生成 `.app`：

```bash
cd /Users/xky/codex/ssq-analyzer
python3 -m pip install -r requirements.txt
PYINSTALLER_CONFIG_DIR="$PWD/.pyinstaller" PYTHONPATH=src:. pyinstaller \
  -y \
  --windowed \
  --name "SSQ Analyzer" \
  --paths src \
  --paths . \
  app/main.py
```

生成结果：

```text
dist/SSQ Analyzer.app
```

如果已经准备好图标文件，把 `app.icns` 放到：

```text
app/assets/app.icns
```

然后使用带图标命令：

```bash
cd /Users/xky/codex/ssq-analyzer
PYINSTALLER_CONFIG_DIR="$PWD/.pyinstaller" PYTHONPATH=src:. pyinstaller \
  -y \
  --windowed \
  --name "SSQ Analyzer" \
  --icon app/assets/app.icns \
  --paths src \
  --paths . \
  app/main.py
```

Intel Mac 可用：在 Intel Mac 上用 Intel 版 Python 执行上述命令，会生成 Intel 架构可运行的 `.app`。如果要做通用二进制，需要在具备对应 Python/Qt universal2 依赖的环境中打包。
