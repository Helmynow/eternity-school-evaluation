"""
Example usage of EOM Nomination Validator for Eternity School Evaluation System.
"""
from backend.database import Database
from backend.eom_validation import EOMNominationValidator


def main():
    # Initialize database
    db = Database()
    db_session = db.get_session()
    
    # Example: Validate EOM nominations for cycle ID 1
    eom_cycle_id = 1
    
    # Create validator
    validator = EOMNominationValidator(db_session)
    
    # Example 1: Validate a single nomination
    print("=== Example 1: Validate Single Nomination ===")
    result = validator.validate_nomination(
        nominee_email='teacher1@eternity.edu',
        eom_cycle_id=eom_cycle_id,
        nominated_by='principal@eternity.edu',
        category='academic',
        check_attendance=True
    )
    
    print(f"Valid: {result.is_valid}")
    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")
    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"  - {warning}")
    print(f"Details: {result.details}")
    print()
    
    # Example 2: Validate batch nominations
    print("=== Example 2: Validate Batch Nominations ===")
    nominations = [
        {
            'nominee_email': 'teacher1@eternity.edu',
            'nominated_by': 'principal@eternity.edu',
            'category': 'academic'
        },
        {
            'nominee_email': 'admin1@eternity.edu',
            'nominated_by': 'ceo@eternity.edu',
            'category': 'admin'
        },
        {
            'nominee_email': 'teacher2@eternity.edu',
            'nominated_by': 'principal@eternity.edu',
            'category': 'academic'  # This should fail - leader can only nominate once per category
        }
    ]
    
    batch_results = validator.validate_batch_nominations(nominations, eom_cycle_id)
    
    for nominee_email, result in batch_results.items():
        print(f"\n{nominee_email}:")
        print(f"  Valid: {result.is_valid}")
        if result.errors:
            print(f"  Errors: {len(result.errors)}")
        if result.warnings:
            print(f"  Warnings: {len(result.warnings)}")
    print()
    
    # Example 3: Get validation summary
    print("=== Example 3: Validation Summary ===")
    summary = validator.get_validation_summary(eom_cycle_id)
    print(f"Total Nominations: {summary['total_nominations']}")
    print(f"Valid: {summary['valid_nominations']}")
    print(f"Invalid: {summary['invalid_nominations']}")
    print(f"Validation Rate: {summary['validation_rate']:.1%}")
    print(f"\nBy Category: {summary['by_category']}")
    print(f"\nBy Nominator: {summary['by_nominator']}")
    print()
    
    # Example 4: Check specific validation rules
    print("=== Example 4: Specific Validation Checks ===")
    
    # Check rotation rules
    rotation = validator._check_rotation_rules(
        'teacher1@eternity.edu',
        '2024-Q1',
        'academic'
    )
    print(f"Rotation Check: {rotation['is_valid']}")
    if not rotation['is_valid']:
        print(f"  Errors: {rotation['errors']}")
    print()
    
    # Check duplicate nominations
    duplicate = validator._check_duplicate_nominations(
        'teacher1@eternity.edu',
        eom_cycle_id,
        'academic'
    )
    print(f"Duplicate Check: {duplicate['is_valid']}")
    if not duplicate['is_valid']:
        print(f"  Errors: {duplicate['errors']}")
    print()
    
    # Check leader nomination limit
    leader_limit = validator._check_leader_nomination_limit(
        'principal@eternity.edu',
        eom_cycle_id,
        'academic'
    )
    print(f"Leader Limit Check: {leader_limit['is_valid']}")
    print(f"  Is Leader: {leader_limit.get('is_leader', False)}")
    if not leader_limit['is_valid']:
        print(f"  Errors: {leader_limit['errors']}")
    print()
    
    # Clean up
    db_session.close()


if __name__ == '__main__':
    main()

