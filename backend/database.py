"""
Database models and connection handling for the Eternity School Evaluation System.

SCALABILITY NOTES (200+ concurrent users):
==========================================
This module uses Supavisor Transaction mode (port 6543) for optimal connection pooling.

Key configuration:
- Transaction mode: Connections released after each transaction (not held per session)
- NullPool for serverless: No local pooling, let Supavisor handle it
- QueuePool for persistent: Local pool with conservative limits
- Prepared statements disabled: Required for Supavisor Transaction mode
- Connection retry with backoff: Handles transient failures gracefully

Environment variables:
- DATABASE_URL: Must use port 6543 for Transaction mode (e.g., ...pooler.supabase.com:6543/postgres)
- DB_POOL_SIZE: Local pool size (default: 5, ignored in serverless mode)
- DB_MAX_OVERFLOW: Additional connections allowed (default: 10)
- DB_POOL_TIMEOUT: Wait time for available connection (default: 30s)
- DB_SERVERLESS: Set to "true" for serverless deployments (Vercel, AWS Lambda)
- DB_STATEMENT_TIMEOUT: Query timeout in milliseconds (default: 30000)
"""

import enum
import logging
import os
import time
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from typing import Generator, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from dotenv import load_dotenv
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    event,
    text,
)
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker, with_loader_criteria
from sqlalchemy.pool import NullPool, QueuePool

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

Base = declarative_base()


class SoftDeleteMixin:
    """Shared soft-delete fields and helpers for core tables."""

    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String(255), ForeignKey("people.email", ondelete="SET NULL"), nullable=True)

    def soft_delete(self, deleted_by_email: Optional[str] = None) -> None:
        self.deleted_at = datetime.utcnow()
        if deleted_by_email:
            self.deleted_by = deleted_by_email

    def restore(self) -> None:
        self.deleted_at = None
        self.deleted_by = None

    @classmethod
    def active_filter(cls):
        return cls.deleted_at.is_(None)

# =============================================================================
# Enum helpers (Supabase-compatible)
# =============================================================================


def pg_enum(enum_cls: type[enum.Enum], *, name: str) -> Enum:
    """
    Create a SQLAlchemy Enum that persists **enum values** (not enum names).

    Supabase migrations define enum values like 'national'/'create' etc, so persisting names
    like 'NATIONAL'/'CREATE' will break at runtime.
    """

    return Enum(enum_cls, name=name, values_callable=lambda obj: [e.value for e in obj], native_enum=True)


# =============================================================================
# Connection Configuration Helpers
# =============================================================================


def _ensure_transaction_mode(database_url: str) -> str:
    """
    Ensure the database URL uses Transaction mode (port 6543) for Supavisor.

    Transaction mode is CRITICAL for scalability:
    - Session mode (5432): Holds connection for entire session → limited to pool_size
    - Transaction mode (6543): Releases connection after each query → 200x clients supported
    """
    if not database_url:
        return database_url

    parsed = urlparse(database_url)

    # Check if this is a Supabase pooler URL
    if "pooler.supabase.com" in (parsed.hostname or ""):
        # Ensure we're using Transaction mode port (6543)
        if parsed.port == 5432:
            logger.warning(
                "DATABASE_URL uses Session mode (port 5432). "
                "Switching to Transaction mode (port 6543) for better scalability."
            )
            # Replace port 5432 with 6543
            netloc = parsed.netloc.replace(":5432", ":6543")
            parsed = parsed._replace(netloc=netloc)

    # Note: We handle prepared statements via connect_args (prepare_threshold=0)
    # rather than URL parameters, since pgbouncer=true is Prisma-specific

    return urlunparse(parsed)


def _add_connection_options(database_url: str) -> str:
    """Add connection options for reliability."""
    if not database_url:
        return database_url

    parsed = urlparse(database_url)
    query_params = parse_qs(parsed.query)

    # Set connection timeout (how long to wait for a connection)
    if "connect_timeout" not in query_params:
        query_params["connect_timeout"] = ["10"]

    # Set statement timeout to prevent long-running queries
    statement_timeout = os.getenv("DB_STATEMENT_TIMEOUT", "30000")
    if "options" not in query_params:
        query_params["options"] = [f"-c statement_timeout={statement_timeout}"]

    new_query = urlencode(query_params, doseq=True)
    parsed = parsed._replace(query=new_query)

    return urlunparse(parsed)


