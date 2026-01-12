# PetClinic Application Analysis for Performance Testing

## Application Overview
**Base URL**: http://10.134.77.66:8080/petclinic
**Framework**: Spring Framework Demonstration
**Type**: Veterinary Clinic Management System

## Data Model & Relationships

### 1. Owners (1,000+ records)
- **Fields**: First Name, Last Name, Address, City, Telephone
- **Relationships**: One-to-Many with Pets
- **Key Operations**: Search, Create, Read, Update, List

### 2. Pets (2,000+ records)
- **Fields**: Name, Birth Date, Type (bird/cat/dog/hamster/lizard/snake)
- **Relationships**: Many-to-One with Owners, One-to-Many with Visits
- **Key Operations**: Create, Read, Update (linked to Owner)

### 3. Visits (5,000+ records)
- **Fields**: Visit Date, Description
- **Relationships**: Many-to-One with Pets
- **Key Operations**: Create, Read (linked to Pet)
- **Sample Descriptions**: Annual checkup, Vaccination, Skin condition, Behavior consultation, Surgery consultation, Follow-up examination

### 4. Veterinarians (50 records)
- **Fields**: First Name, Last Name, Specialties (array)
- **Specialties Available**: cardiology, dentistry, dermatology, neurology, radiology, surgery
- **Key Operations**: List, View (Read-only display)

## Discovered Endpoints

### HTML Endpoints (Web UI)
1. **Home Page**
   - GET `/petclinic/` - Landing page

2. **Owner Management**
   - GET `/petclinic/owners/find.html` - Search form
   - GET `/petclinic/owners.html?lastName={name}` - Search results (paginated list)
   - GET `/petclinic/owners/{id}.html` - Owner detail with pets and visits
   - GET `/petclinic/owners/new` - Add owner form
   - POST `/petclinic/owners/new` - Create owner
   - GET `/petclinic/owners/{id}/edit.html` - Edit owner form
   - POST `/petclinic/owners/{id}/edit` - Update owner

3. **Pet Management**
   - GET `/petclinic/owners/{ownerId}/pets/new.html` - Add pet form
   - POST `/petclinic/owners/{ownerId}/pets/new` - Create pet
   - GET `/petclinic/owners/{ownerId}/pets/{petId}/edit` - Edit pet form
   - POST `/petclinic/owners/{ownerId}/pets/{petId}/edit` - Update pet

4. **Visit Management**
   - GET `/petclinic/owners/{ownerId}/pets/{petId}/visits/new` - Add visit form
   - POST `/petclinic/owners/{ownerId}/pets/{petId}/visits/new` - Create visit

5. **Veterinarian Management**
   - GET `/petclinic/vets.html` - List all veterinarians with specialties

### REST API Endpoints (JSON)
1. **Veterinarians API**
   - GET `/petclinic/vets.json` - JSON list of all vets with specialties
   - GET `/petclinic/vets.xml` - XML list of all vets with specialties

2. **Potential REST APIs** (to be discovered/tested)
   - `/petclinic/api/owners` - Owners REST API
   - `/petclinic/api/pets` - Pets REST API  
   - `/petclinic/api/visits` - Visits REST API

## Critical Business Scenarios for Performance Testing

### Scenario 1: New Client Registration (End-to-End)
**User Journey**: New client brings pet to clinic
1. Search for owner by last name (verify not duplicate)
2. Create new owner with complete information
3. Add first pet to newly created owner
4. Schedule initial visit for new pet

**Performance KPIs**:
- Total journey time: < 5 seconds
- Each step response time: < 1 second
- Concurrent registrations: 20 users

### Scenario 2: Returning Client Visit Scheduling
**User Journey**: Existing client needs to schedule checkup
1. Search owner by last name
2. Navigate search results (may have multiple matches)
3. View owner details with pet history
4. Add new visit to existing pet

**Performance KPIs**:
- Search response time: < 500ms
- Owner detail load: < 1 second
- Visit creation: < 1 second
- Concurrent searches: 20 users

### Scenario 3: Multi-Pet Owner Management
**User Journey**: Owner with multiple pets needs various updates
1. Find owner with multiple pets (e.g., Barbara Anderson with 3 pets)
2. Add new pet to existing owner
3. Update existing pet information (e.g., type correction)
4. Schedule visits for multiple pets

**Performance KPIs**:
- Owner detail with 3+ pets: < 2 seconds
- Pet operations: < 1 second each
- Concurrent multi-pet updates: 20 users

