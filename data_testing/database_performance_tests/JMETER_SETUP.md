# JMeter PetClinic Database Performance Testing Setup

## Overview
This setup enables direct database performance testing using JMeter's JDBC samplers to test PostgreSQL database operations across all PetClinic tables (owners, pets, vets, visits, types, specialties, vet_specialties).

## Prerequisites

### 1. Install JMeter
Download and install Apache JMeter from: https://jmeter.apache.org/download_jmeter.cgi

**Windows:**
```powershell
# Download JMeter 5.6.3
# Extract to C:\Tools\apache-jmeter-5.6.3
# Add to PATH
$env:PATH += ";C:\Tools\apache-jmeter-5.6.3\bin"
```

### 2. Download PostgreSQL JDBC Driver

**Required:** PostgreSQL JDBC Driver

Download from: https://jdbc.postgresql.org/download/

**Installation Steps:**
1. Download `postgresql-42.7.1.jar` (or latest version)
2. Place the JAR file in JMeter's `lib` directory:
   - Windows: `C:\Tools\apache-jmeter-5.6.3\lib\`
   - Linux: `/opt/apache-jmeter-5.6.3/lib/`

**Quick Download:**
```powershell
# Create lib directory if not exists
New-Item -ItemType Directory -Force -Path "C:\Tools\apache-jmeter-5.6.3\lib"

# Download PostgreSQL JDBC driver
Invoke-WebRequest -Uri "https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.1/postgresql-42.7.1.jar" -OutFile "C:\Tools\apache-jmeter-5.6.3\lib\postgresql-42.7.1.jar"
```

### 3. Verify Installation
```powershell
jmeter --version
```

## Test Files

### JMeter Test Plan
- **JMeter_DB_Mixed_Operations.jmx** - Mixed operations across all PetClinic tables with weighted distribution

### Configuration
Database connection settings are configured in the test plan:
- **Server:** 10.134.77.68:5432
- **Database:** petclinic
- **Username:** postgres
- **Password:** (configured in db_config.json)
- **Driver:** org.postgresql.Driver

These values match the `db_config.json` "target" environment.

## Test Plan Structure

### Thread Groups (Weighted Distribution)
1. **Owners Operations (30%)** - 50 threads × 10 loops = 500 operations
   - SELECT All, SELECT by ID, SELECT by City, COUNT
   - INSERT, UPDATE, DELETE

2. **Pets Operations (30%)** - 50 threads × 10 loops = 500 operations
   - SELECT All with Owner, SELECT by Owner, SELECT by Type
   - INSERT, UPDATE, DELETE

3. **Visits Operations (25%)** - 50 threads × 10 loops = 500 operations
   - SELECT Recent, SELECT by Pet, SELECT by Vet
   - INSERT, UPDATE, DELETE

4. **Vets Operations (15%)** - 50 threads × 10 loops = 500 operations
   - SELECT All with Specialties, SELECT by Specialty
   - INSERT, UPDATE, DELETE

**Total Operations:** ~2000

### JDBC Connection Pool
- **Pool Size:** 20 connections
- **Timeout:** 10 seconds
- **Connection Properties:** ssl=false

## Running Tests

### GUI Mode (Testing/Debugging)
```powershell
jmeter -t JMeter_DB_Mixed_Operations.jmx
```

### Command Line Mode (Performance Testing)
```powershell
# Create results directory
New-Item -ItemType Directory -Force -Path "jmeter_results"

# Run test
jmeter -n -t JMeter_DB_Mixed_Operations.jmx `
  -l jmeter_results/results.jtl `
  -j jmeter_results/jmeter.log `
  -e -o jmeter_results/html_report
```

### With Custom Parameters
```powershell
# Override database settings
jmeter -n -t JMeter_DB_Mixed_Operations.jmx `
  -JDB_SERVER=10.134.77.68 `
  -JDB_PORT=5432 `
  -JDB_NAME=petclinic `
  -JDB_USER=postgres `
  -JDB_PASSWORD="your_password" `
  -l jmeter_results/results.jtl `
  -e -o jmeter_results/html_report
