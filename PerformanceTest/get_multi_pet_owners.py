import psycopg2
import json

# Load database config
with open('../db_config.json') as f:
    config = json.load(f)['environments']['target']
    db_config = {
        'host': config['host'],
        'port': config['port'],
        'database': config['database'],
        'user': config['username'],
        'password': config['password']
    }

conn = psycopg2.connect(**db_config)
cur = conn.cursor()

# Get owners with 2+ pets
cur.execute('''
    SELECT o.id, o.first_name, o.last_name, COUNT(p.id) as pet_count
    FROM owners o
    JOIN pets p ON o.id = p.owner_id
    GROUP BY o.id, o.first_name, o.last_name
    HAVING COUNT(p.id) >= 2
    ORDER BY pet_count DESC, o.last_name
''')

print('Owners with 2+ pets:')
print('-' * 60)
print(f'{"ID":<5} {"Name":<25} {"Last Name":<15} {"Pets":>5}')
print('-' * 60)

multi_pet_owners = []
for oid, fname, lname, count in cur.fetchall():
    print(f'{oid:<5} {fname:<25} {lname:<15} {count:>5}')
    multi_pet_owners.append(oid)

cur.close()
conn.close()

print(f'\n\nTotal owners with 2+ pets: {len(multi_pet_owners)}')

if len(multi_pet_owners) == 0:
    print('\nWARNING: No owners with multiple pets found!')
    print('Test 03 requires owners with at least 2 pets.')
else:
    print('\nWriting to multi_pet_owner_ids.csv...')
    with open('multi_pet_owner_ids.csv', 'w') as f:
        f.write('ownerId\n')
        for oid in multi_pet_owners:
            f.write(f'{oid}\n')
    print('Done!')
