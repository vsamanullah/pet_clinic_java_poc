"""
Generate multi_pet_owner_ids.csv from database
Queries for owner IDs that have 3 or more pets
"""
import psycopg2
import csv
import json
import os

# Load database configuration
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
config_path = os.path.join(project_root, 'db_config.json')

with open(config_path, 'r') as f:
    config = json.load(f)

# Use target environment
db_config = config['environments']['target']

print("Connecting to database...")
print(f"Host: {db_config['host']}")
print(f"Database: {db_config['database']}")

# Connect to database
conn = psycopg2.connect(
    host=db_config['host'],
    port=db_config['port'],
    database=db_config['database'],
    user=db_config['username'],
    password=db_config['password'],
    sslmode='require'
)

cursor = conn.cursor()

# Query for owners with 3+ pets
print("\nQuerying for owners with 3 or more pets...")
query = """
SELECT o.id as owner_id, COUNT(p.id) as pet_count
FROM owners o
INNER JOIN pets p ON o.id = p.owner_id
GROUP BY o.id
HAVING COUNT(p.id) >= 3
ORDER BY pet_count DESC, o.id
LIMIT 100;
"""

cursor.execute(query)
results = cursor.fetchall()

print(f"Found {len(results)} owners with 3+ pets")

# Write to CSV
output_file = os.path.join(script_dir, 'multi_pet_owner_ids.csv')
with open(output_file, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['ownerId'])
    
    for row in results:
        owner_id, pet_count = row
        writer.writerow([owner_id])
        print(f"  Owner ID: {owner_id} - {pet_count} pets")

print(f"\n✅ Created: {output_file}")
print(f"Total records: {len(results)}")

# Close connection
cursor.close()
conn.close()
