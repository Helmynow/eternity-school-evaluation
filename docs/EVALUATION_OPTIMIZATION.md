# Evaluation Calculation Optimization for 200+ Staff Members

## Overview

This document describes the optimizations implemented for processing evaluation calculations for 200+ staff members efficiently.

## Performance Challenges

### Before Optimization

**Issues:**
1. **N+1 Query Problem**: Individual queries for each staff member
   - N queries to get person information
   - N queries to get evaluations for each person
   - Total: 2N+ queries for N staff members

2. **Inefficient Looping**: Sequential processing of each staff member
   - No bulk operations
   - No vectorization
   - High memory overhead

3. **Repeated Calculations**: Same calculations performed multiple times
   - Staff type determination repeated
   - Weight lookups repeated
   - No caching

**Performance Impact:**
- For 200 staff: ~400+ database queries
- Processing time: Minutes for large datasets
- Memory usage: High due to inefficient data structures

## Optimizations Implemented

### 1. Bulk Database Queries

**Before:**
```python
# N queries for N staff members
for email in target_emails:
    person = db.query(Person).filter(Person.email == email).first()
    evaluations = db.query(Evaluation).join(Assignment).filter(...).all()
```

**After:**
```python
# Single bulk query for all evaluations
evaluations = (
    db.query(Evaluation, Assignment)
    .join(Assignment, Evaluation.assignment_id == Assignment.id)
    .filter(Assignment.cycle_id == cycle_id)
    .all()
)

# Single bulk query for all people
people = db.query(Person).filter(Person.email.in_(target_emails)).all()
```

**Impact:**
- Reduces queries from 2N+ to 2 queries
- For 200 staff: 400+ queries → 2 queries
- **99.5% reduction in database queries**

### 2. Vectorized Operations with Pandas/NumPy

**Before:**
```python
# Sequential processing
for target_email in target_emails:
    scores = []
    weights = []
    for eval in evaluations:
        if eval.target_email == target_email:
            scores.append(eval.rating)
            weights.append(weight)
    weighted_avg = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
```

**After:**
```python
# Vectorized operations
evaluations_df = pd.DataFrame(evaluations_data)
grouped = evaluations_df.groupby('target_email')

for target_email, group_df in grouped:
    ratings = group_df['rating'].values  # NumPy array
    weights = group_df['base_weight'].values
    weighted_avg = np.sum(ratings * weights) / np.sum(weights)
```

**Impact:**
- Uses optimized NumPy operations
- 10-100x faster for large datasets
- Lower memory overhead

### 3. Caching

**Staff Type Caching:**
```python
# Cache staff type lookups
self._staff_type_cache = {}

def _get_staff_type_cached(self, person):
    if person.email in self._staff_type_cache:
        return self._staff_type_cache[person.email]
    
    staff_type = self._determine_staff_type(person)
    self._staff_type_cache[person.email] = staff_type
    return staff_type
```

**Impact:**
- Eliminates repeated staff type calculations
- Reduces processing time for repeated lookups

### 4. Efficient Data Structures

**Pandas DataFrames:**
- Efficient columnar storage
- Fast grouping and aggregation
- Built-in vectorized operations
- Memory-efficient for large datasets

**NumPy Arrays:**
- Fast mathematical operations
- Optimized C implementations
- Low memory overhead

## Performance Metrics

### Query Reduction

| Staff Count | Before (Queries) | After (Queries) | Reduction |
|-------------|------------------|-----------------|-----------|
| 50          | 100+             | 2               | 98%       |
| 100         | 200+             | 2               | 99%       |
| 200         | 400+             | 2               | 99.5%     |
| 500         | 1000+            | 2               | 99.8%     |

### Processing Time

| Staff Count | Before (seconds) | After (seconds) | Speedup |
|-------------|------------------|-----------------|---------|
| 50          | ~5               | ~0.5            | 10x     |
| 100         | ~15              | ~1              | 15x     |
| 200         | ~45              | ~2              | 22.5x   |
| 500         | ~180             | ~5              | 36x     |

*Estimated based on typical evaluation counts per staff member*

## Usage

### Basic Usage

```python
from backend.optimized_evaluation_calculator import OptimizedEvaluationCalculator

calculator = OptimizedEvaluationCalculator(db_session)

# Calculate scores for all staff (optimized)
scores = calculator.calculate_batch_scores_optimized(cycle_id=1)

# Calculate for specific staff type
academic_scores = calculator.calculate_batch_scores_optimized(
    cycle_id=1,
    staff_type='academic'
)

# Calculate for specific emails
specific_scores = calculator.calculate_batch_scores_optimized(
    cycle_id=1,
    target_emails=['person1@eternity.edu', 'person2@eternity.edu']
)
```

### Get Statistics

```python
# Get aggregate statistics
stats = calculator.get_score_statistics(cycle_id=1)

# Filter by staff type
academic_stats = calculator.get_score_statistics(
    cycle_id=1,
    staff_type='academic'
)
```

### Compare Academic vs Admin

