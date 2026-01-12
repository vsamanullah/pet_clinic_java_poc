"""
PetClinic Database Performance Test Runner with System Monitoring
Supports: PostgreSQL database with PetClinic schema (owners, pets, vets, visits, types, specialties)
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from random import choice, randint, random, sample

import psycopg2
from psycopg2 import sql

# Optional imports for graphing
try:
    import matplotlib.pyplot as plt
    import pandas as pd
    GRAPHING_AVAILABLE = True
except ImportError:
    GRAPHING_AVAILABLE = False

# Configuration
CURRENT_DIR = Path(__file__).parent
JMETER_TEST_PLAN = CURRENT_DIR / "JMeter_DB_Mixed_Operations.jmx"
JMETER_RESULTS_DIR = CURRENT_DIR / "jmeter_results"

# Terminal colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_color(text, color=Colors.ENDC):
    """Print colored text"""
    print(f"{color}{text}{Colors.ENDC}")

def print_header(text):
    """Print formatted header"""
    print()
    print_color("=" * 70, Colors.CYAN)
    print_color(text, Colors.CYAN + Colors.BOLD)
    print_color("=" * 70, Colors.CYAN)

def check_jmeter():
    """Check if JMeter is available"""
    jmeter_cmd = 'jmeter.bat' if os.name == 'nt' else 'jmeter'
    try:
        result = subprocess.run([jmeter_cmd, '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0] if result.stdout else "Unknown version"
            print_color(f"  ✓ JMeter found: {version_line}", Colors.GREEN)
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print_color("  ✗ JMeter not found in PATH", Colors.RED)
    print("    Please install JMeter and add it to your PATH")
    print("    See JMETER_SETUP.md for installation instructions")
    return False

def load_config(config_file):
    """Load database configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print_color(f"Error: Configuration file not found: {config_file}", Colors.RED)
        return None
    except json.JSONDecodeError:
        print_color(f"Error: Invalid JSON in configuration file: {config_file}", Colors.RED)
        return None

def get_connection_from_config(environment, config_file):
    """Get PostgreSQL connection from config file"""
    config = load_config(config_file)
    if not config:
        return None, None
    
    if environment not in config['environments']:
        print_color(f"Error: Environment '{environment}' not found in config", Colors.RED)
        print(f"Available environments: {', '.join(config['environments'].keys())}")
        return None, None
    
    env_config = config['environments'][environment]
    db_name = env_config['database']
    
    conn_params = {
        'host': env_config.get('host') or env_config.get('server'),
        'port': env_config.get('port', 5432),
        'database': db_name,
        'user': env_config['username'],
        'password': env_config['password']
    }
    
    host = env_config.get('host') or env_config.get('server')
    print_color(f"  ✓ Loaded configuration for: {environment}", Colors.GREEN)
    print(f"    Database: {host}:{conn_params['port']}/{db_name}")
    print(f"    User: {env_config['username']}")
    
    return conn_params, db_name

def get_connection(conn_params):
    """Create PostgreSQL database connection"""
    try:
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = False
        return conn
    except psycopg2.Error as e:
        print_color(f"  ✗ Database connection error: {e}", Colors.RED)
        return None

def cleanup_database(conn_params):
    """Clean all records from PetClinic tables"""
    conn = get_connection(conn_params)
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Delete in proper order (respecting foreign keys)
        tables_order = [
            'visits',
            'vet_specialties',
            'pets',
            'owners',
            'vets',
            'specialties',
            'types'
        ]
        
        total_deleted = 0
        for table in tables_order:
            cursor.execute(f"DELETE FROM {table}")
            deleted = cursor.rowcount
            total_deleted += deleted
            print(f"  Cleaned {table}: {deleted} records")
        
        conn.commit()
        print_color(f"\n  ✓ Cleanup complete: {total_deleted} total records removed", Colors.GREEN)
        return True
        
    except psycopg2.Error as e:
        conn.rollback()
        print_color(f"  ✗ Cleanup error: {e}", Colors.RED)
        return False
    finally:
        cursor.close()
        conn.close()

