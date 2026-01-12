"""
PetClinic Database Migration Verifier

This script loads a baseline snapshot, captures current database state,
and performs comprehensive comparison to verify migration integrity.
"""

import psycopg2
import json
import hashlib
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional
import logging
import sys
import os
import argparse

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


class MigrationVerifier:
    """Verifies database migration integrity by comparing with baseline"""
    
    def __init__(self, env_name: str, baseline_file: str, config_path: str = "../../db_config.json"):
        self.env_name = env_name
        self.baseline_file = baseline_file
        self.config_path = config_path
        self.baseline = None
        self.current = None
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Load config
        config = load_config(config_path, env_name)
        self.env_config = config
        
        self.db_info = {
            'host': self.env_config['host'],
            'database': self.env_config['database'],
            'port': self.env_config['port']
        }
        
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "errors": []
        }
    
    def log_test(self, test_name: str, status: str, message: str = ""):
        """Log test result"""
        if status == 'passed':
            self.test_results["passed"] += 1
            logger.info(f"✓ {test_name}: PASSED - {message}")
        elif status == 'warning':
            self.test_results["warnings"] += 1
            logger.warning(f"⚠ {test_name}: WARNING - {message}")
        else:  # failed
            self.test_results["failed"] += 1
            error_msg = f"{test_name}: FAILED - {message}"
            self.test_results["errors"].append(error_msg)
            logger.error(f"✗ {error_msg}")
    
    def get_connection(self):
        """Get database connection"""
        try:
            return get_connection(self.env_config)
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def load_baseline(self):
        """Load baseline from JSON snapshot file"""
        try:
            with open(self.baseline_file, 'r') as f:
                self.baseline = json.load(f)
            logger.info(f"✓ Loaded baseline from: {self.baseline_file}")
            logger.info(f"  Baseline timestamp: {self.baseline['metadata']['snapshot_date']}")
            return True
        except FileNotFoundError:
            logger.error(f"✗ Baseline file not found: {self.baseline_file}")
            return False
        except json.JSONDecodeError:
            logger.error(f"✗ Invalid baseline file format: {self.baseline_file}")
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
            'schema_info': {}
        }
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get tables from baseline
            baseline_tables = list(self.baseline['tables'].keys())
            
            logger.info(f"Processing {len(baseline_tables)} tables...\n")
            
            for table_name in sorted(baseline_tables):
                logger.info(f"• Processing {table_name}...")
                
                try:
                    # Get row count
                    cursor.execute(f'SELECT COUNT(*) FROM petclinic."{table_name}"')
                    row_count = cursor.fetchone()[0]
                    self.current['row_counts'][table_name] = row_count
                    
                    # Get table data
                    table_data = self._get_table_data(conn, table_name)
                    self.current['tables'][table_name] = table_data
                    self.current['checksums'][table_name] = self._calculate_checksum(table_data)
                    
                    # Get schema
                    self.current['schema_info'][table_name] = self._get_table_schema(conn, table_name)
                    
                except Exception as e:
                    logger.warning(f"  Could not process {table_name}: {e}")
            
            logger.info("\n✓ Current state captured successfully")
            
        finally:
            conn.close()
    
    def _get_table_data(self, conn, table_name: str) -> List[Dict]:
        """Get all data from a table"""
        cursor = conn.cursor()
        
        # Get columns first
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'petclinic' AND table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        
        columns = [row[0] for row in cursor.fetchall()]
        
        # Get data
        cursor.execute(f'SELECT * FROM petclinic."{table_name}" ORDER BY 1')
        
        rows = []
        for row in cursor.fetchall():
            row_dict = {}
            for i, column in enumerate(columns):
                value = row[i]
                if value is not None:
                    # Convert date/datetime to string for JSON serialization
                    if isinstance(value, (datetime, date)):
                        row_dict[column] = value.isoformat()
                    else:
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
    
    def _get_table_schema(self, conn, table_name: str) -> List[Dict]:
        """Get schema information"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'petclinic' AND table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        
        return [{'name': r[0], 'type': r[1], 'max_length': r[2], 'nullable': r[3], 'default': r[4]} 
                for r in cursor.fetchall()]
    
    def compare_and_verify(self):
        """Compare baseline with current state and verify migration"""
        logger.info("\n" + "="*70)
        logger.info("MIGRATION VERIFICATION - COMPARING BASELINE VS CURRENT")
        logger.info("="*70)
        logger.info(f"Baseline:  {self.baseline['metadata']['snapshot_date']}")
        logger.info(f"Current:   {self.timestamp}")
        logger.info("="*70 + "\n")
        
        # Run all comparison tests
        self._verify_table_existence()
        self._verify_row_counts()
        self._verify_data_checksums()
        self._verify_schemas()
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
        
        common_tables = set(self.baseline['tables'].keys()) & set(self.current['tables'].keys())
        
        for table in sorted(common_tables):
            before = self.baseline['tables'][table]['row_count']
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
        
        common_tables = set(self.baseline['tables'].keys()) & set(self.current['tables'].keys())
        
        for table in sorted(common_tables):
            # Calculate baseline checksum from snapshot data
            baseline_data = self.baseline['tables'][table]['data']
            before_checksum = self._calculate_checksum(baseline_data)
            after_checksum = self.current['checksums'][table]
            
            if before_checksum == after_checksum:
                self.log_test(f"Checksum - {table}", 'passed', "Data unchanged")
            else:
                before_count = self.baseline['tables'][table]['row_count']
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
        
        common_tables = set(self.baseline['tables'].keys()) & set(self.current['tables'].keys())
        
        for table in sorted(common_tables):
            baseline_columns = self.baseline['tables'][table]['columns']
            current_schema = self.current['schema_info'][table]
            current_columns = [col['name'] for col in current_schema]
            
            if len(baseline_columns) != len(current_columns):
                self.log_test(f"Schema - {table}", 'warning', 
                            f"Column count: {len(baseline_columns)} → {len(current_columns)}")
            elif set(baseline_columns) != set(current_columns):
                self.log_test(f"Schema - {table}", 'warning', "Column names differ")
            else:
                self.log_test(f"Schema - {table}", 'passed', "Schema unchanged")
    
    def _verify_referential_integrity(self):
        """Verify referential integrity"""
        logger.info("\n" + "─" * 70)
        logger.info("REFERENTIAL INTEGRITY VERIFICATION")
        logger.info("─" * 70)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check foreign key constraints
        referential_checks = {
            'pets': [
                ('type_id', 'types', 'id', 'Pet must have valid type'),
                ('owner_id', 'owners', 'id', 'Pet must have valid owner')
            ],
            'visits': [
                ('pet_id', 'pets', 'id', 'Visit must reference valid pet')
            ],
            'vet_specialties': [
                ('vet_id', 'vets', 'id', 'Must reference valid vet'),
                ('specialty_id', 'specialties', 'id', 'Must reference valid specialty')
            ]
        }
        
        try:
            for table, checks in referential_checks.items():
                for fk_column, ref_table, ref_column, message in checks:
                    cursor.execute(f"""
                        SELECT COUNT(*)
                        FROM petclinic."{table}" t
                        LEFT JOIN petclinic."{ref_table}" r ON t."{fk_column}" = r."{ref_column}"
                        WHERE r."{ref_column}" IS NULL
                    """)
                    
                    orphans = cursor.fetchone()[0]
                    
                    if orphans == 0:
                        self.log_test(f"Referential Integrity - {table}.{fk_column}", 'passed', 
                                    f"No orphaned records")
                    else:
                        self.log_test(f"Referential Integrity - {table}.{fk_column}", 'failed', 
                                    f"{orphans} orphaned records found - {message}")
        
        finally:
            conn.close()
    
    def generate_report(self):
        """Generate final verification report"""
        logger.info("\n" + "="*70)
        logger.info("MIGRATION VERIFICATION SUMMARY")
        logger.info("="*70)
        logger.info(f"✓ Tests Passed:  {self.test_results['passed']}")
        logger.info(f"⚠ Warnings:      {self.test_results['warnings']}")
        logger.info(f"✗ Tests Failed:  {self.test_results['failed']}")
        logger.info("="*70)
        
        if self.test_results['failed'] > 0:
            logger.info("\nFAILED TESTS:")
            for error in self.test_results['errors']:
                logger.info(f"  • {error}")
            logger.info("\n" + "="*70)
            logger.info("⚠ MIGRATION VERIFICATION FAILED!")
            logger.info("="*70)
            return False
        elif self.test_results['warnings'] > 0:
            logger.info("\n" + "="*70)
            logger.info("⚠ MIGRATION VERIFIED WITH WARNINGS")
            logger.info("="*70)
            return True
        else:
            logger.info("\n" + "="*70)
            logger.info("✓ MIGRATION VERIFICATION PASSED!")
            logger.info("="*70)
            return True
    
    def run(self):
        """Execute the complete verification workflow"""
        logger.info("\n" + "="*70)
        logger.info("PETCLINIC DATABASE MIGRATION VERIFIER")
        logger.info("="*70)
        logger.info(f"Environment: {self.env_name}")
        logger.info(f"Database: {self.db_info['database']}")
        logger.info(f"Host: {self.db_info['host']}")
        logger.info(f"Baseline file: {self.baseline_file}")
        logger.info("="*70)
        
        # Load baseline
        if not self.load_baseline():
            logger.error("Cannot proceed without baseline")
            sys.exit(1)
        
        # Capture current state
        self.capture_current_state()
        
        # Compare and verify
        self.compare_and_verify()
        
        # Generate report
        success = self.generate_report()
        
        return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Verify PetClinic database migration integrity',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Verify using default snapshot
  python verify_migration.py

  # Verify using specific snapshot file
  python verify_migration.py --baseline ../petclinic_snapshot_source_20260110.json

  # Verify different environment
  python verify_migration.py --env local --baseline ../petclinic_snapshot_local.json
        """
    )
    
    parser.add_argument('--env', type=str, default='target',
                        choices=['source', 'target', 'local'],
                        help='Environment to use (default: target)')
    parser.add_argument('--config', type=str, default='../../db_config.json',
                        help='Path to config file (default: ../../db_config.json)')
    parser.add_argument('--baseline', type=str, default='../petclinic_snapshot_target_20260110_221752.json',
                        help='Baseline snapshot JSON file (default: ../petclinic_snapshot_target_20260110_221752.json)')
    
    args = parser.parse_args()
    
    verifier = MigrationVerifier(
        env_name=args.env,
        baseline_file=args.baseline,
        config_path=args.config
    )
    
    success = verifier.run()
    sys.exit(0 if success else 1)

