# macOS GUI Design

## Goal

Add a macOS desktop GUI to `ssq-analyzer` while preserving the existing terminal workflow and prediction logic.

## Current Structure

The existing CLI already delegates most work to reusable modules:

- `src/ssq_analyzer/generator.py` generates tickets.
- `src/ssq_analyzer/stats.py` analyzes history.
- `src/ssq_analyzer/backtest.py` runs backtests and strategy comparisons.
- `src/ssq_analyzer/cli.py` parses terminal arguments and prints/export results.

The GUI should not call the CLI through subprocess. It should call the same Python functions through a service layer.

## Architecture

- `app/core/config_schema.py` defines fields for GUI forms and future script plugins.
- `app/core/analyzer_service.py` wraps the existing analysis, generation, backtest, compare, and fetch functions.
- `app/core/result_formatter.py` exports structured results to txt, csv, and json.
- `app/scripts/registry.py` registers built-in and plugin scripts.
- `app/gui/main_window.py` builds the PySide6 desktop window and runs scripts in a background thread.
- `cli/main.py` preserves the requested `cli/` entrypoint by delegating to the original CLI.

## GUI Behavior

The main window exposes script selection, parameter controls, action buttons, logs, summary output, and detail rows. Long-running tasks run in a `QThread`, and errors are shown in the window instead of crashing the app.

## Script Plugins

Plugin scripts expose a `SCRIPT = ScriptDefinition(...)` object or a `register(registry)` function. Each plugin supplies a schema and an execution function. The GUI builds controls from the schema and displays returned summary text and rows.

## Packaging

PyInstaller builds `dist/SSQ Analyzer.app`. The project reserves `app/assets/app.icns` for a future icon.
