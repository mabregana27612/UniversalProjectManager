"""
Script to run database migrations for schema updates
"""

from utils.database import create_tables

def run_migrations():
    """
    Run necessary database migrations
    """
    print("Running database migrations...")
    
    # Create any missing tables (including change_requests)
    create_tables()
    
    # Add new columns to existing tables if necessary
    # (create_tables handles this already in newer SQLAlchemy versions)
    
    print("Database migration completed")

if __name__ == "__main__":
    run_migrations()