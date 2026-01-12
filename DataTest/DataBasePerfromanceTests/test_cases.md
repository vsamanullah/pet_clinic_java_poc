# PetClinic Database Performance Testing Suite - Test Cases Documentation

## Overview

This document describes the test cases for the **PetClinic Database Performance Testing Tool**. The tool is a **JMeter wrapper** that automates database performance testing using Apache JMeter with JDBC, including optional system performance profiling.

### Testing Approach

**JMeter JDBC Load Testing**
- Industry-standard performance testing via Apache JMeter
- Direct JDBC connection to PostgreSQL 9.6.24
- System-level performance profiling (CPU, Memory, Disk, Network) via Windows typeperf
- Automated database cleanup and seeding
- 50 threads per table group, 10-minute test duration, 2-second pacing
- Auto-generated HTML reports with detailed statistics and charts
- Ideal for: Enterprise-grade benchmarking, stakeholder reporting, repeatable tests

### Command Examples
```bash
# Basic test with profiling
python run_and_monitor_db_test.py --env target

# Test without system profiling (faster)
python run_and_monitor_db_test.py --env target --no-profiling

# Cleanup database before test
python run_and_monitor_db_test.py --env target --cleanup

# Skip database seeding (use existing data)
python run_and_monitor_db_test.py --env target --no-seed
```

### Execution Steps
<To be updated>

### Tables Under Test
- **owners** - Pet owners with contact information
- **pets** - Pet records linked to owners
- **vets** - Veterinarian information
- **visits** - Visit records linking pets to vets
- **types** - Pet type categories (cat, dog, bird, etc.)
- **specialties** - Veterinary specializations
- **vet_specialties** - Many-to-many relationship between vets and specialties

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
   - Cross-table operations (visits → pets/vets)
   - Foreign key constraint performance
   - Complex JOIN queries
   - Transaction isolation under load

5. **System Health Monitoring**
   - PostgreSQL CPU utilization
   - Memory consumption patterns
   - Active connection tracking
   - Transaction rate monitoring
   - Lock wait and deadlock detection

---

## Test Environment

### Database Schema
```
Database: petclinic

Tables:
1. owners (Parent Table)
   - id (SERIAL, PRIMARY KEY)
   - first_name (VARCHAR(30))
   - last_name (VARCHAR(30))
   - address (VARCHAR(255))
   - city (VARCHAR(80))
   - telephone (VARCHAR(20))

2. types (Lookup Table)
   - id (SERIAL, PRIMARY KEY)
   - name (VARCHAR(80))

3. specialties (Lookup Table)
   - id (SERIAL, PRIMARY KEY)
   - name (VARCHAR(80))

4. pets (Child Table)
   - id (SERIAL, PRIMARY KEY)
   - name (VARCHAR(30))
   - birth_date (DATE)
   - type_id (INTEGER, FK → types.id)
   - owner_id (INTEGER, FK → owners.id)

5. vets (Parent Table)
   - id (SERIAL, PRIMARY KEY)
   - first_name (VARCHAR(30))
   - last_name (VARCHAR(30))

6. vet_specialties (Junction Table)
   - vet_id (INTEGER, FK → vets.id)
   - specialty_id (INTEGER, FK → specialties.id)
   - PRIMARY KEY (vet_id, specialty_id)

7. visits (Transaction Table)
   - id (SERIAL, PRIMARY KEY)
   - pet_id (INTEGER, FK → pets.id)
   - visit_date (DATE)
   - description (VARCHAR(255))
   - vet_id (INTEGER, FK → vets.id)
```

### Configuration
- **Database**: PostgreSQL 9.6.24
- **Driver**: psycopg2-binary (Python), PostgreSQL JDBC (JMeter)
- **Test Duration**: 10 minutes per test
- **Thread Count**: 50 concurrent threads per table group
- **Pacing**: 2-second delay between iterations
- **Monitoring Interval**: 1 second

### Test Data Volume
```
Seeded Data:
- 1,000 owners
- 2,000 pets
- 6 pet types
- 50 vets
- 6 specialties
- ~100 vet-specialty associations
- 5,000 visits
```

---

## Test Cases

### TC-01: Owners Table Performance

**Objective**: Measure CRUD operation performance on the owners table

**Test Configuration**:
- 50 concurrent threads
- 10-minute duration
- Mixed operations: 40% SELECT, 30% INSERT, 20% UPDATE, 10% DELETE

