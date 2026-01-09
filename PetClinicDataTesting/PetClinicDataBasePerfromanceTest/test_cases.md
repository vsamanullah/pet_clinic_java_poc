# Database Load Testing - Test Cases Documentation

## Overview

This document describes the test cases for the **BookServiceContext Database Performance Testing Tool**. The tool is designed to validate database performance under various load conditions and monitor SQL Server behavior during concurrent operations across **6 main business tables**.

### Tables Under Test
- **Authors** - Author information with full biographical data
- **Books** - Book catalog with pricing and ratings
- **Genres** - Book genre categories
- **Customers** - Customer records with registration details
- **Rentals** - Rental transactions and status tracking
- **Stocks** - Book inventory and availability management

## What Are We Testing?

### Primary Objectives

1. **Database Performance Under Load**
   - Measure response times for CRUD operations across all tables
   - Identify performance bottlenecks in multi-table scenarios
   - Evaluate scalability with concurrent connections
   - Monitor resource utilization (CPU, Memory, I/O)

2. **Concurrent Connection Handling**
   - Test database behavior with multiple simultaneous connections
   - Detect deadlocks and lock contention across related tables
   - Validate connection pooling efficiency
   - Assess transaction throughput with foreign key constraints

3. **Operation-Specific Performance**
   - SELECT query performance (single table and JOINs)
   - INSERT operation throughput with FK validation
   - UPDATE statement efficiency across multiple tables
   - DELETE operation handling with referential integrity

4. **Multi-Table Transaction Testing**
   - Cross-table operations (Rentals → Customers/Stocks)
   - Foreign key constraint performance
   - Complex JOIN queries
   - Transaction isolation under load

4. **System Health Monitoring**
   - SQL Server CPU utilization
   - Memory consumption patterns
   - Active connection tracking
   - Transaction rate monitoring
   - Lock wait and deadlock detection

---

## Test Environment

### Database Schema
```
Database: BookStore-Master

Tables:
1. Authors (Parent Table)
   - ID (INT, PRIMARY KEY, IDENTITY)
   - AuthorId (UNIQUEIDENTIFIER)
   - FirstName (NVARCHAR)
   - LastName (NVARCHAR)
   - BirthDate (DATETIME)
   - Nationality (NVARCHAR)
   - Bio (NVARCHAR)
   - Email (NVARCHAR)
   - Affiliation (NVARCHAR)

2. Genres (Lookup Table)
   - ID (INT, PRIMARY KEY, IDENTITY)
   - Name (NVARCHAR)

3. Books (Parent Table)
   - ID (INT, PRIMARY KEY, IDENTITY)
   - Title (NVARCHAR)
   - AuthorId (INT, FOREIGN KEY → Authors.ID)
   - Year (INT)
   - Price (DECIMAL)
   - Description (NVARCHAR)
   - GenreId (INT, FOREIGN KEY → Genres.ID)
   - IssueDate (DATETIME)
   - Rating (TINYINT)
   - Image (NVARCHAR, NULLABLE)
   - TrailURI (NVARCHAR, NULLABLE)

4. Customers (Parent Table)
   - ID (INT, PRIMARY KEY, IDENTITY)
   - FirstName (NVARCHAR)
   - LastName (NVARCHAR)
   - Email (NVARCHAR)
   - IdentityCard (NVARCHAR)
   - UniqueKey (UNIQUEIDENTIFIER)
   - DateOfBirth (DATETIME)
   - Mobile (NVARCHAR, NULLABLE)
   - RegistrationDate (DATETIME)

5. Stocks (Child Table)
   - ID (INT, PRIMARY KEY, IDENTITY)
   - BookId (INT, FOREIGN KEY → Books.ID)
   - UniqueKey (UNIQUEIDENTIFIER)
   - IsAvailable (BIT)

6. Rentals (Transaction Table)
   - ID (INT, PRIMARY KEY, IDENTITY)
   - CustomerId (INT, FOREIGN KEY → Customers.ID)
   - StockId (INT, FOREIGN KEY → Stocks.ID)
   - RentalDate (DATETIME)
   - ReturnedDate (DATETIME, NULLABLE)
   - Status (NVARCHAR)

Foreign Key Relationships:
- Books → Authors (BookId)
- Books → Genres (GenreId)
- Stocks → Books (BookId)
- Rentals → Customers (CustomerId)
- Rentals → Stocks (StockId)
```

