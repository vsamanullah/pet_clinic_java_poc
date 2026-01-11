# PetClinic Database Performance Testing Suite

Comprehensive database performance testing tool for PostgreSQL PetClinic database, supporting both Python-based load testing and JMeter JDBC testing with system performance profiling.

## Features

- **Dual Testing Modes**: Choose between Python (psycopg2) or JMeter (PostgreSQL JDBC) testing
- **System Performance Monitoring**: Real-time CPU, Memory, Disk, and Network metrics (Windows)
- **Automatic Database Setup**: Clean, seed, and prepare test data automatically
- **Performance Graphs**: Auto-generated visualization of system metrics during tests
- **Multiple Test Types**: Owners, Pets, Vets, Visits operations (CRUD)
- **Flexible Configuration**: Use predefined environments or custom connection strings
- **HTML Reports**: JMeter generates detailed HTML reports with charts

## Prerequisites

### For Python Testing (Default)
- Python 3.8+
- Required packages:
  ```bash
  pip install psycopg2-binary pandas matplotlib
  ```
- PostgreSQL 9.6+ accessible

### For JMeter Testing
- Apache JMeter 5.6.3 or higher
- PostgreSQL JDBC Driver (postgresql-42.7.1.jar) ✅ **INSTALLED**
- JMeter must be in system PATH

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

## Usage

### Python Load Testing (Default)

Basic test with 10 concurrent connections, 50 operations each:
```bash
python run_and_monitor_db_test.py --env target -c 10 -o 50
```

Extended test with 120-second monitoring:
```bash
python run_and_monitor_db_test.py --env target -c 20 -o 100 -d 120
```

Test specific operations:
```bash
python run_and_monitor_db_test.py --env source -c 5 -o 100 -t Owners
python run_and_monitor_db_test.py --env source -c 5 -o 100 -t Pets
python run_and_monitor_db_test.py --env source -c 5 -o 100 -t Visits
python run_and_monitor_db_test.py --env source -c 5 -o 100 -t Read
python run_and_monitor_db_test.py --env source -c 5 -o 100 -t Write
```

### JMeter Testing

Standard JMeter test with profiling:
```bash
python run_and_monitor_db_test.py --tool jmeter --env target
```

JMeter test without system profiling (faster):
```bash
python run_and_monitor_db_test.py --tool jmeter --env target --no-profiling
```

Skip database seeding (reuse existing data):
```bash
python run_and_monitor_db_test.py --tool jmeter --env target --no-seed
```

### Database Maintenance

Cleanup database only:
```bash
python run_and_monitor_db_test.py --env target --cleanup
```

## Command-Line Options

### Common Options
| Option | Description | Default |
|--------|-------------|---------|
| `--env, --environment` | Database environment (source/target/local) | None |
| `--config` | Path to db_config.json | ../db_config.json |
| `--cleanup` | Clean database and exit | False |
| `--tool` | Testing tool (python/jmeter) | python |
| `--no-seed` | Skip database seeding | False |

### Python Testing Options
| Option | Description | Default |
|--------|-------------|---------|
| `-c, --connections` | Concurrent connections | 20 |
| `-o, --operations` | Operations per connection | 100 |
| `-t, --test-type` | Test type (Mixed/Books/Customers/Read/Write/etc.) | Mixed |
| `-d, --duration` | Monitoring duration (seconds) | 120 |

### JMeter Testing Options
| Option | Description | Default |
|--------|-------------|---------|
| `--no-profiling` | Skip system performance monitoring | False |

## Test Operations

### Python Testing
- **Books**: SELECT, INSERT, UPDATE, DELETE on Books table
- **Customers**: SELECT, INSERT, UPDATE, DELETE on Customers table  
- **Rentals**: SELECT, UPDATE (return books)
- **Stocks**: SELECT, UPDATE (availability)
- **Mixed**: Weighted distribution (40% Books, 25% Customers, 20% Rentals, 15% Stocks)

### JMeter Testing (530 Operations)
- **Books Thread Group** (200 ops): Full CRUD with JOIN queries
- **Customers Thread Group** (150 ops): Full CRUD with LIKE searches
- **Rentals Thread Group** (100 ops): Read and update operations
- **Stocks Thread Group** (80 ops): Read and update availability

## Output Files

### Python Testing
```
database_test_results/
├── load_test_YYYYMMDD_HHMMSS.csv     # Detailed operation results
├── metrics_YYYYMMDD_HHMMSS.csv       # Database metrics
└── summary_YYYYMMDD_HHMMSS.txt       # Test summary
```

