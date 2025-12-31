"""
Example usage of EOM rotation validation system.
Demonstrates rotation rules, validation, and analytics.
"""
from backend.eom_validation import EOMNominationValidator, RotationPeriodType
from backend.eom_rotation_manager import EOMRotationManager
from backend.database import EOMCategory, EOMCycle
from unittest.mock import Mock


def example_basic_validation():
    """Basic nomination validation example"""
    # Mock database session
    mock_db = Mock()
    validator = EOMNominationValidator(mock_db)
    
    # Validate a nomination
    result = validator.validate_nomination(
        nominee_email='teacher1@eternity.edu',
        eom_cycle_id=1,
        nominated_by='manager@eternity.edu',
        category='academic',
        check_attendance=True
    )
    
    print("=" * 60)
    print("NOMINATION VALIDATION RESULT")
    print("=" * 60)
    print(f"Valid: {result.is_valid}")
    print(f"Errors: {result.errors}")
    print(f"Warnings: {result.warnings}")
    print(f"\nDetails:")
    print(f"  Rotation Check: {result.details.get('rotation_check', {})}")
    print(f"  Attendance Check: {result.details.get('attendance_check', {})}")


def example_rotation_rule_management():
    """Example of managing rotation rules"""
    mock_db = Mock()
    validator = EOMNominationValidator(mock_db)
    
    print("\n" + "=" * 60)
    print("ROTATION RULE MANAGEMENT")
    print("=" * 60)
    
    # Create a rotation rule
    rule = validator.create_rotation_rule(
        category=EOMCategory.ACADEMIC,
        cycle_id=1,
        cooldown_period=3,  # 3 periods cooldown
        max_wins_per_period=1,  # Max 1 win per period
        period_type='year',  # Yearly period
        is_active=True
    )
    
    print(f"Created rule: {rule.id}")
    print(f"  Category: {rule.category.value}")
    print(f"  Cooldown: {rule.cooldown_period} periods")
    print(f"  Max wins: {rule.max_wins_per_period} per {rule.period_type}")
    
    # Update rule
    updated_rule = validator.update_rotation_rule(
        rule_id=rule.id,
        cooldown_period=6,  # Increase cooldown
        max_wins_per_period=2  # Allow 2 wins
    )
    
    print(f"\nUpdated rule:")
    print(f"  Cooldown: {updated_rule.cooldown_period} periods")
    print(f"  Max wins: {updated_rule.max_wins_per_period} per {updated_rule.period_type}")


def example_eligibility_check():
    """Example of checking nominee eligibility"""
    mock_db = Mock()
    validator = EOMNominationValidator(mock_db)
    
    print("\n" + "=" * 60)
    print("ELIGIBILITY CHECK")
    print("=" * 60)
    
    eligibility = validator.check_nominee_rotation_eligibility(
        nominee_email='teacher1@eternity.edu',
        category=EOMCategory.ACADEMIC,
        eom_cycle_id=1
    )
    
    print(f"Nominee: teacher1@eternity.edu")
    print(f"Category: {EOMCategory.ACADEMIC.value}")
    print(f"Eligible: {eligibility['eligible']}")
    print(f"Reason: {eligibility.get('reason', 'N/A')}")
    
    if eligibility.get('rule_results'):
        print(f"\nRule Results:")
        for rule_result in eligibility['rule_results']:
            print(f"  Rule {rule_result['rule_id']}:")
            print(f"    Cooldown passed: {rule_result['cooldown_passed']}")
            print(f"    Max wins OK: {rule_result['max_wins_ok']}")
            print(f"    Wins in period: {rule_result['wins_in_period']}/{rule_result['max_wins_allowed']}")


def example_rotation_analytics():
    """Example of rotation analytics"""
    mock_db = Mock()
    validator = EOMNominationValidator(mock_db)
    
    print("\n" + "=" * 60)
    print("ROTATION ANALYTICS")
    print("=" * 60)
    
    analytics = validator.get_rotation_analytics(
        cycle_id=1,
        category=EOMCategory.ACADEMIC
    )
    
    print(f"Total Wins: {analytics['total_wins']}")
    print(f"Unique Winners: {analytics['unique_winners']}")
    print(f"Average Wins per Winner: {analytics['average_wins_per_winner']:.2f}")
    
    print(f"\nWins by Category:")
    for category, count in analytics['wins_by_category'].items():
        print(f"  {category}: {count}")
    
    if analytics.get('repeat_winners'):
        print(f"\nRepeat Winners:")
        for email, count in analytics['repeat_winners'].items():
            print(f"  {email}: {count} wins")
    
    if analytics.get('rotation_compliance'):
        print(f"\nRotation Compliance:")
        for category, stats in analytics['rotation_compliance'].items():
            print(f"  {category}:")
            print(f"    Compliance Rate: {stats['compliance_rate']:.1%}")
            print(f"    Violations: {len(stats['violations'])}")


def example_rotation_manager():
    """Example using the rotation manager"""
    mock_db = Mock()
    manager = EOMRotationManager(mock_db)
    
    print("\n" + "=" * 60)
    print("ROTATION MANAGER")
    print("=" * 60)
    
    # Setup default rules
    rules = manager.setup_default_rules(cycle_id=1)
    print(f"Created {len(rules)} default rotation rules")
    
    # Get eligible nominees
    eligible = manager.get_eligible_nominees(
        eom_cycle_id=1,
        category=EOMCategory.ACADEMIC
    )
    print(f"\nEligible Nominees: {len(eligible)}")
    for nominee in eligible[:5]:  # Show first 5
        print(f"  - {nominee['name']} ({nominee['email']})")
    
    # Get ineligible nominees
    ineligible = manager.get_ineligible_nominees(
        eom_cycle_id=1,
        category=EOMCategory.ACADEMIC
    )
    print(f"\nIneligible Nominees: {len(ineligible)}")
    for nominee in ineligible[:5]:  # Show first 5
        print(f"  - {nominee['name']}: {nominee['reason']}")


def example_nominee_history():
    """Example of getting nominee rotation history"""
    mock_db = Mock()
    validator = EOMNominationValidator(mock_db)
    
    print("\n" + "=" * 60)
    print("NOMINEE ROTATION HISTORY")
    print("=" * 60)
    
    history = validator.get_nominee_rotation_history(
        nominee_email='teacher1@eternity.edu',
        category=EOMCategory.ACADEMIC
    )
    
    print(f"Nominee: {history['nominee_email']}")
    print(f"Category: {history['category']}")
    print(f"Total Nominations: {history['total_nominations']}")
    print(f"Total Wins: {history['total_wins']}")
    print(f"Win Rate: {history['win_rate']:.1%}")
    print(f"Rotation Eligible: {history['rotation_eligible']}")
    print(f"Last Nominated: {history['last_nominated']}")
    print(f"Last Won: {history['last_won']}")
    
    if history.get('current_eligibility'):
        print(f"\nCurrent Eligibility:")
        print(f"  Eligible: {history['current_eligibility']['eligible']}")
        print(f"  Reason: {history['current_eligibility'].get('reason', 'N/A')}")


if __name__ == '__main__':
    print("=" * 60)
    print("EOM ROTATION VALIDATION SYSTEM EXAMPLES")
    print("=" * 60)
    
    example_basic_validation()
    example_rotation_rule_management()
    example_eligibility_check()
    example_rotation_analytics()
    example_rotation_manager()
    example_nominee_history()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)