# Sample data for seeding
PET_TYPES = ['cat', 'dog', 'lizard', 'snake', 'bird', 'hamster']

SPECIALTIES = [
    'radiology', 'surgery', 'dentistry', 
    'cardiology', 'dermatology', 'neurology'
]

FIRST_NAMES = [
    'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
    'William', 'Barbara', 'David', 'Elizabeth', 'Richard', 'Susan', 'Joseph', 'Jessica',
    'Thomas', 'Sarah', 'Charles', 'Karen', 'Christopher', 'Nancy', 'Daniel', 'Lisa'
]

LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
    'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas'
]

STREET_NAMES = [
    'Main St', 'Oak Ave', 'Maple Dr', 'Park Blvd', 'Washington St', 'Lake View Dr',
    'Hill St', 'Forest Ave', 'River Rd', 'Sunset Blvd', 'Cedar Ln', 'Pine St'
]

CITIES = [
    'Madison', 'Monona', 'Sun Prairie', 'Waunakee', 'Middleton', 
    'McFarland', 'Fitchburg', 'Verona', 'Oregon', 'Stoughton'
]

PET_NAMES = [
    'Max', 'Bella', 'Charlie', 'Lucy', 'Cooper', 'Luna', 'Buddy', 'Daisy',
    'Rocky', 'Molly', 'Duke', 'Maggie', 'Bear', 'Sophie', 'Zeus', 'Sadie'
]

def seed_types(conn_params, count=6):
    """Seed pet types"""
    conn = get_connection(conn_params)
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        for pet_type in PET_TYPES[:count]:
            cursor.execute(
                "INSERT INTO types (name) VALUES (%s) ON CONFLICT DO NOTHING",
                (pet_type,)
            )
        
        conn.commit()
        print_color(f"  ✓ Seeded {count} pet types", Colors.GREEN)
        return True
        
    except psycopg2.Error as e:
        conn.rollback()
        print_color(f"  ✗ Error seeding types: {e}", Colors.RED)
        return False
    finally:
        cursor.close()
        conn.close()

def seed_specialties(conn_params, count=6):
    """Seed vet specialties"""
    conn = get_connection(conn_params)
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        for specialty in SPECIALTIES[:count]:
            cursor.execute(
                "INSERT INTO specialties (name) VALUES (%s) ON CONFLICT DO NOTHING",
                (specialty,)
            )
        
        conn.commit()
        print_color(f"  ✓ Seeded {count} specialties", Colors.GREEN)
        return True
        
    except psycopg2.Error as e:
        conn.rollback()
        print_color(f"  ✗ Error seeding specialties: {e}", Colors.RED)
        return False
    finally:
        cursor.close()
        conn.close()

def seed_owners(conn_params, count=1000):
    """Seed pet owners"""
    conn = get_connection(conn_params)
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        batch_size = 100
        for i in range(0, count, batch_size):
            batch = min(batch_size, count - i)
            values = []
            
            for _ in range(batch):
                first_name = choice(FIRST_NAMES)
                last_name = choice(LAST_NAMES)
                address = f"{randint(100, 9999)} {choice(STREET_NAMES)}"
                city = choice(CITIES)
                phone = f"{randint(100, 999)}{randint(100, 999)}{randint(1000, 9999)}"
                
                values.append((first_name, last_name, address, city, phone))
            
            cursor.executemany(
                """INSERT INTO owners (first_name, last_name, address, city, telephone) 
                   VALUES (%s, %s, %s, %s, %s)""",
                values
            )
            
            if (i + batch) % 100 == 0:
                print(f"  Inserted {i + batch}/{count} owners...")
        
        conn.commit()
        print_color(f"  ✓ Seeded {count} owners", Colors.GREEN)
        return True
        
    except psycopg2.Error as e:
        conn.rollback()
        print_color(f"  ✗ Error seeding owners: {e}", Colors.RED)
        return False
    finally:
        cursor.close()
        conn.close()

