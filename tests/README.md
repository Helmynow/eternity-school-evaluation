# Test Suite Documentation

This directory contains comprehensive unit tests for the Eternity School Evaluation & Recognition System.

## Test Files

### Core Bias Detection Tests

#### `test_bias_detection.py`
Basic tests for bias detection algorithms:
- Centrality bias detection
- Harshness bias detection
- Similarity bias detection
- Weighted score calculation
- Comprehensive bias report generation
- Insufficient data handling

#### `test_bias_detection_comprehensive.py`
**Comprehensive test suite with detailed scenarios:**

**Recency Bias Tests:**
- `test_positive_recency_bias`: Detects when later submissions have higher ratings
- `test_negative_recency_bias`: Detects when later submissions have lower ratings
- `test_no_recency_bias`: Verifies no bias when ratings are random
- `test_insufficient_data_recency`: Handles insufficient data gracefully
- `test_no_cycle_dates`: Handles missing cycle date information

**Role Bias Tests:**
- `test_role_bias_with_statistical_significance`: Detects statistically significant role-based differences
- `test_role_bias_insufficient_data`: Handles insufficient data

**Similarity Bias Tests:**
- `test_halo_effect_detection`: Detects when raters give very similar scores (halo effect)
- `test_inter_rater_similarity`: Detects when multiple raters give similar scores to same target

**Centrality Bias Tests:**
- `test_strong_centrality_bias`: Detects when ratings cluster around middle values
- `test_no_centrality_bias`: Verifies normal distribution detection

**Harshness Bias Tests:**
- `test_harsh_rater_detection`: Identifies raters who consistently rate lower
- `test_lenient_rater_detection`: Identifies raters who consistently rate higher

**Weighted Score Calculation Tests:**
- `test_calculate_weighted_score_basic`: Basic weighted score calculation
- `test_calculate_weighted_score_missing_weights`: Handles missing weights gracefully
- `test_calculate_weighted_score_empty_scores`: Handles empty input
- `test_calculate_weighted_score_zero_total_weight`: Handles zero weight edge case
- `test_calculate_weighted_score_by_assignment`: Tests assignment-based calculation
- `test_calculate_weighted_score_by_assignment_no_data`: Handles missing data

**Comprehensive Report Tests:**
- `test_comprehensive_bias_report_structure`: Verifies report contains all components

**Edge Cases:**
- `test_gender_bias_insufficient_data`: Handles insufficient data for gender bias
- `test_similarity_bias_insufficient_data`: Handles insufficient data
- `test_similarity_bias_no_data`: Handles missing assignment data
- `test_role_bias_no_statistical_test`: Handles cases where statistical test can't be performed

### Weight Matrix Tests

#### `test_weight_matrix_handler.py`
Basic tests for weight matrix handler:
- Weight retrieval
- Loading evaluations
- Final score calculation
- Validation
- Weight matrix updates
- Evaluation summary

#### `test_weight_calculation_edge_cases.py`
**Edge case tests for weight calculations:**

**WeightMatrixHandler Edge Cases:**
- `test_get_weight_unknown_combinations`: Handles unknown target groups/contexts
- `test_get_weight_case_insensitive`: Verifies case-insensitive matching
- `test_load_evaluations_empty`: Handles empty evaluation sets
- `test_load_evaluations_with_null_ratings`: Filters out null ratings
- `test_calculate_final_scores_single_target`: Single target calculation
- `test_calculate_final_scores_empty`: Empty score handling
- `test_validate_evaluations_below_minimum`: Minimum evaluation validation
- `test_validate_evaluations_above_maximum`: Maximum evaluation validation
- `test_validate_evaluations_missing_required_contexts`: Required context validation
- `test_get_evaluation_summary_empty`: Empty summary handling
- `test_update_weight_matrix_new_group`: Adding new target groups
- `test_export_scores_to_dict`: Dictionary export functionality

