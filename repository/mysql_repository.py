from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.mysql_models import Inventory
from core.item import Item
from core.logger import logger 


class MySQLRepository:
    """Repository for MySQL-backed inventory storage."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_pid(self, pid: str) -> Inventory | None:
        normalized_pid = self._normalize_pid(pid)
        logger.info(f"Fetching item from MySQL by PID: {normalized_pid}")
        try:
            return (
                self.db.query(Inventory)
                .filter(Inventory.pid == normalized_pid)
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error fetching item PID {normalized_pid}: {str(e)}", exc_info=True)
            raise e

    def create_item(
        self,
        pid: str,
        name: str,
        qty: int,
        receiver: str = "",
        shipper: str = "",
    ) -> Item:
        normalized_pid = self._normalize_pid(pid)
        logger.info(f"Creating new inventory item: {normalized_pid} ({name})")
        
        try:
            db_item = Inventory(
                pid=normalized_pid,
                item_name=name,
                qty=qty,
                receiver=receiver,
                shipper=shipper,
            )

            self.db.add(db_item)
            self.db.commit()
            self.db.refresh(db_item)
            
            logger.info(f"Successfully created inventory item: {normalized_pid}")
            return self.to_item(db_item)
        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Failed to create item {normalized_pid}: {str(e)}", exc_info=True)
            raise e

    def update_item(
        self,
        db_item: Inventory,
        qty: int,
        receiver: str = "",
        shipper: str = "",
    ) -> Item:
        logger.info(f"Updating inventory item: {db_item.pid}, new qty: {qty}")
        try:
            db_item.qty = qty
            db_item.receiver = receiver
            db_item.shipper = shipper

            self.db.commit()
            self.db.refresh(db_item)

            return self.to_item(db_item)
        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Failed to update item {db_item.pid}: {str(e)}", exc_info=True)
            raise e

    def rollback(self) -> None:
        logger.warning("Rolling back active database transaction")
        self.db.rollback()

    @staticmethod
    def to_item(db_item: Inventory) -> Item:
        return Item(
            pid=db_item.pid,
            name=db_item.item_name,
            current_qty=db_item.qty,
            buyer=db_item.receiver,
            shipper=db_item.shipper,
        )

    @staticmethod
    def _normalize_pid(pid: str) -> str:
        return pid.strip().upper()