# =============================================================================
# Retry Logic
# =============================================================================


def with_retry(max_retries: int = 3, base_delay: float = 0.5, max_delay: float = 10.0):
    """
    Decorator for retrying database operations with exponential backoff.

    Handles transient connection errors gracefully, which is essential
    when 200 users might be hitting the database simultaneously.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    last_exception = e
                    error_msg = str(e).lower()

                    # Retry on connection-related errors
                    retryable_errors = [
                        "connection refused",
                        "connection reset",
                        "connection timed out",
                        "max clients",
                        "too many connections",
                        "server closed",
                        "ssl connection",
                    ]

                    if any(err in error_msg for err in retryable_errors):
                        delay = min(base_delay * (2**attempt), max_delay)
                        logger.warning(
                            f"Database connection error (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        # Non-retryable error
                        raise
                except DBAPIError as e:
                    # Check if it's a connection-related error
                    if e.connection_invalidated:
                        last_exception = e
                        delay = min(base_delay * (2**attempt), max_delay)
                        logger.warning(
                            f"Connection invalidated (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        raise

            # All retries exhausted
            logger.error(f"All {max_retries} database connection attempts failed")
            raise last_exception

        return wrapper

    return decorator


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


class RotationPeriodType(enum.Enum):
    """Rotation period types (matches Supabase enum rotation_period_type)."""

    YEAR = "year"
    QUARTER = "quarter"
    MONTH = "month"
    TERM = "term"


class Cycle(SoftDeleteMixin, Base):
    """Evaluation cycle (e.g., Q1-2024, Annual-2024)"""

    __tablename__ = "cycles"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200))
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String(20), default="draft")  # draft, active, closed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assignments = relationship("Assignment", back_populates="cycle")
    eom_cycles = relationship("EOMCycle", back_populates="cycle")
    weight_matrices = relationship("WeightMatrix", back_populates="cycle")


class Person(SoftDeleteMixin, Base):
    """People in the system (staff, teachers, etc.) with segment support"""

    __tablename__ = "people"

    email = Column(String(255), primary_key=True)
    full_name = Column(String(200), nullable=False)
    role_title = Column(String(100))
    department = Column(String(100))
    segment = Column(pg_enum(StaffSegment, name="staff_segment"), nullable=False, default=StaffSegment.WHOLE_SCHOOL)
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
    survey_responses = relationship(
        "SurveyResponse", foreign_keys="SurveyResponse.respondent_email", back_populates="respondent"
    )
    notifications = relationship("Notification", foreign_keys="Notification.recipient_email", back_populates="recipient")
    objections_submitted = relationship("Objection", foreign_keys="Objection.submitted_by", back_populates="submitter")
    objections_resolved = relationship("Objection", foreign_keys="Objection.resolved_by", back_populates="resolver")
    variance_alerts = relationship("VarianceAlert", foreign_keys="VarianceAlert.target_email", back_populates="target")
    feedback_submitted = relationship("Feedback", foreign_keys="Feedback.submitted_by", back_populates="submitter")
    feedback_reviewed = relationship("Feedback", foreign_keys="Feedback.reviewed_by", back_populates="reviewer")

    __table_args__ = (
        Index("idx_person_segment", "segment"),
        Index("idx_person_active", "active"),
    )


class Assignment(SoftDeleteMixin, Base):
    """MRE assignments: who evaluates whom with weight matrix support"""

    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True)
    cycle_id = Column(Integer, ForeignKey("cycles.id", ondelete="RESTRICT"), nullable=False)
    rater_email = Column(String(255), ForeignKey("people.email", ondelete="CASCADE"), nullable=False)
    rater_role = Column(String(100))
    target_email = Column(String(255), ForeignKey("people.email", ondelete="CASCADE"), nullable=False)
    target_role = Column(String(100))
    target_group = Column(String(50))  # e.g., 'peers', 'direct_reports', 'self'
    rater_context = Column(String(100))  # e.g., 'peer_review', 'manager_review'
    weight = Column(Float, default=1.0)
    weight_matrix_id = Column(Integer, ForeignKey("weight_matrices.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cycle = relationship("Cycle", back_populates="assignments")
    rater = relationship("Person", foreign_keys=[rater_email], back_populates="assignments_as_rater")
    target = relationship("Person", foreign_keys=[target_email], back_populates="assignments_as_target")
    evaluations = relationship("Evaluation", back_populates="assignment")
    weight_matrix = relationship("WeightMatrix", back_populates="assignments")

    __table_args__ = (
        Index("idx_assignment_cycle", "cycle_id"),
        Index("idx_assignment_rater", "rater_email"),
        Index("idx_assignment_target", "target_email"),
        Index("idx_assignment_context", "rater_context"),
    )


class EOMCycle(SoftDeleteMixin, Base):
    """Employee of the Month cycle"""

    __tablename__ = "eom_cycles"

    id = Column(Integer, primary_key=True)
    cycle_id = Column(Integer, ForeignKey("cycles.id", ondelete="RESTRICT"), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    status = Column(String(20), default="draft")
    category_rotation = Column(JSON)  # Track which categories have been used
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cycle = relationship("Cycle", back_populates="eom_cycles")
    voters = relationship("EOMVoter", back_populates="eom_cycle")
    nominees = relationship("EOMNominee", foreign_keys="EOMNominee.eom_cycle_id", back_populates="eom_cycle")

    __table_args__ = (Index("idx_eom_cycle_year_month", "year", "month"),)


class EOMVoter(Base):
    """EOM voters"""

    __tablename__ = "eom_voters"

    id = Column(Integer, primary_key=True)
    eom_cycle_id = Column(Integer, ForeignKey("eom_cycles.id", ondelete="CASCADE"), nullable=False)
    voter_email = Column(String(255), ForeignKey("people.email", ondelete="CASCADE"), nullable=False)
    nominee_email = Column(String(255), ForeignKey("people.email", ondelete="CASCADE"), nullable=True)

    eom_cycle = relationship("EOMCycle", back_populates="voters")
    nominee_person = relationship("Person", foreign_keys=[nominee_email])

    __table_args__ = (
        UniqueConstraint("eom_cycle_id", "voter_email", name="unique_eom_vote_per_cycle"),
        Index("idx_eom_voter_cycle", "eom_cycle_id"),
        Index("idx_eom_voter_email", "voter_email"),
    )


class EOMNominee(SoftDeleteMixin, Base):
    """EOM nominees with categories and rotation tracking"""

    __tablename__ = "eom_nominees"

    id = Column(Integer, primary_key=True)
    eom_cycle_id = Column(Integer, ForeignKey("eom_cycles.id", ondelete="CASCADE"), nullable=False)
    nominee_email = Column(String(255), ForeignKey("people.email", ondelete="CASCADE"), nullable=False)
    nominated_by = Column(String(255), ForeignKey("people.email", ondelete="SET NULL"))
    nomination_reason = Column(Text)
    category = Column(pg_enum(EOMCategory, name="eom_category"), nullable=False)
    rotation_eligible = Column(Boolean, default=True)  # Can be nominated again
    last_nominated_cycle_id = Column(Integer, ForeignKey("eom_cycles.id", ondelete="SET NULL"), nullable=True)
    last_won_cycle_id = Column(Integer, ForeignKey("eom_cycles.id", ondelete="SET NULL"), nullable=True)
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
        Index("idx_eom_nominee_category", "category"),
        Index("idx_eom_nominee_rotation", "rotation_eligible"),
        Index("idx_eom_nominee_cycle", "eom_cycle_id"),
    )


class EOMWinner(Base):
    """EOM winners - tracks who won in each cycle"""

    __tablename__ = "eom_winners"

    id = Column(Integer, primary_key=True)
    eom_cycle_id = Column(Integer, ForeignKey("eom_cycles.id"), nullable=False)
    winner_email = Column(String(255), ForeignKey("people.email"), nullable=False)
    # In Supabase migrations this column is migrated to `eom_category` (enum).
    # Keep it nullable for backward compatibility with early schema versions.
    category = Column(pg_enum(EOMCategory, name="eom_category"), nullable=True)
    term = Column(String(50))  # e.g., '2024-Q1', '2024-Q2', '2024-Annual'
    votes_received = Column(Integer)
    announced_at = Column(Date, default=datetime.utcnow)

    eom_cycle = relationship("EOMCycle")


class WeightMatrix(Base):
    """Weight matrix configurations for MRE evaluations"""

    __tablename__ = "weight_matrices"

    id = Column(Integer, primary_key=True)
    cycle_id = Column(Integer, ForeignKey("cycles.id", ondelete="RESTRICT"), nullable=False)
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
        Index("idx_weight_matrix_cycle", "cycle_id"),
        Index("idx_weight_matrix_active", "is_active"),
    )


class EOMRotationRule(Base):
    """Rules for EOM category rotation and eligibility"""

    __tablename__ = "eom_rotation_rules"

    id = Column(Integer, primary_key=True)
    category = Column(pg_enum(EOMCategory, name="eom_category"), nullable=False)
    cycle_id = Column(Integer, ForeignKey("cycles.id"), nullable=False)
    cooldown_period = Column(Integer, default=3)  # Cycles before eligible again
    max_wins_per_period = Column(Integer, default=1)  # Max wins in a period
    period_type = Column(pg_enum(RotationPeriodType, name="rotation_period_type"), default=RotationPeriodType.QUARTER)
    # Matches Supabase schema/migrations
    max_nominations_per_year = Column(Integer, default=2)  # Max nominations per year
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cycle = relationship("Cycle")

    __table_args__ = (
        Index("idx_rotation_category", "category"),
        Index("idx_rotation_cycle", "cycle_id"),
    )


class AuditLog(Base):
    """Comprehensive audit trail for all system actions"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    action_type = Column(pg_enum(ActionType, name="action_type"), nullable=False)
    entity_type = Column(String(50), nullable=False)  # 'person', 'assignment', 'evaluation', 'eom_nominee', etc.
    entity_id = Column(Integer, nullable=True)  # ID of the affected entity
    user_email = Column(String(255), ForeignKey("people.email"), nullable=False)
    user_role = Column(String(100))
    changes = Column(JSON)  # Store before/after values for updates
    description = Column(Text)
    ip_address = Column(String(45))  # Support IPv6
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("Person", foreign_keys=[user_email])

    __table_args__ = (
        Index("idx_audit_action", "action_type"),
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_user", "user_email"),
        Index("idx_audit_created", "created_at"),
    )


