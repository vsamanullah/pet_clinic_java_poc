import requests
import re

r = requests.get('http://10.134.77.66:8080/petclinic/owners/2.html')
print(f'Status: {r.status_code}')

# Find visit links
patterns = re.findall(r'href="([^"]*visits/new[^"]*)"', r.text)
print(f'\nVisit links found: {len(patterns)}')
for p in patterns[:5]:
    print(f'  {p}')

# Try the regex from JMeter
jmeter_regex = r'/owners/2/pets/(\d+)/visits/new'
pet_ids = re.findall(jmeter_regex, r.text)
print(f'\nPet IDs with JMeter regex: {pet_ids}')

# Show some context around visit links
import re
contexts = re.findall(r'.{0,50}(/owners/\d+/pets/\d+/visits/new).{0,50}', r.text)
print(f'\nContexts around visit links:')
for c in contexts[:3]:
    print(f'  {c}')
