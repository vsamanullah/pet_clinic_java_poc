"""
Create snapshot of PetClinic PostgreSQL database
Saves all data to a JSON file for backup and restoration
"""
import psycopg2
import json
import argparse
from datetime import datetime, date
from pathlib import Path

def load_config(config_path="../db_config.json", env_name="target"):
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

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def create_snapshot(env_name="target", config_path="../../db_config.json", output_file=None):
    """Create a complete snapshot of the database"""
    try:
        # Load configuration
        env_config = load_config(config_path, env_name)
        
        print(f"\n{'='*70}")
        print(f"Creating Database Snapshot")
        print(f"{'='*70}")
        print(f"Environment: {env_name}")
        print(f"Database: {env_config['database']}")
        print(f"Host: {env_config['host']}")
        print(f"{'='*70}\n")
        
        conn = get_connection(env_config)
        cursor = conn.cursor()
        
        snapshot = {
            'metadata': {
                'snapshot_date': datetime.now().isoformat(),
                'database': env_config['database'],
                'host': env_config['host'],
                'environment': env_name
            },
            'tables': {}
        }
        
        # Define table order for restoration (respecting foreign keys)
        table_order = ['types', 'specialties', 'owners', 'vets', 'vet_specialties', 'pets', 'visits']
        
        for table_name in table_order:
            print(f"Snapshotting table: {table_name}...")
            
            # Get column names
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'petclinic' AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = [row[0] for row in cursor.fetchall()]
            
            # Get all data
            cursor.execute(f'SELECT * FROM petclinic."{table_name}"')
            rows = cursor.fetchall()
            
            # Convert rows to list of dictionaries
            table_data = []
            for row in rows:
                row_dict = {}
                for i, col_name in enumerate(columns):
                    value = row[i]
                    # Convert to JSON-serializable format
                    if isinstance(value, (datetime, date)):
                        row_dict[col_name] = value.isoformat()
                    else:
                        row_dict[col_name] = value
                table_data.append(row_dict)
            
            snapshot['tables'][table_name] = {
                'columns': columns,
                'row_count': len(table_data),
                'data': table_data
            }
            
            print(f"  ✓ Captured {len(table_data)} rows from {table_name}")
        
        conn.close()
        
        # Generate output filename if not provided
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"../petclinic_snapshot_{env_name}_{timestamp}.json"
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False, default=json_serial)
        
        print(f"\n{'='*70}")
        print(f"Snapshot saved successfully!")
        print(f"{'='*70}")
        print(f"File: {output_file}")
        print(f"Size: {Path(output_file).stat().st_size:,} bytes")
        print(f"Total tables: {len(snapshot['tables'])}")
        print(f"Total rows: {sum(t['row_count'] for t in snapshot['tables'].values())}")
        print(f"{'='*70}\n")
        
        return output_file
        
    except Exception as e:
        print(f"Error creating snapshot: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create database snapshot')
    parser.add_argument('--env', type=str, default='target',
                        choices=['source', 'target', 'local'],
                        help='Environment to use (default: target)')
    parser.add_argument('--config', type=str, default='../db_config.json',
                        help='Path to config file (default: ../db_config.json)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output file name (default: auto-generated with timestamp)')
    
    args = parser.parse_args()
    create_snapshot(args.env, args.config, args.output)
