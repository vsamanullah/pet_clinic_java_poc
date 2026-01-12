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

# Get owners with their pet counts
cur.execute('''
    SELECT o.id, o.first_name, o.last_name, COUNT(p.id) as pet_count
    FROM owners o
    LEFT JOIN pets p ON o.id = p.owner_id
    GROUP BY o.id, o.first_name, o.last_name
    HAVING COUNT(p.id) > 0
    ORDER BY pet_count DESC, o.last_name
    LIMIT 20
''')

print('Owners with pets:')
print('-' * 60)
print(f'{"ID":<5} {"Name":<25} {"Last Name":<15} {"Pets":>5}')
print('-' * 60)

owners_with_pets = []
for oid, fname, lname, count in cur.fetchall():
    print(f'{oid:<5} {fname:<25} {lname:<15} {count:>5}')
    owners_with_pets.append((oid, lname))

cur.close()
conn.close()

# Get unique last names of owners who have pets
unique_lastnames = {}
for oid, lname in owners_with_pets:
    if lname not in unique_lastnames:
        unique_lastnames[lname] = oid

print(f'\n\nUnique last names with pets: {len(unique_lastnames)}')
print('Writing to common_last_names.csv...')

with open('common_last_names.csv', 'w') as f:
    f.write('searchLastName\n')
    for lname in unique_lastnames.keys():
        f.write(f'{lname}\n')

print('Done!')
