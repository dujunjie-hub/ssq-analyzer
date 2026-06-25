# macOS GUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a PySide6 macOS GUI that wraps the existing SSQ analyzer logic without breaking the CLI.

**Architecture:** Add an app layer with schema, service, formatter, registry, and GUI modules. Keep `src/ssq_analyzer` as the algorithm package and keep `ssq_analyzer.cli:main` as the original CLI entrypoint.

**Tech Stack:** Python, PySide6, PyInstaller, pytest/unittest.

---

### Task 1: Core Schema, Service, Formatter, Registry

**Files:**
- Create: `app/core/config_schema.py`
- Create: `app/core/analyzer_service.py`
- Create: `app/core/result_formatter.py`
- Create: `app/scripts/registry.py`
- Test: `tests/test_app_core.py`

- [x] Write failing tests for schema fields, direct service execution, txt/csv/json export, and script registry execution.
- [x] Implement schema fields for CLI and GUI parameters.
- [x] Implement service calls to existing analyzer modules.
- [x] Implement result formatter exports.
- [x] Implement plugin registry and directory discovery.
- [x] Verify tests pass.

### Task 2: GUI Entrypoint and Main Window

**Files:**
- Create: `app/main.py`
- Create: `app/gui/main_window.py`
- Test: `tests/test_app_entrypoint.py`

- [x] Write failing entrypoint check test.
- [x] Implement `--check` mode without requiring PySide6.
- [x] Implement PySide6 main window with dynamic schema form.
- [x] Run execution in a background `QThread`.
- [x] Add save/load params and export result actions.
- [x] Verify window can instantiate in offscreen mode.

### Task 3: CLI Compatibility and Packaging Docs

**Files:**
- Create: `cli/main.py`
- Create: `requirements.txt`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Test: `tests/test_cli_wrapper.py`

- [x] Write failing wrapper test.
- [x] Add `cli/main.py` delegating to `ssq_analyzer.cli`.
- [x] Keep original `ssq` script and add `ssq-gui`.
- [x] Document GUI, CLI, plugin, and PyInstaller workflows.
- [x] Build and verify `dist/SSQ Analyzer.app`.
