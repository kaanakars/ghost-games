"""Smoke test: every page of the web app runs without an error."""

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = Path(__file__).parents[1] / "app"
PAGES = [APP / "Home.py", *sorted((APP / "pages").glob("*.py"))]


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.stem)
def test_page_runs(page, monkeypatch):
    # pages import common.py from the app folder
    monkeypatch.syspath_prepend(str(APP))
    app = AppTest.from_file(str(page), default_timeout=30).run()
    assert not app.exception
