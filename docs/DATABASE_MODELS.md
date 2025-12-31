# Database Models Documentation

## Overview

The Eternity School Evaluation System uses SQLAlchemy ORM models with comprehensive support for:
- Staff segmentation (National/International/Whole School)
- EOM nominations with categories and rotation tracking
- MRE evaluations with weight matrix support
- Complete audit trail for all actions

## Core Models

### Person (Staff Table)

Enhanced staff table with segment support.

**Fields:**
- `email` (Primary Key): Staff email address
- `full_name`: Full name of staff member
- `role_title`: Job title/role
- `department`: Department name
- `segment` (Enum): Staff segment - `NATIONAL`, `INTERNATIONAL`, or `WHOLE_SCHOOL`
- `hire_date`: Date of hire
- `active`: Whether staff member is currently active
- `created_at`: Timestamp of record creation
- `updated_at`: Timestamp of last update

**Usage:**
```python
from backend.database import Person, StaffSegment

# Create staff member
staff = Person(
    email="teacher1@eternity.edu",
    full_name="John Doe",
    role_title="Mathematics Teacher",
    department="Academics",
    segment=StaffSegment.NATIONAL,
    active=True
)
db.add(staff)
db.commit()

# Query by segment
national_staff = db.query(Person).filter(
    Person.segment == StaffSegment.NATIONAL,
    Person.active == True
).all()
```

### Assignment (MRE Evaluations)

MRE assignments with weight matrix support.

**Fields:**
- `id` (Primary Key)
- `cycle_id`: Reference to evaluation cycle
- `rater_email`: Email of person doing the evaluation
- `target_email`: Email of person being evaluated
- `target_group`: Group classification (peers, direct_reports, etc.)
- `rater_context`: Context of rater (peer_review, manager_review, etc.)
- `weight`: Weight factor for this evaluation
- `weight_matrix_id`: Reference to weight matrix configuration
- `created_at`, `updated_at`: Timestamps

**Usage:**
```python
from backend.database import Assignment, WeightMatrix

# Create assignment with weight matrix
assignment = Assignment(
    cycle_id=1,
    rater_email="manager@eternity.edu",
    target_email="teacher1@eternity.edu",
    target_group="direct_reports",
    rater_context="manager_review",
    weight=1.0,
    weight_matrix_id=1
)
db.add(assignment)
db.commit()
```

### WeightMatrix

Weight matrix configurations for MRE evaluations.

**Fields:**
- `id` (Primary Key)
- `cycle_id`: Reference to evaluation cycle
- `name`: Name of the weight matrix
- `description`: Description
- `matrix_config` (JSON): Weight matrix configuration
  - Format: `{"target_group": {"rater_context": weight, ...}, ...}`
- `is_active`: Whether this matrix is currently active
- `created_at`, `updated_at`: Timestamps

**Usage:**
```python
from backend.database import WeightMatrix

# Create weight matrix
matrix = WeightMatrix(
    cycle_id=1,
    name="Q1 2024 Weight Matrix",
    description="Weight matrix for Q1 2024 evaluations",
    matrix_config={
        "academic": {
            "CEO": 1.0,
            "P&C": 0.8,
            "QA": 0.9,
            "peer_review": 0.7,
            "manager_review": 1.0
        },
        "admin": {
            "CEO": 1.0,
            "P&C": 0.9,
            "QA": 0.7,
            "peer_review": 0.8
        }
    },
    is_active=True
)
db.add(matrix)
db.commit()
```

### EOMNominee (EOM Nominations)

EOM nominations with categories and rotation tracking.

**Fields:**
- `id` (Primary Key)
- `eom_cycle_id`: Reference to EOM cycle
- `nominee_email`: Email of nominated person
- `nominated_by`: Email of person making nomination
- `nomination_reason`: Reason for nomination
- `category` (Enum): Category of nomination
  - `ACADEMIC`, `ADMIN`, `SUPPORT`, `LEADERSHIP`, `INNOVATION`, 
    `COLLABORATION`, `STUDENT_ENGAGEMENT`
- `rotation_eligible`: Whether person can be nominated again
- `last_nominated_cycle_id`: Last cycle this person was nominated
- `last_won_cycle_id`: Last cycle this person won
- `nomination_count`: Total nominations across all cycles
- `win_count`: Total wins across all cycles
- `votes_received`: Votes received in current cycle
- `created_at`, `updated_at`: Timestamps

**Usage:**
```python
from backend.database import EOMNominee, EOMCategory

# Create nomination
nomination = EOMNominee(
    eom_cycle_id=1,
    nominee_email="teacher1@eternity.edu",
    nominated_by="manager@eternity.edu",
    nomination_reason="Outstanding performance in student engagement",
    category=EOMCategory.STUDENT_ENGAGEMENT,
    rotation_eligible=True
)
db.add(nomination)
db.commit()

# Check rotation eligibility
nominee = db.query(EOMNominee).filter(
    EOMNominee.nominee_email == "teacher1@eternity.edu"
).first()

if nominee.rotation_eligible:
    print(f"Can be nominated. Last nominated: {nominee.last_nominated_cycle_id}")
```

### EOMRotationRule

