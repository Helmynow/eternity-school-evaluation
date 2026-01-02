"""
Role-Based Access Control (RBAC) System
Manages user permissions, roles, and access control for the Eternity School Evaluation System.
"""
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, JSON, Enum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, List, Any
import enum
from backend.database import Base, Person, AuditLog, ActionType as DBActionType
from backend.audit_logger import AuditLogger


class PermissionType(enum.Enum):
    """Types of permissions that can be granted"""
    # Evaluation permissions
    CREATE_EVALUATION = "create_evaluation"
    VIEW_EVALUATION = "view_evaluation"
    EDIT_EVALUATION = "edit_evaluation"
    DELETE_EVALUATION = "delete_evaluation"
    
    # EOM permissions
    NOMINATE_EOM = "nominate_eom"
    VOTE_EOM = "vote_eom"
    VIEW_EOM_RESULTS = "view_eom_results"
    MANAGE_EOM_CYCLES = "manage_eom_cycles"
    
    # Admin permissions
    MANAGE_STAFF = "manage_staff"
    MANAGE_CYCLES = "manage_cycles"
    VIEW_REPORTS = "view_reports"
    EXPORT_DATA = "export_data"
    MANAGE_SETTINGS = "manage_settings"
    
    # Permission management
    GRANT_PERMISSIONS = "grant_permissions"
    REVOKE_PERMISSIONS = "revoke_permissions"
    MANAGE_ROLES = "manage_roles"
    
    # Survey permissions
    CREATE_SURVEY = "create_survey"
    VIEW_SURVEY = "view_survey"
    RESPOND_SURVEY = "respond_survey"
    VIEW_SURVEY_RESULTS = "view_survey_results"