def seed_pets(conn_params, count=2000):
    """Seed pets (linked to owners)"""
    conn = get_connection(conn_params)
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Get available owner IDs and type IDs
        cursor.execute("SELECT id FROM owners")
        owner_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM types")
        type_ids = [row[0] for row in cursor.fetchall()]
        
        if not owner_ids or not type_ids:
            print_color("  ✗ No owners or types found. Please seed owners and types first.", Colors.RED)
            return False
        
        batch_size = 100
        for i in range(0, count, batch_size):
            batch = min(batch_size, count - i)
            values = []
            
            for _ in range(batch):
                name = choice(PET_NAMES)
                birth_date = f"20{randint(10, 23):02d}-{randint(1, 12):02d}-{randint(1, 28):02d}"
                type_id = choice(type_ids)
                owner_id = choice(owner_ids)
                
                values.append((name, birth_date, type_id, owner_id))
            
            cursor.executemany(
                """INSERT INTO pets (name, birth_date, type_id, owner_id) 
                   VALUES (%s, %s, %s, %s)""",
                values
            )
            
            if (i + batch) % 200 == 0:
                print(f"  Inserted {i + batch}/{count} pets...")
        
        conn.commit()
        print_color(f"  ✓ Seeded {count} pets", Colors.GREEN)
        return True
        
    except psycopg2.Error as e:
        conn.rollback()
        print_color(f"  ✗ Error seeding pets: {e}", Colors.RED)
        return False
    finally:
        cursor.close()
        conn.close()

def seed_vets(conn_params, count=50):
    """Seed veterinarians"""
    conn = get_connection(conn_params)
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        values = []
        for _ in range(count):
            first_name = choice(FIRST_NAMES)
            last_name = choice(LAST_NAMES)
            values.append((first_name, last_name))
        
        cursor.executemany(
            "INSERT INTO vets (first_name, last_name) VALUES (%s, %s)",
            values
        )
        
        conn.commit()
        print_color(f"  ✓ Seeded {count} vets", Colors.GREEN)
        return True
        
    except psycopg2.Error as e:
        conn.rollback()
        print_color(f"  ✗ Error seeding vets: {e}", Colors.RED)
        return False
    finally:
        cursor.close()
        conn.close()

def seed_vet_specialties(conn_params):
    """Link vets to specialties (many-to-many relationship)"""
    conn = get_connection(conn_params)
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Get available vet and specialty IDs
        cursor.execute("SELECT id FROM vets")
        vet_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM specialties")
        specialty_ids = [row[0] for row in cursor.fetchall()]
        
        if not vet_ids or not specialty_ids:
            print_color("  ✗ No vets or specialties found. Please seed vets and specialties first.", Colors.RED)
            return False
        
        # Assign 1-3 specialties to each vet
        values = []
        for vet_id in vet_ids:
            num_specialties = randint(1, min(3, len(specialty_ids)))
            assigned_specialties = sample(specialty_ids, num_specialties)
            
            for specialty_id in assigned_specialties:
                values.append((vet_id, specialty_id))
        
        cursor.executemany(
            "INSERT INTO vet_specialties (vet_id, specialty_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            values
        )
        
        conn.commit()
        print_color(f"  ✓ Seeded {len(values)} vet-specialty associations", Colors.GREEN)
        return True
        
    except psycopg2.Error as e:
        conn.rollback()
        print_color(f"  ✗ Error seeding vet_specialties: {e}", Colors.RED)
        return False
    finally:
        cursor.close()
        conn.close()