### Test Data
- **Genres**: 1 default genre ("General") - auto-seeded
- **Authors**: 20 pre-seeded records with full biographical data
- **Books**: Generated dynamically during tests
- **Customers**: 20 pre-seeded customer records
- **Stocks**: ~60 stock items (3 copies per book) - auto-seeded
- **Rentals**: Generated dynamically during tests
- **Test Records**: All marked with timestamp-based unique identifiers

---

## Test Cases

### TC-001: Database Cleanup and Initialization

**Objective**: Verify database can be properly cleaned and initialized for testing

**Pre-conditions**:
- Database exists and is accessible
- User has DELETE permissions on all tables

**Test Steps**:
1. Execute `python run_and_monitor_db_test.py --env target --cleanup`
2. Verify all records are deleted from Rentals table (FK child)
3. Verify all records are deleted from Stocks table (FK child)
4. Verify all records are deleted from Books table
5. Verify all records are deleted from Authors table
6. Verify all records are deleted from Customers table
7. Verify identity seeds are reset (if permissions allow)

**Expected Results**:
- Rentals table: 0 records
- Stocks table: 0 records
- Books table: 0 records
- Authors table: 0 records
- Customers table: 0 records
- Genres table: Preserved (not deleted)
- Deletion respects foreign key constraints (correct order)
- No errors during cleanup
- Success message displayed

**Success Criteria**:   All tables are empty, identity reset successful

---

### TC-002: Database Seeding

**Objective**: Verify database can be seeded with initial test data (Genres and Authors)

**Pre-conditions**:
- Database is clean (TC-001 completed)
- User has INSERT permissions on Genres and Authors tables

**Test Steps**:
1. Run seeding process (automatic during test execution)
2. Verify 1 default genre is inserted ("General")
3. Verify 20 author records are inserted with complete biographical data
4. Verify 20 customer records are inserted with registration details
5. Verify stocks are created (3 copies per book when books exist)

**Expected Results**:
- Genres table: 1 record
- Authors table: 20 records with complete data (FirstName, LastName, BirthDate, Nationality, Bio, Email, Affiliation)
- Customers table: 20 records with unique emails and identity cards
- Stocks table: ~30 records when books are seeded
- All GUIDs properly generated
- No duplicate records
- All foreign key relationships valid

**Success Criteria**:
-   All tables seeded successfully
-   Foreign keys properly linked
-   No constraint violations

---

### TC-003: Basic Load Test - Default Configuration

**Objective**: Execute a basic load test with default settings

**Test Configuration**:
```
Connections: 20
Operations per Connection: 100
Test Type: Mixed
Duration: 120 seconds
Total Operations: 2000
```

**Test Steps**:
1. Execute: `python run_and_monitor_db_test.py`
2. Monitor console output for progress
3. Wait for completion
4. Review generated CSV and summary files

**Expected Results**:
- All 2000 operations complete successfully
- Success rate > 95%
- Average response time < 100ms
- No deadlocks detected
- Results saved to `database_test_results/` directory

**Success Criteria**: 
-   >95% success rate
-   Response time within acceptable range
-   All files generated correctly

---

### TC-004: High Concurrency Load Test

**Objective**: Test database behavior under high concurrent load

**Test Configuration**:
```
Connections: 100
Operations per Connection: 500
Test Type: Mixed
Duration: 300 seconds
Total Operations: 50,000
```

**Test Steps**:
1. Execute: `python run_and_monitor_db_test.py -c 100 -o 500 -d 300`
2. Monitor system resources
3. Track error rates and response times
4. Analyze results

**Expected Results**:
- System handles high concurrency without crashes
- Degradation in response time is gradual and predictable
- Lock waits may increase but remain manageable
- CPU and memory stay within acceptable bounds

