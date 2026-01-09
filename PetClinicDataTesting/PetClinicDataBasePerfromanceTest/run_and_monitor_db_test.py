#!/usr/bin/env python3
"""
Combined Database Load Test Runner
Runs load test and monitoring simultaneously
Works on both Windows and Linux
"""

import argparse
import threading
import time
import sys
import pyodbc
import csv
import random
import statistics
import uuid
import json
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Remote SQL Server connection with SQL Authentication
# Auto-detect best available driver
try:
    import pyodbc as _pyodbc_test
    available_drivers = _pyodbc_test.drivers()
    if "ODBC Driver 18 for SQL Server" in available_drivers:
        DEFAULT_DRIVER = "ODBC Driver 18 for SQL Server"
    elif "ODBC Driver 17 for SQL Server" in available_drivers:
        DEFAULT_DRIVER = "ODBC Driver 17 for SQL Server"
    else:
        DEFAULT_DRIVER = "SQL Server"
except:
    DEFAULT_DRIVER = "ODBC Driver 17 for SQL Server"

DEFAULT_CONNECTION_STRING = (
    f"DRIVER={{{DEFAULT_DRIVER}}};"
    "SERVER=10.134.77.68,1433;"  # Remote SQL Server
    "DATABASE=BookStore-Master;"
    "UID=testuser;"
    "PWD=TestDb@26#!;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

RESULTS_DIR = Path("database_test_results")
CONFIG_FILE = Path("db_config.json")


def load_config(config_file: Path = CONFIG_FILE) -> dict:
    """Load database configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Configuration file '{config_file}' not found.")
        print("Using default connection settings.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in configuration file '{config_file}'.")
        return None


def build_connection_string(env_config: dict) -> str:
    """Build connection string from environment configuration"""
    driver = env_config.get('driver', DEFAULT_DRIVER)
    server = env_config.get('server')
    database = env_config.get('database')
    
    # Build base connection string
    conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};"
    
    # Add authentication
    if env_config.get('trusted_connection'):
        conn_str += "Trusted_Connection=yes;"
    else:
        username = env_config.get('username')
        password = env_config.get('password')
        if username and password:
            conn_str += f"UID={username};PWD={password};"
    
    # Add encryption settings
    if env_config.get('encrypt'):
        conn_str += "Encrypt=yes;"
    if env_config.get('trust_certificate'):
        conn_str += "TrustServerCertificate=yes;"
    
    return conn_str


def get_connection_from_config(env_name: str, config_file: Path = CONFIG_FILE) -> tuple:
    """Get connection string and database name from config for specified environment"""
    config = load_config(config_file)
    
    if not config:
        return None, None
    
    if 'environments' not in config:
        print("Error: Configuration file missing 'environments' section.")
        return None, None
    
    if env_name not in config['environments']:
        print(f"Error: Environment '{env_name}' not found in configuration.")
        print(f"Available environments: {', '.join(config['environments'].keys())}")
        return None, None
    
    env_config = config['environments'][env_name]
    connection_string = build_connection_string(env_config)
    database = env_config.get('database')
    description = env_config.get('description', env_name)
    
    print(f"\nUsing environment: {env_name}")
    print(f"Description: {description}")
    print(f"Server: {env_config.get('server')}")
    print(f"Database: {database}")
    print()
    
    return connection_string, database


def create_results_directory():
    """Create results directory if it doesn't exist"""
    RESULTS_DIR.mkdir(exist_ok=True)


def get_cpu_usage(cursor):
    """Get SQL Server CPU usage"""
    query = """
    SELECT TOP 1 
        record.value('(./Record/SchedulerMonitorEvent/SystemHealth/ProcessUtilization)[1]', 'int') AS CPUUsage
    FROM ( 
        SELECT timestamp, CONVERT(xml, record) AS record 
        FROM sys.dm_os_ring_buffers 
        WHERE ring_buffer_type = N'RING_BUFFER_SCHEDULER_MONITOR' 
        AND record LIKE '%<SystemHealth>%'
    ) AS x 
    ORDER BY timestamp DESC
    """
    try:
        cursor.execute(query)
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else 0
    except:
        return 0


def get_memory_usage(cursor):
    """Get SQL Server memory usage in MB"""
    query = "SELECT (physical_memory_in_use_kb/1024) AS MemoryUsageMB FROM sys.dm_os_process_memory"
    try:
        cursor.execute(query)
        row = cursor.fetchone()
        return row[0] if row else 0
    except:
        return 0


def get_active_connections(cursor, database):
    """Get number of active connections to the database"""
    query = f"""
    SELECT COUNT(*) AS ActiveConnections
    FROM sys.dm_exec_sessions 
    WHERE is_user_process = 1 
    AND database_id = DB_ID('{database}')
    """
    try:
        cursor.execute(query)
        row = cursor.fetchone()
        return row[0] if row else 0
    except:
        return 0


def get_performance_counters(cursor):
    """Get performance counters"""
    query = """
    SELECT 
        counter_name,
        cntr_value
    FROM sys.dm_os_performance_counters
    WHERE (counter_name IN ('Batch Requests/sec', 'Page reads/sec', 'Page writes/sec', 'Transactions/sec', 'Lock Waits/sec')
        OR (counter_name = 'Number of Deadlocks/sec' AND instance_name = '_Total'))
        AND (instance_name = '' OR instance_name = '_Total')
    """
    counters = {
        'batch_requests': 0,
        'page_reads': 0,
        'page_writes': 0,
        'transactions': 0,
        'lock_waits': 0,
        'deadlocks': 0
    }
    
    try:
        cursor.execute(query)
        for row in cursor.fetchall():
            counter_name = row[0]
            value = row[1] if row[1] is not None else 0
            
            if counter_name == 'Batch Requests/sec':
                counters['batch_requests'] = value
            elif counter_name == 'Page reads/sec':
                counters['page_reads'] = value
            elif counter_name == 'Page writes/sec':
                counters['page_writes'] = value
            elif counter_name == 'Transactions/sec':
                counters['transactions'] = value
            elif counter_name == 'Lock Waits/sec':
                counters['lock_waits'] = value
            elif counter_name == 'Number of Deadlocks/sec':
                counters['deadlocks'] = value
    except:
        pass
    
    return counters


def run_monitoring(connection_string, database, duration):
    """Run monitoring in background"""
    print("[MONITOR] Starting performance monitoring...")
    
    # Create results directory
    create_results_directory()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    metrics_file = RESULTS_DIR / f"metrics_{timestamp}.csv"
    interval_seconds = 5
    
    # Initialize CSV
    with open(metrics_file, 'w', newline='') as f:
        fieldnames = ['timestamp', 'cpu_usage', 'memory_usage_mb', 'active_connections',
                     'batch_requests', 'page_reads', 'page_writes', 'transactions',
                     'lock_waits', 'deadlocks']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
    
    start_time = datetime.now()
    end_time = start_time.timestamp() + duration
    sample_count = 0
    
    # Collect metrics for stats
    all_metrics = []
    
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        while time.time() < end_time:
            sample_count += 1
            current_time = datetime.now()
            
            try:
                # Collect all metrics
                cpu_usage = get_cpu_usage(cursor)
                memory_usage = get_memory_usage(cursor)
                active_conns = get_active_connections(cursor, database)
                perf_counters = get_performance_counters(cursor)
                
                metrics = {
                    'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'cpu_usage': cpu_usage,
                    'memory_usage_mb': memory_usage,
                    'active_connections': active_conns,
                    'batch_requests': perf_counters['batch_requests'],
                    'page_reads': perf_counters['page_reads'],
                    'page_writes': perf_counters['page_writes'],
                    'transactions': perf_counters['transactions'],
                    'lock_waits': perf_counters['lock_waits'],
                    'deadlocks': perf_counters['deadlocks']
                }
                
                # Write to CSV
                with open(metrics_file, 'a', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=metrics.keys())
                    writer.writerow(metrics)
                
                all_metrics.append(metrics)
                
                # Display current metrics
                print(f"[MONITOR Sample {sample_count}] {current_time.strftime('%H:%M:%S')}")
                print(f"  CPU: {cpu_usage}% | Memory: {memory_usage} MB | Connections: {active_conns}")
                print(f"  Batch Req/sec: {perf_counters['batch_requests']} | Transactions/sec: {perf_counters['transactions']}")
                print(f"  Lock Waits: {perf_counters['lock_waits']} | Deadlocks: {perf_counters['deadlocks']}")
                
            except Exception as e:
                print(f"  [MONITOR] Error collecting metrics: {str(e)}")
            
            # Wait for next sample
            remaining_time = end_time - time.time()
            if remaining_time > 0:
                sleep_time = min(interval_seconds, remaining_time)
                time.sleep(sleep_time)
        
        cursor.close()
        conn.close()
        
    except KeyboardInterrupt:
        print("\n[MONITOR] Monitoring stopped by user")
    except Exception as e:
        print(f"\n[MONITOR] Monitoring error: {str(e)}")
    
    print(f"\n[MONITOR] Monitoring completed! Samples: {sample_count}")
    print(f"[MONITOR] Results saved to: {metrics_file}")
    
    # Generate summary statistics
    if all_metrics:
        cpu_values = [m['cpu_usage'] for m in all_metrics]
        mem_values = [m['memory_usage_mb'] for m in all_metrics]
        conn_values = [m['active_connections'] for m in all_metrics]
        
        if cpu_values:
            print(f"[MONITOR] CPU Avg: {round(sum(cpu_values)/len(cpu_values), 2)}% | Max: {max(cpu_values)}%")
        if mem_values:
            print(f"[MONITOR] Memory Avg: {round(sum(mem_values)/len(mem_values), 2)} MB | Max: {max(mem_values)} MB")
        if conn_values:
            print(f"[MONITOR] Connections Avg: {round(sum(conn_values)/len(conn_values), 2)} | Max: {max(conn_values)}")


# ============================================================================
# LOAD TEST FUNCTIONS
# ============================================================================

def execute_select_operation(cursor):
    """Execute various SELECT operations"""
    operation_type = random.choice(['top100', 'by_id', 'with_join', 'count'])
    
    if operation_type == 'top100':
        cursor.execute("SELECT TOP 100 * FROM [dbo].[Books] ORDER BY Id")
        cursor.fetchall()
        return "SELECT_TOP100"
    
    elif operation_type == 'by_id':
        book_id = random.randint(1, 1000)
        cursor.execute("SELECT * FROM [dbo].[Books] WHERE Id = ?", book_id)
        cursor.fetchall()
        return "SELECT_BY_ID"
    
    elif operation_type == 'with_join':
        cursor.execute("""
            SELECT TOP 50 b.Id, b.Title, a.FirstName, a.LastName 
            FROM [dbo].[Books] b 
            INNER JOIN [dbo].[Authors] a ON b.AuthorId = a.Id
            ORDER BY b.Id
        """)
        cursor.fetchall()
        return "SELECT_WITH_JOIN"
    
    else:  # count
        cursor.execute("SELECT COUNT(*) FROM [dbo].[Books]")
        cursor.fetchall()
        return "SELECT_COUNT"


def execute_insert_operation(cursor):
    """Execute INSERT operation"""
    title = f"Performance Test Book {random.randint(1, 999999)}"
    author_id = random.randint(1, 20)  # Assuming 20 authors seeded
    year = random.randint(1900, 2025)
    price = round(random.uniform(10.0, 100.0), 2)
    description = f"Performance test book description {random.randint(1, 999999)}"
    genre_id = 1  # Default genre ID
    issue_date = datetime.now() - timedelta(days=random.randint(0, 3650))
    rating = random.randint(1, 5)
    
    cursor.execute("""
        INSERT INTO [dbo].[Books] (Title, AuthorId, Year, Price, Description, GenreId, IssueDate, Rating) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, title, author_id, year, price, description, genre_id, issue_date, rating)
    cursor.commit()
    return "INSERT"


def execute_update_operation(cursor):
    """Execute UPDATE operation"""
    book_id = random.randint(1, 1000)
    new_price = round(random.uniform(10.0, 100.0), 2)
    
    cursor.execute("""
        UPDATE [dbo].[Books] 
        SET Price = ? 
        WHERE Id = ?
    """, new_price, book_id)
    cursor.commit()
    return "UPDATE"


def execute_delete_operation(cursor):
    """Execute DELETE operation"""
    # Only delete test records
    cursor.execute("""
        DELETE TOP (1) FROM [dbo].[Books] 
        WHERE Title LIKE 'Performance Test Book%'
    """)
    cursor.commit()
    return "DELETE"


# ============================================================================
# CUSTOMER OPERATIONS
# ============================================================================

def execute_customer_select(cursor):
    """Execute Customer SELECT operations"""
    operation_type = random.choice(['all', 'by_id', 'by_email', 'count'])
    
    if operation_type == 'all':
        cursor.execute("SELECT TOP 50 * FROM [dbo].[Customers] ORDER BY ID")
        cursor.fetchall()
        return "CUSTOMER_SELECT_ALL"
    elif operation_type == 'by_id':
        customer_id = random.randint(1, 100)
        cursor.execute("SELECT * FROM [dbo].[Customers] WHERE ID = ?", customer_id)
        cursor.fetchall()
        return "CUSTOMER_SELECT_BY_ID"
    elif operation_type == 'by_email':
        cursor.execute("SELECT * FROM [dbo].[Customers] WHERE Email LIKE '%test%'")
        cursor.fetchall()
        return "CUSTOMER_SELECT_BY_EMAIL"
    else:
        cursor.execute("SELECT COUNT(*) FROM [dbo].[Customers]")
        cursor.fetchall()
        return "CUSTOMER_COUNT"


def execute_customer_insert(cursor):
    """Execute Customer INSERT operation"""
    unique_id = random.randint(100000, 999999)
    first_name = f"TestFirst{unique_id}"
    last_name = f"TestLast{unique_id}"
    email = f"test{unique_id}@example.com"
    identity_card = f"ID{unique_id}"
    unique_key = str(uuid.uuid4())
    date_of_birth = datetime.now() - timedelta(days=random.randint(7300, 25550))  # 20-70 years old
    mobile = f"555{random.randint(1000000, 9999999)}"
    registration_date = datetime.now()
    
    cursor.execute("""
        INSERT INTO [dbo].[Customers] 
        (FirstName, LastName, Email, IdentityCard, UniqueKey, DateOfBirth, Mobile, RegistrationDate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, first_name, last_name, email, identity_card, unique_key, date_of_birth, mobile, registration_date)
    cursor.commit()
    return "CUSTOMER_INSERT"


def execute_customer_update(cursor):
    """Execute Customer UPDATE operation"""
    customer_id = random.randint(1, 100)
    new_email = f"updated{random.randint(100000, 999999)}@example.com"
    
    cursor.execute("""
        UPDATE [dbo].[Customers] 
        SET Email = ?, Mobile = ?
        WHERE ID = ?
    """, new_email, f"555{random.randint(1000000, 9999999)}", customer_id)
    cursor.commit()
    return "CUSTOMER_UPDATE"


def execute_customer_delete(cursor):
    """Execute Customer DELETE operation"""
    cursor.execute("""
        DELETE TOP (1) FROM [dbo].[Customers]
        WHERE FirstName LIKE 'TestFirst%'
    """)
    cursor.commit()
    return "CUSTOMER_DELETE"


# ============================================================================
# RENTAL OPERATIONS
# ============================================================================

def execute_rental_select(cursor):
    """Execute Rental SELECT operations"""
    operation_type = random.choice(['all', 'by_customer', 'active', 'history'])
    
    if operation_type == 'all':
        cursor.execute("SELECT TOP 50 * FROM [dbo].[Rentals] ORDER BY RentalDate DESC")
        cursor.fetchall()
        return "RENTAL_SELECT_ALL"
    elif operation_type == 'by_customer':
        customer_id = random.randint(1, 100)
        cursor.execute("SELECT * FROM [dbo].[Rentals] WHERE CustomerId = ?", customer_id)
        cursor.fetchall()
        return "RENTAL_SELECT_BY_CUSTOMER"
    elif operation_type == 'active':
        cursor.execute("SELECT * FROM [dbo].[Rentals] WHERE Status = 'Active'")
        cursor.fetchall()
        return "RENTAL_SELECT_ACTIVE"
    else:
        cursor.execute("SELECT COUNT(*) FROM [dbo].[Rentals]")
        cursor.fetchall()
        return "RENTAL_COUNT"


def execute_rental_insert(cursor):
    """Execute Rental INSERT operation"""
    customer_id = random.randint(1, 100)
    stock_id = random.randint(1, 50)
    rental_date = datetime.now()
    status = "Active"
    
    cursor.execute("""
        INSERT INTO [dbo].[Rentals] (CustomerId, StockId, RentalDate, Status)
        VALUES (?, ?, ?, ?)
    """, customer_id, stock_id, rental_date, status)
    cursor.commit()
    return "RENTAL_INSERT"


def execute_rental_update(cursor):
    """Execute Rental UPDATE operation (return book)"""
    cursor.execute("""
        UPDATE TOP (1) [dbo].[Rentals]
        SET ReturnedDate = ?, Status = 'Returned'
        WHERE Status = 'Active' AND ReturnedDate IS NULL
    """, datetime.now())
    cursor.commit()
    return "RENTAL_UPDATE"


# ============================================================================
# STOCK OPERATIONS
# ============================================================================

def execute_stock_select(cursor):
    """Execute Stock SELECT operations"""
    operation_type = random.choice(['all', 'by_book', 'available', 'count'])
    
    if operation_type == 'all':
        cursor.execute("SELECT TOP 50 * FROM [dbo].[Stocks]")
        cursor.fetchall()
        return "STOCK_SELECT_ALL"
    elif operation_type == 'by_book':
        book_id = random.randint(1, 100)
        cursor.execute("SELECT * FROM [dbo].[Stocks] WHERE BookId = ?", book_id)
        cursor.fetchall()
        return "STOCK_SELECT_BY_BOOK"
    elif operation_type == 'available':
        cursor.execute("SELECT * FROM [dbo].[Stocks] WHERE IsAvailable = 1")
        cursor.fetchall()
        return "STOCK_SELECT_AVAILABLE"
    else:
        cursor.execute("SELECT COUNT(*) FROM [dbo].[Stocks]")
        cursor.fetchall()
        return "STOCK_COUNT"


def execute_stock_insert(cursor):
    """Execute Stock INSERT operation"""
    book_id = random.randint(1, 100)
    unique_key = str(uuid.uuid4())
    is_available = 1
    
    cursor.execute("""
        INSERT INTO [dbo].[Stocks] (BookId, UniqueKey, IsAvailable)
        VALUES (?, ?, ?)
    """, book_id, unique_key, is_available)
    cursor.commit()
    return "STOCK_INSERT"


def execute_stock_update(cursor):
    """Execute Stock UPDATE operation"""
    stock_id = random.randint(1, 100)
    is_available = random.choice([0, 1])
    
    cursor.execute("""
        UPDATE [dbo].[Stocks]
        SET IsAvailable = ?
        WHERE ID = ?
    """, is_available, stock_id)
    cursor.commit()
    return "STOCK_UPDATE"


def worker_thread(connection_string, operations_per_thread, test_type, thread_id):
    """Worker thread that executes database operations"""
    results = []
    
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        for i in range(operations_per_thread):
            start_time = time.time()
            
            try:
                # Determine operation type based on test mode
                if test_type == 'Mixed':
                    # Mixed mode: All tables with weighted distribution
                    rand_val = random.random()
                    table_choice = random.choice(['books', 'customers', 'rentals', 'stocks'])
                    
                    if table_choice == 'books':
                        op_type = random.choices(['SELECT', 'INSERT', 'UPDATE', 'DELETE'], 
                                                weights=[0.6, 0.2, 0.1, 0.1])[0]
                        if op_type == 'SELECT':
                            operation = execute_select_operation(cursor)
                        elif op_type == 'INSERT':
                            operation = execute_insert_operation(cursor)
                        elif op_type == 'UPDATE':
                            operation = execute_update_operation(cursor)
                        else:
                            operation = execute_delete_operation(cursor)
                    
                    elif table_choice == 'customers':
                        op_type = random.choices(['SELECT', 'INSERT', 'UPDATE', 'DELETE'], 
                                                weights=[0.5, 0.3, 0.15, 0.05])[0]
                        if op_type == 'SELECT':
                            operation = execute_customer_select(cursor)
                        elif op_type == 'INSERT':
                            operation = execute_customer_insert(cursor)
                        elif op_type == 'UPDATE':
                            operation = execute_customer_update(cursor)
                        else:
                            operation = execute_customer_delete(cursor)
                    
                    elif table_choice == 'rentals':
                        op_type = random.choices(['SELECT', 'INSERT', 'UPDATE'], 
                                                weights=[0.5, 0.3, 0.2])[0]
                        if op_type == 'SELECT':
                            operation = execute_rental_select(cursor)
                        elif op_type == 'INSERT':
                            operation = execute_rental_insert(cursor)
                        else:
                            operation = execute_rental_update(cursor)
                    
                    else:  # stocks
                        op_type = random.choices(['SELECT', 'INSERT', 'UPDATE'], 
                                                weights=[0.6, 0.2, 0.2])[0]
                        if op_type == 'SELECT':
                            operation = execute_stock_select(cursor)
                        elif op_type == 'INSERT':
                            operation = execute_stock_insert(cursor)
                        else:
                            operation = execute_stock_update(cursor)
                
                elif test_type == 'Read':
                    # Read-only: SELECT from all tables
                    table_choice = random.choice(['books', 'customers', 'rentals', 'stocks'])
                    if table_choice == 'books':
                        operation = execute_select_operation(cursor)
                    elif table_choice == 'customers':
                        operation = execute_customer_select(cursor)
                    elif table_choice == 'rentals':
                        operation = execute_rental_select(cursor)
                    else:
                        operation = execute_stock_select(cursor)
                
                elif test_type in ['Write', 'INSERT']:
                    # Write mode: INSERT to all tables
                    table_choice = random.choice(['books', 'customers', 'rentals', 'stocks'])
                    if table_choice == 'books':
                        operation = execute_insert_operation(cursor)
                    elif table_choice == 'customers':
                        operation = execute_customer_insert(cursor)
                    elif table_choice == 'rentals':
                        operation = execute_rental_insert(cursor)
                    else:
                        operation = execute_stock_insert(cursor)
                
                elif test_type == 'UPDATE':
                    # Update mode: UPDATE all tables
                    table_choice = random.choice(['books', 'customers', 'rentals', 'stocks'])
                    if table_choice == 'books':
                        operation = execute_update_operation(cursor)
                    elif table_choice == 'customers':
                        operation = execute_customer_update(cursor)
                    elif table_choice == 'rentals':
                        operation = execute_rental_update(cursor)
                    else:
                        operation = execute_stock_update(cursor)
                
                elif test_type == 'DELETE':
                    # Delete mode: DELETE from deletable tables
                    table_choice = random.choice(['books', 'customers'])
                    if table_choice == 'books':
                        operation = execute_delete_operation(cursor)
                    else:
                        operation = execute_customer_delete(cursor)
                
                else:  # SELECT
                    # Default: SELECT from all tables
                    table_choice = random.choice(['books', 'customers', 'rentals', 'stocks'])
                    if table_choice == 'books':
                        operation = execute_select_operation(cursor)
                    elif table_choice == 'customers':
                        operation = execute_customer_select(cursor)
                    elif table_choice == 'rentals':
                        operation = execute_rental_select(cursor)
                    else:
                        operation = execute_stock_select(cursor)
                
                duration = (time.time() - start_time) * 1000  # Convert to ms
                
                results.append({
                    'thread_id': thread_id,
                    'operation_number': i + 1,
                    'operation_type': operation,
                    'duration_ms': round(duration, 2),
                    'status': 'SUCCESS',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                })
                
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                results.append({
                    'thread_id': thread_id,
                    'operation_number': i + 1,
                    'operation_type': 'ERROR',
                    'duration_ms': round(duration, 2),
                    'status': 'FAILED',
                    'error': str(e),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                })
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"[LOAD TEST] Thread {thread_id} connection error: {str(e)}")
    
    return results


def extract_db_info(connection_string):
    """Extract database connection information from connection string"""
    db_info = {
        'server': 'Unknown',
        'database': 'Unknown',
        'driver': 'Unknown',
        'auth_type': 'Unknown'
    }
    
    try:
        # Parse connection string
        parts = connection_string.split(';')
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip().upper()
                value = value.strip()
                
                if key == 'SERVER':
                    db_info['server'] = value
                elif key == 'DATABASE':
                    db_info['database'] = value
                elif key == 'DRIVER':
                    db_info['driver'] = value.strip('{}')
                elif key == 'UID':
                    db_info['auth_type'] = f'SQL Authentication (User: {value})'
                elif 'TRUSTED_CONNECTION' in key and value.lower() in ['yes', 'true']:
                    db_info['auth_type'] = 'Windows Authentication'
    except:
        pass
    
    return db_info


def run_load_test(connections, operations, connection_string, test_type):
    """Run load test with concurrent connections"""
    print("[LOAD TEST] Starting database load test...")
    time.sleep(3)  # Give monitor time to start
    
    # Create results directory
    create_results_directory()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = RESULTS_DIR / f"load_test_{timestamp}.csv"
    summary_file = RESULTS_DIR / f"summary_{timestamp}.txt"
    
    print(f"[LOAD TEST] Running with {connections} concurrent connections")
    print(f"[LOAD TEST] Each connection will perform {operations} operations")
    print(f"[LOAD TEST] Test type: {test_type}")
    print(f"[LOAD TEST] Total operations: {connections * operations}")
    print()
    
    # Initialize CSV file
    with open(results_file, 'w', newline='') as f:
        fieldnames = ['thread_id', 'operation_number', 'operation_type', 'duration_ms', 'status', 'timestamp', 'error']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
    
    # Execute load test with thread pool
    start_time = time.time()
    all_results = []
    
    print(f"[LOAD TEST] {datetime.now().strftime('%H:%M:%S')} - Starting {connections} worker threads...")
    
    with ThreadPoolExecutor(max_workers=connections) as executor:
        futures = [
            executor.submit(worker_thread, connection_string, operations, test_type, i+1)
            for i in range(connections)
        ]
        
        completed = 0
        for future in as_completed(futures):
            completed += 1
            results = future.result()
            all_results.extend(results)
            
            # Write results to CSV
            with open(results_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['thread_id', 'operation_number', 'operation_type', 'duration_ms', 'status', 'timestamp', 'error'])
                for result in results:
                    writer.writerow({k: result.get(k, '') for k in ['thread_id', 'operation_number', 'operation_type', 'duration_ms', 'status', 'timestamp', 'error']})
            
            if completed % max(1, connections // 10) == 0 or completed == connections:
                print(f"[LOAD TEST] Progress: {completed}/{connections} threads completed ({round(completed/connections*100)}%)")
    
    total_duration = time.time() - start_time
    
    print(f"\n[LOAD TEST] All operations completed in {round(total_duration, 2)} seconds")
    
    # Calculate statistics
    successful_ops = [r for r in all_results if r['status'] == 'SUCCESS']
    failed_ops = [r for r in all_results if r['status'] == 'FAILED']
    
    if successful_ops:
        durations = [r['duration_ms'] for r in successful_ops]
        durations.sort()
        
        avg_duration = statistics.mean(durations)
        median_duration = statistics.median(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        p95_duration = durations[int(len(durations) * 0.95)] if len(durations) > 0 else 0
        p99_duration = durations[int(len(durations) * 0.99)] if len(durations) > 0 else 0
        
        throughput = len(successful_ops) / total_duration
        
        # Count operations by type
        op_counts = {}
        for result in successful_ops:
            op_type = result['operation_type']
            op_counts[op_type] = op_counts.get(op_type, 0) + 1
        
        # Extract database connection details
        db_info = extract_db_info(connection_string)
        
        # Generate summary
        summary = f"""
DATABASE LOAD TEST SUMMARY
{'=' * 60}

Database Information:
  Server: {db_info['server']}
  Database: {db_info['database']}
  Driver: {db_info['driver']}
  Authentication: {db_info['auth_type']}

Test Configuration:
  Concurrent Connections: {connections}
  Operations per Connection: {operations}
  Test Type: {test_type}
  Total Operations: {len(all_results)}
  Test Duration: {round(total_duration, 2)} seconds

Results:
  Successful Operations: {len(successful_ops)} ({round(len(successful_ops)/len(all_results)*100, 2)}%)
  Failed Operations: {len(failed_ops)} ({round(len(failed_ops)/len(all_results)*100, 2) if all_results else 0}%)
  Throughput: {round(throughput, 2)} operations/second

Response Times (milliseconds):
  Average: {round(avg_duration, 2)} ms
  Median: {round(median_duration, 2)} ms
  Min: {round(min_duration, 2)} ms
  Max: {round(max_duration, 2)} ms
  95th Percentile: {round(p95_duration, 2)} ms
  99th Percentile: {round(p99_duration, 2)} ms

Operations by Type:
"""
        for op_type, count in sorted(op_counts.items()):
            summary += f"  {op_type}: {count} ({round(count/len(successful_ops)*100, 2)}%)\n"
        
        summary += f"\nResults saved to:\n  {results_file}\n  {summary_file}\n"
        
        # Write summary to file
        with open(summary_file, 'w') as f:
            f.write(summary)
        
        # Print summary to console
        print(summary)
        
    else:
        print(f"[LOAD TEST] ERROR: All operations failed!")
        with open(summary_file, 'w') as f:
            f.write(f"ERROR: All {len(all_results)} operations failed!\n")
    
    print(f"[LOAD TEST] Results saved to: {results_file}")


def cleanup_database(connection_string):
    """Clean up all records from Books and Authors tables"""
    print("=" * 50)
    print("DATABASE CLEANUP")
    print("=" * 50)
    print()
    print("WARNING: This will DELETE ALL records from Books and Authors tables!")
    print()
    
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Get counts before deletion
        cursor.execute("SELECT COUNT(*) FROM [dbo].[Books]")
        books_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM [dbo].[Authors]")
        authors_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM [dbo].[Customers]")
        customers_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM [dbo].[Rentals]")
        rentals_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM [dbo].[Stocks]")
        stocks_count = cursor.fetchone()[0]
        
        print(f"Current records:")
        print(f"  Books: {books_count}")
        print(f"  Authors: {authors_count}")
        print(f"  Customers: {customers_count}")
        print(f"  Rentals: {rentals_count}")
        print(f"  Stocks: {stocks_count}")
        print()
        
        if (books_count == 0 and authors_count == 0 and customers_count == 0 
            and rentals_count == 0 and stocks_count == 0):
            print("All tables are already empty. No cleanup needed.")
            cursor.close()
            conn.close()
            return
        
        print("Deleting records (respecting foreign key constraints)...")
        
        # Delete in proper order to respect foreign keys
        # Rentals first (references Customers and Stocks)
        cursor.execute("DELETE FROM [dbo].[Rentals]")
        deleted_rentals = cursor.rowcount
        print(f"  Deleted {deleted_rentals} rentals")
        
        # Stocks (references Books)
        cursor.execute("DELETE FROM [dbo].[Stocks]")
        deleted_stocks = cursor.rowcount
        print(f"  Deleted {deleted_stocks} stocks")
        
        # Books (references Authors and Genres)
        cursor.execute("DELETE FROM [dbo].[Books]")
        deleted_books = cursor.rowcount
        print(f"  Deleted {deleted_books} books")
        
        # Authors
        cursor.execute("DELETE FROM [dbo].[Authors]")
        deleted_authors = cursor.rowcount
        print(f"  Deleted {deleted_authors} authors")
        
        # Customers
        cursor.execute("DELETE FROM [dbo].[Customers]")
        deleted_customers = cursor.rowcount
        print(f"  Deleted {deleted_customers} customers")
        
        # Reset identity seeds (skip if user doesn't have permission)
        try:
            cursor.execute("DBCC CHECKIDENT ('[dbo].[Authors]', RESEED, 0)")
            cursor.execute("DBCC CHECKIDENT ('[dbo].[Books]', RESEED, 0)")
            cursor.execute("DBCC CHECKIDENT ('[dbo].[Customers]', RESEED, 0)")
            cursor.execute("DBCC CHECKIDENT ('[dbo].[Rentals]', RESEED, 0)")
            cursor.execute("DBCC CHECKIDENT ('[dbo].[Stocks]', RESEED, 0)")
            print(f"  Reset all identity seeds to 0")
        except Exception as e:
            print(f"  Warning: Could not reset identity seeds (requires elevated permissions)")
        
        # Commit the changes
        cursor.commit()
        
        print()
        print("✓ Cleanup completed successfully!")
        print()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"ERROR: Failed to cleanup database: {str(e)}")
        print()


def seed_database(connection_string):
    """Seed database with initial test data for all tables"""
    print("=" * 50)
    print("DATABASE SEEDING")
    print("=" * 50)
    print()
    
    # Seed Genres first (required by Books)
    seed_genres(connection_string)
    
    # Seed Authors
    print("Adding seed data for Authors...")
    print()
    
    authors = [
        ("William", "Shakespeare"), ("Jane", "Austen"), ("Charles", "Dickens"), ("Mark", "Twain"),
        ("Ernest", "Hemingway"), ("F. Scott", "Fitzgerald"), ("George", "Orwell"), ("J.K.", "Rowling"),
        ("Stephen", "King"), ("Agatha", "Christie"), ("Leo", "Tolstoy"), ("Fyodor", "Dostoevsky"),
        ("Virginia", "Woolf"), ("James", "Joyce"), ("Franz", "Kafka"), ("Gabriel Garcia", "Marquez"),
        ("Haruki", "Murakami"), ("Margaret", "Atwood"), ("Toni", "Morrison"), ("Chinua", "Achebe")
    ]
    
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Check if authors already exist
        cursor.execute("SELECT COUNT(*) FROM [dbo].[Authors]")
        existing_count = cursor.fetchone()[0]
        
        if existing_count >= 20:
            print(f"Authors table already has {existing_count} records. Skipping seed.")
            cursor.close()
            conn.close()
        else:
            # Insert authors
            inserted = 0
            for first_name, last_name in authors:
                try:
                    author_guid = str(uuid.uuid4())
                    birth_date = datetime.now() - timedelta(days=20000)  # ~55 years ago
                    cursor.execute("""
                        INSERT INTO [dbo].[Authors] (AuthorId, FirstName, LastName, BirthDate, Nationality, Bio, Email, Affiliation) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, author_guid, first_name, last_name, birth_date, "Unknown", "Test Author Bio", 
                    f"{first_name.lower()}.{last_name.lower()}@test.com", "Test Affiliation")
                    inserted += 1
                except Exception as e:
                    print(f"  Warning: Could not insert '{first_name} {last_name}': {str(e)}")
            
            cursor.commit()
            
            print(f"✓ Seeded {inserted} authors successfully!")
            print()
            
            cursor.close()
            conn.close()
        
    except Exception as e:
        print(f"ERROR: Failed to seed authors: {str(e)}")
        print()
    
    # Seed Customers
    seed_customers(connection_string)
    
    # Seed Stocks (requires Books to exist)
    seed_stocks(connection_string)


def seed_genres(connection_string):
    """Seed database with default Genre for testing"""
    print("Checking Genres table...")
    
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Check if default genre exists
        cursor.execute("SELECT COUNT(*) FROM [dbo].[Genres]")
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"  Genres table already has {existing_count} record(s). Skipping.")
            cursor.close()
            conn.close()
            return
        
        # Insert default genre
        cursor.execute("INSERT INTO [dbo].[Genres] (Name) VALUES (?)", "General")
        cursor.commit()
        
        print("  ✓ Seeded default genre successfully!")
        print()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"  Warning: Could not seed genres: {str(e)}")
        print()


def seed_customers(connection_string):
    """Seed database with test customers"""
    print("Seeding Customers table...")
    
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Check if customers already exist
        cursor.execute("SELECT COUNT(*) FROM [dbo].[Customers]")
        existing_count = cursor.fetchone()[0]
        
        if existing_count >= 20:
            print(f"  Customers table already has {existing_count} records. Skipping.")
            cursor.close()
            conn.close()
            return
        
        # Insert test customers
        inserted = 0
        for i in range(1, 21):
            try:
                unique_key = str(uuid.uuid4())
                first_name = f"Customer{i}"
                last_name = f"Test{i}"
                email = f"customer{i}@test.com"
                identity_card = f"ID{1000+i}"
                date_of_birth = datetime.now() - timedelta(days=10000 + i*100)
                mobile = f"555000{i:04d}"
                registration_date = datetime.now()
                
                cursor.execute("""
                    INSERT INTO [dbo].[Customers] 
                    (FirstName, LastName, Email, IdentityCard, UniqueKey, DateOfBirth, Mobile, RegistrationDate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, first_name, last_name, email, identity_card, unique_key, date_of_birth, mobile, registration_date)
                inserted += 1
            except Exception as e:
                print(f"  Warning: Could not insert customer {i}: {str(e)}")
        
        cursor.commit()
        print(f"  ✓ Seeded {inserted} customers successfully!")
        print()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"  Warning: Could not seed customers: {str(e)}")
        print()


def seed_stocks(connection_string):
    """Seed database with stock items"""
    print("Seeding Stocks table...")
    
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Check if stocks already exist
        cursor.execute("SELECT COUNT(*) FROM [dbo].[Stocks]")
        existing_count = cursor.fetchone()[0]
        
        if existing_count >= 30:
            print(f"  Stocks table already has {existing_count} records. Skipping.")
            cursor.close()
            conn.close()
            return
        
        # Get existing book IDs
        cursor.execute("SELECT ID FROM [dbo].[Books]")
        book_ids = [row[0] for row in cursor.fetchall()]
        
        if not book_ids:
            print(f"  Warning: No books found. Cannot create stock items.")
            cursor.close()
            conn.close()
            return
        
        # Create 3 stock items per book
        inserted = 0
        for book_id in book_ids[:10]:  # Limit to first 10 books
            for copy in range(3):
                try:
                    unique_key = str(uuid.uuid4())
                    is_available = 1
                    
                    cursor.execute("""
                        INSERT INTO [dbo].[Stocks] (BookId, UniqueKey, IsAvailable)
                        VALUES (?, ?, ?)
                    """, book_id, unique_key, is_available)
                    inserted += 1
                except Exception as e:
                    print(f"  Warning: Could not insert stock for book {book_id}: {str(e)}")
        
        cursor.commit()
        print(f"  ✓ Seeded {inserted} stock items successfully!")
        print()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"  Warning: Could not seed stocks: {str(e)}")
        print()



def main():
    parser = argparse.ArgumentParser(
        description='Combined Database Load & Monitoring Test',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Configuration:
  Use --env to select a pre-configured database environment from db_config.json
  Available environments: source, target, dev, test, localdb
  
Examples:
  # Run test against source database
  python run_and_monitor_db_test.py --env source -c 50 -o 200
  
  # Run test against target database
  python run_and_monitor_db_test.py --env target -c 50 -o 200
  
  # Use custom connection string
  python run_and_monitor_db_test.py -s "DRIVER={...};SERVER=..." -c 20 -o 100
        """)
    
    parser.add_argument('--env', '--environment', type=str, dest='environment',
                       help='Database environment from config file (source, target, dev, test, localdb)')
    parser.add_argument('--config', type=str, default='../db_config.json',
                       help='Path to configuration file (default: ../db_config.json)')
    parser.add_argument('-c', '--connections', type=int, default=20,
                       help='Number of concurrent connections (default: 20)')
    parser.add_argument('-o', '--operations', type=int, default=100,
                       help='Operations per connection (default: 100)')
    parser.add_argument('-t', '--test-type', type=str, default='Mixed',
                       choices=['Read', 'Write', 'Update', 'Delete', 'Mixed', 'SELECT', 'INSERT', 'UPDATE', 'DELETE'],
                       help='Type of test to run (default: Mixed)')
    parser.add_argument('-d', '--duration', type=int, default=120,
                       help='Monitoring duration in seconds (default: 120)')
    parser.add_argument('-s', '--connection-string', type=str, default=DEFAULT_CONNECTION_STRING,
                       help='Database connection string')
    parser.add_argument('--database', type=str, default='BookStore-Master',
                       help='Database name (default: BookStore-Master)')
    parser.add_argument('--cleanup', action='store_true',
                       help='Clean up all records from Books and Authors tables (use before/after testing)')
    
    args = parser.parse_args()
    
    # Determine connection string and database name
    if args.environment:
        # Load from configuration file
        connection_string, database_name = get_connection_from_config(
            args.environment, 
            Path(args.config)
        )
        if not connection_string:
            print("\nFailed to load configuration. Exiting.")
            sys.exit(1)
    else:
        # Use provided connection string or default
        connection_string = args.connection_string
        database_name = args.database
        print(f"\nUsing connection string: {connection_string[:50]}...")
        print(f"Database: {database_name}\n")
    
    # If cleanup flag is set, run cleanup and exit
    if args.cleanup:
        cleanup_database(connection_string)
        return
    
    print("=" * 50)
    print("COMBINED DATABASE LOAD & MONITORING TEST")
    print("=" * 50)
    print()
    
    # Clean up database before running test
    print("Step 1: Cleaning up database...")
    cleanup_database(connection_string)
    
    print("Step 2: Seeding Genres...")
    seed_genres(connection_string)
    
    print("Step 3: Seeding Authors...")
    seed_database(connection_string)
    
    print("Step 4: Starting performance test...")
    print()
    print("Test Configuration:")
    print(f"  Concurrent Connections: {args.connections}")
    print(f"  Operations per Connection: {args.operations}")
    print(f"  Test Type: {args.test_type}")
    print(f"  Monitoring Duration: {args.duration} seconds")
    print()
    
    # Start monitoring in background thread
    monitor_thread = threading.Thread(
        target=run_monitoring,
        args=(connection_string, database_name, args.duration)
    )
    monitor_thread.start()
    
    # Run load test
    run_load_test(args.connections, args.operations, connection_string, args.test_type)
    
    # Wait for monitoring to complete
    print()
    print("[WAITING] Waiting for monitoring to complete...")
    monitor_thread.join()
    
    print()
    print("=" * 50)
    print("COMBINED TEST COMPLETED!")
    print("=" * 50)
    print()
    print("Results saved in: database_test_results/")
    print()
    print("Next steps:")
    print("  1. Review load test results (load_test_*.csv)")
    print("  2. Review monitoring metrics (metrics_*.csv)")
    print()


if __name__ == "__main__":
    main()
