"""
Conditional Anonymity Engine for Hybrid Identity Survey System.
Handles conditional reveal scenarios with trigger events and notification rules.
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set

from sqlalchemy.orm import Session

from backend.database import Person, SurveyConditionalReveal, SurveyIdentityPreference, SurveyIdentityReveal


class RevealTrigger(Enum):
    """Trigger events for conditional reveals"""

    SURVEY_COMPLETED = "survey_completed"
    COOLING_PERIOD_PASSED = "cooling_period_passed"
    TIME_BASED = "time_based"
    MANUAL_REQUEST = "manual_request"
    CONSENT_RECEIVED = "consent_received"
    ADMIN_APPROVAL = "admin_approval"


class NotificationRule(Enum):
    """Notification rules for reveals"""

    BEFORE_REVEAL = "before_reveal"
    AFTER_REVEAL = "after_reveal"
    ON_CONDITION_MET = "on_condition_met"
    REMINDER = "reminder"


class ConditionalAnonymityEngine:
    """
    Conditional Anonymity Engine for processing conditional reveal preferences.
    Manages reveal conditions, trigger events, and notification rules.
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)

        # Default conditions configuration
        self.conditions = {
            "reveal_after_survey": {
                "enabled": True,
                "conditions": ["survey_completed", "cooling_period_passed"],
                "cooling_period_days": 7,  # Default 7-day cooling period
                "auto_reveal": False,  # Require explicit confirmation
            },
            "reveal_to_specific_people": {
                "enabled": True,
                "recipients": ["hr_manager", "principal"],
                "partial_reveal": True,
                "require_consent": True,
            },
            "time_based_reveal": {"enabled": False, "reveal_after_days": 30, "gradual": True},
            "consent_based_reveal": {"enabled": True, "require_explicit_consent": True, "consent_expiry_days": 90},
        }

        # Default cooling periods for different scenarios
        self.cooling_periods = {
            "default": 7,  # 7 days
            "sensitive": 14,  # 14 days for sensitive surveys
            "performance": 30,  # 30 days for performance reviews
            "anonymous": 0,  # No cooling period for anonymous mode
        }

    def process_conditional_reveal(self, user_id: str, user_choice: Dict, survey_id: Optional[int] = None) -> Dict:
        """
        Process user conditional reveal preferences.

        Args:
            user_id: User email or ID
            user_choice: Dictionary with conditional reveal preferences:
                - reveal_after_survey: Enable reveal after survey completion
                - reveal_to_specific_people: List of people to reveal to
                - time_based_reveal: Time-based reveal settings
                - consent_based_reveal: Consent-based reveal settings
            survey_id: Optional survey ID

        Returns:
            Dictionary with reveal conditions, trigger events, and notification preferences
        """
        try:
            # Validate conditions
            validated_conditions = self.validate_conditions(user_id, user_choice, survey_id)

            # Set trigger events
            trigger_events = self.set_trigger_events(user_id, user_choice, survey_id)

            # Set notification rules
            notification_preferences = self.set_notification_rules(user_id, user_choice, survey_id)

            # Store conditional reveal configuration
            self._store_conditional_config(user_id, validated_conditions, trigger_events, survey_id)

            return {
                "reveal_conditions": validated_conditions,
                "trigger_events": trigger_events,
                "notification_preferences": notification_preferences,
                "status": "configured",
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error processing conditional reveal: {e}")
            raise

    def validate_conditions(self, user_id: str, user_choice: Dict, survey_id: Optional[int] = None) -> Dict:
        """
        Validate conditional reveal conditions.

        Args:
            user_id: User email or ID
            user_choice: User's conditional reveal preferences
            survey_id: Optional survey ID

        Returns:
            Dictionary with validated conditions
        """
        validated = {"valid": True, "errors": [], "warnings": [], "conditions": {}}

        # Validate reveal_after_survey
        if user_choice.get("reveal_after_survey", {}).get("enabled", False):
            reveal_after = user_choice["reveal_after_survey"]
            cooling_days = reveal_after.get("cooling_period_days", self.cooling_periods["default"])

            if cooling_days < 0:
                validated["errors"].append("Cooling period cannot be negative")
                validated["valid"] = False
            elif cooling_days > 365:
                validated["warnings"].append("Cooling period exceeds 1 year")

            validated["conditions"]["reveal_after_survey"] = {
                "enabled": True,
                "cooling_period_days": cooling_days,
                "auto_reveal": reveal_after.get("auto_reveal", False),
                "conditions": ["survey_completed", "cooling_period_passed"],
            }

        # Validate reveal_to_specific_people
        if user_choice.get("reveal_to_specific_people", {}).get("enabled", False):
            reveal_to = user_choice["reveal_to_specific_people"]
            recipients = reveal_to.get("recipients", [])

            if not recipients:
                validated["errors"].append("No recipients specified for reveal")
                validated["valid"] = False
            else:
                # Validate recipient emails/roles
                valid_recipients = []
                for recipient in recipients:
                    if self._validate_recipient(recipient):
                        valid_recipients.append(recipient)
                    else:
                        validated["warnings"].append(f"Invalid recipient: {recipient}")

                if not valid_recipients:
                    validated["errors"].append("No valid recipients found")
                    validated["valid"] = False
                else:
                    validated["conditions"]["reveal_to_specific_people"] = {
                        "enabled": True,
                        "recipients": valid_recipients,
                        "partial_reveal": reveal_to.get("partial_reveal", True),
                        "require_consent": reveal_to.get("require_consent", True),
                    }

        # Validate time_based_reveal
        if user_choice.get("time_based_reveal", {}).get("enabled", False):
            time_based = user_choice["time_based_reveal"]
            reveal_after_days = time_based.get("reveal_after_days", 30)

            if reveal_after_days < 1:
                validated["errors"].append("Time-based reveal must be at least 1 day")
                validated["valid"] = False

            validated["conditions"]["time_based_reveal"] = {
                "enabled": True,
                "reveal_after_days": reveal_after_days,
                "gradual": time_based.get("gradual", False),
                "reveal_date": (datetime.utcnow() + timedelta(days=reveal_after_days)).isoformat(),
            }

        # Validate consent_based_reveal
        if user_choice.get("consent_based_reveal", {}).get("enabled", False):
            consent_based = user_choice["consent_based_reveal"]

            validated["conditions"]["consent_based_reveal"] = {
                "enabled": True,
                "require_explicit_consent": consent_based.get("require_explicit_consent", True),
                "consent_expiry_days": consent_based.get("consent_expiry_days", 90),
            }

        return validated

    def set_trigger_events(self, user_id: str, user_choice: Dict, survey_id: Optional[int] = None) -> Dict:
        """
        Set trigger events for conditional reveals.

        Args:
            user_id: User email or ID
            user_choice: User's conditional reveal preferences
            survey_id: Optional survey ID

        Returns:
            Dictionary with configured trigger events
        """
        triggers = {"active_triggers": [], "trigger_config": {}}

        # Survey completion trigger
        if user_choice.get("reveal_after_survey", {}).get("enabled", False):
            reveal_after = user_choice["reveal_after_survey"]
            cooling_days = reveal_after.get("cooling_period_days", self.cooling_periods["default"])

            triggers["active_triggers"].append(RevealTrigger.SURVEY_COMPLETED.value)
            triggers["active_triggers"].append(RevealTrigger.COOLING_PERIOD_PASSED.value)

            triggers["trigger_config"]["survey_completion"] = {
                "trigger": RevealTrigger.SURVEY_COMPLETED.value,
                "survey_id": survey_id,
                "next_trigger": RevealTrigger.COOLING_PERIOD_PASSED.value,
                "cooling_period_days": cooling_days,
                "auto_reveal": reveal_after.get("auto_reveal", False),
            }

        # Time-based trigger
        if user_choice.get("time_based_reveal", {}).get("enabled", False):
            time_based = user_choice["time_based_reveal"]
            reveal_after_days = time_based.get("reveal_after_days", 30)

            triggers["active_triggers"].append(RevealTrigger.TIME_BASED.value)

            triggers["trigger_config"]["time_based"] = {
                "trigger": RevealTrigger.TIME_BASED.value,
                "reveal_date": (datetime.utcnow() + timedelta(days=reveal_after_days)).isoformat(),
                "days_remaining": reveal_after_days,
                "gradual": time_based.get("gradual", False),
            }

        # Consent-based trigger
        if user_choice.get("consent_based_reveal", {}).get("enabled", False):
            triggers["active_triggers"].append(RevealTrigger.CONSENT_RECEIVED.value)

            triggers["trigger_config"]["consent_based"] = {
                "trigger": RevealTrigger.CONSENT_RECEIVED.value,
                "require_explicit_consent": True,
                "consent_expiry_days": user_choice.get("consent_based_reveal", {}).get("consent_expiry_days", 90),
            }

        # Manual request trigger (always available)
        triggers["active_triggers"].append(RevealTrigger.MANUAL_REQUEST.value)

        return triggers

    def set_notification_rules(self, user_id: str, user_choice: Dict, survey_id: Optional[int] = None) -> Dict:
        """
        Set notification rules for conditional reveals.

        Args:
            user_id: User email or ID
            user_choice: User's conditional reveal preferences
            survey_id: Optional survey ID

        Returns:
            Dictionary with notification preferences
        """
        notification_prefs = {"rules": [], "preferences": {}}

        # Before reveal notification
        if user_choice.get("notify_before_reveal", True):
            notification_prefs["rules"].append(NotificationRule.BEFORE_REVEAL.value)
            notification_prefs["preferences"]["before_reveal"] = {
                "enabled": True,
                "days_before": user_choice.get("notify_days_before", 1),
                "message": "Your identity will be revealed in {days} day(s). You can change your preference.",
            }

        # After reveal notification
        if user_choice.get("notify_after_reveal", True):
            notification_prefs["rules"].append(NotificationRule.AFTER_REVEAL.value)
            notification_prefs["preferences"]["after_reveal"] = {
                "enabled": True,
                "message": "Your identity has been revealed as per your conditional settings.",
            }

        # On condition met notification
        if user_choice.get("notify_on_condition_met", True):
            notification_prefs["rules"].append(NotificationRule.ON_CONDITION_MET.value)
            notification_prefs["preferences"]["on_condition_met"] = {
                "enabled": True,
                "message": "Conditional reveal condition has been met. Processing reveal...",
            }

        # Reminder notifications
        if user_choice.get("enable_reminders", False):
            notification_prefs["rules"].append(NotificationRule.REMINDER.value)
            notification_prefs["preferences"]["reminders"] = {
                "enabled": True,
                "frequency": user_choice.get("reminder_frequency", "weekly"),
                "message": "Reminder: Your conditional reveal settings are active.",
            }

        return notification_prefs

    def check_trigger_conditions(self, user_id: str, survey_id: Optional[int] = None) -> Dict:
        """
        Check if any trigger conditions have been met.

        Args:
            user_id: User email or ID
            survey_id: Optional survey ID

        Returns:
            Dictionary with trigger status and actions to take
        """
        # Load conditional configuration
        config = self._load_conditional_config(user_id, survey_id)

        if not config:
            return {"triggers_met": [], "actions_required": [], "status": "no_config"}

        triggers_met = []
        actions_required = []

        # Check survey completion trigger
        if config.get("reveal_after_survey", {}).get("enabled", False):
            survey_completed = self._check_survey_completion(user_id, survey_id)
            if survey_completed:
                cooling_period = config["reveal_after_survey"]["cooling_period_days"]
                cooling_passed = self._check_cooling_period(user_id, survey_id, cooling_period)

                if cooling_passed:
                    triggers_met.append(RevealTrigger.COOLING_PERIOD_PASSED.value)
                    if config["reveal_after_survey"].get("auto_reveal", False):
                        actions_required.append("auto_reveal")
                    else:
                        actions_required.append("request_confirmation")

        # Check time-based trigger
        if config.get("time_based_reveal", {}).get("enabled", False):
            reveal_date = datetime.fromisoformat(config["time_based_reveal"]["reveal_date"])
            if datetime.utcnow() >= reveal_date:
                triggers_met.append(RevealTrigger.TIME_BASED.value)
                actions_required.append("time_based_reveal")

        return {
            "triggers_met": triggers_met,
            "actions_required": actions_required,
            "status": "active" if triggers_met else "pending",
        }

    def execute_conditional_reveal(self, user_id: str, trigger: RevealTrigger, survey_id: Optional[int] = None) -> Dict:
        """
        Execute conditional reveal based on trigger.

        Args:
            user_id: User email or ID
            trigger: Trigger that activated the reveal
            survey_id: Optional survey ID

        Returns:
            Dictionary with reveal execution result
        """
        config = self._load_conditional_config(user_id, survey_id)

        if not config:
            return {"success": False, "error": "No conditional reveal configuration found"}

        # Determine reveal method based on configuration
        reveal_method = "consent_based"  # Default

        if config.get("reveal_to_specific_people", {}).get("enabled", False):
            reveal_to = config["reveal_to_specific_people"]
            recipients = reveal_to.get("recipients", [])
            partial = reveal_to.get("partial_reveal", True)

            # Reveal to specific recipients
            reveal_results = []
            for recipient in recipients:
                result = self._reveal_to_recipient(user_id, recipient, partial=partial, survey_id=survey_id)
                reveal_results.append(result)

            return {
                "success": True,
                "trigger": trigger.value,
                "reveal_method": "partial" if partial else "full",
                "recipients": recipients,
                "results": reveal_results,
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Default reveal
        return {
            "success": True,
            "trigger": trigger.value,
            "reveal_method": reveal_method,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _validate_recipient(self, recipient: str) -> bool:
        """Validate recipient (email or role)"""
        # Check if it's an email
        if "@" in recipient:
            person = self.db.query(Person).filter(Person.email == recipient).first()
            return person is not None

        # Check if it's a valid role
        valid_roles = ["hr_manager", "principal", "ceo", "pnc", "qa"]
        return recipient.lower() in valid_roles

    def _check_survey_completion(self, user_id: str, survey_id: Optional[int]) -> bool:
        """Check if survey is completed by user"""
        try:
            from sqlalchemy import text

            # Check if user has responses for all required questions
            query = text(
                """
                SELECT COUNT(DISTINCT sq.id) as total_required,
                       COUNT(DISTINCT sr.question_id) FILTER (WHERE sq.is_required = true) as answered_required
                FROM survey_questions sq
                LEFT JOIN survey_responses sr ON sq.id = sr.question_id AND sr.respondent_email = :user_id
                WHERE sq.survey_id = :survey_id
            """
            )
            result = self.db.execute(query, {"user_id": user_id, "survey_id": survey_id}).fetchone()

            if result:
                total_required = result[0] or 0
                answered_required = result[1] or 0
                return total_required > 0 and answered_required == total_required

            return False
        except Exception as e:
            self.logger.error(f"Error checking survey completion: {e}")
            return False

    def _check_cooling_period(self, user_id: str, survey_id: Optional[int], cooling_days: int) -> bool:
        """Check if cooling period has passed"""
        try:
            from sqlalchemy import text

            # Get the latest survey response submission date
            query = text(
                """
                SELECT MAX(submitted_at) as last_submission
                FROM survey_responses
                WHERE respondent_email = :user_id AND survey_id = :survey_id
            """
            )
            result = self.db.execute(query, {"user_id": user_id, "survey_id": survey_id}).fetchone()

            if result and result[0]:
                last_submission = result[0]
                if isinstance(last_submission, str):
                    try:
                        last_submission = datetime.fromisoformat(last_submission.replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        # Fallback for other date formats
                        last_submission = datetime.utcnow()

                # Ensure last_submission is timezone-aware or naive datetime
                if last_submission.tzinfo is None:
                    # Assume UTC if naive
                    days_passed = (datetime.utcnow() - last_submission).days
                else:
                    # Convert to UTC for comparison
                    from datetime import timezone

                    days_passed = (datetime.now(timezone.utc) - last_submission).days

                return days_passed >= cooling_days

            return False
        except Exception as e:
            self.logger.error(f"Error checking cooling period: {e}")
            return False

    def _store_conditional_config(self, user_id: str, conditions: Dict, triggers: Dict, survey_id: Optional[int] = None):
        """Store conditional reveal configuration"""
        try:
            # Check if config already exists
            query = self.db.query(SurveyConditionalReveal).filter(SurveyConditionalReveal.user_email == user_id)

            if survey_id:
                query = query.filter(SurveyConditionalReveal.survey_id == survey_id)
            else:
                query = query.filter(SurveyConditionalReveal.survey_id.is_(None))

            existing = query.first()

            if existing:
                # Update existing config
                existing.reveal_conditions = conditions
                existing.trigger_events = triggers
                existing.updated_at = datetime.utcnow()
            else:
                # Create new config
                new_config = SurveyConditionalReveal(
                    user_email=user_id,
                    survey_id=survey_id,
                    reveal_conditions=conditions,
                    trigger_events=triggers,
                    status="active",
                )
                self.db.add(new_config)

            self.db.commit()
            self.logger.info(
                f"Stored conditional config: user={user_id}, "
                f"survey_id={survey_id}, triggers={triggers.get('active_triggers', [])}"
            )
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error storing conditional config: {e}")
            raise

    def _load_conditional_config(self, user_id: str, survey_id: Optional[int] = None) -> Optional[Dict]:
        """Load conditional reveal configuration"""
        try:
            query = self.db.query(SurveyConditionalReveal).filter(
                SurveyConditionalReveal.user_email == user_id, SurveyConditionalReveal.status == "active"
            )

            if survey_id:
                query = query.filter(SurveyConditionalReveal.survey_id == survey_id)
            else:
                query = query.filter(SurveyConditionalReveal.survey_id.is_(None))

            config = query.first()

            if config:
                return {
                    **config.reveal_conditions.get("conditions", {}),
                    "trigger_events": config.trigger_events,
                    "notification_preferences": config.notification_preferences,
                }

            return None
        except Exception as e:
            self.logger.error(f"Error loading conditional config: {e}")
            return None

    def _reveal_to_recipient(
        self, user_id: str, recipient: str, partial: bool = True, survey_id: Optional[int] = None
    ) -> Dict:
        """Reveal identity to a specific recipient"""
        user = self.db.query(Person).filter(Person.email == user_id).first()
        if not user:
            return {"success": False, "error": "User not found"}

        if partial:
            revealed_info = {"role_title": user.role_title, "department": user.department}
        else:
            revealed_info = {
                "email": user.email,
                "full_name": user.full_name,
                "role_title": user.role_title,
                "department": user.department,
            }

        return {"success": True, "recipient": recipient, "revealed_info": revealed_info, "partial": partial}
