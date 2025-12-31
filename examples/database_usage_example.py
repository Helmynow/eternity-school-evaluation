"""
Example usage of the enhanced database models for Eternity School Evaluation System.
"""
from backend.database import (
    Database, Person, Assignment, Evaluation, EOMNominee, EOMCycle,
    WeightMatrix, EOMRotationRule, AuditLog,
    StaffSegment, EOMCategory, ActionType
)
from backend.audit_logger import AuditLogger
from datetime import date, datetime


def main():
    # Initialize database
    db = Database()
    db_session = db.get_session()
    
    # Initialize audit logger
    audit_logger = AuditLogger(db_session)
    
    print("=== Creating Staff Members with Segments ===")
    
    # Create staff members with different segments
    staff1 = Person(
        email="teacher1@eternity.edu",
        full_name="John Doe",
        role_title="Mathematics Teacher",
        department="Academics",
        segment=StaffSegment.NATIONAL,
        active=True,
        hire_date=date(2020, 1, 15)
    )
    
    staff2 = Person(
        email="teacher2@eternity.edu",
        full_name="Jane Smith",
        role_title="English Teacher",
        department="Academics",
        segment=StaffSegment.INTERNATIONAL,
        active=True,
        hire_date=date(2019, 8, 1)
    )
    
    staff3 = Person(
        email="admin1@eternity.edu",
        full_name="Bob Johnson",
        role_title="Administrator",
        department="Administration",
        segment=StaffSegment.WHOLE_SCHOOL,
        active=True,
        hire_date=date(2018, 3, 10)
    )
    
    db_session.add_all([staff1, staff2, staff3])
    db_session.commit()
    
    # Log creation
    audit_logger.log_create("person", None, "admin@eternity.edu", 
                           "Created staff members with segments")
    
    print(f"Created: {staff1.full_name} ({staff1.segment.value})")
    print(f"Created: {staff2.full_name} ({staff2.segment.value})")
    print(f"Created: {staff3.full_name} ({staff3.segment.value})")
    
    # Query by segment
    print("\n=== Querying by Segment ===")
    national_staff = db_session.query(Person).filter(
        Person.segment == StaffSegment.NATIONAL
    ).all()
    print(f"National staff: {len(national_staff)}")
    
    print("\n=== Creating Weight Matrix ===")
    
    # Create weight matrix
    weight_matrix = WeightMatrix(
        cycle_id=1,
        name="Q1 2024 Weight Matrix",
        description="Weight matrix for Q1 2024 evaluations",
        matrix_config={
            "academic": {
                "CEO": 1.0,
                "P&C": 0.8,
                "QA": 0.9,
                "peer_review": 0.7,
                "manager_review": 1.0,
                "direct_report_review": 0.6,
                "self_review": 0.5
            },
            "admin": {
                "CEO": 1.0,
                "P&C": 0.9,
                "QA": 0.7,
                "peer_review": 0.8,
                "manager_review": 1.0,
                "direct_report_review": 0.6,
                "self_review": 0.5
            }
        },
        is_active=True
    )
    
    db_session.add(weight_matrix)
    db_session.commit()
    
    audit_logger.log_create("weight_matrix", weight_matrix.id, "admin@eternity.edu",
                           f"Created weight matrix: {weight_matrix.name}")
    
    print(f"Created weight matrix: {weight_matrix.name}")
    
    print("\n=== Creating MRE Assignment with Weight Matrix ===")
    
    # Create assignment with weight matrix
    assignment = Assignment(
        cycle_id=1,
        rater_email="admin1@eternity.edu",
        target_email="teacher1@eternity.edu",
        target_group="academic",
        rater_context="manager_review",
        weight=1.0,
        weight_matrix_id=weight_matrix.id
    )
    
    db_session.add(assignment)
    db_session.commit()
    
    audit_logger.log_create("assignment", assignment.id, "admin@eternity.edu",
                           f"Created assignment: {assignment.rater_email} -> {assignment.target_email}")
    
    print(f"Created assignment with weight matrix: {assignment.id}")
    
    print("\n=== Creating EOM Nomination with Category ===")
    
    # Create EOM cycle
    eom_cycle = EOMCycle(
        cycle_id=1,
        month=1,
        year=2024,
        status="active",
        category_rotation={"academic": True, "admin": False}
    )
    
    db_session.add(eom_cycle)
    db_session.commit()
    
    # Create EOM nomination
    nomination = EOMNominee(
        eom_cycle_id=eom_cycle.id,
        nominee_email="teacher1@eternity.edu",
        nominated_by="admin1@eternity.edu",
        nomination_reason="Outstanding performance in student engagement and innovative teaching methods",
        category=EOMCategory.STUDENT_ENGAGEMENT,
        rotation_eligible=True,
        nomination_count=0,
        win_count=0,
        votes_received=0
    )
    
    db_session.add(nomination)
    db_session.commit()
    
    audit_logger.log_create("eom_nominee", nomination.id, "admin1@eternity.edu",
                           f"Nominated {nomination.nominee_email} for {nomination.category.value}")
    
    print(f"Created nomination: {nomination.nominee_email} in category {nomination.category.value}")
    
    print("\n=== Creating EOM Rotation Rule ===")
    
    # Create rotation rule
    rotation_rule = EOMRotationRule(
        category=EOMCategory.STUDENT_ENGAGEMENT,
        cycle_id=1,
        cooldown_period=3,
        max_wins_per_period=1,
        period_type="year",
        is_active=True
    )
    
    db_session.add(rotation_rule)
    db_session.commit()
    
    print(f"Created rotation rule for {rotation_rule.category.value}: "
          f"cooldown={rotation_rule.cooldown_period} cycles, "
          f"max_wins={rotation_rule.max_wins_per_period}")
    
    print("\n=== Checking Rotation Eligibility ===")
    
    # Check if person can be nominated again
    nominee = db_session.query(EOMNominee).filter(
        EOMNominee.nominee_email == "teacher1@eternity.edu"
    ).first()
    
    if nominee:
        print(f"Nominee: {nominee.nominee_email}")
        print(f"Rotation eligible: {nominee.rotation_eligible}")
        print(f"Nomination count: {nominee.nomination_count}")
        print(f"Win count: {nominee.win_count}")
        print(f"Last nominated cycle: {nominee.last_nominated_cycle_id}")
    
    print("\n=== Creating Evaluation with Weighted Rating ===")
    
    # Create evaluation
    evaluation = Evaluation(
        assignment_id=assignment.id,
        rating=4.5,
        weighted_rating=4.5 * assignment.weight,  # Apply weight
        comments="Excellent performance in all areas",
        status="submitted",
        domain_scores={
            "teaching": 4.5,
            "collaboration": 4.0,
            "innovation": 5.0
        }
    )
    
    db_session.add(evaluation)
    db_session.commit()
    
    audit_logger.log_submit("evaluation", evaluation.id, "admin1@eternity.edu",
                           f"Submitted evaluation for assignment {assignment.id}")
    
    print(f"Created evaluation: rating={evaluation.rating}, "
          f"weighted_rating={evaluation.weighted_rating}")
    
    print("\n=== Querying Audit Logs ===")
    
    # Get audit history
    audit_history = audit_logger.get_audit_history(
        entity_type="person",
        limit=10
    )
    
    print(f"\nAudit log entries for 'person': {len(audit_history)}")
    for entry in audit_history:
        print(f"  - {entry.action_type.value}: {entry.description} "
              f"by {entry.user_email} at {entry.created_at}")
    
    print("\n=== Querying by Segment ===")
    
    # Query staff by segment
    whole_school_staff = db_session.query(Person).filter(
        Person.segment == StaffSegment.WHOLE_SCHOOL,
        Person.active == True
    ).all()
    
    print(f"Whole school staff: {len(whole_school_staff)}")
    for staff in whole_school_staff:
        print(f"  - {staff.full_name} ({staff.role_title})")
    
    print("\n=== Querying EOM Nominations by Category ===")
    
    # Query nominations by category
    student_engagement_noms = db_session.query(EOMNominee).filter(
        EOMNominee.category == EOMCategory.STUDENT_ENGAGEMENT
    ).all()
    
    print(f"Student Engagement nominations: {len(student_engagement_noms)}")
    for nom in student_engagement_noms:
        print(f"  - {nom.nominee_email} (votes: {nom.votes_received})")
    
    # Clean up
    db_session.close()
    print("\n=== Example Complete ===")


if __name__ == '__main__':
    main()

