import requests
import re

# Test search results
r = requests.get('http://10.134.77.66:8080/petclinic/owners.html', params={'lastName': 'Davis'})
print(f'Search Status: {r.status_code}')
print('\nAll owner links:')
links = re.findall(r'href="([^"]*owners/\d+[^"]*)"', r.text)
for link in links[:5]:
    print(f'  {link}')

print('\nTrying JMeter regex patterns:')
# Current pattern in JMeter
pattern1 = r'/owners/(\d+)\.html'
matches1 = re.findall(pattern1, r.text)
print(f'Pattern "/owners/(\\d+)\\.html": {matches1[:3] if matches1 else "NO MATCH"}')

# Try with context path
pattern2 = r'/petclinic/owners/(\d+)\.html'
matches2 = re.findall(pattern2, r.text)
print(f'Pattern "/petclinic/owners/(\\d+)\\.html": {matches2[:3] if matches2 else "NO MATCH"}')

# Try relative pattern
pattern3 = r'owners/(\d+)\.html'
matches3 = re.findall(pattern3, r.text)
print(f'Pattern "owners/(\\d+)\\.html": {matches3[:3] if matches3 else "NO MATCH"}')
