#!/usr/bin/env python3
"""
Database initialization script
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from src.database import db
from src.models import Base


def init_database():
    """Initialize the database with all tables"""
    try:
        logger.info("Initializing database...")
        db.create_tables()
        logger.info("✅ Database initialized successfully!")

        # Verify tables
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        logger.info(f"Created {len(tables)} tables:")
        for table in tables:
            logger.info(f"  - {table}")

        return True

    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
