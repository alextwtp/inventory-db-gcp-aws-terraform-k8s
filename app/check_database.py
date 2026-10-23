from sqlalchemy import text
from db import SessionLocal

def main():
    db = SessionLocal()

    try:
        result = db.execute(text("SELECT 1 AS test_value"))
        row = result.fetchone()
        print("Database OK:", row.test_value)
    finally:
        db.close()

if __name__ == "__main__":
    main()