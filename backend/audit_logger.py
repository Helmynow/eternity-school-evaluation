"""
Audit logging utility for tracking all system actions.
Supports FastAPI request objects.
"""

from datetime import datetime
from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from backend.database import ActionType, AuditLog, Person

# Type hints for request objects (avoid circular import)
try:
    from fastapi import Request as FastAPIRequest
except ImportError:
    FastAPIRequest = None

RequestType = Union[FastAPIRequest, Any]


class AuditLogger:
    """Utility class for creating audit log entries"""

    def __init__(self, db_session: Session):
        self.db = db_session

    def log_action(
        self,
        action_type: ActionType,
        entity_type: str,
        entity_id: Optional[int],
        user_email: str,
        description: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_obj: Optional[RequestType] = None,
    ) -> AuditLog:
        """
        Create an audit log entry.

        Supports FastAPI Request objects.
        Thread-safe for use in async FastAPI contexts.

        Args:
            action_type: Type of action (CREATE, UPDATE, DELETE, etc.)
            entity_type: Type of entity affected (e.g., 'person', 'assignment')
            entity_id: ID of the affected entity
            user_email: Email of the user performing the action
            description: Human-readable description
            changes: Dictionary with 'before' and 'after' keys for updates
            ip_address: IP address of the user (auto-extracted from request if not provided)
            user_agent: User agent string (auto-extracted from request if not provided)
            request_obj: FastAPI Request object (optional)

        Returns:
            Created AuditLog instance
        """
        # Get user role if available
        user = self.db.query(Person).filter(Person.email == user_email).first()
        user_role = user.role_title if user else None

        # Extract IP and user agent from request if available
        if request_obj is not None:
            if ip_address is None:
                # FastAPI Request object
                if hasattr(request_obj, "client") and request_obj.client:
                    ip_address = request_obj.client.host
                # Try to get from headers as fallback
                elif hasattr(request_obj, "headers"):
                    # Check for X-Forwarded-For or X-Real-IP headers (common in proxies)
                    forwarded_for = request_obj.headers.get("x-forwarded-for")
                    if forwarded_for:
                        ip_address = forwarded_for.split(",")[0].strip()
                    else:
                        ip_address = request_obj.headers.get("x-real-ip")

            if user_agent is None:
                # FastAPI Request object
                if hasattr(request_obj, "headers"):
                    user_agent = request_obj.headers.get("user-agent")

        audit_entry = AuditLog(
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            user_email=user_email,
            user_role=user_role,
            changes=changes,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow(),
        )

        self.db.add(audit_entry)
        self.db.commit()

        return audit_entry

    def log_create(self, entity_type: str, entity_id: int, user_email: str, description: Optional[str] = None) -> AuditLog:
        """Log a create action"""
        return self.log_action(
            ActionType.CREATE,
            entity_type,
            entity_id,
            user_email,
            description=description or f"Created {entity_type} {entity_id}",
        )

    def log_update(
        self, entity_type: str, entity_id: int, user_email: str, changes: Dict[str, Any], description: Optional[str] = None
    ) -> AuditLog:
        """Log an update action with before/after changes"""
        return self.log_action(
            ActionType.UPDATE,
            entity_type,
            entity_id,
            user_email,
            changes=changes,
            description=description or f"Updated {entity_type} {entity_id}",
        )

    def log_delete(self, entity_type: str, entity_id: int, user_email: str, description: Optional[str] = None) -> AuditLog:
        """Log a delete action"""
        return self.log_action(
            ActionType.DELETE,
            entity_type,
            entity_id,
            user_email,
            description=description or f"Deleted {entity_type} {entity_id}",
        )

    def log_submit(self, entity_type: str, entity_id: int, user_email: str, description: Optional[str] = None) -> AuditLog:
        """Log a submit action"""
        return self.log_action(
            ActionType.SUBMIT,
            entity_type,
            entity_id,
            user_email,
            description=description or f"Submitted {entity_type} {entity_id}",
        )

    def log_view(
        self, entity_type: str, entity_id: Optional[int], user_email: str, description: Optional[str] = None
    ) -> AuditLog:
        """Log a view action"""
        return self.log_action(
            ActionType.VIEW,
            entity_type,
            entity_id,
            user_email,
            description=description or f"Viewed {entity_type}" + (f" {entity_id}" if entity_id else ""),
        )

    def get_audit_history(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        user_email: Optional[str] = None,
        action_type: Optional[ActionType] = None,
        limit: int = 100,
    ) -> list:
        """
        Retrieve audit log entries with optional filters.

        Args:
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            user_email: Filter by user email
            action_type: Filter by action type
            limit: Maximum number of results

        Returns:
            List of AuditLog entries
        """
        query = self.db.query(AuditLog)

        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)
        if user_email:
            query = query.filter(AuditLog.user_email == user_email)
        if action_type:
            query = query.filter(AuditLog.action_type == action_type)

        return query.order_by(AuditLog.created_at.desc()).limit(limit).all()
