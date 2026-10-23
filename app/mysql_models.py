from sqlalchemy import Column, DateTime, Integer, String, CheckConstraint
from sqlalchemy.orm import validates

try:
    from app.db import Base
except ImportError:
    from db import Base


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Use CheckConstraint to ensure the pid is in Uppercase
    pid = Column(
        String(50),
        CheckConstraint("pid = UPPER(pid)", name="check_pid_uppercase"),
        nullable=False,
        unique=True
    )
    
    # Use CheckConstraint to ensure the qty is greater than or equal to 0
    qty = Column(
        Integer, 
        CheckConstraint("qty >= 0", name="check_qty_greater_than_or_equal_zero"),
        nullable=False, 
        default=0  
    )
    
    item_name = Column(String(100), nullable=False)
    receiver = Column(String(100), nullable=False)
    shipper = Column(String(100), nullable=False)

    # 1. Use Python validation level automatic uppercase conversion: include pid and other three fields
    @validates("pid", "item_name", "receiver", "shipper")
    def validate_all_uppercase(self, key, value):
        if value is not None:
            return value.upper()
        return value

    # 2. Use CheckConstraint to ensure the qty is greater than or equal to 0
    @validates("qty")
    def validate_qty_positive(self, key, value):
        if value is not None and value < 0:
            raise ValueError(f"{key} must be a Non-negative number")
        return value