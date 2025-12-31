"""
Example usage of EOM Nomination Test Data Generator.
Demonstrates how to use the test data for validation testing.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import Database
from backend.eom_validation import EOMNominationValidator
from tests.test_data.eom_test_data_generator import EOMTestDataGenerator


def example_generate_test_data():
    """Generate all test data"""
    print("=" * 80)
    print("GENERATING EOM NOMINATION TEST DATA")
    print("=" * 80)
    print()
    
    db = Database()
    session = db.get_session()
    
    try:
        generator = EOMTestDataGenerator()
        test_data = generator.generate_all_test_data(session)
        
        print(f"Generated:")
        print(f"  - {len(test_data['people'])} people")
        print(f"  - {len(test_data['cycles'])} cycles")
        print(f"  - {len(test_data['eom_cycles'])} EOM cycles")
        print(f"  - {len(test_data['rotation_rules'])} rotation rules")
        print(f"  - {len(test_data['winners'])} winners")
        print(f"  - {len(test_data['test_nominations'])} test nominations")
        print()
        
        return test_data
    finally:
        session.close()


def example_test_valid_nomination(test_data):
    """Test a valid nomination"""
    print("=" * 80)
    print("TESTING VALID NOMINATION")
    print("=" * 80)
    print()
    
    db = Database()
    session = db.get_session()
    
    try:
        validator = EOMNominationValidator(session)
        generator = EOMTestDataGenerator()
        
        # Get a valid nomination
        valid_nominations = generator.get_valid_nominations()
        test_nomination = valid_nominations[0]
        
        # Use first EOM cycle
        eom_cycle = test_data['eom_cycles'][0]
        
        print(f"Testing nomination:")
        print(f"  Nominee: {test_nomination.nominee_email}")
        print(f"  Nominated by: {test_nomination.nominated_by}")
        print(f"  Category: {test_nomination.category}")
        print(f"  EOM Cycle: {eom_cycle.month}/{eom_cycle.year}")
        print()
        
        result = validator.validate_nomination(
            nominee_email=test_nomination.nominee_email,
            eom_cycle_id=eom_cycle.id,
            nominated_by=test_nomination.nominated_by,
            category=test_nomination.category
        )
        
        print(f"Result: {'✓ VALID' if result.is_valid else '✗ INVALID'}")
        if result.errors:
            print(f"Errors: {result.errors}")
        if result.warnings:
            print(f"Warnings: {result.warnings}")
        print()
        
    finally:
        session.close()


def example_test_cooldown_violation(test_data):
    """Test cooldown period violation"""
    print("=" * 80)
    print("TESTING COOLDOWN PERIOD VIOLATION")
    print("=" * 80)
    print()
    
    db = Database()
    session = db.get_session()
    
    try:
        validator = EOMNominationValidator(session)
        generator = EOMTestDataGenerator()
        
        # Get cooldown violation case
        cooldown_cases = generator.get_nominations_by_type('cooldown_violation')
        test_nomination = cooldown_cases[0]
        
        # Use February cycle (winner won in January)
        eom_cycle = test_data['eom_cycles'][1]  # February
        
        print(f"Testing cooldown violation:")
        print(f"  Nominee: {test_nomination.nominee_email}")
        print(f"  Category: {test_nomination.category}")
        print(f"  EOM Cycle: {eom_cycle.month}/{eom_cycle.year}")
        print(f"  (Nominee won in January, trying to nominate in February)")
        print()
        
        result = validator.validate_nomination(
            nominee_email=test_nomination.nominee_email,
            eom_cycle_id=eom_cycle.id,
            nominated_by=test_nomination.nominated_by,
            category=test_nomination.category
        )
        
        print(f"Result: {'✓ VALID' if result.is_valid else '✗ INVALID'}")
        if result.errors:
            print(f"Errors: {result.errors}")
        if result.warnings:
            print(f"Warnings: {result.warnings}")
        print()
        
    finally:
        session.close()


def example_test_duplicate_nomination(test_data):
    """Test duplicate nomination"""
    print("=" * 80)
    print("TESTING DUPLICATE NOMINATION")
    print("=" * 80)
    print()
    
    db = Database()
    session = db.get_session()
    
    try:
        validator = EOMNominationValidator(session)
        generator = EOMTestDataGenerator()
        
        # Get a valid nomination first
        valid_nominations = generator.get_valid_nominations()
        first_nomination = valid_nominations[0]
        
        eom_cycle = test_data['eom_cycles'][0]
        
        # Create the first nomination
        from backend.database import EOMNominee
        nominee = EOMNominee(
            eom_cycle_id=eom_cycle.id,
            nominee_email=first_nomination.nominee_email,
            nominated_by=first_nomination.nominated_by,
            category=first_nomination.category,
            nomination_reason=first_nomination.nomination_reason
        )
        session.add(nominee)
        session.commit()
        
        print(f"Created first nomination:")
        print(f"  Nominee: {first_nomination.nominee_email}")
        print(f"  Category: {first_nomination.category}")
        print()
        
        # Try duplicate
        print(f"Attempting duplicate nomination...")
        result = validator.validate_nomination(
            nominee_email=first_nomination.nominee_email,
            eom_cycle_id=eom_cycle.id,
            nominated_by=first_nomination.nominated_by,
            category=first_nomination.category
        )
        
        print(f"Result: {'✓ VALID' if result.is_valid else '✗ INVALID'}")
        if result.errors:
            print(f"Errors: {result.errors}")
        print()
        
        # Cleanup
        session.delete(nominee)
        session.commit()
        
    finally:
        session.close()


def example_test_batch_validation(test_data):
    """Test batch validation"""
    print("=" * 80)
    print("TESTING BATCH VALIDATION")
    print("=" * 80)
    print()
    
    db = Database()
    session = db.get_session()
    
    try:
        validator = EOMNominationValidator(session)
        generator = EOMTestDataGenerator()
        
        eom_cycle = test_data['eom_cycles'][0]
        
        # Get mix of valid and invalid nominations
        valid_noms = generator.get_valid_nominations()[:3]
        invalid_noms = generator.get_invalid_nominations()[:3]
        
        batch = []
        for nom in valid_noms + invalid_noms:
            batch.append({
                'nominee_email': nom.nominee_email,
                'nominated_by': nom.nominated_by,
                'category': nom.category,
                'nomination_reason': nom.nomination_reason
            })
        
        print(f"Validating batch of {len(batch)} nominations:")
        print(f"  - {len(valid_noms)} expected valid")
        print(f"  - {len(invalid_noms)} expected invalid")
        print()
        
        results = validator.validate_batch_nominations(
            nominations=batch,
            eom_cycle_id=eom_cycle.id
        )
        
        valid_count = sum(1 for r in results if r['is_valid'])
        invalid_count = sum(1 for r in results if not r['is_valid'])
        
        print(f"Results:")
        print(f"  - Valid: {valid_count}")
        print(f"  - Invalid: {invalid_count}")
        print()
        
        for i, result in enumerate(results, 1):
            status = "✓" if result['is_valid'] else "✗"
            print(f"  {i}. {status} {result['nominee_email']} - {result['category']}")
            if result.get('errors'):
                print(f"     Errors: {', '.join(result['errors'])}")
        print()
        
    finally:
        session.close()


def example_list_all_test_cases():
    """List all test cases"""
    print("=" * 80)
    print("ALL TEST CASES")
    print("=" * 80)
    print()
    
    generator = EOMTestDataGenerator()
    nominations = generator.generate_test_nominations()
    
    # Group by type
    by_type = {}
    for nom in nominations:
        if nom.edge_case_type not in by_type:
            by_type[nom.edge_case_type] = []
        by_type[nom.edge_case_type].append(nom)
    
    for edge_type, cases in sorted(by_type.items()):
        print(f"\n{edge_type.upper().replace('_', ' ')} ({len(cases)} cases):")
        print("-" * 80)
        for i, case in enumerate(cases, 1):
            status = "✓ VALID" if case.expected_valid else "✗ INVALID"
            print(f"  {i}. {status}: {case.description}")
            print(f"     Nominee: {case.nominee_email}, Category: {case.category}")
            if case.expected_errors:
                print(f"     Expected Errors: {', '.join(case.expected_errors)}")
            if case.expected_warnings:
                print(f"     Expected Warnings: {', '.join(case.expected_warnings)}")
            print()


if __name__ == '__main__':
    print("=" * 80)
    print("EOM NOMINATION TEST DATA EXAMPLES")
    print("=" * 80)
    print()
    
    # Generate test data
    test_data = example_generate_test_data()
    
    # Test valid nomination
    example_test_valid_nomination(test_data)
    
    # Test cooldown violation
    example_test_cooldown_violation(test_data)
    
    # Test duplicate nomination
    example_test_duplicate_nomination(test_data)
    
    # Test batch validation
    example_test_batch_validation(test_data)
    
    # List all test cases
    example_list_all_test_cases()
    
    print("=" * 80)
    print("EXAMPLES COMPLETE")
    print("=" * 80)

