"""
Query database tables from PetClinic PostgreSQL database
"""
import psycopg2
import json
import argparse
from pathlib import Path

def load_config(config_path="db_config.json", env_name="target"):
    """Load database configuration from JSON file"""
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config['environments'][env_name]

def get_connection(env_config):
    """Create PostgreSQL connection from environment config"""
    return psycopg2.connect(
        host=env_config['host'],
        port=env_config['port'],
        database=env_config['database'],
        user=env_config['username'],
        password=env_config['password']
    )

def query_tables(env_name="target", config_path="db_config.json"):
    """Query all tables from the database"""
    try:
        # Load configuration
        env_config = load_config(config_path, env_name)
        
        print(f"\nUsing environment: {env_name}")
        print(f"Database: {env_config['database']}")
        print(f"Host: {env_config['host']}\n")
        
        conn = get_connection(env_config)
        cursor = conn.cursor()
        
        # Get all tables (PostgreSQL version)
        query = """
            SELECT 
                table_schema, 
                table_name,
                (SELECT COUNT(*) 
                 FROM information_schema.columns c 
                 WHERE c.table_schema = t.table_schema 
                   AND c.table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_type = 'BASE TABLE'
              AND table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name
        """
        
        cursor.execute(query)
        tables = cursor.fetchall()
        
        print("\n" + "="*70)
        print(f"DATABASE: {env_config['database']}")
        print(f"HOST: {env_config.get('host', 'N/A')}")
        print("="*70)
        print(f"\nTotal Tables Found: {len(tables)}\n")
        
        for row in tables:
            print(f"  {row[0]}.{row[1]:<40} ({row[2]} columns)")
        
        print("\n" + "="*70)
        print("Getting detailed column information for each table...")
        print("="*70 + "\n")
        
        for row in tables:
            schema = row[0]
            table = row[1]
            
            # Get columns for this table (PostgreSQL version)
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """, (schema, table))
            
            columns = cursor.fetchall()
            
            print(f"\n{schema}.{table}")
            print("-" * 70)
            for col in columns:
                col_name = col[0]
                data_type = col[1]
                max_len = f"({col[2]})" if col[2] else ""
                nullable = "NULL" if col[3] == "YES" else "NOT NULL"
                default = f" DEFAULT {col[4]}" if col[4] else ""
                print(f"  {col_name:<30} {data_type}{max_len:<15} {nullable}{default}")
        
        # Get row counts
        print("\n" + "="*70)
        print("Row Counts:")
        print("="*70 + "\n")
        
        for row in tables:
            schema = row[0]
            table = row[1]
            cursor.execute(f'SELECT COUNT(*) FROM "{schema}"."{table}"')
            count = cursor.fetchone()[0]
            print(f"  {schema}.{table:<40} {count:>10} rows")
        
        conn.close()
        print("\n" + "="*70)
        print("Query completed successfully")
        print("="*70)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Query database tables')
    parser.add_argument('--env', type=str, default='target',
                        choices=['source', 'target', 'local'],
                        help='Environment to use (default: target)')
    parser.add_argument('--config', type=str, default='../db_config.json',
                        help='Path to config file (default: ../db_config.json)')
    
    args = parser.parse_args()
    query_tables(args.env, args.config)