class Attendance(Base):
    """Attendance records for validation"""

    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True)
    person_email = Column(String(255), ForeignKey("people.email"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String(20))  # 'present', 'absent', 'late', 'excused'
    cycle_id = Column(Integer, ForeignKey("cycles.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    person = relationship("Person")

    __table_args__ = (
        Index("idx_attendance_person", "person_email"),
        Index("idx_attendance_date", "date"),
    )


class Evaluation(SoftDeleteMixin, Base):
    """Actual evaluation submissions with weight matrix support"""

    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    rating = Column(Float)  # 1-5 scale or similar
    weighted_rating = Column(Float)  # Rating adjusted by weight matrix
    comments = Column(Text)
    status = Column(String(20), default="draft")  # draft, submitted, reviewed
    domain_scores = Column(JSON)  # Store domain-specific scores if applicable
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assignment = relationship("Assignment", back_populates="evaluations")

    __table_args__ = (
        Index("idx_evaluation_assignment", "assignment_id"),
        Index("idx_evaluation_status", "status"),
        Index("idx_evaluation_submitted", "submitted_at"),
    )


class EmailNotification(Base):
    """Email notifications tracking"""

    __tablename__ = "email_notifications"

    id = Column(Integer, primary_key=True)
    notification_type = Column(String(50), nullable=False)
    recipient_email = Column(String(255), ForeignKey("people.email"))
    subject = Column(String(500))
    body = Column(Text)
    status = Column(String(20), default="pending")  # pending, sent, failed
    sent_at = Column(DateTime)
    error_message = Column(Text)
    related_entity_type = Column(String(50))
    related_entity_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_email_notification_recipient", "recipient_email"),
        Index("idx_email_notification_type", "notification_type"),
        Index("idx_email_notification_status", "status"),
    )


class SurveyIdentityPreference(Base):
    """Survey identity preferences - stores user's identity mode choice"""

    __tablename__ = "survey_identity_preferences"

    id = Column(Integer, primary_key=True)
    user_email = Column(String(255), ForeignKey("people.email"), nullable=False)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=True)  # NULL = global preference
    identity_mode = Column(String(20), nullable=False)  # anonymous, identified, conditional
    privacy_level = Column(String(20))  # maximum, high, medium, low
    retention_days = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_survey_identity_user", "user_email"),
        Index("idx_survey_identity_survey", "survey_id"),
        Index("idx_survey_identity_mode", "identity_mode"),
    )


