"""Tests covering the regression suite orchestration helpers."""

from __future__ import annotations

from tests.regression.agent_suite import format_text_report, run_cli, run_suite_with


def _get_run(report, agent):
    for run in report.runs:
        if run.blueprint.agent == agent:
            return run
    raise AssertionError(f"No se encontró el agente {agent!r} en el reporte")


def test_regression_suite_default_execution(rag_test_harness):
    module, harness = rag_test_harness

    report = run_suite_with(module, harness)

    assert report.passed is True
    assert {run.blueprint.agent for run in report.runs} == {"document", "media", "code", "legal"}

    document_run = _get_run(report, "document")
    assert document_run.result.context_documents == 3

    rendered = format_text_report(report)
    assert "document_agent_regression" in rendered
    assert "legal_agent_regression" in rendered


def test_regression_suite_accepts_threshold_overrides(rag_test_harness):
    module, harness = rag_test_harness

    overrides = {"document": {"thresholds": {"max_latency": 0.0}}}
    report = run_suite_with(module, harness, overrides=overrides)

    document_run = _get_run(report, "document")
    assert document_run.result.passed is False
    assert any("latencia_superior_al_umbral" in issue for issue in document_run.result.issues)


def test_cli_can_run_multiple_times_without_metric_collisions(capsys):
    exit_code = run_cli(["--format", "json"])
    first = capsys.readouterr()

    assert exit_code == 0
    assert "Duplicated timeseries" not in first.out
    assert "Duplicated timeseries" not in first.err

    exit_code = run_cli(["--format", "json"])
    second = capsys.readouterr()

    assert exit_code == 0
    assert "Duplicated timeseries" not in second.out
    assert "Duplicated timeseries" not in second.err
