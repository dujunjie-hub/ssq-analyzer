import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "ssq_update_generate.sh"


def test_update_generate_script_exists_and_has_valid_shell_syntax():
    assert SCRIPT_PATH.exists()
    assert os.access(SCRIPT_PATH, os.X_OK)

    result = subprocess.run(["bash", "-n", str(SCRIPT_PATH)], capture_output=True, text=True)

    assert result.returncode == 0, result.stderr


def test_update_generate_script_can_select_ensemble_without_network():
    result = subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        input="1\nn\n",
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        env={
            **os.environ,
            "SSQ_FETCH_COMMAND": "true",
            "SSQ_GENERATE_COMMAND": "ssq generate",
            "SSQ_SEED": "9",
        },
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
    assert "1) ensemble" in result.stdout
    assert "已选择策略：ensemble" in result.stdout
    assert result.stdout.count("红球") == 5


def test_update_generate_script_can_select_liuyao_without_network():
    result = subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        input="8\nn\n",
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        env={
            **os.environ,
            "SSQ_FETCH_COMMAND": "true",
            "SSQ_GENERATE_COMMAND": "ssq generate",
            "SSQ_SEED": "9",
        },
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
    assert "8) liuyao" in result.stdout
    assert "已选择策略：liuyao" in result.stdout
    assert "本卦：" in result.stdout
    assert result.stdout.count("红球") == 5


def test_update_generate_script_can_select_advanced_liuyao_without_network():
    result = subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        input="9\nn\n",
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        env={
            **os.environ,
            "SSQ_FETCH_COMMAND": "true",
            "SSQ_GENERATE_COMMAND": "ssq generate",
            "SSQ_SEED": "19930810",
        },
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
    assert "9) liuyao-advanced" in result.stdout
    assert "已选择策略：liuyao-advanced" in result.stdout
    assert "用神：妻财" in result.stdout


def test_update_generate_script_uses_cached_history_when_fetch_fails(tmp_path):
    history_path = tmp_path / "ssq_history.csv"
    history_path.write_text("cached history", encoding="utf-8")

    result = subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        input="1\nn\n",
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        env={
            **os.environ,
            "SSQ_FETCH_COMMAND": "false",
            "SSQ_GENERATE_COMMAND": "ssq generate",
            "SSQ_HISTORY_PATH": str(history_path),
            "SSQ_SEED": "9",
        },
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
    assert "更新失败，将使用已有缓存" in result.stdout
    assert "已选择策略：ensemble" in result.stdout
