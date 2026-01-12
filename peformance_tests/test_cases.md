# PetClinic Performance Testing - Test Cases

## Document Information

| Property | Value |
|----------|-------|
| **Module** | PetClinic Performance Testing |
| **Version** | 1.0 |
| **Last Updated** | January 11, 2026 |
| **Test Framework** | Apache JMeter 5.6.3 |
| **Application** | PetClinic Spring Application |
| **Base URL** | http://<ip>:<port>/petclinic |
| **Total Test Scenarios** | 6 |

---

## Table of Contents

1. [Test Environment Setup](#test-environment-setup)
2. [Performance Test Scenarios](#performance-test-scenarios)
3. [Load Profile Definitions](#load-profile-definitions)
4. [Performance KPIs and Thresholds](#performance-kpis-and-thresholds)

---

## Test Environment Setup

### Test Prerequisites

| Prerequisite | Description | Verification |
|--------------|-------------|--------------|
| JMeter 5.6.3 | Performance testing tool | `jmeter --version` |
| Python 3.14+ | Test orchestration | `python --version` |
| PostgreSQL 9.6.24 | Database server | Connection to Database <ip>:<port> |
| Application Server | PetClinic running | https://<ip>:<port>/petclinic |
| Test Data | Baseline data loaded | 510 owners, 997 pets, 962 visits |
| CSV Files | Parameterization data | common_last_names.csv, multi_pet_owner_ids.csv, etc. |

### Configuration Files

- **api_config.json**: Endpoint configurations
- **db_config.json**: Database connection settings
- **JMX files**: 6 test scenarios (01-06)

### Performance Thresholds

| Metric | Normal Load | Peak Load | Stress Test |
|--------|-------------|-----------|-------------|
| Concurrent Users | 20 | 150 | 200+ |
| Response Time (95th) | < 3s | < 5s | < 10s |
| Error Rate | < 1% | < 5% | Identify breaking point |
| Throughput | Baseline | 7x Baseline | Maximum capacity |

---

## Performance Test Scenarios

### Scenario 1: New Client Registration (End-to-End)

**Test Case ID**: TC-PERF-001  
**JMeter Script**: 01_New_Client_Registration.jmx  
**Priority**: High  
**Load Profile**: Normal Load (20 users)

#### Objective
Validate performance of complete new client onboarding workflow from search through visit scheduling.

#### User Journey
1. Search for owner by last name (verify not duplicate)
2. Create new owner with complete information
3. Add first pet to newly created owner
4. Schedule initial visit for new pet

#### Test Steps

| Step | Action | Endpoint | Method | Expected Response |
|------|--------|----------|--------|-------------------|
| 1 | Navigate to Find Owners | `/petclinic/owners/find.html` | GET | 200 OK |
| 2 | Search for new owner | `/petclinic/owners.html?lastName={name}` | GET | 200 OK (empty results) |
| 3 | Navigate to Add Owner | `/petclinic/owners/new` | GET | 200 OK |
| 4 | Submit new owner form | `/petclinic/owners/new` | POST | 302 Redirect |
| 5 | Navigate to Add Pet | `/petclinic/owners/{ownerId}/pets/new.html` | GET | 200 OK |
| 6 | Submit new pet form | `/petclinic/owners/{ownerId}/pets/new` | POST | 302 Redirect |
| 7 | Navigate to Add Visit | `/petclinic/owners/{ownerId}/pets/{petId}/visits/new` | GET | 200 OK |
| 8 | Submit new visit form | `/petclinic/owners/{ownerId}/pets/{petId}/visits/new` | POST | 302 Redirect |

#### Parameterization
- **new_owners.csv**: First name, last name, address, city, telephone (unique values)
- **pet_names.csv**: Pet names (randomized)
- **visit_descriptions.csv**: Visit descriptions (Annual checkup, Vaccination, etc.)

#### Correlation Points
- **Owner ID**: Extract from redirect URL after owner creation (`/owners/{id}.html`)
- **Pet ID**: Extract from redirect URL after pet creation (`/owners/{ownerId}/pets/{petId}/edit`)

#### Performance KPIs
- **Total journey time**: < 5 seconds
- **Each step response time**: < 1 second
- **Concurrent users**: 20
- **Error rate**: < 1%

#### Assertions
- Response code 200 OK for GET requests
- Response code 302 for successful POST operations
- Owner ID extracted successfully
- Pet ID extracted successfully

---

### Scenario 2: Returning Client Visit Scheduling

**Test Case ID**: TC-PERF-002  
**JMeter Script**: 02_Returning_Client_Visit.jmx  
**Priority**: High  
**Load Profile**: Normal Load (20 users)

#### Objective
Measure performance of scheduling visits for existing clients with search result handling.

#### User Journey
1. Search owner by last name
2. Navigate search results (may have single or multiple matches)
3. View owner details with pet history
4. Add new visit to existing pet

#### Test Steps

| Step | Action | Endpoint | Method | Expected Response |
|------|--------|----------|--------|-------------------|
| 1 | Navigate to Find Owners | `/petclinic/owners/find.html` | GET | 200 OK |
| 2 | Search for owner | `/petclinic/owners.html?lastName={name}` | GET | 200 OK or 302 (single result) |
| 3 | View owner details | `/petclinic/owners/{ownerId}.html` | GET | 200 OK |
| 4 | Navigate to Add Visit | `/petclinic/owners/{ownerId}/pets/{petId}/visits/new` | GET | 200 OK |
| 5 | Submit visit form | `/petclinic/owners/{ownerId}/pets/{petId}/visits/new` | POST | 302 Redirect |

#### Parameterization
- **common_last_names.csv**: Last names from database (Coleman, Estaban, Rodriquez, Black, Davis, Escobito, Franklin, McTavish, Schroeder)
- **visit_descriptions.csv**: Visit descriptions

#### Correlation Points
- **Owner ID**: Dual extractors (body for list, URL for redirect)
- **Pet ID**: Extract from owner details page (first pet)

#### Special Handling
- **Single result redirect**: If search returns one owner, application redirects directly to owner detail page
- **Dual extraction strategy**: Try extracting from response body first, fallback to URL extraction for redirects

#### Performance KPIs
- **Search response time**: < 500ms
- **Owner detail load**: < 1 second
- **Visit creation**: < 1 second
- **Concurrent users**: 20
- **Error rate**: < 1%

#### Assertions
- Response code 200 OK for all GET requests
- Owner ID extracted (either from body or URL)
- Pet ID extracted successfully

---

### Scenario 3: Multi-Pet Owner Management

**Test Case ID**: TC-PERF-003  
**JMeter Script**: 03_Multi_Pet_Owner.jmx  
**Priority**: High  
**Load Profile**: Normal Load (20 users)

#### Objective
Test performance of complex operations for owners with multiple pets including CRUD operations.

#### User Journey
1. Find owner with multiple pets
2. Add new pet to existing owner
3. Update existing pet information
4. Schedule visits for multiple pets

#### Test Steps

| Step | Action | Endpoint | Method | Expected Response |
|------|--------|----------|--------|-------------------|
| 1 | Navigate to Find Owners | `/petclinic/owners/find.html` | GET | 200 OK |
| 2 | Search multi-pet owner | `/petclinic/owners.html?lastName={name}` | GET | 200 OK or 302 |
| 3 | View owner details | `/petclinic/owners/{ownerId}.html` | GET | 200 OK |
| 4 | Navigate to Add Pet | `/petclinic/owners/{ownerId}/pets/new.html` | GET | 200 OK |
| 5 | Submit new pet form | `/petclinic/owners/{ownerId}/pets/new` | POST | 302 Redirect |
| 6 | Navigate to Edit Pet | `/petclinic/owners/{ownerId}/pets/{petId}/edit` | GET | 200 OK |
| 7 | Submit pet update | `/petclinic/owners/{ownerId}/pets/{petId}/edit` | POST | 302 Redirect |
| 8 | Navigate to Add Visit | `/petclinic/owners/{ownerId}/pets/{petId}/visits/new` | GET | 200 OK |
| 9 | Submit visit form | `/petclinic/owners/{ownerId}/pets/{petId}/visits/new` | POST | 302 Redirect |

#### Parameterization
- **multi_pet_owner_ids.csv**: Owner IDs with 2+ pets (owners: 6, 10, 3)
- **pet_names.csv**: Random pet names
- **visit_descriptions.csv**: Visit descriptions

#### Correlation Points
- **Owner ID**: From CSV file
- **New Pet ID**: Extract from redirect after pet creation
- **Existing Pet ID**: Extract from owner details (second pet)

#### Performance KPIs
- **Owner detail with 3+ pets**: < 2 seconds
- **Pet operations**: < 1 second each
- **Concurrent users**: 20
- **Error rate**: < 1%

#### Assertions
- Response code 200 OK for all GET requests
- All pet operations complete successfully
- Pet ID extraction works for both new and existing pets

---

### Scenario 4: Veterinarian Directory Lookup

**Test Case ID**: TC-PERF-004  
**JMeter Script**: 04_Vet_Directory_Lookup.jmx  
**Priority**: Medium  
**Load Profile**: Peak Load (150 users)

#### Objective
Validate performance of read-only veterinarian directory access across multiple formats.

#### User Journey
1. View list of all veterinarians
2. Access JSON API for vet information
3. Access XML API for vet information

#### Test Steps

| Step | Action | Endpoint | Method | Expected Response |
|------|--------|----------|--------|-------------------|
| 1 | View vets HTML page | `/petclinic/vets.html` | GET | 200 OK |
| 2 | Get vets JSON | `/petclinic/vets.json` | GET | 200 OK |
| 3 | Get vets XML | `/petclinic/vets.xml` | GET | 200 OK |

#### Test Data
- **172 veterinarians** in database
- **Specialties**: cardiology, dentistry, dermatology, neurology, radiology, surgery
- **87 vet-specialty associations**

#### Performance KPIs
- **Vets list load**: < 1 second
- **JSON API response**: < 500ms
- **XML API response**: < 500ms
- **Concurrent users**: 20
- **Error rate**: < 1%

#### Assertions
- Response code 200 OK for all requests
- HTML page renders veterinarian list
- JSON response is valid JSON format
- XML response is valid XML format

---

### Scenario 5: High-Volume Owner Search

**Test Case ID**: TC-PERF-005  
**JMeter Script**: 05_High_Volume_Search.jmx  
**Priority**: High  
**Load Profile**: Peak Load (150 users)

#### Objective
Test search performance with large result sets and pagination handling.

#### User Journey
1. Search by common last name (100+ potential matches)
2. View paginated results
3. Select specific owner from results
4. View owner details

#### Test Steps

| Step | Action | Endpoint | Method | Expected Response |
|------|--------|----------|--------|-------------------|
| 1 | Navigate to Find Owners | `/petclinic/owners/find.html` | GET | 200 OK |
| 2 | Search common name | `/petclinic/owners.html?lastName={name}` | GET | 200 OK (list) |
| 3 | Select first owner | `/petclinic/owners/{ownerId1}.html` | GET | 200 OK |
| 4 | Return to search | `/petclinic/owners.html?lastName={name}` | GET | 200 OK |
| 5 | Select random owner | `/petclinic/owners/{randomOwnerId}.html` | GET | 200 OK |

#### Parameterization
- **common_last_names.csv**: Common last names with multiple matches (Coleman, Estaban, Rodriquez, Black, Davis, Escobito, Franklin, McTavish, Schroeder)

#### Correlation Points
- **First Owner ID**: Dual extractors (body for list, URL for single redirect)
- **Random Owner ID**: Dual extractors from repeated search
- **Owner Count**: Extract number of search results

#### Special Handling
- **Dual extraction pattern**: Extract from body first (multi-results), fallback to URL (single redirect)
- **Dynamic result handling**: Handle both single and multiple result scenarios

#### Performance KPIs
- **Search with 100+ results**: < 2 seconds
- **Pagination**: < 500ms per page
- **Owner detail load**: < 1 second
- **Concurrent users**: 20
- **Error rate**: < 1%

#### Assertions
- Response code 200 OK for all requests
- Owner ID extracted successfully from search results
- Search results contain expected owner names

---

### Scenario 6: Visit History Review

**Test Case ID**: TC-PERF-006  
**JMeter Script**: 06_Visit_History_Review.jmx  
**Priority**: Medium  
**Load Profile**: Normal Load (20 users)

#### Objective
Measure performance when loading owner pages with extensive pet and visit history.

#### User Journey
1. Search and find owner with multiple pets
2. View owner detail page (showing all pets and visit histories)
3. Review visit descriptions for specific pet
4. Navigate through pet history

#### Test Steps

| Step | Action | Endpoint | Method | Expected Response |
|------|--------|----------|--------|-------------------|
| 1 | Navigate to Find Owners | `/petclinic/owners/find.html` | GET | 200 OK |
| 2 | Search owner | `/petclinic/owners.html?lastName={name}` | GET | 200 OK or 302 |
| 3 | View owner details | `/petclinic/owners/{ownerId}.html` | GET | 200 OK |
| 4 | View first pet edit | `/petclinic/owners/{ownerId}/pets/{pet1Id}/edit` | GET | 200 OK |
| 5 | View second pet edit | `/petclinic/owners/{ownerId}/pets/{pet2Id}/edit` | GET | 200 OK |

#### Parameterization
- **multi_pet_owner_ids.csv**: Owners with 2+ pets (owners: 6, 10, 3)

#### Correlation Points
- **Owner ID**: From CSV file
- **First Pet ID**: Extract from owner details
- **Second Pet ID**: Extract from owner details

#### Test Data Requirements
- Owners with 3+ pets
- Each pet has 5+ visits
- Visit history spanning multiple years

#### Performance KPIs
- **Owner with 3 pets + 5 visits each**: < 2 seconds
- **History rendering**: < 1 second
- **Pet detail load**: < 500ms
- **Concurrent users**: 20
- **Error rate**: < 1%

#### Assertions
- Response code 200 OK for all requests
- Owner detail page loads with all pets
- Pet IDs extracted successfully
- Visit history displays correctly

---

## Load Profile Definitions

### Normal Load Profile
- **Concurrent Users**: 20
- **Duration**: 10 minutes
- **Ramp-Up Time**: 5 minutes (gradual increase)
- **Think Time**: 3-5 seconds between requests
- **Use Case**: Regular business hours operation

### Peak Load Profile
- **Concurrent Users**: 150
- **Duration**: 30 minutes
- **Ramp-Up Time**: 3 minutes
- **Think Time**: 1-3 seconds between requests
- **Use Case**: Peak clinic hours (morning/afternoon rush)

### Stress Test Profile
- **Starting Users**: 200
- **Increment**: +50 users every 10 minutes
- **Duration**: Until error rate > 5%
- **Think Time**: 1-2 seconds
- **Use Case**: Identify system breaking point and maximum capacity

### Endurance Test Profile
- **Concurrent Users**: 50
- **Duration**: 4 hours
- **Ramp-Up Time**: 10 minutes
- **Think Time**: 5-10 seconds
- **Use Case**: Identify memory leaks and resource degradation

---

## Performance KPIs and Thresholds

### Response Time Metrics

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Average Response Time | < 1s | 1-2s | > 2s |
| 90th Percentile | < 2s | 2-4s | > 4s |
| 95th Percentile | < 3s | 3-5s | > 5s |
| 99th Percentile | < 5s | 5-10s | > 10s |
| Maximum Response Time | < 10s | 10-15s | > 15s |

### Throughput Metrics

| Operation | Target TPS | Warning | Critical |
|-----------|-----------|---------|----------|
| Owner Search | 50 TPS | 30-50 | < 30 |
| Owner Create | 10 TPS | 5-10 | < 5 |
| Visit Create | 20 TPS | 10-20 | < 10 |
| Vet Directory | 100 TPS | 50-100 | < 50 |

### Error Rate Thresholds

| Load Type | Acceptable | Warning | Failure |
|-----------|-----------|---------|---------|
| Normal Load | < 0.5% | 0.5-1% | > 1% |
| Peak Load | < 2% | 2-5% | > 5% |
| Stress Test | < 5% | 5-10% | > 10% |

### Resource Utilization (Server)

| Resource | Normal | Warning | Critical |
|----------|--------|---------|----------|
| CPU Usage | < 60% | 60-80% | > 80% |
| Memory Usage | < 70% | 70-85% | > 85% |
| Database Connections | < 50 | 50-75 | > 75 |
| Thread Count | < 200 | 200-300 | > 300 |

---

## Test Data Requirements

### CSV Files

| File | Purpose | Records | Format |
|------|---------|---------|--------|
| new_owners.csv | New owner creation | 1000+ | first_name,last_name,address,city,telephone |
| common_last_names.csv | Owner search | 9 | last_name |
| multi_pet_owner_ids.csv | Multi-pet scenarios | 3 | owner_id |
| pet_names.csv | Pet creation | 500+ | pet_name |
| visit_descriptions.csv | Visit creation | 50+ | description |

### Database Baseline

| Table | Record Count | Description |
|-------|--------------|-------------|
| owners | 510 | Existing owners in system |
| pets | 997 | Pets linked to owners |
| visits | 962 | Historical visits |
| vets | 172 | Veterinarians |
| types | 6 | Pet types (bird, cat, dog, hamster, lizard, snake) |
| specialties | 3 | Vet specialties |
| vet_specialties | 87 | Vet-specialty associations |

---

## Test Execution Guidelines

### Pre-Test Checklist
1. Verify application is running: https://<ip>:<port>/petclinic
2. Verify database connection: Database <ip>:<port>
3. Load baseline data: `python populate_test_data.py`
4. Verify CSV files are present and populated
5. Clear previous test results from results/ directory
6. Check JMeter heap size: `-Xms1g -Xmx4g`

### Test Execution Command
```bash
python run_with_profiling.py <test_script.jmx> --env target
```

### Post-Test Validation
1. Review HTML reports in results/ directory
2. Check error rate in JTL files
3. Analyze response time distribution
4. Review server logs for errors
5. Validate database state after test
6. Compare results against KPI thresholds

### Report Generation
- **HTML Dashboard**: `results/<test_name>_report/index.html`
- **JTL File**: `results/<test_name>.jtl`
- **Log File**: `results/<test_name>.log`
- **System Metrics**: CPU, memory, network captured during test

---

## Test Prioritization

### Priority 1 (Critical) - Run Daily
- TC-PERF-001: New Client Registration
- TC-PERF-002: Returning Client Visit
- TC-PERF-005: High-Volume Search

### Priority 2 (High) - Run Weekly
- TC-PERF-003: Multi-Pet Owner Management
- TC-PERF-006: Visit History Review

### Priority 3 (Medium) - Run Monthly
- TC-PERF-004: Vet Directory Lookup

---

## Known Issues and Workarounds

### Issue 1: Console Errors for Static Resources
- **Symptom**: 500 errors for CSS/JS files
- **Impact**: None on core functionality
- **Workaround**: Ignore static resource errors in assertions

### Issue 2: Datepicker jQuery Error
- **Symptom**: `$(...).datepicker is not a function`
- **Impact**: None - manual date entry still works
- **Workaround**: Use format YYYY/MM/DD for date fields

### Issue 3: Single Owner Search Redirect
- **Symptom**: Search for single owner redirects directly to detail page
- **Impact**: Extraction logic needs dual pattern
- **Workaround**: Use dual extractors (body + URL)

---

## Success Criteria

### Test Execution Success
- All 6 scenarios execute without script errors
- Error rate below threshold for each load profile
- Response times meet 95th percentile targets
- No critical errors in application logs
- Database integrity maintained after test

### Performance Success
- 95th percentile response time < 3s (normal load)
- 95th percentile response time < 5s (peak load)
- Error rate < 1% (normal load)
- Error rate < 5% (peak load)
- Throughput meets target TPS for each operation
- System stable under sustained load (4 hours)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-11 | Performance Test Team | Initial test case documentation based on APPLICATION_ANALYSIS.md |

---

**Document Status**: Active  
**Next Review Date**: 2026-02-11  
**Contact**: Performance Testing Team
