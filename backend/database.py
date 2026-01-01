"""
Database models and connection handling for the Eternity School Evaluation System.
"""
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, Float, Text, Boolean, DateTime, Enum, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv
import enum

# Load environment variables
load_dotenv()

Base = declarative_base()


class StaffSegment(enum.Enum):
    """Staff segment types"""
    NATIONAL = "national"
    INTERNATIONAL = "international"
    WHOLE_SCHOOL = "whole_school"


class EOMCategory(enum.Enum):
    """EOM nomination categories - matching original design"""
    OUTSTANDING_LEADERSHIP = "outstanding_leadership"
    TEAM_SPIRIT = "team_spirit"
    INNOVATION = "innovation"
    RISING_STAR = "rising_star"
    SERVICE_EXCELLENCE = "service_excellence"


class ActionType(enum.Enum):
    """Types of actions for audit trail"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"
    VIEW = "view"
    EXPORT = "export"


class Cycle(Base):
    """Evaluation cycle (e.g., Q1-2024, Annual-2024)"""
    __tablename__ = 'cycles'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200))
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String(20), default='draft')  # draft, active, closed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    assignments = relationship("Assignment", back_populates="cycle")
    eom_cycles = relationship("EOMCycle", back_populates="cycle")
    weight_matrices = relationship("WeightMatrix", back_populates="cycle")


class Person(Base):
    """People in the system (staff, teachers, etc.) with segment support"""
    __tablename__ = 'people'
    
    email = Column(String(255), primary_key=True)
    full_name = Column(String(200), nullable=False)
    role_title = Column(String(100))
    department = Column(String(100))
    segment = Column(Enum(StaffSegment), nullable=False, default=StaffSegment.WHOLE_SCHOOL)
    hire_date = Column(Date)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assignments_as_rater = relationship("Assignment", foreign_keys="Assignment.rater_email", back_populates="rater")
    assignments_as_target = relationship("Assignment", foreign_keys="Assignment.target_email", back_populates="target")
    eom_nominations = relationship("EOMNominee", foreign_keys="EOMNominee.nominee_email", back_populates="nominee_person")
    eom_nominated_by = relationship("EOMNominee", foreign_keys="EOMNominee.nominated_by", back_populates="nominator_person")
    audit_logs = relationship("AuditLog", foreign_keys="AuditLog.user_email", back_populates="user")
    survey_responses = relationship("SurveyResponse", foreign_keys="SurveyResponse.respondent_email", back_populates="respondent")
    notifications = relationship("Notification", foreign_keys="Notification.recipient_email", back_populates="recipient")
    objections_submitted = relationship("Objection", foreign_keys="Objection.submitted_by", back_populates="submitter")
    objections_resolved = relationship("Objection", foreign_keys="Objection.resolved_by", back_populates="resolver")
    variance_alerts = relationship("VarianceAlert", foreign_keys="VarianceAlert.target_email", back_populates="target")
    feedback_submitted = relationship("Feedback", foreign_keys="Feedback.submitted_by", back_populates="submitter")
    feedback_reviewed = relationship("Feedback", foreign_keys="Feedback.reviewed_by", back_populates="reviewer")
    
    __table_args__ = (
        Index('idx_person_segment', 'segment'),
        Index('idx_person_active', 'active'),
    )


class Assignment(Base):
    """MRE assignments: who evaluates whom with weight matrix support"""
    __tablename__ = 'assignments'
    
    id = Column(Integer, primary_key=True)
    cycle_id = Column(Integer, ForeignKey('cycles.id'), nullable=False)
    rater_email = Column(String(255), ForeignKey('people.email'), nullable=False)
    rater_role = Column(String(100))
    target_email = Column(String(255), ForeignKey('people.email'), nullable=False)
    target_role = Column(String(100))
    target_group = Column(String(50))  # e.g., 'peers', 'direct_reports', 'self'
    rater_context = Column(String(100))  # e.g., 'peer_review', 'manager_review'
    weight = Column(Float, default=1.0)
    weight_matrix_id = Column(Integer, ForeignKey('weight_matrices.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cycle = relationship("Cycle", back_populates="assignments")
    rater = relationship("Person", foreign_keys=[rater_email], back_populates="assignments_as_rater")
    target = relationship("Person", foreign_keys=[target_email], back_populates="assignments_as_target")
    evaluations = relationship("Evaluation", back_populates="assignment")
    weight_matrix = relationship("WeightMatrix", back_populates="assignments")
    
    __table_args__ = (
        Index('idx_assignment_cycle', 'cycle_id'),
        Index('idx_assignment_rater', 'rater_email'),
        Index('idx_assignment_target', 'target_email'),
        Index('idx_assignment_context', 'rater_context'),
    )


class EOMCycle(Base):
    """Employee of the Month cycle"""
    __tablename__ = 'eom_cycles'
    
    id = Column(Integer, primary_key=True)
    cycle_id = Column(Integer, ForeignKey('cycles.id'), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    status = Column(String(20), default='draft')
    category_rotation = Column(JSON)  # Track which categories have been used
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    cycle = relationship("Cycle", back_populates="eom_cycles")
    voters = relationship("EOMVoter", back_populates="eom_cycle")
    nominees = relationship("EOMNominee", foreign_keys="EOMNominee.eom_cycle_id", back_populates="eom_cycle")
    
    __table_args__ = (
        Index('idx_eom_cycle_year_month', 'year', 'month'),
    )


class EOMVoter(Base):
    """EOM voters"""
    __tablename__ = 'eom_voters'
    
    id = Column(Integer, primary_key=True)
    eom_cycle_id = Column(Integer, ForeignKey('eom_cycles.id'), nullable=False)
    voter_email = Column(String(255), ForeignKey('people.email'), nullable=False)
    
    eom_cycle = relationship("EOMCycle", back_populates="voters")


class EOMNominee(Base):
    """EOM nominees with categories and rotation tracking"""
    __tablename__ = 'eom_nominees'
    
    id = Column(Integer, primary_key=True)
    eom_cycle_id = Column(Integer, ForeignKey('eom_cycles.id'), nullable=False)
    nominee_email = Column(String(255), ForeignKey('people.email'), nullable=False)
    nominated_by = Column(String(255), ForeignKey('people.email'))
    nomination_reason = Column(Text)
    category = Column(Enum(EOMCategory), nullable=False)
    rotation_eligible = Column(Boolean, default=True)  # Can be nominated again
    last_nominated_cycle_id = Column(Integer, ForeignKey('eom_cycles.id'), nullable=True)
    last_won_cycle_id = Column(Integer, ForeignKey('eom_cycles.id'), nullable=True)
    nomination_count = Column(Integer, default=0)  # Total nominations across all cycles
    win_count = Column(Integer, default=0)  # Total wins across all cycles
    votes_received = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    eom_cycle = relationship("EOMCycle", foreign_keys=[eom_cycle_id], back_populates="nominees")
    nominee_person = relationship("Person", foreign_keys=[nominee_email], back_populates="eom_nominations")
    nominator_person = relationship("Person", foreign_keys=[nominated_by], back_populates="eom_nominated_by")
    last_nominated_cycle = relationship("EOMCycle", foreign_keys=[last_nominated_cycle_id])
    last_won_cycle = relationship("EOMCycle", foreign_keys=[last_won_cycle_id])
    
    __table_args__ = (
        Index('idx_eom_nominee_category', 'category'),
        Index('idx_eom_nominee_rotation', 'rotation_eligible'),
        Index('idx_eom_nominee_cycle', 'eom_cycle_id'),
    )


class EOMWinner(Base):
    """EOM winners - tracks who won in each cycle"""
    __tablename__ = 'eom_winners'
    
    id = Column(Integer, primary_key=True)
    eom_cycle_id = Column(Integer, ForeignKey('eom_cycles.id'), nullable=False)
    winner_email = Column(String(255), ForeignKey('people.email'), nullable=False)
    category = Column(String(50))
    term = Column(String(50))  # e.g., '2024-Q1', '2024-Q2', '2024-Annual'
    votes_received = Column(Integer)
    announced_at = Column(Date, default=datetime.utcnow)
    
    eom_cycle = relationship("EOMCycle")


class WeightMatrix(Base):
    """Weight matrix configurations for MRE evaluations"""
    __tablename__ = 'weight_matrices'
    
    id = Column(Integer, primary_key=True)
    cycle_id = Column(Integer, ForeignKey('cycles.id'), nullable=False)
    name = Column(String(200))
    description = Column(Text)
    matrix_config = Column(JSON, nullable=False)  # Store weight matrix as JSON
    # Format: {"target_group": {"rater_context": weight, ...}, ...}
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cycle = relationship("Cycle", back_populates="weight_matrices")
    assignments = relationship("Assignment", back_populates="weight_matrix")
    
    __table_args__ = (
        Index('idx_weight_matrix_cycle', 'cycle_id'),
        Index('idx_weight_matrix_active', 'is_active'),
    )


class EOMRotationRule(Base):
    """Rules for EOM category rotation and eligibility"""
    __tablename__ = 'eom_rotation_rules'
    
    id = Column(Integer, primary_key=True)
    category = Column(Enum(EOMCategory), nullable=False)
    cycle_id = Column(Integer, ForeignKey('cycles.id'), nullable=False)
    cooldown_period = Column(Integer, default=3)  # Cycles before eligible again
    max_wins_per_period = Column(Integer, default=1)  # Max wins in a period
    period_type = Column(String(20), default='year')  # 'year', 'quarter', 'month'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    cycle = relationship("Cycle")
    
    __table_args__ = (
        Index('idx_rotation_category', 'category'),
        Index('idx_rotation_cycle', 'cycle_id'),
    )


class AuditLog(Base):
    """Comprehensive audit trail for all system actions"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    action_type = Column(Enum(ActionType), nullable=False)
    entity_type = Column(String(50), nullable=False)  # 'person', 'assignment', 'evaluation', 'eom_nominee', etc.
    entity_id = Column(Integer, nullable=True)  # ID of the affected entity
    user_email = Column(String(255), ForeignKey('people.email'), nullable=False)
    user_role = Column(String(100))
    changes = Column(JSON)  # Store before/after values for updates
    description = Column(Text)
    ip_address = Column(String(45))  # Support IPv6
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("Person", foreign_keys=[user_email])
    
    __table_args__ = (
        Index('idx_audit_action', 'action_type'),
        Index('idx_audit_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_user', 'user_email'),
        Index('idx_audit_created', 'created_at'),
    )


