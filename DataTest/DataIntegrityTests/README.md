# PetClinic Test Data Integrity Module

## Overview
The **PetClinicDataIntegrity** module provides comprehensive automated testing tools for verifying database integrity, schema validation, and data consistency for the PetClinic PostgreSQL database. This module is essential for:

- **Database Migration Verification**: Ensure zero data loss during database migrations
- **Schema Validation**: Verify database structure matches expected design
- **Data Integrity Testing**: Validate referential integrity, constraints, and data consistency
- **Test Data Management**: Create reproducible test datasets with snapshot restore capability
- **Baseline Comparison**: Compare current database state against captured snapshots

---

## Module Components

### Core Scripts

| Script | Purpose | Key Features |
|--------|---------|--------------|
| **check_schema.py** | Quick schema inspection | Display table structures, columns, data types, constraints (PK, FK, UNIQUE), and auto-increment sequences |
| **create_snapshot.py** | Database snapshot creation | Capture complete database state to JSON file with metadata, schema, and all data |
| **populate_test_data.py** | Test data population | Clear database, load baseline from snapshot, create additional test records with relationships |
| **verify_migration.py** | Post-migration verification | Compare current state against snapshot baseline and generate detailed report |

### Documentation

- **README.md** (this file): Setup guide and usage instructions
- **TEST_CASES.md**: Comprehensive test case documentation with pass/fail criteria
- **migration_testcase.md**: Detailed migration test scenarios and procedures

---

## Quick Start

### Prerequisites

**Required Software:**
- Python 3.8 or higher
- PostgreSQL client libraries
- psycopg2-binary library (`pip install psycopg2-binary`)

**Database Access:**
- PostgreSQL 9.6+ database connection
- Valid database credentials
- Appropriate permissions (SELECT, INSERT, DELETE, TRUNCATE for testing)

### Installation

```bash
# Navigate to module directory
cd DataTest\DataIntegrityTests

# Install Python dependencies
pip install psycopg2-binary
```

### Configuration

The module uses `../../db_config.json` for database connections. Ensure this file exists with your environment configurations:

```json
{
  "environments": {
    "source": {
      "host": "10.130.73.5",
      "port": 5432,
      "database": "petclinic",
      "username": "petclinic",
      "password": "petclinic"
    },
    "target": {
      "host": "10.130.73.5",
      "port": 5432,
      "database": "petclinic",
      "username": "petclinic",
      "password": "petclinic"
    },
    "local": {
      "host": "localhost",
      "port": 5432,
      "database": "petclinic",
      "username": "petclinic",
      "password": "petclinic"
    }
  }
}
```

---

## Usage Guide

### 1. Schema Inspection

**Purpose**: Quickly view database table structures with constraints

```bash
# Check source environment (default)
python check_schema.py --env source

# Check target environment
python check_schema.py --env target

# Check local environment
python check_schema.py --env local

# Using custom config file
python check_schema.py --env target --config /path/to/db_config.json
```

**Output Example:**
```
======================================================================
Checking Schema - Environment: SOURCE
Database: petclinic
Server: 10.130.73.5:5432
======================================================================

=== OWNERS Table Structure ===
  Column Name                    Data Type       Nullable   Max Length  Default
  ------------------------------ --------------- ---------- ----------- --------
  id                             integer         NO         N/A         AUTO INCREMENT
  first_name                     character vary  YES        30          None
  last_name                      character vary  YES        30          None
  address                        character vary  YES        255         None
  city                           character vary  YES        80          None
  telephone                      character vary  YES        20          None

  PRIMARY KEY: owners_pkey (id)

=== PETS Table Structure ===
  Column Name                    Data Type       Nullable   Max Length  Default
  ------------------------------ --------------- ---------- ----------- --------
  id                             integer         NO         N/A         AUTO INCREMENT
  name                           character vary  YES        30          None
  birth_date                     date            YES        N/A         None
  type_id                        integer         YES        N/A         None
  owner_id                       integer         YES        N/A         None

  PRIMARY KEY: pets_pkey (id)
  FOREIGN KEY: pets_owner_id_fkey (owner_id) → owners(id)
  FOREIGN KEY: pets_type_id_fkey (type_id) → types(id)
```

