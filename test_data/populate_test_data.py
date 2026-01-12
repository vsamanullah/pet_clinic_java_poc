"""
PetClinic Database Test Data Populator

This script:
1. Clears all existing records from the database
2. Loads baseline data from snapshot JSON file
3. Creates additional test records (N specified via command line)
"""

import psycopg2
import sys
from datetime import datetime, timedelta, date
import logging
import random
import argparse
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'populate_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Loaded configuration from: {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {e}")
        sys.exit(1)


def get_connection(env_config: dict):
    """Create PostgreSQL connection from environment config"""
    return psycopg2.connect(
        host=env_config['host'],
        port=env_config['port'],
        database=env_config['database'],
        user=env_config['username'],
        password=env_config['password']
    )


class PetClinicDataPopulator:
    """Manages test data population for PetClinic database"""
    
    def __init__(self, env_name: str, config_path: str, snapshot_file: str, additional_records: int):
        self.env_name = env_name
        self.config_path = config_path
        self.snapshot_file = snapshot_file
        self.additional_records = additional_records
        self.timestamp = datetime.now()
        
        # Load config
        config = load_config(config_path)
        if env_name not in config['environments']:
            logger.error(f"Environment '{env_name}' not found in configuration")
            sys.exit(1)
        
        self.env_config = config['environments'][env_name]
        logger.info(f"Using environment: {env_name}")
        
    def get_connection(self):
        """Get database connection"""
        try:
            return get_connection(self.env_config)
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
            logger.info(f"✓ Connected to database successfully")
            logger.info(f"  Database Version: {version[:100]}...")
            return True
        except Exception as e:
            logger.error(f"✗ Database connection failed: {e}")
            return False
    
    def clear_database(self):
        """Clear all records from all tables"""
        logger.info("\n" + "="*70)
        logger.info("CLEARING ALL RECORDS FROM DATABASE")
        logger.info("="*70)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Order: delete child tables first to respect foreign keys
            tables_order = ['visits', 'pets', 'vet_specialties', 'vets', 'owners', 'specialties', 'types']
            
            logger.info(f"Found {len(tables_order)} tables to clear\n")
            
            for table_name in tables_order:
                try:
                    # Get current row count
                    cursor.execute(f'SELECT COUNT(*) FROM petclinic."{table_name}"')
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        # Delete all records
                        cursor.execute(f'DELETE FROM petclinic."{table_name}"')
                        conn.commit()
                        logger.info(f"  ✓ Deleted {count:>5} rows from {table_name}")
                    else:
                        logger.info(f"  • Skipped {table_name} (already empty)")
                        
                except Exception as e:
                    logger.warning(f"  ✗ Could not delete from {table_name}: {e}")
                    conn.rollback()
            
            logger.info("="*70)
            logger.info("✓ All records cleared successfully")
            logger.info("="*70)
            
        except Exception as e:
            logger.error(f"Error during deletion: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def load_snapshot_data(self):
        """Load data from snapshot JSON file"""
        logger.info("\n" + "="*70)
        logger.info("LOADING BASELINE DATA FROM SNAPSHOT")
        logger.info("="*70)
        
        # Load snapshot file
        try:
            with open(self.snapshot_file, 'r', encoding='utf-8') as f:
                snapshot = json.load(f)
            logger.info(f"Loaded snapshot from: {self.snapshot_file}")
            logger.info(f"Snapshot date: {snapshot['metadata']['snapshot_date']}")
        except FileNotFoundError:
            logger.error(f"Snapshot file not found: {self.snapshot_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in snapshot file: {e}")
            sys.exit(1)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Load tables in order (respecting foreign keys)
            table_order = ['types', 'specialties', 'owners', 'vets', 'vet_specialties', 'pets', 'visits']
            
            for table_name in table_order:
                if table_name not in snapshot['tables']:
                    logger.warning(f"  ⚠ Table {table_name} not found in snapshot")
                    continue
                
                table_data = snapshot['tables'][table_name]
                rows = table_data['data']
                
                if not rows:
                    logger.info(f"  • Skipped {table_name} (no data in snapshot)")
                    continue
                
                columns = table_data['columns']
                placeholders = ', '.join(['%s'] * len(columns))
                columns_str = ', '.join([f'"{col}"' for col in columns])
                
                insert_query = f'INSERT INTO petclinic."{table_name}" ({columns_str}) VALUES ({placeholders})'
                
                for row in rows:
                    values = [row[col] for col in columns]
                    cursor.execute(insert_query, values)
                
                conn.commit()
                logger.info(f"  ✓ Loaded {len(rows):>5} rows into {table_name}")
            
            # Reset sequences to match the loaded data
            logger.info("\n• Resetting sequence counters...")
            sequences = {
                'owners_id_seq': 'owners',
                'pets_id_seq': 'pets',
                'vets_id_seq': 'vets',
                'specialties_id_seq': 'specialties',
                'types_id_seq': 'types',
                'visits_id_seq': 'visits'
            }
            
            for seq_name, table_name in sequences.items():
                try:
                    cursor.execute(f"""
                        SELECT setval('petclinic.{seq_name}', 
                                     (SELECT COALESCE(MAX(id), 0) FROM petclinic."{table_name}"), 
                                     true)
                    """)
                    logger.info(f"    ✓ Reset {seq_name}")
                except Exception as e:
                    logger.warning(f"    Could not reset {seq_name}: {e}")
            
            conn.commit()
            
            logger.info("="*70)
            logger.info("✓ Baseline data loaded successfully")
            logger.info("="*70)
            
        except Exception as e:
            logger.error(f"Error loading snapshot data: {e}")
            import traceback
            traceback.print_exc()
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def create_additional_records(self):
        """Create additional test records"""
        if self.additional_records == 0:
            logger.info("\n• No additional records requested")
            return
        
        logger.info("\n" + "="*70)
        logger.info(f"CREATING {self.additional_records} ADDITIONAL RECORDS")
        logger.info("="*70)
        
        conn = self.get_connection()
        
        try:
            # Get current max IDs
            cursor = conn.cursor()
            cursor.execute('SELECT MAX(id) FROM petclinic.owners')
            max_owner_id = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT MAX(id) FROM petclinic.types')
            max_type_id = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT MAX(id) FROM petclinic.pets')
            max_pet_id = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT MAX(id) FROM petclinic.vets')
            max_vet_id = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT MAX(id) FROM petclinic.specialties')
            max_specialty_id = cursor.fetchone()[0] or 0
            
            # Get existing type IDs for pet creation
            cursor.execute('SELECT id FROM petclinic.types')
            type_ids = [row[0] for row in cursor.fetchall()]
            
            if not type_ids:
                logger.error("No pet types found in database. Cannot create pets.")
                return
            
            # Create additional owners
            owner_ids = self.populate_owners(conn, self.additional_records, max_owner_id)
            
            # Create additional pets (1-3 pets per owner)
            self.populate_pets(conn, owner_ids, type_ids, max_pet_id)
            
            # Create additional vets
            vet_ids = self.populate_vets(conn, max(3, self.additional_records // 3), max_vet_id)
            
            # Create additional visits
            cursor.execute('SELECT id FROM petclinic.pets WHERE id > %s', (max_pet_id,))
            new_pet_ids = [row[0] for row in cursor.fetchall()]
            if new_pet_ids:
                self.populate_visits(conn, new_pet_ids)
            
            logger.info("="*70)
            logger.info("✓ Additional records created successfully")
            logger.info("="*70)
            
        except Exception as e:
            logger.error(f"Error creating additional records: {e}")
            import traceback
            traceback.print_exc()
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def populate_owners(self, conn, count: int, start_id: int):
        """Populate owners table with test data"""
        cursor = conn.cursor()
        
        logger.info(f"\n• Populating owners table with {count} records...")
        
        first_names = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emma', 'Robert', 'Lisa', 
                      'William', 'Mary', 'James', 'Patricia', 'Charles', 'Jennifer', 'Daniel',
                      'Christopher', 'Jessica', 'Matthew', 'Ashley', 'Andrew', 'Amanda', 'Joseph']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 
                     'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Wilson', 'Anderson',
                     'Taylor', 'Thomas', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson']
        cities = ['Madison', 'Sun Prairie', 'McFarland', 'Windsor', 'Monona', 'Waunakee', 
                 'Middleton', 'Verona', 'Fitchburg', 'Stoughton']
        
        owner_ids = []
        
        for i in range(count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            address = f"{random.randint(100, 9999)} {random.choice(['Oak', 'Maple', 'Pine', 'Cedar', 'Elm'])} {random.choice(['St.', 'Ave.', 'Blvd.', 'Rd.', 'Lane'])}"
            city = random.choice(cities)
            telephone = f"608555{random.randint(1000, 9999)}"
            
            try:
                cursor.execute("""
                    INSERT INTO petclinic.owners (first_name, last_name, address, city, telephone)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (first_name, last_name, address, city, telephone))
                
                owner_id = cursor.fetchone()[0]
                owner_ids.append(owner_id)
                
                if (i + 1) % 10 == 0 or i == count - 1:
                    logger.info(f"    Created {i + 1}/{count} owners...")
                    
            except Exception as e:
                logger.error(f"    Error creating owner {i+1}: {e}")
                raise
        
        conn.commit()
        logger.info(f"  ✓ Created {len(owner_ids)} owners successfully")
        
        return owner_ids
    
    def populate_pets(self, conn, owner_ids: list, type_ids: list, start_id: int):
        """Populate pets table with test data"""
        cursor = conn.cursor()
        
        # Create 1-3 pets per owner
        total_pets = 0
        pet_names = ['Max', 'Bella', 'Charlie', 'Lucy', 'Cooper', 'Luna', 'Buddy', 'Daisy',
                    'Rocky', 'Molly', 'Duke', 'Sadie', 'Zeus', 'Maggie', 'Oliver', 'Sophie',
                    'Leo', 'Chloe', 'Milo', 'Zoe', 'Teddy', 'Lily', 'Bear', 'Stella']
        
        logger.info(f"\n• Populating pets table...")
        
        for owner_id in owner_ids:
            num_pets = random.randint(1, 3)
            
            for _ in range(num_pets):
                name = random.choice(pet_names)
                birth_date = date.today() - timedelta(days=random.randint(365, 5475))  # 1-15 years old
                type_id = random.choice(type_ids)
                
                try:
                    cursor.execute("""
                        INSERT INTO petclinic.pets (name, birth_date, type_id, owner_id)
                        VALUES (%s, %s, %s, %s)
                    """, (name, birth_date, type_id, owner_id))
                    
                    total_pets += 1
                    
                except Exception as e:
                    logger.error(f"    Error creating pet: {e}")
                    raise
        
        conn.commit()
        logger.info(f"  ✓ Created {total_pets} pets successfully")
    
    def populate_vets(self, conn, count: int, start_id: int):
        """Populate vets table with test data"""
        cursor = conn.cursor()
        
        logger.info(f"\n• Populating vets table with {count} records...")
        
        first_names = ['James', 'Helen', 'Linda', 'Rafael', 'Henry', 'Sharon', 'Thomas', 'Nancy',
                      'Richard', 'Betty', 'Michael', 'Sandra', 'Steven', 'Dorothy', 'Paul']
        last_names = ['Carter', 'Leary', 'Douglas', 'Ortega', 'Stevens', 'Jenkins', 'Wright',
                     'Anderson', 'Taylor', 'Baker', 'Nelson', 'Hill', 'Mitchell', 'Campbell']
        
        vet_ids = []
        
        for i in range(count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            try:
                cursor.execute("""
                    INSERT INTO petclinic.vets (first_name, last_name)
                    VALUES (%s, %s)
                    RETURNING id
                """, (first_name, last_name))
                
                vet_id = cursor.fetchone()[0]
                vet_ids.append(vet_id)
                
            except Exception as e:
                logger.error(f"    Error creating vet {i+1}: {e}")
                raise
        
        conn.commit()
        logger.info(f"  ✓ Created {len(vet_ids)} vets successfully")
        
        # Assign specialties to some vets
        cursor.execute('SELECT id FROM petclinic.specialties')
        specialty_ids = [row[0] for row in cursor.fetchall()]
        
        if specialty_ids:
            for vet_id in vet_ids:
                # 50% chance to have a specialty
                if random.random() > 0.5:
                    specialty_id = random.choice(specialty_ids)
                    try:
                        cursor.execute("""
                            INSERT INTO petclinic.vet_specialties (vet_id, specialty_id)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING
                        """, (vet_id, specialty_id))
                    except Exception as e:
                        logger.debug(f"    Could not assign specialty: {e}")
            
            conn.commit()
            logger.info(f"  ✓ Assigned specialties to vets")
        
        return vet_ids
    
    def populate_visits(self, conn, pet_ids: list):
        """Populate visits table with test data"""
        cursor = conn.cursor()
        
        logger.info(f"\n• Populating visits table...")
        
        visit_descriptions = [
            'rabies shot', 'neutered', 'spayed', 'regular checkup', 
            'dental cleaning', 'vaccination', 'injury treatment', 
            'skin condition', 'ear infection', 'annual exam'
        ]
        
        total_visits = 0
        
        for pet_id in pet_ids:
            # Each pet gets 0-2 visits
            num_visits = random.randint(0, 2)
            
            for _ in range(num_visits):
                visit_date = date.today() - timedelta(days=random.randint(1, 365))
                description = random.choice(visit_descriptions)
                
                try:
                    cursor.execute("""
                        INSERT INTO petclinic.visits (pet_id, visit_date, description)
                        VALUES (%s, %s, %s)
                    """, (pet_id, visit_date, description))
                    
                    total_visits += 1
                    
                except Exception as e:
                    logger.error(f"    Error creating visit: {e}")
                    raise
        
        conn.commit()
        logger.info(f"  ✓ Created {total_visits} visits successfully")
    
    def run(self):
        """Execute the complete population workflow"""
        logger.info("\n" + "="*70)
        logger.info("PETCLINIC DATABASE TEST DATA POPULATOR")
        logger.info("="*70)
        logger.info(f"Environment: {self.env_name}")
        logger.info(f"Database: {self.env_config['database']}")
        logger.info(f"Host: {self.env_config['host']}")
        logger.info(f"Snapshot file: {self.snapshot_file}")
        logger.info(f"Additional records: {self.additional_records}")
        logger.info("="*70)
        
        # Test connection
        if not self.test_connection():
            logger.error("Cannot proceed without database connection")
            sys.exit(1)
        
        # Clear database
        self.clear_database()
        
        # Load snapshot data
        self.load_snapshot_data()
        
        # Create additional records
        self.create_additional_records()
        
        logger.info("\n" + "="*70)
        logger.info("✓ DATABASE POPULATION COMPLETED SUCCESSFULLY")
        logger.info("="*70 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Populate PetClinic database with test data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load snapshot only (no additional records) - uses default snapshot
  python populate_test_data.py

  # Load snapshot and create 50 additional owners (with pets)
  python populate_test_data.py --additional 50

  # Use specific snapshot file
  python populate_test_data.py --snapshot ../petclinic_snapshot_custom.json --additional 20

  # Use different environment
  python populate_test_data.py --env local --additional 20
        """
    )
    
    parser.add_argument('--env', type=str, default='source',
                        choices=['source', 'target', 'local'],
                        help='Environment to use (default: source)')
    parser.add_argument('--config', type=str, default='../db_config.json',
                        help='Path to config file (default: ../db_config.json)')
    parser.add_argument('--snapshot', type=str, default='../petclinic_snapshot_source_20260110_221752.json',
                        help='Snapshot JSON file to load baseline data from (default: ../petclinic_snapshot_source_20260110_221752.json)')
    parser.add_argument('--additional', type=int, default=0,
                        help='Number of additional owner records to create (with pets, vets, and visits) (default: 0)')
    
    args = parser.parse_args()
    
    # Check if snapshot file exists
    if not Path(args.snapshot).exists():
        logger.error(f"Snapshot file not found: {args.snapshot}")
        sys.exit(1)
    
    populator = PetClinicDataPopulator(
        env_name=args.env,
        config_path=args.config,
        snapshot_file=args.snapshot,
        additional_records=args.additional
    )
    
    populator.run()
