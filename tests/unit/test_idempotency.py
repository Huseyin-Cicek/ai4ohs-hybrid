# filepath: tests/unit/test_idempotency.py


from src.utils.stamps import read_stamp_or_epoch, write_stamp_atomic


def test_stamp_idempotency(tmp_path):
    stamp_dir = tmp_path / "stamps"
    write_stamp_atomic(stamp_dir, "test")
    write_stamp_atomic(stamp_dir, "test")  # Idempotent
    assert read_stamp_or_epoch(stamp_dir, "test") != datetime.fromtimestamp(0)


def test_stamp_missing_fallback(tmp_path):
    stamp_dir = tmp_path / "stamps"
    assert read_stamp_or_epoch(stamp_dir, "missing") == datetime.fromtimestamp(0)
