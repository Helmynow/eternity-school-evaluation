"""
Script to populate database with EOM nomination test data.
Run this to set up test data for EOM nomination validation testing.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.database import Database
from tests.test_data.eom_test_data_generator import EOMTestDataGenerator


def main():
    """Populate database with EOM test data"""
    print("=" * 80)
    print("POPULATING EOM NOMINATION TEST DATA")
    print("=" * 80)
    print()

    # Initialize database
    db = Database()
    session = db.get_session()

    try:
        # Generate test data
        generator = EOMTestDataGenerator()
        test_data = generator.generate_all_test_data(session)

        print(f"✓ Generated {len(test_data['people'])} test people")
        print(f"✓ Generated {len(test_data['cycles'])} test cycles")
        print(f"✓ Generated {len(test_data['eom_cycles'])} test EOM cycles")
        print(f"✓ Generated {len(test_data['rotation_rules'])} rotation rules")
        print(f"✓ Generated {len(test_data['winners'])} test winners")
        print(f"✓ Generated {len(test_data['test_nominations'])} test nomination scenarios")
        print()

        # Print summary
        valid_count = len([n for n in test_data["test_nominations"] if n.expected_valid])
        invalid_count = len([n for n in test_data["test_nominations"] if not n.expected_valid])

        print("Test Nomination Scenarios:")
        print(f"  - Valid: {valid_count}")
        print(f"  - Invalid: {invalid_count}")
        print(f"  - Total: {len(test_data['test_nominations'])}")
        print()

        # Export summary
        from tests.test_data.eom_test_data_generator import create_test_data_summary

        summary = create_test_data_summary()
        print(summary)

        print()
        print("=" * 80)
        print("TEST DATA POPULATION COMPLETE")
        print("=" * 80)
        print()
        print("You can now run tests using this test data:")
        print("  pytest tests/test_eom_nomination_data.py -v")
        print()

    except Exception as e:
        print(f"Error populating test data: {e}")
        import traceback

        traceback.print_exc()
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    main()