**BiasDetector Weight Calculation Edge Cases:**
- `test_calculate_weighted_score_single_score`: Single score handling
- `test_calculate_weighted_score_all_same_weights`: Equal weights scenario
- `test_calculate_weighted_score_extreme_weights`: Extreme weight values
- `test_calculate_weighted_score_negative_scores`: Negative score handling
- `test_calculate_weighted_score_very_large_values`: Large value handling
- `test_calculate_weighted_score_many_contexts`: Many contexts scenario

### 360-Degree Bias Detection Tests

#### `test_360_bias_detection.py`
Tests for complete 360-degree bias detection system:
- Complete report generation
- 360-degree completeness checks
- Overall bias score calculation
- Target-specific bias summaries
- Report export functionality

### EOM Validation Tests

#### `test_eom_validation.py`
Tests for Employee of the Month nomination validation:
- Rotation rules validation
- Duplicate nomination checks
- Leader nomination limits
- Attendance validation
- Validation summary generation

### Weight Matrix Tests

#### `test_weight_matrix.py`
Tests for weight matrix calculations and optimization.

## Running Tests

### Run all tests:
```bash
pytest tests/
```

### Run specific test file:
```bash
pytest tests/test_bias_detection_comprehensive.py
```

### Run specific test class:
```bash
pytest tests/test_bias_detection_comprehensive.py::TestRecencyBias
```

### Run specific test:
```bash
pytest tests/test_bias_detection_comprehensive.py::TestRecencyBias::test_positive_recency_bias
```

### Run with coverage:
```bash
pytest tests/ --cov=backend --cov-report=html
```

### Run with verbose output:
```bash
pytest tests/ -v
```

### Run with detailed output:
```bash
pytest tests/ -vv
```

## Test Coverage

The test suite covers:

1. **Bias Detection Algorithms:**
   - Recency bias (positive, negative, none)
   - Role-based bias with statistical tests
   - Similarity bias (halo effect, inter-rater)
   - Centrality bias (strong, none)
   - Harshness/leniency bias
   - Gender bias (structure)

2. **Weight Calculations:**
   - Basic weighted score calculation
   - Edge cases (empty, null, extreme values)
   - Missing weights handling
   - Multiple contexts
   - Assignment-based calculations

3. **Weight Matrix Handler:**
   - Weight retrieval and updates
   - Evaluation loading and filtering
   - Final score calculations
   - Validation (min/max, required contexts)
   - Summary generation
   - Dictionary export

4. **360-Degree Bias Detection:**
   - Complete report generation
   - Structural completeness checks
   - Overall bias scoring
   - Target-specific analysis

5. **EOM Validation:**
   - Rotation rules
   - Duplicate checks
   - Leader limits
   - Attendance validation

## Test Fixtures

Common fixtures used across tests:

- `mock_db_session`: Mock database session
- `sample_cycle`: Sample cycle with dates
- `sample_evaluations`: Sample evaluation data
- `sample_assignments`: Sample assignment data
- `sample_eom_cycle`: Sample EOM cycle
- `sample_person`: Sample person data

## Best Practices

1. **Isolation**: Each test is independent and doesn't rely on other tests
2. **Mocking**: Database queries are mocked to avoid dependencies
3. **Edge Cases**: Comprehensive coverage of edge cases and error conditions
4. **Clear Names**: Test names clearly describe what they're testing
5. **Assertions**: Multiple assertions verify different aspects of results
6. **Fixtures**: Reusable fixtures reduce code duplication

## Adding New Tests

When adding new tests:

1. Follow the existing naming conventions
2. Use appropriate fixtures
3. Mock database queries properly
4. Test both success and failure cases
5. Include edge cases
6. Add docstrings explaining what the test verifies
7. Group related tests in classes

## Continuous Integration

These tests should be run:
- Before committing code
- In CI/CD pipeline
- Before deploying to production
- When refactoring code

