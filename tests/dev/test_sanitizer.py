# Test file in tests/dev/test_sanitizer.py


from scripts.dev.reorg_sanitizer import FileSanitizer


def test_file_size_validation(tmp_path):
    """Test file size exceeds limit is quarantined."""
    dropzone = tmp_path / "dropzone"
    sources = tmp_path / "sources"
    dropzone.mkdir()

    sanitizer = FileSanitizer(dropzone, sources)

    # Create oversized file (101MB)
    large_file = dropzone / "large.pdf"
    large_file.write_bytes(b"0" * (101 * 1024 * 1024))

    sanitizer.process_file(large_file)

    # Should be quarantined
    assert not large_file.exists()
    assert sanitizer.stats["quarantined"] == 1
    assert len(list(sanitizer.quarantine_dir.glob("*.quarantine.json"))) == 1


def test_duplicate_detection(tmp_path):
    """Test duplicate files are detected and deleted."""
    dropzone = tmp_path / "dropzone"
    sources = tmp_path / "sources"
    dropzone.mkdir()

    sanitizer = FileSanitizer(dropzone, sources)

    # Create two identical files
    file1 = dropzone / "doc1.pdf"
    file1.write_bytes(b"test content")

    file2 = dropzone / "doc2.pdf"
    file2.write_bytes(b"test content")

    # Process first file
    sanitizer.process_file(file1)
    assert sanitizer.stats["files_processed"] == 1

    # Process duplicate
    sanitizer.process_file(file2)
    assert sanitizer.stats["duplicates_skipped"] == 1
