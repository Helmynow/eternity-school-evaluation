"""
Unit tests using generated EOM nomination test data.
Tests various edge cases and validation scenarios.
"""

from datetime import date

import pytest
from sqlalchemy import text

from backend.database import Cycle, Database, EOMCategory, EOMCycle, EOMNominee, EOMWinner, Person
from backend.eom_validation import EOMNominationValidator
from tests.test_data.eom_test_data_generator import EOMTestDataGenerator, TestNomination


@pytest.fixture(scope="module")
def test_db(test_database_url):
    """Create test database session"""
    db = Database(test_database_url)
    try:
        session = db.get_session()
        session.execute(text("SELECT 1"))
    except Exception:
        pytest.skip("Postgres test database not available; set DATABASE_URL or start local Postgres to run these tests")
    yield session
    session.close()


@pytest.fixture(scope="module")
def test_data(test_db):
    """Generate all test data"""
    generator = EOMTestDataGenerator()
    data = generator.generate_all_test_data(test_db)
    return data


class TestValidNominations:
    """Test valid nomination scenarios"""

    def test_valid_first_time_nomination(self, test_db, test_data):
        """Test valid first-time nomination"""
        validator = EOMNominationValidator(test_db)
        generator = EOMTestDataGenerator()

        valid_nominations = generator.get_valid_nominations()
        first_valid = [n for n in valid_nominations if n.edge_case_type == "valid"][0]

        # Use first EOM cycle
        eom_cycle = test_data["eom_cycles"][0]

        result = validator.validate_nomination(
            nominee_email=first_valid.nominee_email,
            eom_cycle_id=eom_cycle.id,
            nominated_by=first_valid.nominated_by,
            category=first_valid.category,
        )

        assert result.is_valid, f"Expected valid but got errors: {result.errors}"
        assert len(result.errors) == 0

    def test_valid_different_category(self, test_db, test_data):
        """Test valid nomination in different category"""
        validator = EOMNominationValidator(test_db)
        generator = EOMTestDataGenerator()

        valid_nominations = generator.get_valid_nominations()
        diff_category = [n for n in valid_nominations if "different category" in n.description.lower()][0]

        eom_cycle = test_data["eom_cycles"][0]

        result = validator.validate_nomination(
            nominee_email=diff_category.nominee_email,
            eom_cycle_id=eom_cycle.id,
            nominated_by=diff_category.nominated_by,
            category=diff_category.category,
        )

        assert result.is_valid, f"Expected valid but got errors: {result.errors}"


class TestRotationRuleViolations:
    """Test rotation rule violation scenarios"""

    def test_cooldown_period_violation(self, test_db, test_data):
        """Test cooldown period violation"""
        validator = EOMNominationValidator(test_db)
        generator = EOMTestDataGenerator()

        cooldown_cases = generator.get_nominations_by_type("cooldown_violation")

        for case in cooldown_cases:
            # Find appropriate EOM cycle (February for January winner)
            eom_cycle = test_data["eom_cycles"][1]  # February

            result = validator.validate_nomination(
                nominee_email=case.nominee_email,
                eom_cycle_id=eom_cycle.id,
                nominated_by=case.nominated_by,
                category=case.category,
            )

            assert not result.is_valid, f"Expected invalid for cooldown violation"
            assert any(
                "cooldown" in error.lower() for error in result.errors
            ), f"Expected cooldown error but got: {result.errors}"

    def test_max_wins_per_period_violation(self, test_db, test_data):
        """Test max wins per period violation"""
        validator = EOMNominationValidator(test_db)
        generator = EOMTestDataGenerator()

        max_wins_cases = generator.get_nominations_by_type("max_wins_violation")

        for case in max_wins_cases:
            eom_cycle = test_data["eom_cycles"][3]  # April

            result = validator.validate_nomination(
                nominee_email=case.nominee_email,
                eom_cycle_id=eom_cycle.id,
                nominated_by=case.nominated_by,
                category=case.category,
            )

            assert not result.is_valid, f"Expected invalid for max wins violation"
            assert any(
                "max" in error.lower() or "period" in error.lower() for error in result.errors
            ), f"Expected max wins error but got: {result.errors}"