**Success Criteria**:
-   >90% success rate maintained
-   No critical errors or crashes
-   Response time P95 < 500ms

---

### TC-005: Read-Only Load Test

**Objective**: Measure SELECT query performance

**Test Configuration**:
```
Connections: 30
Operations per Connection: 200
Test Type: Read
Duration: 120 seconds
```

**Test Steps**:
1. Execute: `python run_and_monitor_db_test.py -c 30 -o 200 -t Read`
2. Monitor query execution times
3. Analyze different SELECT patterns:
   - SELECT TOP 100
   - SELECT by ID
   - SELECT with JOIN
   - SELECT COUNT(*)

**Expected Results**:
- Fastest response times among all test types
- Minimal lock contention
- High throughput (operations/second)
- Low CPU utilization

**Success Criteria**:
-   Average response time < 50ms
-   >99% success rate
-   Throughput > 100 ops/sec

---

### TC-006: Write-Intensive Load Test

**Objective**: Test INSERT operation performance and throughput

**Test Configuration**:
```
Connections: 20
Operations per Connection: 300
Test Type: Write
Duration: 150 seconds
```

**Test Steps**:
1. Execute: `python run_and_monitor_db_test.py -c 20 -o 300 -t Write`
2. Monitor INSERT performance
3. Track transaction log growth
4. Verify data integrity

**Expected Results**:
- All INSERTs complete successfully
- Higher response times than reads (expected)
- Increased page writes and transaction counts
- No constraint violations

**Success Criteria**:
-   >95% success rate
-   Average response time < 150ms
-   All inserted records are valid

---

### TC-007: Update Operations Test

**Objective**: Validate UPDATE statement performance

**Test Configuration**:
```
Connections: 15
Operations per Connection: 200
Test Type: UPDATE
Duration: 120 seconds
```

**Test Steps**:
1. Seed database with test data
2. Execute: `python run_and_monitor_db_test.py -c 15 -o 200 -t UPDATE`
3. Monitor lock waits and blocking
4. Verify updated values

**Expected Results**:
- UPDATEs complete without excessive locking
- Moderate response times
- Lock waits tracked and logged
- Data consistency maintained

**Success Criteria**:
-   >95% success rate
-   Lock wait count < 100
-   No deadlocks

---

### TC-008: Delete Operations Test

**Objective**: Test DELETE operation performance

**Test Configuration**:
```
Connections: 10
Operations per Connection: 100
Test Type: DELETE
Duration: 120 seconds
```

**Test Steps**:
1. Pre-populate database with test records
2. Execute: `python run_and_monitor_db_test.py -c 10 -o 100 -t DELETE`
3. Verify only test records are deleted
4. Check foreign key constraint handling

**Expected Results**:
- Only "Performance Test Book" records are deleted
- No errors from constraint violations
- Consistent performance
- Transaction log properly managed

**Success Criteria**:
-   >95% success rate
-   Only test data deleted
-   No constraint errors

---

### TC-009: Mixed Workload Test (Realistic Scenario)

**Objective**: Simulate real-world mixed operations

**Test Configuration**:
```
Connections: 50
Operations per Connection: 300
Test Type: Mixed
Duration: 240 seconds

Operation Distribution:
- 60% SELECT queries
- 20% INSERT operations
- 10% UPDATE operations
- 10% DELETE operations
```

**Test Steps**:
1. Execute: `python run_and_monitor_db_test.py -c 50 -o 300 -t Mixed -d 240`
2. Monitor all metrics simultaneously
3. Analyze operation type breakdown
4. Compare performance across operation types

**Expected Results**:
- Balanced workload distribution
- Different response times per operation type
- System handles mixed load efficiently
- No significant blocking or deadlocks

**Success Criteria**:
-   >95% overall success rate
-   Operation distribution matches expected ratios (±5%)
-   P95 response time < 200ms

---

### TC-010: Performance Monitoring Verification

**Objective**: Validate monitoring metrics are captured correctly

