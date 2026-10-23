from db import SessionLocal
from mysql_models import Inventory


def main():
    db = SessionLocal()
    TEST_PID = "C719"
    db.query(Inventory).filter(Inventory.pid == TEST_PID).delete()
    db.commit()

    try:
        # INSERT
        item = Inventory(
            pid=TEST_PID,
            item_name="DUMMY",
            qty=30,
            receiver="LEE",
            shipper="CHAO",
        )
        
        db.add(item)
        db.commit()
        db.refresh(item)

        print("Inserted item id:", item.id)

        # SELECT
        found = db.query(Inventory).filter(Inventory.pid == TEST_PID).first()

        if found:
            print("Found:")
            print("pid:", found.pid)
            print("item_name:", found.item_name)
            print("qty:", found.qty)           
        else:
            print("Item not found")

    except Exception as e:
        db.rollback()
        print("Error:", e)

    finally:
        db.close()

if __name__ == "__main__":
    main()