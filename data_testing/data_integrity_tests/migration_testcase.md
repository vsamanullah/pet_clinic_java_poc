# Database Migration Data Integrity Test Cases

## Overview
This document outlines the comprehensive test cases for verifying data integrity during database migration. The tests are automated using the `verify_migration.py` script which compares a baseline snapshot (pre-migration) against the current database state (post-migration).

### Database Tables Covered
This test suite covers **6 main business tables** plus supporting tables:

| Table | Type | Description | Test Coverage |
|-------|------|-------------|---------------|
| **Authors** | Main | Author information with bio, nationality | Full (Row Count, Checksum, Schema, FK) |
| **Books** | Main | Book catalog with pricing, ratings | Full (Row Count, Checksum, Schema, FK) |
| **Genres** | Support | Book genre categories | Full (Row Count, Checksum, Schema) |
| **Customers** | Main | Customer records with registration | Full (Row Count, Checksum, Schema, FK) |
| **Rentals** | Main | Rental transactions and status | Full (Row Count, Checksum, Schema, FK) |
| **Stocks** | Main | Book inventory and availability | Full (Row Count, Checksum, Schema, FK) |
| Users, Roles, UserRoles | Support | Authentication and authorization | Schema and FK only |
| Errors, __MigrationHistory | System | System tables | Not tested |

**Total Test Cases**: 34 individual test cases across 10 categories

---

## Test Environment

### Prerequisites
- **Baseline File**: Created using `create_baseline.py` before migration
- **Database Access**: Connection to both source and target databases
- **Tools**: Python 3.x, pyodbc, SQL Server
- **Configuration**: `db_config.json` with source/target/local environments

### Configuration Setup

Create `db_config.json` with your database environments:
```json
{
  "environments": {
    "source": {
      "server": "10.134.77.68,1433",
      "database": "BookStore-Master-Source",
      "authentication": "SQL",
      "username": "testuser",
      "password": "TestDb@26#!",
      "driver": "ODBC Driver 18 for SQL Server",
      "encrypt": "yes",
      "trust_certificate": "yes"
    },
    "target": {
      "server": "10.134.77.68,1433",
      "database": "BookStore-Master",
      "authentication": "SQL",
      "username": "testuser",
      "password": "TestDb@26#!",
      "driver": "ODBC Driver 18 for SQL Server",
      "encrypt": "yes",
      "trust_certificate": "yes"
    },
    "local": {
      "server": "(localdb)\\MSSQLLocalDB",
      "database": "BookServiceContext",
      "authentication": "Windows",
      "driver": "ODBC Driver 17 for SQL Server"
    }
  }
}
```

### Test Data Setup

#### Option 1: Using Environment Configuration (Recommended)
```bash
# Populate test data in source database (creates all 6 main tables)
python populate_test_data.py 25 --env source
# This creates:
#   - 25 Authors
#   - 50 Books (2 per author)
#   - 25 Customers
#   - 150 Stocks (3 copies per book)
#   - ~75 Rentals (50% of stocks)

# Create baseline from source database
python create_baseline.py --env source

# Run migration
# (Your migration process here)

# Verify migration on target database
python verify_migration.py --env target
```

#### Option 2: Using Direct Connection Strings
```bash
# Populate test data
python populate_test_data.py 25 --conn "DRIVER={ODBC Driver 18 for SQL Server};SERVER=...;..."

# Create baseline
python create_baseline.py --conn "DRIVER={...};SERVER=...;..."

# Verify migration
python verify_migration.py --conn "DRIVER={...};SERVER=...;..." --baseline baseline_YYYYMMDD_HHMMSS.json
```

#### Expected Data Volumes
When you populate with N records (e.g., `populate_test_data.py 25`):
- **Authors**: N records (e.g., 25)
- **Books**: 2×N records (e.g., 50) - 2 books per author
- **Genres**: 1 record (default genre)
- **Customers**: N records (e.g., 25)
- **Stocks**: 6×N records (e.g., 150) - 3 copies of each book
- **Rentals**: ~3×N records (e.g., ~75) - approximately 50% of stocks rented

