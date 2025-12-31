# EOM Nomination Test Data

## Overview

This directory contains test data generators for EOM (Employee of the Month) nominations with comprehensive edge cases.

## Test Data Generator

### `eom_test_data_generator.py`

Generates comprehensive test data including:

1. **Test People**: Academic staff, admin staff, leaders, support staff, inactive staff
2. **Test Cycles**: Evaluation cycles for different quarters
3. **Test EOM Cycles**: Monthly EOM cycles for 2024
4. **Test Rotation Rules**: Category-specific rotation rules
5. **Test Winners**: Historical winners to create rotation scenarios
6. **Test Nominations**: 24+ test cases covering various scenarios

## Test Scenarios

### Valid Nominations (8 cases)
- First-time nominations
- Different categories
- Multiple categories for same person
- Nominations after cooldown period
- Different quarters/periods

### Rotation Rule Violations (4 cases)
- Cooldown period violations (Academic, Admin)
- Max wins per period violations
- Period-based violations (year, quarter)

### Duplicate Nominations (2 cases)
- Same cycle, same category
- Different nominator, same nominee/category

### Leader Limit Violations (1 case)
- Same leader nominating twice in same category

### Attendance Issues (1 case)
- Low attendance below threshold

### Invalid Data (4 cases)
- Non-existent nominee
- Inactive nominee
- Self-nomination
- Invalid category

### Boundary Conditions (4 cases)
- Exactly at cooldown period end
- Exactly at max wins
- One below max wins
- First nomination after cooldown

### Warning Cases (2 cases)
- High nomination count
- Recent winner in different category

## Usage

### Generate Test Data

```python
from tests.test_data.eom_test_data_generator import EOMTestDataGenerator
from backend.database import Database

db = Database()
session = db.get_session()

generator = EOMTestDataGenerator()
test_data = generator.generate_all_test_data(session)

# Access test data
people = test_data['people']
cycles = test_data['cycles']
eom_cycles = test_data['eom_cycles']
test_nominations = test_data['test_nominations']
```

### Filter Test Cases

```python
# Get valid nominations
valid = generator.get_valid_nominations()

# Get invalid nominations
invalid = generator.get_invalid_nominations()

# Get by edge case type
cooldown_cases = generator.get_nominations_by_type('cooldown_violation')

# Get by category
academic_cases = generator.get_nominations_by_category('ACADEMIC')
```

### Export Test Data

```python
# Export to dictionary
exported = generator.export_to_dict()

# Print summary
from tests.test_data.eom_test_data_generator import create_test_data_summary
print(create_test_data_summary())
```

## Test Cases by Type

### Valid Cases
1. Valid first-time nomination
2. Valid nomination - different category
3. Valid nomination - admin category
4. Leader nominating in different category
5. Multiple categories for same nominee
6. First nomination after cooldown
7. Different quarter nomination
8. One below max wins

### Invalid Cases
1. Cooldown period violation - Academic
2. Cooldown period violation - Admin
3. Max wins per period violation
4. Duplicate nomination (same cycle)
5. Duplicate nomination (different nominator)
6. Leader limit violation
7. Low attendance
8. Non-existent nominee
9. Inactive nominee
10. Self-nomination
11. Invalid category
12. Exactly at max wins
13. Year-based period violation

### Boundary Cases
1. Exactly at cooldown period end
2. Exactly at max wins
3. One below max wins
4. First nomination after cooldown

### Warning Cases
1. High nomination count
2. Recent winner in different category

## Running Tests

```bash
# Run all EOM nomination tests
pytest tests/test_eom_nomination_data.py -v

# Run specific test class
pytest tests/test_eom_nomination_data.py::TestValidNominations -v

# Run with test data summary
pytest tests/test_eom_nomination_data.py -v -s
```

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

## Edge Case Types

- `valid`: Valid nomination
- `cooldown_violation`: Cooldown period violation
- `max_wins_violation`: Max wins per period violation
- `duplicate`: Duplicate nomination
- `leader_limit`: Leader nomination limit violation
- `attendance_issue`: Attendance-related issue
- `invalid_data`: Invalid data (non-existent, inactive, etc.)
- `self_nomination`: Self-nomination attempt
- `boundary_cooldown`: Boundary case at cooldown end
- `boundary_max_wins`: Boundary case at max wins
- `boundary_valid`: Valid boundary case
- `period_violation`: Period-based violation
- `warning`: Warning case (valid but with warnings)