### 2. Create Database Snapshot

**Purpose**: Capture complete database state to JSON file for baseline comparison or restore

```bash
# Create snapshot for source environment (default)
python create_snapshot.py --env source

# Create snapshot for target environment
python create_snapshot.py --env target

# Create snapshot for local environment
python create_snapshot.py --env local

# Specify custom output filename
python create_snapshot.py --env source --output my_snapshot.json

# Using custom config file
python create_snapshot.py --env source --config /path/to/db_config.json
```

**Generated Files:**
- `petclinic_snapshot_<env>_YYYYMMDD_HHMMSS.json`: Complete database snapshot (saved in parent directory, e.g., `../../petclinic_snapshot_source_20260110_221752.json`)
- `snapshot_YYYYMMDD_HHMMSS.log`: Detailed execution log

**Snapshot Contents:**
```json
{
  "metadata": {
    "snapshot_date": "2026-01-10 22:17:52",
    "database": "petclinic",
    "total_tables": 7,
    "total_rows": 47
  },
  "tables": {
    "owners": {
      "row_count": 10,
      "columns": ["id", "first_name", "last_name", "address", "city", "telephone"],
      "data": [...]
    },
    "pets": {...},
    "vets": {...},
    "specialties": {...},
    "types": {...},
    "vet_specialties": {...},
    "visits": {...}
  }
}
```

### 3. Populate Test Data (with Snapshot Restore)

**Purpose**: Clear database, load baseline from snapshot, and optionally create additional test records

```bash
# Load snapshot only (no additional records) - uses default snapshot file
python populate_test_data.py

# Load snapshot and create 50 additional owners (with pets, vets, and visits)
python populate_test_data.py --additional 50

# Use specific snapshot file
python populate_test_data.py --snapshot ../../petclinic_snapshot_custom.json --additional 20

# Use different environment
python populate_test_data.py --env target --additional 20

# Using custom config file
python populate_test_data.py --env local --config /path/to/db_config.json --additional 30
```

**Data Population Workflow:**
1. **Clear Database**: Deletes all records from all tables (respects foreign key order)
2. **Load Snapshot**: Restores baseline data from JSON file
3. **Reset Sequences**: Resets PostgreSQL auto-increment sequences
4. **Create Additional Records** (if --additional N specified):
   - **N owners** with addresses, cities, phone numbers
   - **1-3 pets per owner** with names, birth dates, types
   - **N/3 vets** with first/last names and specialties (50% chance)
   - **0-2 visits per new pet** with visit dates and descriptions

**Important Notes:**
- ⚠ **This script DELETES all existing records** before populating
- Requires snapshot JSON file to exist (use `create_snapshot.py` first)
- All foreign key relationships are automatically maintained
- Generated data uses realistic names, dates, and descriptions
- Maintains referential integrity with proper foreign key relationships

**Generated Files:**
- `populate_YYYYMMDD_HHMMSS.log`: Execution log with record counts

### 4. Verify Migration (Post-Migration)

**Purpose**: Compare current database state against snapshot baseline

```bash
# Verify source environment using specific snapshot
python verify_migration.py --env source --snapshot ../../petclinic_snapshot_source_20260110_221752.json

# Verify target environment
python verify_migration.py --env target --snapshot ../../petclinic_snapshot_target_20260110_221752.json

# Verify local environment
python verify_migration.py --env local --snapshot ../../petclinic_snapshot_local.json

# Using custom config file
python verify_migration.py --env target --snapshot ../../snapshot.json --config /path/to/db_config.json
```

