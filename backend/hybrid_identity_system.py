"""
Complete Hybrid Identity Survey System
Main System Controller for managing all identity modes and survey operations.
"""

import hashlib
import json
import logging
import secrets
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from backend.conditional_anonymity_engine import ConditionalAnonymityEngine
from backend.survey_identity_manager import IdentityMode, SurveyIdentityManager


class HybridIdentityMode(Enum):
    """Extended identity modes for hybrid system"""

    ANONYMOUS = "anonymous"
    CONDITIONALLY_ANONYMOUS = "conditional"
    PARTIALLY_IDENTIFIED = "partial"
    FULLY_IDENTIFIED = "identified"


class HybridIdentitySurveySystem:
    """
    Complete hybrid identity management for school surveys.
    Main controller that orchestrates all identity and survey operations.
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)

        # Initialize sub-systems
        self.identity_manager = IdentityManager(db_session)
        self.survey_engine = SurveyEngine(db_session)
        self.analytics_engine = AnalyticsEngine(db_session)
        self.privacy_manager = PrivacyManager(db_session)
        self.consent_tracker = ConsentTracker(db_session)

        # Session storage (in production, use Redis or database)
        self.sessions = {}

    def initialize_user_session(self, user_id: str, preferred_mode: str, survey_id: Optional[int] = None) -> Dict:
        """
        Initialize a new user session with chosen identity mode.

        Args:
            user_id: User email or ID
            preferred_mode: Preferred identity mode
            survey_id: Optional survey ID

        Returns:
            Dictionary with session information
        """
        try:
            # Validate mode
            try:
                mode = HybridIdentityMode(preferred_mode.lower())
            except ValueError:
                raise ValueError(f"Invalid identity mode: {preferred_mode}")

            session_id = secrets.token_urlsafe(32)
            session_data = {
                "user_id": user_id,
                "session_id": session_id,
                "identity_mode": mode.value,
                "survey_id": survey_id,
                "created_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "permissions": self.get_permissions_for_mode(mode),
                "consent_granted": self.get_initial_consent(mode),
            }

            # Store session
            self.store_session(session_data)

            # Get available surveys
            available_surveys = self.get_available_surveys(mode, survey_id)

            return {
                "session_token": session_id,
                "mode": mode.value,
                "available_surveys": available_surveys,
                "privacy_level": self.calculate_privacy_level(mode),
                "can_switch_modes": self.can_switch_modes(mode),
                "consent_required": self.get_consent_requirements(mode),
                "session_expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error initializing user session: {e}")
            raise

    def get_permissions_for_mode(self, mode: HybridIdentityMode) -> Dict:
        """Get permissions for identity mode"""
        permissions = {
            HybridIdentityMode.ANONYMOUS: {
                "can_reveal_identity": False,
                "can_switch_to_identified": True,
                "can_switch_to_conditional": True,
                "can_switch_to_partial": True,
                "can_receive_follow_up": False,
                "can_edit_responses": True,
                "data_retention_days": 90,
            },
            HybridIdentityMode.CONDITIONALLY_ANONYMOUS: {
                "can_reveal_identity": True,
                "can_switch_to_identified": True,
                "can_switch_to_anonymous": True,
                "can_switch_to_partial": True,
                "can_receive_follow_up": True,
                "can_edit_responses": True,
                "data_retention_days": 180,
            },
            HybridIdentityMode.PARTIALLY_IDENTIFIED: {
                "can_reveal_identity": True,
                "can_switch_to_identified": True,
                "can_switch_to_conditional": True,
                "can_switch_to_anonymous": True,
                "can_receive_follow_up": True,
                "can_edit_responses": True,
                "data_retention_days": 365,
            },
            HybridIdentityMode.FULLY_IDENTIFIED: {
                "can_reveal_identity": True,
                "can_switch_to_identified": False,
                "can_switch_to_conditional": True,
                "can_switch_to_anonymous": True,
                "can_receive_follow_up": True,
                "can_edit_responses": True,
                "data_retention_days": 365,
            },
        }
        return permissions.get(mode, {})

    def get_initial_consent(self, mode: HybridIdentityMode) -> Dict:
        """Get initial consent requirements for mode"""
        consent = {
            HybridIdentityMode.ANONYMOUS: {
                "data_collection": True,
                "anonymous_processing": True,
                "data_retention": True,
                "analytics_use": True,
            },
            HybridIdentityMode.CONDITIONALLY_ANONYMOUS: {
                "data_collection": True,
                "conditional_reveal": True,
                "data_retention": True,
                "analytics_use": True,
                "follow_up_contact": True,
            },
            HybridIdentityMode.PARTIALLY_IDENTIFIED: {
                "data_collection": True,
                "partial_identification": True,
                "data_retention": True,
                "analytics_use": True,
                "follow_up_contact": True,
            },
            HybridIdentityMode.FULLY_IDENTIFIED: {
                "data_collection": True,
                "full_identification": True,
                "data_retention": True,
                "analytics_use": True,
                "follow_up_contact": True,
                "public_attribution": False,  # Can be enabled
            },
        }
        return consent.get(mode, {})

    def get_available_surveys(self, mode: HybridIdentityMode, survey_id: Optional[int] = None) -> List[Dict]:
        """Get available surveys for identity mode"""
        # This would query the surveys table
        # For now, return mock data
        return [
            {
                "id": survey_id or 1,
                "title": "School Climate Survey",
                "type": "comprehensive",
                "available_for_mode": True,
                "estimated_time": "15-20 minutes",
            }
        ]

    def calculate_privacy_level(self, mode: HybridIdentityMode) -> str:
        """Calculate privacy level for mode"""
        levels = {
            HybridIdentityMode.ANONYMOUS: "maximum",
            HybridIdentityMode.CONDITIONALLY_ANONYMOUS: "high",
            HybridIdentityMode.PARTIALLY_IDENTIFIED: "medium",
            HybridIdentityMode.FULLY_IDENTIFIED: "low",
        }
        return levels.get(mode, "medium")

    def can_switch_modes(self, mode: HybridIdentityMode) -> bool:
        """Check if user can switch modes"""
        return True  # All modes allow switching

    def get_consent_requirements(self, mode: HybridIdentityMode) -> List[str]:
        """Get consent requirements for mode"""
        requirements = {
            HybridIdentityMode.ANONYMOUS: ["data_collection", "anonymous_processing"],
            HybridIdentityMode.CONDITIONALLY_ANONYMOUS: ["data_collection", "conditional_reveal", "follow_up_contact"],
            HybridIdentityMode.PARTIALLY_IDENTIFIED: ["data_collection", "partial_identification", "follow_up_contact"],
            HybridIdentityMode.FULLY_IDENTIFIED: [
                "data_collection",
                "full_identification",
                "follow_up_contact",
                "public_attribution",
            ],
        }
        return requirements.get(mode, [])

    def store_session(self, session_data: Dict):
        """Store session data"""
        self.sessions[session_data["session_id"]] = session_data
        self.logger.info(f"Session stored: {session_data['session_id']}")

    def get_all_survey_data(self) -> List[Dict]:
        """Get all survey data for analytics"""
        # This would query survey_responses table
        return []

    def get_identity_breakdown(self) -> Dict:
        """Get breakdown of responses by identity mode"""
        # This would aggregate from survey_responses and identity_preferences
        return {"anonymous": 0, "conditional": 0, "partial": 0, "identified": 0}


# Import sub-components
from backend.hybrid_identity_components import AnalyticsEngine, ConsentTracker, IdentityManager, PrivacyManager, SurveyEngine