class Attendance(Base):
    """Attendance records for validation"""
    __tablename__ = 'attendance'
    
    id = Column(Integer, primary_key=True)
    person_email = Column(String(255), ForeignKey('people.email'), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String(20))  # 'present', 'absent', 'late', 'excused'
    cycle_id = Column(Integer, ForeignKey('cycles.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    person = relationship("Person")
    
    __table_args__ = (
        Index('idx_attendance_person', 'person_email'),
        Index('idx_attendance_date', 'date'),
    )


class Evaluation(Base):
    """Actual evaluation submissions with weight matrix support"""
    __tablename__ = 'evaluations'
    
    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey('assignments.id'), nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    rating = Column(Float)  # 1-5 scale or similar
    weighted_rating = Column(Float)  # Rating adjusted by weight matrix
    comments = Column(Text)
    status = Column(String(20), default='draft')  # draft, submitted, reviewed
    domain_scores = Column(JSON)  # Store domain-specific scores if applicable
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assignment = relationship("Assignment", back_populates="evaluations")
    
    __table_args__ = (
        Index('idx_evaluation_assignment', 'assignment_id'),
        Index('idx_evaluation_status', 'status'),
        Index('idx_evaluation_submitted', 'submitted_at'),
    )


class EmailNotification(Base):
    """Email notifications tracking"""
    __tablename__ = 'email_notifications'
    
    id = Column(Integer, primary_key=True)
    notification_type = Column(String(50), nullable=False)
    recipient_email = Column(String(255), ForeignKey('people.email'))
    subject = Column(String(500))
    body = Column(Text)
    status = Column(String(20), default='pending')  # pending, sent, failed
    sent_at = Column(DateTime)
    error_message = Column(Text)
    related_entity_type = Column(String(50))
    related_entity_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_email_notification_recipient', 'recipient_email'),
        Index('idx_email_notification_type', 'notification_type'),
        Index('idx_email_notification_status', 'status'),
    )


class SurveyIdentityPreference(Base):
    """Survey identity preferences - stores user's identity mode choice"""
    __tablename__ = 'survey_identity_preferences'
    
    id = Column(Integer, primary_key=True)
    user_email = Column(String(255), ForeignKey('people.email'), nullable=False)
    survey_id = Column(Integer, ForeignKey('surveys.id'), nullable=True)  # NULL = global preference
    identity_mode = Column(String(20), nullable=False)  # anonymous, identified, conditional
    privacy_level = Column(String(20))  # maximum, high, medium, low
    retention_days = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_survey_identity_user', 'user_email'),
        Index('idx_survey_identity_survey', 'survey_id'),
        Index('idx_survey_identity_mode', 'identity_mode'),
    )


