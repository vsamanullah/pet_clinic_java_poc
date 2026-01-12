# PetClinic Database Performance Testing Suite

Comprehensive database performance testing tool for PostgreSQL PetClinic database using JMeter JDBC testing with system performance profiling.

## Features

- **JMeter-Based Testing**: Industry-standard performance testing with PostgreSQL JDBC
- **System Performance Monitoring**: Real-time CPU, Memory, Disk, and Network metrics (Windows typeperf)
- **Automatic Database Setup**: Clean, seed, and prepare test data automatically (8,056 records)
- **Performance Graphs**: Auto-generated 2×2 grid visualization of system metrics during tests
- **Multiple Thread Groups**: Owners (30%), Pets (30%), Visits (25%), Vets (10%) operations
- **CRUD Operations**: Full Create, Read, Update, Delete operations with randomization
- **Flexible Configuration**: Use predefined environments from db_config.json
- **HTML Reports**: JMeter automatically generates detailed HTML reports with charts and statistics

## Prerequisites

### Required Software
- **Python 3.8+** for test runner script
- **Apache JMeter 5.6.3** or higher
- **PostgreSQL JDBC Driver** (postgresql-42.7.1.jar) ✅ **INSTALLED**
- **PostgreSQL 9.6+** database accessible
- **Windows OS** (recommended for performance monitoring)

**JMeter Setup:**
```powershell
# Add JMeter to PATH (Windows)
$env:PATH += ';C:\Tools\apache-jmeter-5.6.3\bin'

# PostgreSQL JDBC driver - ALREADY INSTALLED
# Location: C:\Tools\apache-jmeter-5.6.3\lib\postgresql-42.7.1.jar
# Downloaded from: https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.1/

# To verify installation:
Test-Path "C:\Tools\apache-jmeter-5.6.3\lib\postgresql-42.7.1.jar"
```

**Note:** PostgreSQL JDBC driver has been successfully installed. Restart JMeter if it was already running to load the new driver.

See [JMETER_SETUP.md](JMETER_SETUP.md) for detailed instructions.

## Configuration

Database environments are configured in `../../db_config.json`:

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
    "target": { ... },
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

## Required Python Packages

Install dependencies for the test runner:
```bash
pip install psycopg2-binary pandas matplotlib
```

- **psycopg2-binary**: PostgreSQL database connection and seeding
- **pandas**: Performance data processing
- **matplotlib**: Performance graph generation

## Usage

### Standard JMeter Test with Profiling

Runs complete test with cleanup, seeding, and system monitoring:
```bash
python run_and_monitor_db_test.py --env target
```

### Quick Test (No Profiling)

Faster execution without system performance monitoring:
```bash
python run_and_monitor_db_test.py --env target --no-profiling
```

### Skip Database Seeding

Reuse existing data (saves ~10-15 seconds):
```bash
python run_and_monitor_db_test.py --env target --no-seed
```

### Database Cleanup Only

Clean all tables and exit (no test execution):
```bash
python run_and_monitor_db_test.py --env target --cleanup
```

### Custom Timeout

Extend JMeter test timeout (default: 1800 seconds):
```bash
python run_and_monitor_db_test.py --env target --timeout 3600
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--env` | Database environment (source/target/local) | target |
| `--config` | Path to db_config.json | ../../db_config.json |
| `--cleanup` | Clean database and exit | False |
| `--no-seed` | Skip database seeding | False |
| `--no-profiling` | Skip system performance monitoring | False |
| `--timeout` | JMeter test timeout in seconds | 1800 |

## Test Operations

### JMeter Test Plan Structure

The test runs **4 parallel thread groups** for 60 seconds each with 2-second delays between operations:

#### 1. Owners Operations - CRUD (30%)
- **Thread Count**: 1 user, 60-second duration
- **Operations** (randomized):
  - SELECT all owners (LIMIT 50)
  - SELECT by random ID
  - COUNT owners
  - INSERT new owner (random data)
  - UPDATE existing owner (address, telephone)
  - INSERT then DELETE (transaction test)

#### 2. Pets Operations - CRUD (30%)
- **Thread Count**: 1 user, 60-second duration
- **Operations** (randomized):
  - SELECT all pets (LIMIT 50)
  - SELECT by random ID
  - SELECT with JOIN (pets + owners)
  - COUNT pets
  - INSERT new pet (random owner, type)
  - UPDATE existing pet (name, birth_date)
  - INSERT then DELETE (transaction test)

