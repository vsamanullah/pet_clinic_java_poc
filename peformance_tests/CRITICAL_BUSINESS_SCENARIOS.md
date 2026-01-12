# PetClinic - Critical Business Scenarios for Performance Testing

## Executive Summary
This document outlines the critical business scenarios identified through Playwright-based application analysis of the PetClinic application. These scenarios represent real-world user journeys that will be used as the foundation for performance testing.

**Application**: Spring PetClinic Demo  
**URL**: http://<IP address>/petclinic  
**Test Data**: 1,000 owners, 2,000 pets, 50 vets, 5,000 visits

---

## Scenario 1: New Client Registration Journey ⭐⭐⭐
**Priority**: Critical  
**Business Impact**: First impression, revenue generation  
**User Role**: Receptionist  
**Frequency**: 50-100 times per day

### User Story
"As a receptionist, when a new client walks in with their pet, I need to quickly register them in the system so they can receive veterinary care without delays."

### Workflow Steps
1. **Search Verification** (Prevent Duplicates)
   - Navigate to "Find owners" page
   - Enter last name in search box
   - Submit search to verify owner doesn't exist
   - **Expected**: Empty result or confirmation of new client

2. **Owner Creation**
   - Click "Add Owner" button
   - Fill form:
     - First Name (required)
     - Last Name (required)
     - Address (required)
     - City (required)
     - Telephone (required)
   - Submit form
   - **Expected**: Redirect to new owner detail page with owner ID

3. **Pet Registration**
   - From owner detail page, click "Add New Pet"
   - Fill form:
     - Name (e.g., "Max", "Bella")
     - Birth Date (format: YYYY/MM/DD)
     - Type (dropdown: bird, cat, dog, hamster, lizard, snake)
   - Submit form
   - **Expected**: Redirect back to owner page showing new pet