class TestDuplicateNominations:
    """Test duplicate nomination scenarios"""

    def test_duplicate_nomination_same_cycle(self, test_db, test_data):
        """Test duplicate nomination in same cycle"""
        validator = EOMNominationValidator(test_db)
        generator = EOMTestDataGenerator()

        # First create a valid nomination
        eom_cycle = test_data["eom_cycles"][0]
        valid_nom = generator.get_valid_nominations()[0]

        # Create the first nomination
        nominee = EOMNominee(
            eom_cycle_id=eom_cycle.id,
            nominee_email=valid_nom.nominee_email,
            nominated_by=valid_nom.nominated_by,
            category=EOMCategory(valid_nom.category),
            nomination_reason=valid_nom.nomination_reason,
        )
        test_db.add(nominee)
        test_db.commit()

        # Try to create duplicate
        duplicate_cases = generator.get_nominations_by_type("duplicate")
        for case in duplicate_cases:
            if case.nominee_email == valid_nom.nominee_email:
                result = validator.validate_nomination(
                    nominee_email=case.nominee_email,
                    eom_cycle_id=eom_cycle.id,
                    nominated_by=case.nominated_by,
                    category=case.category,
                )

                assert not result.is_valid, f"Expected invalid for duplicate"
                assert any(
                    "duplicate" in error.lower() for error in result.errors
                ), f"Expected duplicate error but got: {result.errors}"
                break

        # Cleanup
        test_db.delete(nominee)
        test_db.commit()


class TestLeaderLimitViolations:
    """Test leader nomination limit violations"""

    def test_leader_limit_violation(self, test_db, test_data):
        """Test leader nomination limit"""
        validator = EOMNominationValidator(test_db)
        generator = EOMTestDataGenerator()

        # First create a nomination by leader
        eom_cycle = test_data["eom_cycles"][0]
        valid_nom = generator.get_valid_nominations()[0]

        nominee = EOMNominee(
            eom_cycle_id=eom_cycle.id,
            nominee_email=valid_nom.nominee_email,
            nominated_by=valid_nom.nominated_by,
            category=EOMCategory(valid_nom.category),
            nomination_reason=valid_nom.nomination_reason,
        )
        test_db.add(nominee)
        test_db.commit()

        # Try second nomination by same leader
        leader_limit_cases = generator.get_nominations_by_type("leader_limit")
        for case in leader_limit_cases:
            if case.nominated_by == valid_nom.nominated_by:
                result = validator.validate_nomination(
                    nominee_email=case.nominee_email,
                    eom_cycle_id=eom_cycle.id,
                    nominated_by=case.nominated_by,
                    category=case.category,
                )

                assert not result.is_valid, f"Expected invalid for leader limit"
                assert any(
                    "leader" in error.lower() or "limit" in error.lower() for error in result.errors
                ), f"Expected leader limit error but got: {result.errors}"
                break

        # Cleanup
        test_db.delete(nominee)
        test_db.commit()