def seed_visits(conn_params, count=5000):
    """Seed pet visits"""
    conn = get_connection(conn_params)
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Get available pet IDs
        cursor.execute("SELECT id FROM pets")
        pet_ids = [row[0] for row in cursor.fetchall()]
        
        if not pet_ids:
            print_color("  ✗ No pets found. Please seed pets first.", Colors.RED)
            return False
        
        descriptions = [
            'Annual checkup', 'Vaccination', 'Dental cleaning', 'Surgery consultation',
            'Skin condition', 'Weight check', 'Behavior consultation', 'Emergency visit',
            'Follow-up examination', 'Routine care'
        ]
        
        batch_size = 200
        for i in range(0, count, batch_size):
            batch = min(batch_size, count - i)
            values = []
            
            for _ in range(batch):
                pet_id = choice(pet_ids)
                visit_date = f"20{randint(20, 24):02d}-{randint(1, 12):02d}-{randint(1, 28):02d}"
                description = choice(descriptions)
                
                values.append((pet_id, visit_date, description))
            
            cursor.executemany(
                """INSERT INTO visits (pet_id, visit_date, description) 
                   VALUES (%s, %s, %s)""",
                values
            )
            
            if (i + batch) % 500 == 0:
                print(f"  Inserted {i + batch}/{count} visits...")
        
        conn.commit()
        print_color(f"  ✓ Seeded {count} visits", Colors.GREEN)
        return True
        
    except psycopg2.Error as e:
        conn.rollback()
        print_color(f"  ✗ Error seeding visits: {e}", Colors.RED)
        return False
    finally:
        cursor.close()
        conn.close()

def seed_all_tables(conn_params):
    """Seed all PetClinic tables with test data"""
    print_header("Seeding Database with Test Data")
    
    # Seed in correct order (respecting foreign keys)
    steps = [
        ("Types", lambda: seed_types(conn_params, 6)),
        ("Specialties", lambda: seed_specialties(conn_params, 6)),
        ("Owners", lambda: seed_owners(conn_params, 1000)),
        ("Pets", lambda: seed_pets(conn_params, 2000)),
        ("Vets", lambda: seed_vets(conn_params, 50)),
        ("Vet Specialties", lambda: seed_vet_specialties(conn_params)),
        ("Visits", lambda: seed_visits(conn_params, 5000))
    ]
    
    for name, func in steps:
        print(f"\nSeeding {name}...")
        if not func():
            print_color(f"Failed to seed {name}. Stopping.", Colors.RED)
            return False
    
    print()
    print_color("✓ All tables seeded successfully!", Colors.GREEN)
    return True

def run_jmeter_test(env_config, results_dir, timeout=600):
    """Run JMeter test"""
    print_header("[Step 4/7] Running JMeter Test")
    
    # Create results directory
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamped filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    jtl_file = results_dir / f"results_{timestamp}.jtl"
    report_dir = results_dir / f"report_{timestamp}"
    log_file = results_dir / f"jmeter_{timestamp}.log"
    
    # Prepare JMeter command
    jmeter_cmd = 'jmeter.bat' if os.name == 'nt' else 'jmeter'
    cmd = [
        jmeter_cmd,
        '-n',  # Non-GUI mode
        '-t', str(JMETER_TEST_PLAN),
        '-l', str(jtl_file),
        '-e',  # Generate HTML report
        '-o', str(report_dir),
        '-j', str(log_file),
        f"-JDB_SERVER={env_config.get('host') or env_config.get('server')}",
        f"-JDB_PORT={env_config.get('port', '5432')}",
        f"-JDB_NAME={env_config['database']}",
        f"-JDB_USER={env_config['username']}",
        f"-JDB_PASSWORD={env_config['password']}"
    ]
    
    print(f"  Test Plan: {JMETER_TEST_PLAN}")
    print(f"  Results: {jtl_file}")
    print(f"  Report: {report_dir}")
    print(f"  Timeout: {timeout} seconds")
    print()
    print_color("  Starting JMeter test...", Colors.YELLOW)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        
        if result.returncode == 0:
            print_color("  ✓ JMeter test completed successfully", Colors.GREEN)
            
            # Parse JMeter log for summary
            try:
                with open(log_file, 'r') as f:
                    log_content = f.read()
                    if 'summary =' in log_content:
                        summary_lines = [line for line in log_content.split('\n') if 'summary =' in line]
                        if summary_lines:
                            print()
                            print_color("  Test Summary:", Colors.CYAN)
                            for line in summary_lines[-1:]:
                                print(f"    {line.split('summary =')[1].strip()}")
            except Exception:
                pass
        else:
            print_color(f"  ✗ JMeter test failed with return code {result.returncode}", Colors.RED)
            if result.stderr:
                print(f"    Error: {result.stderr[:200]}")
    
    except subprocess.TimeoutExpired:
        print_color("  ✗ JMeter test timed out", Colors.RED)
    except Exception as e:
        print_color(f"  ✗ Error running JMeter: {e}", Colors.RED)
    
    print()
    return jtl_file, report_dir

