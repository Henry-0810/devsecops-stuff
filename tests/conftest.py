import importlib
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def app_module(tmp_path_factory):
    # The app initializes SQLite at import time; never touch a developer's data.
    database = tmp_path_factory.mktemp("app-import") / "ideas.db"
    with patch.dict(os.environ, {"DATABASE_PATH": str(database)}):
        yield importlib.import_module("app.main")


@pytest.fixture
def client(app_module, tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "DATABASE_PATH", tmp_path / "ideas.db")
    app_module.initialize_database()
    with TestClient(app_module.app) as test_client:
        yield test_client
