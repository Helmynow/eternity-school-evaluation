# Context-Aware 360-Degree Bias Detection System

## Overview

The Context-Aware 360-Degree Bias Detection System provides comprehensive bias detection specifically designed for multi-rater 360-degree feedback evaluations. It analyzes bias patterns across different rater contexts (peer, manager, direct report, self, CEO, P&C, QA) and provides context-specific insights.

## Key Features

### 1. Context-Specific Bias Detection

Analyzes bias within each rater context:
- **Centrality Bias**: Raters avoiding extreme ratings
- **Harshness/Leniency Bias**: Context-specific rating tendencies
- **Halo Effect**: Low variance in ratings within a context
- **Context Statistics**: Mean, std, min, max per context

### 2. Cross-Context Comparison

Compares ratings across different contexts:
- **Statistical Significance**: t-tests between context pairs
- **Effect Size**: Cohen's d calculation
- **Mean Differences**: Quantified differences between contexts
- **Bias Indication**: Levels (none, low, medium, high)

### 3. Context Consistency Analysis

Analyzes consistency for same targets across contexts:
- **Coefficient of Variation**: Measures consistency
- **Inconsistent Targets**: Identifies targets with high variation
- **Context Means Comparison**: Per-target analysis

### 4. Context-Specific Patterns

Detects specific patterns:
- **Hierarchy Bias**: Higher hierarchy contexts rate higher
- **Self-Review Inflation**: Self-ratings significantly higher
- **Role-Based Patterns**: Manager vs peer differences

### 5. Multi-Context Statistical Analysis

Advanced statistical analysis:
- **ANOVA**: Tests differences across all contexts
- **Effect Size**: Eta-squared calculation
- **Pairwise Comparisons**: All context pairs analyzed

### 6. Context Balance and Coverage

Validates 360-degree completeness:
- **Context Coverage**: Evaluations per context
- **Missing Contexts**: Identifies missing required contexts
- **Balance Analysis**: Distribution across contexts
- **Minimum Requirements**: Validates minimum evaluations per context

## Rater Contexts

### Standard Contexts

- **peer_review**: Peer evaluations
- **manager_review**: Manager/supervisor evaluations
- **direct_report_review**: Direct report evaluations
- **self_review**: Self-evaluations
- **CEO**: CEO evaluations
- **P&C**: People & Culture evaluations
- **QA**: Quality Assurance evaluations
- **360_review**: Comprehensive 360-degree reviews

### Required Contexts for Complete 360

- peer_review (minimum 2 evaluations)
- manager_review (minimum 1 evaluation)
- direct_report_review (minimum 1 evaluation)
- self_review (minimum 1 evaluation)

## Usage Examples

### Generate Context-Aware Report

```python
from backend.context_aware_bias_detection import ContextAware360BiasDetection

detector = ContextAware360BiasDetection(db_session)

report = detector.generate_context_aware_report(cycle_id=1)

print(f"Overall Bias Score: {report['overall_bias_score']}")
print(f"Context Bias Scores: {report['context_bias_scores']}")
print(f"Total Findings: {report['total_findings']}")
```

### Get Target Context Analysis

```python
analysis = detector.get_target_context_analysis(
    cycle_id=1,
    target_email='teacher1@eternity.edu'
)

print(f"Context Ratings: {analysis['context_ratings']}")
print(f"Consistency: {analysis['consistency']}")
print(f"Missing Contexts: {analysis['missing_contexts']}")
print(f"Is Complete 360: {analysis['is_complete_360']}")
```

### Access Cross-Context Comparisons

```python
report = detector.generate_context_aware_report(cycle_id=1)

for comparison in report['cross_context_analyses']:
    print(f"{comparison['context_pair'][0]} vs {comparison['context_pair'][1]}")
    print(f"  Mean Difference: {comparison['mean_difference']:.2f}")
    print(f"  Statistical Significance: {comparison['statistical_significance']}")
    print(f"  Effect Size: {comparison['effect_size']:.3f}")
    print(f"  Bias Indication: {comparison['bias_indication']}")
```

## API Endpoints

### Context-Aware Report Generation

- `POST /api/v2/bias/360/context-aware-report/{cycle_id}`: Generate comprehensive context-aware report

### Target Analysis

- `GET /api/v2/bias/360/context-analysis/{cycle_id}/target/{email}`: Get target-specific context analysis

### Context Comparison

