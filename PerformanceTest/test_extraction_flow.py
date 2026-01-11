import requests
import re

# Step 1: Search for Coleman (owner with 2 pets)
r1 = requests.get('http://10.134.77.66:8080/petclinic/owners.html', params={'lastName': 'Coleman'})
print(f'Search status: {r1.status_code}')

# Extract owner IDs
owner_ids = re.findall(r'/owners/(\d+)\.html', r1.text)
print(f'Owner IDs found: {owner_ids[:3]}')

if owner_ids:
    oid = owner_ids[0]
    print(f'\nTesting owner ID: {oid}')
    
    # Step 2: Get owner detail page
    r2 = requests.get(f'http://10.134.77.66:8080/petclinic/owners/{oid}.html')
    print(f'Owner detail status: {r2.status_code}')
    
    # Extract pet IDs using JMeter regex
    pet_ids = re.findall(r'/owners/\d+/pets/(\d+)/visits/new', r2.text)
    print(f'\nPet IDs extracted: {pet_ids}')
    
    # Show all visit links
    print('\nAll visit links found:')
    links = re.findall(r'href="([^"]*visits/new[^"]*)"', r2.text)
    for link in links:
        print(f'  {link}')
    
    # Show HTML context around visit links
    print('\nHTML context around visit links:')
    contexts = re.findall(r'.{50}/owners/\d+/pets/\d+/visits/new.{50}', r2.text, re.DOTALL)
    for i, ctx in enumerate(contexts[:2]):
        print(f'\n  Context {i+1}:')
        print(f'  {repr(ctx)}')
