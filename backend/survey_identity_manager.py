"""
Hybrid Identity Survey System - Flexible Identity Controller
Allows users to choose between anonymous, identified, or conditional identity modes.
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging
from sqlalchemy.orm import Session
from backend.database import Person, SurveyIdentityPreference, SurveyIdentityReveal


class IdentityMode(Enum):
    """Identity preference modes"""
    ANONYMOUS = "anonymous"
    IDENTIFIED = "identified"
    CONDITIONAL = "conditional"


class PrivacyLevel(Enum):
    """Privacy levels"""
    MAXIMUM = "maximum"  # Anonymous, no tracking
    HIGH = "high"  # Conditional, minimal tracking
    MEDIUM = "medium"  # Identified, standard tracking
    LOW = "low"  # Full identification, complete tracking


class RevealMethod(Enum):
    """Methods for revealing identity"""
    FULL = "full"  # Complete identity reveal
    PARTIAL_ROLE = "partial_role"  # Reveal role only
    PARTIAL_DEPARTMENT = "partial_department"  # Reveal department only
    GRADUAL = "gradual"  # Gradual reveal over time
    CONSENT_BASED = "consent_based"  # Reveal with explicit consent


class SurveyIdentityManager:
    """
    Flexible Identity Controller for Hybrid Identity Survey System.
    Manages user identity preferences, reveal options, and privacy settings.
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.anonymous_mode = False
        self.user_choice = None
        self.logger = logging.getLogger(__name__)
        
        # Default privacy settings
        self.default_retention_days = {
            IdentityMode.ANONYMOUS: 90,  # Short retention for anonymous
            IdentityMode.IDENTIFIED: 365,  # Standard retention
            IdentityMode.CONDITIONAL: 180  # Medium retention
        }
        
        # Privacy level mappings
        self.privacy_level_map = {
            IdentityMode.ANONYMOUS: PrivacyLevel.MAXIMUM,
            IdentityMode.CONDITIONAL: PrivacyLevel.HIGH,
            IdentityMode.IDENTIFIED: PrivacyLevel.MEDIUM
        }
    
    def set_identity_preference(
        self,
        user_id: str,
        preference: str,
        survey_id: Optional[int] = None
    ) -> Dict:
        """
        User chooses: anonymous, identified, or conditional identity mode.
        
        Args:
            user_id: User email or ID
            preference: "anonymous", "identified", or "conditional"
            survey_id: Optional survey ID for survey-specific preferences
        
        Returns:
            Dictionary with mode, reveal options, privacy level, and data retention
        """
        try:
            # Validate preference
            try:
                mode = IdentityMode(preference.lower())
            except ValueError:
                raise ValueError(f"Invalid preference: {preference}. Must be 'anonymous', 'identified', or 'conditional'")
            
            # Store preference
            self.user_choice = mode
            if mode == IdentityMode.ANONYMOUS:
                self.anonymous_mode = True
            
            # Get reveal options based on preference
            reveal_options = self.get_reveal_options(preference)
            
            # Calculate privacy level
            privacy_level = self.calculate_privacy_level(preference)
            
            # Set data retention policy
            data_retention = self.set_retention_policy(preference)
            
            # Store in database (if table exists)
            self._store_preference(user_id, preference, survey_id)
            
            return {
                "mode": preference,
                "mode_enum": mode.value,
                "reveal_options": reveal_options,
                "privacy_level": privacy_level.value,
                "data_retention": data_retention,
                "anonymous_mode": self.anonymous_mode,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Error setting identity preference: {e}")
            raise
    
    def get_reveal_options(self, preference: str) -> Dict:
        """
        Get available reveal options based on identity preference.
        
        Args:
            preference: Identity preference mode
        
        Returns:
            Dictionary with available reveal options
        """
        mode = IdentityMode(preference.lower())
        
        if mode == IdentityMode.ANONYMOUS:
            return {
                "can_reveal": False,
                "options": [],
                "message": "Anonymous mode: Identity cannot be revealed",
                "revoke_anonymity": True  # Can revoke to switch modes
            }
        
        elif mode == IdentityMode.IDENTIFIED:
            return {
                "can_reveal": True,
                "options": [
                    {
                        "method": RevealMethod.FULL.value,
                        "description": "Full identity reveal",
                        "available": True
                    },
                    {
                        "method": RevealMethod.PARTIAL_ROLE.value,
                        "description": "Reveal role only",
                        "available": True
                    },
                    {
                        "method": RevealMethod.PARTIAL_DEPARTMENT.value,
                        "description": "Reveal department only",
                        "available": True
                    }
                ],
                "message": "Identified mode: Full reveal options available"
            }
        
        else:  # CONDITIONAL
            return {
                "can_reveal": True,
                "options": [
                    {
                        "method": RevealMethod.CONSENT_BASED.value,
                        "description": "Reveal with explicit consent",
                        "available": True
                    },
                    {
                        "method": RevealMethod.GRADUAL.value,
                        "description": "Gradual reveal over time",
                        "available": True
                    },
                    {
                        "method": RevealMethod.PARTIAL_ROLE.value,
                        "description": "Reveal role only",
                        "available": True
                    }
                ],
                "message": "Conditional mode: Limited reveal options with consent"
            }
    
    def calculate_privacy_level(self, preference: str) -> PrivacyLevel:
        """
        Calculate privacy level based on preference.
        
        Args:
            preference: Identity preference mode
        
        Returns:
            PrivacyLevel enum
        """
        mode = IdentityMode(preference.lower())
        return self.privacy_level_map.get(mode, PrivacyLevel.MEDIUM)
    
    def set_retention_policy(self, preference: str) -> Dict:
        """
        Set data retention policy based on identity preference.
        
        Args:
            preference: Identity preference mode
        
        Returns:
            Dictionary with retention policy details
        """
        mode = IdentityMode(preference.lower())
        retention_days = self.default_retention_days.get(mode, 180)
        
        return {
            "retention_days": retention_days,
            "auto_delete": mode == IdentityMode.ANONYMOUS,
            "anonymize_after": retention_days - 30 if mode == IdentityMode.CONDITIONAL else None,
            "policy_type": mode.value
        }
    
    def handle_identity_reveal(
        self,
        user_id: str,
        reveal_request: Dict,
        survey_id: Optional[int] = None
    ) -> Dict:
        """
        Handle user request to reveal identity.
        
        Args:
            user_id: User email or ID
            reveal_request: Dictionary with reveal parameters:
                - method: Reveal method (full, partial_role, etc.)
                - target: Who to reveal to (optional)
                - consent: Consent confirmation (for consent-based)
                - conditions: Conditions for reveal (optional)
            survey_id: Optional survey ID
        
        Returns:
            Dictionary with reveal decision and details
        """
        try:
            # Verify reveal conditions
            can_reveal = self.verify_reveal_conditions(user_id, reveal_request, survey_id)
            
            if not can_reveal["allowed"]:
                return {
                    "can_reveal": False,
                    "reason": can_reveal.get("reason", "Reveal conditions not met"),
                    "suggestions": can_reveal.get("suggestions", [])
                }
            
            # Determine reveal method
            reveal_method = self.determine_reveal_method(reveal_request)
            
            # Offer partial reveal options if applicable
            partial_reveal = self.offer_partial_reveal_options(reveal_request)
            
            # Process revoke anonymity if requested
            revoke_result = None
            if reveal_request.get("revoke_anonymity", False):
                revoke_result = self.process_revoke_anonymity(user_id, survey_id)
            
            # Execute reveal
            reveal_result = self._execute_reveal(
                user_id,
                reveal_method,
                reveal_request,
                survey_id
            )
            
            return {
                "can_reveal": True,
                "reveal_method": reveal_method.value,
                "partial_reveal": partial_reveal,
                "revoke_anonymity": revoke_result,
                "reveal_executed": reveal_result,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Error handling identity reveal: {e}")
            raise
    
    def verify_reveal_conditions(
        self,
        user_id: str,
        reveal_request: Dict,
        survey_id: Optional[int] = None
    ) -> Dict:
        """
        Verify if reveal conditions are met.
        
        Args:
            user_id: User email or ID
            reveal_request: Reveal request parameters
            survey_id: Optional survey ID
        
        Returns:
            Dictionary with verification result
        """
        # Check if user has anonymous mode
        if self.anonymous_mode and not reveal_request.get("revoke_anonymity", False):
            return {
                "allowed": False,
                "reason": "User is in anonymous mode. Revoke anonymity first.",
                "suggestions": ["Set identity preference to 'identified' or 'conditional'"]
            }
        
        # Check consent for consent-based reveals
        if reveal_request.get("method") == RevealMethod.CONSENT_BASED.value:
            if not reveal_request.get("consent", False):
                return {
                    "allowed": False,
                    "reason": "Explicit consent required for consent-based reveal",
                    "suggestions": ["Provide consent confirmation in reveal_request"]
                }
        
        # Check conditions for conditional reveals
        if self.user_choice == IdentityMode.CONDITIONAL:
            conditions = reveal_request.get("conditions", {})
            if not conditions:
                return {
                    "allowed": False,
                    "reason": "Conditions required for conditional reveal",
                    "suggestions": ["Provide conditions in reveal_request"]
                }
        
        # Check if user exists
        user = self.db.query(Person).filter(Person.email == user_id).first()
        if not user:
            return {
                "allowed": False,
                "reason": "User not found",
                "suggestions": []
            }
        
        return {
            "allowed": True,
            "reason": "All conditions met"
        }
    
    def determine_reveal_method(self, reveal_request: Dict) -> RevealMethod:
        """
        Determine the appropriate reveal method from request.
        
        Args:
            reveal_request: Reveal request parameters
        
        Returns:
            RevealMethod enum
        """
        method_str = reveal_request.get("method", "full")
        
        try:
            return RevealMethod(method_str.lower())
        except ValueError:
            # Default to consent-based for conditional, full for identified
            if self.user_choice == IdentityMode.CONDITIONAL:
                return RevealMethod.CONSENT_BASED
            return RevealMethod.FULL
    
    def offer_partial_reveal_options(self, reveal_request: Dict) -> Dict:
        """
        Offer partial reveal options based on request.
        
        Args:
            reveal_request: Reveal request parameters
        
        Returns:
            Dictionary with partial reveal options
        """
        method = reveal_request.get("method", "")
        
        partial_options = {
            "available": False,
            "options": []
        }
        
        # If method is already partial, return it
        if method in ["partial_role", "partial_department"]:
            partial_options["available"] = True
            partial_options["options"] = [
                {
                    "type": "role",
                    "description": "Reveal role/title only",
                    "available": True
                },
                {
                    "type": "department",
                    "description": "Reveal department only",
                    "available": True
                }
            ]
        
        # If full reveal requested, offer partial alternatives
        elif method == "full" and self.user_choice == IdentityMode.CONDITIONAL:
            partial_options["available"] = True
            partial_options["options"] = [
                {
                    "type": "role",
                    "description": "Reveal role only (recommended)",
                    "available": True
                },
                {
                    "type": "department",
                    "description": "Reveal department only",
                    "available": True
                },
                {
                    "type": "gradual",
                    "description": "Gradual reveal over time",
                    "available": True
                }
            ]
        
        return partial_options
    
    def process_revoke_anonymity(
        self,
        user_id: str,
        survey_id: Optional[int] = None
    ) -> Dict:
        """
        Process request to revoke anonymity and switch to identified/conditional mode.
        
        Args:
            user_id: User email or ID
            survey_id: Optional survey ID
        
        Returns:
            Dictionary with revocation result
        """
        try:
            if not self.anonymous_mode:
                return {
                    "success": False,
                    "message": "User is not in anonymous mode",
                    "current_mode": self.user_choice.value if self.user_choice else "unknown"
                }
            
            # Revoke anonymity
            self.anonymous_mode = False
            
            # Default to conditional mode (safer than full identified)
            new_preference = IdentityMode.CONDITIONAL
            self.user_choice = new_preference
            
            # Update preference in database
            self._store_preference(user_id, new_preference.value, survey_id)
            
            return {
                "success": True,
                "message": "Anonymity revoked successfully",
                "new_mode": new_preference.value,
                "reveal_options": self.get_reveal_options(new_preference.value),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Error revoking anonymity: {e}")
            return {
                "success": False,
                "message": f"Error revoking anonymity: {str(e)}"
            }
    
    def get_identity_status(self, user_id: str, survey_id: Optional[int] = None) -> Dict:
        """
        Get current identity status for a user.
        
        Args:
            user_id: User email or ID
            survey_id: Optional survey ID
        
        Returns:
            Dictionary with current identity status
        """
        # Try to load from database
        preference = self._load_preference(user_id, survey_id)
        
        if preference:
            mode = IdentityMode(preference)
            self.user_choice = mode
            self.anonymous_mode = (mode == IdentityMode.ANONYMOUS)
        else:
            # Default to conditional if no preference set
            mode = IdentityMode.CONDITIONAL
            self.user_choice = mode
            self.anonymous_mode = False
        
        return {
            "user_id": user_id,
            "current_mode": mode.value,
            "anonymous_mode": self.anonymous_mode,
            "privacy_level": self.calculate_privacy_level(mode.value).value,
            "reveal_options": self.get_reveal_options(mode.value),
            "retention_policy": self.set_retention_policy(mode.value)
        }
    
    def _execute_reveal(
        self,
        user_id: str,
        method: RevealMethod,
        reveal_request: Dict,
        survey_id: Optional[int] = None
    ) -> Dict:
        """
        Execute the identity reveal.
        
        Args:
            user_id: User email or ID
            method: Reveal method
            reveal_request: Reveal request parameters
            survey_id: Optional survey ID
        
        Returns:
            Dictionary with reveal execution result
        """
        user = self.db.query(Person).filter(Person.email == user_id).first()
        if not user:
            return {
                "success": False,
                "error": "User not found"
            }
        
        reveal_data = {
            "user_id": user_id,
            "method": method.value,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if method == RevealMethod.FULL:
            reveal_data["revealed_info"] = {
                "email": user.email,
                "full_name": user.full_name,
                "role_title": user.role_title,
                "department": user.department
            }
        
        elif method == RevealMethod.PARTIAL_ROLE:
            reveal_data["revealed_info"] = {
                "role_title": user.role_title
            }
        
        elif method == RevealMethod.PARTIAL_DEPARTMENT:
            reveal_data["revealed_info"] = {
                "department": user.department
            }
        
        elif method == RevealMethod.GRADUAL:
            # Gradual reveal - start with minimal info
            reveal_data["revealed_info"] = {
                "role_title": user.role_title
            }
            reveal_data["next_reveal_date"] = (datetime.utcnow() + timedelta(days=30)).isoformat()
        
        elif method == RevealMethod.CONSENT_BASED:
            reveal_data["revealed_info"] = {
                "email": user.email,
                "full_name": user.full_name,
                "consent_confirmed": reveal_request.get("consent", False)
            }
        
        # Store reveal in database (if table exists)
        self._store_reveal(user_id, reveal_data, survey_id)
        
        return {
            "success": True,
            "reveal_data": reveal_data
        }
    
    def _store_preference(
        self,
        user_id: str,
        preference: str,
        survey_id: Optional[int] = None
    ):
        """Store identity preference in database"""
        try:
            # Check if preference already exists
            query = self.db.query(SurveyIdentityPreference).filter(
                SurveyIdentityPreference.user_email == user_id
            )
            
            if survey_id:
                query = query.filter(SurveyIdentityPreference.survey_id == survey_id)
            else:
                query = query.filter(SurveyIdentityPreference.survey_id.is_(None))
            
            existing = query.first()
            
            # Calculate privacy level and retention
            privacy_level = self.calculate_privacy_level(preference)
            retention = self.set_retention_policy(preference)
            
            if existing:
                # Update existing preference
                existing.identity_mode = preference
                existing.privacy_level = privacy_level.value
                existing.retention_days = retention["retention_days"]
                existing.updated_at = datetime.utcnow()
            else:
                # Create new preference
                new_pref = SurveyIdentityPreference(
                    user_email=user_id,
                    survey_id=survey_id,
                    identity_mode=preference,
                    privacy_level=privacy_level.value,
                    retention_days=retention["retention_days"]
                )
                self.db.add(new_pref)
            
            self.db.commit()
            self.logger.info(
                f"Stored identity preference: user={user_id}, "
                f"preference={preference}, survey_id={survey_id}"
            )
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error storing preference: {e}")
            raise
    
    def _load_preference(
        self,
        user_id: str,
        survey_id: Optional[int] = None
    ) -> Optional[str]:
        """Load identity preference from database"""
        try:
            query = self.db.query(SurveyIdentityPreference).filter(
                SurveyIdentityPreference.user_email == user_id
            )
            
            if survey_id:
                query = query.filter(SurveyIdentityPreference.survey_id == survey_id)
            else:
                query = query.filter(SurveyIdentityPreference.survey_id.is_(None))
            
            preference = query.first()
            return preference.identity_mode if preference else None
        except Exception as e:
            self.logger.error(f"Error loading preference: {e}")
            return None
    
    def _store_reveal(
        self,
        user_id: str,
        reveal_data: Dict,
        survey_id: Optional[int] = None
    ):
        """Store identity reveal in database"""
        try:
            reveal = SurveyIdentityReveal(
                user_email=user_id,
                survey_id=survey_id,
                reveal_method=reveal_data.get("method"),
                revealed_info=reveal_data.get("revealed_info", {}),
                target=reveal_data.get("target"),
                consent_confirmed=reveal_data.get("revealed_info", {}).get("consent_confirmed", False),
                next_reveal_date=datetime.fromisoformat(reveal_data["next_reveal_date"]) if reveal_data.get("next_reveal_date") else None
            )
            self.db.add(reveal)
            self.db.commit()
            self.logger.info(
                f"Stored identity reveal: user={user_id}, "
                f"method={reveal_data.get('method')}, survey_id={survey_id}"
            )
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error storing reveal: {e}")
            # Don't raise - reveal can still proceed even if storage fails