class SurveyIdentityReveal(Base):
    """Survey identity reveals - tracks when and how identity was revealed"""
    __tablename__ = 'survey_identity_reveals'
    
    id = Column(Integer, primary_key=True)
    user_email = Column(String(255), ForeignKey('people.email'), nullable=False)
    survey_id = Column(Integer, ForeignKey('surveys.id'), nullable=True)
    reveal_method = Column(String(50), nullable=False)  # full, partial_role, partial_department, gradual, consent_based
    revealed_info = Column(JSON)  # What information was revealed
    target = Column(String(255))  # Who the reveal was for (optional)
    consent_confirmed = Column(Boolean, default=False)
    next_reveal_date = Column(DateTime)  # For gradual reveals
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_survey_reveal_user', 'user_email'),
        Index('idx_survey_reveal_survey', 'survey_id'),
        Index('idx_survey_reveal_method', 'reveal_method'),
    )


class SurveyConditionalReveal(Base):
    """Survey conditional reveal configurations"""
    __tablename__ = 'survey_conditional_reveals'
    
    id = Column(Integer, primary_key=True)
    user_email = Column(String(255), ForeignKey('people.email'), nullable=False)
    survey_id = Column(Integer, ForeignKey('surveys.id'), nullable=True)
    reveal_conditions = Column(JSON)  # Stored conditions configuration
    trigger_events = Column(JSON)  # Stored trigger events configuration
    notification_preferences = Column(JSON)  # Stored notification preferences
    status = Column(String(20), default='active')  # active, paused, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_survey_conditional_user', 'user_email'),
        Index('idx_survey_conditional_survey', 'survey_id'),
        Index('idx_survey_conditional_status', 'status'),
    )


