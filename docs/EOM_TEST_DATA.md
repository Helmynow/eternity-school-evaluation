# EOM Nomination Test Data Documentation

## Overview

Comprehensive test data generator for EOM (Employee of the Month) nominations with 24+ test cases covering valid nominations, rotation rule violations, edge cases, and boundary conditions.

## Test Data Generator

### Location
- `tests/test_data/eom_test_data_generator.py`: Main test data generator
- `tests/test_data/populate_eom_test_data.py`: Script to populate database
- `tests/test_eom_nomination_data.py`: Unit tests using test data
- `examples/eom_test_data_example.py`: Usage examples

## Test Data Components

### 1. Test People (15 people)
- **Academic Staff**: 5 teachers (teacher1-5@eternity.edu)
- **Admin Staff**: 4 administrators (admin1-4@eternity.edu)
- **Leaders**: 3 leaders (leader1-3@eternity.edu)
- **Support Staff**: 2 support staff (support1-2@eternity.edu)
- **Inactive Staff**: 1 inactive person (inactive1@eternity.edu)

### 2. Test Cycles (4 cycles)
- CYCLE-2024-Q1: January - March 2024
- CYCLE-2024-Q2: April - June 2024
- CYCLE-2024-Q3: July - September 2024
- CYCLE-2024-Q4: October - December 2024

### 3. Test EOM Cycles (12 cycles)
- One EOM cycle for each month in 2024 (January - December)

### 4. Test Rotation Rules (4 rules)
- **Academic**: 3 months cooldown, max 1 win per quarter
- **Admin**: 2 months cooldown, max 1 win per quarter
- **Leadership**: 6 months cooldown, max 1 win per year
- **Innovation**: 1 month cooldown, max 2 wins per year

### 5. Test Winners (4 winners)
- **January 2024**: teacher1@eternity.edu (ACADEMIC)
- **February 2024**: admin1@eternity.edu (ADMIN)
- **March 2024**: teacher1@eternity.edu (INNOVATION)
- **April 2024**: teacher2@eternity.edu (ACADEMIC)

### 6. Test Nominations (24 scenarios)

## Test Scenarios

### Valid Nominations (11 cases)

1. **Valid first-time nomination**
   - Nominee: teacher3@eternity.edu
   - Category: ACADEMIC
   - Expected: Valid

2. **Valid nomination - different category**
   - Nominee: teacher2@eternity.edu
   - Category: INNOVATION
   - Expected: Valid

3. **Valid admin nomination**
   - Nominee: admin2@eternity.edu
   - Category: ADMIN
   - Expected: Valid

4. **Leader nominating in different category**
   - Nominee: teacher4@eternity.edu
   - Category: INNOVATION
   - Expected: Valid (different category from previous)

5. **Multiple categories for same nominee**
   - Nominee: teacher3@eternity.edu
   - Category: COLLABORATION
   - Expected: Valid

6. **First nomination after cooldown**
   - Nominee: teacher1@eternity.edu
   - Category: ACADEMIC
   - Expected: Valid (after 3-month cooldown)

7. **Different quarter nomination**
   - Nominee: teacher1@eternity.edu
   - Category: ACADEMIC
   - Expected: Valid (different quarter)

8. **One below max wins**
   - Nominee: teacher2@eternity.edu
   - Category: INNOVATION
   - Expected: Valid

9. **Boundary at cooldown end**
   - Nominee: teacher1@eternity.edu
   - Category: ACADEMIC
   - Expected: Valid (exactly at cooldown end)

10. **High nomination count (warning)**
    - Nominee: teacher2@eternity.edu
    - Category: ACADEMIC
    - Expected: Valid with warning

11. **Recent winner different category (warning)**
    - Nominee: teacher2@eternity.edu
    - Category: INNOVATION
    - Expected: Valid with warning

### Invalid Nominations (13 cases)

1. **Cooldown period violation - Academic**
   - Nominee: teacher1@eternity.edu (won in January)
   - Category: ACADEMIC
   - Cycle: February
   - Expected Error: "Nominee is within cooldown period"

2. **Cooldown period violation - Admin**
   - Nominee: admin1@eternity.edu (won in February)
   - Category: ADMIN
   - Cycle: March
   - Expected Error: "Nominee is within cooldown period"

3. **Max wins per period violation**
   - Nominee: teacher1@eternity.edu (won 2 in year)
   - Category: INNOVATION
   - Expected Error: "Maximum wins per period exceeded"

4. **Duplicate nomination - same cycle**
   - Nominee: teacher3@eternity.edu
   - Category: ACADEMIC
   - Expected Error: "Duplicate nomination"

5. **Duplicate nomination - different nominator**
   - Nominee: teacher3@eternity.edu
   - Category: ACADEMIC
   - Expected Error: "Duplicate nomination"

6. **Leader limit violation**
   - Nominee: teacher4@eternity.edu
   - Nominated by: leader1@eternity.edu (already nominated once)
   - Category: ACADEMIC
   - Expected Error: "Leader nomination limit exceeded"

