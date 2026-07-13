from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.analyzer_service import AnalyzerResult
from app.core.config_schema import ConfigField
from app.core.result_formatter import export_result
from app.scripts.registry import ScriptDefinition, create_default_registry


class ScriptWorker(QObject):
    log = Signal(str)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, script: ScriptDefinition, params: dict[str, Any]) -> None:
        super().__init__()
        self._script = script
        self._params = params

    @Slot()
    def run(self) -> None:
        try:
            emitted_logs: list[str] = []

            def emit_log(message: str) -> None:
                emitted_logs.append(message)
                self.log.emit(message)

            raw = self._script.execute(self._params, emit_log)
            if isinstance(raw, AnalyzerResult):
                result = AnalyzerResult(
                    command=raw.command,
                    title=raw.title,
                    rows=raw.rows,
                    logs=emitted_logs + raw.logs,
                    summary_text=raw.summary_text,
                    metadata=raw.metadata,
                )
            else:
                result = AnalyzerResult(
                    command=self._script.script_id,
                    title=str(raw.get("title", self._script.name)),
                    rows=list(raw.get("rows", [])),
                    logs=emitted_logs + list(raw.get("logs", [])),
                    summary_text=str(raw.get("summary_text", "")),
                    metadata=dict(raw.get("metadata", {})),
                )
            self.finished.emit(result)
        except Exception as error:
            self.failed.emit(str(error))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SSQ Analyzer")
        self._registry = create_default_registry()
        self._current_script = self._registry.list()[0]
        self._controls: dict[str, Any] = {}
        self._last_result: AnalyzerResult | None = None
        self._thread: QThread | None = None
        self._worker: ScriptWorker | None = None
        self._cancel_requested = False

        self._script_combo = QComboBox()
        self._description = QLabel()
        self._form = QFormLayout()
        self._log = QTextEdit()
        self._summary = QTextEdit()
        self._table = QTableWidget()
        self._start_button = QPushButton("开始分析/预测")
        self._refresh_button = QPushButton("刷新历史数据")
        self._stop_button = QPushButton("停止执行")
        self._clear_button = QPushButton("清空日志")
        self._export_button = QPushButton("导出结果")
        self._save_button = QPushButton("保存当前参数方案")
        self._load_button = QPushButton("加载参数方案")

        self._build_ui()
        self._connect_signals()
        self._populate_scripts()

    def _build_ui(self) -> None:
        central = QWidget()
        root = QGridLayout(central)

        left = QWidget()
        left_layout = QVBoxLayout(left)

        script_box = QGroupBox("脚本")
        script_layout = QVBoxLayout(script_box)
        script_layout.addWidget(self._script_combo)
        self._description.setWordWrap(True)
        script_layout.addWidget(self._description)

        params_box = QGroupBox("参数")
        params_box.setLayout(self._form)

        button_box = QGroupBox("操作")
        button_layout = QGridLayout(button_box)
        button_layout.addWidget(self._start_button, 0, 0)
        button_layout.addWidget(self._stop_button, 0, 1)
        button_layout.addWidget(self._refresh_button, 1, 0)
        button_layout.addWidget(self._clear_button, 1, 1)
        button_layout.addWidget(self._export_button, 2, 0)
        button_layout.addWidget(self._save_button, 2, 1)
        button_layout.addWidget(self._load_button, 3, 0, 1, 2)

        left_layout.addWidget(script_box)
        left_layout.addWidget(params_box, 1)
        left_layout.addWidget(button_box)

        tabs = QTabWidget()
        self._log.setReadOnly(True)
        self._summary.setReadOnly(True)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tabs.addTab(self._summary, "推荐号码/结果")
        tabs.addTab(self._table, "明细")
        tabs.addTab(self._log, "实时日志")

        splitter = QSplitter()
        splitter.addWidget(left)
        splitter.addWidget(tabs)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        root.addWidget(splitter, 0, 0)
        self.setCentralWidget(central)
        self._stop_button.setEnabled(False)
        self._export_button.setEnabled(False)

    def _connect_signals(self) -> None:
        self._script_combo.currentIndexChanged.connect(self._script_changed)
        self._start_button.clicked.connect(self._start)
        self._refresh_button.clicked.connect(self._refresh_history)
        self._stop_button.clicked.connect(self._stop)
        self._clear_button.clicked.connect(self._clear_log)
        self._export_button.clicked.connect(self._export)
        self._save_button.clicked.connect(self._save_params)
        self._load_button.clicked.connect(self._load_params)

    def _populate_scripts(self) -> None:
        self._script_combo.clear()
        for script in self._registry.list():
            self._script_combo.addItem(script.name, script.script_id)
        self._script_changed(0)

    def _script_changed(self, index: int) -> None:
        script_id = self._script_combo.itemData(index)
        self._current_script = self._registry.get(script_id)
        self._description.setText(self._current_script.description)
        self._rebuild_form()

    def _rebuild_form(self) -> None:
        while self._form.count():
            item = self._form.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._controls.clear()

        for field in self._current_script.schema.fields:
            control = self._control_for_field(field)
            self._controls[field.name] = control
            self._form.addRow(field.label, control)

    def _control_for_field(self, field: ConfigField):
        if field.field_type == "choice":
            control = QComboBox()
            for choice in field.choices:
                control.addItem(field.choice_label(choice), choice)
            index = control.findData(str(field.default))
            if index >= 0:
                control.setCurrentIndex(index)
            return control
        if field.field_type == "bool":
            control = QCheckBox()
            control.setChecked(bool(field.default))
            return control
        if field.field_type == "optional_int":
            control = QLineEdit()
            control.setPlaceholderText("留空")
            if field.default is not None:
                control.setText(str(field.default))
            return control
        if field.field_type == "int":
            control = QSpinBox()
            control.setMinimum(field.minimum if field.minimum is not None else -999999)
            control.setMaximum(field.maximum if field.maximum is not None else 999999)
            control.setValue(int(field.default))
            return control
        control = QLineEdit(str(field.default))
        return control

    def _params(self) -> dict[str, Any]:
        params: dict[str, Any] = {}
        for field in self._current_script.schema.fields:
            control = self._controls[field.name]
            if isinstance(control, QComboBox):
                params[field.name] = control.currentData()
            elif isinstance(control, QCheckBox):
                params[field.name] = control.isChecked()
            elif isinstance(control, QSpinBox):
                params[field.name] = control.value()
            elif isinstance(control, QLineEdit):
                params[field.name] = control.text().strip()
            else:
                params[field.name] = None
        return params

    def _apply_params(self, params: dict[str, Any]) -> None:
        for name, value in params.items():
            control = self._controls.get(name)
            if control is None:
                continue
            if isinstance(control, QComboBox):
                index = control.findData(str(value))
                if index >= 0:
                    control.setCurrentIndex(index)
            elif isinstance(control, QCheckBox):
                control.setChecked(bool(value))
            elif isinstance(control, QSpinBox):
                control.setValue(int(value))
            elif isinstance(control, QLineEdit):
                control.setText("" if value is None else str(value))

    def _start(self) -> None:
        self._run_script(self._current_script, self._params(), "开始执行")

    def _refresh_history(self) -> None:
        params = self._params()
        params["command"] = "fetch"
        self._run_script(self._registry.get("ssq"), params, "开始刷新历史数据")

    def _run_script(self, script: ScriptDefinition, params: dict[str, Any], start_message: str) -> None:
        if self._thread is not None:
            return
        self._cancel_requested = False
        self._set_running(True)
        self._append_log(start_message)
        self._thread = QThread()
        self._worker = ScriptWorker(script, params)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.log.connect(self._append_log)
        self._worker.finished.connect(self._finished)
        self._worker.failed.connect(self._failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_thread)
        self._thread.start()

    def _stop(self) -> None:
        self._cancel_requested = True
        self._append_log("已请求停止，当前任务会在本轮计算结束后停止更新。")
        self._stop_button.setEnabled(False)

    @Slot(object)
    def _finished(self, raw_result: object) -> None:
        if self._cancel_requested:
            self._append_log("任务已停止。")
            return
        result = raw_result if isinstance(raw_result, AnalyzerResult) else AnalyzerResult("script", "结果", [], summary_text=str(raw_result))
        self._last_result = result
        self._summary.setPlainText(result.summary_text)
        self._render_rows(result.rows)
        self._append_log("执行完成")
        self._export_button.setEnabled(True)

    @Slot(str)
    def _failed(self, message: str) -> None:
        self._append_log(f"执行失败：{message}")
        QMessageBox.warning(self, "执行失败", message)

    def _cleanup_thread(self) -> None:
        self._thread = None
        self._worker = None
        self._set_running(False)

    def _set_running(self, running: bool) -> None:
        self._start_button.setEnabled(not running)
        self._refresh_button.setEnabled(not running)
        self._stop_button.setEnabled(running)
        self._save_button.setEnabled(not running)
        self._load_button.setEnabled(not running)

    @Slot(str)
    def _append_log(self, message: str) -> None:
        self._log.append(message)

    def _clear_log(self) -> None:
        self._log.clear()

    def _render_rows(self, rows: list[dict[str, object]]) -> None:
        if not rows:
            self._table.setRowCount(0)
            self._table.setColumnCount(0)
            return
        headers = list(rows[0].keys())
        self._table.setColumnCount(len(headers))
        self._table.setHorizontalHeaderLabels(headers)
        self._table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for col_index, header in enumerate(headers):
                self._table.setItem(row_index, col_index, QTableWidgetItem(str(row.get(header, ""))))

    def _export(self) -> None:
        if self._last_result is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出结果", str(Path.home() / "ssq-result.txt"), "Text (*.txt);;CSV (*.csv);;JSON (*.json)")
        if not path:
            return
        output = export_result(self._last_result, path)
        self._append_log(f"已导出：{output}")

    def _save_params(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "保存参数方案", str(Path.home() / "ssq-params.json"), "JSON (*.json)")
        if not path:
            return
        payload = {"script_id": self._current_script.script_id, "params": self._params()}
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self._append_log(f"已保存参数方案：{path}")

    def _load_params(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "加载参数方案", str(Path.home()), "JSON (*.json)")
        if not path:
            return
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        script_id = payload.get("script_id")
        for index in range(self._script_combo.count()):
            if self._script_combo.itemData(index) == script_id:
                self._script_combo.setCurrentIndex(index)
                break
        self._apply_params(dict(payload.get("params", {})))
        self._append_log(f"已加载参数方案：{path}")