class EOMFeedback(Base):
    """EOM feedback collection"""
    __tablename__ = 'eom_feedback'
    
    id = Column(Integer, primary_key=True)
    eom_cycle_id = Column(Integer, ForeignKey('eom_cycles.id'), nullable=False)
    feedback_type = Column(String(50), nullable=False)  # 'nominee', 'nominator', 'voter'
    person_email = Column(String(255), ForeignKey('people.email'))
    feedback_text = Column(Text, nullable=False)
    rating = Column(Integer)  # 1-5 scale
    submitted_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_eom_feedback_cycle', 'eom_cycle_id'),
        Index('idx_eom_feedback_person', 'person_email'),
        Index('idx_eom_feedback_type', 'feedback_type'),
    )


class Survey(Base):
    """Survey definitions"""
    __tablename__ = 'surveys'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    survey_type = Column(String(50))  # 'comprehensive', 'climate', 'feedback', etc.
    status = Column(String(20), default='draft')  # draft, active, closed
    start_date = Column(Date)
    end_date = Column(Date)
    created_by = Column(String(255), ForeignKey('people.email'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    questions = relationship("SurveyQuestion", back_populates="survey", cascade="all, delete-orphan")
    responses = relationship("SurveyResponse", back_populates="survey", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_survey_status', 'status'),
        Index('idx_survey_type', 'survey_type'),
        Index('idx_survey_dates', 'start_date', 'end_date'),
    )


class SurveyQuestion(Base):
    """Survey questions with metadata"""
    __tablename__ = 'survey_questions'
    
    id = Column(Integer, primary_key=True)
    survey_id = Column(Integer, ForeignKey('surveys.id'), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50))  # 'multiple_choice', 'text', 'rating', 'yes_no', etc.
    category = Column(String(100))  # 'physical_environment', 'workplace_culture', etc.
    section = Column(String(100))
    order_index = Column(Integer, default=0)
    required = Column(Boolean, default=True)
    identity_modes = Column(JSON)  # List of identity modes this question is available for
    sensitivity_level = Column(String(20))  # 'low', 'medium', 'high', 'very_high'
    options = Column(JSON)  # For multiple choice questions
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    survey = relationship("Survey", back_populates="questions")
    responses = relationship("SurveyResponse", back_populates="question")
    
    __table_args__ = (
        Index('idx_survey_question_survey', 'survey_id'),
        Index('idx_survey_question_category', 'category'),
        Index('idx_survey_question_order', 'survey_id', 'order_index'),
    )


class SurveyResponse(Base):
    """Survey responses with identity mode tracking"""
    __tablename__ = 'survey_responses'
    
    id = Column(Integer, primary_key=True)
    survey_id = Column(Integer, ForeignKey('surveys.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('survey_questions.id'), nullable=False)
    respondent_email = Column(String(255), ForeignKey('people.email'), nullable=True)  # NULL for anonymous
    anonymous_id = Column(String(255))  # For anonymous responses
    session_id = Column(String(255))  # Survey session ID
    identity_mode = Column(String(20))  # 'anonymous', 'conditional', 'partial', 'identified'
    response_text = Column(Text)
    response_value = Column(JSON)  # For structured responses
    submitted_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    survey = relationship("Survey", back_populates="responses")
    question = relationship("SurveyQuestion", back_populates="responses")
    respondent = relationship("Person", foreign_keys=[respondent_email], back_populates="survey_responses")
    
    __table_args__ = (
        Index('idx_survey_response_survey', 'survey_id'),
        Index('idx_survey_response_question', 'question_id'),
        Index('idx_survey_response_respondent', 'respondent_email'),
        Index('idx_survey_response_anonymous', 'anonymous_id'),
        Index('idx_survey_response_session', 'session_id'),
        Index('idx_survey_response_mode', 'identity_mode'),
    )


class Notification(Base):
    """In-app notifications"""
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True)
    recipient_email = Column(String(255), ForeignKey('people.email'), nullable=False)
    notification_type = Column(String(50), nullable=False)  # 'evaluation_due', 'eom_nomination', 'bias_alert', etc.
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    action_url = Column(String(500))  # URL to navigate to when clicked
    related_entity_type = Column(String(50))  # 'evaluation', 'eom_nominee', etc.
    related_entity_id = Column(Integer)
    priority = Column(String(20), default='normal')  # 'low', 'normal', 'high', 'urgent'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    recipient = relationship("Person", foreign_keys=[recipient_email], back_populates="notifications")
    
    __table_args__ = (
        Index('idx_notification_recipient', 'recipient_email'),
        Index('idx_notification_read', 'read'),
        Index('idx_notification_type', 'notification_type'),
        Index('idx_notification_created', 'created_at'),
        Index('idx_notification_priority', 'priority'),
    )


class Objection(Base):
    """Objections/Appeals system"""
    __tablename__ = 'objections'
    
    id = Column(Integer, primary_key=True)
    submitted_by = Column(String(255), ForeignKey('people.email'), nullable=False)
    objection_type = Column(String(50), nullable=False)  # 'evaluation', 'eom_nomination', 'score', etc.
    related_entity_type = Column(String(50), nullable=False)
    related_entity_id = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(20), default='pending')  # pending, under_review, resolved, rejected
    resolution_notes = Column(Text)
    resolved_by = Column(String(255), ForeignKey('people.email'))
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    submitter = relationship("Person", foreign_keys=[submitted_by])
    resolver = relationship("Person", foreign_keys=[resolved_by])
    
    __table_args__ = (
        Index('idx_objection_submitter', 'submitted_by'),
        Index('idx_objection_status', 'status'),
        Index('idx_objection_type', 'objection_type'),
        Index('idx_objection_entity', 'related_entity_type', 'related_entity_id'),
    )


class VarianceAlert(Base):
    """Variance alert tracking"""
    __tablename__ = 'variance_alerts'
    
    id = Column(Integer, primary_key=True)
    cycle_id = Column(Integer, ForeignKey('cycles.id'), nullable=False)
    alert_type = Column(String(50), nullable=False)  # 'bias', 'participation', 'scoring', etc.
    severity = Column(String(20), default='medium')  # 'low', 'medium', 'high', 'critical'
    target_email = Column(String(255), ForeignKey('people.email'))
    description = Column(Text, nullable=False)
    details = Column(JSON)  # Additional alert details
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(255), ForeignKey('people.email'))
    acknowledged_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    cycle = relationship("Cycle")
    target = relationship("Person", foreign_keys=[target_email])
    
    __table_args__ = (
        Index('idx_variance_alert_cycle', 'cycle_id'),
        Index('idx_variance_alert_type', 'alert_type'),
        Index('idx_variance_alert_severity', 'severity'),
        Index('idx_variance_alert_acknowledged', 'acknowledged'),
    )


