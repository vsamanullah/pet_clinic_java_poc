"""
BookService Database Migration Verifier (Part 2)

This script loads a baseline snapshot, captures current database state,
and performs comprehensive comparison to verify migration integrity.
"""

import pyodbc
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'verification_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MigrationVerifier:
    """Verifies database migration integrity by comparing with baseline"""
    
    def __init__(self, connection_string: str, baseline_file: str):
        self.connection_string = connection_string
        self.baseline_file = baseline_file
        self.baseline = None
        self.current = None
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Extract database connection details
        self.db_info = self._extract_db_info(connection_string)
        
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "errors": []
        }
    
    def _extract_db_info(self, connection_string: str) -> dict:
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
    
    def log_test(self, test_name: str, status: str, message: str = ""):
        """Log test result"""
        if status == 'passed':
            self.test_results["passed"] += 1
            logger.info(f" {test_name}: PASSED - {message}")
        elif status == 'warning':
            self.test_results["warnings"] += 1
            logger.warning(f" {test_name}: WARNING - {message}")
        else:  # failed
            self.test_results["failed"] += 1
            error_msg = f"{test_name}: FAILED - {message}"
            self.test_results["errors"].append(error_msg)
            logger.error(f" {error_msg}")
    
    def get_connection(self):
        """Get database connection"""
        try:
            return pyodbc.connect(self.connection_string)
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def load_baseline(self):
        """Load baseline from JSON file"""
        try:
            with open(self.baseline_file, 'r') as f:
                self.baseline = json.load(f)
            logger.info(f" Loaded baseline from: {self.baseline_file}")
            logger.info(f"  Baseline timestamp: {self.baseline['timestamp']}")
            return True
        except FileNotFoundError:
            logger.error(f" Baseline file not found: {self.baseline_file}")
            return False
        except json.JSONDecodeError:
            logger.error(f" Invalid baseline file format: {self.baseline_file}")
            return False
    
    def capture_current_state(self):
        """Capture current database state"""
        logger.info("\n" + "="*70)
        logger.info("CAPTURING CURRENT DATABASE STATE")
        logger.info("="*70)
        
        self.current = {
            'timestamp': self.timestamp,
            'tables': {},
            'row_counts': {},
            'checksums': {},
            'foreign_keys': {},
            'indexes': {},
            'schema_info': {}
        }
        
        conn = self.get_connection()
        
        try:
            # Get same tables as baseline
            baseline_tables = list(self.baseline['tables'].keys())
            
            # Also get current tables to detect new ones
            current_tables = self._get_user_tables(conn)
            current_table_names = [f"{t[0]}.{t[1]}" for t in current_tables]
            
            # Combine both sets
            all_tables = set(baseline_tables + current_table_names)
            
            logger.info(f"Processing {len(all_tables)} tables...\n")
            
            for full_table in sorted(all_tables):
                if '.' in full_table:
                    schema, table_name = full_table.split('.')
                else:
                    continue
                
                logger.info(f" Processing {full_table}...")
                
                try:
                    # Get row count
                    row_count = self._get_row_count(conn, schema, table_name)
                    self.current['row_counts'][full_table] = row_count
                    
                    # Get table data and checksum
                    table_data = self._get_table_data(conn, schema, table_name)
                    self.current['tables'][full_table] = table_data
                    self.current['checksums'][full_table] = self._calculate_checksum(table_data)
                    
                    # Get schema
                    self.current['schema_info'][full_table] = self._get_table_schema(conn, schema, table_name)
                    
                    # Get foreign keys
                    self.current['foreign_keys'][full_table] = self._get_foreign_keys(conn, schema, table_name)
                    
                    # Get indexes
                    self.current['indexes'][full_table] = self._get_indexes(conn, schema, table_name)
                    
                except Exception as e:
                    logger.warning(f"   Could not process {full_table}: {e}")
            
            logger.info("\n Current state captured successfully")
            
        finally:
            conn.close()
    
    def _get_user_tables(self, conn) -> List[Tuple[str, str]]:
        """Get list of user tables"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TABLE_SCHEMA, TABLE_NAME
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
                if value is not None:
                    row_dict[column] = str(value) if not isinstance(value, (int, float, str, bool)) else value
                else:
                    row_dict[column] = None
            rows.append(row_dict)
        
        return rows
    
    def _calculate_checksum(self, data: List[Dict]) -> str:
        """Calculate checksum for table data"""
        sorted_data = sorted([json.dumps(row, sort_keys=True) for row in data])
        data_string = ''.join(sorted_data)
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    def _get_table_schema(self, conn, schema: str, table_name: str) -> List[Dict]:
        """Get schema information"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE, COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
        """, (schema, table_name))
        
        return [{'name': r[0], 'type': r[1], 'max_length': r[2], 'nullable': r[3], 'default': r[4]} 
                for r in cursor.fetchall()]
    
    def _get_foreign_keys(self, conn, schema: str, table_name: str) -> List[Dict]:
        """Get foreign keys"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT fk.name, tp.name, cp.name, tr.name, cr.name
            FROM sys.foreign_keys AS fk
            INNER JOIN sys.foreign_key_columns AS fkc ON fk.object_id = fkc.constraint_object_id
            INNER JOIN sys.tables AS tp ON fk.parent_object_id = tp.object_id
            INNER JOIN sys.columns AS cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
            INNER JOIN sys.tables AS tr ON fk.referenced_object_id = tr.object_id
            INNER JOIN sys.columns AS cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
            INNER JOIN sys.schemas AS s ON tp.schema_id = s.schema_id
            WHERE s.name = ? AND tp.name = ?
        """, (schema, table_name))
        
        return [{'name': r[0], 'parent_table': r[1], 'parent_column': r[2], 
                'referenced_table': r[3], 'referenced_column': r[4]} for r in cursor.fetchall()]
    
    def _get_indexes(self, conn, schema: str, table_name: str) -> List[Dict]:
        """Get indexes"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.name, i.type_desc, i.is_unique, i.is_primary_key, COL_NAME(ic.object_id, ic.column_id)
            FROM sys.indexes AS i
            INNER JOIN sys.index_columns AS ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            INNER JOIN sys.tables AS t ON i.object_id = t.object_id
            INNER JOIN sys.schemas AS s ON t.schema_id = s.schema_id
            WHERE s.name = ? AND t.name = ? AND i.name IS NOT NULL
            ORDER BY i.name, ic.key_ordinal
        """, (schema, table_name))
        
        indexes = {}
        for row in cursor.fetchall():
            idx_name = row[0]
            if idx_name not in indexes:
                indexes[idx_name] = {
                    'name': idx_name, 'type': row[1], 'is_unique': bool(row[2]),
                    'is_primary_key': bool(row[3]), 'columns': []
                }
            indexes[idx_name]['columns'].append(row[4])
        
        return list(indexes.values())
    
    def compare_and_verify(self):
        """Compare baseline with current state and verify migration"""
        logger.info("\n" + "="*70)
        logger.info("MIGRATION VERIFICATION - COMPARING BASELINE VS CURRENT")
        logger.info("="*70)
        logger.info(f"Baseline:  {self.baseline['timestamp']}")
        logger.info(f"Current:   {self.current['timestamp']}")
        logger.info("="*70 + "\n")
        
        # Run all comparison tests
        self._verify_table_existence()
        self._verify_row_counts()
        self._verify_data_checksums()
        self._verify_schemas()
        self._verify_foreign_keys()
        self._verify_indexes()
        self._verify_referential_integrity()
    
    def _verify_table_existence(self):
        """Verify table existence"""
        logger.info("─" * 70)
        logger.info("TABLE EXISTENCE VERIFICATION")
        logger.info("─" * 70)
        
        baseline_tables = set(self.baseline['tables'].keys())
        current_tables = set(self.current['tables'].keys())
        
        added = current_tables - baseline_tables
        removed = baseline_tables - current_tables
        
        if removed:
            for table in removed:
                self.log_test(f"Table Existence - {table}", 'failed', "TABLE REMOVED!")
        
        if added:
            for table in added:
                self.log_test(f"Table Existence - {table}", 'warning', "New table added")
        
        if not added and not removed:
            self.log_test("Table Existence", 'passed', "All tables preserved")
    
    def _verify_row_counts(self):
        """Verify row counts"""
        logger.info("\n" + "─" * 70)
        logger.info("ROW COUNT VERIFICATION")
        logger.info("─" * 70)
        
        common_tables = set(self.baseline['row_counts'].keys()) & set(self.current['row_counts'].keys())
        
        for table in sorted(common_tables):
            before = self.baseline['row_counts'][table]
            after = self.current['row_counts'][table]
            diff = after - before
            
            if diff == 0:
                self.log_test(f"Row Count - {table}", 'passed', f"{before} rows (unchanged)")
            elif diff < 0:
                self.log_test(f"Row Count - {table}", 'failed', 
                            f"{before} → {after} ({diff} rows - DATA LOSS!)")
            else:
                self.log_test(f"Row Count - {table}", 'warning', 
                            f"{before} → {after} (+{diff} rows)")
    
    def _verify_data_checksums(self):
        """Verify data integrity using checksums"""
        logger.info("\n" + "─" * 70)
        logger.info("DATA INTEGRITY CHECKSUMS")
        logger.info("─" * 70)
        
        common_tables = set(self.baseline['checksums'].keys()) & set(self.current['checksums'].keys())
        
        for table in sorted(common_tables):
            before_checksum = self.baseline['checksums'][table]
            after_checksum = self.current['checksums'][table]
            
            if before_checksum == after_checksum:
                self.log_test(f"Checksum - {table}", 'passed', "Data unchanged")
            else:
                before_count = self.baseline['row_counts'][table]
                after_count = self.current['row_counts'][table]
                
                if before_count != after_count:
                    self.log_test(f"Checksum - {table}", 'warning', 
                                "Data modified (row count changed)")
                else:
                    self.log_test(f"Checksum - {table}", 'warning', 
                                "Data modified (same count, different values)")
    
    def _verify_schemas(self):
        """Verify table schemas"""
        logger.info("\n" + "─" * 70)
        logger.info("SCHEMA VERIFICATION")
        logger.info("─" * 70)
        
        common_tables = set(self.baseline['schema_info'].keys()) & set(self.current['schema_info'].keys())
        
        for table in sorted(common_tables):
            before_schema = self.baseline['schema_info'][table]
            after_schema = self.current['schema_info'][table]
            
            if len(before_schema) != len(after_schema):
                self.log_test(f"Schema - {table}", 'warning', 
                            f"Column count: {len(before_schema)} → {len(after_schema)}")
            elif before_schema != after_schema:
                self.log_test(f"Schema - {table}", 'warning', "Schema modified")
            else:
                self.log_test(f"Schema - {table}", 'passed', "Schema unchanged")
    
    def _verify_foreign_keys(self):
        """Verify foreign keys"""
        logger.info("\n" + "─" * 70)
        logger.info("FOREIGN KEY VERIFICATION")
        logger.info("─" * 70)
        
        common_tables = set(self.baseline['foreign_keys'].keys()) & set(self.current['foreign_keys'].keys())
        
        for table in sorted(common_tables):
            before_fks = {fk['name']: fk for fk in self.baseline['foreign_keys'][table]}
            after_fks = {fk['name']: fk for fk in self.current['foreign_keys'][table]}
            
            added = set(after_fks.keys()) - set(before_fks.keys())
            removed = set(before_fks.keys()) - set(after_fks.keys())
            
            if removed:
                self.log_test(f"Foreign Keys - {table}", 'warning', 
                            f"{len(removed)} FK(s) removed")
            elif added:
                self.log_test(f"Foreign Keys - {table}", 'warning', 
                            f"{len(added)} FK(s) added")
            elif len(before_fks) > 0:
                self.log_test(f"Foreign Keys - {table}", 'passed', 
                            f"{len(before_fks)} FK(s) unchanged")
    
    def _verify_indexes(self):
        """Verify indexes"""
        logger.info("\n" + "─" * 70)
        logger.info("INDEX VERIFICATION")
        logger.info("─" * 70)
        
        common_tables = set(self.baseline['indexes'].keys()) & set(self.current['indexes'].keys())
        
        for table in sorted(common_tables):
            before_idx = {idx['name']: idx for idx in self.baseline['indexes'][table]}
            after_idx = {idx['name']: idx for idx in self.current['indexes'][table]}
            
            added = set(after_idx.keys()) - set(before_idx.keys())
            removed = set(before_idx.keys()) - set(after_idx.keys())
            
            if removed:
                self.log_test(f"Indexes - {table}", 'warning', f"{len(removed)} index(es) removed")
            elif added:
                self.log_test(f"Indexes - {table}", 'warning', f"{len(added)} index(es) added")
            elif len(before_idx) > 0:
                self.log_test(f"Indexes - {table}", 'passed', f"{len(before_idx)} index(es) unchanged")
    
    def _verify_referential_integrity(self):
        """Verify referential integrity"""
        logger.info("\n" + "─" * 70)
        logger.info("REFERENTIAL INTEGRITY VERIFICATION")
        logger.info("─" * 70)
        
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    OBJECT_SCHEMA_NAME(fk.parent_object_id) AS Parent_Schema,
                    OBJECT_NAME(fk.parent_object_id) AS Parent_Table,
                    COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS Parent_Column,
                    OBJECT_SCHEMA_NAME(fk.referenced_object_id) AS Referenced_Schema,
                    OBJECT_NAME(fk.referenced_object_id) AS Referenced_Table,
                    COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS Referenced_Column
                FROM sys.foreign_keys AS fk
                INNER JOIN sys.foreign_key_columns AS fkc ON fk.object_id = fkc.constraint_object_id
            """)
            
            for fk in cursor.fetchall():
                parent_schema, parent_table, parent_col = fk[0], fk[1], fk[2]
                ref_schema, ref_table, ref_col = fk[3], fk[4], fk[5]
                
                # Check for orphaned records
                check_query = f"""
                    SELECT COUNT(*) 
                    FROM [{parent_schema}].[{parent_table}] p
                    LEFT JOIN [{ref_schema}].[{ref_table}] r ON p.[{parent_col}] = r.[{ref_col}]
                    WHERE p.[{parent_col}] IS NOT NULL AND r.[{ref_col}] IS NULL
                """
                
                cursor.execute(check_query)
                orphaned = cursor.fetchone()[0]
                
                test_name = f"FK Integrity - {parent_schema}.{parent_table}.{parent_col}"
                
                if orphaned == 0:
                    self.log_test(test_name, 'passed', "No orphaned records")
                else:
                    self.log_test(test_name, 'failed', f"{orphaned} ORPHANED RECORDS!")
        
        finally:
            conn.close()
    
    def generate_report(self):
        """Generate final verification report"""
        logger.info("\n" + "="*70)
        logger.info("MIGRATION VERIFICATION REPORT")
        logger.info("="*70)
        
        # Database information
        logger.info("\nDatabase Information:")
        logger.info(f"  Server:         {self.db_info['server']}")
        logger.info(f"  Database:       {self.db_info['database']}")
        logger.info(f"  Driver:         {self.db_info['driver']}")
        logger.info(f"  Authentication: {self.db_info['auth_type']}")
        
        # Check if baseline has database_info (for new baselines)
        if 'database_info' in self.baseline:
            logger.info("\nBaseline Database Information:")
            logger.info(f"  Server:         {self.baseline['database_info']['server']}")
            logger.info(f"  Database:       {self.baseline['database_info']['database']}")
        
        total = self.test_results['passed'] + self.test_results['failed'] + self.test_results['warnings']
        
        logger.info(f"\nBaseline:     {self.baseline['timestamp']}")
        logger.info(f"Verified:     {self.current['timestamp']}")
        logger.info(f"\nTotal Tests:  {total}")
        logger.info(f" Passed:     {self.test_results['passed']}")
        logger.info(f" Warnings:   {self.test_results['warnings']}")
        logger.info(f" Failed:     {self.test_results['failed']}")
        
        if self.test_results['failed'] > 0:
            logger.info("\n" + "─" * 70)
            logger.info("CRITICAL FAILURES:")
            logger.info("─" * 70)
            for error in self.test_results['errors']:
                logger.error(f"   {error}")
        
        logger.info("="*70)
        
        if total > 0:
            success_rate = ((self.test_results['passed'] + self.test_results['warnings']) / total) * 100
            logger.info(f"\n Success Rate: {success_rate:.1f}%")
        
        return self.test_results