#### Option 3: Auto-Detect Baseline
```bash
# Create baseline
python create_baseline.py --env source

# Verify (automatically uses latest baseline)
python verify_migration.py --env target
```

---

## Test Suite Categories

### 1. Table Existence Verification

#### TC-001: Verify All Tables Are Preserved
**Objective**: Ensure no tables are dropped during migration  
**Priority**: Critical  
**Test Steps**:
1. Compare table list in baseline vs. current database
2. Identify any removed tables
3. Identify any new tables added

**Expected Results**:
- All baseline tables exist in current database
- Warning if new tables are added
- Fail if any baseline tables are missing

**Verification Method**: Table count comparison
```sql
SELECT TABLE_SCHEMA, TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
```

---

### 2. Row Count Verification

#### TC-002: Verify No Data Loss in Authors Table
**Objective**: Ensure all author records are preserved  
**Priority**: Critical  
**Test Steps**:
1. Get row count from baseline for `dbo.Authors`
2. Get current row count for `dbo.Authors`
3. Compare counts

**Expected Results**:
- ✅ Pass: Row count unchanged (before = after)
- ⚠️ Warning: Row count increased (before < after)
- ❌ Fail: Row count decreased (DATA LOSS)

**Verification SQL**:
```sql
SELECT COUNT(*) FROM [dbo].[Authors]
```

#### TC-003: Verify No Data Loss in Books Table
**Objective**: Ensure all book records are preserved  
**Priority**: Critical  
**Test Steps**:
1. Get row count from baseline for `dbo.Books`
2. Get current row count for `dbo.Books`
3. Compare counts

**Expected Results**:
- Pass: Row count unchanged
- Warning: Row count increased
- Fail: Row count decreased (DATA LOSS)

#### TC-003a: Verify No Data Loss in Customers Table
**Objective**: Ensure all customer records are preserved  
**Priority**: Critical  
**Test Steps**:
1. Get row count from baseline for `dbo.Customers`
2. Get current row count for `dbo.Customers`
3. Compare counts

**Expected Results**:
- ✅ Pass: Row count unchanged (before = after)
- ⚠️ Warning: Row count increased (before < after)
- ❌ Fail: Row count decreased (DATA LOSS)

**Verification SQL**:
```sql
SELECT COUNT(*) FROM [dbo].[Customers]
```

#### TC-003b: Verify No Data Loss in Rentals Table
**Objective**: Ensure all rental transaction records are preserved  
**Priority**: Critical  
**Test Steps**:
1. Get row count from baseline for `dbo.Rentals`
2. Get current row count for `dbo.Rentals`
3. Compare counts

**Expected Results**:
- Pass: Row count unchanged
- Warning: Row count increased
- Fail: Row count decreased (DATA LOSS)

#### TC-003c: Verify No Data Loss in Stocks Table
**Objective**: Ensure all stock inventory records are preserved  
**Priority**: Critical  
**Test Steps**:
1. Get row count from baseline for `dbo.Stocks`
2. Get current row count for `dbo.Stocks`
3. Compare counts

**Expected Results**:
- Pass: Row count unchanged
- Warning: Row count increased
- Fail: Row count decreased (DATA LOSS)

#### TC-004: Verify Row Counts for All Tables
**Objective**: Comprehensive row count validation across all tables  
**Priority**: High  
**Test Steps**:
1. Iterate through all tables in baseline
2. Compare row counts for each table
3. Report discrepancies

**Expected Results**: Row integrity maintained across all tables

---

### 3. Data Integrity Checksums

#### TC-005: Verify Authors Data Integrity
**Objective**: Ensure author data remains unchanged during migration  
**Priority**: Critical  
**Test Steps**:
1. Calculate SHA256 checksum of all `Authors` records (baseline)
2. Calculate SHA256 checksum of all `Authors` records (current)
3. Compare checksums

**Expected Results**:
- Pass: Checksums match (data unchanged)
- Warning: Checksums differ but row count changed (acceptable data modification)
- Warning: Checksums differ with same row count (data values modified)

**Checksum Calculation**: SHA256 hash of sorted JSON representation of all rows