- `GET /api/v2/bias/360/context-comparison/{cycle_id}`: Get all context comparisons
- `GET /api/v2/bias/360/context-comparison/{cycle_id}?context1=X&context2=Y`: Compare specific contexts

### Context Coverage

- `GET /api/v2/bias/360/context-coverage/{cycle_id}`: Get context coverage analysis

## Report Structure

### Overall Report

```json
{
  "cycle_id": 1,
  "overall_bias_score": 0.45,
  "context_bias_scores": {
    "peer_review": 0.3,
    "manager_review": 0.6,
    "direct_report_review": 0.2,
    "self_review": 0.5
  },
  "total_findings": 8,
  "context_specific_findings": 4,
  "cross_context_findings": 4,
  "findings": [...],
  "context_findings": [...],
  "cross_context_analyses": [...],
  "context_coverage": {...},
  "statistical_summary": {...},
  "recommendations": [...]
}
```

### Cross-Context Analysis

```json
{
  "context_pair": ["peer_review", "manager_review"],
  "mean_difference": 0.5,
  "statistical_significance": true,
  "p_value": 0.023,
  "effect_size": 0.65,
  "interpretation": "medium effect",
  "bias_indication": "medium"
}
```

### Target Context Analysis

```json
{
  "target_email": "teacher1@eternity.edu",
  "status": "analyzed",
  "context_ratings": {
    "peer_review": {
      "count": 3,
      "mean": 4.1,
      "std": 0.3,
      "min": 3.8,
      "max": 4.5
    },
    "manager_review": {
      "count": 1,
      "mean": 3.5,
      "std": 0.0,
      "min": 3.5,
      "max": 3.5
    }
  },
  "missing_contexts": ["direct_report_review", "self_review"],
  "is_complete_360": false,
  "consistency": {
    "coefficient_of_variation": 0.15,
    "interpretation": "high"
  }
}
```

## Bias Types Detected

### Context-Specific

1. **Centrality Bias**: Raters avoiding extreme ratings
2. **Harshness Bias**: Consistently rating lower
3. **Leniency Bias**: Consistently rating higher
4. **Halo Effect**: Low variance in ratings

### Cross-Context

1. **Context Inconsistency**: High variation across contexts for same targets
2. **Hierarchy Bias**: Higher hierarchy contexts rate higher
3. **Self-Review Inflation**: Self-ratings significantly higher
4. **Multi-Context Statistical Difference**: Significant differences across contexts

### Structural

1. **Missing Required Contexts**: Incomplete 360-degree coverage
2. **Insufficient Context Coverage**: Not enough evaluations per context
3. **Context Imbalance**: Uneven distribution across contexts

## Statistical Methods

### T-Test
- Compares means between two contexts
- Calculates p-value for significance
- Used for pairwise context comparisons

### ANOVA
- Tests differences across all contexts
- Calculates F-statistic and p-value
- Identifies if any context differs significantly

### Effect Size
- **Cohen's d**: For pairwise comparisons
- **Eta-squared (η²)**: For multi-context analysis
- Interprets practical significance

### Coefficient of Variation (CV)
- Measures consistency across contexts
- CV < 0.2: High consistency
- CV 0.2-0.4: Medium consistency
- CV > 0.4: Low consistency

## Recommendations

The system provides context-aware recommendations:

1. **Context-Specific Training**: Targeted training for contexts showing bias
2. **Calibration Sessions**: Cross-context calibration to improve consistency
3. **Coverage Improvement**: Ensure complete 360-degree coverage
4. **Pattern-Specific Actions**: Address hierarchy bias, self-inflation, etc.

## Best Practices

1. **Complete 360 Coverage**: Ensure all required contexts are represented
2. **Adequate Evaluations**: Meet minimum evaluation requirements per context
3. **Balance**: Distribute evaluations evenly across contexts
4. **Regular Monitoring**: Run context-aware reports regularly
5. **Action on Findings**: Address identified biases promptly
6. **Calibration**: Conduct cross-context calibration sessions

## Integration

The system integrates with:
- `Complete360BiasDetection`: Uses existing bias detection methods
- `BiasDetector`: Leverages base bias detection algorithms
- Database models: Uses Assignment and Evaluation models
- FastAPI: Provides RESTful API endpoints

## Performance

- **Optimized Queries**: Single join query for data loading
- **Vectorized Calculations**: NumPy for efficient statistical analysis
- **Efficient Grouping**: Dictionary-based grouping for context analysis
- **Scalable**: Handles large evaluation cycles efficiently

