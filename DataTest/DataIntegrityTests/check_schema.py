"""
Check database schema structure for PetClinic PostgreSQL database
"""
import psycopg2
import json
import argparse
from pathlib import Path

def load_config(config_path="../../db_config.json", env_name="target"):
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

def check_schema(env_name="target", config_path="../../db_config.json"):
    """Check database schema structure"""
    try:
        # Load configuration
        env_config = load_config(config_path, env_name)
        
        print(f"\n{'='*70}")
        print(f"Checking Schema - Environment: {env_name.upper()}")
        print(f"Database: {env_config['database']}")
        print(f"Host: {env_config.get('host', 'N/A')}")
        print(f"{'='*70}\n")
        
        conn = get_connection(env_config)
        cursor = conn.cursor()

        # PetClinic tables
        tables = ['owners', 'pets', 'vets', 'specialties', 'vet_specialties', 'types', 'visits']

        for table_name in tables:
            print(f"\n=== {table_name.upper()} Table Structure ===")
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, character_maximum_length, 
                       column_default, numeric_precision, numeric_scale
                FROM information_schema.columns
                WHERE table_schema = 'petclinic' AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            rows = cursor.fetchall()
            if rows:
                print(f"  {'Column Name':<25} {'Data Type':<20} {'Nullable':<10} {'Details'}")
                print(f"  {'-'*25} {'-'*20} {'-'*10} {'-'*30}")
                for row in rows:
                    col_name = row[0]
                    data_type = row[1]
                    nullable = row[2]
                    max_len = row[3]
                    default = row[4]
                    precision = row[5]
                    scale = row[6]
                    
                    # Build data type string with details
                    if max_len:
                        data_type_str = f"{data_type}({max_len})"
                    elif precision:
                        data_type_str = f"{data_type}({precision},{scale})" if scale else f"{data_type}({precision})"
                    else:
                        data_type_str = data_type
                    
                    details = ""
                    if default:
                        # Simplify default display
                        if "nextval" in str(default):
                            details = "AUTO INCREMENT"
                        else:
                            details = f"DEFAULT {default}"
                    
                    print(f"  {col_name:<25} {data_type_str:<20} {nullable:<10} {details}")
            else:
                print(f"  ⚠ Table '{table_name}' not found or has no columns")
            
            # Get constraints
            cursor.execute("""
                SELECT
                    tc.constraint_name,
                    tc.constraint_type,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                LEFT JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                LEFT JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.table_schema = 'petclinic' 
                    AND tc.table_name = %s
                ORDER BY tc.constraint_type, tc.constraint_name
            """, (table_name,))
            
            constraints = cursor.fetchall()
            if constraints:
                print(f"\n  Constraints:")
                for constraint in constraints:
                    constraint_name = constraint[0]
                    constraint_type = constraint[1]
                    column_name = constraint[2]
                    foreign_table = constraint[3]
                    foreign_column = constraint[4]
                    
                    if constraint_type == 'PRIMARY KEY':
                        print(f"    • PRIMARY KEY: {column_name}")
                    elif constraint_type == 'FOREIGN KEY':
                        print(f"    • FOREIGN KEY: {column_name} → {foreign_table}({foreign_column})")
                    elif constraint_type == 'UNIQUE':
                        print(f"    • UNIQUE: {column_name}")

        conn.close()
        
        print(f"\n{'='*70}")
        print("Schema check completed successfully")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check database schema structure')
    parser.add_argument('--env', type=str, default='target',
                        choices=['source', 'target', 'local'],
                        help='Environment to use (default: target)')
    parser.add_argument('--config', type=str, default='../../db_config.json',
                        help='Path to config file (default: ../../db_config.json)')
    
    args = parser.parse_args()
    check_schema(args.env, args.config)