7. **Low attendance**
   - Nominee: teacher5@eternity.edu
   - Expected Error: "Attendance below minimum threshold"

8. **Non-existent nominee**
   - Nominee: nonexistent@eternity.edu
   - Expected Error: "Nominee not found"

9. **Inactive nominee**
   - Nominee: inactive1@eternity.edu
   - Expected Error: "Nominee is not active"

10. **Self-nomination**
    - Nominee: teacher3@eternity.edu
    - Nominated by: teacher3@eternity.edu
    - Expected Error: "Self-nomination not allowed"

11. **Invalid category**
    - Category: INVALID_CATEGORY
    - Expected Error: "Invalid category"

12. **Exactly at max wins**
    - Nominee: teacher1@eternity.edu
    - Category: INNOVATION
    - Expected Error: "Maximum wins per period exceeded"

13. **Year-based period violation**
    - Nominee: admin1@eternity.edu
    - Category: LEADERSHIP
    - Expected Error: "Maximum wins per period exceeded"

## Usage

### Generate Test Data

```python
from tests.test_data.eom_test_data_generator import EOMTestDataGenerator
from backend.database import Database

db = Database()
session = db.get_session()

generator = EOMTestDataGenerator()
test_data = generator.generate_all_test_data(session)
```

### Filter Test Cases

```python
# Get valid nominations
valid = generator.get_valid_nominations()

# Get invalid nominations
invalid = generator.get_invalid_nominations()

# Get by edge case type
cooldown_cases = generator.get_nominations_by_type('cooldown_violation')
duplicate_cases = generator.get_nominations_by_type('duplicate')
leader_limit_cases = generator.get_nominations_by_type('leader_limit')

# Get by category
academic_cases = generator.get_nominations_by_category('ACADEMIC')
```

### Run Tests

```bash
# Populate test data
python tests/test_data/populate_eom_test_data.py

# Run tests
pytest tests/test_eom_nomination_data.py -v

# Run specific test class
pytest tests/test_eom_nomination_data.py::TestValidNominations -v

# Run with examples
python examples/eom_test_data_example.py
```

## Edge Case Types

| Type | Count | Description |
|------|-------|-------------|
| `valid` | 7 | Valid nominations |
| `cooldown_violation` | 2 | Cooldown period violations |
| `max_wins_violation` | 1 | Max wins per period violations |
| `duplicate` | 2 | Duplicate nominations |
| `leader_limit` | 1 | Leader nomination limit violations |
| `attendance_issue` | 1 | Attendance-related issues |
| `invalid_data` | 3 | Invalid data (non-existent, inactive, invalid category) |
| `self_nomination` | 1 | Self-nomination attempts |
| `boundary_cooldown` | 1 | Boundary at cooldown end |
| `boundary_max_wins` | 1 | Boundary at max wins |
| `boundary_valid` | 1 | Valid boundary case |
| `period_violation` | 1 | Period-based violations |
| `warning` | 2 | Warning cases (valid but with warnings) |

## Test Data Structure

Each test nomination includes:
- `nominee_email`: Person being nominated
- `nominated_by`: Person making nomination
- `category`: EOM category
- `nomination_reason`: Reason for nomination
- `expected_valid`: Whether nomination should be valid
- `expected_errors`: List of expected error messages
- `expected_warnings`: List of expected warning messages
- `description`: Human-readable description
- `edge_case_type`: Type of edge case

## Validation Rules Tested

1. **Rotation Rules**
   - Cooldown periods (1, 2, 3, 6 months)
   - Max wins per period (quarter, year)
   - Period types (year, quarter, month, term)

2. **Duplicate Prevention**
   - Same cycle, same category
   - Different nominator, same nominee/category

3. **Leader Limits**
   - One nomination per category per cycle

4. **Attendance Validation**
   - Minimum attendance threshold

5. **Data Validation**
   - Person existence
   - Active status
   - Self-nomination prevention
   - Category validity

6. **Boundary Conditions**
   - Exactly at cooldown end
   - Exactly at max wins
   - One below max wins

## Best Practices

1. **Use Test Data Generator**: Always use the generator for consistent test data
2. **Clean Up**: Clean up test data after tests
3. **Isolate Tests**: Each test should be independent
4. **Cover Edge Cases**: Test all edge case types
5. **Validate Expectations**: Check both `is_valid` and error messages
6. **Test Boundaries**: Include boundary condition tests

## Example Test

```python
def test_cooldown_violation(test_db, test_data):
    """Test cooldown period violation"""
    validator = EOMNominationValidator(test_db)
    generator = EOMTestDataGenerator()
    
    cooldown_cases = generator.get_nominations_by_type('cooldown_violation')
    case = cooldown_cases[0]
    eom_cycle = test_data['eom_cycles'][1]  # February
    
    result = validator.validate_nomination(
        nominee_email=case.nominee_email,
        eom_cycle_id=eom_cycle.id,
        nominated_by=case.nominated_by,
        category=case.category
    )
    
    assert not result.is_valid
    assert any('cooldown' in error.lower() for error in result.errors)
```

