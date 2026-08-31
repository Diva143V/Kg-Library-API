"""
Database initialization script to create tables in the configured SQL database (Supabase/PostgreSQL).
"""

import os
import sys
from sqlalchemy import create_engine
from kg_library_api.core.schema import Base


def main():
    db_url = os.getenv("KG_LIBRARY_DATABASE_URL")
    if not db_url:
        print("Error: KG_LIBRARY_DATABASE_URL environment variable is not set.")
        print("Please set it to your database connection string and try again.")
        sys.exit(1)

    print("Connecting to database to initialize tables...")
    try:
        engine = create_engine(db_url)
        # Create all tables defined in schema.py
        Base.metadata.create_all(engine)
        print("Successfully created/verified all tables on Supabase:")
        print(" - nodes")
        print(" - relationships")
        print(" - collections")
        print(" - annotations")
        print(" - annotation_relationships")
        print(" - annotation_collections")
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
