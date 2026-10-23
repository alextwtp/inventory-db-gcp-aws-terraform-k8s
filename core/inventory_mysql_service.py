from core.exceptions import (
    NameLackError,
    NegativeError,
    NoItemError,
    StockShortError,
)
from core.item import Item


class InventoryMySQLService:
    """Business logic for MySQL-backed inventory operations."""

    def __init__(self, repo):
        self.repo = repo

    def get_item(self, pid: str) -> Item:
        db_item = self.repo.get_by_pid(pid)

        if db_item is None:
            raise NoItemError("Item not found")

        return self.repo.to_item(db_item)

    def inventory_in(
        self,
        pid: str,
        name: str,
        qty: int,
        receiver: str = "",
        shipper: str = "",
    ) -> Item:
        self._validate_pid(pid)
        self._validate_qty(qty)

        db_item = self.repo.get_by_pid(pid)

        if db_item is None:
            if not name:
                raise NameLackError("Item name is required for new inventory item.")

            return self.repo.create_item(
                pid=pid,
                name=name,
                qty=qty,
                receiver="",
                shipper="",
            )

        new_qty = db_item.qty + qty

        return self.repo.update_item(
            db_item=db_item,
            qty=new_qty,
            receiver="",
            shipper="",
        )

    def inventory_out(
        self,
        pid: str,
        name: str,
        qty: int,
        receiver: str,
        shipper: str,
    ) -> Item:
        self._validate_pid(pid)
        self._validate_qty(qty)

        if not receiver or not shipper:
            raise NameLackError(
                "Buyer and shipper names must be provided for stock-out operations."
            )

        db_item = self.repo.get_by_pid(pid)

        if db_item is None:
            raise NoItemError("Item not found")

        if qty > db_item.qty:
            raise StockShortError("Insufficient inventory quantity.")

        new_qty = db_item.qty - qty

        return self.repo.update_item(
            db_item=db_item,
            qty=new_qty,
            receiver=receiver,
            shipper=shipper,
        )

    @staticmethod
    def _validate_pid(pid: str) -> None:
        if not pid or not pid.strip():
            raise NameLackError("Product ID is required.")

    @staticmethod
    def _validate_qty(qty: int) -> None:
        if qty <= 0:
            raise NegativeError("Quantity must be greater than zero.")