### JMeter Testing
```
jmeter_results/
├── results_YYYYMMDD_HHMMSS.jtl              # Raw JMeter results
├── report_YYYYMMDD_HHMMSS/                  # HTML report (open index.html)
├── jmeter_YYYYMMDD_HHMMSS.log              # JMeter execution log
├── performance_YYYYMMDD_HHMMSS.csv         # System metrics (raw)
├── performance_YYYYMMDD_HHMMSS.clean.csv   # Cleaned metrics
└── performance_graphs_YYYYMMDD_HHMMSS.png  # Performance visualizations
```

## Performance Graphs

When profiling is enabled (JMeter on Windows), the script generates a 2×2 grid of performance graphs:

1. **CPU Usage**: Processor utilization over time with average line
2. **Memory Usage**: Memory commitment percentage with average
3. **Disk I/O**: Read/write operations per second
4. **Network Activity**: Network throughput in MB/s

## Test Database Schema

The script automatically seeds the following test data:
- **20 Authors**: Fiction, Mystery, Sci-Fi, Romance, Horror writers
- **20 Books**: 2 books per author with titles, prices, ratings
- **20 Customers**: Test customers with email, phone, addresses
- **30 Stocks**: 3 copies per book (first 10 books)
- **1 Genre**: Fiction (persistent)

## Monitoring Metrics

### Python Testing
- **Database Metrics** (via DMVs):
  - CPU usage (processor time)
  - Memory usage (MB)
  - Active connections
  - Batch requests/sec
  - Transactions/sec

### JMeter Testing (Windows only)
- **System Metrics** (via typeperf):
  - CPU: Processor Time %
  - Memory: Available MB, Committed %
  - Disk: Reads/sec, Writes/sec
  - Network: Bytes Total/sec (all interfaces)

## Troubleshooting

### JMeter Not Found
```
Error: JMeter not found in PATH
Solution: Add JMeter bin directory to PATH
```

### JDBC Connection Failed
```
Error: Cannot create PoolableConnectionFactory
Solution: Check JDBC driver in JMeter lib/ folder
```

### Performance Monitoring Shows N/A
```
Cause: Requires VIEW SERVER STATE permission
Solution: This is expected; metrics are for system-level monitoring
```

### Graph Generation Failed
```
Error: Graphing libraries not available
Solution: pip install pandas matplotlib
```

## Examples

### Full Test Suite
```bash
# 1. Cleanup previous test data
python run_and_monitor_db_test.py --env target --cleanup

# 2. Run Python load test
python run_and_monitor_db_test.py --env target -c 10 -o 50

# 3. Run JMeter test with profiling
python run_and_monitor_db_test.py --tool jmeter --env target

# 4. Compare results from both tests
```

### Performance Testing Workflow
```bash
# Light load (baseline)
python run_and_monitor_db_test.py --env target -c 5 -o 20

# Medium load
python run_and_monitor_db_test.py --env target -c 10 -o 50

# Heavy load (stress test)
python run_and_monitor_db_test.py --env target -c 50 -o 200
```

### JMeter Quick Test (No Profiling)
```bash
# Fast execution without system monitoring
python run_and_monitor_db_test.py --tool jmeter --env target --no-profiling
```

## Comparison: Python vs JMeter

| Aspect | Python Testing | JMeter Testing |
|--------|---------------|----------------|
| **Protocol** | pyodbc (native) | JDBC |
| **Concurrency** | Configurable | Fixed (530 ops, 10 threads/group) |
| **Operations** | Flexible | Predefined test plan |
| **Database Metrics** | Yes (DMVs) | No |
| **System Metrics** | No | Yes (Windows typeperf) |
| **HTML Reports** | No | Yes |
| **Real-time Feedback** | Yes | Log parsing |
| **Use Case** | Flexible load testing | Industry-standard benchmarking |

## Best Practices

1. **Always cleanup before major tests**: `--cleanup` ensures clean baseline
2. **Start with small loads**: Test with `-c 5 -o 20` before scaling up
3. **Monitor system resources**: Use `--tool jmeter` with profiling for system-level analysis
4. **Save HTML reports**: JMeter reports provide detailed analysis and can be archived
5. **Compare both tools**: Run both Python and JMeter tests for comprehensive coverage
6. **Use appropriate test types**: Match test type to workload (Books for read-heavy, etc.)

## Support

For detailed JMeter setup, see [JMETER_SETUP.md](JMETER_SETUP.md)

For test case documentation, see [test_cases.md](test_cases.md)

## License

Internal testing tool for BookStore database performance validation.
