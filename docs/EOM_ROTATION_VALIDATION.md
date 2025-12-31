# Complete EOM Nomination Validation System with Rotation Rules

## Overview

The EOM (Employee of the Month) Nomination Validation System provides comprehensive validation for nominations with advanced rotation rules to ensure fairness and prevent repeat winners. The system includes category-specific rules, cooldown periods, maximum wins per period, and comprehensive analytics.

## Features

### 1. Comprehensive Rotation Rules

- **Category-Specific Rules**: Different rotation rules for each EOM category (Academic, Admin, Support, Leadership, Innovation, Collaboration, Student Engagement)
- **Cooldown Periods**: Configurable cooldown periods before a nominee can win again
- **Maximum Wins Per Period**: Limit the number of wins allowed in a specific period (year, quarter, month)
- **Period Types**: Support for yearly, quarterly, monthly, and term-based periods
- **Rotation Eligibility Tracking**: Automatic tracking of rotation eligibility flags

### 2. Validation Checks

- **Rotation Rules**: Comprehensive rotation rule validation
- **Attendance Validation**: Checks attendance records for eligibility
- **Duplicate Prevention**: Prevents duplicate nominations in the same cycle
- **Leader Limits**: Ensures leaders can only nominate once per category
- **Additional Validations**: Person existence, active status, self-nomination checks

### 3. Rotation Rule Management

- **Create Rules**: Create new rotation rules for categories
- **Update Rules**: Modify existing rotation rules
- **Default Rules**: Set up default rotation rules for cycles
- **Rule Queries**: Retrieve rules by cycle, category, or active status

### 4. Analytics and Reporting

- **Rotation Analytics**: Comprehensive statistics on wins, winners, and compliance
- **Nominee History**: Complete rotation history for individual nominees
- **Eligibility Reports**: Lists of eligible and ineligible nominees
- **Compliance Tracking**: Track violations of rotation rules

## Architecture

### Core Classes

#### `EOMNominationValidator`
Main validation class that performs all validation checks.

**Key Methods:**
- `validate_nomination()`: Validate a single nomination
- `validate_batch_nominations()`: Validate multiple nominations
- `check_nominee_rotation_eligibility()`: Check if nominee is eligible
- `create_rotation_rule()`: Create a new rotation rule
- `update_rotation_rule()`: Update an existing rule
- `get_rotation_analytics()`: Get comprehensive analytics
- `get_nominee_rotation_history()`: Get nominee's complete history

#### `EOMRotationManager`
High-level manager for rotation rule operations.

**Key Methods:**
- `setup_default_rules()`: Set up default rotation rules
- `get_eligible_nominees()`: Get list of eligible nominees
- `get_ineligible_nominees()`: Get list of ineligible nominees with reasons
- `update_rotation_eligibility_flags()`: Update eligibility flags
- `get_rotation_summary()`: Get comprehensive summary

## Rotation Rules

### Rule Configuration

Each rotation rule includes:
- **Category**: EOMCategory enum (ACADEMIC, ADMIN, SUPPORT, etc.)
- **Cycle ID**: The evaluation cycle this rule applies to
- **Cooldown Period**: Number of periods before eligible again
- **Max Wins Per Period**: Maximum wins allowed in a period
- **Period Type**: Type of period ('year', 'quarter', 'month')
- **Active Status**: Whether the rule is currently active

### Example Rule

```python
{
    "category": "ACADEMIC",
    "cycle_id": 1,
    "cooldown_period": 3,  # 3 periods cooldown
    "max_wins_per_period": 1,  # Max 1 win per period
    "period_type": "year",  # Yearly period
    "is_active": true
}
```

### Period Types

- **Year**: Calendar year (January 1 - December 31)
- **Quarter**: Q1 (Jan-Mar), Q2 (Apr-Jun), Q3 (Jul-Sep), Q4 (Oct-Dec)
- **Month**: Calendar month (1st to last day of month)
- **Term**: Based on cycle code (e.g., '2024-Q1', '2024-Annual')

## Usage Examples

### Basic Validation

```python
from backend.eom_validation import EOMNominationValidator

validator = EOMNominationValidator(db_session)

result = validator.validate_nomination(
    nominee_email='teacher1@eternity.edu',
    eom_cycle_id=1,
    nominated_by='manager@eternity.edu',
    category='academic',
    check_attendance=True
)

if result.is_valid:
    print("Nomination is valid!")
else:
    print(f"Errors: {result.errors}")
```

### Creating Rotation Rules