class SurveyIdentityReveal(Base):
    """Survey identity reveals - tracks when and how identity was revealed"""

    __tablename__ = "survey_identity_reveals"

    id = Column(Integer, primary_key=True)
    user_email = Column(String(255), ForeignKey("people.email"), nullable=False)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=True)
    reveal_method = Column(String(50), nullable=False)  # full, partial_role, partial_department, gradual, consent_based
    revealed_info = Column(JSON)  # What information was revealed
    target = Column(String(255))  # Who the reveal was for (optional)
    consent_confirmed = Column(Boolean, default=False)
    next_reveal_date = Column(DateTime)  # For gradual reveals
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_survey_reveal_user", "user_email"),
        Index("idx_survey_reveal_survey", "survey_id"),
        Index("idx_survey_reveal_method", "reveal_method"),
    )


class SurveyConditionalReveal(Base):
    """Survey conditional reveal configurations"""

    __tablename__ = "survey_conditional_reveals"

    id = Column(Integer, primary_key=True)
    user_email = Column(String(255), ForeignKey("people.email"), nullable=False)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=True)
    reveal_conditions = Column(JSON)  # Stored conditions configuration
    trigger_events = Column(JSON)  # Stored trigger events configuration
    notification_preferences = Column(JSON)  # Stored notification preferences
    status = Column(String(20), default="active")  # active, paused, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_survey_conditional_user", "user_email"),
        Index("idx_survey_conditional_survey", "survey_id"),
        Index("idx_survey_conditional_status", "status"),
    )


