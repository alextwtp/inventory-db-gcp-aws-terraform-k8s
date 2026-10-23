from sqlalchemy import create_engine, text

from db import DATABASE_URL


engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("MySQL connection OK:", result.scalar())
except Exception as e:
    print("MySQL connection failed:")
    print(e)
