"""
Example usage of Academic vs Admin Weighted Scoring System.
Demonstrates specialized scoring for academic and administrative staff.
"""
from backend.academic_admin_scoring import AcademicAdminScoring
from unittest.mock import Mock


def example_weighted_score_calculation():
    """Calculate weighted score for a staff member"""
    mock_db = Mock()
    scorer = AcademicAdminScoring(mock_db)
    
    print("=" * 60)
    print("ACADEMIC VS ADMIN WEIGHTED SCORING SYSTEM")
    print("=" * 60)
    
    print("\n1. Calculate Weighted Score for Academic Staff:")
    print("   - Academic staff: Higher weight on QA (1.0) and peer review (0.9)")
    print("   - Manager review: Full weight (1.0)")
    print("   - P&C: High weight (0.8)")
    
    print("\n2. Calculate Weighted Score for Admin Staff:")
    print("   - Admin staff: Higher weight on P&C (1.0) and manager review (1.0)")
    print("   - QA: Lower weight (0.7)")
    print("   - Peer review: High weight (0.8)")


def example_weight_matrices():
    """Show weight matrices for academic and admin"""
    mock_db = Mock()
    scorer = AcademicAdminScoring(mock_db)
    
    print("\n" + "=" * 60)
    print("WEIGHT MATRICES")
    print("=" * 60)
    
    print("\nAcademic Staff Weight Matrix:")
    for context, weight in scorer.ACADEMIC_WEIGHT_MATRIX.items():
        print(f"  {context:25s}: {weight:.2f}")
    
    print("\nAdmin Staff Weight Matrix:")
    for context, weight in scorer.ADMIN_WEIGHT_MATRIX.items():
        print(f"  {context:25s}: {weight:.2f}")
    
    print("\nKey Differences:")
    print("  - Academic: QA = 1.0 (full weight), P&C = 0.8")
    print("  - Admin: P&C = 1.0 (full weight), QA = 0.7")


def example_batch_scoring():
    """Calculate scores for multiple staff members"""
    mock_db = Mock()
    scorer = AcademicAdminScoring(mock_db)
    
    print("\n" + "=" * 60)
    print("BATCH SCORING")
    print("=" * 60)
    
    print("\nBatch scoring features:")
    print("  - Calculate scores for all academic staff")
    print("  - Calculate scores for all admin staff")
    print("  - Filter by specific emails")
    print("  - Automatic staff type detection")


def example_comparison():
    """Compare academic vs admin scoring"""
    mock_db = Mock()
    scorer = AcademicAdminScoring(mock_db)
    
    print("\n" + "=" * 60)
    print("ACADEMIC VS ADMIN COMPARISON")
    print("=" * 60)
    
    print("\nComparison includes:")
    print("  - Mean scores for academic vs admin")
    print("  - Median scores")
    print("  - Standard deviations")
    print("  - Score differences")
    print("  - Fairness recommendations")


def example_validation():
    """Validate evaluation requirements"""
    mock_db = Mock()
    scorer = AcademicAdminScoring(mock_db)
    
    print("\n" + "=" * 60)
    print("EVALUATION VALIDATION")
    print("=" * 60)
    
    print("\nAcademic Staff Minimum Requirements:")
    for context, min_count in scorer.MIN_EVALUATIONS['academic'].items():
        print(f"  {context:25s}: {min_count}")
    
    print("\nAdmin Staff Minimum Requirements:")
    for context, min_count in scorer.MIN_EVALUATIONS['admin'].items():
        print(f"  {context:25s}: {min_count}")
    
    print("\nKey Differences:")
    print("  - Academic: More QA evaluations (2), More peer reviews (3)")
    print("  - Admin: More P&C evaluations (2)")


def example_score_distribution():
    """Get score distribution"""
    mock_db = Mock()
    scorer = AcademicAdminScoring(mock_db)
    
    print("\n" + "=" * 60)
    print("SCORE DISTRIBUTION")
    print("=" * 60)
    
    print("\nDistribution analysis includes:")
    print("  - Histogram bins (0-1, 1-2, 2-3, 3-4, 4-5, 5+)")
    print("  - Mean, median, std")
    print("  - Min and max scores")
    print("  - Separate distributions for academic and admin")


def example_staff_type_detection():
    """Show staff type detection logic"""
    mock_db = Mock()
    scorer = AcademicAdminScoring(mock_db)
    
    print("\n" + "=" * 60)
    print("STAFF TYPE DETECTION")
    print("=" * 60)
    
    print("\nAcademic Keywords:")
    print("  - teacher, instructor, professor, lecturer, faculty")
    print("  - academic, curriculum, pedagogy, education")
    
    print("\nAdmin Keywords:")
    print("  - admin, administrative, coordinator, manager, director")
    print("  - secretary, assistant, operations, hr, finance, it")
    
    print("\nDetection Logic:")
    print("  1. Check role title for keywords")
    print("  2. Check department for keywords")
    print("  3. Default to 'academic' if unclear")


if __name__ == '__main__':
    print("=" * 60)
    print("ACADEMIC VS ADMIN WEIGHTED SCORING SYSTEM EXAMPLES")
    print("=" * 60)
    
    example_weighted_score_calculation()
    example_weight_matrices()
    example_batch_scoring()
    example_comparison()
    example_validation()
    example_score_distribution()
    example_staff_type_detection()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
    print("\nKey Features:")
    print("  ✓ Separate weight matrices for academic and admin")
    print("  ✓ Context-specific weighting")
    print("  ✓ Automatic staff type detection")
    print("  ✓ Batch scoring capabilities")
    print("  ✓ Comparative analysis")
    print("  ✓ Evaluation validation")
    print("  ✓ Score distribution analysis")