```python
# Optimized comparison
comparison = calculator.compare_academic_vs_admin_optimized(cycle_id=1)

print(f"Academic Mean: {comparison['academic_stats']['mean']}")
print(f"Admin Mean: {comparison['admin_stats']['mean']}")
print(f"Difference: {comparison['differences']['mean_difference']}")
```

### Export to DataFrame

```python
# Export for further analysis
df = calculator.export_scores_to_dataframe(cycle_id=1)

# Use pandas operations
high_scores = df[df['weighted_average'] > 4.0]
average_by_type = df.groupby('staff_type')['weighted_average'].mean()
```

## API Endpoints

### Optimized Batch Scores

```
GET /api/v2/scoring/optimized/batch/{cycle_id}
```

**Query Parameters:**
- `staff_type`: Filter by staff type (academic/admin)
- `target_emails`: Comma-separated list of emails

**Response:**
```json
{
  "cycle_id": 1,
  "staff_type": "all",
  "total_scores": 200,
  "scores": [...]
}
```

### Statistics

```
GET /api/v2/scoring/optimized/statistics/{cycle_id}
```

**Query Parameters:**
- `staff_type`: Filter by staff type

**Response:**
```json
{
  "cycle_id": 1,
  "staff_type": "all",
  "statistics": {
    "count": 200,
    "mean": 4.2,
    "median": 4.1,
    "std": 0.5,
    "min": 3.0,
    "max": 5.0
  }
}
```

### Comparison

```
GET /api/v2/scoring/optimized/compare/{cycle_id}
```

**Response:**
```json
{
  "cycle_id": 1,
  "academic_stats": {...},
  "admin_stats": {...},
  "differences": {...},
  "recommendations": [...]
}
```

## Best Practices

### 1. Use Bulk Operations

**Good:**
```python
# Calculate all at once
scores = calculator.calculate_batch_scores_optimized(cycle_id=1)
```

**Bad:**
```python
# Don't loop and calculate individually
for email in emails:
    score = calculator.calculate_single_score_optimized(cycle_id=1, target_email=email)
```

### 2. Clear Cache When Needed

```python
# Clear cache if staff types change
calculator.clear_cache()
```

### 3. Use DataFrame Export for Analysis

```python
# Export to DataFrame for complex analysis
df = calculator.export_scores_to_dataframe(cycle_id=1)

# Use pandas for filtering, grouping, etc.
filtered = df[df['weighted_average'] > 4.0]
grouped = df.groupby('staff_type').agg({
    'weighted_average': ['mean', 'std', 'count']
})
```

### 4. Filter Early

```python
# Filter at query level, not after loading
scores = calculator.calculate_batch_scores_optimized(
    cycle_id=1,
    staff_type='academic'  # Filter early
)
```

## Memory Considerations

### For Very Large Datasets (1000+ staff)

1. **Process in Chunks:**
```python
# Process in batches of 200
chunk_size = 200
all_emails = get_all_staff_emails()

for i in range(0, len(all_emails), chunk_size):
    chunk = all_emails[i:i+chunk_size]
    scores = calculator.calculate_batch_scores_optimized(
        cycle_id=1,
        target_emails=chunk
    )
    # Process chunk results
```

2. **Clear Cache Periodically:**
```python
# Clear cache every N iterations
if i % 5 == 0:
    calculator.clear_cache()
```

3. **Use Generators for Large Results:**
```python
# For very large result sets, consider streaming
def stream_scores(cycle_id, chunk_size=200):
    all_emails = get_all_staff_emails()
    for i in range(0, len(all_emails), chunk_size):
        chunk = all_emails[i:i+chunk_size]
        yield calculator.calculate_batch_scores_optimized(
            cycle_id=cycle_id,
            target_emails=chunk
        )
```

## Migration Guide

### From Old Implementation

**Old Code:**
```python
scorer = AcademicAdminScoring(db_session)
scores = scorer.calculate_batch_scores(cycle_id=1, staff_type='academic')
```

**New Code:**
```python
calculator = OptimizedEvaluationCalculator(db_session)
scores = calculator.calculate_batch_scores_optimized(cycle_id=1, staff_type='academic')
```

### Key Differences

1. **Class Name**: `AcademicAdminScoring` → `OptimizedEvaluationCalculator`
2. **Method Name**: `calculate_batch_scores` → `calculate_batch_scores_optimized`
3. **Return Type**: `List[StaffTypeScore]` → `List[OptimizedScore]`
4. **Performance**: Much faster for large datasets

## Testing

Run performance tests:

```bash
pytest tests/test_optimized_evaluation_calculator.py -v
```

## Monitoring

Monitor these metrics:
- Query count per operation
- Processing time
- Memory usage
- Cache hit rate

## Future Optimizations

Potential further optimizations:
1. **Database Indexing**: Ensure proper indexes on frequently queried columns
2. **Connection Pooling**: Optimize database connection management
3. **Parallel Processing**: Use multiprocessing for very large datasets
4. **Caching Layer**: Redis/Memcached for frequently accessed data
5. **Materialized Views**: Pre-compute common aggregations

