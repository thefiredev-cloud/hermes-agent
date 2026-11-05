"""``hermes cron doctor`` must surface open failure incidents that belong to paused/disabled jobs
and to jobs that no longer exist, not only the active jobs' own state."""

import pytest


@pytest.fixture
def cron_home(tmp_path, monkeypatch):
    from cron import jobs

    home = tmp_path / "home"
    (home / "cron").mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(jobs, "CRON_DIR", home / "cron")
    monkeypatch.setattr(jobs, "JOBS_FILE", home / "cron/jobs.json")
    monkeypatch.setattr(jobs, "OUTPUT_DIR", home / "cron/output")
    return home


def _paused_job():
    from cron import jobs

    job = jobs.create_job(prompt="probe", schedule="every 1h", name="paused-probe")
    jobs.pause_job(job["id"])
    return job


def test_doctor_reports_open_incident_on_paused_job(cron_home, capsys):
    from cron import incidents
    from hermes_cli.cron import cron_doctor

    job = _paused_job()
    incident_id, _ = incidents.upsert_incident(job["id"], "Script exited with code 1")

    assert cron_doctor() == 1
    out = capsys.readouterr().out
    assert job["id"] in out and "[paused]" in out
    assert f"open incident {incident_id}" in out


def test_doctor_reports_open_incident_for_deleted_job(cron_home, capsys):
    from cron import incidents
    from hermes_cli.cron import cron_doctor

    incident_id, _ = incidents.upsert_incident("deadbeef0000", "boom")

    assert cron_doctor() == 1
    out = capsys.readouterr().out
    assert "deadbeef0000" in out and "job no longer exists" in out
    assert f"open incident {incident_id}" in out


def test_doctor_clean_once_incidents_are_closed(cron_home, capsys):
    from cron import incidents
    from hermes_cli.cron import cron_doctor

    job = _paused_job()
    paused_id, _ = incidents.upsert_incident(job["id"], "Script exited with code 1")
    orphan_id, _ = incidents.upsert_incident("deadbeef0000", "boom")
    assert incidents.ack_incident(paused_id) and incidents.ack_incident(orphan_id)

    assert cron_doctor() == 0
    assert "found no issues" in capsys.readouterr().out


def test_doctor_ignores_resolved_incident_on_paused_job(cron_home, capsys):
    from cron import incidents
    from hermes_cli.cron import cron_doctor

    job = _paused_job()
    incident_id, _ = incidents.upsert_incident(job["id"], "flaky")
    assert incidents.set_incident_state(incident_id, "resolved")

    assert cron_doctor() == 0
