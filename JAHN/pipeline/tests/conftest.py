import os
import pathlib
import subprocess

import pytest

DATA = pathlib.Path(os.environ.get("ABPIPE_DATA_DIR", os.path.expanduser("~/hackathon-team-3/apheris/hackathon-data")))
HERE = pathlib.Path(__file__).resolve().parent


def pytest_collection_modifyitems(config, items):
    ok = DATA.exists()
    try:
        import abguard  # noqa: F401
    except Exception:
        ok = False
    if not ok:
        skip = pytest.mark.skip(reason="needs abguard and the organiser data (set ABPIPE_DATA_DIR)")
        for item in items:
            if "needs_data" in item.keywords:
                item.add_marker(skip)


@pytest.fixture(scope="session")
def data_dir():
    return DATA


@pytest.fixture(scope="session")
def repo_root():
    out = subprocess.run(["git", "-C", str(HERE), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    return pathlib.Path(out.stdout.strip())


@pytest.fixture(scope="session")
def pipeline_dir():
    return HERE.parent