#### 3. Visits Operations - CRUD (25%)
- **Thread Count**: 1 user, 60-second duration
- **Operations** (randomized):
  - SELECT all visits (LIMIT 100)
  - SELECT by pet ID
  - SELECT with JOIN (visits + pets + owners)
  - COUNT visits
  - INSERT new visit
  - UPDATE visit description
  - INSERT then DELETE (transaction test)

#### 4. Vets Operations - Read Only (10%)
- **Thread Count**: 1 user, 60-second duration
- **Operations** (randomized):
  - SELECT all vets (LIMIT 50)
  - SELECT by random ID
  - SELECT with specialties JOIN
  - COUNT vets
  - SELECT vets with specific specialty

### Database Connection Configuration
- **JDBC Driver**: org.postgresql.Driver
- **Connection Pool**: Max 50 connections
- **Auto-commit**: Enabled
- **Keep-alive**: Enabled
- **Connection Age**: 5000ms
- **Timeout**: 10 seconds
- **SSL**: Required (sslmode=require)

## Output Files

All outputs are saved to `jmeter_results/` directory:

```
jmeter_results/
├── results_YYYYMMDD_HHMMSS.jtl              # Raw JMeter test results (CSV format)
├── report_YYYYMMDD_HHMMSS/                  # HTML dashboard (open index.html in browser)
│   ├── index.html                           # Main dashboard with graphs
│   ├── content/                             # Detailed statistics pages
│   └── sbadmin2-1.0.7/                     # Report theme assets
├── jmeter_YYYYMMDD_HHMMSS.log              # JMeter execution log with summary
├── performance_YYYYMMDD_HHMMSS.csv         # Raw system metrics (Windows typeperf format)
├── performance_YYYYMMDD_HHMMSS.clean.csv   # Cleaned/processed metrics (UTF-8)
└── performance_graphs_YYYYMMDD_HHMMSS.png  # System performance visualization (2×2 grid)
```

## Performance Graphs

When profiling is enabled (JMeter on Windows), the script generates a 2×2 grid of performance graphs:

1. **CPU Usage**: Processor utilization over time with average line
2. **Memory Usage**: Memory commitment percentage with average
3. **Disk I/O**: Read/write operations per second
4. **Network Activity**: Network throughput in MB/s

## Test Database Schema

The script automatically seeds the following test data (8,056 total records):

| Table | Records | Description |
|-------|---------|-------------|
| **types** | 6 | Pet types: cat, dog, lizard, snake, bird, hamster |
| **specialties** | 6 | Vet specialties: radiology, surgery, dentistry, cardiology, dermatology, neurology |
| **owners** | 1,000 | Pet owners with first/last name, address, city, telephone |
| **pets** | 2,000 | Pets linked to owners (name, birth_date, type_id, owner_id) |
| **vets** | 50 | Veterinarians with first/last name |
| **vet_specialties** | ~100 | Many-to-many: vets linked to 1-3 specialties each |
| **visits** | 5,000 | Pet visits with date and description |

### Data Generation Details
- **Names**: 24 first names, 16 last names (random combinations)
- **Addresses**: 12 street names, 10 Wisconsin cities
- **Pets**: 16 pet names, birth dates 2010-2023
- **Visits**: 10 description types (checkup, vaccination, surgery, etc.), dates 2020-2024
- **Batched Inserts**: 100-200 records per batch for performance

## System Performance Monitoring

When profiling is enabled (Windows only), the script monitors system metrics using `typeperf`:

### Metrics Collected (1-second intervals)
- **CPU**: `\Processor(_Total)\% Processor Time`
- **Memory**: 
  - `\Memory\Available MBytes`
  - `\Memory\% Committed Bytes In Use`
- **Disk I/O**: 
  - `\PhysicalDisk(_Total)\Disk Reads/sec`
  - `\PhysicalDisk(_Total)\Disk Writes/sec`
- **Network**: `\Network Interface(*)\Bytes Total/sec` (all adapters)

### Performance Graph Layout

Auto-generated 2×2 grid with 4 subplots:
1. **Top-Left**: CPU Usage (%) with average line
2. **Top-Right**: Memory Usage (%) with average line  
3. **Bottom-Left**: Disk I/O (Reads/Writes per second)
4. **Bottom-Right**: Network Activity (MB/s total)

## Troubleshooting