**Test Steps**:
1. Run any load test
2. Verify metrics_*.csv file is generated
3. Check all metric columns are populated:
   - timestamp
   - cpu_usage
   - memory_usage_mb
   - active_connections
   - batch_requests
   - page_reads
   - page_writes
   - transactions
   - lock_waits
   - deadlocks

**Expected Results**:
- Metrics collected every 5 seconds
- All values are numeric (except timestamp)
- No missing data points
- Summary statistics displayed at end

**Success Criteria**:
-   All metrics captured
-   No data gaps
-   Statistics calculated correctly

---

### TC-011: Stress Test - Maximum Connections

**Objective**: Find breaking point and maximum capacity

**Test Configuration**:
```
Connections: 200
Operations per Connection: 1000
Test Type: Mixed
Duration: 600 seconds
Total Operations: 200,000
```

**Test Steps**:
1. Execute: `python run_and_monitor_db_test.py -c 200 -o 1000 -d 600`
2. Monitor for failures and errors
3. Track resource exhaustion
4. Document degradation patterns

**Expected Results**:
- System may show degraded performance
- Error rate may increase
- Resource utilization near maximum
- System remains stable (no crashes)

**Success Criteria**:
-   >80% success rate maintained
-   System recovers after test
-   No data corruption

---

### TC-012: Results File Generation

**Objective**: Verify all output files are created correctly

**Test Steps**:
1. Run complete test cycle
2. Check `database_test_results/` directory
3. Verify file creation:
   - load_test_YYYYMMDD_HHMMSS.csv
   - summary_YYYYMMDD_HHMMSS.txt
   - metrics_YYYYMMDD_HHMMSS.csv

**Expected Results**:
- All three file types created
- Files contain valid data
- CSV files importable to Excel
- Summary file readable and formatted

**Success Criteria**:
-   All files present
-   No empty or corrupt files
-   Timestamps match test execution time

---

### TC-012a: Multi-Table Operation Distribution

**Objective**: Verify operations are distributed across all 4 main tables (Books, Customers, Rentals, Stocks)

**Test Configuration**:
```
Connections: 20
Operations per Connection: 100
Test Type: Mixed
Total Operations: 2000
```

**Test Steps**:
1. Execute: `python run_and_monitor_db_test.py --env target -c 20 -o 100 -t Mixed`
2. Review summary report for operation distribution
3. Verify operations across all tables:
   - Books operations (40% - SELECT, INSERT, UPDATE, DELETE)
   - Customer operations (25% - SELECT, INSERT, UPDATE, DELETE)
   - Rental operations (20% - SELECT, INSERT, UPDATE)
   - Stock operations (15% - SELECT, INSERT, UPDATE)

**Expected Results**:
- Operations distributed across all 4 table types
- Each table type shows multiple operation types
- Proper weighting: Books > Customers > Rentals > Stocks
- Foreign key operations succeed (Rentals referencing Customers/Stocks)

**Success Criteria**:
-   All 4 table types have operations
-   Operation distribution roughly matches weights (±10%)
-   >75% success rate across all table types
-   No orphaned FK records

---

### TC-012b: Customer Operations Performance

**Objective**: Test Customer table CRUD operations under load

**Test Configuration**:
```
Connections: 15
Operations per Connection: 150
Focus: Customer operations (INSERT, SELECT, UPDATE, DELETE)
```

**Test Steps**:
1. Seed customers (20 records)
2. Execute mixed operations
3. Monitor operations:
   - CUSTOMER_INSERT: New customer registrations
   - CUSTOMER_SELECT_BY_ID: Customer lookup
   - CUSTOMER_SELECT_BY_EMAIL: Email-based search
   - CUSTOMER_SELECT_ALL: List all customers
   - CUSTOMER_COUNT: Count operations
   - CUSTOMER_UPDATE: Modify customer details
   - CUSTOMER_DELETE: Remove customers (if no rentals)

**Expected Results**:
- All customer operations complete successfully
- Email uniqueness maintained
- UniqueKey (GUID) properly generated
- SELECT operations faster than INSERT/UPDATE

