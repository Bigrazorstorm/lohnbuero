#!/usr/bin/env python3
"""
Database migration script - adds missing columns without affecting existing data.
Run this on startup to ensure the database schema is up to date.
"""
import sys
from sqlalchemy import create_engine, text, inspect


def get_database_url():
    import os
    return os.environ.get('DATABASE_URL', 'mysql+pymysql://lohnbuero:lohnbuero123@mysql:3306/lohnbuero')


def table_exists(inspector, table_name):
    """Check if a table exists in the database."""
    return table_name in inspector.get_table_names()


def get_table_columns(inspector, table_name):
    """Safely get columns for a table, returns empty list if table doesn't exist."""
    if not table_exists(inspector, table_name):
        return []
    return [c['name'] for c in inspector.get_columns(table_name)]


def migrate():
    engine = create_engine(get_database_url())
    
    with engine.connect() as conn:
        inspector = inspect(engine)
        
        # --- mandanten table ---
        if table_exists(inspector, 'mandanten'):
            mandanten_columns = get_table_columns(inspector, 'mandanten')
            
            if 'workflow_konfiguration' not in mandanten_columns:
                print("Adding workflow_konfiguration column to mandanten...")
                conn.execute(text(
                    "ALTER TABLE mandanten ADD COLUMN workflow_konfiguration TEXT"
                ))
                conn.commit()
                print("  ✓ Added workflow_konfiguration")
            else:
                print("  ✓ workflow_konfiguration already exists")
        else:
            print("  ℹ mandanten table does not exist yet (will be created on app startup)")
        
        # --- workflow_vorlage_items table ---
        if table_exists(inspector, 'workflow_vorlage_items'):
            vorlage_items_columns = get_table_columns(inspector, 'workflow_vorlage_items')
            
            if 'ist_kernprozess' not in vorlage_items_columns:
                print("Adding ist_kernprozess column to workflow_vorlage_items...")
                conn.execute(text(
                    "ALTER TABLE workflow_vorlage_items ADD COLUMN ist_kernprozess BOOLEAN DEFAULT FALSE"
                ))
                conn.commit()
                print("  ✓ Added ist_kernprozess")
            else:
                print("  ✓ ist_kernprozess already exists")
            
            if 'ist_optional_pro_mandant' not in vorlage_items_columns:
                print("Adding ist_optional_pro_mandant column to workflow_vorlage_items...")
                conn.execute(text(
                    "ALTER TABLE workflow_vorlage_items ADD COLUMN ist_optional_pro_mandant BOOLEAN DEFAULT FALSE"
                ))
                conn.commit()
                print("  ✓ Added ist_optional_pro_mandant")
            else:
                print("  ✓ ist_optional_pro_mandant already exists")
        else:
            print("  ℹ workflow_vorlage_items table does not exist yet (will be created on app startup)")
    
    print("\n✅ Migration check complete!")


if __name__ == '__main__':
    try:
        migrate()
    except Exception as e:
        print(f"Migration error: {e}", file=sys.stderr)
        sys.exit(1)