def main():
    """Main entry point"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║   Database Migration Verifier - Part 2                          ║
║   Verify migration against baseline                             ║
╚══════════════════════════════════════════════════════════════════╝
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
    
    # Get baseline file
    baseline_file = None
    if len(sys.argv) > 1:
        baseline_file = sys.argv[1]
    else:
        # Find most recent baseline file
        baseline_files = [f for f in os.listdir('.') if f.startswith('baseline_') and f.endswith('.json')]
        if baseline_files:
            baseline_file = sorted(baseline_files)[-1]
            print(f"Using baseline file: {baseline_file}")
        else:
            print(f"\n❌ No baseline files found in current directory")
            print("\n📋 Please create a baseline first using: python create_baseline.py")
            sys.exit(1)
    
    if not os.path.exists(baseline_file):
        print(f"\n❌ Baseline file not found: {baseline_file}")
        print("\n📋 Please create a baseline first using: python create_baseline.py")
        sys.exit(1)
    
    # Create verifier
    verifier = MigrationVerifier(connection_string, baseline_file)
    
    # Load baseline
    if not verifier.load_baseline():
        print("\n❌ Failed to load baseline file")
        sys.exit(1)
    
    # Capture current state
    print("\n" + "="*70)
    print("Capturing current database state for comparison...")
    print("="*70)
    
    try:
        verifier.capture_current_state()
        
        # Compare and verify
        verifier.compare_and_verify()
        
        # Generate report
        results = verifier.generate_report()
        
        # Final result
        if results['failed'] == 0:
            print("\n" + "="*70)
            print("✅ MIGRATION VERIFICATION PASSED")
            print("="*70)
            print("No critical issues found. Migration integrity verified!")
            if results['warnings'] > 0:
                print(f"⚠  Note: {results['warnings']} warnings detected (see log for details)")
            sys.exit(0)
        else:
            print("\n" + "="*70)
            print("❌ MIGRATION VERIFICATION FAILED")
            print("="*70)
            print(f"Found {results['failed']} critical issue(s).")
            print("Check the log file for detailed information.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
