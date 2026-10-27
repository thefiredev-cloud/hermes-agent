"""verify_sqlite_integrity must separate proven corruption from unverified states."""

import sqlite3

from hermes_cli.backup import verify_sqlite_integrity


def test_valid_database_is_ok(tmp_path):
    db = tmp_path / "state.db"
    conn = sqlite3.connect(str(db))
    conn.execute("CREATE TABLE t (v TEXT)")
    conn.commit()
    conn.close()

    result = verify_sqlite_integrity(db, check_header=True, run_pragma=True)

    assert result["status"] == "ok"
    assert result["valid"] is True


def test_zeroed_header_is_proven_corrupt(tmp_path):
    db = tmp_path / "state.db"
    db.write_bytes(b"\x00" * 4096)

    result = verify_sqlite_integrity(db, check_header=True, run_pragma=True)

    assert result["status"] == "corrupt"
    assert result["valid"] is False


def test_missing_file_is_unverified_not_corrupt(tmp_path):
    result = verify_sqlite_integrity(tmp_path / "absent.db", check_header=True, run_pragma=True)

    assert result["status"] == "unverified"
    assert result["valid"] is False