#### TC-006: Verify Books Data Integrity
**Objective**: Ensure book data remains unchanged during migration  
**Priority**: Critical  
**Test Steps**:
1. Calculate SHA256 checksum of all `Books` records (baseline)
2. Calculate SHA256 checksum of all `Books` records (current)
3. Compare checksums

**Expected Results**: Same as TC-005

#### TC-006a: Verify Customers Data Integrity
**Objective**: Ensure customer data remains unchanged during migration  
**Priority**: Critical  
**Test Steps**:
1. Calculate SHA256 checksum of all `Customers` records (baseline)
2. Calculate SHA256 checksum of all `Customers` records (current)
3. Compare checksums

**Expected Results**: Same as TC-005

**Checksum Calculation**: SHA256 hash of sorted JSON representation of all rows

#### TC-006b: Verify Rentals Data Integrity
**Objective**: Ensure rental transaction data remains unchanged during migration  
**Priority**: Critical  
**Test Steps**:
1. Calculate SHA256 checksum of all `Rentals` records (baseline)
2. Calculate SHA256 checksum of all `Rentals` records (current)
3. Compare checksums

**Expected Results**: Same as TC-005

#### TC-006c: Verify Stocks Data Integrity
**Objective**: Ensure stock inventory data remains unchanged during migration  
**Priority**: Critical  
**Test Steps**:
1. Calculate SHA256 checksum of all `Stocks` records (baseline)
2. Calculate SHA256 checksum of all `Stocks` records (current)
3. Compare checksums

**Expected Results**: Same as TC-005

#### TC-007: Verify Data Integrity for All Tables
**Objective**: Comprehensive checksum validation across all tables  
**Priority**: High  
**Test Steps**:
1. Iterate through all tables
2. Calculate and compare checksums
3. Identify data modifications

**Expected Results**: Data integrity maintained or modifications documented

---

### 4. Schema Verification

#### TC-008: Verify Authors Table Schema
**Objective**: Ensure Authors table structure is preserved  
**Priority**: High  
**Test Steps**:
1. Get column definitions from baseline (name, type, length, nullable, default)
2. Get current column definitions
3. Compare schemas

**Expected Schema** (Example):
```sql
- Id (int, NOT NULL, Identity)
- Name (nvarchar(100), NOT NULL)
- Country (nvarchar(50), NULL)
- BirthDate (datetime2(7), NULL)
```

**Expected Results**:
- Pass: Schema unchanged
- Warning: Column count changed
- Warning: Column properties modified

#### TC-009: Verify Books Table Schema
**Objective**: Ensure Books table structure is preserved  
**Priority**: High  
**Test Steps**: Same as TC-008

**Expected Schema** (Example):
```sql
- Id (int, NOT NULL, Identity)
- Title (nvarchar(200), NOT NULL)
- AuthorId (int, NOT NULL, FK)
- PublishedDate (datetime2(7), NULL)
- ISBN (nvarchar(20), NULL)
- Price (decimal(18,2), NULL)
```

#### TC-009a: Verify Customers Table Schema
**Objective**: Ensure Customers table structure is preserved  
**Priority**: High  
**Test Steps**: Same as TC-008

**Expected Schema**:
```sql
- ID (int, NOT NULL, Identity)
- FirstName (nvarchar(100), NOT NULL)
- LastName (nvarchar(100), NOT NULL)
- Email (nvarchar(200), NOT NULL)
- IdentityCard (nvarchar(50), NOT NULL)
- UniqueKey (uniqueidentifier, NOT NULL)
- DateOfBirth (datetime, NOT NULL)
- Mobile (nvarchar(10), NULL)
- RegistrationDate (datetime, NOT NULL)
```

#### TC-009b: Verify Rentals Table Schema
**Objective**: Ensure Rentals table structure is preserved  
**Priority**: High  
**Test Steps**: Same as TC-008

**Expected Schema**:
```sql
- ID (int, NOT NULL, Identity)
- CustomerId (int, NOT NULL, FK)
- StockId (int, NOT NULL, FK)
- RentalDate (datetime, NOT NULL)
- ReturnedDate (datetime, NULL)
- Status (nvarchar(10), NOT NULL)
```

