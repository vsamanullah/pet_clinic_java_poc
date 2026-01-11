import requests
from datetime import datetime

session = requests.Session()

# Get the visit form
r1 = session.get('http://10.134.77.66:8080/petclinic/owners/2/pets/2/visits/new')
print(f'GET status: {r1.status_code}')

# Submit the form
data = {
    'date': datetime.now().strftime('%Y/%m/%d'),
    'description': 'Checkup'
}
r2 = session.post('http://10.134.77.66:8080/petclinic/owners/2/pets/2/visits/new', data=data)
print(f'POST status: {r2.status_code}')
print(f'Final URL: {r2.url}')
print(f'Response length: {len(r2.text)}')
if r2.status_code >= 400:
    print('Error response:')
    print(r2.text[:1000])
