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

def get_users(env_name="target", config_path="db_config.json"):
    """Query Users table from the database"""
    # Load configuration
    env = load_config(config_path, env_name)
    conn_str = build_connection_string(env)
    
    print(f"\nUsing environment: {env_name}")
    
    # Connect and query
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    print(f"\n{'='*80}")
    print(f"Users Table Content - Database: {env['database']}")
    print(f"{'='*80}\n")
    
    cursor.execute("SELECT * FROM Users")
    
    # Get column names
    columns = [column[0] for column in cursor.description]
    print(f"Columns: {', '.join(columns)}")
    print(f"{'-'*80}")
    
    # Fetch and display rows
    rows = cursor.fetchall()
    if rows:
        for i, row in enumerate(rows, 1):
            print(f"\nRow {i}:")
            for col, val in zip(columns, row):
                print(f"  {col}: {val}")
    else:
        print("\nNo records found in Users table.")
    
    print(f"\n{'-'*80}")
    print(f"Total records: {len(rows)}")
    print(f"{'='*80}\n")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Query Users table')
    parser.add_argument('--env', type=str, default='target',
                        choices=['source', 'target', 'local'],
                        help='Environment to use (default: target)')
    parser.add_argument('--config', type=str, default='db_config.json',
                        help='Path to config file (default: db_config.json)')
    
    args = parser.parse_args()
    get_users(args.env, args.config)
    get_users()
