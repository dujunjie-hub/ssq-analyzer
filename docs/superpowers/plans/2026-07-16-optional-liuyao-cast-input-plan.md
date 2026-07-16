# Optional Liuyao Cast Input Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let GUI and CLI users optionally provide text, numbers, or a short phrase to deterministically cast a 六爻 reading, without changing existing empty-input behavior.

**Architecture:** `liuyao.py` owns the stable text-to-six-lines conversion. Generation accepts `cast_input` only for 六爻 strategies, while the GUI schema, registry, CLI, service summary, metadata, and exported ticket rows pass through the same normalized value. Leaving it blank retains the current random/seed casting behavior.

**Tech Stack:** Python standard library `hashlib`, PySide6 schema-driven form, argparse, pytest/unittest.

---

### Task 1: Deterministic core casting

**Files:**
- Modify: `src/ssq_analyzer/liuyao.py`
- Modify: `src/ssq_analyzer/generator.py`
- Test: `tests/test_liuyao.py`

- [x] Write tests that the same non-empty input produces the same six line values and generated tickets when the seed is fixed.
- [x] Run the new test and confirm it fails because the input-casting API does not exist.
- [x] Add `line_values_from_input(value: str)` using SHA-256 and map its first six bytes into the valid values `6`, `7`, `8`, and `9`.
- [x] Add optional `cast_input` parameters to both 六爻 ticket generators. When non-empty, create the reading from the input; otherwise retain `cast_liuyao` / `cast_advanced_liuyao` behavior.
- [x] Re-run the focused core tests and confirm they pass.

### Task 2: Expose the input consistently

**Files:**
- Modify: `src/ssq_analyzer/cli.py`
- Modify: `app/core/config_schema.py`
- Modify: `app/core/analyzer_service.py`
- Modify: `app/scripts/registry.py`
- Modify: `README.md`
- Test: `tests/test_cli.py`
- Test: `tests/test_app_core.py`
- Test: `tests/test_gui_labels.py`

- [x] Write tests for `--cast-input`, the schema field, and service output metadata that includes a provided input.
- [x] Run the focused tests and confirm they fail because CLI parsing, schema fields, and service propagation are absent.
- [x] Add `--cast-input` to `ssq generate`; include it in 六爻 console text and exported ticket metadata only when supplied.
- [x] Add the optional GUI field `六爻起卦输入`, map it in the built-in script registry, and pass it into both current and previous-prediction 六爻 generation.
- [x] Include the input in service summary, result metadata, and ticket rows for export; preserve all blank-input output behavior.
- [x] Document the CLI option and GUI behavior in the README.
- [x] Re-run the focused tests and confirm they pass.

### Task 3: Full verification, packaging, and delivery

**Files:**
- Build: `dist/SSQ Analyzer.app`

- [x] Run the full test suite with `.venv/bin/python -m pytest -q`.
- [x] Rebuild the PyInstaller macOS application from `app/main.py` with the project data file included.
- [x] Run the bundled executable with `--check`.
- [x] Inspect `git diff --check`, commit the implementation, push `main` through the configured GitHub SSH key, and verify the remote branch revision.