**Operations**:
1. **SELECT All Owners**
   ```sql
   SELECT id, first_name, last_name, address, city, telephone 
   FROM owners 
   ORDER BY last_name, first_name
   LIMIT 100
   ```

2. **SELECT Owner by ID**
   ```sql
   SELECT * FROM owners WHERE id = ${random_id}
   ```

3. **SELECT Owners by City**
   ```sql
   SELECT * FROM owners WHERE city = '${random_city}'
   ```

4. **INSERT New Owner**
   ```sql
   INSERT INTO owners (first_name, last_name, address, city, telephone)
   VALUES ('${first_name}', '${last_name}', '${address}', '${city}', '${phone}')
   ```

5. **UPDATE Owner Contact**
   ```sql
   UPDATE owners 
   SET address = '${new_address}', telephone = '${new_phone}'
   WHERE id = ${random_id}
   ```

6. **DELETE Owner** (with cascade cleanup)
   ```sql
   DELETE FROM visits WHERE pet_id IN (SELECT id FROM pets WHERE owner_id = ${random_id});
   DELETE FROM pets WHERE owner_id = ${random_id};
   DELETE FROM owners WHERE id = ${random_id}
   ```

**Expected Results**:
- SELECT queries: < 50ms avg response time
- INSERT operations: < 100ms avg response time
- UPDATE operations: < 80ms avg response time
- DELETE operations: < 200ms avg response time (cascades to pets/visits)
- Error rate: < 1%

---

### TC-02: Pets Table Performance

**Objective**: Test performance of pet records with foreign key relationships to owners and types

**Test Configuration**:
- 50 concurrent threads
- 10-minute duration
- Mixed operations: 50% SELECT, 25% INSERT, 20% UPDATE, 5% DELETE

**Operations**:
1. **SELECT All Pets with Owner Info**
   ```sql
   SELECT p.id, p.name, p.birth_date, t.name as type, 
          o.first_name || ' ' || o.last_name as owner_name
   FROM pets p
   JOIN owners o ON p.owner_id = o.id
   JOIN types t ON p.type_id = t.id
   ORDER BY p.name
   LIMIT 100
   ```

2. **SELECT Pets by Owner**
   ```sql
   SELECT p.*, t.name as type_name
   FROM pets p
   JOIN types t ON p.type_id = t.id
   WHERE p.owner_id = ${random_owner_id}
   ```

3. **SELECT Pets by Type**
   ```sql
   SELECT p.*, o.last_name as owner_last_name
   FROM pets p
   JOIN owners o ON p.owner_id = o.id
   WHERE p.type_id = ${random_type_id}
   ```

4. **INSERT New Pet**
   ```sql
   INSERT INTO pets (name, birth_date, type_id, owner_id)
   VALUES ('${pet_name}', '${birth_date}', ${type_id}, ${owner_id})
   ```

5. **UPDATE Pet Information**
   ```sql
   UPDATE pets 
   SET name = '${new_name}', type_id = ${new_type_id}
   WHERE id = ${random_pet_id}
   ```

6. **DELETE Pet** (with visit cleanup)
   ```sql
   DELETE FROM visits WHERE pet_id = ${random_pet_id};
   DELETE FROM pets WHERE id = ${random_pet_id}
   ```

**Expected Results**:
- Simple SELECT: < 50ms
- JOIN queries: < 100ms
- INSERT with FK validation: < 120ms
- UPDATE operations: < 80ms
- DELETE with cascade: < 150ms
- FK constraint violations: 0

---

### TC-03: Vets and Specialties Performance

**Objective**: Test veterinarian records and many-to-many specialty relationships

**Test Configuration**:
- 50 concurrent threads
- 10-minute duration
- Mixed operations: 50% SELECT, 30% INSERT, 15% UPDATE, 5% DELETE

**Operations**:
1. **SELECT All Vets with Specialties**
   ```sql
   SELECT v.id, v.first_name, v.last_name,
          STRING_AGG(s.name, ', ') as specialties
   FROM vets v
   LEFT JOIN vet_specialties vs ON v.id = vs.vet_id
   LEFT JOIN specialties s ON vs.specialty_id = s.id
   GROUP BY v.id, v.first_name, v.last_name
   ORDER BY v.last_name
   ```

2. **SELECT Vets by Specialty**
   ```sql
   SELECT v.*
   FROM vets v
   JOIN vet_specialties vs ON v.id = vs.vet_id
   WHERE vs.specialty_id = ${specialty_id}
   ```

