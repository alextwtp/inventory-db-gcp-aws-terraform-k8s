import sys
from pathlib import Path

# Add the project's root directory to the Python module search path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Use standard module imports
from app.db import engine
from app.mysql_models import Base

# Create all tables
Base.metadata.create_all(bind=engine)

print("Tables created successfully.")