#### TC-009c: Verify Stocks Table Schema
**Objective**: Ensure Stocks table structure is preserved  
**Priority**: High  
**Test Steps**: Same as TC-008

**Expected Schema**:
```sql
- ID (int, NOT NULL, Identity)
- BookId (int, NOT NULL, FK)
- UniqueKey (uniqueidentifier, NOT NULL)
- IsAvailable (bit, NOT NULL)
```

#### TC-010: Verify Schema for All Tables
**Objective**: Comprehensive schema validation  
**Priority**: High  
**Test Steps**:
1. Compare column count for each table
2. Compare data types and properties
3. Identify schema changes

**Verification SQL**:
```sql
SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, 
       IS_NULLABLE, COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
ORDER BY ORDINAL_POSITION
```

---

### 5. Foreign Key Verification

#### TC-011: Verify Foreign Key Relationships
**Objective**: Ensure all foreign key constraints are maintained  
**Priority**: High  
**Test Steps**:
1. List all foreign keys from baseline
2. List all current foreign keys
3. Compare FK definitions

**Expected Foreign Keys**:
```
Books.AuthorId → Authors.Id
Books.GenreId → Genres.Id
Rentals.CustomerId → Customers.Id
Rentals.StockId → Stocks.Id
Stocks.BookId → Books.Id
UserRoles.UserId → Users.Id
UserRoles.RoleId → Roles.Id
```

**Expected Results**:
- Pass: All FKs unchanged
- Warning: FKs removed
- Warning: New FKs added

**Verification SQL**:
```sql
SELECT fk.name, tp.name, cp.name, tr.name, cr.name
FROM sys.foreign_keys AS fk
INNER JOIN sys.foreign_key_columns AS fkc 
  ON fk.object_id = fkc.constraint_object_id
-- ... (full query in verify_migration.py)
```

#### TC-012: Verify FK Constraints Are Enforced
**Objective**: Ensure FK constraints are active and enforced  
**Priority**: High  
**Test Steps**:
1. Verify FK exists in sys.foreign_keys
2. Check is_disabled flag
3. Validate constraint is active

**Expected Results**: All FKs are enabled and enforced

---

### 6. Index Verification

#### TC-013: Verify Primary Key Indexes
**Objective**: Ensure all primary keys are maintained  
**Priority**: Critical  
**Test Steps**:
1. List all primary key indexes from baseline
2. List current primary key indexes
3. Compare definitions

**Expected Results**:
- Pass: All PKs unchanged
- Fail: PKs removed or modified

#### TC-014: Verify Non-Clustered Indexes
**Objective**: Ensure all performance indexes are maintained  
**Priority**: Medium  
**Test Steps**:
1. List all non-clustered indexes from baseline
2. List current non-clustered indexes
3. Compare index definitions (columns, uniqueness)

**Expected Results**:
- Pass: All indexes unchanged
- Warning: Indexes removed
- Warning: New indexes added

**Verification SQL**:
```sql
SELECT i.name, i.type_desc, i.is_unique, i.is_primary_key,
       COL_NAME(ic.object_id, ic.column_id)
FROM sys.indexes AS i
INNER JOIN sys.index_columns AS ic 
  ON i.object_id = ic.object_id AND i.index_id = ic.index_id
-- ... (full query in verify_migration.py)
```

#### TC-015: Verify Index Performance
**Objective**: Ensure indexes are properly optimized  
**Priority**: Low  
**Test Steps**:
1. Check index fragmentation levels
2. Verify index usage statistics
3. Identify unused indexes

---

### 7. Referential Integrity Verification

#### TC-016: Verify No Orphaned Books Records
**Objective**: Ensure all books have valid author references  
**Priority**: Critical  
**Test Steps**:
1. Execute LEFT JOIN query to find orphaned records
2. Count records where FK reference is invalid

**Verification SQL**:
```sql
SELECT COUNT(*) 
FROM [dbo].[Books] b
LEFT JOIN [dbo].[Authors] a ON b.AuthorId = a.Id
WHERE b.AuthorId IS NOT NULL AND a.Id IS NULL
```

**Expected Results**:
- Pass: 0 orphaned records
- Fail: Any orphaned records found (CRITICAL)