def start_performance_monitoring(perf_file):
    """Start Windows performance monitoring"""
    print_header("[Step 3/7] Starting Performance Monitoring")
    
    if os.name != 'nt':
        print_color("  ⚠ Performance monitoring only available on Windows", Colors.YELLOW)
        return None
    
    try:
        perf_cmd = ['typeperf',
            r'\Processor(_Total)\% Processor Time',
            r'\Memory\Available MBytes',
            r'\Memory\% Committed Bytes In Use',
            r'\PhysicalDisk(_Total)\Disk Reads/sec',
            r'\PhysicalDisk(_Total)\Disk Writes/sec',
            r'\Network Interface(*)\Bytes Total/sec',
            '-si', '1',
            '-o', str(perf_file)
        ]
        
        proc = subprocess.Popen(perf_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print_color("  ✓ Performance monitoring started", Colors.GREEN)
        print(f"    Output file: {perf_file}")
        print(f"    Process ID: {proc.pid}")
        print()
        return proc
    except Exception as e:
        print_color(f"  ✗ Failed to start monitoring: {e}", Colors.RED)
        print()
        return None

def stop_performance_monitoring(proc):
    """Stop performance monitoring process"""
    print_header("[Step 5/7] Stopping Performance Monitoring")
    
    if proc is None:
        print_color("  ⚠ No monitoring process to stop", Colors.YELLOW)
        print()
        return
    
    try:
        # Try graceful shutdown first
        if os.name == 'nt':
            subprocess.run(['taskkill', '/F', '/PID', str(proc.pid)], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
        else:
            proc.send_signal(signal.SIGINT)
            proc.wait(timeout=3)
        print_color("  ✓ Performance monitoring stopped", Colors.GREEN)
    except subprocess.TimeoutExpired:
        print_color("  ⚠ Monitoring process timeout, forcing termination", Colors.YELLOW)
        try:
            proc.kill()
            proc.wait(timeout=1)
        except:
            pass
    except KeyboardInterrupt:
        print_color("  ⚠ Interrupted - forcing process termination", Colors.YELLOW)
        try:
            proc.kill()
        except:
            pass
        raise
    except Exception as e:
        print_color(f"  ⚠ Error stopping monitoring: {e}", Colors.YELLOW)
        try:
            proc.kill()
        except:
            pass
    print()

def clean_csv(file_path):
    """Clean Windows typeperf CSV output"""
    with open(file_path, 'r', encoding='utf-16') as f:
        lines = f.readlines()
    
    # Remove first line (PDH header)
    if lines and lines[0].startswith('"(PDH-CSV'):
        lines = lines[1:]
    
    clean_file = file_path.with_suffix('.clean.csv')
    with open(clean_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    return clean_file

def generate_performance_graphs(perf_csv, output_file):
    """Generate performance graphs"""
    if not GRAPHING_AVAILABLE:
        print_color("  ⚠ Graphing libraries not available (install pandas and matplotlib)", Colors.YELLOW)
        return
    
    try:
        df = pd.read_csv(perf_csv)
        df.columns = df.columns.str.strip('"')
        df['Timestamp'] = pd.to_datetime(df.iloc[:, 0], format='%m/%d/%Y %H:%M:%S.%f')
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('System Performance During Test', fontsize=16)
        
        # CPU Usage
        cpu_col = [col for col in df.columns if 'Processor Time' in col][0]
        axes[0, 0].plot(df['Timestamp'], df[cpu_col], label='CPU Usage', color='blue')
        axes[0, 0].axhline(y=df[cpu_col].mean(), color='r', linestyle='--', label=f'Avg: {df[cpu_col].mean():.1f}%')
        axes[0, 0].fill_between(df['Timestamp'], df[cpu_col], alpha=0.3)
        axes[0, 0].set_ylabel('CPU %')
        axes[0, 0].set_title('CPU Usage')
        axes[0, 0].legend()
        axes[0, 0].grid(True)
        
        # Memory Usage
        mem_col = [col for col in df.columns if 'Committed Bytes In Use' in col][0]
        axes[0, 1].plot(df['Timestamp'], df[mem_col], label='Memory Usage', color='green')
        axes[0, 1].axhline(y=df[mem_col].mean(), color='r', linestyle='--', label=f'Avg: {df[mem_col].mean():.1f}%')
        axes[0, 1].fill_between(df['Timestamp'], df[mem_col], alpha=0.3)
        axes[0, 1].set_ylabel('Memory %')
        axes[0, 1].set_title('Memory Usage')
        axes[0, 1].legend()
        axes[0, 1].grid(True)
        
        # Disk I/O
        disk_read = [col for col in df.columns if 'Disk Reads' in col][0]
        disk_write = [col for col in df.columns if 'Disk Writes' in col][0]
        axes[1, 0].plot(df['Timestamp'], df[disk_read], label='Reads', color='orange')
        axes[1, 0].plot(df['Timestamp'], df[disk_write], label='Writes', color='purple')
        axes[1, 0].set_ylabel('Operations/sec')
        axes[1, 0].set_title('Disk I/O')
        axes[1, 0].legend()
        axes[1, 0].grid(True)
        
        # Network Activity
        net_cols = [col for col in df.columns if 'Bytes Total/sec' in col]
        if net_cols:
            net_data = df[net_cols].sum(axis=1) / 1024 / 1024  # Convert to MB/s
            axes[1, 1].plot(df['Timestamp'], net_data, label='Network', color='red')
            axes[1, 1].set_ylabel('MB/s')
            axes[1, 1].set_title('Network Activity')
            axes[1, 1].legend()
            axes[1, 1].grid(True)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print_color(f"  ✓ Performance graphs saved: {output_file}", Colors.GREEN)
        plt.close()
    except Exception as e:
        print_color(f"  ✗ Error generating graphs: {e}", Colors.RED)

def process_performance_data(perf_file, results_dir):
    """Process and graph performance data"""
    print_header("[Step 6/7] Processing Performance Data")
    
    if not perf_file.exists():
        print_color("  ⚠ Performance data file not found", Colors.YELLOW)
        print()
        return
    
    try:
        clean_file = clean_csv(perf_file)
        print_color(f"  ✓ Cleaned performance data: {clean_file}", Colors.GREEN)
        
        graph_file = results_dir / f"performance_graphs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        generate_performance_graphs(clean_file, graph_file)
    except Exception as e:
        print_color(f"  ✗ Error processing performance data: {e}", Colors.RED)
    print()

def consolidate_results(jtl_file, report_dir, perf_file):
    """Consolidate and display final results"""
    print_header("[Step 7/7] Test Results Summary")
    
    files_exist = []
    if jtl_file.exists():
        files_exist.append(f"  ✓ JMeter Results: {jtl_file}")
    if report_dir.exists():
        files_exist.append(f"  ✓ HTML Report: {report_dir}/index.html")
    if perf_file and perf_file.exists():
        files_exist.append(f"  ✓ Performance Data: {perf_file}")
        clean_file = perf_file.with_suffix('.clean.csv')
        if clean_file.exists():
            files_exist.append(f"  ✓ Cleaned CSV: {clean_file}")
    
    graph_files = list(JMETER_RESULTS_DIR.glob("performance_graphs_*.png"))
    if graph_files:
        files_exist.append(f"  ✓ Performance Graphs: {graph_files[-1]}")
    
    if files_exist:
        print_color("Test outputs:", Colors.GREEN)
        for line in files_exist:
            print(line)
    else:
        print_color("  ⚠ No output files found", Colors.YELLOW)
    print()

def main():
    parser = argparse.ArgumentParser(
        description='JMeter Database Performance Test Runner for PetClinic',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run JMeter test with profiling
  python run_and_monitor_db_test.py --env target
  
  # Run without profiling (faster)
  python run_and_monitor_db_test.py --env target --no-profiling
  
  # Skip database seeding (reuse existing data)
  python run_and_monitor_db_test.py --env target --no-seed
  
  # Cleanup only
  python run_and_monitor_db_test.py --env target --cleanup
        """)
    
    parser.add_argument('--env', '--environment', type=str, dest='environment', default='target',
                       help='Database environment from config file (source, target, local)')
    parser.add_argument('--config', type=str, default='../../db_config.json',
                       help='Path to configuration file (default: ../../db_config.json)')
    parser.add_argument('--cleanup', action='store_true',
                       help='Clean up all records from database tables (use before/after testing)')
    parser.add_argument('--no-profiling', action='store_true',
                       help='Skip system performance profiling')
    parser.add_argument('--no-seed', action='store_true',
                       help='Skip database seeding')
    parser.add_argument('--timeout', type=int, default=1800,
                       help='JMeter test timeout in seconds (default: 1800)')
    
    args = parser.parse_args()
    
    # Load from configuration file
    conn_params, database_name = get_connection_from_config(
        args.environment, 
        Path(args.config)
    )
    if not conn_params:
        print("\nFailed to load configuration. Exiting.")
        sys.exit(1)
    
    # Load environment config for JMeter
    config = load_config(Path(args.config))
    env_config = config['environments'][args.environment]
    
    # If cleanup flag is set, run cleanup and exit
    if args.cleanup:
        cleanup_database(conn_params)
        return
    
    # JMeter execution path
    print_header("PETCLINIC DATABASE PERFORMANCE TEST - JMETER MODE")
    print(f"Environment: {args.environment}")
    print(f"Database: {database_name}")
    print()
    
    # Check JMeter installation
    print_header("[Step 1/7] Checking Prerequisites")
    if not check_jmeter():
        sys.exit(1)
    print()
    
    # Step 2: Cleanup
    print_header("[Step 2/7] Cleaning Database")
    cleanup_database(conn_params)
    print()
    
    # Step 3: Seeding (unless skipped)
    if not args.no_seed:
        if not seed_all_tables(conn_params):
            print_color("\nDatabase seeding failed. Exiting.", Colors.RED)
            sys.exit(1)
    
    # Setup directories
    JMETER_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Performance monitoring (if enabled)
    perf_proc = None
    perf_file = None
    if not args.no_profiling and os.name == 'nt':
        perf_file = JMETER_RESULTS_DIR / f"performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        perf_proc = start_performance_monitoring(perf_file)
        time.sleep(2)  # Let monitoring stabilize
    
    # Run JMeter test
    jtl_file, report_dir = run_jmeter_test(env_config, JMETER_RESULTS_DIR, timeout=args.timeout)
    
    # Stop monitoring
    if perf_proc:
        stop_performance_monitoring(perf_proc)
    
    # Process performance data
    if perf_file and not args.no_profiling:
        process_performance_data(perf_file, JMETER_RESULTS_DIR)
    
    # Consolidate results
    consolidate_results(jtl_file, report_dir, perf_file)
    
    print_color("\n" + "=" * 70, Colors.GREEN)
    print_color("JMETER TEST COMPLETED SUCCESSFULLY!", Colors.GREEN)
    print_color("=" * 70, Colors.GREEN)
    print()
    print(f"Results directory: {JMETER_RESULTS_DIR}")
    print(f"Open report: {report_dir}/index.html")
    print()

if __name__ == "__main__":
    main()