class UserPermission(Base):
    """Time-based user permissions"""
    __tablename__ = 'user_permissions'
    
    id = Column(Integer, primary_key=True)
    user_email = Column(String(255), ForeignKey('people.email'), nullable=False)
    permission_type = Column(Enum(PermissionType), nullable=False)
    granted_by = Column(String(255), ForeignKey('people.email'), nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # None = unlimited
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(String(255), ForeignKey('people.email'), nullable=True)
    metadata = Column(JSON)  # Additional permission context
    
    # Relationships
    user = relationship("Person", foreign_keys=[user_email])
    granter = relationship("Person", foreign_keys=[granted_by])
    revoker = relationship("Person", foreign_keys=[revoked_by])
    
    __table_args__ = (
        Index('idx_user_permission', 'user_email', 'permission_type'),
        Index('idx_permission_active', 'user_email', 'permission_type', 'revoked_at'),
    )


class RBACSystem:
    """Role-Based Access Control system"""
    
    # Super admin email
    SUPER_ADMIN_EMAIL = "ahelmy@eternityschoolegypt.com"
    
    # Role hierarchy (higher number = more permissions)
    ROLE_HIERARCHY = {
        'super_admin': 100,
        'ceo': 90,
        'pnc': 70,
        'department_head': 50,
        'staff': 10,
    }
    
    # Default permissions for each role
    ROLE_PERMISSIONS = {
        'super_admin': list(PermissionType),  # All permissions
        'ceo': [
            PermissionType.VIEW_EVALUATION,
            PermissionType.VIEW_REPORTS,
            PermissionType.EXPORT_DATA,
            PermissionType.VIEW_EOM_RESULTS,
            PermissionType.MANAGE_SETTINGS,
            PermissionType.GRANT_PERMISSIONS,
            PermissionType.REVOKE_PERMISSIONS,
            PermissionType.MANAGE_ROLES,
        ],
        'pnc': [
            PermissionType.MANAGE_STAFF,
            PermissionType.VIEW_EVALUATION,
            PermissionType.VIEW_REPORTS,
            PermissionType.NOMINATE_EOM,
            PermissionType.VOTE_EOM,
        ],
        'department_head': [
            PermissionType.CREATE_EVALUATION,
            PermissionType.VIEW_EVALUATION,
            PermissionType.EDIT_EVALUATION,
            PermissionType.NOMINATE_EOM,
            PermissionType.VOTE_EOM,
        ],
        'staff': [
            PermissionType.VIEW_EVALUATION,
            PermissionType.RESPOND_SURVEY,
        ],
    }
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.audit_logger = AuditLogger(db_session)
    
    def is_super_admin(self, user_email: str) -> bool:
        """Check if user is super admin"""
        return user_email.lower() == self.SUPER_ADMIN_EMAIL.lower()
    
    def get_user_role(self, user_email: str) -> Optional[str]:
        """Get user's role from Person table or Supabase metadata"""
        person = self.db.query(Person).filter(Person.email == user_email).first()
        if person:
            # Check role_title or infer from metadata
            role = getattr(person, 'role_title', None)
            if role:
                # Normalize role names
                role_lower = role.lower()
                if 'ceo' in role_lower or 'director' in role_lower:
                    return 'ceo'
                elif 'pnc' in role_lower or 'people' in role_lower or 'culture' in role_lower:
                    return 'pnc'
                elif 'head' in role_lower or 'principal' in role_lower or 'coordinator' in role_lower:
                    return 'department_head'
                else:
                    return 'staff'
        return 'staff'  # Default
    
    def has_permission(self, user_email: str, permission: PermissionType, context: Optional[Dict] = None) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            user_email: Email of the user
            permission: Permission to check
            context: Optional context for permission check
        
        Returns:
            True if user has permission, False otherwise
        """
        # Super admin has all permissions
        if self.is_super_admin(user_email):
            return True
        
        # Check role-based permissions
        role = self.get_user_role(user_email)
        role_perms = self.ROLE_PERMISSIONS.get(role, [])
        if permission in role_perms:
            return True
        
        # Check explicit user permissions (not revoked, not expired)
        active_permission = self.db.query(UserPermission).filter(
            UserPermission.user_email == user_email,
            UserPermission.permission_type == permission,
            UserPermission.revoked_at.is_(None),
            (UserPermission.expires_at.is_(None) | (UserPermission.expires_at > datetime.utcnow()))
        ).first()
        
        return active_permission is not None
    
    def grant_permission(
        self,
        user_email: str,
        permission: PermissionType,
        granted_by: str,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ) -> UserPermission:
        """
        Grant a permission to a user.
        
        Args:
            user_email: Email of user to grant permission to
            permission: Permission type to grant
            granted_by: Email of user granting permission (must be super admin or have GRANT_PERMISSIONS)
            expires_at: Optional expiration date (None = unlimited)
            metadata: Optional metadata
        
        Returns:
            Created UserPermission object
        """
        # Check if granter has permission to grant permissions
        if not self.has_permission(granted_by, PermissionType.GRANT_PERMISSIONS):
            raise PermissionError(f"User {granted_by} does not have permission to grant permissions")
        
        # Check if user exists
        user = self.db.query(Person).filter(Person.email == user_email).first()
        if not user:
            raise ValueError(f"User {user_email} not found")
        
        # Revoke any existing permission of this type
        existing = self.db.query(UserPermission).filter(
            UserPermission.user_email == user_email,
            UserPermission.permission_type == permission,
            UserPermission.revoked_at.is_(None)
        ).first()
        
        if existing:
            existing.revoked_at = datetime.utcnow()
            existing.revoked_by = granted_by
        
        # Create new permission
        new_permission = UserPermission(
            user_email=user_email,
            permission_type=permission,
            granted_by=granted_by,
            expires_at=expires_at,  # None = unlimited
            metadata=metadata or {}
        )
        
        self.db.add(new_permission)
        self.db.commit()
        
        # Audit log
        self.audit_logger.log_action(
            DBActionType.CREATE,
            'user_permission',
            new_permission.id,
            granted_by,
            description=f"Granted {permission.value} to {user_email}",
            changes={'permission': permission.value, 'user': user_email, 'expires_at': str(expires_at) if expires_at else 'unlimited'}
        )
        
        return new_permission
    
    def revoke_permission(
        self,
        user_email: str,
        permission: PermissionType,
        revoked_by: str
    ) -> bool:
        """
        Revoke a permission from a user.
        
        Args:
            user_email: Email of user to revoke permission from
            permission: Permission type to revoke
            revoked_by: Email of user revoking permission
        
        Returns:
            True if permission was revoked, False if it didn't exist
        """
        # Check if revoker has permission
        if not self.has_permission(revoked_by, PermissionType.REVOKE_PERMISSIONS):
            raise PermissionError(f"User {revoked_by} does not have permission to revoke permissions")
        
        # Find active permission
        active_permission = self.db.query(UserPermission).filter(
            UserPermission.user_email == user_email,
            UserPermission.permission_type == permission,
            UserPermission.revoked_at.is_(None)
        ).first()
        
        if not active_permission:
            return False
        
        # Revoke it
        active_permission.revoked_at = datetime.utcnow()
        active_permission.revoked_by = revoked_by
        
        self.db.commit()
        
        # Audit log
        self.audit_logger.log_action(
            DBActionType.UPDATE,
            'user_permission',
            active_permission.id,
            revoked_by,
            description=f"Revoked {permission.value} from {user_email}",
            changes={'permission': permission.value, 'user': user_email}
        )
        
        return True
    
    def get_user_permissions(self, user_email: str) -> List[Dict]:
        """Get all active permissions for a user"""
        # Super admin has all permissions
        if self.is_super_admin(user_email):
            return [{'permission': perm.value, 'source': 'super_admin', 'unlimited': True} for perm in PermissionType]
        
        permissions = []
        
        # Role-based permissions
        role = self.get_user_role(user_email)
        role_perms = self.ROLE_PERMISSIONS.get(role, [])
        for perm in role_perms:
            permissions.append({
                'permission': perm.value,
                'source': f'role:{role}',
                'unlimited': True
            })
        
        # Explicit permissions
        explicit_perms = self.db.query(UserPermission).filter(
            UserPermission.user_email == user_email,
            UserPermission.revoked_at.is_(None),
            (UserPermission.expires_at.is_(None) | (UserPermission.expires_at > datetime.utcnow()))
        ).all()
        
        for perm in explicit_perms:
            permissions.append({
                'permission': perm.permission_type.value,
                'source': 'explicit',
                'granted_by': perm.granted_by,
                'granted_at': perm.granted_at.isoformat(),
                'expires_at': perm.expires_at.isoformat() if perm.expires_at else None,
                'unlimited': perm.expires_at is None,
                'metadata': perm.metadata
            })
        
        return permissions
    
    def require_permission(self, permission: PermissionType):
        """Decorator to require a permission for an endpoint"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Extract user_email from request
                # This is a simplified version - in practice, extract from JWT token
                request = kwargs.get('request') or args[0] if args else None
                if not request:
                    raise ValueError("Request object required")
                
                # Get user from request (simplified - should use auth middleware)
                user_email = getattr(request.state, 'user_email', None)
                if not user_email:
                    raise PermissionError("User not authenticated")
                
                if not self.has_permission(user_email, permission):
                    raise PermissionError(f"User {user_email} does not have permission: {permission.value}")
                
                return func(*args, **kwargs)
            return wrapper
        return decorator
