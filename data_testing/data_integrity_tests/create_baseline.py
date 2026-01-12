"""
BookService Database Baseline Creator (Part 1)

This script creates a baseline snapshot of the database state BEFORE migration.
The baseline is saved as a JSON file that can be used later for comparison.
"""

import psycopg2
import psycopg2.extras
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging
import sys
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'baseline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_config(config_path="../../db_config.json", env_name="target"):
    """Load database configuration from JSON file"""
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config['environments'][env_name]


def build_connection_params(env_config):
    """Build PostgreSQL connection parameters from environment config"""
    return {
        'host': env_config['host'],
        'port': env_config['port'],
        'database': env_config['database'],
        'user': env_config['username'],
        'password': env_config['password'],
        'sslmode': 'require'
    }


class DatabaseBaseline:
    """Creates and manages database baseline snapshots"""
    
    def __init__(self, connection_params: dict, env_name: str = "target"):
        self.connection_params = connection_params
        self.env_name = env_name
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Extract database connection details
        self.db_info = {
            'server': connection_params.get('host', 'Unknown'),
            'port': connection_params.get('port', 'Unknown'),
            'database': connection_params.get('database', 'Unknown'),
            'driver': 'PostgreSQL (psycopg2)',
            'auth_type': f"PostgreSQL Authentication (User: {connection_params.get('user', 'Unknown')})"
        }
        
        self.baseline_data = {
            'timestamp': self.timestamp,
            'database_info': self.db_info,
            'tables': {},
            'row_counts': {},
            'checksums': {},
            'foreign_keys': {},
            'indexes': {},
            'schema_info': {}
        }
    
    def get_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(**self.connection_params)
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            conn.close()
            logger.info(f"  Connected to database successfully")
            logger.info(f"  Database Version: {version[:100]}...")
            return True
        except Exception as e:
            logger.error(f" Database connection failed: {e}")
            return False
    
    def _get_user_tables(self, conn) -> List[Tuple[str, str]]:
        """Get list of user tables (excluding system tables)"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                table_schema,
                table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
                AND table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name
        """)
        return cursor.fetchall()
    
    def _get_row_count(self, conn, schema: str, table_name: str) -> int:
        """Get row count for a table"""
        cursor = conn.cursor()
        cursor.execute(f'SELECT COUNT(*) FROM "{schema}"."{table_name}"')
        return cursor.fetchone()[0]
    
    def _get_table_data(self, conn, schema: str, table_name: str) -> List[Dict]:
        """Get all data from a table"""
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM "{schema}"."{table_name}" ORDER BY 1')
        
        columns = [column[0] for column in cursor.description]
        rows = []
        
        for row in cursor.fetchall():
            row_dict = {}
            for i, column in enumerate(columns):
                value = row[i]
                # Convert to JSON-serializable format
                if value is not None:
                    row_dict[column] = str(value) if not isinstance(value, (int, float, str, bool)) else value
                else:
                    row_dict[column] = None
            rows.append(row_dict)
        
        return rows
    
    def _calculate_table_checksum(self, data: List[Dict]) -> str:
        """Calculate checksum for table data"""
        sorted_data = sorted([json.dumps(row, sort_keys=True) for row in data])
        data_string = ''.join(sorted_data)
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    def _get_table_schema(self, conn, schema: str, table_name: str) -> List[Dict]:
        """Get schema information for a table"""
        cursor = conn.cursor()
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
        """, (schema, table_name))
        
        columns = []
        for row in cursor.fetchall():
            columns.append({
                'name': row[0],
                'type': row[1],
                'max_length': row[2],
                'nullable': row[3],
                'default': row[4]
            })
        
        return columns
    
    def _get_foreign_keys(self, conn, schema: str, table_name: str) -> List[Dict]:
        """Get foreign key constraints for a table"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                tc.constraint_name,
                kcu.table_name AS parent_table,
                kcu.column_name AS parent_column,
                ccu.table_name AS referenced_table,
                ccu.column_name AS referenced_column
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = %s
                AND tc.table_name = %s
        """, (schema, table_name))
        
        fks = []
        for row in cursor.fetchall():
            fks.append({
                'name': row[0],
                'parent_table': row[1],
                'parent_column': row[2],
                'referenced_table': row[3],
                'referenced_column': row[4]
            })
        
        return fks
    
    def _get_indexes(self, conn, schema: str, table_name: str) -> List[Dict]:
        """Get indexes for a table"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = %s AND tablename = %s
            ORDER BY indexname
        """, (schema, table_name))
        
        indexes = []
        for row in cursor.fetchall():
            idx_name = row[0]
            idx_def = row[1]
            indexes.append({
                'name': idx_name,
                'definition': idx_def,
                'is_unique': 'UNIQUE' in idx_def.upper(),
                'is_primary_key': 'PRIMARY KEY' in idx_def.upper()
            })
        
        return indexes
    
    def create_baseline(self):
        """Create complete baseline snapshot of database"""
        logger.info("\n" + "="*70)
        logger.info("CREATING DATABASE BASELINE SNAPSHOT")
        logger.info("="*70)
        logger.info(f"Timestamp: {self.timestamp}")
        logger.info("="*70 + "\n")
        
        conn = self.get_connection()
        
        try:
            # Get list of user tables
            tables = self._get_user_tables(conn)
            logger.info(f"Found {len(tables)} user tables to baseline\n")
            
            for table in tables:
                schema = table[0]
                table_name = table[1]
                full_table = f"{schema}.{table_name}"
                
                logger.info(f" Processing {full_table}...")
                
                # Get row count
                row_count = self._get_row_count(conn, schema, table_name)
                self.baseline_data['row_counts'][full_table] = row_count
                logger.info(f"   Rows: {row_count}")
                
                # Get table data and create checksum
                table_data = self._get_table_data(conn, schema, table_name)
                self.baseline_data['tables'][full_table] = table_data
                
                checksum = self._calculate_table_checksum(table_data)
                self.baseline_data['checksums'][full_table] = checksum
                logger.info(f"   Checksum: {checksum[:16]}...")
                
                # Get schema information
                schema_info = self._get_table_schema(conn, schema, table_name)
                self.baseline_data['schema_info'][full_table] = schema_info
                logger.info(f"   Columns: {len(schema_info)}")
                
                # Get foreign keys
                foreign_keys = self._get_foreign_keys(conn, schema, table_name)
                self.baseline_data['foreign_keys'][full_table] = foreign_keys
                if foreign_keys:
                    logger.info(f"   Foreign Keys: {len(foreign_keys)}")
                
                # Get indexes
                indexes = self._get_indexes(conn, schema, table_name)
                self.baseline_data['indexes'][full_table] = indexes
                if indexes:
                    logger.info(f"   Indexes: {len(indexes)}")
                
                logger.info("")
            
            logger.info("="*70)
            logger.info(" Baseline snapshot created successfully")
            logger.info("="*70)
            
        finally:
            conn.close()
    
    def save_baseline(self, filename: Optional[str] = None) -> str:
        """Save baseline to JSON file"""
        if filename is None:
            filename = f"baseline_{self.env_name}_{self.timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.baseline_data, f, indent=2, default=str)
        
        logger.info(f"\n Baseline saved to: {filename}")
        return filename
    
    def print_summary(self):
        """Print summary of baseline"""
        logger.info("\n" + "="*70)
        logger.info("BASELINE SUMMARY")
        logger.info("="*70)
        
        # Database information
        logger.info("\nDatabase Information:")
        logger.info(f"  Server:         {self.db_info['server']}")
        logger.info(f"  Database:       {self.db_info['database']}")
        logger.info(f"  Driver:         {self.db_info['driver']}")
        logger.info(f"  Authentication: {self.db_info['auth_type']}")
        
        total_rows = sum(self.baseline_data['row_counts'].values())
        total_tables = len(self.baseline_data['tables'])
        
        logger.info(f"\nTotal Tables: {total_tables}")
        logger.info(f"Total Rows:   {total_rows}")
        logger.info("")
        
        logger.info("Table Details:")
        logger.info("-" * 70)
        for table, count in sorted(self.baseline_data['row_counts'].items()):
            logger.info(f"  {table:40} {count:>10} rows")
        
        logger.info("="*70)


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Create database baseline snapshot')
    parser.add_argument('--env', type=str, default='source',
                        choices=['source', 'target', 'local'],
                        help='Environment to use (default: source)')
    parser.add_argument('--config', type=str, default='../../db_config.json',
                        help='Path to config file (default: ../../db_config.json)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output filename for baseline (default: baseline_<env>_<timestamp>.json)')
    
    args = parser.parse_args()
    
    print("""