### Scenario 4: Veterinarian Directory Lookup
**User Journey**: Client wants to know available specialties
1. View list of all veterinarians (50 vets)
2. Filter/search veterinarians by specialty
3. View specialties for specific vet

**Performance KPIs**:
- Vets list load: < 1 second
- JSON API response: < 500ms
- Concurrent lookups: 20 users

### Scenario 5: High-Volume Owner Search
**User Journey**: Receptionist searching frequent common names
1. Search by common last name (e.g., "Anderson")
2. Navigate paginated results (potentially 100+ matches)
3. Export search results to PDF
4. Drill down to specific owner

**Performance KPIs**:
- Search with 100+ results: < 2 seconds
- Pagination: < 500ms per page
- PDF export: < 3 seconds
- Concurrent searches: 20 users

### Scenario 6: Visit History Review
**User Journey**: Veterinarian reviewing pet's medical history
1. Search and find owner
2. View owner detail page (showing all pets and visit histories)
3. Review visit descriptions for specific pet
4. Add follow-up visit based on history

**Performance KPIs**:
- Owner with 3 pets + 5 visits each: < 2 seconds
- History rendering: < 1 second
- Concurrent history reviews: 20 users

## Performance Test Design Recommendations

### Load Profile
1. **Normal Load**: 
   - 20 concurrent users
   - 10-minute duration
   - Ramp-up: 5 minutes

2. **Peak Load**:
   - 20 concurrent users
   - 30-minute duration
   - Ramp-up: 3 minutes

3. **Stress Test**:
   - Start at 20 users, increase by 50 every 10 minutes
   - Test until errors exceed 5%
   - Identify breaking point

### Test Data Requirements
- **Owners**: Use existing 1,000+ owners, create additional if needed
- **Pets**: Use existing 2,000+ pets, randomize types
- **Visits**: Create dates within realistic range (past 3 years)
- **Search Keywords**: Mix of common (Smith, Johnson, Garcia) and unique names

### Parameterization Strategy
1. **Owner Creation**: Random unique first/last names, addresses, phone numbers
2. **Pet Creation**: Random names, types from dropdown, birth dates within valid range
3. **Visit Creation**: Random dates (format: YYYY/MM/DD), realistic descriptions
4. **Search Terms**: CSV file with weighted name distribution (80% common, 20% unique)

### Correlation Points
1. **Owner ID**: Extract from redirect after owner creation (`/owners/{id}.html`)
2. **Pet ID**: Extract from form submission response
3. **Session Management**: Handle cookies/session tokens if present
4. **CSRF Tokens**: Check if forms include CSRF protection tokens

### Assertions & Validation
1. **Response Codes**: 200 for successful GETs, 302 for successful POSTs (redirect)
2. **Content Validation**: 
   - Owner list contains expected owner name
   - Pet types match dropdown options
   - Visit dates display correctly
3. **Performance Thresholds**: Response time < 3s for 95th percentile
4. **Error Rate**: < 1% under normal load, < 5% under peak load

## Technical Observations

### Application Behavior
1. **Console Errors**: Multiple 500 errors for static resources (likely CSS/JS files missing)
   - Does not affect core functionality
   - May indicate environment configuration issue
2. **Datepicker Error**: `$(...).datepicker is not a function` - jQuery UI missing
   - Date fields still functional with manual entry
3. **URL Pattern**: RESTful structure with hierarchical relationships
4. **Data Integrity**: Proper referential integrity (Owner → Pet → Visit)

### Database Schema
- **Tables**: owners, pets, types, vets, specialties, vet_specialties, visits
- **Test Data Volume**: 
  - 1,000 owners
  - 2,000 pets
  - 50 vets
  - 5,000 visits
  - 6 types, 6 specialties, 106 vet-specialty associations

### Network Configuration
- **Application Server**: 10.134.77.66:8080
- **Database Server**: 10.130.73.5:5432 (PostgreSQL 9.6.24 on GCP)
- **SSL Required**: Database uses SSL/TLS encryption

## Next Steps
1. ✅ Update `api_config.json` with discovered endpoints
2. Create JMeter test plans for each critical scenario
3. Implement correlation for dynamic IDs (owner_id, pet_id)
4. Add CSV data files for parameterization
5. Configure timers for realistic think time
6. Set up listeners and reporting dashboards
7. Execute baseline performance tests
8. Analyze results and identify bottlenecks
9. Tune and retest

## API Testing Priority
1. **High Priority**: Owner search, Owner creation, Visit scheduling (80% traffic)
2. **Medium Priority**: Pet management, Vet listing (15% traffic)
3. **Low Priority**: PDF export, XML/JSON endpoints (5% traffic)
