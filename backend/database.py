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
    """EOM nomination categories"""
    ACADEMIC = "academic"
    ADMIN = "admin"
    SUPPORT = "support"
    LEADERSHIP = "leadership"
    INNOVATION = "innovation"
    COLLABORATION = "collaboration"
    STUDENT_ENGAGEMENT = "student_engagement"


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


class Database:
    """Database connection and session management"""
    
    def __init__(self, database_url=None):
        if database_url is None:
            database_url = os.getenv(
                'DATABASE_URL',
                'postgresql://user:password@localhost/eternity_eval'
            )
        self.engine = create_engine(database_url, echo=False)
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

