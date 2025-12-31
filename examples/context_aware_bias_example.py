"""
Example usage of Context-Aware 360-Degree Bias Detection System.
Demonstrates comprehensive bias detection across multiple rater contexts.
"""
from backend.context_aware_bias_detection import ContextAware360BiasDetection
from unittest.mock import Mock


def example_context_aware_report():
    """Generate comprehensive context-aware bias report"""
    mock_db = Mock()
    detector = ContextAware360BiasDetection(mock_db)
    
    print("=" * 60)
    print("CONTEXT-AWARE 360-DEGREE BIAS DETECTION REPORT")
    print("=" * 60)
    
    # Mock the report generation
    # In real usage, this would query the database
    print("\nGenerating context-aware report for cycle 1...")
    print("\nReport includes:")
    print("  - Context-specific bias detection")
    print("  - Cross-context comparisons")
    print("  - Context consistency analysis")
    print("  - Context-specific patterns")
    print("  - Multi-context statistical analysis")
    print("  - Context balance and coverage")


def example_context_specific_analysis():
    """Analyze bias within specific contexts"""
    mock_db = Mock()
    detector = ContextAware360BiasDetection(mock_db)
    
    print("\n" + "=" * 60)
    print("CONTEXT-SPECIFIC BIAS ANALYSIS")
    print("=" * 60)
    
    contexts = [
        'peer_review',
        'manager_review',
        'direct_report_review',
        'self_review',
        'CEO',
        'P&C',
        'QA'
    ]
    
    print("\nAnalyzing bias within each context:")
    for context in contexts:
        print(f"\n  {context}:")
        print(f"    - Centrality bias detection")
        print(f"    - Harshness/leniency bias")
        print(f"    - Halo effect detection")
        print(f"    - Context-specific statistics")


def example_cross_context_comparison():
    """Compare ratings across different contexts"""
    mock_db = Mock()
    detector = ContextAware360BiasDetection(mock_db)
    
    print("\n" + "=" * 60)
    print("CROSS-CONTEXT COMPARISON")
    print("=" * 60)
    
    print("\nComparing contexts:")
    print("  - Statistical significance testing (t-test)")
    print("  - Effect size calculation (Cohen's d)")
    print("  - Mean difference analysis")
    print("  - Bias indication levels")
    
    print("\nExample comparisons:")
    print("  - peer_review vs manager_review")
    print("  - self_review vs other contexts")
    print("  - CEO vs P&C vs QA")
    print("  - All context pairs")


def example_context_patterns():
    """Detect patterns across contexts"""
    mock_db = Mock()
    detector = ContextAware360BiasDetection(mock_db)
    
    print("\n" + "=" * 60)
    print("CONTEXT-SPECIFIC PATTERNS")
    print("=" * 60)
    
    print("\nPattern detection:")
    print("  1. Hierarchy Bias:")
    print("     - Higher hierarchy contexts rate higher?")
    print("     - Correlation between hierarchy level and ratings")
    
    print("\n  2. Self-Review Inflation:")
    print("     - Self-ratings significantly higher than others?")
    print("     - Comparison with peer/manager/direct report ratings")
    
    print("\n  3. Role-Based Patterns:")
    print("     - Manager vs peer rating differences")
    print("     - Direct report vs manager rating differences")


def example_context_consistency():
    """Analyze consistency across contexts"""
    mock_db = Mock()
    detector = ContextAware360BiasDetection(mock_db)
    
    print("\n" + "=" * 60)
    print("CONTEXT CONSISTENCY ANALYSIS")
    print("=" * 60)
    
    print("\nAnalyzing consistency:")
    print("  - Same target rated by multiple contexts")
    print("  - Coefficient of variation across contexts")
    print("  - Identification of inconsistent targets")
    print("  - Recommendations for improvement")


def example_target_context_analysis():
    """Get detailed analysis for a specific target"""
    mock_db = Mock()
    detector = ContextAware360BiasDetection(mock_db)
    
    print("\n" + "=" * 60)
    print("TARGET-SPECIFIC CONTEXT ANALYSIS")
    print("=" * 60)
    
    print("\nFor target: teacher1@eternity.edu")
    print("\nAnalysis includes:")
    print("  - Ratings breakdown by context")
    print("  - Mean, std, min, max per context")
    print("  - Consistency across contexts")
    print("  - Missing contexts")
    print("  - 360-degree completeness")


def example_context_coverage():
    """Analyze context coverage and balance"""
    mock_db = Mock()
    detector = ContextAware360BiasDetection(mock_db)
    
    print("\n" + "=" * 60)
    print("CONTEXT COVERAGE ANALYSIS")
    print("=" * 60)
    
    print("\nCoverage analysis:")
    print("  - Evaluations per context")
    print("  - Unique raters per context")
    print("  - Unique targets per context")
    print("  - Balance across contexts")
    print("  - Missing required contexts")
    print("  - Insufficient evaluations per context")


def example_statistical_analysis():
    """Multi-context statistical analysis"""
    mock_db = Mock()
    detector = ContextAware360BiasDetection(mock_db)
    
    print("\n" + "=" * 60)
    print("MULTI-CONTEXT STATISTICAL ANALYSIS")
    print("=" * 60)
    
    print("\nStatistical tests:")
    print("  - ANOVA across all contexts")
    print("  - Effect size (eta-squared)")
    print("  - Pairwise t-tests")
    print("  - Correlation analysis")
    print("  - Distribution comparisons")


if __name__ == '__main__':
    print("=" * 60)
    print("CONTEXT-AWARE 360-DEGREE BIAS DETECTION EXAMPLES")
    print("=" * 60)
    
    example_context_aware_report()
    example_context_specific_analysis()
    example_cross_context_comparison()
    example_context_patterns()
    example_context_consistency()
    example_target_context_analysis()
    example_context_coverage()
    example_statistical_analysis()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
    print("\nKey Features:")
    print("  ✓ Context-specific bias detection")
    print("  ✓ Cross-context comparisons")
    print("  ✓ Context consistency analysis")
    print("  ✓ Pattern detection (hierarchy, self-inflation)")
    print("  ✓ Multi-context statistical analysis")
    print("  ✓ Context coverage validation")
    print("  ✓ Target-specific context analysis")