#### TC-017: Verify All Foreign Key Relationships
**Objective**: Comprehensive referential integrity check  
**Priority**: Critical  
**Test Steps**:
1. Iterate through all foreign key relationships
2. Check for orphaned records in each relationship
3. Report any violations

**Expected Results**: No orphaned records in any table

#### TC-017a: Verify No Orphaned Rental Records
**Objective**: Ensure all rentals have valid customer and stock references  
**Priority**: Critical  
**Test Steps**:
1. Check for rentals with invalid CustomerId references
2. Check for rentals with invalid StockId references

**Verification SQL**:
```sql
-- Check orphaned customer references
SELECT COUNT(*) 
FROM [dbo].[Rentals] r
LEFT JOIN [dbo].[Customers] c ON r.CustomerId = c.ID
WHERE r.CustomerId IS NOT NULL AND c.ID IS NULL;

-- Check orphaned stock references
SELECT COUNT(*) 
FROM [dbo].[Rentals] r
LEFT JOIN [dbo].[Stocks] s ON r.StockId = s.ID
WHERE r.StockId IS NOT NULL AND s.ID IS NULL;
```

**Expected Results**:
- Pass: 0 orphaned records
- Fail: Any orphaned records found (CRITICAL)

#### TC-017b: Verify No Orphaned Stock Records
**Objective**: Ensure all stocks have valid book references  
**Priority**: Critical  
**Test Steps**:
1. Check for stocks with invalid BookId references

**Verification SQL**:
```sql
SELECT COUNT(*) 
FROM [dbo].[Stocks] s
LEFT JOIN [dbo].[Books] b ON s.BookId = b.ID
WHERE s.BookId IS NOT NULL AND b.ID IS NULL;
```

**Expected Results**:
- Pass: 0 orphaned records
- Fail: Any orphaned records found (CRITICAL)

---

### 8. Data Content Validation

#### TC-018: Verify Sample Author Records
**Objective**: Spot-check specific author records for data accuracy  
**Priority**: Medium  
**Test Steps**:
1. Select sample author records from baseline
2. Retrieve same records from current database
3. Compare all field values

**Sample Test Data**:
```
Author ID: 1
Expected AuthorId: [GUID]
Expected FirstName: "John"
Expected LastName: "Smith [timestamp]"
Expected BirthDate: [datetime]
Expected Nationality: "USA"
Expected Bio: "Bio for John Smith [timestamp]"
Expected Email: "john.smith.0@example.com"
Expected Affiliation: "Publisher 1"
```

**Expected Results**: All field values match exactly

#### TC-019: Verify Sample Book Records
**Objective**: Spot-check specific book records for data accuracy  
**Priority**: Medium  
**Test Steps**:
1. Select sample book records from baseline
2. Retrieve same records from current database
3. Compare all field values including foreign keys

**Expected Results**: All field values match exactly

#### TC-019a: Verify Sample Customer Records
**Objective**: Spot-check specific customer records for data accuracy  
**Priority**: Medium  
**Test Steps**:
1. Select sample customer records from baseline
2. Retrieve same records from current database
3. Compare all field values including UniqueKey GUID

**Sample Test Data**:
```
Customer ID: 1
Expected FirstName: "Customer1"
Expected Email: "customer1@test.com"
Expected IdentityCard: "ID1001"
```

**Expected Results**: All field values match exactly

#### TC-019b: Verify Sample Rental Records
**Objective**: Spot-check specific rental transaction records for data accuracy  
**Priority**: Medium  
**Test Steps**:
1. Select sample rental records from baseline
2. Retrieve same records from current database
3. Compare all field values including foreign keys and status

**Expected Results**: All field values match exactly

#### TC-019c: Verify Sample Stock Records
**Objective**: Spot-check specific stock inventory records for data accuracy  
**Priority**: Medium  
**Test Steps**:
1. Select sample stock records from baseline
2. Retrieve same records from current database
3. Compare all field values including UniqueKey and availability status

**Expected Results**: All field values match exactly

---

### 9. Edge Case Testing

