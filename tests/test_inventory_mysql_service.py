import pytest

from core.exceptions import NameLackError, NegativeError, NoItemError, StockShortError
from core.inventory_mysql_service import InventoryMySQLService
from core.item import Item


class FakeDBItem:
    def __init__(
        self,
        pid="A001",
        item_name="Apple",
        qty=10,
        receiver="",
        shipper="",
    ):
        self.pid = pid
        self.item_name = item_name
        self.qty = qty
        self.receiver = receiver
        self.shipper = shipper


class FakeMySQLRepo:
    def __init__(self, db_item=None):
        self.db_item = db_item
        self.created = None
        self.updated = None

    def get_by_pid(self, pid):
        return self.db_item

    def create_item(self, pid, name, qty, receiver="", shipper=""):
        self.created = {
            "pid": pid.strip().upper(),
            "name": name,
            "qty": qty,
            "receiver": receiver,
            "shipper": shipper,
        }
        return Item(
            pid=pid.strip().upper(),
            name=name,
            current_qty=qty,
            buyer=receiver,
            shipper=shipper,
        )

    def update_item(self, db_item, qty, receiver="", shipper=""):
        db_item.qty = qty
        db_item.receiver = receiver
        db_item.shipper = shipper

        self.updated = {
            "pid": db_item.pid,
            "qty": qty,
            "receiver": receiver,
            "shipper": shipper,
        }

        return self.to_item(db_item)

    @staticmethod
    def to_item(db_item):
        return Item(
            pid=db_item.pid,
            name=db_item.item_name,
            current_qty=db_item.qty,
            buyer=db_item.receiver,
            shipper=db_item.shipper,
        )


def test_get_item_success():
    repo = FakeMySQLRepo(FakeDBItem(pid="A001", item_name="Apple", qty=10))
    service = InventoryMySQLService(repo)

    item = service.get_item("A001")

    assert item.pid == "A001"
    assert item.name == "Apple"
    assert item.current_qty == 10


def test_get_item_not_found():
    repo = FakeMySQLRepo(None)
    service = InventoryMySQLService(repo)

    with pytest.raises(NoItemError):
        service.get_item("A001")


def test_inventory_in_creates_new_item():
    repo = FakeMySQLRepo(None)
    service = InventoryMySQLService(repo)

    item = service.inventory_in(
        pid="a001",
        name="Apple",
        qty=5,
    )

    assert item.pid == "A001"
    assert item.name == "Apple"
    assert item.current_qty == 5
    assert repo.created["receiver"] == ""
    assert repo.created["shipper"] == ""


def test_inventory_in_existing_item_adds_qty():
    repo = FakeMySQLRepo(FakeDBItem(pid="A001", item_name="Apple", qty=10))
    service = InventoryMySQLService(repo)

    item = service.inventory_in(
        pid="A001",
        name="Apple",
        qty=5,
    )

    assert item.current_qty == 15
    assert repo.updated["qty"] == 15
    assert repo.updated["receiver"] == ""
    assert repo.updated["shipper"] == ""


def test_inventory_in_new_item_requires_name():
    repo = FakeMySQLRepo(None)
    service = InventoryMySQLService(repo)

    with pytest.raises(NameLackError):
        service.inventory_in(
            pid="A001",
            name="",
            qty=5,
        )


def test_inventory_in_rejects_zero_qty():
    repo = FakeMySQLRepo(None)
    service = InventoryMySQLService(repo)

    with pytest.raises(NegativeError):
        service.inventory_in(
            pid="A001",
            name="Apple",
            qty=0,
        )

def test_inventory_out_success():
    repo = FakeMySQLRepo(FakeDBItem(pid="A001", item_name="Apple", qty=10))
    service = InventoryMySQLService(repo)

    item = service.inventory_out(
        pid="A001",
        name="Apple",
        qty=4,
        receiver="Bob",
        shipper="Tom",
    )

    assert item.current_qty == 6
    assert item.buyer == "Bob"
    assert item.shipper == "Tom"
    assert repo.updated["qty"] == 6


def test_inventory_out_item_not_found():
    repo = FakeMySQLRepo(None)
    service = InventoryMySQLService(repo)

    with pytest.raises(NoItemError):
        service.inventory_out(
            pid="A001",
            name="Apple",
            qty=4,
            receiver="Bob",
            shipper="Tom",
        )


def test_inventory_out_requires_receiver_and_shipper():
    repo = FakeMySQLRepo(FakeDBItem(pid="A001", item_name="Apple", qty=10))
    service = InventoryMySQLService(repo)

    with pytest.raises(NameLackError):
        service.inventory_out(
            pid="A001",
            name="Apple",
            qty=4,
            receiver="",
            shipper="Tom",
        )


def test_inventory_out_rejects_over_stock():
    repo = FakeMySQLRepo(FakeDBItem(pid="A001", item_name="Apple", qty=3))
    service = InventoryMySQLService(repo)

    with pytest.raises(StockShortError):
        service.inventory_out(
            pid="A001",
            name="Apple",
            qty=4,
            receiver="Bob",
            shipper="Tom",
        )


def test_inventory_out_rejects_blank_pid():
    repo = FakeMySQLRepo(FakeDBItem(pid="A001", item_name="Apple", qty=10))
    service = InventoryMySQLService(repo)

    with pytest.raises(NameLackError):
        service.inventory_out(
            pid=" ",
            name="Apple",
            qty=4,
            receiver="Bob",
            shipper="Tom",
        )
