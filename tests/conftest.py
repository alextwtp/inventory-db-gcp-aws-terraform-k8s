# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from api.fastapi_app import app  

# tests/conftest.py
@pytest.fixture
def client():
    return TestClient(app)