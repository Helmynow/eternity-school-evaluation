"""
Example usage of WeightMatrixHandler for Eternity School Evaluation System.
"""
from backend.database import Database
from backend.weight_matrix_handler import WeightMatrixHandler


def main():
    # Initialize database
    db = Database()
    db_session = db.get_session()
    
    # Example: Process evaluations for cycle ID 1
    cycle_id = 1
    
    # Create handler
    handler = WeightMatrixHandler(cycle_id=cycle_id, db_session=db_session)
    
    # Example 1: Get weight for specific combination
    print("=== Example 1: Get Weight ===")
    weight_academic_ceo = handler.get_weight('academic', 'CEO')
    weight_admin_pc = handler.get_weight('admin', 'P&C')
    print(f"Academic + CEO weight: {weight_academic_ceo}")
    print(f"Admin + P&C weight: {weight_admin_pc}")
    print()
    
    # Example 2: Calculate final weighted scores
    print("=== Example 2: Calculate Final Scores ===")
    final_scores = handler.calculate_final_scores()
    
    for target_email, score_data in final_scores.items():
        print(f"\nTarget: {target_email}")
        print(f"  Group: {score_data['target_group']}")
        print(f"  Evaluations: {score_data['evaluation_count']}")
        print(f"  Weighted Average: {score_data['weighted_average']:.2f}")
        print(f"  Simple Average: {score_data['simple_average']:.2f}")
        print(f"  Total Weight: {score_data['total_weight']:.2f}")
    print()
    
    # Example 3: Validate evaluations
    print("=== Example 3: Validate Evaluations ===")
    validation = handler.validate_evaluations()
    
    if validation.is_valid:
        print("✓ All evaluations are valid!")
    else:
        print("✗ Validation errors found:")
        for error in validation.errors:
            print(f"  - {error}")
    
    if validation.warnings:
        print("\nWarnings:")
        for warning in validation.warnings:
            print(f"  - {warning}")
    print()
    
    # Example 4: Get evaluation summary
    print("=== Example 4: Evaluation Summary ===")
    summary = handler.get_evaluation_summary()
    print(f"Total Evaluations: {summary['total_evaluations']}")
    print(f"Total Targets: {summary['total_targets']}")
    print(f"Total Raters: {summary['total_raters']}")
    print(f"Average Raw Score: {summary['average_raw_score']:.2f}")
    print(f"Average Weighted Score: {summary['average_weighted_score']:.2f}")
    print(f"\nGroup Distribution: {summary['group_distribution']}")
    print(f"Context Distribution: {summary['context_distribution']}")
    print()
    
    # Example 5: Update weight matrix
    print("=== Example 5: Update Weight Matrix ===")
    print("Original weight for Academic + P&C:", handler.get_weight('academic', 'P&C'))
    handler.update_weight_matrix('academic', 'P&C', 0.9)
    print("Updated weight for Academic + P&C:", handler.get_weight('academic', 'P&C'))
    print()
    
    # Example 6: Export complete results
    print("=== Example 6: Export Complete Results ===")
    export_data = handler.export_scores_to_dict()
    print(f"Cycle ID: {export_data['cycle_id']}")
    print(f"Number of targets with scores: {len(export_data['scores'])}")
    print(f"Validation status: {'Valid' if export_data['validation']['is_valid'] else 'Invalid'}")
    print(f"Total evaluations: {export_data['summary']['total_evaluations']}")
    
    # Clean up
    db_session.close()


if __name__ == '__main__':
    main()