#### TC-020: Verify NULL Value Handling
**Objective**: Ensure NULL values are preserved correctly  
**Priority**: Medium  
**Test Steps**:
1. Identify records with NULL values in baseline
2. Verify same records have NULL values in current database
3. Check NULLable columns maintain NULL capability

**Expected Results**: NULL values preserved, no unexpected NULLs or non-NULLs

#### TC-021: Verify Empty String Handling
**Objective**: Ensure empty strings are not converted to NULL  
**Priority**: Low  
**Test Steps**:
1. Identify records with empty strings in baseline
2. Verify same values in current database
3. Confirm empty strings ≠ NULL

#### TC-022: Verify Special Characters
**Objective**: Ensure special characters are preserved  
**Priority**: Medium  
**Test Steps**:
1. Test records containing: quotes, apostrophes, unicode, newlines
2. Verify character encoding is preserved
3. Check for data truncation

**Test Characters**:
```
- Single quote: O'Reilly
- Double quote: "Test"
- Unicode: 北京, Москва, العربية
- Special: &, <, >, ", ', \
```

#### TC-023: Verify Date/Time Precision
**Objective**: Ensure datetime values maintain precision  
**Priority**: Medium  
**Test Steps**:
1. Compare datetime values including milliseconds
2. Check for timezone conversion issues
3. Verify datetime2(7) precision maintained

---

### 10. Performance Validation

#### TC-024: Verify Migration Completion Time
**Objective**: Ensure migration completes within acceptable timeframe  
**Priority**: Low  
**Test Steps**:
1. Record migration start time
2. Record migration end time
3. Calculate duration

**Expected Results**: Migration completes within SLA (e.g., < 1 hour)

#### TC-025: Verify Database Size
**Objective**: Ensure database size is reasonable post-migration  
**Priority**: Low  
**Test Steps**:
1. Check baseline database size
2. Check current database size
3. Compare and analyze growth

**Expected Results**: Size increase is justified and reasonable

---

## Test Execution Results Template

### Migration Verification Summary

| **Metric** | **Count** |
|------------|-----------|
| Baseline Timestamp | YYYY-MM-DD HH:MM:SS |
| Verification Timestamp | YYYY-MM-DD HH:MM:SS |
| Total Tests Executed | X |
| Tests Passed  | X |
| Tests with Warnings  | X |
| Tests Failed  | X |
| Success Rate | XX.X% |

---

### Test Results by Category

#### Table Existence
-  All baseline tables exist
-  N new tables added
-  N tables removed

#### Row Counts
- Authors: N rows (unchanged)
- Books: N rows (unchanged)
- Customers: N rows (unchanged)
- Rentals: N rows (unchanged)
- Stocks: N rows (unchanged)
- Summary: No data loss detected

#### Data Checksums
-  Authors: Data unchanged
-  Books: Data unchanged
-  Customers: Data unchanged
-  Rentals: Data unchanged
-  Stocks: Data unchanged
- Summary: Data integrity verified

#### Schema Verification
-  Authors schema: Unchanged
-  Books schema: Unchanged
-  Customers schema: Unchanged
-  Rentals schema: Unchanged
-  Stocks schema: Unchanged
- Summary: Schema preserved

#### Foreign Keys
-  N foreign keys preserved
-  N foreign keys added/removed

#### Indexes
-  N indexes preserved
-  N indexes added/removed

#### Referential Integrity
-  No orphaned records
- Summary: All FK relationships valid

---

## Critical Failure Scenarios

### Data Loss (CRITICAL)
**Trigger**: Row count decrease in any table  
**Action**:
1. STOP further migration activities
2. Investigate missing data
3. Rollback if necessary
4. Re-run migration with fixes

### Orphaned Records (CRITICAL)
**Trigger**: Foreign key violations detected  
**Action**:
1. Identify orphaned records
2. Determine root cause
3. Fix data integrity issues
4. Re-validate

### Schema Changes (HIGH)
**Trigger**: Column removed or type changed  
**Action**:
1. Verify change is intentional
2. Update baseline if expected
3. Test application compatibility

---

## Automation Commands

### Full Test Suite Execution

