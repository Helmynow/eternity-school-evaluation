"""
Example usage of detect_evaluation_bias with pandas DataFrame.
Demonstrates how to use the comprehensive bias detection method.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backend.bias_detection import BiasDetector
from unittest.mock import Mock


def example_with_dataframe():
    """Example using a pre-loaded DataFrame"""
    # Create mock database session
    mock_db = Mock()
    detector = BiasDetector(mock_db)
    
    # Create sample evaluation data
    np.random.seed(42)
    n_evaluations = 50
    
    # Sample data with various patterns
    data = {
        'rater_id': [f'rater{i % 10}@example.com' for i in range(n_evaluations)],
        'target_id': [f'target{i % 15}@example.com' for i in range(n_evaluations)],
        'score': np.random.normal(3.5, 0.8, n_evaluations).clip(1.0, 5.0),
        'rater_context': ['peer_review', 'manager_review', 'direct_report_review'] * (n_evaluations // 3 + 1),
        'target_group': ['academic', 'admin', 'peers'] * (n_evaluations // 3 + 1),
        'department': ['national', 'international', 'whole_school'] * (n_evaluations // 3 + 1),
        'segment': ['national', 'international', 'whole_school'] * (n_evaluations // 3 + 1),
        'submitted_at': [datetime.now() - timedelta(days=i*2) for i in range(n_evaluations)]
    }
    
    # Add some bias patterns
    # 1. Halo effect for rater0 (low variance)
    data['score'][:5] = 4.0 + np.random.normal(0, 0.1, 5)
    
    # 2. Department bias (national gets higher scores)
    for i in range(n_evaluations):
        if data['department'][i] == 'national':
            data['score'][i] = min(5.0, data['score'][i] + 0.5)
        elif data['department'][i] == 'international':
            data['score'][i] = max(1.0, data['score'][i] - 0.3)
    
    # 3. Recency bias (later submissions rate higher)
    for i in range(n_evaluations):
        days_ago = (datetime.now() - data['submitted_at'][i]).days
        if days_ago < 10:  # Recent
            data['score'][i] = min(5.0, data['score'][i] + 0.3)
    
    df = pd.DataFrame(data)
    
    # Run comprehensive bias detection
    result = detector.detect_evaluation_bias(df)
    
    print("=" * 60)
    print("COMPREHENSIVE BIAS DETECTION REPORT")
    print("=" * 60)
    print(f"\nStatus: {result['status']}")
    print(f"Total Evaluations: {result['total_evaluations']}")
    
    # Similarity Bias
    print("\n" + "-" * 60)
    print("SIMILARITY BIAS (Halo Effect)")
    print("-" * 60)
    sim_bias = result['similarity_bias']
    print(f"Status: {sim_bias['status']}")
    print(f"Raters with Bias: {sim_bias['raters_with_bias']}")
    print(f"Overall Variance: {sim_bias['overall_variance']:.3f}")
    if sim_bias['bias_flags']:
        print("\nBias Flags:")
        for flag in sim_bias['bias_flags'][:3]:  # Show first 3
            print(f"  - {flag['rater_id']}: {flag['bias_type']} (variance: {flag['variance']:.3f}, severity: {flag['severity']})")
    
    # Recency Bias
    print("\n" + "-" * 60)
    print("RECENCY BIAS")
    print("-" * 60)
    rec_bias = result['recency_bias']
    if rec_bias['status'] == 'analyzed':
        print(f"Correlation: {rec_bias['correlation']:.3f}")
        print(f"Interpretation: {rec_bias['interpretation']}")
        print(f"Early Submissions Mean: {rec_bias['early_submissions_mean']:.2f}")
        print(f"Late Submissions Mean: {rec_bias['late_submissions_mean']:.2f}")
        print(f"Mean Difference: {rec_bias['mean_difference']:.2f}")
        print(f"Message: {rec_bias['message']}")
    else:
        print(f"Status: {rec_bias['status']}")
        if 'message' in rec_bias:
            print(f"Message: {rec_bias['message']}")
    
    # Department Bias
    print("\n" + "-" * 60)
    print("DEPARTMENT BIAS")
    print("-" * 60)
    dept_bias = result['department_bias']
    if dept_bias['status'] == 'analyzed':
        print(f"Total Departments: {dept_bias['total_departments']}")
        print(f"Overall Mean: {dept_bias['overall_mean']:.2f}")
        print("\nDepartment Statistics:")
        for dept, stats in dept_bias['departments'].items():
            print(f"  {dept}:")
            print(f"    Count: {stats['count']}")
            print(f"    Mean: {stats['mean']:.2f}")
            print(f"    Std: {stats['std']:.2f}")
        
        if dept_bias['statistical_test']:
            test = dept_bias['statistical_test']
            print(f"\nStatistical Test: {test['test']}")
            print(f"  P-value: {test['p_value']:.4f}")
            print(f"  Significant: {test['significant']}")
            print(f"  Interpretation: {test['interpretation']}")
        
        if dept_bias['significant_deviations']:
            print("\nSignificant Deviations:")
            for dept, dev in dept_bias['significant_deviations'].items():
                print(f"  {dept}: Mean difference = {dev['mean_difference']:.2f}, Severity: {dev['severity']}")
    else:
        print(f"Status: {dept_bias['status']}")
        if 'message' in dept_bias:
            print(f"Message: {dept_bias['message']}")
    
    # Rater Reliability
    print("\n" + "-" * 60)
    print("RATER RELIABILITY")
    print("-" * 60)
    reliability = result['rater_reliability']
    if reliability['status'] == 'analyzed':
        print(f"Total Targets Analyzed: {reliability['total_targets_analyzed']}")
        metrics = reliability['overall_metrics']
        print(f"\nOverall Metrics:")
        print(f"  Average CV: {metrics['average_coefficient_of_variation']:.3f}" if metrics['average_coefficient_of_variation'] else "  Average CV: N/A")
        print(f"  Approximate ICC: {metrics['approximate_icc']:.3f}")
        print(f"  Overall Mean: {metrics['overall_mean']:.2f}")
        
        print(f"\nReliability Distribution:")
        dist = reliability['reliability_distribution']
        print(f"  High: {dist['high']}")
        print(f"  Medium: {dist['medium']}")
        print(f"  Low: {dist['low']}")
        
        print(f"\nInterpretation: {reliability['interpretation']}")
    else:
        print(f"Status: {reliability['status']}")
        if 'message' in reliability:
            print(f"Message: {reliability['message']}")
    
    print("\n" + "=" * 60)
    return result


def example_with_cycle_id():
    """Example loading from database using cycle_id"""
    # This would work with a real database session
    # from backend.database import Database
    # db = Database()
    # detector = BiasDetector(db.session)
    # 
    # # Load evaluations as DataFrame
    # df = detector.load_evaluations_as_dataframe(cycle_id=1)
    # 
    # # Run bias detection
    # result = detector.detect_evaluation_bias(df)
    # 
    # return result
    pass


if __name__ == '__main__':
    print("Running comprehensive bias detection example...")
    result = example_with_dataframe()
    print("\nExample completed successfully!")

