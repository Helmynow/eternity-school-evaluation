#!/usr/bin/env python3
"""
Apply all database migrations directly via SQL connection
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get database connection from environment"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not set in environment")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)

def apply_migration(conn, migration_file):
    """Apply a single migration file"""
    print(f"\n📄 Applying: {migration_file.name}")
    
    try:
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        # Execute the SQL, handling errors gracefully
        with conn.cursor() as cur:
            try:
                cur.execute(sql)
                print(f"✅ Successfully applied: {migration_file.name}")
                return True
            except psycopg2.errors.DuplicateObject as e:
                # Object already exists - this is OK for migrations that may have been partially applied
                if 'already exists' in str(e).lower():
                    print(f"⚠️  Some objects already exist (may be partially applied): {migration_file.name}")
                    print(f"   Continuing...")
                    return True
                else:
                    raise
            except psycopg2.errors.DuplicateTable as e:
                print(f"⚠️  Table already exists: {migration_file.name}")
                print(f"   Continuing...")
                return True
            except psycopg2.errors.DuplicateFunction as e:
                print(f"⚠️  Function already exists: {migration_file.name}")
                print(f"   Continuing...")
                return True
            except Exception as e:
                # Check if it's a "does not exist" error (which is OK for DROP IF EXISTS)
                if 'does not exist' in str(e).lower() and 'drop' in sql.lower():
                    print(f"⚠️  Object doesn't exist (OK for DROP IF EXISTS): {migration_file.name}")
                    return True
                raise
        
    except Exception as e:
        print(f"❌ Error applying {migration_file.name}: {e}")
        print(f"   Error details: {str(e)}")
        return False

def main():
    """Apply all migrations in order"""
    migrations_dir = Path(__file__).parent / 'supabase' / 'migrations'
    
    if not migrations_dir.exists():
        print(f"❌ Migrations directory not found: {migrations_dir}")
        sys.exit(1)
    
    # Get all migration files sorted by name
    migration_files = sorted(migrations_dir.glob('*.sql'))
    
    if not migration_files:
        print("❌ No migration files found")
        sys.exit(1)
    
    print(f"🔍 Found {len(migration_files)} migration files")
    print("=" * 60)
    
    # Connect to database
    print("🔌 Connecting to database...")
    conn = get_db_connection()
    print("✅ Connected")
    
    # Apply each migration
    success_count = 0
    failed_count = 0
    
    for migration_file in migration_files:
        if apply_migration(conn, migration_file):
            success_count += 1
        else:
            failed_count += 1
            print(f"\n⚠️  Stopping after error in {migration_file.name}")
            print("   Fix the error and run again to continue")
            break
    
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"✅ Successfully applied: {success_count}")
    if failed_count > 0:
        print(f"❌ Failed: {failed_count}")
        sys.exit(1)
    else:
        print("🎉 All migrations applied successfully!")

if __name__ == "__main__":
    main()