#### Using Environment Configuration (Recommended)
```bash
# Step 1: Create test data in source
python populate_test_data.py 25 --env source
# Output: Creates 25 authors, 50 books, 25 customers, 150 stocks, ~75 rentals

# Step 2: Create baseline from source
python create_baseline.py --env source
# Output: baseline_YYYYMMDD_HHMMSS.json

# Step 3: Run migration
# (Your migration process)

# Step 4: Verify migration on target
python verify_migration.py --env target
# Output: verification_YYYYMMDD_HHMMSS.log

# Step 5: Review logs
# Check verification_YYYYMMDD_HHMMSS.log
```

#### Using Direct Connection Strings
```bash
# Step 1: Create test data
python populate_test_data.py 25 --conn "DRIVER={ODBC Driver 18 for SQL Server};SERVER=10.134.77.68,1433;DATABASE=BookStore-Master-Source;UID=testuser;PWD=TestDb@26#!;Encrypt=yes;TrustServerCertificate=yes;"

# Step 2: Create baseline
python create_baseline.py --conn "DRIVER={...};SERVER=...;..."

# Step 3: Run migration
# (Your migration process)

# Step 4: Verify migration
python verify_migration.py --conn "DRIVER={...};SERVER=...;..." --baseline baseline_YYYYMMDD_HHMMSS.json

# Step 5: Review logs
```

### Quick Verification (After Migration)
```bash
# Auto-detects latest baseline, uses target environment
python verify_migration.py --env target

# Or with specific baseline
python verify_migration.py --env target --baseline baseline_20260108_143000.json
```

### Command Line Options

#### create_baseline.py
```bash
--env {source|target|local}  # Environment from config file
--config <path>              # Custom config file (default: db_config.json)
--conn <connection_string>   # Direct connection string (overrides --env)
```

#### verify_migration.py
```bash
--env {source|target|local}  # Environment from config file
--baseline <file>            # Baseline JSON file (auto-detects if omitted)
--config <path>              # Custom config file (default: db_config.json)
--conn <connection_string>   # Direct connection string (overrides --env)
```

#### populate_test_data.py
```bash
<count>                      # Number of records to create (required)
--env {source|target|local}  # Environment from config file
--config <path>              # Custom config file (default: db_config.json)
--conn <connection_string>   # Direct connection string (overrides --env)
```

---

## Success Criteria

### Migration is considered SUCCESSFUL if:
1. All baseline tables exist in target (Authors, Books, Genres, Customers, Rentals, Stocks)
2. Row counts are unchanged or increased (documented)
3. Data checksums match (or changes documented)
4. Schema is preserved for all 6 main business tables (or changes documented)
5. Foreign keys are maintained (Books→Authors, Books→Genres, Rentals→Customers, Rentals→Stocks, Stocks→Books)
6. No orphaned records exist in any table
7. All indexes are present
8. No critical test failures

### Migration requires REVIEW if:
- Warnings present but no failures
- Row counts increased (verify expected growth)
- Schema modifications detected (verify intentional)
- New tables/indexes added (verify expected)

### Migration has FAILED if:
- Any row count decreased (data loss)
- Orphaned records exist (referential integrity violation)
- Tables or primary keys missing
- Critical schema changes unexpected

---

## Rollback Procedures

### If Migration Fails:
1. **Document Failures**: Capture all failed test cases and errors
2. **Preserve State**: Do not modify current database
3. **Analyze Logs**: Review `verification_*.log` for root cause
4. **Execute Rollback**:
   ```bash
   # Restore from backup
   RESTORE DATABASE [BookStore-Master] 
   FROM DISK = 'path/to/backup.bak'
   WITH REPLACE, RECOVERY
   ```
5. **Verify Rollback**: Run verification against original baseline
6. **Fix Issues**: Address root cause before re-attempting migration

---

## Practical Examples & Real Output

### Example 1: Creating Test Data (5 Records)

**Command**:
```bash
python populate_test_data.py 5 --env target
```

