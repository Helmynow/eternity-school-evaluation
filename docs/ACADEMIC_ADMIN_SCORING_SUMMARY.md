# Academic vs Admin Weighted Scoring System - Implementation Summary

## Overview

A specialized weighted scoring system for academic vs admin staff evaluations has been implemented. The system uses different weight matrices to reflect the different evaluation priorities for each staff type.

## Key Components

### 1. AcademicAdminScoring Class (`backend/academic_admin_scoring.py`)

**Core Methods:**
- `get_staff_type()`: Automatically detects academic vs admin staff
- `get_weight_matrix()`: Returns appropriate weight matrix
- `calculate_weighted_score()`: Calculates score for a single staff member
- `calculate_batch_scores()`: Batch scoring for multiple staff
- `compare_academic_vs_admin()`: Comparative analysis
- `validate_evaluations()`: Validates minimum/maximum requirements
- `get_score_distribution()`: Score distribution analysis

**Data Structures:**
- `StaffTypeScore`: Detailed score breakdown
- `ComparisonResult`: Academic vs admin comparison

### 2. Weight Matrices

**Academic Staff Matrix:**
- QA: 1.0 (full weight - critical for academics)
- Peer Review: 0.9 (high weight)
- Manager Review: 1.0 (full weight)
- P&C: 0.8 (high weight)

**Admin Staff Matrix:**
- P&C: 1.0 (full weight - critical for admin)
- Manager Review: 1.0 (full weight)
- Peer Review: 0.8 (high weight)
- QA: 0.7 (lower weight)

### 3. FastAPI Endpoints (`backend/fastapi_app.py`)

**Scoring Endpoints:**
- `GET /api/v2/scoring/academic-admin/{cycle_id}/score/{email}`: Get weighted score
- `GET /api/v2/scoring/academic-admin/{cycle_id}/batch`: Batch scoring
- `GET /api/v2/scoring/academic-admin/{cycle_id}/compare`: Compare academic vs admin
- `GET /api/v2/scoring/academic-admin/{cycle_id}/distribution`: Score distribution
- `GET /api/v2/scoring/academic-admin/{cycle_id}/validate`: Validate evaluations
- `GET /api/v2/scoring/academic-admin/weight-matrices`: Get weight matrices

### 4. Testing (`tests/test_academic_admin_scoring.py`)

Comprehensive unit tests covering:
- Staff type detection
- Weight matrix retrieval
- Weighted score calculation
- Batch scoring
- Comparison analysis
- Validation
- Score distribution

### 5. Examples (`examples/academic_admin_scoring_example.py`)

Usage examples demonstrating:
- Weighted score calculation
- Weight matrices
- Batch scoring
- Comparison
- Validation
- Distribution analysis
- Staff type detection

## Features

### Staff Type Detection

**Automatic Detection:**
- Checks role title for keywords
- Checks department for keywords
- Defaults to 'academic' if unclear

**Academic Keywords:**
- teacher, instructor, professor, lecturer, faculty
- academic, curriculum, pedagogy, education

**Admin Keywords:**
- admin, administrative, coordinator, manager, director
- secretary, assistant, operations, hr, finance, it

### Weighted Scoring

**Calculation Process:**
1. Determine staff type (academic or admin)
2. Get appropriate weight matrix
3. For each evaluation:
   - Get base weight from matrix
   - Apply assignment-specific multiplier
   - Calculate weighted score
4. Calculate overall weighted average

**Formula:**
```
weighted_average = sum(rating * weight) / sum(weights)
```

### Evaluation Requirements

**Academic Staff:**
- QA: Min 2, Max 5
- Peer Review: Min 3, Max 8
- P&C: Min 1, Max 2

**Admin Staff:**
- P&C: Min 2, Max 5
- Peer Review: Min 2, Max 6
- QA: Min 1, Max 3

### Comparative Analysis

**Comparison Features:**
- Mean scores for both types
- Median scores
- Standard deviations
- Score differences
- Fairness recommendations

## Usage

### Python

```python
from backend.academic_admin_scoring import AcademicAdminScoring

scorer = AcademicAdminScoring(db_session)

# Calculate score
score = scorer.calculate_weighted_score(
    cycle_id=1,
    target_email='teacher1@eternity.edu'
)

# Compare
comparison = scorer.compare_academic_vs_admin(cycle_id=1)
```

### API

```bash
# Get weighted score
GET /api/v2/scoring/academic-admin/1/score/teacher1@eternity.edu

# Batch scoring
GET /api/v2/scoring/academic-admin/1/batch?staff_type=academic

# Compare
GET /api/v2/scoring/academic-admin/1/compare

# Distribution
GET /api/v2/scoring/academic-admin/1/distribution?staff_type=academic

# Validate
GET /api/v2/scoring/academic-admin/1/validate?staff_type=academic
```

## Key Advantages

1. **Specialized Weighting**: Different priorities for academic vs admin
2. **Automatic Detection**: No manual classification needed
3. **Fairness Monitoring**: Comparative analysis ensures fairness
4. **Validation**: Ensures evaluation requirements are met
5. **Comprehensive Analysis**: Distribution and statistical analysis
6. **Batch Processing**: Efficient scoring for multiple staff

## Integration

- **Database**: Uses Person, Assignment, Evaluation models
- **Weight Matrix Handler**: Similar structure and concepts
- **FastAPI**: Provides RESTful API endpoints
- **Bias Detection**: Can integrate with bias detection systems

## Files Created

- `backend/academic_admin_scoring.py`: Main implementation
- `examples/academic_admin_scoring_example.py`: Usage examples
- `tests/test_academic_admin_scoring.py`: Unit tests
- `docs/ACADEMIC_ADMIN_SCORING.md`: Documentation
- `docs/ACADEMIC_ADMIN_SCORING_SUMMARY.md`: This summary

## Files Modified

- `backend/fastapi_app.py`: Added academic/admin scoring endpoints

## Next Steps

1. **Run Scoring**: Calculate weighted scores for evaluation cycles
2. **Monitor Fairness**: Use comparison tool regularly
3. **Validate Requirements**: Ensure minimum/maximum requirements are met
4. **Review Distributions**: Check score distributions for anomalies
5. **Adjust Weights**: Fine-tune weight matrices based on results