**Verification Checks:**
- ✅ Table existence validation
- ✅ Row count comparison (baseline vs current)
- ✅ Data checksum verification (SHA256 for data integrity)
- ✅ Schema structure validation (columns, types)
- ✅ Referential integrity checks (no orphaned foreign key references)

**Generated Files:**
- `verification_YYYYMMDD_HHMMSS.log`: Test execution log with detailed results

**Sample Output:**
```
======================================================================
PetClinic Database Migration Verification
======================================================================
Environment: source
Snapshot file: ../../petclinic_snapshot_source_20260110_221752.json

TABLE VERIFICATION RESULTS:
✓ types: PASSED (6 rows match baseline)
✓ specialties: PASSED (3 rows match baseline)
✓ owners: PASSED (10 rows match baseline)
⚠ owners: Row count increased from 10 to 30 (+20 rows)
✓ pets: PASSED (13 rows match baseline)
⚠ pets: Row count increased from 13 to 52 (+39 rows)

======================================================================
VERIFICATION SUMMARY
======================================================================
✓ Tests Passed: 17
⚠ Warnings: 10
✗ Tests Failed: 0
======================================================================
```

---

## Typical Workflows

### Workflow 1: Initial Database Setup

```bash
# Step 1: Create initial snapshot of source database
python create_snapshot.py --env source

# Step 2: Populate database with baseline + test data
python populate_test_data.py --env source --additional 50

# Step 3: Verify population succeeded
python verify_migration.py --env source --snapshot ../../petclinic_snapshot_source_*.json
```

### Workflow 2: Database Migration Testing

```bash
# Step 1: Create source baseline snapshot
python create_snapshot.py --env source

# Step 2: Perform your database migration
# (External migration process - e.g., pg_dump/pg_restore, custom ETL, etc.)

# Step 3: Verify target matches source
python verify_migration.py --env target --snapshot ../../petclinic_snapshot_source_*.json

# Step 4: Review results
# Check verification log for any discrepancies
```

### Workflow 3: Reset Database to Known State

```bash
# Single command to clear and reload baseline data
python populate_test_data.py --env local

# Or with additional test records
python populate_test_data.py --env local --additional 100
```

### Workflow 4: Schema Inspection

```bash
# Quick view of current database structure
python check_schema.py --env source

# Compare with target environment
python check_schema.py --env target
```

### Workflow 5: Continuous Integration Testing

```bash
# CI/CD Pipeline Example

# 1. Reset test database to baseline state
python populate_test_data.py --env target --snapshot ../../baseline.json

# 2. Run application integration tests
# (Your PetClinic application tests)

# 3. Verify data integrity after tests
python verify_migration.py --env target --snapshot ../../baseline.json

# 4. Check exit code (0 = all passed, 1 = failures detected)
echo $?
```

---

## Testing Scenarios Covered

### 1. **Table Existence Validation**
- **Test**: Verify all expected tables exist in database
- **Pass Criteria**: All tables from snapshot present in current database
- **Tables**: owners, pets, vets, specialties, types, vet_specialties, visits

### 2. **Row Count Verification**
- **Test**: Compare record counts in all tables
- **Pass Criteria**: Exact match between baseline and current (or expected growth)
- **Warning**: Generates warning if counts differ (not a failure if additional records created)

### 3. **Data Checksum Validation**
- **Test**: SHA256 checksum of sorted data for each table
- **Pass Criteria**: Checksums match (proves no data modification)
- **Sensitivity**: Detects any change in baseline data content

### 4. **Schema Structure Validation**
- **Test**: Compare column names and order
- **Pass Criteria**: All columns from snapshot exist in same order
- **Detects**: Missing columns, column reordering

### 5. **Referential Integrity**
- **Test**: Validate no orphaned foreign key records
- **Pass Criteria**: All foreign key references are valid
- **Relationships Tested**:
  - pets → owners (owner_id)
  - pets → types (type_id)
  - visits → pets (pet_id)
  - vet_specialties → vets (vet_id)
  - vet_specialties → specialties (specialty_id)
