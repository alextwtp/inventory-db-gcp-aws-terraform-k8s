from db import engine, SessionLocal, Base
from mysql_models import Inventory


def create_tables():
    Base.metadata.create_all(bind=engine)

def insert_sample_item():
    db = SessionLocal()

    try:
        item = Inventory(
            pid="N001",
            item_name="Nance",
            qty=10,
            receiver="Alex",
            shipper="Tommy",
        )

        db.add(item)
        db.commit()
        db.refresh(item)

        print("Inserted item:")
        print(item.pid, item.item_name, item.qty, item.receiver, item.shipper)

    except Exception as e:
        db.rollback()
        print("Error:", e)

    finally:
        db.close()

def query_items():
    db = SessionLocal()

    try:
        items = db.query(Inventory).all()
        print("Current items:")
        for item in items:
            print(item.pid, item.item_name, item.qty, item.receiver, item.shipper)

    finally:
        db.close() 

if __name__ == "__main__":
    create_tables()
    insert_sample_item()
    query_items()