```python
# Create a rule for Academic category
rule = validator.create_rotation_rule(
    category=EOMCategory.ACADEMIC,
    cycle_id=1,
    cooldown_period=3,  # 3 periods cooldown
    max_wins_per_period=1,  # Max 1 win per period
    period_type='year',  # Yearly period
    is_active=True
)
```

### Checking Eligibility

```python
eligibility = validator.check_nominee_rotation_eligibility(
    nominee_email='teacher1@eternity.edu',
    category=EOMCategory.ACADEMIC,
    eom_cycle_id=1
)

if eligibility['eligible']:
    print("Nominee is eligible for nomination")
else:
    print(f"Not eligible: {eligibility['reason']}")
```

### Using Rotation Manager

```python
from backend.eom_rotation_manager import EOMRotationManager

manager = EOMRotationManager(db_session)

# Set up default rules
rules = manager.setup_default_rules(cycle_id=1)

# Get eligible nominees
eligible = manager.get_eligible_nominees(
    eom_cycle_id=1,
    category=EOMCategory.ACADEMIC
)

# Get ineligible nominees with reasons
ineligible = manager.get_ineligible_nominees(
    eom_cycle_id=1,
    category=EOMCategory.ACADEMIC
)
```

### Getting Analytics

```python
analytics = validator.get_rotation_analytics(
    cycle_id=1,
    category=EOMCategory.ACADEMIC
)

print(f"Total Wins: {analytics['total_wins']}")
print(f"Unique Winners: {analytics['unique_winners']}")
print(f"Compliance Rate: {analytics['rotation_compliance']['academic']['compliance_rate']}")
```

## API Endpoints

### Nomination Validation

- `POST /api/v2/eom/nominations/submit`: Submit nomination with validation
- `POST /api/v2/eom/nominations/validate`: Validate without submitting
- `POST /api/v2/eom/nominations/batch-validate`: Validate multiple nominations

### Rotation Rule Management

- `POST /api/v2/eom/rotation-rules/create`: Create a new rotation rule
- `PUT /api/v2/eom/rotation-rules/{rule_id}`: Update a rotation rule
- `GET /api/v2/eom/rotation-rules/cycle/{cycle_id}`: Get rules for a cycle
- `POST /api/v2/eom/rotation-rules/setup-defaults/{cycle_id}`: Set up default rules

### Eligibility Checking

- `POST /api/v2/eom/rotation-rules/check-eligibility`: Check nominee eligibility
- `GET /api/v2/eom/rotation-rules/eligible-nominees/{eom_cycle_id}`: Get eligible nominees
- `GET /api/v2/eom/rotation-rules/ineligible-nominees/{eom_cycle_id}`: Get ineligible nominees

### Analytics and Reporting

- `GET /api/v2/eom/rotation-rules/analytics/{cycle_id}`: Get rotation analytics
- `GET /api/v2/eom/rotation-rules/nominee-history/{nominee_email}`: Get nominee history
- `GET /api/v2/eom/rotation-rules/summary/{cycle_id}`: Get rotation summary
- `POST /api/v2/eom/rotation-rules/update-eligibility-flags/{eom_cycle_id}`: Update flags

## Validation Flow

1. **Rotation Rules Check**
   - Get rotation rules for category
   - Check cooldown period since last win
   - Check max wins in current period
   - Verify rotation_eligible flag

2. **Attendance Validation**
   - Check attendance records for the month
   - Calculate attendance rate
   - Verify minimum attendance requirements

3. **Duplicate Check**
   - Verify nominee not already nominated in this cycle/category

4. **Leader Limits**
   - Check if nominator is a leader
   - Verify leader hasn't exceeded nomination limit

5. **Additional Validations**
   - Verify nominee and nominator exist and are active
   - Check for self-nomination
   - Verify nominee is not also a voter

## Default Behavior

When no rotation rules are configured for a category, the system uses default behavior:
- **One win per term**: Prevents same person from winning in the same term
- **Warning for recent wins**: Warns if nominee has won recently (last 3 wins)

## Best Practices

1. **Set up rules early**: Configure rotation rules when setting up a new cycle
2. **Use appropriate periods**: Choose period type based on nomination frequency
3. **Monitor compliance**: Regularly check rotation analytics for violations
4. **Update eligibility flags**: Run `update_rotation_eligibility_flags()` after rule changes
5. **Review history**: Check nominee rotation history before making exceptions

## Error Handling

The validation system provides detailed error messages:
- **Rotation errors**: Specific cooldown and max wins violations
- **Attendance errors**: Attendance rate below minimum
- **Duplicate errors**: Already nominated in this cycle
- **Leader limit errors**: Leader has already nominated

All errors include context and actionable information for resolution.

