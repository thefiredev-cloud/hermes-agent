"""Behavior tests for the strict CI aggregate gate (scripts/ci/required_results.py)."""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "required_results.py"

_spec = importlib.util.spec_from_file_location("required_results", SCRIPT)
required_results = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(required_results)

evaluate_gate = required_results.evaluate_gate


import pytest


@pytest.mark.parametrize("release", [False, True])
@pytest.mark.parametrize("job", ["tests", "osv-scanner", "history-check", "e2e-desktop"])
@pytest.mark.parametrize("result,ordinary,excluded", [
    ("success", True, True), ("skipped", False, True), ("failure", False, False),
    ("cancelled", False, False), ("with-status", False, False),
    ("action_required", False, False), ("unknown", False, False), (None, False, False),
])
def test_status_policy(job, result, ordinary, excluded, release):
    expected = excluded if job in ("history-check", "e2e-desktop") else ordinary
    if result == "skipped" and not release:
        expected = True
    verdict = evaluate_gate({job: {} if result is None else {"result": result}}, release=release)
    assert verdict == {"ok": expected, "failed": [] if expected else [job],
                       "allowed_skips": [job] if expected and result == "skipped" else []}


def test_release_exclusion_policy():
    assert required_results.EXCLUDED_JOBS == {
        "history-check", "lockfile-diff", "supply-chain", "review-labels", "e2e-desktop",
    }


@pytest.mark.parametrize("needs", [{}, None])
@pytest.mark.parametrize("release", [False, True])
def test_empty_needs_fails_closed(needs, release):
    assert evaluate_gate(needs, release=release) == {
        "ok": False, "failed": ["<no-needs>"], "allowed_skips": [],
    }
    assert required_results.compact_results(needs) == {}


@pytest.mark.parametrize("release,results,code,report", [
    (True, {"detect": "success", "e2e-desktop": "skipped"}, 0, "All checks passed"),
    (True, {"tests": "skipped", "history-check": "skipped", "lint": "failure"},
     1, "::error::2 job(s) failed: lint, tests"),
    (False, {"tests": "failure"}, 1, "::error::1 job(s) failed: tests"),
])
def test_cli_stdin_exit_codes_and_output(tmp_path, release, results, code, report):
    output = tmp_path / "github-output.txt"
    needs = {name: {"result": result, "outputs": {"detail": "kept"}}
             for name, result in results.items()}
    child = subprocess.run(
        [sys.executable, str(SCRIPT), *(["--release"] if release else [])],
        input=json.dumps(needs), capture_output=True, text=True, timeout=30,
        env={**os.environ, "GITHUB_OUTPUT": str(output)},
    )
    assert child.returncode == code, child.stderr
    assert report in child.stdout
    key, value = output.read_text(encoding="utf-8").strip().split("=", 1)
    assert key == "needs-json"
    assert json.loads(value) == results
    assert f"{key}={value}" in child.stdout
    for name, result in results.items():
        assert f"{name}: {result}" in child.stdout


ADVISORY = ("tests", "tests-os", "e2e-desktop-core", "e2e-desktop-update")


@pytest.mark.parametrize("result", ["failure", "cancelled"])
def test_advisory_job_warns_without_failing_an_ordinary_run(result):
    needs = {"lint": {"result": "success"}, "tests": {"result": result}}
    assert evaluate_gate(needs, advisory=ADVISORY) == {
        "ok": True, "failed": [], "allowed_skips": [], "advisory_failed": ["tests"],
    }


def test_advisory_never_covers_a_job_outside_the_list():
    needs = {"lint": {"result": "failure"}, "tests": {"result": "failure"}}
    assert evaluate_gate(needs, advisory=ADVISORY) == {
        "ok": False, "failed": ["lint"], "allowed_skips": [], "advisory_failed": ["tests"],
    }


def test_advisory_is_ignored_on_a_release_run():
    needs = {"tests": {"result": "failure"}}
    assert evaluate_gate(needs, release=True, advisory=ADVISORY) == {
        "ok": False, "failed": ["tests"], "allowed_skips": [],
    }


def test_cli_advisory_reports_a_warning_and_exits_zero():
    needs = {"lint": {"result": "success"}, "e2e-desktop-core": {"result": "failure"}}
    child = subprocess.run(
        [sys.executable, str(SCRIPT), "--advisory", *ADVISORY],
        input=json.dumps(needs), capture_output=True, text=True, timeout=30,
    )
    assert child.returncode == 0, child.stderr
    assert "⚠️ e2e-desktop-core: failure" in child.stdout
    assert "::warning::1 advisory job(s) not green: e2e-desktop-core" in child.stdout
    assert "::error::" not in child.stdout


def test_cli_release_with_advisory_still_fails_closed():
    needs = {"tests": {"result": "failure"}}
    child = subprocess.run(
        [sys.executable, str(SCRIPT), "--release", "--advisory", *ADVISORY],
        input=json.dumps(needs), capture_output=True, text=True, timeout=30,
    )
    assert child.returncode == 1
    assert "::error::1 job(s) failed: tests" in child.stdout