**Success Criteria**:
-   >90% success rate for SELECT operations
-   >80% success rate for INSERT operations
-   Average SELECT response < 10ms
-   Average INSERT response < 50ms

---

### TC-012c: Rental Transaction Performance

**Objective**: Test Rental transaction operations with FK constraints

**Test Configuration**:
```
Connections: 10
Operations per Connection: 100
Focus: Rental operations with FK validation
```

**Test Steps**:
1. Seed customers and stocks
2. Execute rental operations:
   - RENTAL_INSERT: Create new rentals (requires valid CustomerId and StockId)
   - RENTAL_SELECT_ACTIVE: Query active rentals
   - RENTAL_SELECT_BY_CUSTOMER: Customer rental history
   - RENTAL_UPDATE: Update rental status (Active → Returned)
   - RENTAL_COUNT: Count operations

**Expected Results**:
- Rental INSERTs validate FK constraints
- Cannot create rental with invalid CustomerId
- Cannot create rental with invalid StockId
- Status updates work correctly
- ReturnedDate set properly when status = 'Returned'

**Success Criteria**:
-   >85% success rate (some failures expected for invalid FKs)
-   All successful rentals have valid FK references
-   No orphaned rental records
-   Average response time < 100ms

---

### TC-012d: Stock Inventory Operations

**Objective**: Test Stock inventory management operations

**Test Configuration**:
```
Connections: 12
Operations per Connection: 120
Focus: Stock availability tracking
```

**Test Steps**:
1. Seed books and stocks (3 copies per book)
2. Execute stock operations:
   - STOCK_INSERT: Add new stock items
   - STOCK_SELECT_AVAILABLE: Find available books
   - STOCK_SELECT_BY_BOOK: Get all copies of a book
   - STOCK_UPDATE: Toggle availability
   - STOCK_COUNT: Count operations

**Expected Results**:
- Stock items properly linked to Books via BookId
- IsAvailable bit field works correctly
- UniqueKey (GUID) properly generated
- Multiple copies per book tracked correctly

**Success Criteria**:
-   >90% success rate
-   All stock items have valid BookId references
-   IsAvailable toggles work correctly
-   Average response time < 20ms

---

### TC-012e: Foreign Key Constraint Validation

**Objective**: Verify FK constraints are enforced under load

**Test Steps**:
1. Attempt to create Books with invalid AuthorId → Should fail
2. Attempt to create Rentals with invalid CustomerId → Should fail
3. Attempt to create Rentals with invalid StockId → Should fail
4. Attempt to create Stocks with invalid BookId → Should fail
5. Verify error messages are proper FK violations

**Expected Results**:
- All FK violations caught by database
- Proper error messages returned
- No orphaned records created
- Database maintains referential integrity

**Success Criteria**:
-   100% FK validation enforcement
-   No orphaned records after test
-   Clear error messages for violations

---

### TC-013: Error Handling and Recovery

**Objective**: Verify system handles errors gracefully

**Test Scenarios**:
1. **Invalid connection string**
   - Expected: Clear error message, graceful exit
   
2. **Database not found**
   - Expected: Connection error reported, no crash
   
3. **Insufficient permissions**
   - Expected: Permission error logged, partial results saved
   
4. **Interrupted test (Ctrl+C)**
   - Expected: Monitoring stops cleanly, partial results saved

**Success Criteria**:
-   No unhandled exceptions
-   Meaningful error messages
-   Partial results preserved

---

### TC-014: Statistical Accuracy

**Objective**: Validate statistical calculations are correct

**Test Steps**:
1. Run load test
2. Export results to Excel
3. Manually calculate:
   - Average response time
   - Median response time
   - 95th percentile
   - 99th percentile
   - Throughput
4. Compare with tool output

**Expected Results**:
- Manual calculations match tool output (±0.5%)
- Percentiles correctly calculated
- Throughput formula accurate

**Success Criteria**:
-   <1% variance from manual calculations
-   All statistics present in summary

---

## Performance Benchmarks

### Expected Response Times (Baseline)

