# Context-Aware 360-Degree Bias Detection - Implementation Summary

## Overview

A comprehensive bias detection system for 360-degree feedback with multiple rater contexts has been implemented. The system provides context-specific analysis, cross-context comparisons, and pattern detection across all rater perspectives.

## Key Components

### 1. Context-Aware Bias Detection (`backend/context_aware_bias_detection.py`)

**`ContextAware360BiasDetection`** - Main class for context-aware analysis:

**Core Methods:**
- `generate_context_aware_report()`: Complete context-aware report
- `get_target_context_analysis()`: Target-specific context analysis
- `_load_context_data()`: Load data grouped by context
- `_analyze_context_specific_bias()`: Bias within each context
- `_analyze_cross_context_comparisons()`: Compare contexts
- `_analyze_context_consistency()`: Consistency across contexts
- `_detect_context_patterns()`: Pattern detection
- `_analyze_context_balance()`: Balance and coverage
- `_multi_context_statistical_analysis()`: Statistical tests
- `_validate_context_coverage()`: Coverage validation

**Data Structures:**
- `ContextBiasFinding`: Context-specific bias finding
- `CrossContextAnalysis`: Cross-context comparison result

### 2. FastAPI Endpoints (`backend/fastapi_app.py`)

**Context-Aware Endpoints:**
- `POST /api/v2/bias/360/context-aware-report/{cycle_id}`: Generate report
- `GET /api/v2/bias/360/context-analysis/{cycle_id}/target/{email}`: Target analysis
- `GET /api/v2/bias/360/context-comparison/{cycle_id}`: Context comparison
- `GET /api/v2/bias/360/context-coverage/{cycle_id}`: Coverage analysis

### 3. Testing (`tests/test_context_aware_bias.py`)

Comprehensive unit tests covering:
- Context data loading
- Context-specific bias detection
- Cross-context comparisons
- Context consistency
- Pattern detection
- Context balance
- Statistical analysis
- Target analysis

### 4. Examples (`examples/context_aware_bias_example.py`)

Usage examples demonstrating:
- Report generation
- Context-specific analysis
- Cross-context comparison
- Pattern detection
- Consistency analysis
- Target analysis
- Coverage analysis

## Features

### Context-Specific Analysis

**Per-Context Bias Detection:**
- Centrality bias (avoiding extremes)
- Harshness bias (consistently low)
- Leniency bias (consistently high)
- Halo effect (low variance)

**Context Statistics:**
- Mean, std, min, max per context
- Unique raters and targets per context
- Evaluation counts per context

### Cross-Context Comparison

**Statistical Comparison:**
- T-tests between context pairs
- Effect size (Cohen's d)
- Mean differences
- P-values and significance

**Bias Indication Levels:**
- None: No significant difference
- Low: Small but significant difference
- Medium: Moderate difference
- High: Large difference

### Context Consistency

**Consistency Metrics:**
- Coefficient of variation across contexts
- Per-target consistency analysis
- Identification of inconsistent targets
- Recommendations for improvement

### Pattern Detection

**Specific Patterns:**
1. **Hierarchy Bias**: Higher hierarchy = higher ratings
2. **Self-Review Inflation**: Self-ratings significantly higher
3. **Role-Based Patterns**: Manager vs peer differences

### Statistical Analysis

**Multi-Context Tests:**
- ANOVA across all contexts
- Effect size (eta-squared)
- Pairwise t-tests
- Correlation analysis

### Coverage Validation

**Completeness Checks:**
- Missing required contexts
- Insufficient evaluations per context
- Context imbalance
- 360-degree completeness

## Rater Contexts Supported

### Standard Contexts
- `peer_review`: Peer evaluations
- `manager_review`: Manager/supervisor evaluations
- `direct_report_review`: Direct report evaluations
- `self_review`: Self-evaluations
- `CEO`: CEO evaluations
- `P&C`: People & Culture evaluations
- `QA`: Quality Assurance evaluations
- `360_review`: Comprehensive reviews

### Context Hierarchy
Used for hierarchy bias detection:
- CEO: 5
- P&C, QA: 4
- manager_review: 3
- peer_review, direct_report_review, 360_review: 2
- self_review: 1

## Report Structure

### Main Report

```python
{
    'cycle_id': int,
    'overall_bias_score': float,  # 0-1
    'context_bias_scores': Dict[str, float],  # Per context
    'total_findings': int,
    'context_specific_findings': int,
    'cross_context_findings': int,
    'findings': List[Dict],  # All findings
    'context_findings': List[Dict],  # Context-specific
    'cross_context_analyses': List[Dict],  # Comparisons
    'context_coverage': Dict,  # Coverage stats
    'statistical_summary': Dict,  # Statistics
    'recommendations': List[str]
}
```

### Cross-Context Analysis

```python
{
    'context_pair': Tuple[str, str],
    'mean_difference': float,
    'statistical_significance': bool,
    'p_value': float,
    'effect_size': float,  # Cohen's d
    'interpretation': str,  # negligible/small/medium/large
    'bias_indication': str  # none/low/medium/high
}
```

## Usage

### Python

```python
from backend.context_aware_bias_detection import ContextAware360BiasDetection

detector = ContextAware360BiasDetection(db_session)

# Generate full report
report = detector.generate_context_aware_report(cycle_id=1)

# Get target analysis
analysis = detector.get_target_context_analysis(
    cycle_id=1,
    target_email='teacher1@eternity.edu'
)
```

### API

```bash
# Generate context-aware report
POST /api/v2/bias/360/context-aware-report/1

# Get target context analysis
GET /api/v2/bias/360/context-analysis/1/target/teacher1@eternity.edu

# Compare contexts
GET /api/v2/bias/360/context-comparison/1?context1=peer_review&context2=manager_review

# Get coverage analysis
GET /api/v2/bias/360/context-coverage/1
```

## Key Advantages

1. **Context-Specific Insights**: Identifies bias within each rater context
2. **Cross-Context Comparison**: Statistical comparison between contexts
3. **Consistency Analysis**: Measures agreement across contexts
4. **Pattern Detection**: Identifies specific bias patterns
5. **Statistical Rigor**: Uses proper statistical tests
6. **Comprehensive Coverage**: Validates 360-degree completeness
7. **Actionable Recommendations**: Context-specific recommendations

## Integration

- **Database**: Uses Assignment and Evaluation models
- **Existing Systems**: Integrates with Complete360BiasDetection
- **Bias Detection**: Uses BiasDetector for base algorithms
- **FastAPI**: Provides RESTful API endpoints
- **Testing**: Comprehensive unit test coverage

## Files Created

- `backend/context_aware_bias_detection.py`: Main implementation
- `examples/context_aware_bias_example.py`: Usage examples
- `tests/test_context_aware_bias.py`: Unit tests
- `docs/CONTEXT_AWARE_BIAS_DETECTION.md`: Documentation
- `docs/CONTEXT_BIAS_DETECTION_SUMMARY.md`: This summary

## Files Modified

- `backend/fastapi_app.py`: Added context-aware endpoints

## Next Steps

1. **Run Reports**: Generate context-aware reports for evaluation cycles
2. **Monitor Patterns**: Track context-specific bias patterns over time
3. **Take Action**: Implement recommendations for identified biases
4. **Calibration**: Conduct cross-context calibration sessions
5. **Coverage**: Ensure complete 360-degree coverage for all targets

