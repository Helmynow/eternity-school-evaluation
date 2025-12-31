# Complete 360-Degree Bias Detection System

## Overview

The Complete 360-Degree Bias Detection System is a comprehensive solution for identifying and analyzing bias in multi-rater evaluation systems. It provides detailed analysis across multiple dimensions of bias, generates actionable recommendations, and ensures 360-degree evaluation completeness.

## Features

### 1. Structural Bias Detection
- **360-Degree Completeness**: Validates that all required perspectives (peer, manager, direct report, self) are represented
- **Evaluation Coverage**: Checks minimum evaluation requirements per context
- **Context Balance**: Analyzes distribution of evaluations across different rater contexts

### 2. Role-Based Bias
- Detects significant differences in ratings between different role relationships
- Identifies patterns where manager, peer, or direct report ratings systematically differ
- Provides statistical analysis using Kruskal-Wallis tests

### 3. Temporal Bias
- **Recency Bias**: Detects if recent events disproportionately influence ratings
- **Primacy Bias**: Identifies if early impressions affect ratings
- Analyzes correlation between submission timing and rating scores

### 4. Distribution Bias
- **Centrality Bias**: Identifies tendency to avoid extreme ratings
- **Harshness Bias**: Detects raters who consistently rate lower than average
- **Leniency Bias**: Detects raters who consistently rate higher than average

### 5. Similarity Bias
- **Halo Effect**: Detects when raters give similar scores across all dimensions
- **Low Variance Detection**: Identifies raters with insufficient rating differentiation

### 6. Advanced ML-Based Detection
- **Outlier Detection**: Uses Isolation Forest to identify unusual rating patterns
- **Reciprocal Bias**: Detects mutual high ratings between pairs
- **Systematic Patterns**: Identifies organization-wide bias patterns

### 7. Inter-Rater Reliability
- Measures agreement between multiple raters for the same target
- Calculates coefficient of variation to assess rating consistency
- Identifies targets with high disagreement between raters

## API Usage

### Generate Complete Report

```bash
GET /api/cycles/<cycle_id>/360_bias_report
```

**Response:**
```json
{
  "cycle_id": 1,
  "overall_bias_score": 0.45,
  "bias_level": "medium",
  "total_evaluations": 150,
  "total_raters": 25,
  "total_targets": 30,
  "findings_count": 5,
  "findings_by_type": {
    "role_bias": 1,
    "harshness_bias": 2,
    "structural_incomplete_360": 1,
    "temporal_bias": 1
  },
  "findings_by_severity": {
    "high": 1,
    "medium": 3,
    "low": 1
  },
  "findings": [...],
  "context_coverage": {...},
  "statistical_summary": {...},
  "recommendations": [...]
}
```

### Get Target-Specific Summary

```bash
GET /api/cycles/<cycle_id>/360_bias/target/<target_email>
```

**Response:**
```json
{
  "target_email": "teacher1@eternity.edu",
  "status": "analyzed",
  "total_evaluations": 8,
  "mean_rating": 4.2,
  "std_rating": 0.5,
  "context_breakdown": {
    "peer_review": {
      "count": 3,
      "mean": 4.3,
      "std": 0.4
    },
    "manager_review": {
      "count": 1,
      "mean": 4.5,
      "std": 0.0
    }
  },
  "missing_contexts": ["direct_report_review"],
  "inter_rater_reliability": {
    "coefficient_of_variation": 0.12,
    "interpretation": "high"
  },
  "is_complete_360": false
}
```

## Python Usage

### Basic Usage

```python
from backend.database import Database
from backend.bias_detection_360 import Complete360BiasDetection

# Initialize
db = Database()
db_session = db.get_session()
detector = Complete360BiasDetection(db_session)

# Generate complete report
report = detector.generate_complete_report(cycle_id=1)

# Access findings
for finding in report.findings:
    print(f"{finding.bias_type}: {finding.description}")
    print(f"Severity: {finding.severity}")
    print(f"Score: {finding.score}")
    print("Recommendations:")
    for rec in finding.recommendations:
        print(f"  - {rec}")
```