- **Critical For**: Data consistency and application stability

---

## Database Schema

### Main Business Tables---

## Database Schema

### Core Tables

| Table | Primary Key | Foreign Keys | Description |
|-------|-------------|--------------|-------------|
| **types** | id (integer) | None | Pet type categories (cat, dog, bird, etc.) |
| **specialties** | id (integer) | None | Vet specialty types (radiology, surgery, dentistry) |
| **owners** | id (integer) | None | Pet owner records with contact information |
| **vets** | id (integer) | None | Veterinarian records |
| **vet_specialties** | vet_id, specialty_id | vet_id → vets<br>specialty_id → specialties | Vet-specialty assignments |
| **pets** | id (integer) | owner_id → owners<br>type_id → types | Pet records with birth dates |
| **visits** | id (integer) | pet_id → pets | Vet visit records with dates and descriptions |

---

## Troubleshooting

### Common Issues

#### 1. **Connection Failures**

**Error**: `Failed to connect to database`

**Solutions**:
- Verify PostgreSQL is running and accessible
- Check firewall settings (port 5432)
- Confirm credentials in db_config.json
- Test connectivity: `psql -h <host> -p 5432 -U petclinic -d petclinic`
- Verify psycopg2 installation: `pip list | grep psycopg2`

#### 2. **Snapshot File Not Found**

**Error**: `Snapshot file not found: petclinic_snapshot_*.json`

**Solutions**:
- Run `create_snapshot.py` first to create baseline
- Use `--snapshot` flag to specify correct file path
- Check file permissions and path

#### 3. **Sequence Reset Issues**

**Error**: `duplicate key value violates unique constraint`

**Causes**:
- Sequence counters not properly reset after data load
- Manual inserts with explicit IDs

**Solutions**:
- `populate_test_data.py` automatically resets sequences
- Manual reset if needed:
```sql
SELECT setval('petclinic.owners_id_seq', (SELECT MAX(id) FROM petclinic.owners), true);
SELECT setval('petclinic.pets_id_seq', (SELECT MAX(id) FROM petclinic.pets), true);
```

#### 4. **Foreign Key Violations**

**Error**: `violates foreign key constraint`

**Solutions**:
- `populate_test_data.py` deletes in correct FK order (child tables first)
- Ensure parent records exist before creating children
- Check that snapshot contains all related data

#### 5. **Python/PostgreSQL Issues**

**Error**: `ModuleNotFoundError: No module named 'psycopg2'`

**Solutions**:
```bash
# Install psycopg2-binary
pip install psycopg2-binary

# If binary installation fails, try building from source
pip install psycopg2

# Verify installation
python -c "import psycopg2; print(psycopg2.__version__)"
```

---

## Best Practices

### 1. **Always Create Snapshots Before Major Operations**
```bash
# Before any migration or significant data changes
python create_snapshot.py --env source --output ../../backups/snapshot_before_migration.json
```

### 2. **Use Descriptive Snapshot Names**
```bash
# Include context in filename
python create_snapshot.py --env source --output ../../snapshot_v2.5_baseline.json
```

### 3. **Archive Snapshot Files**
```bash
# Keep snapshots for audit trail
mkdir -p ../../snapshots/2026/january
cp ../../petclinic_snapshot_*.json ../../snapshots/2026/january/
```

### 4. **Review Logs Thoroughly**
- Even if verification passes, review warnings
- Check for unexpected data growth
- Monitor execution time for performance issues

### 5. **Test in Non-Production First**
```bash
# Test population process on non-prod environment first
python populate_test_data.py --env local --additional 50
python verify_migration.py --env local --snapshot ../../petclinic_snapshot_source.json
```

### 6. **Regular Integrity Checks**
```bash
# Schedule regular integrity verification
python verify_migration.py --env target --snapshot ../../baselines/production_baseline.json
```

---

## Output Files Reference