| Operation Type | Average | P95 | P99 | Max Acceptable |
|---------------|---------|-----|-----|----------------|
| SELECT TOP 100 | <30ms | <50ms | <80ms | 100ms |
| SELECT BY ID | <10ms | <20ms | <40ms | 50ms |
| SELECT WITH JOIN | <40ms | <70ms | <100ms | 150ms |
| SELECT COUNT | <20ms | <40ms | <60ms | 80ms |
| INSERT | <50ms | <100ms | <150ms | 200ms |
| UPDATE | <60ms | <120ms | <180ms | 250ms |
| DELETE | <40ms | <80ms | <120ms | 150ms |

### Resource Utilization Thresholds

| Metric | Normal | Warning | Critical |
|--------|--------|---------|----------|
| CPU Usage | <50% | 50-80% | >80% |
| Memory | <2GB | 2-4GB | >4GB |
| Active Connections | <100 | 100-200 | >200 |
| Lock Waits/sec | <10 | 10-50 | >50 |
| Deadlocks | 0 | 1-5 | >5 |

---

## Test Execution Checklist

### Before Testing
- [ ] SQL Server is running (remote server: 10.134.77.68:1433)
- [ ] Database exists (BookStore-Master)
- [ ] ODBC Driver 17 or 18 for SQL Server installed
- [ ] Python 3.6+ installed
- [ ] pyodbc package installed (`pip install -r requirements.txt`)
- [ ] Sufficient disk space for results
- [ ] Network connectivity to remote SQL Server
- [ ] SQL authentication credentials valid (testuser)

### During Testing
- [ ] Monitor console output for errors
- [ ] Check CPU/Memory on server
- [ ] Observe response time trends
- [ ] Note any warnings or failures

### After Testing
- [ ] Review load_test CSV file
- [ ] Analyze summary statistics
- [ ] Check monitoring metrics
- [ ] Compare against benchmarks
- [ ] Document any anomalies
- [ ] Clean up test data (optional)

---

## Test Data Summary

### What Gets Created
- **Genres**: 1 default genre ("General") - created on first run
- **Authors**: 20 records with unique GUIDs (persistent across tests)
  - Includes FirstName, LastName, and AuthorId (GUID)
- **Books**: Variable count based on test configuration
  - Each INSERT operation adds 1 book with Title, Year, Price, Description, GenreId, IssueDate, Rating
  - Each DELETE operation removes 1 test book

### What Gets Cleaned Up
- Running with `--cleanup` removes ALL data from Books, Authors, and Genres tables
- DELETE operations only remove "Performance Test Book" records
- Regular cleanup recommended after major tests

---

## Success Criteria (Overall)

| Criteria | Target | Minimum Acceptable |
|----------|--------|-------------------|
| Success Rate | >99% | >95% |
| Average Response Time | <100ms | <200ms |
| P95 Response Time | <200ms | <500ms |
| Throughput | >50 ops/sec | >20 ops/sec |
| CPU Usage (avg) | <60% | <80% |
| Memory Usage (avg) | <3GB | <5GB |
| Deadlock Count | 0 | <5 |
| Test Completion | 100% | 100% |

---

## Common Issues and Solutions

### Issue 1: High Response Times
**Symptoms**: Average >200ms, P95 >500ms
**Possible Causes**: 
- Insufficient indexing
- Lock contention
- CPU/Memory constraints
**Solution**: Add indexes, reduce concurrency, optimize queries

### Issue 2: Connection Failures
**Symptoms**: Thread connection errors
**Possible Causes**:
- Max connections exceeded
- Connection string invalid
- Server not responding
**Solution**: Check connection limits, verify credentials

### Issue 3: Lock Waits/Deadlocks
**Symptoms**: High lock_waits counter, deadlock errors
**Possible Causes**:
- Concurrent UPDATEs on same records
- Long-running transactions
**Solution**: Reduce UPDATE concurrency, implement retry logic

### Issue 4: Memory Growth
**Symptoms**: Memory usage continuously increases
**Possible Causes**:
- Connection leaks
- Large result sets
- Transaction log growth
**Solution**: Verify connections close, limit result sizes

