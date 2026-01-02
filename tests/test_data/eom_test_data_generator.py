"""
Test Data Generator for EOM Nominations
Generates comprehensive test data including valid nominations and various edge cases.
"""

import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from backend.database import (
    Cycle,
    EOMCategory,
    EOMCycle,
    EOMNominee,
    EOMRotationRule,
    EOMVoter,
    EOMWinner,
    Person,
    StaffSegment,
)


@dataclass
class TestNomination:
    """Test nomination data structure"""

    nominee_email: str
    nominated_by: str
    category: str
    nomination_reason: str
    expected_valid: bool
    expected_errors: List[str]
    expected_warnings: List[str]
    description: str
    edge_case_type: str


class EOMTestDataGenerator:
    """
    Generates comprehensive test data for EOM nominations.

    Includes:
    - Valid nominations
    - Rotation rule violations
    - Attendance issues
    - Duplicate nominations
    - Leader limit violations
    - Edge cases and boundary conditions
    """

    def __init__(self):
        self.test_people = []
        self.test_cycles = []
        self.test_eom_cycles = []
        # Many unit tests instantiate a new generator and immediately call
        # get_valid_nominations()/get_nominations_by_type() without generating DB data.
        # Pre-populate the nomination scenarios so those helpers work out of the box.
        self.test_nominations = []
        self.test_winners = []
        self.test_rotation_rules = []
        self.test_nominations = self.generate_test_nominations()

    def generate_test_people(self, db_session) -> List[Person]:
        """Generate test people (staff members)"""
        people_data = [
            # Academic staff
            {
                "email": "teacher1@eternity.edu",
                "name": "John Teacher",
                "role": "Mathematics Teacher",
                "dept": "Academics",
                "segment": StaffSegment.NATIONAL,
            },
            {
                "email": "teacher2@eternity.edu",
                "name": "Jane Instructor",
                "role": "Science Teacher",
                "dept": "Academics",
                "segment": StaffSegment.INTERNATIONAL,
            },
            {
                "email": "teacher3@eternity.edu",
                "name": "Bob Professor",
                "role": "English Teacher",
                "dept": "Academics",
                "segment": StaffSegment.WHOLE_SCHOOL,
            },
            {
                "email": "teacher4@eternity.edu",
                "name": "Alice Lecturer",
                "role": "History Teacher",
                "dept": "Academics",
                "segment": StaffSegment.NATIONAL,
            },
            {
                "email": "teacher5@eternity.edu",
                "name": "Charlie Faculty",
                "role": "Art Teacher",
                "dept": "Academics",
                "segment": StaffSegment.INTERNATIONAL,
            },
            # Admin staff
            {
                "email": "admin1@eternity.edu",
                "name": "David Coordinator",
                "role": "Administrative Coordinator",
                "dept": "Administration",
                "segment": StaffSegment.WHOLE_SCHOOL,
            },
            {
                "email": "admin2@eternity.edu",
                "name": "Eve Manager",
                "role": "Operations Manager",
                "dept": "Administration",
                "segment": StaffSegment.NATIONAL,
            },
            {
                "email": "admin3@eternity.edu",
                "name": "Frank Director",
                "role": "HR Director",
                "dept": "Administration",
                "segment": StaffSegment.INTERNATIONAL,
            },
            {
                "email": "admin4@eternity.edu",
                "name": "Grace Secretary",
                "role": "Executive Secretary",
                "dept": "Administration",
                "segment": StaffSegment.WHOLE_SCHOOL,
            },
            # Leaders (for nomination limits)
            {
                "email": "leader1@eternity.edu",
                "name": "Henry Principal",
                "role": "School Principal",
                "dept": "Leadership",
                "segment": StaffSegment.WHOLE_SCHOOL,
            },
            {
                "email": "leader2@eternity.edu",
                "name": "Iris VP",
                "role": "Vice Principal",
                "dept": "Leadership",
                "segment": StaffSegment.NATIONAL,
            },
            {
                "email": "leader3@eternity.edu",
                "name": "Jack Head",
                "role": "Department Head",
                "dept": "Leadership",
                "segment": StaffSegment.INTERNATIONAL,
            },
            # Support staff
            {
                "email": "support1@eternity.edu",
                "name": "Karen Assistant",
                "role": "Teaching Assistant",
                "dept": "Support",
                "segment": StaffSegment.NATIONAL,
            },
            {
                "email": "support2@eternity.edu",
                "name": "Larry Helper",
                "role": "IT Support",
                "dept": "Support",
                "segment": StaffSegment.INTERNATIONAL,
            },
            # Inactive staff (for edge cases)
            {
                "email": "inactive1@eternity.edu",
                "name": "Inactive Person",
                "role": "Former Teacher",
                "dept": "Academics",
                "segment": StaffSegment.NATIONAL,
                "active": False,
            },
        ]

        people = []
        for data in people_data:
            person = Person(
                email=data["email"],
                full_name=data["name"],
                role_title=data["role"],
                department=data["dept"],
                segment=data["segment"],
                active=data.get("active", True),
                hire_date=date(2020, 1, 1),
            )
            people.append(person)
            db_session.add(person)

        db_session.commit()
        self.test_people = people
        return people

    def generate_test_cycles(self, db_session) -> List[Cycle]:
        """Generate test evaluation cycles"""
        cycles_data = [
            {
                "code": "CYCLE-2024-Q1",
                "name": "2024 Q1 Evaluation",
                "start_date": date(2024, 1, 1),
                "end_date": date(2024, 3, 31),
            },
            {
                "code": "CYCLE-2024-Q2",
                "name": "2024 Q2 Evaluation",
                "start_date": date(2024, 4, 1),
                "end_date": date(2024, 6, 30),
            },
            {
                "code": "CYCLE-2024-Q3",
                "name": "2024 Q3 Evaluation",
                "start_date": date(2024, 7, 1),
                "end_date": date(2024, 9, 30),
            },
            {
                "code": "CYCLE-2024-Q4",
                "name": "2024 Q4 Evaluation",
                "start_date": date(2024, 10, 1),
                "end_date": date(2024, 12, 31),
            },
        ]

        cycles = []
        for data in cycles_data:
            cycle = Cycle(
                code=data["code"], name=data["name"], start_date=data["start_date"], end_date=data["end_date"], status="active"
            )
            cycles.append(cycle)
            db_session.add(cycle)

        db_session.commit()
        self.test_cycles = cycles
        return cycles

    def generate_test_eom_cycles(self, db_session, cycles: List[Cycle]) -> List[EOMCycle]:
        """Generate test EOM cycles"""
        eom_cycles = []

        # Create EOM cycles for each month in 2024
        for month in range(1, 13):
            # Map month to quarter cycle
            if month <= 3:
                cycle = cycles[0]  # Q1
            elif month <= 6:
                cycle = cycles[1]  # Q2
            elif month <= 9:
                cycle = cycles[2]  # Q3
            else:
                cycle = cycles[3]  # Q4

            eom_cycle = EOMCycle(
                cycle_id=cycle.id,
                month=month,
                year=2024,
                status="active" if month <= datetime.now().month else "draft",
                category_rotation={},
            )
            eom_cycles.append(eom_cycle)
            db_session.add(eom_cycle)

        db_session.commit()
        self.test_eom_cycles = eom_cycles
        return eom_cycles

    def generate_test_rotation_rules(self, db_session, cycle_id: int) -> List[EOMRotationRule]:
        """Generate test rotation rules"""
        rules_data = [
            {
                "category": EOMCategory.OUTSTANDING_LEADERSHIP,
                "cooldown_period": 3,  # 3 months cooldown
                "max_wins_per_period": 1,
                "period_type": "quarter",
                "max_nominations_per_year": 2,
            },
            {
                "category": EOMCategory.SERVICE_EXCELLENCE,
                "cooldown_period": 2,  # 2 months cooldown
                "max_wins_per_period": 1,
                "period_type": "quarter",
                "max_nominations_per_year": 2,
            },
            {
                "category": EOMCategory.TEAM_SPIRIT,
                "cooldown_period": 6,  # 6 months cooldown
                "max_wins_per_period": 1,
                "period_type": "year",
                "max_nominations_per_year": 1,
            },
            {
                "category": EOMCategory.INNOVATION,
                "cooldown_period": 1,  # 1 month cooldown
                "max_wins_per_period": 2,
                "period_type": "year",
                "max_nominations_per_year": 3,
            },
        ]

        rules = []
        for data in rules_data:
            rule = EOMRotationRule(
                cycle_id=cycle_id,
                category=data["category"],
                cooldown_period=data["cooldown_period"],
                max_wins_per_period=data["max_wins_per_period"],
                period_type=data["period_type"],
                max_nominations_per_year=data["max_nominations_per_year"],
                is_active=True,
            )
            rules.append(rule)
            db_session.add(rule)

        db_session.commit()
        self.test_rotation_rules = rules
        return rules

    def generate_test_winners(self, db_session, eom_cycles: List[EOMCycle], people: List[Person]) -> List[EOMWinner]:
        """Generate test winners to create rotation scenarios"""
        winners = []

        # Create winners for various scenarios
        # January 2024 - Outstanding Leadership winner
        if len(eom_cycles) > 0:
            winner1 = EOMWinner(
                eom_cycle_id=eom_cycles[0].id,  # January
                winner_email="teacher1@eternity.edu",
                category="outstanding_leadership",
                term="2024-Q1",
                votes_received=15,
                announced_at=date(2024, 1, 31),
            )
            winners.append(winner1)
            db_session.add(winner1)

            # Also add an Innovation win for the same nominee early in the year so that
            # max-wins-per-period scenarios have enough prior wins by April.
            winner1b = EOMWinner(
                eom_cycle_id=eom_cycles[0].id,  # January (additional category)
                winner_email="teacher1@eternity.edu",
                category="innovation",
                term="2024-Q1",
                votes_received=11,
                announced_at=date(2024, 1, 31),
            )
            winners.append(winner1b)
            db_session.add(winner1b)

        # February 2024 - Service Excellence winner
        if len(eom_cycles) > 1:
            winner2 = EOMWinner(
                eom_cycle_id=eom_cycles[1].id,  # February
                winner_email="admin1@eternity.edu",
                category="service_excellence",
                term="2024-Q1",
                votes_received=12,
                announced_at=date(2024, 2, 28),
            )
            winners.append(winner2)
            db_session.add(winner2)

        # March 2024 - Innovation winner (same person as January to test cooldown)
        if len(eom_cycles) > 2:
            winner3 = EOMWinner(
                eom_cycle_id=eom_cycles[2].id,  # March
                winner_email="teacher1@eternity.edu",
                category="innovation",
                term="2024-Q1",
                votes_received=18,
                announced_at=date(2024, 3, 31),
            )
            winners.append(winner3)
            db_session.add(winner3)

        # April 2024 - Outstanding Leadership winner (different person)
        if len(eom_cycles) > 3:
            winner4 = EOMWinner(
                eom_cycle_id=eom_cycles[3].id,  # April
                winner_email="teacher2@eternity.edu",
                category="outstanding_leadership",
                term="2024-Q2",
                votes_received=14,
                announced_at=date(2024, 4, 30),
            )
            winners.append(winner4)
            db_session.add(winner4)

        db_session.commit()
        self.test_winners = winners
        return winners

    def generate_test_nominations(self) -> List[TestNomination]:
        """Generate test nominations with various scenarios"""
        nominations = []

        # ============================================================
        # VALID NOMINATIONS
        # ============================================================

        # 1. Valid first-time nomination
        nominations.append(
            TestNomination(
                nominee_email="teacher3@eternity.edu",
                nominated_by="leader1@eternity.edu",
                category="outstanding_leadership",
                nomination_reason="Excellent teaching performance and student engagement",
                expected_valid=True,
                expected_errors=[],
                expected_warnings=[],
                description="Valid first-time nomination (Outstanding Leadership)",
                edge_case_type="valid",
            )
        )

        # 2. Valid nomination - different category
        nominations.append(
            TestNomination(
                nominee_email="teacher2@eternity.edu",
                nominated_by="leader2@eternity.edu",
                category="innovation",
                nomination_reason="Introduced innovative teaching methods",
                expected_valid=True,
                expected_errors=[],
                expected_warnings=[],
                description="Valid nomination in different category",
                edge_case_type="valid",
            )
        )

        # 3. Valid nomination - admin category
        nominations.append(
            TestNomination(
                nominee_email="admin2@eternity.edu",
                nominated_by="leader1@eternity.edu",
                category="service_excellence",
                nomination_reason="Outstanding administrative support",
                expected_valid=True,
                expected_errors=[],
                expected_warnings=[],
                description="Valid Service Excellence nomination",
                edge_case_type="valid",
            )
        )

        # ============================================================
        # ROTATION RULE VIOLATIONS
        # ============================================================

        # 4. Cooldown period violation - Academic (won in January, trying in February)
        nominations.append(
            TestNomination(
                nominee_email="teacher1@eternity.edu",
                nominated_by="leader1@eternity.edu",
                category="outstanding_leadership",
                nomination_reason="Great work",
                expected_valid=False,
                expected_errors=["Nominee is within cooldown period"],
                expected_warnings=[],
                description="Cooldown period violation - Outstanding Leadership (3 months cooldown)",
                edge_case_type="cooldown_violation",
            )
        )

        # 5. Cooldown period violation - Admin (won in February, trying in March)
        nominations.append(
            TestNomination(
                nominee_email="admin1@eternity.edu",
                nominated_by="leader1@eternity.edu",
                category="service_excellence",
                nomination_reason="Great work",
                expected_valid=False,
                expected_errors=["Nominee is within cooldown period"],
                expected_warnings=[],
                description="Cooldown period violation - Service Excellence (2 months cooldown)",
                edge_case_type="cooldown_violation",
            )
        )

        # 6. Max wins per period violation - Innovation (already won 2 in year)
        nominations.append(
            TestNomination(
                nominee_email="teacher1@eternity.edu",
                nominated_by="leader1@eternity.edu",
                category="innovation",
                nomination_reason="Another innovation",
                expected_valid=False,
                expected_errors=["Maximum wins per period exceeded"],
                expected_warnings=[],
                description="Max wins per period violation - Innovation (max 2 per year)",
                edge_case_type="max_wins_violation",
            )
        )

        # 7. Boundary case - Exactly at cooldown period end
        nominations.append(
            TestNomination(
                nominee_email="teacher1@eternity.edu",
                nominated_by="leader1@eternity.edu",
                category="outstanding_leadership",
                nomination_reason="Great work after cooldown",
                expected_valid=True,  # Should be valid if exactly at cooldown end
                expected_errors=[],
                expected_warnings=[],
                description="Boundary case - Exactly at cooldown period end (April, won in January)",
                edge_case_type="boundary_cooldown",
            )
        )

        # ============================================================
        # DUPLICATE NOMINATIONS
        # ============================================================

        # 8. Duplicate nomination - same cycle, same category
        nominations.append(
            TestNomination(
                nominee_email="teacher3@eternity.edu",
                nominated_by="leader1@eternity.edu",
                category="outstanding_leadership",
                nomination_reason="Duplicate nomination",
                expected_valid=False,
                expected_errors=["Duplicate nomination"],
                expected_warnings=[],
                description="Duplicate nomination in same cycle and category",
                edge_case_type="duplicate",
            )
        )

        # 9. Duplicate nomination - different nominator, same nominee/category
        nominations.append(
            TestNomination(
                nominee_email="teacher3@eternity.edu",
                nominated_by="leader2@eternity.edu",
                category="outstanding_leadership",
                nomination_reason="Another duplicate",
                expected_valid=False,
                expected_errors=["Duplicate nomination"],
                expected_warnings=[],
                description="Duplicate nomination by different nominator",
                edge_case_type="duplicate",
            )
        )

        # ============================================================
        # LEADER LIMIT VIOLATIONS
        # ============================================================

        # 10. Leader nomination limit - same leader, same category
        nominations.append(
            TestNomination(
                nominee_email="teacher4@eternity.edu",
                nominated_by="leader1@eternity.edu",
                category="outstanding_leadership",
                nomination_reason="Second nomination by same leader",
                expected_valid=False,
                expected_errors=["Leader nomination limit exceeded"],
                expected_warnings=[],
                description="Leader limit violation - same leader nominating twice in same category",
                edge_case_type="leader_limit",
            )
        )

        # 11. Leader nomination limit - different category (should be valid)
        nominations.append(
            TestNomination(
                nominee_email="teacher4@eternity.edu",
                nominated_by="leader1@eternity.edu",
                category="innovation",
                nomination_reason="Different category nomination",
                expected_valid=True,
                expected_errors=[],
                expected_warnings=[],
                description="Leader nominating in different category (should be valid)",
                edge_case_type="valid",
            )
        )

        # ============================================================
        # ATTENDANCE ISSUES
        # ============================================================

        # 12. Low attendance - below threshold
        nominations.append(
            TestNomination(
                nominee_email="teacher5@eternity.edu",
                nominated_by="leader1@eternity.edu",
                category="outstanding_leadership",
                nomination_reason="Good work but low attendance",
                expected_valid=False,
                expected_errors=["Attendance below minimum threshold"],
                expected_warnings=[],
                description="Low attendance violation",
                edge_case_type="attendance_issue",
            )
        )

        # ============================================================
        # INVALID DATA
        # ============================================================

        # 13. Non-existent nominee
        nominations.append(
            TestNomination(
                nominee_email="nonexistent@eternity.edu",
                nominated_by="leader1@eternity.edu",
                category="outstanding_leadership",
                nomination_reason="Test",
                expected_valid=False,
                expected_errors=["Nominee not found"],
                expected_warnings=[],
                description="Nonexistent nominee",
                edge_case_type="invalid_data",
            )
        )

        # 14. Inactive nominee
        nominations.append(
            TestNomination(
                nominee_email="inactive1@eternity.edu",
                nominated_by="leader1@eternity.edu",
                category="outstanding_leadership",
                nomination_reason="Test",
                expected_valid=False,
                expected_errors=["Nominee is not active"],
                expected_warnings=[],
                description="Inactive staff member",
                edge_case_type="invalid_data",
            )
        )

        # 15. Self-nomination
        nominations.append(
            TestNomination(
                nominee_email="teacher3@eternity.edu",
                nominated_by="teacher3@eternity.edu",
                category="outstanding_leadership",
                nomination_reason="Self nomination",
                expected_valid=False,
                expected_errors=["Self-nomination not allowed"],
                expected_warnings=[],
                description="Self-nomination violation",
                edge_case_type="self_nomination",
            )
        )

        # 16. Invalid category
        nominations.append(
            TestNomination(
                nominee_email="teacher3@eternity.edu",
                nominated_by="leader1@eternity.edu",
                category="INVALID_CATEGORY",
                nomination_reason="Test",
                expected_valid=False,
                expected_errors=["Invalid category"],
                expected_warnings=[],
                description="Invalid category",
                edge_case_type="invalid_data",
            )
        )

        # ============================================================
        # EDGE CASES - BOUNDARY CONDITIONS
        # ============================================================

        # 17. Exactly at max wins (should be invalid)
        nominations.append(
            TestNomination(
                nominee_email="teacher1@eternity.edu",
                nominated_by="leader1@eternity.edu",
                category="innovation",
                nomination_reason="At max wins",
                expected_valid=False,
                expected_errors=["Maximum wins per period exceeded"],
                expected_warnings=[],
                description="Boundary case - Exactly at max wins per period",
                edge_case_type="boundary_max_wins",
            )
        )

        # 18. One below max wins (should be valid)
        nominations.append(
            TestNomination(
                nominee_email="teacher2@eternity.edu",
                nominated_by="leader1@eternity.edu",
                category="innovation",
                nomination_reason="One below max",
                expected_valid=True,
                expected_errors=[],
                expected_warnings=[],
                description="Boundary case - One below max wins (should be valid)",
                edge_case_type="boundary_valid",
            )
        )

        # 19. Multiple categories for same person (should be valid)
        nominations.append(
            TestNomination(
                nominee_email="teacher3@eternity.edu",
                nominated_by="leader1@eternity.edu",
                category="team_spirit",
                nomination_reason="Great collaboration",
                expected_valid=True,
                expected_errors=[],
                expected_warnings=[],
                description="Multiple categories for same nominee (should be valid)",
                edge_case_type="valid",
            )
        )

        # 20. First nomination after cooldown period
        nominations.append(
            TestNomination(
                nominee_email="teacher1@eternity.edu",
                nominated_by="leader1@eternity.edu",
                category="outstanding_leadership",
                nomination_reason="First nomination after cooldown",
                expected_valid=True,
                expected_errors=[],
                expected_warnings=[],
                description="First nomination after cooldown period ends",
                edge_case_type="valid",
            )
        )

        # ============================================================
        # PERIOD TYPE EDGE CASES
        # ============================================================

        # 21. Year-based period - same year violation
        nominations.append(
            TestNomination(
                nominee_email="admin1@eternity.edu",
                nominated_by="leader1@eternity.edu",
                category="outstanding_leadership",
                nomination_reason="Leadership nomination",
                expected_valid=False,
                expected_errors=["Maximum wins per period exceeded"],
                expected_warnings=[],
                description="Year-based period violation - already won this year",
                edge_case_type="period_violation",
            )
        )

        # 22. Quarter-based period - different quarter (should be valid)
        nominations.append(
            TestNomination(
                nominee_email="teacher1@eternity.edu",
                nominated_by="leader1@eternity.edu",
                category="outstanding_leadership",
                nomination_reason="Different quarter",
                expected_valid=True,
                expected_errors=[],
                expected_warnings=[],
                description="Quarter-based period - different quarter (should be valid)",
                edge_case_type="valid",
            )
        )

        # ============================================================
        # WARNING CASES
        # ============================================================

        # 23. High nomination count (warning)
        nominations.append(
            TestNomination(
                nominee_email="teacher2@eternity.edu",
                nominated_by="leader1@eternity.edu",
                category="outstanding_leadership",
                nomination_reason="High nomination count",
                expected_valid=True,
                expected_errors=[],
                expected_warnings=["High nomination count"],
                description="High nomination count warning",
                edge_case_type="warning",
            )
        )

        # 24. Recent winner (warning but valid)
        nominations.append(
            TestNomination(
                nominee_email="teacher2@eternity.edu",
                nominated_by="leader1@eternity.edu",
                category="innovation",
                nomination_reason="Recent winner",
                expected_valid=True,
                expected_errors=[],
                expected_warnings=["Recent winner in different category"],
                description="Recent winner in different category (warning but valid)",
                edge_case_type="warning",
            )
        )

        self.test_nominations = nominations
        return nominations

    def generate_all_test_data(self, db_session) -> Dict:
        """Generate all test data"""
        # Generate people
        people = self.generate_test_people(db_session)

        # Generate cycles
        cycles = self.generate_test_cycles(db_session)

        # Generate EOM cycles
        eom_cycles = self.generate_test_eom_cycles(db_session, cycles)

        # Generate rotation rules (apply to all cycles so monthly EOM cycles always find rules)
        rotation_rules = []
        if cycles:
            for cycle in cycles:
                rotation_rules.extend(self.generate_test_rotation_rules(db_session, cycle.id))

        # Generate winners
        winners = self.generate_test_winners(db_session, eom_cycles, people)

        # Generate test nominations (data structures, not DB records)
        nominations = self.generate_test_nominations()

        return {
            "people": people,
            "cycles": cycles,
            "eom_cycles": eom_cycles,
            "rotation_rules": rotation_rules,
            "winners": winners,
            "test_nominations": nominations,
        }

    def get_nominations_by_type(self, edge_case_type: str) -> List[TestNomination]:
        """Get nominations filtered by edge case type"""
        return [n for n in self.test_nominations if n.edge_case_type == edge_case_type]

    def get_valid_nominations(self) -> List[TestNomination]:
        """Get all valid nominations"""
        return [n for n in self.test_nominations if n.expected_valid]

    def get_invalid_nominations(self) -> List[TestNomination]:
        """Get all invalid nominations"""
        return [n for n in self.test_nominations if not n.expected_valid]

    def get_nominations_by_category(self, category: str) -> List[TestNomination]:
        """Get nominations filtered by category"""
        return [n for n in self.test_nominations if n.category == category]

    def export_to_dict(self) -> Dict:
        """Export test data to dictionary format"""
        return {
            "people": [
                {
                    "email": p.email,
                    "name": p.full_name,
                    "role": p.role_title,
                    "department": p.department,
                    "segment": p.segment.value if p.segment else None,
                    "active": p.active,
                }
                for p in self.test_people
            ],
            "cycles": [
                {
                    "code": c.code,
                    "name": c.name,
                    "start_date": c.start_date.isoformat() if c.start_date else None,
                    "end_date": c.end_date.isoformat() if c.end_date else None,
                }
                for c in self.test_cycles
            ],
            "eom_cycles": [
                {"id": ec.id, "cycle_id": ec.cycle_id, "month": ec.month, "year": ec.year, "status": ec.status}
                for ec in self.test_eom_cycles
            ],
            "winners": [
                {
                    "eom_cycle_id": w.eom_cycle_id,
                    "winner_email": w.winner_email,
                    "category": w.category,
                    "term": w.term,
                    "announced_at": w.announced_at.isoformat() if w.announced_at else None,
                }
                for w in self.test_winners
            ],
            "test_nominations": [
                {
                    "nominee_email": n.nominee_email,
                    "nominated_by": n.nominated_by,
                    "category": n.category,
                    "nomination_reason": n.nomination_reason,
                    "expected_valid": n.expected_valid,
                    "expected_errors": n.expected_errors,
                    "expected_warnings": n.expected_warnings,
                    "description": n.description,
                    "edge_case_type": n.edge_case_type,
                }
                for n in self.test_nominations
            ],
        }