class Announcement(Base):
    """System announcements"""
    __tablename__ = 'announcements'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    author_email = Column(String(255), ForeignKey('people.email'))
    priority = Column(String(20), default='normal')  # low, normal, high, urgent
    target_audience = Column(String(50), default='all')  # all, ceo, pnc, department_head, staff
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = relationship("Person", foreign_keys=[author_email])
    
    __table_args__ = (
        Index('idx_announcements_active', 'is_active'),
        Index('idx_announcements_priority', 'priority'),
        Index('idx_announcements_audience', 'target_audience'),
    )


class Feedback(Base):
    """General feedback collection (separate from EOMFeedback)"""
    __tablename__ = 'feedback'
    
    id = Column(Integer, primary_key=True)
    submitted_by = Column(String(255), ForeignKey('people.email'), nullable=False)
    feedback_type = Column(String(50), nullable=False)  # 'system', 'process', 'feature', 'general'
    category = Column(String(100))  # 'ui', 'performance', 'functionality', etc.
    title = Column(String(200))
    message = Column(Text, nullable=False)
    rating = Column(Integer)  # 1-5 scale
    status = Column(String(20), default='new')  # new, reviewed, addressed, closed
    reviewed_by = Column(String(255), ForeignKey('people.email'))
    reviewed_at = Column(DateTime)
    response = Column(Text)  # Response from admin
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    submitter = relationship("Person", foreign_keys=[submitted_by])
    reviewer = relationship("Person", foreign_keys=[reviewed_by])
    
    __table_args__ = (
        Index('idx_feedback_submitter', 'submitted_by'),
        Index('idx_feedback_type', 'feedback_type'),
        Index('idx_feedback_status', 'status'),
        Index('idx_feedback_category', 'category'),
    )


class Database:
    """Database connection and session management"""
    
    def __init__(self, database_url=None):
        if database_url is None:
            database_url = os.getenv(
                'DATABASE_URL',
                'postgresql://user:password@localhost/eternity_eval'
            )
        # Production-ready connection pooling
        pool_size = int(os.getenv('DB_POOL_SIZE', '10'))
        max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '20'))
        pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', '30'))
        pool_recycle = int(os.getenv('DB_POOL_RECYCLE', '3600'))
        
        self.engine = create_engine(
            database_url,
            echo=False,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_pre_ping=True,  # Verify connections before using
        )
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """Get a database session"""
        return self.SessionLocal()
    
    def close(self):
        """Close database connection"""
        self.engine.dispose()


def get_db_session(database_url: str = None):
    """
    Convenience helper to create a database session.
    
    Usage:
        db = get_db_session()
        try:
            # Use db session
            result = db.query(Model).all()
        finally:
            db.close()
    
    Or use as context manager:
        with get_db_session() as db:
            result = db.query(Model).all()
    """
    db_instance = Database(database_url)
    session = db_instance.get_session()
    # Make session act as context manager
    session.__enter__ = lambda: session
    session.__exit__ = lambda exc_type, exc_val, exc_tb: session.close()
    return session