class EOMFeedback(Base):
    """EOM feedback collection"""

    __tablename__ = "eom_feedback"

    id = Column(Integer, primary_key=True)
    eom_cycle_id = Column(Integer, ForeignKey("eom_cycles.id"), nullable=False)
    feedback_type = Column(String(50), nullable=False)  # 'nominee', 'nominator', 'voter'
    person_email = Column(String(255), ForeignKey("people.email"))
    feedback_text = Column(Text, nullable=False)
    rating = Column(Integer)  # 1-5 scale
    submitted_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_eom_feedback_cycle", "eom_cycle_id"),
        Index("idx_eom_feedback_person", "person_email"),
        Index("idx_eom_feedback_type", "feedback_type"),
    )


class Survey(Base):
    """Survey definitions"""

    __tablename__ = "surveys"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    survey_type = Column(String(50))  # 'comprehensive', 'climate', 'feedback', etc.
    status = Column(String(20), default="draft")  # draft, active, closed
    start_date = Column(Date)
    end_date = Column(Date)
    created_by = Column(String(255), ForeignKey("people.email"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    questions = relationship("SurveyQuestion", back_populates="survey", cascade="all, delete-orphan")
    responses = relationship("SurveyResponse", back_populates="survey", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_survey_status", "status"),
        Index("idx_survey_type", "survey_type"),
        Index("idx_survey_dates", "start_date", "end_date"),
    )


class SurveyQuestion(Base):
    """Survey questions with metadata"""

    __tablename__ = "survey_questions"

    id = Column(Integer, primary_key=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
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
        Index("idx_survey_question_survey", "survey_id"),
        Index("idx_survey_question_category", "category"),
        Index("idx_survey_question_order", "survey_id", "order_index"),
    )


class SurveyResponse(Base):
    """Survey responses with identity mode tracking"""

    __tablename__ = "survey_responses"

    id = Column(Integer, primary_key=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("survey_questions.id"), nullable=False)
    respondent_email = Column(String(255), ForeignKey("people.email"), nullable=True)  # NULL for anonymous
    anonymous_id = Column(String(255))  # For anonymous responses
    session_id = Column(String(255))  # Survey session ID
    identity_mode = Column(String(20))  # 'anonymous', 'conditional', 'partial', 'identified'
    response_text = Column(Text)
    response_value = Column(JSON)  # For structured responses
    # Session lifecycle tracking (used for abandonment analytics)
    started_at = Column(DateTime, default=datetime.utcnow)
    abandoned_at = Column(DateTime)
    session_status = Column(String(20))  # active, completed, abandoned, timeout
    abandoned_confidence = Column(String(10))  # HIGH/MEDIUM/LOW/NULL for estimated historical values
    submitted_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    survey = relationship("Survey", back_populates="responses")
    question = relationship("SurveyQuestion", back_populates="responses")
    respondent = relationship("Person", foreign_keys=[respondent_email], back_populates="survey_responses")

    __table_args__ = (
        Index("idx_survey_response_survey", "survey_id"),
        Index("idx_survey_response_question", "question_id"),
        Index("idx_survey_response_respondent", "respondent_email"),
        Index("idx_survey_response_anonymous", "anonymous_id"),
        Index("idx_survey_response_session", "session_id"),
        Index("idx_survey_response_mode", "identity_mode"),
    )


class Notification(Base):
    """In-app notifications"""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    recipient_email = Column(String(255), ForeignKey("people.email"), nullable=False)
    notification_type = Column(String(50), nullable=False)  # 'evaluation_due', 'eom_nomination', 'bias_alert', etc.
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    action_url = Column(String(500))  # URL to navigate to when clicked
    related_entity_type = Column(String(50))  # 'evaluation', 'eom_nominee', etc.
    related_entity_id = Column(Integer)
    priority = Column(String(20), default="normal")  # 'low', 'normal', 'high', 'urgent'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    recipient = relationship("Person", foreign_keys=[recipient_email], back_populates="notifications")

    __table_args__ = (
        Index("idx_notification_recipient", "recipient_email"),
        Index("idx_notification_read", "read"),
        Index("idx_notification_type", "notification_type"),
        Index("idx_notification_created", "created_at"),
        Index("idx_notification_priority", "priority"),
    )


class Objection(Base):
    """Objections/Appeals system"""

    __tablename__ = "objections"

    id = Column(Integer, primary_key=True)
    submitted_by = Column(String(255), ForeignKey("people.email"), nullable=False)
    objection_type = Column(String(50), nullable=False)  # 'evaluation', 'eom_nomination', 'score', etc.
    related_entity_type = Column(String(50), nullable=False)
    related_entity_id = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(20), default="pending")  # pending, under_review, resolved, rejected
    resolution_notes = Column(Text)
    resolved_by = Column(String(255), ForeignKey("people.email"))
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    submitter = relationship("Person", foreign_keys=[submitted_by])
    resolver = relationship("Person", foreign_keys=[resolved_by])

    __table_args__ = (
        Index("idx_objection_submitter", "submitted_by"),
        Index("idx_objection_status", "status"),
        Index("idx_objection_type", "objection_type"),
        Index("idx_objection_entity", "related_entity_type", "related_entity_id"),
    )


class VarianceAlert(Base):
    """Variance alert tracking"""

    __tablename__ = "variance_alerts"

    id = Column(Integer, primary_key=True)
    cycle_id = Column(Integer, ForeignKey("cycles.id"), nullable=False)
    alert_type = Column(String(50), nullable=False)  # 'bias', 'participation', 'scoring', etc.
    severity = Column(String(20), default="medium")  # 'low', 'medium', 'high', 'critical'
    target_email = Column(String(255), ForeignKey("people.email"))
    description = Column(Text, nullable=False)
    details = Column(JSON)  # Additional alert details
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(255), ForeignKey("people.email"))
    acknowledged_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    cycle = relationship("Cycle")
    target = relationship("Person", foreign_keys=[target_email])

    __table_args__ = (
        Index("idx_variance_alert_cycle", "cycle_id"),
        Index("idx_variance_alert_type", "alert_type"),
        Index("idx_variance_alert_severity", "severity"),
        Index("idx_variance_alert_acknowledged", "acknowledged"),
    )


