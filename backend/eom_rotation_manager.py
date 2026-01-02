"""
EOM Rotation Rule Manager
Provides high-level interface for managing rotation rules and checking eligibility.
"""

import logging
from datetime import date
from typing import Dict, List, Optional

from backend.database import Cycle, EOMCategory, EOMCycle, EOMNominee, EOMRotationRule, EOMWinner
from backend.eom_validation import EOMNominationValidator, RotationPeriodType


class EOMRotationManager:
    """
    High-level manager for EOM rotation rules.
    Provides convenient methods for rule management and eligibility checking.
    """

    def __init__(self, db_session):
        self.db = db_session
        self.validator = EOMNominationValidator(db_session)
        self.logger = logging.getLogger(__name__)

    def setup_default_rules(self, cycle_id: int, categories: Optional[List[EOMCategory]] = None) -> List[EOMRotationRule]:
        """
        Set up default rotation rules for a cycle.

        Args:
            cycle_id: Cycle ID
            categories: List of categories to create rules for (all if None)

        Returns:
            List of created rotation rules
        """
        if categories is None:
            categories = list(EOMCategory)

        created_rules = []

        for category in categories:
            # Check if rule already exists
            existing = (
                self.db.query(EOMRotationRule)
                .filter(EOMRotationRule.category == category, EOMRotationRule.cycle_id == cycle_id)
                .first()
            )

            if existing:
                self.logger.info(f"Rule already exists for {category.value} in cycle {cycle_id}")
                continue

            rule = self.validator.create_rotation_rule(
                category=category,
                cycle_id=cycle_id,
                cooldown_period=3,  # 3 periods cooldown
                max_wins_per_period=1,  # 1 win per period
                period_type="year",  # Yearly period
                is_active=True,
            )

            created_rules.append(rule)

        return created_rules

    def get_eligible_nominees(self, eom_cycle_id: int, category: EOMCategory) -> List[Dict]:
        """
        Get list of eligible nominees for a category in an EOM cycle.

        Args:
            eom_cycle_id: EOM cycle ID
            category: Category

        Returns:
            List of eligible nominees with eligibility details
        """
        # Get all active people
        from backend.database import Person

        all_people = self.db.query(Person).filter(Person.active == True).all()

        eligible_nominees = []

        for person in all_people:
            eligibility = self.validator.check_nominee_rotation_eligibility(
                nominee_email=person.email, category=category, eom_cycle_id=eom_cycle_id
            )

            if eligibility["eligible"]:
                eligible_nominees.append(
                    {"email": person.email, "name": person.full_name, "role": person.role_title, "eligibility": eligibility}
                )

        return eligible_nominees

    def get_ineligible_nominees(self, eom_cycle_id: int, category: EOMCategory) -> List[Dict]:
        """
        Get list of ineligible nominees with reasons.

        Args:
            eom_cycle_id: EOM cycle ID
            category: Category

        Returns:
            List of ineligible nominees with reasons
        """
        from backend.database import Person

        all_people = self.db.query(Person).filter(Person.active == True).all()

        ineligible_nominees = []

        for person in all_people:
            eligibility = self.validator.check_nominee_rotation_eligibility(
                nominee_email=person.email, category=category, eom_cycle_id=eom_cycle_id
            )

            if not eligibility["eligible"]:
                ineligible_nominees.append(
                    {
                        "email": person.email,
                        "name": person.full_name,
                        "role": person.role_title,
                        "reason": eligibility.get("reason", "Unknown"),
                        "eligibility": eligibility,
                    }
                )

        return ineligible_nominees

    def update_rotation_eligibility_flags(self, eom_cycle_id: int) -> Dict:
        """
        Update rotation_eligible flags for all nominees based on current rules.

        Args:
            eom_cycle_id: EOM cycle ID

        Returns:
            Dictionary with update statistics
        """
        eom_cycle = self.db.query(EOMCycle).filter(EOMCycle.id == eom_cycle_id).first()

        if not eom_cycle:
            return {"error": f"EOM cycle {eom_cycle_id} not found"}

        # Get all nominees
        nominees = self.db.query(EOMNominee).filter(EOMNominee.eom_cycle_id == eom_cycle_id).all()

        updated_count = 0
        eligible_count = 0
        ineligible_count = 0

        for nominee in nominees:
            eligibility = self.validator.check_nominee_rotation_eligibility(
                nominee_email=nominee.nominee_email, category=nominee.category, eom_cycle_id=eom_cycle_id
            )

            new_eligible_status = eligibility["eligible"]

            if nominee.rotation_eligible != new_eligible_status:
                nominee.rotation_eligible = new_eligible_status
                updated_count += 1

            if new_eligible_status:
                eligible_count += 1
            else:
                ineligible_count += 1

        self.db.commit()

        return {
            "total_nominees": len(nominees),
            "updated_flags": updated_count,
            "eligible": eligible_count,
            "ineligible": ineligible_count,
        }

    def get_rotation_summary(self, cycle_id: int) -> Dict:
        """
        Get comprehensive rotation summary for a cycle.

        Args:
            cycle_id: Cycle ID

        Returns:
            Dictionary with rotation summary
        """
        # Get all rotation rules
        rules = self.validator.get_rotation_rules_for_cycle(cycle_id)

        # Get analytics
        analytics = self.validator.get_rotation_analytics(cycle_id=cycle_id)

        # Get EOM cycles for this cycle
        eom_cycles = self.db.query(EOMCycle).filter(EOMCycle.cycle_id == cycle_id).all()

        summary = {
            "cycle_id": cycle_id,
            "rotation_rules": [
                {
                    "id": rule.id,
                    "category": rule.category.value,
                    "cooldown_period": rule.cooldown_period,
                    "max_wins_per_period": rule.max_wins_per_period,
                    "period_type": rule.period_type,
                    "is_active": rule.is_active,
                }
                for rule in rules
            ],
            "analytics": analytics,
            "eom_cycles": [{"id": ec.id, "month": ec.month, "year": ec.year, "status": ec.status} for ec in eom_cycles],
            "total_rules": len(rules),
            "active_rules": len([r for r in rules if r.is_active]),
        }

        return summary
