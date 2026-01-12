# PetClinic Test Data Integrity - Test Cases

## Document Information

| Property | Value |
|----------|-------|
| **Module** | PetClinicDataIntegrity |
| **Version** | 2.0 |
| **Last Updated** | January 10, 2026 |
| **Test Framework** | Python + psycopg2 |
| **Database** | PostgreSQL 9.6.24 |
| **Total Test Cases** | 35 |

---

## Table of Contents

1. [Test Environment Setup](#test-environment-setup)
2. [Schema Validation Tests](#schema-validation-tests)
3. [Data Integrity Tests](#data-integrity-tests)
4. [Migration Verification Tests](#migration-verification-tests)
5. [Referential Integrity Tests](#referential-integrity-tests)
6. [Test Data Population Tests](#test-data-population-tests)
7. [Performance Tests](#performance-tests)
8. [Negative Tests](#negative-tests)
9. [Edge Case Tests](#edge-case-tests)

---

## Test Environment Setup

### Test Prerequisites

| Prerequisite | Description | Verification Command |
|--------------|-------------|---------------------|
| Python 3.8+ | Python runtime | `python --version` |
| psycopg2-binary | PostgreSQL connectivity | `pip show psycopg2-binary` |
| PostgreSQL Client | PostgreSQL 9.6+ | `psql --version` |
| Database Access | Read/Write/TRUNCATE permissions | Connection test |
| db_config.json | Configuration file | File exists in ../../ |
| Snapshot File | Baseline JSON snapshot | Required for populate/verify |

### Test Data Configuration

```json
{
  "test_data_sizes": {
    "small": 10,
    "medium": 50,
    "large": 100,
    "xlarge": 500
  },
  "test_environments": ["local", "source", "target"]
}
```

---

## Schema Validation Tests

### TC-SV-001: Verify Owners Table Schema

**Objective**: Validate owners table structure matches expected schema

**Prerequisites**:
- Database connection established
- owners table exists in petclinic schema

**Test Steps**:
1. Run `check_schema.py --env source`
2. Verify owners table structure

**Expected Results**:
```
OWNERS Table Structure:
  id                   integer         NULL=NO (Primary Key, AUTO INCREMENT)
  first_name           character vary  NULL=YES (max 30)
  last_name            character vary  NULL=YES (max 30)
  address              character vary  NULL=YES (max 255)
  city                 character vary  NULL=YES (max 80)
  telephone            character vary  NULL=YES (max 20)
```

**Pass Criteria**:
- All columns present
- Data types match (integer, character varying)
- Auto-increment sequence configured
- Primary key constraint exists

**Priority**: High  
**Automated**: Yes  
**Script**: check_schema.py

---

### TC-SV-002: Verify Pets Table Schema

**Objective**: Validate pets table structure with foreign key relationships

**Test Steps**:
1. Run schema inspection
2. Verify column definitions
3. Validate foreign keys to owners and types

**Expected Results**:
```
PETS Table Structure:
  id                   integer         NULL=NO (Primary Key, AUTO INCREMENT)
  name                 character vary  NULL=YES (max 30)
  birth_date           date            NULL=YES
  type_id              integer         NULL=YES (Foreign Key → types)
  owner_id             integer         NULL=YES (Foreign Key → owners)
  
  FOREIGN KEY: pets_owner_id_fkey (owner_id) → owners(id)
  FOREIGN KEY: pets_type_id_fkey (type_id) → types(id)
```

**Pass Criteria**:
- All columns present with correct PostgreSQL types
- Foreign keys defined to owners and types tables
- Auto-increment sequence configured
- Date type used for birth_date

**Priority**: High  
**Automated**: Yes

---

### TC-SV-003: Verify Vets Table Schema

**Objective**: Validate veterinarians table structure

**Expected Results**:
```
VETS Table Structure:
  id                   integer         NULL=NO (Primary Key, AUTO INCREMENT)
  first_name           character vary  NULL=YES (max 30)
  last_name            character vary  NULL=YES (max 30)
```

**Pass Criteria**:
- All columns present
- Auto-increment sequence configured
- first_name and last_name character varying

**Priority**: High  
**Automated**: Yes

---

### TC-SV-004: Verify Visits Table Schema

**Objective**: Validate vet visits table structure

**Expected Results**:
```
VISITS Table Structure:
  id                   integer         NULL=NO (Primary Key, AUTO INCREMENT)
  pet_id               integer         NULL=YES (Foreign Key → pets)
  visit_date           date            NULL=YES
  description          character vary  NULL=YES (max 255)
  
  FOREIGN KEY: visits_pet_id_fkey (pet_id) → pets(id)
```

**Pass Criteria**:
- Foreign key to pets table exists
- visit_date uses date type
- description allows NULL
- Auto-increment sequence configured

**Priority**: High  
**Automated**: Yes

---

### TC-SV-005: Verify Types Table Schema

**Objective**: Validate pet types reference table structure

**Expected Results**:
```
TYPES Table Structure:
  id                   integer         NULL=NO (Primary Key, AUTO INCREMENT)
  name                 character vary  NULL=YES (max 80)
```

**Pass Criteria**:
- Primary key defined
- Auto-increment sequence configured
- name field is character varying

**Priority**: Medium  
**Automated**: Yes

---

### TC-SV-006: Verify Specialties Table Schema

**Objective**: Validate vet specialties reference table

**Expected Results**:
```
SPECIALTIES Table Structure:
  id                   integer         NULL=NO (Primary Key, AUTO INCREMENT)
  name                 character vary  NULL=YES (max 80)
```

**Pass Criteria**:
- Primary key defined
- Auto-increment sequence configured
- name field is character varying

**Priority**: Medium  
**Automated**: Yes

---

### TC-SV-007: Verify Vet_Specialties Junction Table Schema

**Objective**: Validate many-to-many relationship table between vets and specialties

**Expected Results**:
```
VET_SPECIALTIES Table Structure:
  vet_id               integer         NULL=NO (Foreign Key → vets)
  specialty_id         integer         NULL=NO (Foreign Key → specialties)
  
  PRIMARY KEY: (vet_id, specialty_id)
  FOREIGN KEY: vet_specialties_vet_id_fkey (vet_id) → vets(id)
  FOREIGN KEY: vet_specialties_specialty_id_fkey (specialty_id) → specialties(id)
```

**Pass Criteria**:
- Composite primary key on (vet_id, specialty_id)
- Two foreign keys defined correctly
- No auto-increment (junction table)

**Priority**: High  
**Automated**: Yes

---

## Data Integrity Tests

### TC-DI-001: Row Count Verification - Owners

**Objective**: Verify no records lost during migration/population for owners table

**Prerequisites**:
- Snapshot created with known record count
- Data population/migration completed

**Test Steps**:
1. Run `create_snapshot.py --env source` (before migration)
2. Perform migration or data population
3. Run `verify_migration.py --env target --snapshot ../petclinic_snapshot_source_*.json`

**Expected Results**:
```
✓ owners: PASSED (10 rows match baseline)
  Baseline: 10 records
  Current:  10 records
  Difference: 0
```

**Pass Criteria**:
- Row counts match exactly (if no additional data created)
- Warning shown if additional records created (expected behavior)
- No baseline data lost or modified

**Priority**: Critical  
**Automated**: Yes  
**Script**: verify_migration.py

---

### TC-DI-002: Row Count Verification - Pets

**Objective**: Verify pets table record integrity

**Test Data**: 13 pet records in baseline (1-3 pets per owner)

**Expected Results**:
```
✓ pets: PASSED (13 rows match baseline)
  Baseline: 13 records
  Current:  13 records
```

**Pass Criteria**: Exact match or expected growth from --additional parameter

**Priority**: Critical  
**Automated**: Yes

---

### TC-DI-003: Row Count Verification - Vets

**Objective**: Verify veterinarian data integrity

**Expected Results**:
```
✓ vets: PASSED (6 rows match baseline)
  Baseline: 6 records
  Current:  6 records
```

**Priority**: Critical  
**Automated**: Yes

---

### TC-DI-004: Row Count Verification - Visits

**Objective**: Verify vet visit data integrity

**Test Data**: 4 visit records in baseline

**Expected Results**:
```
✓ visits: PASSED (4 rows match baseline)
  Baseline: 4 records
  Current:  4 records
```

**Priority**: Critical  
**Automated**: Yes

---

### TC-DI-005: Row Count Verification - Types

**Objective**: Verify pet types reference data integrity

**Expected Results**:
```
✓ types: PASSED (6 rows match baseline)
  Baseline: 6 records (cat, dog, lizard, snake, bird, hamster)
  Current:  6 records
```

**Priority**: Critical  
**Automated**: Yes

---

### TC-DI-006: Row Count Verification - Specialties

**Objective**: Verify vet specialties reference data integrity

**Expected Results**:
```
✓ specialties: PASSED (3 rows match baseline)
  Baseline: 3 records (radiology, surgery, dentistry)
  Current:  3 records
```

**Priority**: Critical  
**Automated**: Yes

---

### TC-DI-007: Row Count Verification - Vet_Specialties

**Objective**: Verify vet-specialty assignments integrity

**Expected Results**:
```
✓ vet_specialties: PASSED (5 rows match baseline)
  Baseline: 5 records
  Current:  5 records
```

**Priority**: High  
**Automated**: Yes

---

### TC-DI-008: Data Checksum Validation - Owners

**Objective**: Verify owners data content integrity using SHA256 checksums

**Test Steps**:
1. Snapshot creates checksum of sorted owners data
2. Post-migration, calculate current checksum
3. Compare checksums

**Expected Results**:
```
✓ owners: Data checksum matched
  Baseline Checksum: 7a3f8c2d9e1b...
  Current Checksum:  7a3f8c2d9e1b...
```

**Pass Criteria**:
- Checksums match exactly
- Indicates no data corruption
- Proves data fidelity

**Priority**: Critical  
**Automated**: Yes  
**Detects**: Any data modification, corruption, or loss

---

### TC-DI-009: Data Checksum Validation - Pets

**Objective**: Verify pets data integrity through checksums

**Sensitivity**: Detects any change in name, birth_date, type_id, owner_id

**Expected Results**:
```
✓ pets: Data checksum matched
```

**Priority**: Critical  
**Automated**: Yes

---

### TC-DI-010: Data Checksum Validation - Vets

**Objective**: Verify veterinarian data hasn't been corrupted

**Expected Results**:
```
✓ vets: Data checksum matched
```

**Priority**: Critical  
**Automated**: Yes

---

### TC-DI-011: Data Checksum Validation - Visits

**Objective**: Verify visit data integrity

**Expected Results**:
```
✓ visits: Data checksum matched
```

**Priority**: High  
**Automated**: Yes

---

### TC-DI-012: Data Checksum Validation - Types

**Objective**: Verify pet types reference data integrity

**Expected Results**:
```
✓ types: Data checksum matched
```

**Priority**: Medium  
**Automated**: Yes

---

### TC-DI-013: Data Checksum Validation - Specialties

**Objective**: Verify specialties reference data integrity

**Expected Results**:
```
✓ specialties: Data checksum matched
```

**Priority**: Medium  
**Automated**: Yes

---

## Migration Verification Tests

### TC-MV-001: Complete Migration Verification

**Objective**: Execute full migration verification suite

**Test Steps**:
1. Create snapshot: `python create_snapshot.py --env source`
2. Perform data population: `python populate_test_data.py --env source --additional 50`
3. Perform migration (external process - pg_dump/pg_restore or custom ETL)
4. Verify migration: `python verify_migration.py --env target --snapshot ../petclinic_snapshot_source_*.json`

**Expected Results**:
```
======================================================================
VERIFICATION SUMMARY
======================================================================
✓ Tests Passed: 17
Tests Failed: 0
Warnings: 0
Overall Status: PASSED
```

**Detailed Checks**:
- ✓ All 6 main tables: Row counts match
- ✓ All 6 main tables: Checksums match
- ✓ Schema structure preserved
- ✓ Foreign keys intact
- ✓ Indexes present

**Pass Criteria**:
- 0 failed tests
- All critical checks pass
- Warnings acceptable if documented

**Priority**: Critical  
**Automated**: Yes  
**Duration**: ~30-60 seconds

---

### TC-MV-002: Schema Migration Verification

**Objective**: Verify schema structure preserved during migration

**Test Steps**:
1. Compare snapshot schema with current schema
2. Validate column definitions
3. Check data types and constraints

**Expected Results**:
```
✓ owners: Schema structure matched (6 columns)
✓ pets: Schema structure matched (5 columns)
✓ vets: Schema structure matched (3 columns)
✓ visits: Schema structure matched (4 columns)
✓ types: Schema structure matched (2 columns)
✓ specialties: Schema structure matched (2 columns)
✓ vet_specialties: Schema structure matched (2 columns)
```

**Pass Criteria**:
- All columns present
- Data types unchanged (integer, character varying, date)
- Nullability constraints preserved
- Auto-increment sequences configured

**Priority**: Critical  
**Automated**: Yes

---

### TC-MV-003: Foreign Key Preservation

**Objective**: Verify all foreign key relationships maintained

**Test Steps**:
1. Extract foreign key definitions from snapshot
2. Compare with current database
3. Validate all relationships exist
4. Check for orphaned records

**Expected Results**:
```
✓ pets.owner_id → owners.id: Preserved (no orphaned pets)
✓ pets.type_id → types.id: Preserved (no orphaned pets)
✓ visits.pet_id → pets.id: Preserved (no orphaned visits)
✓ vet_specialties.vet_id → vets.id: Preserved (no orphaned assignments)
✓ vet_specialties.specialty_id → specialties.id: Preserved (no orphaned assignments)
```

**Pass Criteria**:
- All foreign key constraints present
- No orphaned records (all FK references valid)
- Referential integrity maintained

**Priority**: Critical  
**Automated**: Yes

---

### TC-MV-004: Sequence and Primary Key Preservation

**Objective**: Verify auto-increment sequences and primary keys maintained

**Test Steps**:
1. Check sequence definitions for all tables with auto-increment IDs
2. Validate primary key constraints
3. Verify sequence current values match max IDs

**Expected Results**:
```
✓ petclinic.owners_id_seq: Configured (currval matches MAX(id))
✓ petclinic.pets_id_seq: Configured (currval matches MAX(id))
✓ petclinic.vets_id_seq: Configured (currval matches MAX(id))
✓ petclinic.visits_id_seq: Configured (currval matches MAX(id))
✓ petclinic.types_id_seq: Configured (currval matches MAX(id))
✓ petclinic.specialties_id_seq: Configured (currval matches MAX(id))
✓ owners.owners_pkey (id): Present
✓ pets.pets_pkey (id): Present
✓ vets.vets_pkey (id): Present
✓ vet_specialties primary key (vet_id, specialty_id): Present
```

**Pass Criteria**:
- All sequences properly configured
- Sequence values > MAX(id) to prevent duplicate key errors
- All primary key constraints exist
- Composite primary key on vet_specialties junction table

**Priority**: Critical  
**Automated**: Yes

---

### TC-MV-005: Migration with Large Dataset

**Objective**: Test migration verification with substantial data volume

**Test Data**:
- 100 Owners
- 200+ Pets (1-3 per owner)
- 30 Vets
- 100+ Visits
- 6 Types (baseline)
- 3 Specialties (baseline)

**Test Steps**:
```bash
python create_snapshot.py --env source
python populate_test_data.py --env source --additional 100
python create_snapshot.py --env source --output large_baseline.json
# Perform migration
python verify_migration.py --env target --snapshot large_baseline.json
```

**Expected Results**:
- All checksums match for baseline data
- Verification completes within 60 seconds
- No memory issues

**Pass Criteria**:
- 100% baseline data integrity
- Performance acceptable

**Priority**: High  
**Automated**: Yes  
**Duration**: ~1 minute

---

## Referential Integrity Tests

### TC-RI-001: Pets-Owners Relationship

**Objective**: Verify every pet has a valid owner reference

**Test Steps**:
1. Query all pet_id → owner_id relationships
2. Validate all owner_ids exist in owners table
3. Check for orphaned pets

**SQL Validation**:
```sql
-- Should return 0 orphaned pets
SELECT COUNT(*) 
FROM petclinic.pets p
LEFT JOIN petclinic.owners o ON p.owner_id = o.id
WHERE o.id IS NULL
```

**Expected Results**:
```
✓ pets-owners: No orphaned records
  Total Pets: 13
  Valid References: 13
  Orphaned: 0
```

**Pass Criteria**: 0 orphaned records

**Priority**: Critical  
**Automated**: Yes

---

### TC-RI-002: Pets-Types Relationship

**Objective**: Verify pet type references are valid

**SQL Validation**:
```sql
-- Should return 0 invalid type references
SELECT COUNT(*) 
FROM petclinic.pets p
LEFT JOIN petclinic.types t ON p.type_id = t.id
WHERE p.type_id IS NOT NULL AND t.id IS NULL
```

**Expected Results**:
```
✓ pets-types: All references valid
  Pets with Type: 13
  Invalid References: 0
```

**Priority**: High  
**Automated**: Yes

---

### TC-RI-003: Visits-Pets Relationship

**Objective**: Verify every visit entry references a valid pet

**SQL Validation**:
```sql
-- Should return 0 orphaned visits
SELECT COUNT(*) 
FROM petclinic.visits v
LEFT JOIN petclinic.pets p ON v.pet_id = p.id
WHERE p.id IS NULL
```

**Expected Results**:
```
✓ visits-pets: No orphaned records
  Total Visits: 4
  Valid References: 4
  Orphaned: 0
```

**Priority**: Critical  
**Automated**: Yes

---

### TC-RI-004: Vet_Specialties-Vets Relationship

**Objective**: Verify all vet specialty assignments have valid vet references

**SQL Validation**:
```sql
-- Should return 0 orphaned vet_specialty assignments
SELECT COUNT(*) 
FROM petclinic.vet_specialties vs
LEFT JOIN petclinic.vets v ON vs.vet_id = v.id
WHERE v.id IS NULL
```

**Expected Results**:
```
✓ vet_specialties-vets: No orphaned records
  Total Assignments: 5
  Valid Vet References: 5
  Orphaned: 0
```

**Priority**: High  
**Automated**: Yes

---

### TC-RI-005: Vet_Specialties-Specialties Relationship

**Objective**: Verify all vet specialty assignments have valid specialty references

**SQL Validation**:
```sql
-- Should return 0 orphaned specialty assignments
SELECT COUNT(*) 
FROM petclinic.vet_specialties vs
LEFT JOIN petclinic.specialties s ON vs.specialty_id = s.id
WHERE s.id IS NULL
```

**Expected Results**:
```
✓ vet_specialties-specialties: All references valid
  Total Assignments: 5
  Valid Specialty Refs: 5
  Orphaned: 0
```

**Priority**: High  
**Automated**: Yes

---

### TC-RI-006: Cascade Delete Validation

**Objective**: Verify cascade delete rules work correctly

**Test Steps**:
1. Create test data with relationships
2. Attempt to delete an owner with pets
3. Verify cascade behavior or constraint enforcement

**Expected Behavior**:
```
Option A: Cascade Delete Enabled
  - Delete owner → pets also deleted → visits also deleted
  
Option B: Restrict Delete (Recommended)
  - Delete owner → Error: FK constraint violation
  - Must delete visits, then pets, then owner
```

**Pass Criteria**: Behavior matches PostgreSQL FK constraint configuration

**Priority**: High  
**Automated**: Partial  
**Note**: May require manual verification

---

## Test Data Population Tests

### TC-TP-001: Load Snapshot Only (Baseline Data)

**Objective**: Verify snapshot loading without additional records

**Test Command**:
```bash
python populate_test_data.py --env local
```

**Expected Results**:
```
Data Population Summary:
  Types Loaded: 6 (cat, dog, lizard, snake, bird, hamster)
  Specialties Loaded: 3 (radiology, surgery, dentistry)
  Owners Loaded: 10
  Vets Loaded: 6
  Vet_Specialties Loaded: 5
  Pets Loaded: 13 (1-3 per owner)
  Visits Loaded: 4
```

**Validation**:
```sql
SELECT 
  (SELECT COUNT(*) FROM petclinic.owners) as owners,
  (SELECT COUNT(*) FROM petclinic.pets) as pets,
  (SELECT COUNT(*) FROM petclinic.vets) as vets,
  (SELECT COUNT(*) FROM petclinic.visits) as visits,
  (SELECT COUNT(*) FROM petclinic.types) as types
```

**Pass Criteria**:
- All baseline tables populated from snapshot
- Sequences reset correctly
- Execution time < 3 seconds

**Priority**: High  
**Automated**: Yes

---

### TC-TP-002: Populate with Additional Records (20)

**Objective**: Test data generation with additional owners/pets

**Test Command**:
```bash
python populate_test_data.py --env source --additional 20
```

**Expected Results**:
- Baseline: 10 owners, 13 pets, 6 vets, 4 visits
- Additional: 20 owners, ~40 pets (1-3 per owner), ~6 vets, ~30 visits
- Total: 30 owners, 53 pets, 12 vets, 34 visits

**Pass Criteria**:
- Baseline data loaded correctly
- Additional data created with valid relationships
- All foreign keys valid
- Execution time < 5 seconds

**Priority**: High  
**Automated**: Yes

---

### TC-TP-003: Populate Large Dataset (100 records)

**Objective**: Verify data generation scales to larger volumes

**Test Command**:
```bash
python populate_test_data.py 100 --env target
```

**Expected Results**:
- 100 Authors
- 200 Books
- 100 Customers
- 600 Stocks
- ~300 Rentals

**Performance**: Should complete within 30 seconds

**Priority**: High  
**Automated**: Yes

---

### TC-TP-003: Populate with Large Additional Dataset (100)

**Objective**: Test data generation with large volume

**Test Command**:
```bash
python populate_test_data.py --env target --additional 100
```

**Expected Results**:
- Baseline: 10 owners, 13 pets, 6 vets, 4 visits
- Additional: 100 owners, ~200 pets, ~33 vets, ~150 visits
- Total: 110 owners, 213 pets, 39 vets, 154 visits

**Pass Criteria**:
- All data created successfully
- Execution time < 10 seconds
- No duplicate key errors

**Priority**: High  
**Automated**: Yes

---

### TC-TP-004: Verify Data Relationships

**Objective**: Ensure populated data has correct relationships

**Validations**:
1. Every pet has exactly 1 owner
2. Every pet has exactly 1 type
3. Every visit references existing pet
4. Every vet_specialty has valid vet and specialty

**Expected Results**:
```
✓ pets-owners: 100% valid (13/13)
✓ pets-types: 100% valid (13/13)
✓ visits-pets: 100% valid (4/4)
✓ vet_specialties-vets: 100% valid (5/5)
✓ vet_specialties-specialties: 100% valid (5/5)
```

**Priority**: Critical  
**Automated**: Yes

---

### TC-TP-005: Data Cleanup and Reload

**Objective**: Verify cleanup deletes all existing data before snapshot reload

**Test Steps**:
1. Populate initial data with `--additional 20`
2. Run population script again (includes cleanup)
3. Verify old data removed, snapshot reloaded

**Expected Behavior**:
```
CLEARING ALL RECORDS FROM DATABASE
  ✓ Deleted    41 rows from visits
  ✓ Deleted    53 rows from pets
  ✓ Deleted     5 rows from vet_specialties
  ✓ Deleted    12 rows from vets
  ✓ Deleted    30 rows from owners
  ✓ Deleted     3 rows from specialties
  ✓ Deleted     6 rows from types

LOADING BASELINE DATA FROM SNAPSHOT
  ✓ Loaded     6 rows into types
  ✓ Loaded     3 rows into specialties
  ✓ Loaded    10 rows into owners
  [... baseline restored ...]
```

**Pass Criteria**:
- All tables cleared in correct FK order (visits→pets→...)
- No foreign key constraint violations
- Snapshot reloaded successfully

**Priority**: High  
**Automated**: Yes

---

---

## Test Execution Instructions

### Full Test Suite Execution

```bash
# 1. Setup test environment
cd DataTest/DataIntegrityTests

# 2. Run schema validation
python check_schema.py --env source > test_results/schema_validation.log

# 3. Create snapshot
python create_snapshot.py --env source --output test_results/baseline_snapshot.json

# 4. Test data population (20 additional records for speed)
python populate_test_data.py --env local --snapshot test_results/baseline_snapshot.json --additional 20

# 5. Verify data integrity 
python verify_migration.py --env local --snapshot test_results/baseline_snapshot.json

# 6. Review results
cat verification_*.log
```

### Smoke Test (Quick Validation)

```bash
# Quick snapshot + baseline 
<To be Updated>
```

### Regression Test (Comprehensive)

```bash
<To be Updated>
```

---

## Test Results Tracking

### Success Criteria

**All Critical Tests (22)**: Must pass 100%  
**High Priority Tests (17)**: Must pass ≥ 95%  
**Medium Priority Tests (9)**: Must pass ≥ 90%  
**Low Priority Tests (4)**: Best effort

### Test Report Template

```
Test Execution Report
=====================
Date: YYYY-MM-DD
Tester: [Name]
Environment: [local/source/target]
Data Size: Baseline + [0/20/50/100] additional

Results:
  Total Tests: 50
  Passed: __
  Failed: __
  Warnings: __
  Skipped: __
  
Critical Issues: [None/List]
Recommendations: [Actions needed]

Status: PASS/FAIL
```

---

## Maintenance and Updates

### When to Update Test Cases

- New database tables added to PetClinic schema
- Schema changes implemented (column additions, constraint modifications)
- New validation requirements
- Performance benchmarks change
- Bug fixes requiring new test coverage
- Snapshot format changes

### Test Case Review Schedule

- Monthly: Review failed/flaky tests
- Quarterly: Update expected values and benchmarks
- After major releases: Full test case review
- After PostgreSQL version upgrades: Compatibility testing

---

## References

- [README.md](README.md) - Module setup and usage guide
- [migration_testcase.md](migration_testcase.md) - Migration-specific test procedures
- [../../db_config.json](../../db_config.json) - Database configuration
- PostgreSQL 9.6 documentation
- Python psycopg2 best practices

---

## Appendix: Test Data Patterns

### Owners Test Data Pattern
```python
first_name: Random from ['John', 'Jane', 'Michael', 'Sarah', 'David', ...]
last_name: Random from ['Smith', 'Johnson', 'Williams', 'Brown', ...]
address: "{random_number} {street_name} {street_type}"
city: Random from ['Madison', 'Sun Prairie', 'McFarland', 'Windsor', ...]
telephone: "608555{random_4_digits}"
```

### Pets Test Data Pattern
```python
name: Random from ['Max', 'Bella', 'Charlie', 'Lucy', 'Cooper', ...]
birth_date: Random date 1-15 years ago
type_id: Random from existing types (cat, dog, lizard, snake, bird, hamster)
owner_id: Reference to created owner
```

### Vets Test Data Pattern
```python
first_name: Random from ['James', 'Helen', 'Linda', 'Rafael', 'Henry', ...]
last_name: Random from ['Carter', 'Leary', 'Douglas', 'Ortega', ...]
specialty: 50% chance of specialty assignment (radiology, surgery, dentistry)
```

### Visits Test Data Pattern
```python
pet_id: Reference to created pet
visit_date: Random date within last 365 days
description: Random from ['rabies shot', 'neutered', 'spayed', 'regular checkup', ...]
```

### Baseline Snapshot Data (47 records)
```
types: 6 records (cat, dog, lizard, snake, bird, hamster)
specialties: 3 records (radiology, surgery, dentistry)
owners: 10 records
vets: 6 records
vet_specialties: 5 records (vet-specialty assignments)
pets: 13 records (1-3 per owner)
visits: 4 records
```

---
