# Database Model Enhancements Summary

## Overview

Enhanced SQLAlchemy models for the Eternity School Evaluation System with comprehensive support for:
1. Staff segmentation (National/International/Whole School)
2. EOM nominations with categories and rotation tracking
3. MRE evaluations with weight matrix support
4. Complete audit trail for all actions

## New Features

### 1. Staff Segmentation

**Enhanced Person Model:**
- Added `segment` field (Enum: `NATIONAL`, `INTERNATIONAL`, `WHOLE_SCHOOL`)
- Added `created_at` and `updated_at` timestamps
- Added indexes for efficient segment-based queries

**Usage:**
```python
staff = Person(
    email="teacher@eternity.edu",
    segment=StaffSegment.NATIONAL,
    ...
)
```

### 2. EOM Nominations with Categories and Rotation

**Enhanced EOMNominee Model:**
- Added `category` field (Enum with 7 categories)
- Added rotation tracking fields:
  - `rotation_eligible`: Can be nominated again
  - `last_nominated_cycle_id`: Last nomination cycle
  - `last_won_cycle_id`: Last win cycle
  - `nomination_count`: Total nominations
  - `win_count`: Total wins
  - `votes_received`: Current cycle votes
- Added timestamps

**New EOMRotationRule Model:**
- Defines rotation rules per category
- Configurable cooldown periods
- Maximum wins per period
- Period types (year/quarter/month)

**Usage:**
```python
nomination = EOMNominee(
    category=EOMCategory.STUDENT_ENGAGEMENT,
    rotation_eligible=True,
    ...
)
```

### 3. MRE Evaluations with Weight Matrix Support

**Enhanced Assignment Model:**
- Added `weight_matrix_id` foreign key
- Added relationship to `WeightMatrix`
- Added timestamps

**New WeightMatrix Model:**
- Stores weight matrix configurations as JSON
- Links to evaluation cycles
- Active/inactive status
- Format: `{"target_group": {"rater_context": weight, ...}}`

**Enhanced Evaluation Model:**
- Added `weighted_rating` field
- Added `domain_scores` JSON field
- Changed `submitted_at` to DateTime
- Added timestamps

**Usage:**
```python
matrix = WeightMatrix(
    matrix_config={
        "academic": {
            "CEO": 1.0,
            "peer_review": 0.7,
            ...
        }
    }
)

assignment = Assignment(
    weight_matrix_id=matrix.id,
    ...
)
```

### 4. Audit Trail

**New AuditLog Model:**
- Tracks all system actions
- Stores action type (CREATE, UPDATE, DELETE, etc.)
- Stores entity type and ID
- Stores user information
- Stores before/after changes for updates
- Stores IP address and user agent
- Comprehensive indexing for queries

**New AuditLogger Utility:**
- Helper class for creating audit entries
- Methods for common actions (log_create, log_update, etc.)
- Query methods for audit history
- Automatic IP/user agent capture from Flask request

**Usage:**
```python
logger = AuditLogger(db_session)
logger.log_create("person", person_id, user_email, "Created staff member")
logger.log_update("assignment", assignment_id, user_email, 
                  changes={"before": {...}, "after": {...}})
```

## New Enums

### StaffSegment
- `NATIONAL`
- `INTERNATIONAL`
- `WHOLE_SCHOOL`

### EOMCategory
- `ACADEMIC`
- `ADMIN`
- `SUPPORT`
- `LEADERSHIP`
- `INNOVATION`
- `COLLABORATION`
- `STUDENT_ENGAGEMENT`

### ActionType
- `CREATE`
- `UPDATE`
- `DELETE`
- `SUBMIT`
- `APPROVE`
- `REJECT`
- `VIEW`
- `EXPORT`

## Database Indexes

Added indexes for performance:
- Person: `segment`, `active`
- Assignment: `cycle_id`, `rater_email`, `target_email`, `rater_context`
- EOMNominee: `category`, `rotation_eligible`, `eom_cycle_id`
- EOMCycle: `year`, `month`
- WeightMatrix: `cycle_id`, `is_active`
- AuditLog: `action_type`, `entity_type`+`entity_id`, `user_email`, `created_at`
- Attendance: `person_email`, `date`

## Files Created/Modified

### Modified
- `backend/database.py`: Enhanced all models, added new models

### Created
- `backend/audit_logger.py`: Audit logging utility
- `docs/DATABASE_MODELS.md`: Comprehensive documentation
- `docs/MODEL_ENHANCEMENTS_SUMMARY.md`: This file
- `examples/database_usage_example.py`: Usage examples

## Migration Considerations

When upgrading existing databases:

1. **Person.segment**: Add with default `WHOLE_SCHOOL` for existing records
2. **Assignment.weight_matrix_id**: Add as nullable initially
3. **EOMNominee.category**: Convert string to enum, map existing values
4. **EOMNominee rotation fields**: Initialize from historical data
5. **AuditLog table**: New table, no migration needed
6. **WeightMatrix table**: New table, no migration needed
7. **EOMRotationRule table**: New table, no migration needed

## Next Steps

1. Run database migrations to add new fields
2. Update existing code to use new enums
3. Integrate AuditLogger into API endpoints
4. Implement rotation eligibility checks in EOM nomination logic
5. Update weight matrix handler to use new WeightMatrix model

