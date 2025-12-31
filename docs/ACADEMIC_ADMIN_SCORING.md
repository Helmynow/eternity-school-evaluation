# Academic vs Admin Weighted Scoring System

## Overview

The Academic vs Admin Weighted Scoring System provides specialized weighted scoring for academic and administrative staff evaluations. It uses different weight matrices to reflect the different evaluation priorities for each staff type.

## Key Features

### 1. Separate Weight Matrices

**Academic Staff Weight Matrix:**
- Emphasizes QA (Quality Assurance) - Full weight (1.0)
- High weight on peer review (0.9)
- Full weight on manager review (1.0)
- High weight on P&C (0.8)

**Admin Staff Weight Matrix:**
- Emphasizes P&C (People & Culture) - Full weight (1.0)
- High weight on manager review (1.0)
- Lower weight on QA (0.7)
- High weight on peer review (0.8)

### 2. Automatic Staff Type Detection

The system automatically detects whether a staff member is academic or admin based on:
- Role title keywords
- Department keywords
- Defaults to 'academic' if unclear

### 3. Context-Specific Weighting

Each rater context has different weights depending on staff type:
- **CEO**: Full weight (1.0) for both
- **P&C**: Higher for admin (1.0) vs academic (0.8)
- **QA**: Higher for academic (1.0) vs admin (0.7)
- **Peer Review**: Higher for academic (0.9) vs admin (0.8)

### 4. Evaluation Requirements

Different minimum/maximum evaluation requirements:
- **Academic**: More QA evaluations (min 2), more peer reviews (min 3)
- **Admin**: More P&C evaluations (min 2)

## Weight Matrices

### Academic Staff Matrix

```python
{
    'CEO': 1.0,           # Full weight
    'P&C': 0.8,           # High weight
    'QA': 1.0,            # Full weight (critical for academics)
    'peer_review': 0.9,   # High weight
    'manager_review': 1.0, # Full weight
    'direct_report_review': 0.7,
    'self_review': 0.5,
    '360_review': 0.85
}
```

### Admin Staff Matrix

```python
{
    'CEO': 1.0,           # Full weight
    'P&C': 1.0,           # Full weight (critical for admin)
    'QA': 0.7,            # Lower weight
    'peer_review': 0.8,   # High weight
    'manager_review': 1.0, # Full weight
    'direct_report_review': 0.6,
    'self_review': 0.5,
    '360_review': 0.85
}
```

## Usage Examples

### Calculate Weighted Score

```python
from backend.academic_admin_scoring import AcademicAdminScoring

scorer = AcademicAdminScoring(db_session)

# Calculate score for a staff member
score = scorer.calculate_weighted_score(
    cycle_id=1,
    target_email='teacher1@eternity.edu'
)

print(f"Staff Type: {score.staff_type}")
print(f"Raw Average: {score.raw_average:.2f}")
print(f"Weighted Average: {score.weighted_average:.2f}")
print(f"Final Score: {score.final_score:.2f}")
```

### Batch Scoring

```python
# Get all academic staff scores
academic_scores = scorer.calculate_batch_scores(
    cycle_id=1,
    staff_type='academic'
)

# Get all admin staff scores
admin_scores = scorer.calculate_batch_scores(
    cycle_id=1,
    staff_type='admin'
)
```

### Compare Academic vs Admin

```python
comparison = scorer.compare_academic_vs_admin(cycle_id=1)

print(f"Academic Mean: {comparison.academic_stats['mean_weighted']:.2f}")
print(f"Admin Mean: {comparison.admin_stats['mean_weighted']:.2f}")
print(f"Difference: {comparison.differences['mean_difference']:.2f}")

for recommendation in comparison.recommendations:
    print(f"  - {recommendation}")
```

### Validate Evaluations

```python
validation = scorer.validate_evaluations(
    cycle_id=1,
    staff_type='academic'
)

if validation['is_valid']:
    print("All evaluations meet requirements")
else:
    print("Errors found:")
    for error in validation['errors']:
        print(f"  - {error}")
```

### Get Score Distribution

```python
distribution = scorer.get_score_distribution(
    cycle_id=1,
    staff_type='academic'
)

print(f"Mean: {distribution['mean']:.2f}")
print(f"Median: {distribution['median']:.2f}")
print(f"Distribution: {distribution['distribution']}")
```

## API Endpoints

### Get Weighted Score

- `GET /api/v2/scoring/academic-admin/{cycle_id}/score/{email}`: Get weighted score for a staff member

### Batch Scoring

- `GET /api/v2/scoring/academic-admin/{cycle_id}/batch`: Get scores for multiple staff
  - Query params: `staff_type`, `target_emails`

### Comparison

- `GET /api/v2/scoring/academic-admin/{cycle_id}/compare`: Compare academic vs admin scoring

### Distribution

- `GET /api/v2/scoring/academic-admin/{cycle_id}/distribution`: Get score distribution
  - Query param: `staff_type`

### Validation

- `GET /api/v2/scoring/academic-admin/{cycle_id}/validate`: Validate evaluations
  - Query param: `staff_type` (required)

### Weight Matrices

- `GET /api/v2/scoring/academic-admin/weight-matrices`: Get weight matrices

## Staff Type Detection

### Academic Keywords

- Role titles: teacher, instructor, professor, lecturer, faculty
- Departments: academic, curriculum, pedagogy, education

### Admin Keywords

- Role titles: admin, administrative, coordinator, manager, director
- Departments: administration, operations, hr, finance, it

## Score Calculation

### Formula

For each evaluation:
1. Get base weight from matrix: `weight = matrix[staff_type][context]`
2. Apply assignment multiplier: `final_weight = weight * assignment.weight`
3. Calculate weighted score: `weighted_score = rating * final_weight`

Overall weighted average:
```
weighted_average = sum(weighted_scores) / sum(weights)
```

## Minimum/Maximum Requirements

### Academic Staff

- **QA**: Min 2, Max 5
- **Peer Review**: Min 3, Max 8
- **P&C**: Min 1, Max 2
- **Manager Review**: Min 1, Max 2

### Admin Staff

- **P&C**: Min 2, Max 5
- **Peer Review**: Min 2, Max 6
- **QA**: Min 1, Max 3
- **Manager Review**: Min 1, Max 2

## Best Practices

1. **Ensure Balanced Coverage**: Both academic and admin should have adequate evaluations
2. **Use Appropriate Weights**: Weight matrices reflect different priorities
3. **Validate Requirements**: Check minimum/maximum requirements before finalizing
4. **Monitor Fairness**: Use comparison tool to ensure fairness
5. **Review Distributions**: Check score distributions for anomalies

## Integration

The system integrates with:
- `WeightMatrixHandler`: Uses similar structure
- `Assignment` and `Evaluation` models: Loads evaluation data
- `Person` model: Determines staff type
- FastAPI: Provides RESTful API endpoints

## Performance

- **Optimized Queries**: Single join query for data loading
- **Vectorized Calculations**: NumPy for efficient score calculations
- **Batch Processing**: Efficient batch scoring
- **Scalable**: Handles large evaluation cycles