| File Pattern | Generated By | Purpose | Location |
|--------------|--------------|---------|----------|
| `petclinic_snapshot_<env>_YYYYMMDD_HHMMSS.json` | create_snapshot.py | Complete database snapshot with metadata | Parent directory (../../) |
| `snapshot_YYYYMMDD_HHMMSS.log` | create_snapshot.py | Snapshot creation execution log | Current directory |
| `populate_YYYYMMDD_HHMMSS.log` | populate_test_data.py | Data population execution log with record counts | Current directory |
| `verification_YYYYMMDD_HHMMSS.log` | verify_migration.py | Verification test results and summary | Current directory |

**File Name Examples:**
- `../../petclinic_snapshot_source_20260110_221752.json` - Source environment snapshot
- `../../petclinic_snapshot_target_20260110_222015.json` - Target environment snapshot
- `../../petclinic_snapshot_local_20260110_120000.json` - Local environment snapshot

---

## Command Reference Summary

### Quick Command Reference

```bash
# Schema inspection
python check_schema.py --env <source|target|local>

# Create snapshot
python create_snapshot.py --env <source|target|local> [--output filename.json]

# Populate database (clear + load snapshot + optional additional records)
python populate_test_data.py [--env <source|target|local>] [--additional N] [--snapshot filename.json]

# Verify migration
python verify_migration.py --env <source|target|local> --snapshot filename.json
```

### Common Parameter Options

All scripts support these common parameters:
- `--env {source,target,local}` - Environment from config file (default: source)
- `--config /path/to/db_config.json` - Custom config file path (default: ../../db_config.json)

---

## Performance Considerations

- **Snapshot Creation**: ~2-10 seconds depending on data volume
- **Verification**: ~5-30 seconds depending on data volume
- **Data Population**: ~2-5 seconds for baseline + 1 second per 50 additional records
- **Network Latency**: Add 1-5 seconds for remote PostgreSQL connections

**Optimization Tips**:
- Run during off-peak hours for large databases
- Use local database copies for faster execution during development
- Keep snapshot files under 10MB for quick loading
- Limit additional records (--additional) for quick iterations

---

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Reset Test Database
  run: |
    cd DataTest/DataIntegrityTests
    python populate_test_data.py --env staging --snapshot ../../baselines/baseline.json

- name: Verify Database Integrity
  run: |
    cd DataTest/DataIntegrityTests
    python verify_migration.py --env staging --snapshot ../../baselines/baseline.json
    if [ $? -ne 0 ]; then
      echo "Database integrity verification failed!"
      exit 1
    fi
```

### Azure DevOps Example
```yaml
- task: PythonScript@0
  displayName: 'Populate Test Data'
  inputs:
    scriptSource: 'filePath'
    scriptPath: 'DataTest/DataIntegrityTests/populate_test_data.py'
    arguments: '--env $(Environment) --snapshot $(SnapshotFile) --additional 100'

- task: PythonScript@0
  displayName: 'Verify Database Integrity'
  inputs:
    scriptSource: 'filePath'
    scriptPath: 'DataTest/DataIntegrityTests/verify_migration.py'
    arguments: '--env $(Environment) --snapshot $(SnapshotFile)'
```

---

## Support and Contact

For questions, issues, or suggestions:
- Review detailed logs in generated `.log` files
- Check **TEST_CASES.md** for specific test case details
- Consult **migration_testcase.md** for migration-specific scenarios

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | January 2026 | Migrated to PostgreSQL PetClinic database with snapshot-based workflow |
| 1.0 | January 2026 | Initial BookService SQL Server implementation |

---

## Related Documentation

- [TEST_CASES.md](TEST_CASES.md) - Comprehensive test case specifications
- [migration_testcase.md](migration_testcase.md) - Migration test procedures
- [../../db_config.json](../../db_config.json) - Database configuration file

---

## License

This module is part of the PetClinic POC UniCredit test automation framework.