### Target-Specific Analysis

```python
# Get bias summary for specific target
summary = detector.get_bias_summary_by_target(
    cycle_id=1,
    target_email='teacher1@eternity.edu'
)

if summary['status'] == 'analyzed':
    print(f"Mean Rating: {summary['mean_rating']}")
    print(f"Is Complete 360: {summary['is_complete_360']}")
    print(f"Missing Contexts: {summary['missing_contexts']}")
```

## Bias Finding Structure

Each bias finding includes:

- **bias_type**: Type of bias detected
- **severity**: 'low', 'medium', 'high', or 'critical'
- **score**: 0-1 normalized bias score
- **description**: Human-readable description
- **affected_raters**: List of affected rater emails
- **affected_targets**: List of affected target emails
- **evidence**: Detailed evidence and statistics
- **recommendations**: Actionable recommendations

## Bias Types

1. **structural_incomplete_360**: Missing required 360-degree perspectives
2. **structural_insufficient_evaluations**: Not enough evaluations per context
3. **role_bias**: Differences between role-based ratings
4. **temporal_bias**: Recency or primacy effects
5. **centrality_bias**: Tendency to avoid extremes
6. **harshness_bias**: Consistently low ratings
7. **leniency_bias**: Consistently high ratings
8. **similarity_bias_halo**: Halo effect / low variance
9. **outlier_patterns**: Unusual rating patterns
10. **reciprocal_bias**: Mutual high ratings
11. **low_inter_rater_reliability**: High disagreement between raters
12. **context_imbalance**: Uneven distribution across contexts

## Overall Bias Score

The overall bias score (0-1) is calculated as:
- Weighted combination of all findings
- Severity weights: critical=1.0, high=0.75, medium=0.5, low=0.25
- Formula: 60% max weighted score + 40% average weighted score

**Interpretation:**
- 0.0-0.3: Low bias (good)
- 0.3-0.5: Medium bias (needs attention)
- 0.5-0.7: High bias (significant issues)
- 0.7-1.0: Critical bias (urgent action required)

## Recommendations

The system generates specific recommendations for each finding, including:
- Training suggestions
- Process improvements
- Data collection enhancements
- Calibration activities

## Best Practices

1. **Run reports regularly**: Generate bias reports after each evaluation cycle
2. **Review findings systematically**: Address high and critical severity findings first
3. **Track trends**: Compare bias scores across cycles to identify improvements
4. **Act on recommendations**: Implement suggested improvements
5. **Monitor specific targets**: Use target-specific analysis for individuals with concerns

## Integration

The system integrates with:
- `BiasDetector`: Basic bias detection methods
- `AdvancedBiasAlgorithms`: ML-based detection
- `WeightMatrixHandler`: Weight matrix validation
- Database models: `Evaluation`, `Assignment`, `Person`, `Cycle`

## Example Workflow

1. **After evaluation cycle closes**:
   ```python
   report = detector.generate_complete_report(cycle_id)
   ```

2. **Review overall score**:
   ```python
   if report.overall_bias_score > 0.5:
       print("High bias detected - review findings")
   ```

3. **Address critical findings**:
   ```python
   critical = [f for f in report.findings if f.severity == 'critical']
   for finding in critical:
       print(finding.recommendations)
   ```

4. **Check specific targets**:
   ```python
   for target in problematic_targets:
       summary = detector.get_bias_summary_by_target(cycle_id, target)
       if not summary['is_complete_360']:
           print(f"Missing contexts: {summary['missing_contexts']}")
   ```

## Testing

Run tests with:
```bash
pytest tests/test_360_bias_detection.py -v
```

## See Also

- `backend/bias_detection.py`: Basic bias detection methods
- `ai_models/bias_algorithms.py`: Advanced ML algorithms
- `examples/360_bias_detection_example.py`: Usage examples

