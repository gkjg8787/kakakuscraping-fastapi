import pytest
import tempfile
import pathlib


@pytest.fixture
def tmp_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield pathlib.Path(tmpdir)
