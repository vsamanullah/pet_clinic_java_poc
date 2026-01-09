# Database Performance Testing - Configuration Guide

## Overview

The database performance testing tool now supports environment-based configuration, allowing you to easily switch between different databases (source, target, dev, test, etc.) without modifying code.

## Configuration File: `db_config.json`

The `db_config.json` file contains pre-configured database environments. Each environment includes connection details such as server, database name, credentials, and driver settings.

### Configuration Structure

```json
{
  "environments": {
    "environment_name": {
      "server": "hostname,port",
      "database": "database_name",
      "username": "username",
      "password": "password",
      "driver": "ODBC Driver Name",
      "encrypt": true/false,
      "trust_certificate": true/false,
      "trusted_connection": true/false,
      "description": "Description of this environment"
    }
  }
}
```

### Pre-configured Environments

| Environment | Description | Authentication |
|------------|-------------|----------------|
| `source` | Source Database (Pre-Migration) | SQL Auth |
| `target` | Target Database (Post-Migration) | SQL Auth |
| `dev` | Development Environment | SQL Auth |
| `test` | Test Environment | SQL Auth |
| `localdb` | Local Development Database | Windows Auth |

## Usage Examples

### 1. Run Test Against Source Database

```bash
python run_and_monitor_db_test.py --env source -c 50 -o 200 -t Mixed -d 30
```

This will:
- Load connection details from the `source` environment
- Use 50 concurrent connections
- Execute 200 operations per connection
- Run mixed workload (60% SELECT, 20% INSERT, 10% UPDATE, 10% DELETE)
- Monitor for 30 seconds

### 2. Run Test Against Target Database

```bash
python run_and_monitor_db_test.py --env target -c 50 -o 200 -t Mixed -d 30
```

### 3. Compare Source vs Target Performance

```bash
# Test source database
python run_and_monitor_db_test.py --env source -c 50 -o 200 -t Read -d 60

# Test target database  
python run_and_monitor_db_test.py --env target -c 50 -o 200 -t Read -d 60

# Compare the results from database_test_results/ directory
```

### 4. Use Custom Configuration File

```bash
python run_and_monitor_db_test.py --env prod --config my_config.json -c 20 -o 100
```

### 5. Use Direct Connection String (Old Method - Still Supported)

```bash
python run_and_monitor_db_test.py -s "DRIVER={ODBC Driver 18 for SQL Server};SERVER=server;DATABASE=db;UID=user;PWD=pass" -c 20 -o 100
```

### 6. Cleanup Database Using Environment

```bash
python run_and_monitor_db_test.py --env source --cleanup
python run_and_monitor_db_test.py --env target --cleanup
```

## Command Line Options

### Environment Options
- `--env ENVIRONMENT` : Select environment from config file (source, target, dev, test, localdb)
- `--config FILE` : Path to custom configuration file (default: db_config.json)

### Test Configuration
- `-c, --connections N` : Number of concurrent connections (default: 20)
- `-o, --operations N` : Operations per connection (default: 100)
- `-t, --test-type TYPE` : Test type - Read, Write, Update, Delete, Mixed (default: Mixed)
- `-d, --duration N` : Monitoring duration in seconds (default: 120)

### Database Options
- `-s, --connection-string STR` : Direct connection string (overrides environment)
- `--database NAME` : Database name (when using connection string)
- `--cleanup` : Clean up all test data and exit

## Configuration File Security

⚠️ **Important**: The `db_config.json` file contains sensitive credentials (passwords).

### Security Best Practices:

1. **Add to .gitignore**:
   ```
   db_config.json
   *.json
   ```

2. **Create a template file** (`db_config.template.json`) for version control:
   ```json
   {
     "environments": {
       "example": {
         "server": "your-server,1433",
         "database": "your-database",
         "username": "your-username",
         "password": "your-password",
         ...
       }
     }
   }
   ```

3. **Use environment variables** for sensitive data:
   - Set passwords in environment variables
   - Update config loading to read from env vars

4. **Restrict file permissions**:
   ```bash
   # Linux/Mac
   chmod 600 db_config.json
   ```

## Customizing Environments

### Add a New Environment

Edit `db_config.json` and add a new environment:

```json
{
  "environments": {
    ...existing environments...,
    "staging": {
      "server": "staging-server.example.com,1433",
      "database": "BookStore-Staging",
      "username": "staginguser",
      "password": "StagingPassword123!",
      "driver": "ODBC Driver 18 for SQL Server",
      "encrypt": true,
      "trust_certificate": true,
      "description": "Staging Environment"
    }
  }
}
```

Then use it:
```bash
python run_and_monitor_db_test.py --env staging -c 30 -o 150
```

### Windows Authentication Example

```json
{
  "localdb": {
    "server": "(localdb)\\MSSQLLocalDB",
    "database": "BookServiceContext",
    "username": null,
    "password": null,
    "driver": "ODBC Driver 17 for SQL Server",
    "encrypt": false,
    "trust_certificate": false,
    "trusted_connection": true,
    "description": "Local Development Database (Windows Auth)"
  }
}
```

## Migration Testing Workflow

### Typical workflow for testing database migration:

```bash
# Step 1: Test source database performance (before migration)
python run_and_monitor_db_test.py --env source -c 50 -o 200 -t Mixed -d 60

# Step 2: Run your database migration scripts
# ... perform migration ...

# Step 3: Test target database performance (after migration)
python run_and_monitor_db_test.py --env target -c 50 -o 200 -t Mixed -d 60

# Step 4: Compare results
# Review files in database_test_results/ directory:
# - load_test_YYYYMMDD_HHMMSS.csv
# - summary_YYYYMMDD_HHMMSS.txt
# - metrics_YYYYMMDD_HHMMSS.csv
```

## Troubleshooting

### Error: "Environment 'xyz' not found in configuration"

**Solution**: Check available environments:
```bash
python run_and_monitor_db_test.py --env invalid_name
```
This will list all available environments.

### Error: "Configuration file 'db_config.json' not found"

**Solution**: 
1. Ensure `db_config.json` exists in the same directory as the script
2. Or specify a custom path: `--config /path/to/config.json`

### Connection Failures

**Solution**:
1. Verify server is reachable
2. Check credentials in config file
3. Ensure ODBC driver is installed
4. Test connection manually using SQL Server Management Studio

## Results Analysis

Results are saved in `database_test_results/` directory with timestamps:

- **load_test_YYYYMMDD_HHMMSS.csv**: Detailed operation results
- **summary_YYYYMMDD_HHMMSS.txt**: Test summary with statistics
- **metrics_YYYYMMDD_HHMMSS.csv**: System metrics (CPU, memory, connections)

Compare source vs target results to validate migration performance impact.

## Help

View all available options:
```bash
python run_and_monitor_db_test.py --help
```
