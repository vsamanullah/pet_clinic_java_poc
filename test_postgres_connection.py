"""
Test PostgreSQL connection for PetClinic database
Database: prj-unicr-dev-svc-mig-demo:us-central1:pg-9
Host IP: 10.130.73.5
Port: 5432
Database: petclinic
Credentials: petclinic/petclinic
"""

import psycopg2
from psycopg2 import OperationalError, Error
import sys

def test_postgres_connection():
    """Test connection to PetClinic PostgreSQL database"""
    
    connection_params = {
        'host': '10.130.73.5',
        'port': 5432,
        'database': 'petclinic',
        'user': 'petclinic',
        'password': 'petclinic'
    }
    
    print("=" * 60)
    print("Testing PostgreSQL Connection")
    print("=" * 60)
    print(f"Host: {connection_params['host']}")
    print(f"Port: {connection_params['port']}")
    print(f"Database: {connection_params['database']}")
    print(f"User: {connection_params['user']}")
    print("-" * 60)
    
    connection = None
    try:
        print("\nAttempting to connect...")
        connection = psycopg2.connect(**connection_params)
        
        print("✓ Connection successful!")
        
        # Get PostgreSQL version
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print(f"\nPostgreSQL Version:")
        print(f"  {db_version[0]}")
        
        # Get list of tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        print(f"\nTables in database '{connection_params['database']}':")
        if tables:
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("  No tables found in public schema")
        
        # Get table count
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        table_count = cursor.fetchone()[0]
        print(f"\nTotal tables: {table_count}")
        
        cursor.close()
        print("\n" + "=" * 60)
        print("Database is REACHABLE and accessible!")
        print("=" * 60)
        return True
        
    except OperationalError as e:
        print(f"\n✗ Connection failed!")
        print(f"\nError details:")
        print(f"  Type: OperationalError")
        print(f"  Message: {str(e)}")
        print("\nPossible reasons:")
        print("  1. Database server is not running")
        print("  2. Firewall blocking connection")
        print("  3. Incorrect host IP or port")
        print("  4. Network connectivity issues")
        print("  5. Database instance not accessible from this location")
        return False
        
    except Error as e:
        print(f"\n✗ Database error!")
        print(f"\nError details:")
        print(f"  Type: {type(e).__name__}")
        print(f"  Message: {str(e)}")
        return False
        
    except Exception as e:
        print(f"\n✗ Unexpected error!")
        print(f"\nError details:")
        print(f"  Type: {type(e).__name__}")
        print(f"  Message: {str(e)}")
        return False
        
    finally:
        if connection:
            connection.close()
            print("\nConnection closed.")

if __name__ == "__main__":
    success = test_postgres_connection()
    sys.exit(0 if success else 1)
