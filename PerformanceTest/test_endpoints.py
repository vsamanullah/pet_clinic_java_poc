"""
Test PetClinic endpoints to verify correct URL patterns
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://10.134.77.66:8080/petclinic"

def test_endpoint(method, path, data=None, follow_redirects=True, description=""):
    """Test an endpoint and print results"""
    url = BASE_URL + path
    print(f"\n{'='*80}")
    print(f"Testing: {description}")
    print(f"{method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, allow_redirects=follow_redirects)
        elif method == "POST":
            print(f"POST Data: {data}")
            response = requests.post(url, data=data, allow_redirects=follow_redirects)
        
        print(f"Status Code: {response.status_code}")
        print(f"Final URL: {response.url}")
        
        # Check for redirects
        if response.history:
            print(f"Redirect History:")
            for i, resp in enumerate(response.history, 1):
                print(f"  {i}. {resp.status_code} -> {resp.url}")
        
        # Look for important patterns in response
        content = response.text
        
        # Check for owner ID in response
        if "/owners/" in content:
            import re
            owner_links = re.findall(r'/owners/(\d+)', content)
            if owner_links:
                print(f"Found owner IDs in response: {set(owner_links)}")
        
        # Check for pet links
        if "/pets/" in content:
            import re
            pet_links = re.findall(r'/pets/(\d+)', content)
            if pet_links:
                print(f"Found pet IDs in response: {set(pet_links)}")
        
        # Check for Add Pet link
        if "pets/new" in content:
            import re
            add_pet_links = re.findall(r'href="([^"]*pets/new[^"]*)"', content)
            if add_pet_links:
                print(f"Found 'Add Pet' links: {add_pet_links}")
        
        # Check for Add Visit link
        if "visits/new" in content:
            import re
            add_visit_links = re.findall(r'href="([^"]*visits/new[^"]*)"', content)
            if add_visit_links:
                print(f"Found 'Add Visit' links: {add_visit_links}")
        
        return response
        
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def main():
    print("="*80)
    print("PetClinic Endpoint Testing")
    print("="*80)
    
    # Test 1: Home page
    test_endpoint("GET", "/", description="Home Page")
    
    # Test 2: Find owners page
    test_endpoint("GET", "/owners/find.html", description="Find Owners Page")
    
    # Test 3: Search for existing owner
    test_endpoint("GET", "/owners.html?lastName=Davis", description="Search for Davis")
    
    # Test 4: View specific owner (use a known ID like 1)
    test_endpoint("GET", "/owners/1.html", description="View Owner 1")
    
    # Test 5: Get add owner form
    test_endpoint("GET", "/owners/new", description="Get New Owner Form")
    
    # Test 6: Create a new owner
    new_owner_data = {
        'firstName': 'TestUser',
        'lastName': 'Python',
        'address': '123 Test Street',
        'city': 'Madison',
        'telephone': '6085559999'
    }
    response = test_endpoint("POST", "/owners/new", data=new_owner_data, 
                           description="Create New Owner")
    
    if response and response.status_code in [200, 302]:
        # Extract owner ID from redirect or response
        import re
        
        # Try from URL
        owner_id = None
        if response.url and "/owners/" in response.url:
            match = re.search(r'/owners/(\d+)', response.url)
            if match:
                owner_id = match.group(1)
        
        # Try from response body
        if not owner_id and response.text:
            # Look for pets/new link
            match = re.search(r'/owners/(\d+)/pets/new', response.text)
            if match:
                owner_id = match.group(1)
        
        if owner_id:
            print(f"\n{'='*80}")
            print(f"✓ Successfully created owner with ID: {owner_id}")
            print(f"{'='*80}")
            
            # Test 7: Get add pet form
            test_endpoint("GET", f"/owners/{owner_id}/pets/new", 
                        description=f"Get New Pet Form for Owner {owner_id}")
            
            # Test 8: Create a new pet
            new_pet_data = {
                'name': 'TestPet',
                'birthDate': datetime.now().strftime('%Y/%m/%d'),
                'type': 'dog'
            }
            pet_response = test_endpoint("POST", f"/owners/{owner_id}/pets/new", 
                                       data=new_pet_data, 
                                       description=f"Create New Pet for Owner {owner_id}")
            
            if pet_response and pet_response.status_code in [200, 302]:
                # Extract pet ID
                import re
                pet_id = None
                
                # Look for pet ID in visits/new link
                if pet_response.text:
                    match = re.search(r'/pets/(\d+)/visits/new', pet_response.text)
                    if match:
                        pet_id = match.group(1)
                
                if pet_id:
                    print(f"\n{'='*80}")
                    print(f"✓ Successfully created pet with ID: {pet_id}")
                    print(f"{'='*80}")
                    
                    # Test 9: Get add visit form
                    test_endpoint("GET", f"/owners/{owner_id}/pets/{pet_id}/visits/new", 
                                description=f"Get New Visit Form for Pet {pet_id}")
                    
                    # Test 10: Create a visit
                    new_visit_data = {
                        'date': datetime.now().strftime('%Y/%m/%d'),
                        'description': 'Test visit from Python script'
                    }
                    test_endpoint("POST", f"/owners/{owner_id}/pets/{pet_id}/visits/new", 
                                data=new_visit_data, 
                                description=f"Create New Visit for Pet {pet_id}")
    
    # Test 11: Vets page
    test_endpoint("GET", "/vets.html", description="Vets Page (HTML)")
    test_endpoint("GET", "/vets.json", description="Vets Page (JSON)")
    
    print(f"\n{'='*80}")
    print("Testing Complete")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
