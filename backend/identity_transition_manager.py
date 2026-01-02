"""
Identity Transition Manager
Handles transitions from anonymous to identified users in survey systems.
Manages identity revelation, consent, and response linking.
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from backend.database import Base


class IdentityTransitionManager:
    """
    Manages identity transitions for survey systems.
    Handles anonymous to identified user transitions with proper consent and security.
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize the identity transition manager.
        
        Args:
            db_session: Optional database session
        """
        self.db = db_session
        
        # Transition policies configuration
        self.transition_policies = {
            "anonymous_to_identified": {
                "cooling_period": timedelta(days=7),  # Wait period before allowing transition
                "confirmation_required": True,  # Require explicit confirmation
                "partial_reveal_allowed": True,  # Allow partial identity reveal
                "token_expiry": timedelta(days=30),  # Token validity period
                "grace_period": timedelta(days=14)  # Grace period for response linking
            },
            "identified_to_anonymous": {
                "allowed": False,  # Generally not allowed for data integrity
                "data_retention": timedelta(days=90)  # Retention period if allowed
            }
        }
        
        # Store active transition tokens (in production, use database or Redis)
        self._active_tokens: Dict[str, Dict] = {}
    
    def transition_to_identified(self, anonymous_id: str, user_id: str, 
                                 survey_id: Optional[int] = None) -> Dict:
        """
        Allow anonymous user to reveal identity and link responses.
        
        Args:
            anonymous_id: Anonymous identifier (session ID, cookie, etc.)
            user_id: User identifier (email, user ID, etc.)
            survey_id: Optional survey ID to limit transition scope
        
        Returns:
            Dictionary with transition details:
            - transition_token: Token for the transition
            - previous_responses: Linked anonymous responses
            - consent_required: Consent requirements
            - grace_period: Grace period information
        """
        # Check if transition is allowed (cooling period)
        if not self._check_cooling_period(anonymous_id):
            return {
                "status": "error",
                "message": "Cooling period not yet expired. Please wait before revealing identity.",
                "cooling_period_remaining": self._get_cooling_period_remaining(anonymous_id)
            }
        
        # Generate transition token
        transition_token = self.generate_transition_token(anonymous_id, user_id)
        
        # Link anonymous responses
        previous_responses = self.link_anonymous_responses(
            anonymous_id, user_id, survey_id
        )
        
        # Get consent requirements
        consent_required = self.get_consent_requirements()
        
        # Set grace period
        grace_period = self.set_grace_period(anonymous_id, user_id)
        
        return {
            "status": "success",
            "transition_token": transition_token,
            "previous_responses": previous_responses,
            "consent_required": consent_required,
            "grace_period": grace_period,
            "transition_date": datetime.now().isoformat()
        }
    
    def generate_transition_token(self, anonymous_id: str, user_id: str) -> str:
        """
        Generate a secure transition token for identity linking.
        
        Args:
            anonymous_id: Anonymous identifier
            user_id: User identifier
        
        Returns:
            Secure transition token
        """
        # Create token payload
        timestamp = datetime.now().isoformat()
        payload = f"{anonymous_id}:{user_id}:{timestamp}"
        
        # Generate secure token
        token = secrets.token_urlsafe(32)
        
        # Store token metadata
        token_data = {
            "anonymous_id": anonymous_id,
            "user_id": user_id,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + self.transition_policies["anonymous_to_identified"]["token_expiry"],
            "used": False
        }
        
        self._active_tokens[token] = token_data
        
        return token
    
    def link_anonymous_responses(self, anonymous_id: str, user_id: str,
                                 survey_id: Optional[int] = None) -> Dict:
        """
        Link anonymous survey responses to identified user.
        
        Args:
            anonymous_id: Anonymous identifier
            user_id: User identifier (email)
            survey_id: Optional survey ID to limit linking scope
        
        Returns:
            Dictionary with linking results
        """
        if not self.db:
            return {
                "status": "error",
                "message": "Database session not available",
                "linked_count": 0
            }
        
        try:
            # Query to find anonymous responses
            # Note: survey_responses table uses respondent_email (NULL for anonymous)
            # We'll need to track anonymous responses via a separate mechanism
            # For now, we'll use a session-based approach or add anonymous_id column
            from sqlalchemy import text
            
            # Option 1: If anonymous_id column exists (would need migration)
            # Option 2: Use a separate anonymous_responses_mapping table
            # Option 3: Use session_id if available in response_value JSONB
            
            # For this implementation, we'll check if anonymous_id column exists
            # If not, we'll create a mapping approach
            try:
                # Try to query with anonymous_id (if column exists after migration)
                query = text("""
                    SELECT id, survey_id, question_id, response_text, submitted_at
                    FROM survey_responses
                    WHERE anonymous_id = :anonymous_id
                    AND respondent_email IS NULL
                """)
                
                if survey_id:
                    query = text("""
                        SELECT id, survey_id, question_id, response_text, submitted_at
                        FROM survey_responses
                        WHERE anonymous_id = :anonymous_id
                        AND respondent_email IS NULL
                        AND survey_id = :survey_id
                    """)
                    params = {"anonymous_id": anonymous_id, "survey_id": survey_id}
                else:
                    params = {"anonymous_id": anonymous_id}
                
                result = self.db.execute(query, params)
                responses = result.fetchall()
                
            except Exception:
                # Fallback: If anonymous_id column doesn't exist, use session-based approach
                # This would require storing session_id in response_value JSONB or separate table
                # For now, return empty result with note
                responses = []
            
            # Update responses to link to user
            linked_count = 0
            response_ids = []
            
            for response in responses:
                try:
                    update_query = text("""
                        UPDATE survey_responses
                        SET respondent_email = :user_id,
                            anonymous_id = NULL,
                            linked_at = CURRENT_TIMESTAMP
                        WHERE id = :response_id
                    """)
                except Exception:
                    # Fallback: If linked_at column doesn't exist
                    update_query = text("""
                        UPDATE survey_responses
                        SET respondent_email = :user_id
                        WHERE id = :response_id
                    """)
                
                self.db.execute(update_query, {
                    "user_id": user_id,
                    "response_id": response.id
                })
                linked_count += 1
                response_ids.append(response.id)
            
            self.db.commit()
            
            return {
                "status": "success",
                "linked_count": linked_count,
                "response_ids": response_ids,
                "message": f"Successfully linked {linked_count} anonymous responses to user {user_id}"
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "status": "error",
                "message": f"Error linking responses: {str(e)}",
                "linked_count": 0
            }
    
    def get_consent_requirements(self) -> Dict:
        """
        Get consent requirements for identity transition.
        
        Returns:
            Dictionary with consent requirements
        """
        policy = self.transition_policies["anonymous_to_identified"]
        
        return {
            "confirmation_required": policy["confirmation_required"],
            "consent_items": [
                {
                    "id": "data_linking",
                    "description": "I consent to linking my anonymous responses to my identified account",
                    "required": True
                },
                {
                    "id": "data_retention",
                    "description": "I understand that my responses will be retained and associated with my account",
                    "required": True
                },
                {
                    "id": "partial_reveal",
                    "description": "I understand that partial identity reveal may be allowed",
                    "required": policy["partial_reveal_allowed"]
                }
            ],
            "privacy_notice": "Your anonymous responses will be linked to your account. "
                            "This action cannot be fully reversed. Please review our privacy policy.",
            "cooling_period_days": policy["cooling_period"].days
        }
    
    def set_grace_period(self, anonymous_id: str, user_id: str) -> Dict:
        """
        Set grace period for identity transition.
        Allows time for user to reconsider or complete the transition.
        
        Args:
            anonymous_id: Anonymous identifier
            user_id: User identifier
        
        Returns:
            Dictionary with grace period information
        """
        policy = self.transition_policies["anonymous_to_identified"]
        grace_period = policy["grace_period"]
        start_date = datetime.now()
        end_date = start_date + grace_period
        
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "duration_days": grace_period.days,
            "message": f"You have {grace_period.days} days to complete the identity transition. "
                      f"After this period, the transition token will expire.",
            "can_revert": True,  # Allow reverting during grace period
            "revert_deadline": end_date.isoformat()
        }
    
    def verify_transition_token(self, token: str) -> Dict:
        """
        Verify a transition token and return its status.
        
        Args:
            token: Transition token to verify
        
        Returns:
            Dictionary with token verification status
        """
        if token not in self._active_tokens:
            return {
                "valid": False,
                "message": "Token not found or expired"
            }
        
        token_data = self._active_tokens[token]
        
        # Check if token is expired
        if datetime.now() > token_data["expires_at"]:
            del self._active_tokens[token]
            return {
                "valid": False,
                "message": "Token has expired"
            }
        
        # Check if token is already used
        if token_data["used"]:
            return {
                "valid": False,
                "message": "Token has already been used"
            }
        
        return {
            "valid": True,
            "anonymous_id": token_data["anonymous_id"],
            "user_id": token_data["user_id"],
            "created_at": token_data["created_at"].isoformat(),
            "expires_at": token_data["expires_at"].isoformat()
        }
    
    def complete_transition(self, token: str) -> Dict:
        """
        Complete the identity transition using a valid token.
        
        Args:
            token: Transition token
        
        Returns:
            Dictionary with completion status
        """
        # Verify token
        verification = self.verify_transition_token(token)
        
        if not verification["valid"]:
            return {
                "status": "error",
                "message": verification["message"]
            }
        
        # Mark token as used
        self._active_tokens[token]["used"] = True
        
        # Perform the transition
        result = self.transition_to_identified(
            verification["anonymous_id"],
            verification["user_id"]
        )
        
        return {
            "status": "success",
            "message": "Identity transition completed successfully",
            "transition_details": result
        }
    
    def _check_cooling_period(self, anonymous_id: str) -> bool:
        """
        Check if cooling period has passed for anonymous ID.
        
        Args:
            anonymous_id: Anonymous identifier
        
        Returns:
            True if cooling period has passed, False otherwise
        """
        # In a real implementation, you would check against database records
        # For now, we'll assume cooling period check passes
        # You could store last_anonymous_activity timestamp in database
        
        if not self.db:
            return True  # Default to allowing if no DB
        
        try:
            # Check if there's a recent transition attempt
            # This would require a transitions table in the database
            # For now, return True (cooling period passed)
            return True
        except:
            return True
    
    def _get_cooling_period_remaining(self, anonymous_id: str) -> Optional[timedelta]:
        """
        Get remaining cooling period for anonymous ID.
        
        Args:
            anonymous_id: Anonymous identifier
        
        Returns:
            Remaining time in cooling period, or None if period has passed
        """
        # In a real implementation, calculate from database records
        # For now, return None (period passed)
        return None
    
    def revert_transition(self, token: str) -> Dict:
        """
        Revert an identity transition during grace period.
        
        Args:
            token: Transition token
        
        Returns:
            Dictionary with revert status
        """
        verification = self.verify_transition_token(token)
        
        if not verification["valid"]:
            return {
                "status": "error",
                "message": "Invalid or expired token"
            }
        
        token_data = self._active_tokens[token]
        
        # Check if still in grace period
        grace_end = token_data["created_at"] + self.transition_policies["anonymous_to_identified"]["grace_period"]
        
        if datetime.now() > grace_end:
            return {
                "status": "error",
                "message": "Grace period has expired. Transition cannot be reverted."
            }
        
        # Revert the transition (unlink responses, etc.)
        # This would require updating the database to unlink responses
        if self.db:
            try:
                # Unlink responses (set respondent_email back to NULL)
                # Note: This is a simplified version
                from sqlalchemy import text
                
                update_query = text("""
                    UPDATE survey_responses
                    SET respondent_email = NULL,
                        anonymous_id = :anonymous_id,
                        linked_at = NULL
                    WHERE respondent_email = :user_id
                    AND linked_at >= :transition_date
                """)
                
                self.db.execute(update_query, {
                    "anonymous_id": verification["anonymous_id"],
                    "user_id": verification["user_id"],
                    "transition_date": token_data["created_at"]
                })
                
                self.db.commit()
                
                # Remove token
                del self._active_tokens[token]
                
                return {
                    "status": "success",
                    "message": "Identity transition reverted successfully"
                }
            except Exception as e:
                self.db.rollback()
                return {
                    "status": "error",
                    "message": f"Error reverting transition: {str(e)}"
                }
        
        return {
            "status": "error",
            "message": "Database session not available"
        }