class Announcement(Base):
    """System announcements"""

    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    author_email = Column(String(255), ForeignKey("people.email"))
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    target_audience = Column(String(50), default="all")  # all, ceo, pnc, department_head, staff
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    author = relationship("Person", foreign_keys=[author_email])

    __table_args__ = (
        Index("idx_announcements_active", "is_active"),
        Index("idx_announcements_priority", "priority"),
        Index("idx_announcements_audience", "target_audience"),
    )


class Feedback(Base):
    """General feedback collection (separate from EOMFeedback)"""

    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)
    submitted_by = Column(String(255), ForeignKey("people.email"), nullable=False)
    feedback_type = Column(String(50), nullable=False)  # 'system', 'process', 'feature', 'general'
    category = Column(String(100))  # 'ui', 'performance', 'functionality', etc.
    title = Column(String(200))
    message = Column(Text, nullable=False)
    rating = Column(Integer)  # 1-5 scale
    status = Column(String(20), default="new")  # new, reviewed, addressed, closed
    reviewed_by = Column(String(255), ForeignKey("people.email"))
    reviewed_at = Column(DateTime)
    response = Column(Text)  # Response from admin
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    submitter = relationship("Person", foreign_keys=[submitted_by])
    reviewer = relationship("Person", foreign_keys=[reviewed_by])

    __table_args__ = (
        Index("idx_feedback_submitter", "submitted_by"),
        Index("idx_feedback_type", "feedback_type"),
        Index("idx_feedback_status", "status"),
        Index("idx_feedback_category", "category"),
    )