3. **INSERT New Vet**
   ```sql
   INSERT INTO vets (first_name, last_name)
   VALUES ('${first_name}', '${last_name}')
   ```

4. **ASSIGN Specialty to Vet**
   ```sql
   INSERT INTO vet_specialties (vet_id, specialty_id)
   VALUES (${vet_id}, ${specialty_id})
   ON CONFLICT DO NOTHING
   ```

5. **UPDATE Vet Information**
   ```sql
   UPDATE vets 
   SET first_name = '${new_first}', last_name = '${new_last}'
   WHERE id = ${vet_id}
   ```

6. **DELETE Vet** (with cleanup)
   ```sql
   DELETE FROM visits WHERE vet_id = ${vet_id};
   DELETE FROM vet_specialties WHERE vet_id = ${vet_id};
   DELETE FROM vets WHERE id = ${vet_id}
   ```

**Expected Results**:
- Simple SELECT: < 50ms
- Aggregate queries: < 150ms
- INSERT operations: < 100ms
- Many-to-many inserts: < 120ms
- UPDATE operations: < 80ms
- DELETE with cascade: < 200ms

---

### TC-04: Visits Table Performance (Transaction Workload)

**Objective**: Test high-volume visit transactions with multiple foreign key relationships

**Test Configuration**:
- 50 concurrent threads
- 10-minute duration
- Heavy INSERT focus: 20% SELECT, 50% INSERT, 20% UPDATE, 10% DELETE

**Operations**:
1. **SELECT Recent Visits**
   ```sql
   SELECT v.id, v.visit_date, v.description,
          p.name as pet_name,
          o.last_name as owner_name,
          vt.first_name || ' ' || vt.last_name as vet_name
   FROM visits v
   JOIN pets p ON v.pet_id = p.id
   JOIN owners o ON p.owner_id = o.id
   JOIN vets vt ON v.vet_id = vt.id
   WHERE v.visit_date >= CURRENT_DATE - INTERVAL '30 days'
   ORDER BY v.visit_date DESC
   LIMIT 100
   ```

2. **SELECT Visits by Pet**
   ```sql
   SELECT v.*, vt.first_name || ' ' || vt.last_name as vet_name
   FROM visits v
   JOIN vets vt ON v.vet_id = vt.id
   WHERE v.pet_id = ${pet_id}
   ORDER BY v.visit_date DESC
   ```

3. **SELECT Visits by Vet**
   ```sql
   SELECT v.*, p.name as pet_name, o.last_name as owner_name
   FROM visits v
   JOIN pets p ON v.pet_id = p.id
   JOIN owners o ON p.owner_id = o.id
   WHERE v.vet_id = ${vet_id}
   AND v.visit_date = CURRENT_DATE
   ```

4. **INSERT New Visit**
   ```sql
   INSERT INTO visits (pet_id, visit_date, description, vet_id)
   VALUES (${pet_id}, '${visit_date}', '${description}', ${vet_id})
   ```

5. **UPDATE Visit Description**
   ```sql
   UPDATE visits 
   SET description = '${updated_description}'
   WHERE id = ${visit_id}
   ```

6. **DELETE Visit**
   ```sql
   DELETE FROM visits WHERE id = ${visit_id}
   ```

**Expected Results**:
- Simple SELECT: < 80ms
- Complex JOIN queries: < 150ms
- INSERT with multiple FK checks: < 150ms
- UPDATE operations: < 100ms
- DELETE operations: < 80ms
- Concurrent inserts: No deadlocks

---

### TC-05: Complex Multi-Table Queries

**Objective**: Test performance of complex analytical queries spanning multiple tables

**Test Configuration**:
- 25 concurrent threads
- 10-minute duration
- 100% SELECT operations (read-heavy analytics)

**Operations**:
1. **Owner Statistics Dashboard**
   ```sql
   SELECT o.id, o.first_name, o.last_name, o.city,
          COUNT(DISTINCT p.id) as pet_count,
          COUNT(v.id) as visit_count,
          MAX(v.visit_date) as last_visit
   FROM owners o
   LEFT JOIN pets p ON o.id = p.owner_id
   LEFT JOIN visits v ON p.id = v.pet_id
   GROUP BY o.id, o.first_name, o.last_name, o.city
   ORDER BY visit_count DESC
   LIMIT 50
   ```

