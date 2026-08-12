import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/test.db"
os.environ["LLM_PROVIDER"] = "auto"
os.environ["OPENAI_API_KEY"] = ""
os.environ["DASHSCOPE_API_KEY"] = ""
database_file = Path("data/test.db")
if database_file.exists():
    database_file.unlink()

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client
