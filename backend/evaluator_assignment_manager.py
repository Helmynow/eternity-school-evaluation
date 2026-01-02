"""
Evaluator Assignment Manager
Automatically assigns evaluators when staff members are added or roles change.
Manages the "who evaluates whom" relationships based on staff type (academic/admin).
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from backend.academic_admin_scoring import AcademicAdminScoring
from backend.audit_logger import ActionType as DBActionType
from backend.audit_logger import AuditLogger
from backend.database import Assignment, Cycle, Person, WeightMatrix


class EvaluatorAssignmentManager:
    """
    Manages evaluator assignments for staff members.

    When a staff member is added or their role changes:
    - Automatically determines their staff type (academic vs admin)
    - Creates assignments for all required evaluators based on weight matrix
    - Allows editing assignments when roles change
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.scoring = AcademicAdminScoring(db_session)
        self.audit_logger = AuditLogger(db_session)
        self.logger = logging.getLogger(__name__)

    def get_staff_type(self, person: Person) -> str:
        """Determine if person is academic or admin staff"""
        return self.scoring.get_staff_type(person)

    def get_required_evaluators(self, staff_type: str) -> List[Dict[str, any]]:
        """
        Get list of required evaluators based on staff type.

        Returns list of evaluator configurations with:
        - rater_context: Type of evaluator (CEO, P&C, manager_review, etc.)
        - weight: Weight percentage (0.0 to 1.0)
        - required: Whether this evaluator is required
        - description: Human-readable description
        """
        if staff_type.lower() == "academic":
            return [
                {
                    "rater_context": "manager_review",  # Stage principal
                    "weight": 0.30,
                    "required": True,
                    "description": "Stage Principal (30%)",
                },
                {"rater_context": "P&C", "weight": 0.25, "required": True, "description": "People & Culture (25%)"},
                {"rater_context": "coordinator_hod", "weight": 0.25, "required": True, "description": "Coordinator/HOD (25%)"},
                {"rater_context": "CEO", "weight": 0.15, "required": True, "description": "Director/CEO (15%)"},
                {"rater_context": "self_review", "weight": 0.05, "required": True, "description": "Self Evaluation (5%)"},
                {
                    "rater_context": "peer_review",
                    "weight": 0.0,  # Optional, limit to 2 colleagues
                    "required": False,
                    "description": "Peer Review (up to 2 colleagues)",
                    "max_count": 2,
                },
            ]
        else:  # admin
            return [
                {
                    "rater_context": "manager_review",  # Department head
                    "weight": 0.40,
                    "required": True,
                    "description": "Department Head/Manager (40%)",
                },
                {"rater_context": "P&C", "weight": 0.20, "required": True, "description": "People & Culture (20%)"},
                {
                    "rater_context": "peer_review",
                    "weight": 0.10,
                    "required": True,
                    "description": "Peer Review (10%, up to 2 colleagues)",
                    "max_count": 2,
                },
                {"rater_context": "QA", "weight": 0.10, "required": True, "description": "Quality Assurance (10%)"},
                {"rater_context": "CEO", "weight": 0.15, "required": True, "description": "CEO (15%)"},
                {"rater_context": "self_review", "weight": 0.05, "required": True, "description": "Self Evaluation (5%)"},
            ]

    def find_evaluator_by_context(self, target_person: Person, rater_context: str, cycle_id: int) -> Optional[Person]:
        """
        Find the appropriate evaluator for a given context.

        Args:
            target_person: Person being evaluated
            rater_context: Type of evaluator needed (CEO, P&C, manager_review, etc.)
            cycle_id: Current cycle ID

        Returns:
            Person who should be the evaluator, or None if not found
        """
        if rater_context == "self_review":
            return target_person

        if rater_context == "CEO":
            # Find CEO
            ceo = (
                self.db.query(Person)
                .filter(
                    Person.role_title.ilike("%CEO%")
                    | Person.role_title.ilike("%Director%")
                    | Person.email.ilike("%ceo%")
                    | Person.email.ilike("%director%")
                )
                .first()
            )
            return ceo

        if rater_context == "P&C":
            # Find P&C person
            pnc = (
                self.db.query(Person)
                .filter(
                    Person.role_title.ilike("%P&C%")
                    | Person.role_title.ilike("%People%")
                    | Person.role_title.ilike("%Culture%")
                    | Person.email.ilike("%p.c%")
                    | Person.email.ilike("%people%")
                )
                .first()
            )
            return pnc

        if rater_context == "manager_review":
            # Find manager based on department/role hierarchy
            # For academic: Stage principal
            # For admin: Department head
            staff_type = self.get_staff_type(target_person)

            if staff_type == "academic":
                # Find stage principal (based on department or role)
                manager = (
                    self.db.query(Person)
                    .filter(
                        Person.role_title.ilike("%Principal%")
                        | Person.role_title.ilike("%Stage%")
                        | (Person.department == target_person.department if target_person.department else False)
                    )
                    .first()
                )
            else:  # admin
                # Find department head
                manager = (
                    self.db.query(Person)
                    .filter(
                        Person.role_title.ilike("%Head%")
                        | Person.role_title.ilike("%Manager%")
                        | Person.role_title.ilike("%Director%"),
                        Person.department == target_person.department if target_person.department else True,
                    )
                    .first()
                )
            return manager

        if rater_context == "coordinator_hod":
            # Find Coordinator or HOD
            coordinator = (
                self.db.query(Person)
                .filter(
                    Person.role_title.ilike("%Coordinator%")
                    | Person.role_title.ilike("%HOD%")
                    | Person.role_title.ilike("%Head of Department%"),
                    Person.department == target_person.department if target_person.department else True,
                )
                .first()
            )
            return coordinator

        if rater_context == "QA":
            # Find Quality Assurance person
            qa = (
                self.db.query(Person)
                .filter(
                    Person.role_title.ilike("%QA%")
                    | Person.role_title.ilike("%Quality%")
                    | Person.role_title.ilike("%Assurance%")
                )
                .first()
            )
            return qa

        # For peer_review, we don't auto-assign - user must select peers
        return None

    def create_assignments_for_staff(
        self, target_email: str, cycle_id: int, evaluator_overrides: Optional[Dict[str, str]] = None
    ) -> List[Assignment]:
        """
        Create all required evaluator assignments for a staff member.

        Args:
            target_email: Email of staff member being evaluated
            cycle_id: Evaluation cycle ID
            evaluator_overrides: Optional dict mapping rater_context to evaluator_email

        Returns:
            List of created Assignment objects
        """
        target_person = self.db.query(Person).filter(Person.email == target_email).first()
        if not target_person:
            raise ValueError(f"Person not found: {target_email}")

        staff_type = self.get_staff_type(target_person)
        required_evaluators = self.get_required_evaluators(staff_type)

        created_assignments = []

        for eval_config in required_evaluators:
            rater_context = eval_config["rater_context"]
            weight = eval_config["weight"]

            # Check if override provided
            if evaluator_overrides and rater_context in evaluator_overrides:
                rater_email = evaluator_overrides[rater_context]
                rater_person = self.db.query(Person).filter(Person.email == rater_email).first()
                if not rater_person:
                    self.logger.warning(f"Override evaluator not found: {rater_email}")
                    continue
            else:
                # Auto-find evaluator
                rater_person = self.find_evaluator_by_context(target_person, rater_context, cycle_id)
                if not rater_person:
                    if eval_config.get("required", False):
                        self.logger.warning(f"Required evaluator not found for {target_email}: {rater_context}")
                    continue

            # Skip if assignment already exists
            existing = (
                self.db.query(Assignment)
                .filter(
                    Assignment.cycle_id == cycle_id,
                    Assignment.rater_email == rater_person.email,
                    Assignment.target_email == target_email,
                    Assignment.rater_context == rater_context,
                )
                .first()
            )

            if existing:
                continue

            # Determine target_group
            target_group = "academic" if staff_type == "academic" else "admin"
            if rater_context == "self_review":
                target_group = "self"
            elif rater_context == "peer_review":
                target_group = "peers"

            # Create assignment
            assignment = Assignment(
                cycle_id=cycle_id,
                rater_email=rater_person.email,
                rater_role=rater_person.role_title,
                target_email=target_email,
                target_role=target_person.role_title,
                target_group=target_group,
                rater_context=rater_context,
                weight=weight,
            )

            self.db.add(assignment)
            created_assignments.append(assignment)

        self.db.commit()

        # Audit log
        for assignment in created_assignments:
            self.audit_logger.log_action(
                DBActionType.CREATE,
                "assignment",
                assignment.id,
                "system",  # System-created
                description=f"Created evaluator assignment: {assignment.rater_email} evaluates {assignment.target_email}",
                changes={
                    "rater_context": assignment.rater_context,
                    "weight": assignment.weight,
                    "target_group": assignment.target_group,
                },
            )

        return created_assignments

    def update_assignments_for_staff(
        self, target_email: str, cycle_id: int, updated_assignments: List[Dict[str, any]]
    ) -> List[Assignment]:
        """
        Update evaluator assignments for a staff member.
        Used when roles change or evaluators need to be manually adjusted.

        Args:
            target_email: Email of staff member
            cycle_id: Evaluation cycle ID
            updated_assignments: List of assignment updates with:
                - id: Assignment ID (if updating existing)
                - rater_email: Email of evaluator
                - rater_context: Type of evaluator
                - weight: Weight percentage
                - action: 'create', 'update', or 'delete'

        Returns:
            List of updated/created Assignment objects
        """
        target_person = self.db.query(Person).filter(Person.email == target_email).first()
        if not target_person:
            raise ValueError(f"Person not found: {target_email}")

        staff_type = self.get_staff_type(target_person)
        result_assignments = []

        for assignment_data in updated_assignments:
            action = assignment_data.get("action", "update")
            assignment_id = assignment_data.get("id")

            if action == "delete":
                if assignment_id:
                    assignment = (
                        self.db.query(Assignment)
                        .filter(
                            Assignment.id == assignment_id,
                            Assignment.target_email == target_email,
                            Assignment.cycle_id == cycle_id,
                        )
                        .first()
                    )
                    if assignment:
                        self.audit_logger.log_action(
                            DBActionType.DELETE,
                            "assignment",
                            assignment.id,
                            "system",
                            description=f"Deleted evaluator assignment: {assignment.rater_email} evaluates {assignment.target_email}",
                        )
                        self.db.delete(assignment)
                continue

            rater_email = assignment_data.get("rater_email")
            rater_context = assignment_data.get("rater_context")
            weight = assignment_data.get("weight", 0.0)

            if not rater_email or not rater_context:
                continue

            # Verify rater exists
            rater_person = self.db.query(Person).filter(Person.email == rater_email).first()
            if not rater_person:
                self.logger.warning(f"Rater not found: {rater_email}")
                continue

            target_group = "academic" if staff_type == "academic" else "admin"
            if rater_context == "self_review":
                target_group = "self"
            elif rater_context == "peer_review":
                target_group = "peers"

            if action == "create" or not assignment_id:
                # Create new assignment
                assignment = Assignment(
                    cycle_id=cycle_id,
                    rater_email=rater_email,
                    rater_role=rater_person.role_title,
                    target_email=target_email,
                    target_role=target_person.role_title,
                    target_group=target_group,
                    rater_context=rater_context,
                    weight=weight,
                )
                self.db.add(assignment)
                result_assignments.append(assignment)
            else:
                # Update existing assignment
                assignment = (
                    self.db.query(Assignment)
                    .filter(
                        Assignment.id == assignment_id,
                        Assignment.target_email == target_email,
                        Assignment.cycle_id == cycle_id,
                    )
                    .first()
                )
                if assignment:
                    assignment.rater_email = rater_email
                    assignment.rater_role = rater_person.role_title
                    assignment.rater_context = rater_context
                    assignment.weight = weight
                    assignment.target_group = target_group
                    assignment.updated_at = datetime.utcnow()
                    result_assignments.append(assignment)

        self.db.commit()

        # Audit log
        for assignment in result_assignments:
            self.audit_logger.log_action(
                DBActionType.UPDATE if assignment.id else DBActionType.CREATE,
                "assignment",
                assignment.id,
                "system",
                description=f"Updated evaluator assignment: {assignment.rater_email} evaluates {assignment.target_email}",
                changes={"rater_context": assignment.rater_context, "weight": assignment.weight},
            )

        return result_assignments

    def get_assignments_for_staff(self, target_email: str, cycle_id: Optional[int] = None) -> List[Assignment]:
        """
        Get all evaluator assignments for a staff member.

        Args:
            target_email: Email of staff member
            cycle_id: Optional cycle ID filter

        Returns:
            List of Assignment objects
        """
        query = self.db.query(Assignment).filter(Assignment.target_email == target_email)

        if cycle_id:
            query = query.filter(Assignment.cycle_id == cycle_id)

        return query.order_by(Assignment.rater_context, Assignment.created_at).all()

    def get_evaluation_matrix(self, cycle_id: int) -> Dict[str, List[Dict]]:
        """
        Get complete evaluation matrix showing who evaluates whom.

        Returns:
            Dictionary with:
            - targets: List of people being evaluated
            - assignments: List of all assignments with rater/target info
            - matrix: Matrix view of assignments
        """
        assignments = self.db.query(Assignment).filter(Assignment.cycle_id == cycle_id).all()

        targets = {}
        raters = {}

        for assignment in assignments:
            # Get target info
            if assignment.target_email not in targets:
                target_person = self.db.query(Person).filter(Person.email == assignment.target_email).first()
                targets[assignment.target_email] = {
                    "email": assignment.target_email,
                    "name": target_person.full_name if target_person else assignment.target_email,
                    "role": assignment.target_role,
                    "department": target_person.department if target_person else None,
                    "staff_type": self.get_staff_type(target_person) if target_person else "unknown",
                    "evaluators": [],
                }

            # Get rater info
            if assignment.rater_email not in raters:
                rater_person = self.db.query(Person).filter(Person.email == assignment.rater_email).first()
                raters[assignment.rater_email] = {
                    "email": assignment.rater_email,
                    "name": rater_person.full_name if rater_person else assignment.rater_email,
                    "role": assignment.rater_role,
                }

            # Add to target's evaluators
            targets[assignment.target_email]["evaluators"].append(
                {
                    "assignment_id": assignment.id,
                    "rater_email": assignment.rater_email,
                    "rater_name": raters[assignment.rater_email]["name"],
                    "rater_context": assignment.rater_context,
                    "weight": assignment.weight,
                    "target_group": assignment.target_group,
                }
            )

        return {
            "cycle_id": cycle_id,
            "targets": list(targets.values()),
            "assignments": [
                {
                    "id": a.id,
                    "rater_email": a.rater_email,
                    "rater_name": raters.get(a.rater_email, {}).get("name", a.rater_email),
                    "target_email": a.target_email,
                    "target_name": targets.get(a.target_email, {}).get("name", a.target_email),
                    "rater_context": a.rater_context,
                    "weight": a.weight,
                    "target_group": a.target_group,
                }
                for a in assignments
            ],
            "summary": {"total_assignments": len(assignments), "total_targets": len(targets), "total_raters": len(raters)},
        }
