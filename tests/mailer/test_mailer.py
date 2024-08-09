import os
import tempfile
from pathlib import Path

import pytest

from experiment_runner.processing.mail import Mailer


@pytest.fixture
def create_temp_file():
    temp_files = []

    def _create_temp_file(size_mb):
        size_bytes = size_mb * 1024 * 1024
        line = "a" * 79 + "\n"  # 80 characters per line
        lines_needed = size_bytes // len(line)

        temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8", suffix=".log")
        for _ in range(lines_needed):
            temp_file.write(line)
        temp_file.close()

        temp_files.append(Path(temp_file.name))
        return temp_files[-1]

    yield _create_temp_file

    # Cleanup after tests
    for temp_file in temp_files:
        if temp_file.exists():
            temp_file.unlink()


def test_trim_large_file(create_temp_file):
    max_size_mb = 1  # 1MB
    file_size_mb = 2  # 2MB
    temp_file_path = create_temp_file(file_size_mb)

    initial_size = temp_file_path.stat().st_size
    assert initial_size > max_size_mb * 1024 * 1024, "File is not large enough for the test."

    new_file = Mailer().trim_file_to_size(temp_file_path, max_size_mb)
    trimmed_size = os.path.getsize(new_file)

    assert trimmed_size <= max_size_mb * 1024 * 1024, "File was not trimmed correctly."
    print(f"Initial size: {initial_size} bytes, Trimmed size: {trimmed_size} bytes")


def test_file_within_limit(create_temp_file):
    max_size_mb = 2  # 2MB
    file_size_mb = 1  # 1MB
    temp_file_path = create_temp_file(file_size_mb)

    initial_size = temp_file_path.stat().st_size
    assert initial_size <= max_size_mb * 1024 * 1024, "File size exceeds the limit for this test."

    Mailer().trim_file_to_size(temp_file_path, max_size_mb)
    trimmed_size = os.path.getsize(temp_file_path)

    assert initial_size == trimmed_size, "File should not have been trimmed."
    print(f"Initial size: {initial_size} bytes, Trimmed size: {trimmed_size} bytes")
