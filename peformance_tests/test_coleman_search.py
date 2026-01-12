import requests

# Test Coleman search
r = requests.get('http://10.134.77.66:8080/petclinic/owners.html', 
                 params={'lastName': 'Coleman'}, 
                 allow_redirects=False)
print(f'Status: {r.status_code}')
print(f'Location: {r.headers.get("Location", "None")}')

# With redirects
r2 = requests.get('http://10.134.77.66:8080/petclinic/owners.html', 
                  params={'lastName': 'Coleman'})
print(f'\nWith redirects:')
print(f'Final URL: {r2.url}')
print(f'Status: {r2.status_code}')
print(f'Has "Owner Information" in body: {"Owner Information" in r2.text}')