class TestInvalidData:
    """Test invalid data scenarios"""

    def test_nonexistent_nominee(self, test_db, test_data):
        """Test nomination of non-existent person"""
        validator = EOMNominationValidator(test_db)
        generator = EOMTestDataGenerator()

        invalid_cases = generator.get_nominations_by_type("invalid_data")
        nonexistent = [c for c in invalid_cases if "nonexistent" in c.description.lower()][0]

        eom_cycle = test_data["eom_cycles"][0]

        result = validator.validate_nomination(
            nominee_email=nonexistent.nominee_email,
            eom_cycle_id=eom_cycle.id,
            nominated_by=nonexistent.nominated_by,
            category=nonexistent.category,
        )

        assert not result.is_valid, f"Expected invalid for nonexistent nominee"
        assert any(
            "not found" in error.lower() or "exist" in error.lower() for error in result.errors
        ), f"Expected not found error but got: {result.errors}"

    def test_inactive_nominee(self, test_db, test_data):
        """Test nomination of inactive person"""
        validator = EOMNominationValidator(test_db)
        generator = EOMTestDataGenerator()

        invalid_cases = generator.get_nominations_by_type("invalid_data")
        inactive = [c for c in invalid_cases if "inactive" in c.description.lower()][0]

        eom_cycle = test_data["eom_cycles"][0]

        result = validator.validate_nomination(
            nominee_email=inactive.nominee_email,
            eom_cycle_id=eom_cycle.id,
            nominated_by=inactive.nominated_by,
            category=inactive.category,
        )

        assert not result.is_valid, f"Expected invalid for inactive nominee"
        assert any("active" in error.lower() for error in result.errors), f"Expected active error but got: {result.errors}"

    def test_self_nomination(self, test_db, test_data):
        """Test self-nomination"""
        validator = EOMNominationValidator(test_db)
        generator = EOMTestDataGenerator()

        self_nom = generator.get_nominations_by_type("self_nomination")[0]
        eom_cycle = test_data["eom_cycles"][0]

        result = validator.validate_nomination(
            nominee_email=self_nom.nominee_email,
            eom_cycle_id=eom_cycle.id,
            nominated_by=self_nom.nominated_by,
            category=self_nom.category,
        )

        assert not result.is_valid, f"Expected invalid for self-nomination"
        assert any(
            "self" in error.lower() for error in result.errors
        ), f"Expected self-nomination error but got: {result.errors}"


class TestBoundaryConditions:
    """Test boundary condition scenarios"""

    def test_boundary_cooldown_period(self, test_db, test_data):
        """Test boundary case at cooldown period end"""
        validator = EOMNominationValidator(test_db)
        generator = EOMTestDataGenerator()

        boundary_cases = generator.get_nominations_by_type("boundary_cooldown")

        for case in boundary_cases:
            # Use April cycle (4 months after January)
            eom_cycle = test_data["eom_cycles"][3]  # April

            result = validator.validate_nomination(
                nominee_email=case.nominee_email,
                eom_cycle_id=eom_cycle.id,
                nominated_by=case.nominated_by,
                category=case.category,
            )

            # Should be valid if exactly at cooldown end
            if case.expected_valid:
                assert result.is_valid, f"Expected valid at boundary but got: {result.errors}"

    def test_boundary_max_wins(self, test_db, test_data):
        """Test boundary case at max wins"""
        validator = EOMNominationValidator(test_db)
        generator = EOMTestDataGenerator()

        boundary_cases = generator.get_nominations_by_type("boundary_max_wins")

        for case in boundary_cases:
            eom_cycle = test_data["eom_cycles"][3]  # April

            result = validator.validate_nomination(
                nominee_email=case.nominee_email,
                eom_cycle_id=eom_cycle.id,
                nominated_by=case.nominated_by,
                category=case.category,
            )

            assert not result.is_valid, f"Expected invalid at max wins boundary"
            assert any("max" in error.lower() for error in result.errors), f"Expected max wins error but got: {result.errors}"


class TestBatchValidation:
    """Test batch validation scenarios"""

    def test_batch_validation_mixed(self, test_db, test_data):
        """Test batch validation with mixed valid/invalid"""
        validator = EOMNominationValidator(test_db)
        generator = EOMTestDataGenerator()

        eom_cycle = test_data["eom_cycles"][0]

        # Get mix of valid and invalid
        valid_noms = generator.get_valid_nominations()[:2]
        invalid_noms = generator.get_invalid_nominations()[:2]

        batch = []
        for nom in valid_noms + invalid_noms:
            batch.append(
                {
                    "nominee_email": nom.nominee_email,
                    "nominated_by": nom.nominated_by,
                    "category": nom.category,
                    "nomination_reason": nom.nomination_reason,
                }
            )

        results = validator.validate_batch_nominations(nominations=batch, eom_cycle_id=eom_cycle.id)

        assert len(results) == len(batch)
        assert any(r.is_valid for r in results.values()), "Should have some valid results"
        assert any(not r.is_valid for r in results.values()), "Should have some invalid results"


if __name__ == "__main__":
    # Generate and print test data summary
    from tests.test_data.eom_test_data_generator import create_test_data_summary

    print(create_test_data_summary())