2. **Vet Workload Analysis**
   ```sql
   SELECT vt.id, vt.first_name, vt.last_name,
          COUNT(v.id) as total_visits,
          COUNT(DISTINCT v.pet_id) as unique_pets,
          STRING_AGG(DISTINCT s.name, ', ') as specialties
   FROM vets vt
   LEFT JOIN visits v ON vt.id = v.vet_id
   LEFT JOIN vet_specialties vs ON vt.id = vs.vet_id
   LEFT JOIN specialties s ON vs.specialty_id = s.id
   GROUP BY vt.id, vt.first_name, vt.last_name
   ORDER BY total_visits DESC
   ```

3. **Pet Type Distribution**
   ```sql
   SELECT t.name as pet_type,
          COUNT(p.id) as pet_count,
          COUNT(v.id) as visit_count,
          AVG(EXTRACT(YEAR FROM AGE(CURRENT_DATE, p.birth_date))) as avg_age_years
   FROM types t
   LEFT JOIN pets p ON t.id = p.type_id
   LEFT JOIN visits v ON p.id = v.pet_id
   GROUP BY t.id, t.name
   ORDER BY pet_count DESC
   ```

4. **Visit Trends by Month**
   ```sql
   SELECT DATE_TRUNC('month', visit_date) as month,
          COUNT(*) as visit_count,
          COUNT(DISTINCT pet_id) as unique_pets,
          COUNT(DISTINCT vet_id) as vets_involved
   FROM visits
   WHERE visit_date >= CURRENT_DATE - INTERVAL '12 months'
   GROUP BY DATE_TRUNC('month', visit_date)
   ORDER BY month DESC
   ```

5. **Full PetClinic Report**
   ```sql
   SELECT o.first_name || ' ' || o.last_name as owner_name,
          p.name as pet_name,
          t.name as pet_type,
          v.visit_date,
          v.description,
          vt.first_name || ' ' || vt.last_name as vet_name
   FROM visits v
   JOIN pets p ON v.pet_id = p.id
   JOIN owners o ON p.owner_id = o.id
   JOIN types t ON p.type_id = t.id
   JOIN vets vt ON v.vet_id = vt.id
   WHERE v.visit_date >= CURRENT_DATE - INTERVAL '7 days'
   ORDER BY v.visit_date DESC, o.last_name, p.name
   ```

**Expected Results**:
- Simple aggregations: < 200ms
- Multi-table JOINs with GROUP BY: < 300ms
- Complex analytical queries: < 500ms
- No query timeout errors
- Consistent performance under concurrent load

---

### TC-06: Stress Test - High Concurrency

**Objective**: Test database behavior under extreme concurrent load

**Test Configuration**:
- 200 concurrent threads (4x normal load)
- 15-minute duration
- All operations mixed equally

**Scenario**: Simulate peak clinic hours with:
- Multiple receptionists creating/updating owner records
- Vets recording visit information
- Administrative staff running reports
- Online portal users checking appointments

**Monitored Metrics**:
- Connection pool saturation
- Lock wait times
- Deadlock occurrence
- Transaction rollback rate
- Response time degradation curve

**Expected Results**:
- No deadlocks or connection timeouts
- Response time increase: < 3x baseline
- Error rate: < 2%
- All transactions eventually complete
- Database remains responsive

---

### TC-07: Foreign Key Constraint Validation

**Objective**: Verify FK constraint enforcement under load

**Test Configuration**:
- 30 concurrent threads
- 10-minute duration
- Intentional FK violations mixed with valid operations

**Invalid Operations**:
1. Insert pet with non-existent owner_id
2. Insert visit with non-existent pet_id
3. Insert visit with non-existent vet_id
4. Delete owner with existing pets (without cascade)
5. Delete pet with existing visits (without cascade)

**Expected Results**:
- All FK violations properly rejected
- Error messages correctly identify constraint
- Valid operations unaffected by violations
- No orphaned records created
- Transaction rollback works correctly

---

### TC-08: Lookup Table Performance

**Objective**: Test performance of small, frequently-accessed lookup tables

**Test Configuration**:
- 100 concurrent threads
- 10-minute duration
- Read-heavy: 95% SELECT, 5% INSERT

**Operations**:
1. **Cache Test - Repeated Type Lookups**
   ```sql
   SELECT * FROM types ORDER BY name
   ```

2. **Cache Test - Repeated Specialty Lookups**
   ```sql
   SELECT * FROM specialties ORDER BY name
   ```