4. **Initial Visit Scheduling**
   - From owner detail page, locate newly added pet
   - Click "Add Visit" for the pet
   - Fill form:
     - Date (default: today's date)
     - Description (e.g., "Initial checkup", "Vaccination")
   - Submit form
   - **Expected**: Visit appears in pet's visit history

### Performance SLAs
- **Total Journey Time**: < 5 seconds (95th percentile)
- **Each Individual Step**: < 1 second
- **Concurrent Users**: 50 (normal), 150 (peak)
- **Error Rate**: < 1%

### Test Data Requirements
```csv
firstName,lastName,address,city,telephone
John,NewClient1,123 Main St,Springfield,5551234567
Jane,NewClient2,456 Oak Ave,Madison,5559876543
```

### JMeter Test Plan Components
1. Thread Group: 50 virtual users, 5-minute ramp-up
2. HTTP Cookie Manager (session persistence)
3. CSV Data Set (owner data)
4. Regular Expression Extractor (owner ID, pet ID)
5. Timers: 2-3 seconds think time between steps
6. Assertions: Response code 200/302, text validation

---

## Scenario 2: Returning Client Visit Scheduling ⭐⭐⭐
**Priority**: Critical  
**Business Impact**: Daily operations, customer service  
**User Role**: Veterinarian/Receptionist  
**Frequency**: 200-300 times per day

### User Story
"As a receptionist, when an existing client calls to schedule a follow-up visit, I need to quickly find their account and add the appointment."

### Workflow Steps
1. **Owner Search**
   - Navigate to "Find owners"
   - Enter partial or full last name
   - Submit search
   - **Expected**: List of matching owners (may be paginated)

2. **Owner Selection**
   - Review search results table
   - Identify correct owner by address/city/telephone
   - Click owner name link
   - **Expected**: Owner detail page with all pets and visit history

3. **Visit History Review** (Optional)
   - Review existing visits for context
   - Identify which pet needs visit
   - Note any recurring conditions

4. **New Visit Scheduling**
   - Click "Add Visit" for specific pet
   - Fill form:
     - Date (select future date or today)
     - Description (e.g., "Follow-up - skin condition", "Annual checkup")
   - Submit form
   - **Expected**: Visit added to pet's history

### Performance SLAs
- **Owner Search**: < 500ms (even with 100+ results)
- **Owner Detail Load**: < 1 second (with 3 pets, 10 visits)
- **Visit Creation**: < 1 second
- **Concurrent Users**: 100 (normal), 200 (peak)
- **Error Rate**: < 1%

### Test Data Requirements
```csv
searchLastName,expectedResults
Anderson,20+
Smith,30+
Garcia,25+
Wilson,15+
```

### JMeter Test Plan Components
1. Thread Group: 100 virtual users, 3-minute ramp-up
2. CSV Data Set (common last names with distribution)
3. Regular Expression Extractor (owner ID from search results)
4. Response Assertion (owner name exists in results)
5. Random Variable (select random pet from owner detail)
6. Visit description randomizer

---

## Scenario 3: Multi-Pet Owner Management ⭐⭐
**Priority**: High  
**Business Impact**: Complex customer management  
**User Role**: Veterinarian/Receptionist  
**Frequency**: 50-80 times per day

### User Story
"As a receptionist, when an owner with multiple pets comes in, I need to efficiently manage all their pets' information and schedule appointments."

### Workflow Steps
1. **Find Multi-Pet Owner**
   - Search by last name
   - Select owner known to have multiple pets
   - View owner detail page
   - **Expected**: Owner page displaying 2-4 pets with visit histories

2. **Add New Pet** (Expansion)
   - Click "Add New Pet"
   - Fill form with new pet details
   - Submit
   - **Expected**: New pet added to owner's pet list

3. **Update Existing Pet**
   - Click "Edit Pet" for existing pet
   - Update information (e.g., correct birth date)
   - Submit
   - **Expected**: Pet information updated

4. **Schedule Multiple Visits**
   - Add visit for Pet #1
   - Return to owner page
   - Add visit for Pet #2
   - Return to owner page
   - Add visit for Pet #3
   - **Expected**: All visits scheduled, visible in history

### Performance SLAs
- **Owner Detail with 3+ Pets**: < 2 seconds
- **Each Pet Operation**: < 1 second
- **Concurrent Multi-Pet Updates**: 30 users
- **Error Rate**: < 2%

### Test Data Requirements
- Pre-identify owners with 3+ pets in database
- Use owner IDs: 4622 (Barbara Anderson - 3 pets), similar

---

## Scenario 4: Veterinarian Directory Lookup ⭐
**Priority**: Medium  
**Business Impact**: Information access, client inquiries  
**User Role**: Receptionist/Client  
**Frequency**: 100-150 times per day

### User Story
"As a receptionist, when clients ask about available specialties or specific veterinarians, I need to quickly access the vet directory."

### Workflow Steps
1. **Access Vet Directory**
   - Click "Veterinarians" in navigation
   - View complete list of 50 vets
   - **Expected**: Searchable table with names and specialties

2. **Search/Filter by Specialty** (Client-side)
   - Use search box to filter by specialty keyword (e.g., "cardiology")
   - **Expected**: Filtered results showing only matching vets

3. **API Access** (System Integration)
   - Fetch `/vets.json` endpoint
   - Parse JSON response with vet details
   - **Expected**: JSON array with all vets and specialties

### Performance SLAs
- **HTML List Load**: < 1 second (50 vets)
- **JSON API Response**: < 500ms
- **Concurrent Lookups**: 200 users
- **Error Rate**: < 0.5%

### Test Data Requirements
- No dynamic data needed (read-only)
- Test specialty keywords: cardiology, dentistry, dermatology, neurology, radiology, surgery

---

## Scenario 5: High-Volume Owner Search & Export ⭐⭐
**Priority**: High  
**Business Impact**: Reporting, data analysis  
**User Role**: Administrator/Manager  
**Frequency**: 20-30 times per day

### User Story
"As a clinic manager, I need to search for owners by common last names and export results for reporting purposes."

### Workflow Steps
1. **Broad Search Query**
   - Enter common last name (e.g., "Anderson")
   - Submit search
   - **Expected**: 100+ results with pagination

2. **Navigate Results**
   - View first page (typically 10-25 results)
   - Click pagination controls
   - Navigate to page 2, 3, etc.
   - **Expected**: Smooth pagination with < 500ms load

3. **Export to PDF** (if available)
   - Click "PDF export" or similar link
   - Generate downloadable report
   - **Expected**: PDF generated within 3 seconds

4. **Drill Down to Specific Owner**
   - Select specific owner from results
   - View detail page
   - **Expected**: Standard owner detail load time

### Performance SLAs
- **Search with 100+ Results**: < 2 seconds
- **Pagination Load**: < 500ms per page
- **PDF Export**: < 3 seconds (if implemented)
- **Concurrent Searches**: 150 users
- **Error Rate**: < 1%

### Test Data Requirements
```csv
commonLastName,expectedCount
Anderson,100+
Smith,120+
Johnson,90+
Garcia,85+
Rodriguez,75+
```

---

## Scenario 6: Visit History Review (Read-Heavy) ⭐
**Priority**: Medium  
**Business Impact**: Clinical decision making  
**User Role**: Veterinarian  
**Frequency**: 150-200 times per day

### User Story
"As a veterinarian, before examining a pet, I need to review its complete visit history to understand medical background."

### Workflow Steps
1. **Search Owner**
   - Search by last name
   - Select correct owner from results

2. **Review Complete History**
   - View owner detail page
   - Scroll through all pets (1-4 typically)
   - Read visit descriptions for each pet
   - Note patterns (e.g., recurring skin conditions, vaccination schedules)
   - **Expected**: All data visible on one page without additional clicks

3. **Add Follow-Up Visit**
   - Based on history review, schedule follow-up
   - Reference previous visit in description
   - **Expected**: Visit added with context

### Performance SLAs
- **Owner Page with 3 Pets + 5 Visits Each**: < 2 seconds
- **History Rendering**: < 1 second
- **Concurrent History Reviews**: 80 users
- **Error Rate**: < 1%

---

## Load Testing Strategy

### Test Phases

#### Phase 1: Baseline (Weeks 1-2)
- **Objective**: Establish current performance metrics
- **Load**: 30 concurrent users
- **Duration**: 60 minutes
- **Scenarios**: All 6 scenarios with realistic distribution

#### Phase 2: Normal Load (Week 3)
- **Objective**: Validate normal daily operations
- **Load**: 50-100 concurrent users
- **Duration**: 120 minutes (2 hours)
- **Scenario Distribution**:
  - 40% Returning Client Visits (Scenario 2)
  - 20% New Client Registration (Scenario 1)
  - 15% Vet Directory Lookup (Scenario 4)
  - 10% Multi-Pet Management (Scenario 3)
  - 10% High-Volume Search (Scenario 5)
  - 5% History Review (Scenario 6)

#### Phase 3: Peak Load (Week 4)
- **Objective**: Test peak hour performance (morning rush, 9-11 AM)
- **Load**: 150-200 concurrent users
- **Duration**: 60 minutes
- **Ramp-up**: 5 minutes
- **Expected Behavior**: Response times within SLA, error rate < 3%

#### Phase 4: Stress Test (Week 5)
- **Objective**: Identify breaking point
- **Load**: Start at 200, increase by 50 every 10 minutes
- **Duration**: Until error rate exceeds 5% or response time > 10 seconds
- **Outcome**: Document maximum capacity

#### Phase 5: Soak Test (Week 6)
- **Objective**: Identify memory leaks, resource exhaustion
- **Load**: 70 concurrent users (70% of normal load)
- **Duration**: 8 hours (simulated workday)
- **Monitoring**: Memory usage, database connections, response time degradation

### Success Criteria
| Metric | Target | Acceptable | Failure |
|--------|--------|------------|---------|
| Response Time (95th percentile) | < 2s | < 3s | > 5s |
| Error Rate | < 0.5% | < 1% | > 2% |
| Throughput | 100+ req/s | 80+ req/s | < 50 req/s |
| Database Response Time | < 100ms | < 200ms | > 500ms |
| Server CPU Utilization | < 70% | < 85% | > 95% |
| Server Memory Usage | < 80% | < 90% | > 95% |
| Database Connections | < 50 | < 80 | > 100 |

---

## Implementation Checklist

### JMeter Test Plans
- [ ] `01_New_Client_Registration.jmx`
- [ ] `02_Returning_Client_Visit.jmx`
- [ ] `03_Multi_Pet_Management.jmx`
- [ ] `04_Vet_Directory_Lookup.jmx`
- [ ] `05_High_Volume_Search.jmx`
- [ ] `06_Visit_History_Review.jmx`
- [ ] `00_Master_Test_Plan.jmx` (orchestrates all scenarios)

### Test Data Files
- [ ] `new_owners.csv` (500 rows)
- [ ] `common_last_names.csv` (50 rows with distribution weights)
- [ ] `pet_names.csv` (200 rows)
- [ ] `pet_types.csv` (6 rows: bird, cat, dog, hamster, lizard, snake)
- [ ] `visit_descriptions.csv` (100 rows with realistic veterinary visit descriptions)
- [ ] `multi_pet_owner_ids.csv` (50 owner IDs with 3+ pets)

### Scripts & Utilities
- [ ] `setup_test_environment.py` - Seed database with test data
- [ ] `cleanup_test_data.py` - Remove test data after run
- [ ] `run_performance_test.py` - Execute JMeter with monitoring
- [ ] `analyze_results.py` - Parse JTL files and generate reports
- [ ] `compare_runs.py` - Compare multiple test run results

### Monitoring & Reporting
- [ ] Configure InfluxDB + Grafana for real-time dashboards
- [ ] Set up application server monitoring (CPU, memory, threads)
- [ ] Configure database monitoring (query times, connections, locks)
- [ ] Network latency monitoring
- [ ] Configure alerting for SLA violations
- [ ] Generate HTML reports from JMeter results

---

## Appendix: Form Field Validations

### Owner Form
- **firstName**: Required, max length unknown
- **lastName**: Required, max length unknown, searchable
- **address**: Required
- **city**: Required
- **telephone**: Required, format validation unknown

### Pet Form
- **name**: Required, varchar(30) based on DB schema
- **birthDate**: Required, format YYYY/MM/DD
- **type**: Required, dropdown with 6 options

### Visit Form
- **date**: Required, format YYYY/MM/DD, default to today
- **description**: Required, text field

---

## Next Steps
1. ✅ Create `APPLICATION_ANALYSIS.md` (completed)
2. ✅ Update `api_config.json` (completed)
3. Create test data CSV files
4. Develop JMeter test plans for each scenario
5. Implement correlation for dynamic IDs
6. Set up monitoring infrastructure
7. Execute baseline tests
8. Analyze and optimize
9. Document findings and recommendations
