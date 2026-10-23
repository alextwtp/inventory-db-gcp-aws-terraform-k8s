import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

import app.main as main
from core.exceptions import AppError
from core.item import Item


class DummyDb:
    def __init__(self):
        self.rollback_called = False

    def rollback(self):
        self.rollback_called = True


class FakeService:
    def __init__(self):
        self.calls = []

    def get_item(self, pid):
        self.calls.append(("get_item", pid))
        return Item(
            pid=pid,
            name="Test Item",
            current_qty=10,
            row=1,
            buyer="",
            shipper="",
        )

    def inventory_in(self, pid, name, qty, receiver, shipper):
        self.calls.append(("inventory_in", pid, name, qty, receiver, shipper))
        return Item(
            pid=pid,
            name=name,
            current_qty=15,
            row=1,
            buyer=receiver,
            shipper=shipper,
        )

    def inventory_out(self, pid, name, qty, receiver, shipper):
        self.calls.append(("inventory_out", pid, name, qty, receiver, shipper))
        return Item(
            pid=pid,
            name=name,
            current_qty=5,
            row=1,
            buyer=receiver,
            shipper=shipper,
        )


class FakeAppError(AppError):
    status_code = 404

    def __init__(self, message):
        Exception.__init__(self, message)


class FailingService:
    def get_item(self, pid):
        raise FakeAppError("Item not found")


class DatabaseFailingService:
    def inventory_in(self, pid, name, qty, receiver, shipper):
        raise SQLAlchemyError("database failed")


@pytest.fixture
def dummy_db():
    return DummyDb()


@pytest.fixture(autouse=True)
def override_db(dummy_db):
    def _override_get_db():
        yield dummy_db

    main.app.dependency_overrides[main.get_db] = _override_get_db
    yield
    main.app.dependency_overrides.clear()


@pytest.fixture
def client():
    original_startup = list(main.app.router.on_startup)
    main.app.router.on_startup.clear()

    with TestClient(main.app) as test_client:
        yield test_client

    main.app.router.on_startup[:] = original_startup


def test_root_status(client):  
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_get_item_success(client, monkeypatch):
    fake_service = FakeService()
    monkeypatch.setattr(main, "get_service", lambda db: fake_service)

    response = client.get("/item/A001")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "success"
    assert body["message"] == "Item found"
    assert body["item"]["pid"] == "A001"
    assert body["item"]["name"] == "Test Item"
    assert body["item"]["current_qty"] == 10
    assert fake_service.calls == [("get_item", "A001")]


def test_inventory_in_success(client, monkeypatch):
    fake_service = FakeService()
    monkeypatch.setattr(main, "get_service", lambda db: fake_service)

    payload = {
        "pid": "A001",
        "name": "MOUSE",
        "qty": 5,
        "receiver": "",
        "shipper": "Vendor A",
    }

    response = client.post("/inventory/in", json=payload)

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "success"
    assert body["message"] == "Inventory-in success"
    assert body["item"]["pid"] == "A001"
    assert body["item"]["name"] == "MOUSE"
    assert body["item"]["current_qty"] == 15
    assert body["item"]["shipper"] == "Vendor A"

    assert fake_service.calls == [
        ("inventory_in", "A001", "MOUSE", 5, "", "Vendor A")
    ]

def test_inventory_out_success(client, monkeypatch):
    fake_service = FakeService()
    monkeypatch.setattr(main, "get_service", lambda db: fake_service)

    payload = {
        "pid": "A001",
        "name": "MOUSE",
        "qty": 5,
        "receiver": "Customer A",
        "shipper": "",
    }

    response = client.post("/inventory/out", json=payload)

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "success"
    assert body["message"] == "Inventory-out success"
    assert body["item"]["pid"] == "A001"
    assert body["item"]["name"] == "MOUSE"
    assert body["item"]["current_qty"] == 5
    assert body["item"]["buyer"] == "Customer A"

    assert fake_service.calls == [
        ("inventory_out", "A001", "MOUSE", 5, "Customer A", "")
    ]


def test_app_error_returns_http_error(client, monkeypatch):
    monkeypatch.setattr(main, "get_service", lambda db: FailingService())

    response = client.get("/item/NO_SUCH_ID")

    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}


def test_sqlalchemy_error_rolls_back_and_returns_500(
    client, monkeypatch, dummy_db
):
    monkeypatch.setattr(main, "get_service", lambda db: DatabaseFailingService())

    payload = {
        "pid": "A001",
        "name": "MOUSE",
        "qty": 5,
        "receiver": "",
        "shipper": "Vendor A",
    }

    response = client.post("/inventory/in", json=payload)

    assert response.status_code == 500
    assert response.json() == {"detail": "Database error"}
    assert dummy_db.rollback_called is True