Rules for EOM category rotation and eligibility.

**Fields:**
- `id` (Primary Key)
- `category` (Enum): EOM category
- `cycle_id`: Reference to cycle
- `cooldown_period`: Cycles before eligible again (default: 3)
- `max_wins_per_period`: Maximum wins in a period (default: 1)
- `period_type`: Period type - 'year', 'quarter', 'month' (default: 'year')
- `is_active`: Whether rule is active
- `created_at`: Timestamp

**Usage:**
```python
from backend.database import EOMRotationRule, EOMCategory

# Create rotation rule
rule = EOMRotationRule(
    category=EOMCategory.ACADEMIC,
    cycle_id=1,
    cooldown_period=3,
    max_wins_per_period=1,
    period_type='year',
    is_active=True
)
db.add(rule)
db.commit()
```

### AuditLog

Comprehensive audit trail for all system actions.

**Fields:**
- `id` (Primary Key)
- `action_type` (Enum): Type of action
  - `CREATE`, `UPDATE`, `DELETE`, `SUBMIT`, `APPROVE`, `REJECT`, `VIEW`, `EXPORT`
- `entity_type`: Type of entity (e.g., 'person', 'assignment', 'evaluation')
- `entity_id`: ID of affected entity
- `user_email`: Email of user performing action
- `user_role`: Role of user
- `changes` (JSON): Before/after values for updates
- `description`: Human-readable description
- `ip_address`: IP address of user
- `user_agent`: User agent string
- `created_at`: Timestamp

**Usage:**
```python
from backend.database import AuditLog, ActionType
from backend.audit_logger import AuditLogger

# Using AuditLogger utility
logger = AuditLogger(db)

# Log create action
logger.log_create(
    entity_type="person",
    entity_id=1,
    user_email="admin@eternity.edu",
    description="Created new staff member"
)

# Log update with changes
logger.log_update(
    entity_type="assignment",
    entity_id=5,
    user_email="manager@eternity.edu",
    changes={
        "before": {"weight": 1.0},
        "after": {"weight": 1.2}
    },
    description="Updated assignment weight"
)

# Query audit history
history = logger.get_audit_history(
    entity_type="person",
    entity_id=1,
    limit=50
)
```

## Enums

### StaffSegment
- `NATIONAL`: National segment staff
- `INTERNATIONAL`: International segment staff
- `WHOLE_SCHOOL`: Whole school staff

### EOMCategory
- `ACADEMIC`: Academic excellence
- `ADMIN`: Administrative excellence
- `SUPPORT`: Support staff excellence
- `LEADERSHIP`: Leadership excellence
- `INNOVATION`: Innovation excellence
- `COLLABORATION`: Collaboration excellence
- `STUDENT_ENGAGEMENT`: Student engagement excellence

### ActionType
- `CREATE`: Entity creation
- `UPDATE`: Entity update
- `DELETE`: Entity deletion
- `SUBMIT`: Submission action
- `APPROVE`: Approval action
- `REJECT`: Rejection action
- `VIEW`: View action
- `EXPORT`: Export action

## Indexes

The models include optimized indexes for common queries:

- **Person**: `segment`, `active`
- **Assignment**: `cycle_id`, `rater_email`, `target_email`, `rater_context`
- **EOMNominee**: `category`, `rotation_eligible`, `eom_cycle_id`
- **EOMCycle**: `year`, `month`
- **WeightMatrix**: `cycle_id`, `is_active`
- **AuditLog**: `action_type`, `entity_type`+`entity_id`, `user_email`, `created_at`
- **Attendance**: `person_email`, `date`

## Relationships

### Person Relationships
- `assignments_as_rater`: Assignments where person is the rater
- `assignments_as_target`: Assignments where person is the target
- `eom_nominations`: EOM nominations for this person
- `eom_nominated_by`: EOM nominations made by this person
- `audit_logs`: Audit log entries by this user

### Assignment Relationships
- `cycle`: Evaluation cycle
- `rater`: Person doing the evaluation
- `target`: Person being evaluated
- `evaluations`: Evaluation submissions
- `weight_matrix`: Weight matrix configuration

### EOMNominee Relationships
- `eom_cycle`: EOM cycle
- `nominee_person`: Nominated person
- `nominator_person`: Person making nomination
- `last_nominated_cycle`: Last cycle nominated
- `last_won_cycle`: Last cycle won

## Best Practices

1. **Always use enums** for segment, category, and action types
2. **Use AuditLogger** for all create/update/delete operations
3. **Check rotation eligibility** before creating EOM nominations
4. **Use weight matrices** for consistent evaluation weighting
5. **Index frequently queried fields** (already included in models)
6. **Use timestamps** (`created_at`, `updated_at`) for tracking changes

## Migration Notes

When upgrading from the old schema:

1. **Add segment to Person**: Set default to `WHOLE_SCHOOL` for existing records
2. **Add weight_matrix_id to Assignment**: Can be nullable initially
3. **Convert EOM category strings to enum**: Map existing categories to enum values
4. **Create audit_logs table**: New table, no migration needed
5. **Add rotation tracking**: Initialize `nomination_count` and `win_count` from historical data