class SystemSetting(Base):
    """Global (singleton) system settings configured by the CEO"""

    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, default=1)
    email_notifications = Column(Boolean, default=True)
    auto_activate_cycles = Column(Boolean, default=False)
    require_approval = Column(Boolean, default=True)
    default_rotation_period = Column(String(20), default="term")  # term, quarter, month, year
    max_nominations_per_person = Column(Integer, default=1)
    evaluation_deadline_days = Column(Integer, default=30)
    updated_by = Column(String(255), ForeignKey("people.email"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    updater = relationship("Person", foreign_keys=[updated_by])


class HybridIdentitySession(Base):
    """Persisted Hybrid Identity sessions for cross-request reliability"""

    __tablename__ = "hybrid_identity_sessions"

    id = Column(Integer, primary_key=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    user_email = Column(String(255), ForeignKey("people.email"), nullable=False)
    identity_mode = Column(String(20), nullable=False)
    survey_id = Column(Integer, ForeignKey("surveys.id"))
    permissions = Column(JSON, default=dict)
    consent_granted = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    session_status = Column(String(20), default="active")  # active, completed, abandoned, timeout
    abandoned_at = Column(DateTime)

    user = relationship("Person", foreign_keys=[user_email])
    survey = relationship("Survey", foreign_keys=[survey_id])

    __table_args__ = (
        Index("idx_hybrid_identity_sessions_user", "user_email"),
        Index("idx_hybrid_identity_sessions_survey", "survey_id"),
    )


class Database:
    """
    Production-ready database connection management for 200+ concurrent users.

    Uses singleton pattern to ensure only ONE engine exists for the application.
    Automatically configures for optimal performance based on environment:

    - Serverless (Vercel, Lambda): NullPool - no local pooling, Supavisor handles it
    - Persistent (VMs, containers): QueuePool - local pool with conservative limits

    IMPORTANT: Use Transaction mode connection string (port 6543) for scalability!
    """

    _instance = None
    _engine = None
    _SessionLocal = None
    _is_serverless = None

    def __new__(cls, database_url=None):
        """Singleton pattern - only create one Database instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, database_url=None):
        # Only initialize once
        if getattr(self, "_initialized", False):
            return
        self._initialized = True

        if database_url is None:
            # Support multiple deployment environments (Supabase, Vercel Postgres, local dev).
            database_url = (
                os.getenv("DATABASE_URL")
                or os.getenv("POSTGRES_URL_NON_POOLING")
                or os.getenv("POSTGRES_URL")
                or os.getenv("POSTGRES_PRISMA_URL")
            )
            if database_url:
                # Heroku/Vercel sometimes provide "postgres://" which SQLAlchemy doesn't accept.
                if database_url.startswith("postgres://"):
                    database_url = "postgresql://" + database_url[len("postgres://") :]
            else:
                database_url = "postgresql://user:password@localhost/eternity_eval"

        # Optimize URL for Supavisor Transaction mode
        database_url = _ensure_transaction_mode(database_url)
        database_url = _add_connection_options(database_url)

        # Detect serverless environment
        Database._is_serverless = (
            os.getenv("DB_SERVERLESS", "").lower() == "true"
            or os.getenv("VERCEL", "").lower() == "1"
            or os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None
            or os.getenv("SERVERLESS", "").lower() == "true"
        )

        if Database._is_serverless:
            # SERVERLESS MODE: Use NullPool
            # No local connection pooling - let Supavisor handle everything
            # This is ideal for edge functions and serverless where each invocation
            # should create fresh connections
            logger.info("Database configured for SERVERLESS mode (NullPool)")
            Database._engine = create_engine(
                database_url,
                echo=False,
                poolclass=NullPool,  # No local pooling
            )
        else:
            # PERSISTENT MODE: Use QueuePool with conservative limits
            # Local pooling for VMs/containers, but conservative to work with Supavisor
            pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
            max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
            pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
            pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "300"))  # 5 min recycle

            logger.info(f"Database configured for PERSISTENT mode (QueuePool: size={pool_size}, overflow={max_overflow})")

            Database._engine = create_engine(
                database_url,
                echo=False,
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout,
                pool_recycle=pool_recycle,
                pool_pre_ping=True,  # Verify connections before using
            )

        # Add connection event listeners for monitoring
        @event.listens_for(Database._engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            logger.debug("New database connection established")

        @event.listens_for(Database._engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            logger.debug("Connection checked out from pool")

        @event.listens_for(Database._engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            logger.debug("Connection returned to pool")

        Database._SessionLocal = sessionmaker(
            bind=Database._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,  # Avoid lazy loading issues after commit
        )

        # Apply soft-delete filtering globally for SELECTs unless explicitly disabled.
        @event.listens_for(Database._SessionLocal, "do_orm_execute")
        def _add_soft_delete_criteria(execute_state):
            if (
                execute_state.is_select
                and not execute_state.execution_options.get("include_deleted", False)
            ):
                execute_state.statement = execute_state.statement.options(
                    with_loader_criteria(
                        SoftDeleteMixin,
                        lambda cls: cls.deleted_at.is_(None),
                        include_aliases=True,
                    )
                )
        self.engine = Database._engine
        self.SessionLocal = Database._SessionLocal

    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.

        Usage:
            db = Database()
            with db.session_scope() as session:
                session.query(Model).all()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self):
        """Close database connection and dispose of connection pool"""
        if Database._engine:
            Database._engine.dispose()
            logger.info("Database connection pool disposed")

    @classmethod
    def reset_instance(cls):
        """Reset singleton (for testing only)"""
        if cls._engine:
            cls._engine.dispose()
        cls._instance = None
        cls._engine = None
        cls._SessionLocal = None
        cls._is_serverless = None

    @classmethod
    def get_pool_status(cls) -> dict:
        """Get current connection pool status (useful for monitoring)"""
        if cls._engine is None:
            return {"status": "not_initialized"}

        if cls._is_serverless:
            return {"mode": "serverless", "pool": "NullPool"}

        pool = cls._engine.pool
        return {
            "mode": "persistent",
            "pool": "QueuePool",
            "size": pool.size(),
            "checkedin": pool.checkedin(),
            "checkedout": pool.checkedout(),
            "overflow": pool.overflow(),
        }


def get_db_session(database_url: str = None) -> Session:
    """
    Convenience helper to create a database session.

    Uses the singleton Database instance to prevent connection exhaustion.

    Usage:
        session = get_db_session()
        try:
            result = session.query(Model).all()
        finally:
            session.close()

    Or use as context manager:
        with get_db_session() as session:
            result = session.query(Model).all()
    """
    db_instance = Database(database_url)
    session = db_instance.get_session()
    # Make session act as context manager
    session.__enter__ = lambda: session
    session.__exit__ = lambda exc_type, exc_val, exc_tb: session.close()
    return session


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions with automatic commit/rollback.

    Usage:
        with get_db_context() as session:
            session.add(new_object)
            # Automatically commits on success, rolls back on exception
    """
    db_instance = Database()
    with db_instance.session_scope() as session:
        yield session


def get_database() -> Database:
    """Get the singleton Database instance."""
    return Database()


# =============================================================================
# Health Check
# =============================================================================


@with_retry(max_retries=3, base_delay=1.0)
def check_database_health() -> dict:
    """
    Check database connectivity and pool health.

    Returns a dict with status information, useful for health check endpoints.
    """
    db = Database()
    try:
        with db.session_scope() as session:
            # Simple query to verify connection
            result = session.execute(text("SELECT 1 as health")).fetchone()
            if result and result[0] == 1:
                return {
                    "status": "healthy",
                    "pool": Database.get_pool_status(),
                }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "pool": Database.get_pool_status(),
        }

    return {"status": "unknown"}
