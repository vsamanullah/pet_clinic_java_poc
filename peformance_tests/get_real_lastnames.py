import psycopg2
import json
import sys
sys.path.append('..')

# Load database config
with open('../db_config.json') as f:
    config = json.load(f)['environments']['target']
    # Remove non-psycopg2 fields
    db_config = {
        'host': config['host'],
        'port': config['port'],
        'database': config['database'],
        'user': config['username'],
        'password': config['password']
    }

# Connect and get last names
conn = psycopg2.connect(**db_config)
cur = conn.cursor()

cur.execute('SELECT DISTINCT last_name, COUNT(*) as count FROM owners GROUP BY last_name ORDER BY count DESC, last_name LIMIT 30')
results = cur.fetchall()

print('Last names in database with owner count:')
print('-' * 40)
for name, count in results:
    print(f'{name:<20} {count:>3} owners')

cur.close()
conn.close()

# Write to CSV
print('\nWriting to common_last_names.csv...')
with open('common_last_names.csv', 'w') as f:
    f.write('searchLastName\n')
    for name, _ in results:
        f.write(f'{name}\n')
print('Done!')