```

## Using Python Script

Run the automated script that prepares the database and executes JMeter:

```powershell
python run_and_monitor_db_test.py --env target
```

Options:
```powershell
# Specify environment
python run_and_monitor_db_test.py --env target

# Skip profiling (faster)
python run_and_monitor_db_test.py --env target --no-profiling

# Skip database seeding
python run_and_monitor_db_test.py --env target --no-seed

# Cleanup only
python run_and_monitor_db_test.py --env target --cleanup

# Custom timeout
python run_and_monitor_db_test.py --env target --timeout 3600
```

## Test Operations

### Owners Table Operations
- **SELECT All:** Retrieve owners ordered by last name
- **SELECT by ID:** Find owner by random ID
- **SELECT by City:** Filter owners by city
- **COUNT:** Total owners in database
- **INSERT:** Add new owner
- **UPDATE:** Modify owner contact information
- **DELETE:** Remove owner (cascades to pets/visits)

### Pets Table Operations
- **SELECT All with Owner:** Retrieve pets with owner information
- **SELECT by Owner:** Find all pets for specific owner
- **SELECT by Type:** Filter pets by type (cat, dog, etc.)
- **COUNT:** Total pets
- **INSERT:** Add new pet linked to owner
- **UPDATE:** Modify pet name or type
- **DELETE:** Remove pet (cascades to visits)

### Visits Table Operations
- **SELECT Recent:** Recent 100 visits
- **SELECT by Pet:** Visits for specific pet
- **SELECT by Vet:** Visits handled by specific vet
- **COUNT:** Total visits
- **INSERT:** Add new visit record
- **UPDATE:** Modify visit description
- **DELETE:** Remove visit record

### Vets Table Operations
- **SELECT All with Specialties:** Vets with their specializations
- **SELECT by Specialty:** Vets with specific specialty
- **COUNT:** Total vets
- **INSERT:** Add new vet
- **UPDATE:** Modify vet information
- **DELETE:** Remove vet (cascades to visits/vet_specialties)

## Viewing Results

### HTML Report
After test completes, open:
```
jmeter_results/html_report/index.html
```

### JTL File Analysis
Use JMeter GUI to analyze:
```powershell
jmeter -g jmeter_results/results.jtl -o jmeter_results/analysis_report
```

## Key Metrics

Monitor these metrics in the reports:
- **Throughput:** Operations per second
- **Response Time:** Average, Median, 90th, 95th, 99th percentile
- **Error Rate:** Percentage of failed operations
- **Concurrent Users:** Thread count
- **Connection Pool:** Utilization

## Troubleshooting

### Error: Cannot load JDBC driver
**Solution:** Ensure `postgresql-*.jar` is in JMeter's `lib` directory

### Error: Authentication failed
**Solution:** Verify credentials in test plan match `db_config.json`

### Error: Cannot connect to database
**Solution:** Check database name and server connectivity, verify port 5432

### Low Performance
**Solution:** 
- Increase connection pool size
- Reduce thread count or loop count
- Check network latency
- Monitor server resources
- Run VACUUM ANALYZE on PostgreSQL

## Comparison with Python Script

| Feature | JMeter | Python (run_and_monitor_db_test.py) |
|---------|--------|--------------------------------------|
| Thread Count | 50 per group (200 total) | Configurable (default 50) |
| Total Operations | ~2000 | Configurable |
| Distribution | 30/30/25/15% | Configurable |
| Monitoring | Via listeners | Real-time system metrics |
| Reporting | HTML dashboard | CSV + graphs + text summary |
| Setup Complexity | Medium (JDBC driver) | Low (Python packages) |
| Execution | JMeter CLI | Python script |

## Best Practices

1. **Always seed the database** before running tests
2. **Run in non-GUI mode** for performance testing
3. **Monitor server resources** during test execution
4. **Use connection pooling** to simulate realistic load
5. **Cleanup test data** after completion
6. **Compare results** with baseline metrics
7. **Run VACUUM ANALYZE** on PostgreSQL before/after tests

## Next Steps

1. Install JMeter and PostgreSQL JDBC driver
2. Run test in GUI mode to verify connectivity
3. Execute full test in CLI mode
4. Analyze HTML report
5. Compare with Python script results
6. Tune parameters for your requirements
