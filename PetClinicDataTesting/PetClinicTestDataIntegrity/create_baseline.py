"""
BookService Database Baseline Creator (Part 1)

This script creates a baseline snapshot of the database state BEFORE migration.
The baseline is saved as a JSON file that can be used later for comparison.
"""

import pyodbc
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging
import sys

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


class DatabaseBaseline:
    """Creates and manages database baseline snapshots"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Extract database connection details
        self.db_info = self._extract_db_info(connection_string)
        
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
    
    def _extract_db_info(self, connection_string: str) -> Dict:
        """Extract database connection information from connection string"""
        db_info = {
            'server': 'Unknown',
            'database': 'Unknown',
            'driver': 'Unknown',
            'auth_type': 'Unknown'
        }
        
        try:
            # Parse connection string
            parts = connection_string.split(';')
            for part in parts:
                if '=' in part:
                    key, value = part.split('=', 1)
                    key = key.strip().upper()
                    value = value.strip()
                    
                    if key == 'SERVER':
                        db_info['server'] = value
                    elif key == 'DATABASE':
                        db_info['database'] = value
                    elif key == 'DRIVER':
                        db_info['driver'] = value.strip('{}')
                    elif key == 'UID':
                        db_info['auth_type'] = f'SQL Authentication (User: {value})'
                    elif 'TRUSTED_CONNECTION' in key and value.lower() in ['yes', 'true']:
                        db_info['auth_type'] = 'Windows Authentication'
        except:
            pass
        
        return db_info
    
    def get_connection(self):
        """Get database connection"""
        try:
            return pyodbc.connect(self.connection_string)
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
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
                TABLE_SCHEMA,
                TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
                AND TABLE_SCHEMA NOT IN ('sys', 'INFORMATION_SCHEMA')
            ORDER BY TABLE_SCHEMA, TABLE_NAME
        """)
        return cursor.fetchall()
    
    def _get_row_count(self, conn, schema: str, table_name: str) -> int:
        """Get row count for a table"""
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM [{schema}].[{table_name}]")
        return cursor.fetchone()[0]
    
    def _get_table_data(self, conn, schema: str, table_name: str) -> List[Dict]:
        """Get all data from a table"""
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM [{schema}].[{table_name}] ORDER BY 1")
        
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
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE,
                COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
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
                fk.name AS FK_Name,
                tp.name AS Parent_Table,
                cp.name AS Parent_Column,
                tr.name AS Referenced_Table,
                cr.name AS Referenced_Column
            FROM sys.foreign_keys AS fk
            INNER JOIN sys.foreign_key_columns AS fkc 
                ON fk.object_id = fkc.constraint_object_id
            INNER JOIN sys.tables AS tp 
                ON fk.parent_object_id = tp.object_id
            INNER JOIN sys.columns AS cp 
                ON fkc.parent_object_id = cp.object_id 
                AND fkc.parent_column_id = cp.column_id
            INNER JOIN sys.tables AS tr 
                ON fk.referenced_object_id = tr.object_id
            INNER JOIN sys.columns AS cr 
                ON fkc.referenced_object_id = cr.object_id 
                AND fkc.referenced_column_id = cr.column_id
            INNER JOIN sys.schemas AS s 
                ON tp.schema_id = s.schema_id
            WHERE s.name = ? AND tp.name = ?
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
                i.name AS Index_Name,
                i.type_desc AS Index_Type,
                i.is_unique,
                i.is_primary_key,
                COL_NAME(ic.object_id, ic.column_id) AS Column_Name
            FROM sys.indexes AS i
            INNER JOIN sys.index_columns AS ic 
                ON i.object_id = ic.object_id 
                AND i.index_id = ic.index_id
            INNER JOIN sys.tables AS t 
                ON i.object_id = t.object_id
            INNER JOIN sys.schemas AS s 
                ON t.schema_id = s.schema_id
            WHERE s.name = ? AND t.name = ? AND i.name IS NOT NULL
            ORDER BY i.name, ic.key_ordinal
        """, (schema, table_name))
        
        indexes = {}
        for row in cursor.fetchall():
            idx_name = row[0]
            if idx_name not in indexes:
                indexes[idx_name] = {
                    'name': idx_name,
                    'type': row[1],
                    'is_unique': bool(row[2]),
                    'is_primary_key': bool(row[3]),
                    'columns': []
                }
            indexes[idx_name]['columns'].append(row[4])
        
        return list(indexes.values())
    
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
            filename = f"baseline_{self.timestamp}.json"
        
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
    """Main entry point"""
    print("""
          Database Baseline Creator - Part 1 
          Create a baseline snapshot BEFORE migration  
    """)
    
    # Database connection string - Try multiple driver options
    # Try to find best available driver (prefer newer ones)
    available_driver = None
    try:
        import pyodbc
        all_drivers = pyodbc.drivers()
        
        # Preferred driver order (newest first)
        preferred_drivers = [
            "ODBC Driver 17 for SQL Server",
            "ODBC Driver 13 for SQL Server",
            "SQL Server Native Client 11.0",
            "SQL Server"
        ]
        
        for driver in preferred_drivers:
            if driver in all_drivers:
                available_driver = driver
                print(f"Using ODBC driver: {available_driver}")
                break
                
        if not available_driver:
            available_driver = "SQL Server"
            print(f"Using default ODBC driver: {available_driver}")
    except Exception as e:
        available_driver = "SQL Server"
        print(f"Warning: Could not detect drivers, using default: {e}")
    
    # Remote SQL Server connection with SQL Authentication
    # Force use of ODBC Driver 18 for SQL Server (supports encryption parameters)
    driver_to_use = "ODBC Driver 18 for SQL Server" if "ODBC Driver 18 for SQL Server" in pyodbc.drivers() else available_driver
    
    connection_string = (
        f"DRIVER={{{driver_to_use}}};"
        "SERVER=10.134.77.68,1433;"  # Using IP address directly
        "DATABASE=BookStore-Master;"
        "UID=testuser;"
        "PWD=TestDb@26#!;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )
    
    # Allow custom connection string from command line
    if len(sys.argv) > 1:
        connection_string = sys.argv[1]
    
    # Create baseline
    baseline = DatabaseBaseline(connection_string)
    
    # Test connection
    if not baseline.test_connection():
        print("\n Cannot connect to database. Please check connection string.")
        print(f"   Connection: {connection_string}")
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
        filename = baseline.save_baseline()
        
        print("\n" + "="*70)
        print(" BASELINE CREATED SUCCESSFULLY")
        print("="*70)
        print(f"\n Baseline file: {filename}")
        print("\n Next Steps:")
        print("   1. Run your database migration")
        print("   2. Execute: python verify_migration.py")
        print(f"   3. Use baseline file: {filename}")
        print("="*70)
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"\n Error creating baseline: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