### JMeter Not Found
```
Error: JMeter not found in PATH
Solution: Install JMeter and add bin directory to PATH
  Windows: $env:PATH += ';C:\Tools\apache-jmeter-5.6.3\bin'
  See JMETER_SETUP.md for full instructions
```

### JDBC Connection Failed
```
Error: Cannot create PoolableConnectionFactory
Solution: 
  1. Verify PostgreSQL JDBC driver is in JMeter lib/ folder
  2. Check database connection parameters in db_config.json
  3. Ensure database is accessible and credentials are correct
  4. Restart JMeter after adding JDBC driver
```

### Python Package Missing
```
Error: ModuleNotFoundError: No module named 'psycopg2'
Solution: Install required packages
  pip install psycopg2-binary pandas matplotlib
```

### Graph Generation Failed
```
Error: Graphing libraries not available
Solution: Install matplotlib and pandas
  pip install pandas matplotlib
```

### Performance Monitoring Not Working
```
Cause: Not running on Windows or typeperf not available
Solution: Use --no-profiling flag or run on Windows with typeperf
  python run_and_monitor_db_test.py --env target --no-profiling
```

## Workflow Examples

### Complete Test Run (Recommended)
```bash
# Full test with cleanup, seeding, profiling
python run_and_monitor_db_test.py --env target
```
**Execution steps:**
1. Check JMeter prerequisites
2. Cleanup database (delete all records)
3. Seed test data (8,056 records)
4. Start performance monitoring (typeperf)
5. Run JMeter test (60 seconds, 4 thread groups)
6. Stop monitoring
7. Process performance data and generate graphs
8. Display results summary

### Quick Test (Skip Profiling)
```bash
# Faster execution without system metrics
python run_and_monitor_db_test.py --env target --no-profiling
```

### Reuse Existing Data
```bash
# Skip cleanup and seeding (saves ~15 seconds)
python run_and_monitor_db_test.py --env target --no-seed --no-profiling
```

### Database Maintenance
```bash
# Cleanup before/after testing
python run_and_monitor_db_test.py --env target --cleanup
```

### Test Different Environments
```bash
# Source environment
python run_and_monitor_db_test.py --env source

# Local environment
python run_and_monitor_db_test.py --env local

# Target environment (default)
python run_and_monitor_db_test.py --env target
```

## Test Execution Flow

The test runner follows a 7-step process:

### Step 1: Check Prerequisites
- Verify JMeter is installed and in PATH
- Display JMeter version
- Validate PostgreSQL JDBC driver

### Step 2: Clean Database
- Delete records from all tables in correct order:
  1. visits
  2. vet_specialties  
  3. pets
  4. owners
  5. vets
  6. specialties
  7. types

### Step 3: Seed Database (unless --no-seed)
- Insert test data in correct order (respecting foreign keys)
- Use batched inserts for performance
- Display progress for large tables

### Step 4: Start Performance Monitoring (unless --no-profiling)
- Launch Windows typeperf in background
- Monitor CPU, Memory, Disk, Network at 1-second intervals
- Save to timestamped CSV file

### Step 5: Run JMeter Test
- Execute test plan with environment-specific DB parameters
- Generate JTL results file
- Create HTML dashboard report
- Write execution log with summary

### Step 6: Stop Performance Monitoring
- Gracefully terminate typeperf process
- Wait for final metrics to be written

### Step 7: Process and Consolidate Results
- Clean CSV (convert UTF-16 to UTF-8, remove PDH headers)
- Generate performance graphs (2×2 grid)
- Display summary of all output files

## Best Practices

1. **Always cleanup before major tests**: Use `--cleanup` to ensure clean baseline data
2. **Use profiling for analysis**: Enable system monitoring (default) to understand resource usage
3. **Archive HTML reports**: Save JMeter HTML reports for historical comparison
4. **Test different environments**: Run against source, target, and local to compare
5. **Check graph trends**: Review performance graphs for bottlenecks (CPU spikes, memory leaks)
6. **Monitor JMeter log**: Check log file for connection errors or timeouts
7. **Adjust timeout if needed**: Use `--timeout` for longer test durations or slow networks

## Support

For detailed JMeter setup, see [JMETER_SETUP.md](JMETER_SETUP.md)

For test case documentation, see [test_cases.md](test_cases.md)

## License

Internal testing tool for PetClinic PostgreSQL database performance validation.
