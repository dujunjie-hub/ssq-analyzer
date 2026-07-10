import csv
import json
import unittest
from datetime import date

from app.core.analyzer_service import AnalyzerConfig, AnalyzerService
from app.core.config_schema import default_schema
from app.core.result_formatter import export_result, format_result_text
from app.scripts.registry import ScriptDefinition, ScriptRegistry, create_default_registry
from ssq_analyzer.models import Draw


def sample_draws():
    return [
        Draw("2026001", date(2026, 1, 1), (1, 2, 3, 4, 5, 6), 1),
        Draw("2026002", date(2026, 1, 3), (7, 8, 9, 10, 11, 12), 2),
        Draw("2026003", date(2026, 1, 5), (13, 14, 15, 16, 17, 18), 3),
        Draw("2026004", date(2026, 1, 7), (19, 20, 21, 22, 23, 24), 4),
    ]


class AppCoreTests(unittest.TestCase):
    def test_default_schema_exposes_cli_and_gui_parameters(self):
        schema = default_schema()
        names = {field.name for field in schema.fields}

        self.assertIn("command", names)
        self.assertIn("strategy", names)
        self.assertIn("history_limit", names)
        self.assertIn("count", names)
        self.assertIn("seed", names)
        self.assertIn("window", names)
        self.assertIn("use_hot", names)
        self.assertIn("use_cold", names)
        self.assertIn("use_sum_analysis", names)
        self.assertIn("use_parity_ratio", names)
        self.assertIn("use_range_ratio", names)
        self.assertIn("use_consecutive", names)
        self.assertIn("filter_duplicates", names)
        self.assertIn("balanced", schema.field("strategy").choices)
        self.assertIn("liuyao", schema.field("strategy").choices)
        self.assertEqual(schema.field("command").choice_label("generate"), "生成推荐号码")
        self.assertEqual(schema.field("strategy").choice_label("balanced"), "均衡模型")

    def test_service_generates_structured_tickets_without_subprocess(self):
        service = AnalyzerService(draw_loader=sample_draws)
        config = AnalyzerConfig(command="generate", strategy="balanced", count=3, seed=9, history_limit=3)

        result = service.run(config)

        self.assertEqual(result.command, "generate")
        self.assertEqual(result.rows[0]["strategy"], "balanced")
        self.assertEqual(len(result.rows), 3)
        self.assertTrue(any("加载历史数据：3 期" in message for message in result.logs))
        self.assertIn("上一期开奖结果：2026004", result.summary_text)
        self.assertIn("红球", result.summary_text)

    def test_service_backtest_shows_actual_prediction_and_hit_balls(self):
        service = AnalyzerService(draw_loader=sample_draws)
        config = AnalyzerConfig(command="backtest", strategy="random", count=1, seed=5, window=3)

        result = service.run(config)

        self.assertEqual(len(result.rows), 3)
        self.assertIn("2026002 开奖", result.summary_text)
        self.assertIn("预测 1", result.summary_text)
        self.assertIn("命中红球", result.summary_text)
        self.assertIn("red_hit_balls", result.rows[0])
        self.assertIn("blue_hit_ball", result.rows[0])

    def test_backtest_window_uses_latest_draws_not_history_limit(self):
        draws = [
            Draw(f"2026{index:03d}", date(2026, 1, index), (1, 2, 3, 4, 5, 6), 1)
            for index in range(1, 11)
        ]
        service = AnalyzerService(draw_loader=lambda: draws)
        config = AnalyzerConfig(command="backtest", strategy="random", count=1, seed=5, window=5, history_limit=5)

        result = service.run(config)

        self.assertEqual([row["issue"] for row in result.rows], ["2026006", "2026007", "2026008", "2026009", "2026010"])

    def test_service_preserves_liuyao_reading_metadata(self):
        service = AnalyzerService(draw_loader=sample_draws)
        config = AnalyzerConfig(command="generate", strategy="liuyao", count=2, seed=9)

        result = service.run(config)

        self.assertEqual(len(result.rows), 2)
        self.assertTrue(result.metadata["primary_hexagram"])
        self.assertIn("本卦", result.summary_text)
        self.assertIn("moving_lines", result.rows[0])

    def test_formatter_exports_txt_csv_and_json(self):
        service = AnalyzerService(draw_loader=sample_draws)
        result = service.run(AnalyzerConfig(command="generate", strategy="random", count=2, seed=4))

        text = format_result_text(result)
        self.assertIn("红球", text)

        with self.subTest("txt"):
            txt_output = export_result(result, self.tmp_path("tickets.txt"))
            self.assertIn("红球", txt_output.read_text(encoding="utf-8"))

        with self.subTest("csv"):
            csv_output = export_result(result, self.tmp_path("tickets.csv"))
            with csv_output.open("r", encoding="utf-8", newline="") as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(len(rows), 2)
            self.assertIn("red", rows[0])

        with self.subTest("json"):
            json_output = export_result(result, self.tmp_path("tickets.json"))
            payload = json.loads(json_output.read_text(encoding="utf-8"))
            self.assertEqual(payload["command"], "generate")
            self.assertEqual(len(payload["rows"]), 2)

    def test_registry_runs_scripts_by_schema(self):
        registry = ScriptRegistry()

        def execute(params, emit_log):
            emit_log(f"received {params['name']}")
            return {"rows": [{"name": params["name"]}], "summary_text": "done"}

        registry.register(
            ScriptDefinition(
                script_id="demo",
                name="Demo",
                description="Demo script",
                schema=default_schema(),
                execute=execute,
            )
        )

        result = registry.run("demo", {"name": "alice"})

        self.assertEqual(result.rows, [{"name": "alice"}])
        self.assertEqual(result.logs, ["received alice"])
        self.assertEqual(registry.get("demo").name, "Demo")

    def test_registry_discovers_python_scripts_from_directory(self):
        from pathlib import Path
        import tempfile

        directory = Path(tempfile.mkdtemp(prefix="ssq-script-discovery-"))
        (directory / "hello_script.py").write_text(
            """
from app.core.config_schema import ConfigSchema, ConfigField
from app.scripts.registry import ScriptDefinition

def execute(params, emit_log):
    emit_log("hello log")
    return {"rows": [{"message": params["message"]}], "summary_text": "hello"}

SCRIPT = ScriptDefinition(
    script_id="hello",
    name="Hello",
    description="Example script",
    schema=ConfigSchema(fields=(ConfigField("message", "Message", "text", "hi"),)),
    execute=execute,
)
""",
            encoding="utf-8",
        )
        registry = ScriptRegistry()

        registry.discover(directory)
        result = registry.run("hello", {"message": "world"})

        self.assertEqual(registry.get("hello").name, "Hello")
        self.assertEqual(result.rows, [{"message": "world"}])
        self.assertEqual(result.logs, ["hello log"])

    def test_default_registry_does_not_include_pboss_mail_plugin(self):
        registry = create_default_registry()
        script_ids = {script.script_id for script in registry.list()}

        self.assertNotIn("pboss_mail", script_ids)

    def tmp_path(self, name):
        path = self._testMethodName
        from pathlib import Path
        import tempfile

        directory = Path(tempfile.mkdtemp(prefix=f"{path}-"))
        return directory / name


if __name__ == "__main__":
    unittest.main()