══════════════════════════════════════════════════════════════════════
          Database Baseline Creator - Part 1 
          Create a baseline snapshot BEFORE migration  
══════════════════════════════════════════════════════════════════════
    """)
    
    # Load configuration
    try:
        env_config = load_config(args.config, args.env)
        connection_params = build_connection_params(env_config)
    except Exception as e:
        print(f"\n✗ Error loading configuration: {e}")
        sys.exit(1)
    
    # Create baseline
    baseline = DatabaseBaseline(connection_params, args.env)
    
    # Print environment info
    print("="*70)
    print(f"Environment: {args.env.upper()}")
    print(f"Database: {env_config['database']}")
    print(f"Server: {env_config.get('host', 'N/A')}")
    print("="*70)
    
    # Test connection
    if not baseline.test_connection():
        print("\n✗ Cannot connect to database. Please check configuration.")
        sys.exit(1)
    
    # Info message
    print("\n" + "="*70)
    print("Creating baseline snapshot of current database state...")
    print("="*70)
    
    try:
        # Create baseline
        baseline.create_baseline()
        
        # Print summary
        baseline.print_summary()
        
        # Save baseline
        filename = baseline.save_baseline(args.output)
        
        print("\n" + "="*70)
        print("✓ BASELINE CREATED SUCCESSFULLY")
        print("="*70)
        print(f"\n✓ Baseline file: {filename}")
        print(f"✓ Environment: {args.env.upper()}")
        print("\n  Next Steps:")
        if args.env == 'source':
            print("    1. Run your database migration")
            print("    2. Create target baseline: python create_baseline.py --env target")
            print("    3. Compare: python verify_migration.py --source <source_baseline> --target <target_baseline>")
        else:
            print(f"    1. Use this baseline for verification")
            print(f"    2. Run: python verify_migration.py")
        print("="*70)
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"\n✗ Error creating baseline: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