3. **INSERT New Type** (occasional)
   ```sql
   INSERT INTO types (name) VALUES ('${new_type}')
   ```

4. **INSERT New Specialty** (occasional)
   ```sql
   INSERT INTO specialties (name) VALUES ('${new_specialty}')
   ```

**Expected Results**:
- SELECT on types/specialties: < 10ms (cached)
- High cache hit ratio
- No contention on small tables
- INSERT operations: < 50ms

---

## Performance Baselines

### Acceptable Performance Thresholds

| Operation Type | Target Response Time | Maximum Response Time | Throughput (ops/sec) |
|----------------|---------------------|----------------------|---------------------|
| Simple SELECT  | < 50ms              | < 100ms              | > 1000              |
| Complex JOIN   | < 150ms             | < 300ms              | > 200               |
| INSERT         | < 100ms             | < 200ms              | > 500               |
| UPDATE         | < 80ms              | < 150ms              | > 600               |
| DELETE         | < 100ms             | < 200ms              | > 400               |
| Aggregate Query| < 200ms             | < 500ms              | > 100               |

### System Resource Thresholds

| Resource       | Normal Range | Warning Level | Critical Level |
|----------------|-------------|---------------|----------------|
| CPU Usage      | 30-60%      | 70%           | 85%            |
| Memory Usage   | 40-70%      | 80%           | 90%            |
| Disk I/O       | < 1000 ops/s| 2000 ops/s    | 3000 ops/s     |
| Network        | < 10 MB/s   | 50 MB/s       | 100 MB/s       |
| Active Connections | < 100   | 150           | 200            |

---

## Monitoring & Reporting

### Collected Metrics

1. **JMeter Metrics**
   - Response time (avg, min, max, percentiles)
   - Throughput (transactions/second)
   - Error rate and error types
   - Active threads over time

2. **System Metrics** (Windows typeperf)
   - CPU utilization (% Processor Time)
   - Memory usage (Available MBytes, % Committed Bytes)
   - Disk I/O (Reads/sec, Writes/sec)
   - Network throughput (Bytes Total/sec)

3. **PostgreSQL Metrics** (via queries)
   - Active connections
   - Long-running queries
   - Lock waits
   - Cache hit ratio
   - Transaction rate

### Output Files

```
jmeter_results/
├── results_YYYYMMDD_HHMMSS.jtl          # Raw JMeter results
├── report_YYYYMMDD_HHMMSS/              # HTML report
│   ├── index.html                        # Main dashboard
│   ├── content/graphs/                   # Performance graphs
│   └── content/pages/                    # Detailed statistics
├── performance_YYYYMMDD_HHMMSS.csv      # Raw performance data
├── performance_YYYYMMDD_HHMMSS.clean.csv# Cleaned CSV
└── performance_graphs_YYYYMMDD_HHMMSS.png# Performance charts
```

---

## Troubleshooting Guide

### Common Issues

1. **High Error Rate**
   - **Cause**: FK constraint violations, connection timeouts
   - **Solution**: Check seed data, verify connection pool settings

2. **Slow Response Times**
   - **Cause**: Missing indexes, table scans, lock contention
   - **Solution**: Review query plans, add indexes, adjust isolation level

3. **Connection Failures**
   - **Cause**: max_connections limit, firewall rules
   - **Solution**: Increase PostgreSQL max_connections, check network

4. **Memory Issues**
   - **Cause**: Large result sets, insufficient shared_buffers
   - **Solution**: Add LIMIT clauses, increase PostgreSQL memory settings

5. **Lock Timeouts**
   - **Cause**: Long-running transactions, deadlocks
   - **Solution**: Reduce transaction scope, add proper indexes

### Performance Optimization Tips

1. **Indexes**: Ensure foreign keys have indexes
2. **Connection Pooling**: Use pgBouncer for connection management
3. **Query Optimization**: Avoid SELECT *, use appropriate JOINs
4. **Vacuum**: Regular VACUUM ANALYZE for statistics
5. **Monitoring**: Enable pg_stat_statements for query analysis

---

## Conclusion

This test suite provides comprehensive coverage of:
- All 7 PetClinic tables
- CRUD operations under concurrent load
- Foreign key constraint validation
- Complex multi-table queries
- System resource monitoring
- Stress testing and edge cases

Results from these tests inform database tuning, capacity planning, and application optimization decisions for the PetClinic application.
