"""
Query database tables from BookStore database
"""
import pyodbc
import json
import argparse
from pathlib import Path

def load_config(config_path="db_config.json", env_name="target"):
    """Load database configuration from JSON file"""
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config['environments'][env_name]

def build_connection_string(env_config):
    """Build ODBC connection string from environment config"""
    server = env_config.get('server', '')
    port = env_config.get('port', '')
    server_str = f"{server},{port}" if port else server
    
    return (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server_str};"
        f"DATABASE={env_config['database']};"
        f"UID={env_config.get('username', '')};"
        f"PWD={env_config.get('password', '')};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=yes"
    )

def query_tables(env_name="target", config_path="db_config.json"):
    """Query all tables from the database"""
    try:
        # Load configuration
        env_config = load_config(config_path, env_name)
        connection_string = build_connection_string(env_config)
        
        print(f"\nUsing environment: {env_name}")
        print(f"Database: {env_config['database']}\n")
        
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Get all tables
        query = """
            SELECT 
                TABLE_SCHEMA, 
                TABLE_NAME,
                (SELECT COUNT(*) 
                 FROM INFORMATION_SCHEMA.COLUMNS c 
                 WHERE c.TABLE_SCHEMA = t.TABLE_SCHEMA 
                   AND c.TABLE_NAME = t.TABLE_NAME) as ColumnCount
            FROM INFORMATION_SCHEMA.TABLES t
            WHERE TABLE_TYPE = 'BASE TABLE'
              AND TABLE_SCHEMA NOT IN ('sys', 'INFORMATION_SCHEMA')
            ORDER BY TABLE_SCHEMA, TABLE_NAME
        """
        
        cursor.execute(query)
        tables = cursor.fetchall()
        
        print("\n" + "="*70)
        print(f"DATABASE: {env_config['database']}")
        print(f"SERVER: {env_config.get('server', 'N/A')}")
        print("="*70)
        print(f"\nTotal Tables Found: {len(tables)}\n")
        
        for row in tables:
            print(f"  {row.TABLE_SCHEMA}.{row.TABLE_NAME:<40} ({row.ColumnCount} columns)")
        
        print("\n" + "="*70)
        print("Getting detailed column information for each table...")
        print("="*70 + "\n")
        
        for row in tables:
            schema = row.TABLE_SCHEMA
            table = row.TABLE_NAME
            
            # Get columns for this table
            cursor.execute(f"""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    IS_NULLABLE,
                    COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}'
                ORDER BY ORDINAL_POSITION
            """)
            
            columns = cursor.fetchall()
            
            print(f"\n{schema}.{table}")
            print("-" * 70)
            for col in columns:
                col_name = col.COLUMN_NAME
                data_type = col.DATA_TYPE
                max_len = f"({col.CHARACTER_MAXIMUM_LENGTH})" if col.CHARACTER_MAXIMUM_LENGTH else ""
                nullable = "NULL" if col.IS_NULLABLE == "YES" else "NOT NULL"
                default = f" DEFAULT {col.COLUMN_DEFAULT}" if col.COLUMN_DEFAULT else ""
                print(f"  {col_name:<30} {data_type}{max_len:<15} {nullable}{default}")
        
        # Get row counts
        print("\n" + "="*70)
        print("Row Counts:")
        print("="*70 + "\n")
        
        for row in tables:
            schema = row.TABLE_SCHEMA
            table = row.TABLE_NAME
            cursor.execute(f"SELECT COUNT(*) FROM [{schema}].[{table}]")
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
    parser.add_argument('--config', type=str, default='db_config.json',
                        help='Path to config file (default: db_config.json)')
    
    args = parser.parse_args()
    query_tables(args.env, args.config)
