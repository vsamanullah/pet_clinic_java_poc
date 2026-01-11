"""
Query and display all content from PetClinic PostgreSQL database
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

def query_database_content(env_name="target", config_path="db_config.json"):
    """Query and display all content from all tables"""
    try:
        # Load configuration
        env_config = load_config(config_path, env_name)
        
        print(f"\n{'='*80}")
        print(f"PETCLINIC DATABASE CONTENT")
        print(f"{'='*80}")
        print(f"Environment: {env_name}")
        print(f"Database: {env_config['database']}")
        print(f"Host: {env_config['host']}")
        print(f"{'='*80}\n")
        
        conn = get_connection(env_config)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
              AND table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        
        for schema, table in tables:
            # Get column names
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """, (schema, table))
            
            columns = cursor.fetchall()
            column_names = [col[0] for col in columns]
            
            # Get all data from table
            cursor.execute(f'SELECT * FROM "{schema}"."{table}"')
            rows = cursor.fetchall()
            
            # Display table header
            print(f"\n{'='*80}")
            print(f"TABLE: {schema}.{table.upper()}")
            print(f"{'='*80}")
            print(f"Total Rows: {len(rows)}")
            
            if rows:
                # Calculate column widths
                col_widths = []
                for i, col_name in enumerate(column_names):
                    max_width = len(str(col_name))
                    for row in rows:
                        if row[i] is not None:
                            max_width = max(max_width, len(str(row[i])))
                    col_widths.append(min(max_width + 2, 30))  # Cap at 30 chars
                
                # Print header
                print("\n" + "-"*80)
                header = " | ".join([str(col_name).ljust(col_widths[i]) 
                                    for i, col_name in enumerate(column_names)])
                print(header)
                print("-"*80)
                
                # Print rows
                for row in rows:
                    row_str = " | ".join([str(val if val is not None else 'NULL').ljust(col_widths[i])[:col_widths[i]] 
                                         for i, val in enumerate(row)])
                    print(row_str)
            else:
                print("\n(No data in this table)")
        
        conn.close()
        
        print(f"\n{'='*80}")
        print("DATABASE CONTENT QUERY COMPLETED")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Query all database content')
    parser.add_argument('--env', type=str, default='target',
                        choices=['source', 'target', 'local'],
                        help='Environment to use (default: target)')
    parser.add_argument('--config', type=str, default='../db_config.json',
                        help='Path to config file (default: ../db_config.json)')
    
    args = parser.parse_args()
    query_database_content(args.env, args.config)