def create_test_data_summary() -> str:
    """Create a summary of test data scenarios"""
    generator = EOMTestDataGenerator()
    nominations = generator.generate_test_nominations()

    summary = []
    summary.append("=" * 80)
    summary.append("EOM NOMINATION TEST DATA SUMMARY")
    summary.append("=" * 80)
    summary.append("")

    # Group by edge case type
    by_type = {}
    for nom in nominations:
        if nom.edge_case_type not in by_type:
            by_type[nom.edge_case_type] = []
        by_type[nom.edge_case_type].append(nom)

    summary.append(f"Total Test Cases: {len(nominations)}")
    summary.append(f"Valid Cases: {len([n for n in nominations if n.expected_valid])}")
    summary.append(f"Invalid Cases: {len([n for n in nominations if not n.expected_valid])}")
    summary.append("")

    for edge_type, cases in sorted(by_type.items()):
        summary.append(f"\n{edge_type.upper().replace('_', ' ')} ({len(cases)} cases):")
        summary.append("-" * 80)
        for i, case in enumerate(cases, 1):
            status = "✓ VALID" if case.expected_valid else "✗ INVALID"
            summary.append(f"  {i}. {status}: {case.description}")
            if case.expected_errors:
                summary.append(f"     Errors: {', '.join(case.expected_errors)}")
            if case.expected_warnings:
                summary.append(f"     Warnings: {', '.join(case.expected_warnings)}")
            summary.append(f"     Nominee: {case.nominee_email}, Category: {case.category}")
            summary.append("")

    return "\n".join(summary)