**Expected Output**:
```
✓ Created 5 authors successfully
✓ Created 10 books successfully
✓ Created 5 customers successfully
✓ Created 30 stocks successfully
✓ Created 15 rentals successfully

DATABASE SUMMARY
======================================================================
  dbo.Authors                                       5 rows
  dbo.Books                                        10 rows
  dbo.Customers                                     5 rows
  dbo.Genres                                        1 rows
  dbo.Rentals                                      15 rows
  dbo.Stocks                                       30 rows
======================================================================
  Total Rows: 66
```

### Example 2: Checking All Table Schemas

**Command**:
```bash
python check_schema.py
```

**Expected Output** (abbreviated):
```
=== Authors Table Structure ===
  ID                   int             NULL=NO
  AuthorId             uniqueidentifier NULL=NO
  FirstName            nvarchar        NULL=NO
  LastName             nvarchar        NULL=NO
  BirthDate            datetime        NULL=NO
  ...

=== Customers Table Structure ===
  ID                   int             NULL=NO
  FirstName            nvarchar        NULL=NO
  LastName             nvarchar        NULL=NO
  Email                nvarchar        NULL=NO
  ...

=== Rentals Table Structure ===
  ID                   int             NULL=NO
  CustomerId           int             NULL=NO
  StockId              int             NULL=NO
  RentalDate           datetime        NULL=NO
  ReturnedDate         datetime        NULL=YES
  Status               nvarchar        NULL=NO

=== Stocks Table Structure ===
  ID                   int             NULL=NO
  BookId               int             NULL=NO
  UniqueKey            uniqueidentifier NULL=NO
  IsAvailable          bit             NULL=NO
```

### Example 3: Baseline Creation

**Command**:
```bash
python create_baseline.py --env source
```

**Expected Output**:
```
✓ Connected to database successfully
  Database: BookStore-Master-Source on 10.134.77.68,1433

Collecting baseline data...
  ✓ Found 11 tables
  ✓ Collected row counts for all tables
  ✓ Calculated checksums for all tables
  ✓ Collected schema information
  ✓ Collected foreign key relationships
  ✓ Collected index information

Baseline saved to: baseline_20260108_220620.json
```

### Example 4: Verification After Migration

**Command**:
```bash
python verify_migration.py --env target
```

**Expected Output** (successful migration):
```
✓ Using baseline: baseline_20260108_220620.json
✓ Connected to database successfully

Verification Results:
  ✓ All 11 baseline tables exist
  ✓ Row counts match for all tables:
      Authors: 5 → 5 (unchanged)
      Books: 10 → 10 (unchanged)
      Customers: 5 → 5 (unchanged)
      Rentals: 15 → 15 (unchanged)
      Stocks: 30 → 30 (unchanged)
  ✓ Data checksums match for all tables
  ✓ Schema preserved for all tables
  ✓ All foreign keys preserved
  ✓ No orphaned records found

VERIFICATION PASSED ✓
```

---

## Reporting

### Log Files Generated
- `baseline_YYYYMMDD_HHMMSS.json` - Pre-migration snapshot
- `baseline_YYYYMMDD_HHMMSS.log` - Baseline creation log
- `verification_YYYYMMDD_HHMMSS.log` - Verification execution log

### Report Contents
- Timestamp of baseline and verification
- Total tests executed, passed, warned, failed
- Detailed test results for each category
- List of critical failures (if any)
- Success rate percentage

---

## Maintenance

### Updating Test Cases
- Add new test cases as database schema evolves
- Update expected results when intentional changes occur
- Document exceptions and known differences

### Baseline Management
- Create new baseline after each successful migration
- Archive old baselines with migration documentation
- Label baselines clearly with version/date

### Version History
- v1.0 (2026-01-08): Initial test case documentation
- Added comprehensive coverage for all verification categories
- v1.1 (2026-01-08): Extended coverage for multi-table testing
- Added test cases for Customers, Rentals, and Stocks tables (TC-003a-c, TC-006a-c, TC-009a-c, TC-017a-b, TC-019a-c)
- Updated FK verification to include all table relationships
- Increased total test cases from 25 to 34 individual test cases

---

## Contact & Support

For issues or questions regarding migration verification:
- Review logs in `verification_*.log`
- Check baseline file integrity
- Verify database connectivity
- Consult database administrator

---

**END OF TEST CASES DOCUMENT**