---

## Reporting Results

### Key Metrics to Report
1. **Test Configuration** (connections, operations, duration)
2. **Success Rate** (%)
3. **Response Times** (avg, median, P95, P99)
4. **Throughput** (operations/second)
5. **Resource Utilization** (CPU, Memory peaks)
6. **Error Summary** (if any)
7. **Recommendations** (based on findings)

### Report Template
```
Test Date: [DATE]
Configuration: [X] connections, [Y] operations, [Z] test type
Duration: [N] seconds
Total Operations: [TOTAL]

Results:
- Success Rate: [%]
- Avg Response Time: [X]ms
- P95 Response Time: [Y]ms
- Throughput: [Z] ops/sec

Resource Usage:
- CPU: [X]% avg, [Y]% max
- Memory: [X]GB avg, [Y]GB max
- Connections: [X] avg, [Y] max

Observations:
[Key findings]

Recommendations:
[Actions to take]
```

---

## Conclusion

This test suite provides comprehensive coverage of database performance testing scenarios across **6 main business tables**. By executing these test cases, you can:

- Validate database performance under various loads across all tables
- Identify bottlenecks and optimization opportunities in multi-table scenarios
- Verify foreign key constraint performance
- Test referential integrity under concurrent load
- Assess scalability with complex table relationships
- Monitor cross-table transaction behavior

### Test Coverage Summary

| Table | Operations Tested | FK Relationships | Test Cases |
|-------|------------------|------------------|------------|
| **Authors** | INSERT (seed), SELECT | Parent to Books | TC-002, TC-003, TC-012e |
| **Books** | SELECT, INSERT, UPDATE, DELETE | Child of Authors/Genres, Parent to Stocks | TC-003, TC-005-008, TC-012a |
| **Genres** | INSERT (seed), SELECT | Parent to Books | TC-002, TC-003 |
| **Customers** | SELECT, INSERT, UPDATE, DELETE | Parent to Rentals | TC-003, TC-012a, TC-012b |
| **Rentals** | SELECT, INSERT, UPDATE | Child of Customers/Stocks | TC-003, TC-012a, TC-012c, TC-012e |
| **Stocks** | SELECT, INSERT, UPDATE | Child of Books, Parent to Rentals | TC-003, TC-012a, TC-012d, TC-012e |

### Operation Distribution in Mixed Tests

When running Mixed test type, operations are weighted as follows:
- **Books**: 40% (primary table with full CRUD)
- **Customers**: 25% (active user management)
- **Rentals**: 20% (transaction processing)
- **Stocks**: 15% (inventory management)

### Key Performance Indicators

**Target Metrics**:
- SELECT operations: < 10ms average
- INSERT operations: < 50ms average  
- UPDATE operations: < 75ms average
- DELETE operations: < 100ms average
- Overall success rate: > 85% under normal load
- FK constraint validation: 100% enforcement

**Resource Thresholds**:
- CPU utilization: < 80% sustained
- Memory usage: Stable, no leaks
- Connection count: < configured max
- Lock waits: < 5% of operations
- Deadlocks: 0 (zero tolerance)

### Typical Test Workflow

```bash
# 1. Clean database
python run_and_monitor_db_test.py --env target --cleanup

# 2. Run comprehensive load test
python run_and_monitor_db_test.py --env target -c 20 -o 100 -t Mixed -d 120

# 3. Review results
# - Check database_test_results/load_test_*.csv
# - Review database_test_results/summary_*.txt
# - Analyze database_test_results/metrics_*.csv

# 4. Run specific table tests if needed
python run_and_monitor_db_test.py --env target -c 10 -o 50 -t Mixed
```

### Version History
- **v1.0** (Initial): Basic Books testing only
- **v2.0** (Current): Comprehensive 6-table testing with FK validation, multi-table operations, and referential integrity testing

---

**END OF TEST CASES DOCUMENT**
- Establish performance baselines
- Monitor system health during load
- Generate data-driven performance reports

Regular execution of these tests ensures database reliability and helps maintain performance SLAs.
