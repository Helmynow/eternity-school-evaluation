"""
Smart Notification System for Eternity School Evaluation System.
Automatically sends notifications based on rules and user preferences.
Includes smart reminders based on user behavior and escalation alerts.
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, time
from collections import defaultdict
import logging
import statistics
from backend.database import Person, EmailNotification, Evaluation, Assignment, Cycle
from backend.email_service import EmailService


class SmartNotificationSystem:
    """
    Smart notification system that automatically sends notifications
    based on rules and user preferences, avoiding spam.
    """
    
    message_templates = {
        "bias_detected": "Potential bias detected in evaluation for {employee_name}. Please review the evaluation.",
        "insufficient_raters": "Insufficient raters for {target_group}. Minimum required: {min_required}, current: {current_count}.",
        "deadline_approaching": "Deadline approaching for {task}. Due date: {deadline}.",
        "nomination_submitted": "New EOM nomination submitted for {nominee_name} in {category} category.",
        "evaluation_submitted": "New evaluation submitted for {target_name} by {rater_name}.",
        "variance_alert": "Variance alert: Evaluation score for {target_name} shows ≥2pt spread from average.",
        "eom_winner_announced": "Congratulations! {winner_name} has been selected as Employee of the Month in {category} category.",
        "nomination_window_opening": "EOM nomination window opens on {opening_date}. Nominations close on {closing_date}.",
        "nomination_window_closing": "EOM nomination window closes in {days_remaining} day(s). Submit nominations before {closing_date}.",
        "cycle_started": "New evaluation cycle '{cycle_name}' has started. Deadline: {deadline}.",
        "cycle_ending": "Evaluation cycle '{cycle_name}' ends in {days_remaining} day(s). Complete your evaluations before {deadline}.",
        "evaluation_overdue": "⚠️ URGENT: Evaluation for {target_name} is overdue by {days_overdue} day(s). Please complete immediately.",
        "evaluation_overdue_escalation": "🚨 ESCALATION: Evaluation for {target_name} is {days_overdue} days overdue. Manager notified.",
        "smart_reminder": "Reminder: You have {pending_count} pending evaluation(s). Based on your typical completion time, now is a good time to complete them.",
        "evaluation_due_soon": "Evaluation for {target_name} is due in {days_remaining} day(s). Complete it at your convenience."
    }
    
    def __init__(self, db_session):
        self.db = db_session
        self.email_service = EmailService()
        self.logger = logging.getLogger(__name__)
        
        # Default notification preferences
        self.default_preferences = {
            "bias_detected": {"enabled": True, "frequency": "immediate", "quiet_hours": (22, 8)},
            "insufficient_raters": {"enabled": True, "frequency": "daily", "quiet_hours": (22, 8)},
            "deadline_approaching": {"enabled": True, "frequency": "daily", "quiet_hours": (22, 8)},
            "nomination_submitted": {"enabled": True, "frequency": "immediate", "quiet_hours": (22, 8)},
            "evaluation_submitted": {"enabled": False, "frequency": "daily", "quiet_hours": (22, 8)},
            "variance_alert": {"enabled": True, "frequency": "immediate", "quiet_hours": (22, 8)},
            "eom_winner_announced": {"enabled": True, "frequency": "immediate", "quiet_hours": None},
            "nomination_window_opening": {"enabled": True, "frequency": "immediate", "quiet_hours": (22, 8)},
            "nomination_window_closing": {"enabled": True, "frequency": "daily", "quiet_hours": (22, 8)},
            "cycle_started": {"enabled": True, "frequency": "immediate", "quiet_hours": (22, 8)},
            "cycle_ending": {"enabled": True, "frequency": "daily", "quiet_hours": (22, 8)},
            "evaluation_overdue": {"enabled": True, "frequency": "daily", "quiet_hours": None},
            "evaluation_overdue_escalation": {"enabled": True, "frequency": "daily", "quiet_hours": None},
            "smart_reminder": {"enabled": True, "frequency": "daily", "quiet_hours": (22, 8)},
            "evaluation_due_soon": {"enabled": True, "frequency": "daily", "quiet_hours": (22, 8)}
        }
    
    def should_notify(
        self,
        event_type: str,
        user_id: str,
        context: Optional[Dict] = None
    ) -> bool:
        """
        Smart logic to determine if a notification should be sent.
        Avoids spam by checking user preferences, notification history, and quiet hours.
        
        Args:
            event_type: Type of notification event
            user_id: User email or ID
            context: Additional context for the notification
        
        Returns:
            True if notification should be sent, False otherwise
        """
        # Get user preferences
        user_prefs = self.get_user_preferences(user_id)
        
        # Check if notification type is enabled for this user
        if not user_prefs.get(event_type, {}).get("enabled", True):
            return False
        
        # Check quiet hours
        if self._is_quiet_hours(event_type, user_prefs):
            self.logger.info(f"Quiet hours active for {event_type}, notification deferred")
            return False
        
        # Get last notification of this type
        last_notification = self.get_last_notification(user_id, event_type)
        
        if last_notification:
            # Check frequency limits
            frequency = user_prefs.get(event_type, {}).get("frequency", "immediate")
            time_since_last = datetime.utcnow() - last_notification.sent_at
            
            if frequency == "daily" and time_since_last < timedelta(hours=24):
                self.logger.info(f"Daily limit reached for {event_type}, notification skipped")
                return False
            elif frequency == "weekly" and time_since_last < timedelta(days=7):
                self.logger.info(f"Weekly limit reached for {event_type}, notification skipped")
                return False
            elif frequency == "immediate":
                # For immediate notifications, check if it's a duplicate
                if self._is_duplicate_notification(user_id, event_type, context, last_notification):
                    self.logger.info(f"Duplicate notification detected for {event_type}, skipped")
                    return False
        
        return True
    
    def get_user_preferences(self, user_id: str) -> Dict:
        """
        Get user notification preferences.
        Falls back to default preferences if user preferences not found.
        
        Args:
            user_id: User email or ID
        
        Returns:
            Dictionary of user preferences
        """
        # In a real implementation, this would fetch from a user_preferences table
        # For now, return default preferences
        return self.default_preferences.copy()
    
    def get_last_notification(
        self,
        user_id: str,
        event_type: str
    ) -> Optional[EmailNotification]:
        """
        Get the last notification sent to a user for a specific event type.
        
        Args:
            user_id: User email or ID
            event_type: Type of notification event
        
        Returns:
            Last EmailNotification or None
        """
        return self.db.query(EmailNotification).filter(
            EmailNotification.recipient_email == user_id,
            EmailNotification.notification_type == event_type,
            EmailNotification.status == 'sent'
        ).order_by(EmailNotification.sent_at.desc()).first()
    
    def _is_quiet_hours(self, event_type: str, user_prefs: Dict) -> bool:
        """
        Check if current time is within quiet hours for the notification type.
        
        Args:
            event_type: Type of notification
            user_prefs: User preferences
        
        Returns:
            True if within quiet hours, False otherwise
        """
        quiet_hours = user_prefs.get(event_type, {}).get("quiet_hours")
        
        if quiet_hours is None:
            return False
        
        if isinstance(quiet_hours, tuple) and len(quiet_hours) == 2:
            start_hour, end_hour = quiet_hours
            current_hour = datetime.utcnow().hour
            
            if start_hour > end_hour:  # Spans midnight
                return current_hour >= start_hour or current_hour < end_hour
            else:
                return start_hour <= current_hour < end_hour
        
        return False
    
    def _is_duplicate_notification(
        self,
        user_id: str,
        event_type: str,
        context: Optional[Dict],
        last_notification: EmailNotification
    ) -> bool:
        """
        Check if this notification is a duplicate of the last one.
        
        Args:
            user_id: User email or ID
            event_type: Type of notification
            context: Current notification context
            last_notification: Last notification sent
        
        Returns:
            True if duplicate, False otherwise
        """
        if not context or not last_notification:
            return False
        
        # Check if same entity (e.g., same evaluation, same cycle)
        if last_notification.related_entity_type and last_notification.related_entity_id:
            if (context.get("related_entity_type") == last_notification.related_entity_type and
                context.get("related_entity_id") == last_notification.related_entity_id):
                # Same entity, check time window (within 1 hour = duplicate)
                time_diff = datetime.utcnow() - last_notification.sent_at
                if time_diff < timedelta(hours=1):
                    return True
        
        return False
    
    def send_notification(
        self,
        event_type: str,
        recipients: List[str],
        context: Dict,
        priority: str = "normal"
    ) -> Dict:
        """
        Send notification to recipients if they should receive it.
        
        Args:
            event_type: Type of notification event
            recipients: List of recipient emails
            context: Context data for message template
            priority: Notification priority (low, normal, high, urgent)
        
        Returns:
            Dictionary with send results
        """
        template = self.message_templates.get(event_type)
        if not template:
            self.logger.warning(f"No template found for event type: {event_type}")
            return {"success": False, "error": "Template not found"}
        
        # Format message
        try:
            message = template.format(**context)
        except KeyError as e:
            self.logger.error(f"Missing context key for template: {e}")
            return {"success": False, "error": f"Missing context: {e}"}
        
        # Determine subject
        subject = self._get_subject(event_type, context)
        
        results = {
            "sent": [],
            "skipped": [],
            "failed": []
        }
        
        for recipient in recipients:
            # Check if should notify
            if not self.should_notify(event_type, recipient, context):
                results["skipped"].append({
                    "recipient": recipient,
                    "reason": "User preferences or frequency limits"
                })
                continue
            
            # Send notification
            try:
                self.email_service.send_email(
                    to_email=recipient,
                    subject=subject,
                    html_body=message,
                    text_body=message
                )
                
                # Record notification
                notification = EmailNotification(
                    notification_type=event_type,
                    recipient_email=recipient,
                    subject=subject,
                    body=message,
                    status="sent",
                    related_entity_type=context.get("related_entity_type"),
                    related_entity_id=context.get("related_entity_id")
                )
                self.db.add(notification)
                
                results["sent"].append(recipient)
                
            except Exception as e:
                self.logger.error(f"Failed to send notification to {recipient}: {e}")
                
                # Record failed notification
                notification = EmailNotification(
                    notification_type=event_type,
                    recipient_email=recipient,
                    subject=subject,
                    body=message,
                    status="failed",
                    error_message=str(e),
                    related_entity_type=context.get("related_entity_type"),
                    related_entity_id=context.get("related_entity_id")
                )
                self.db.add(notification)
                
                results["failed"].append({
                    "recipient": recipient,
                    "error": str(e)
                })
        
        self.db.commit()
        
        return {
            "success": len(results["sent"]) > 0,
            "results": results,
            "total_sent": len(results["sent"]),
            "total_skipped": len(results["skipped"]),
            "total_failed": len(results["failed"])
        }
    
    def _get_subject(self, event_type: str, context: Dict) -> str:
        """
        Generate notification subject based on event type.
        
        Args:
            event_type: Type of notification
            context: Context data
        
        Returns:
            Subject string
        """
        subjects = {
            "bias_detected": "⚠️ Bias Detected in Evaluation",
            "insufficient_raters": "⚠️ Insufficient Raters",
            "deadline_approaching": "⏰ Deadline Approaching",
            "nomination_submitted": "⭐ New EOM Nomination",
            "evaluation_submitted": "📝 New Evaluation Submitted",
            "variance_alert": "⚠️ Variance Alert",
            "eom_winner_announced": "🏆 EOM Winner Announced",
            "nomination_window_opening": "📅 EOM Nomination Window Opening",
            "nomination_window_closing": "⏰ EOM Nomination Window Closing Soon",
            "cycle_started": "🔄 New Evaluation Cycle Started",
            "cycle_ending": "⏰ Evaluation Cycle Ending Soon",
            "evaluation_overdue": "⚠️ Evaluation Overdue",
            "evaluation_overdue_escalation": "🚨 URGENT: Evaluation Overdue - Escalation",
            "smart_reminder": "💡 Smart Reminder: Pending Evaluations",
            "evaluation_due_soon": "⏰ Evaluation Due Soon"
        }
        
        base_subject = subjects.get(event_type, "Notification from Eternity School Evaluation System")
        
        # Add context-specific details if available
        if context.get("employee_name"):
            return f"{base_subject} - {context['employee_name']}"
        elif context.get("cycle_name"):
            return f"{base_subject} - {context['cycle_name']}"
        
        return base_subject
    
    def schedule_reminder(
        self,
        event_type: str,
        recipients: List[str],
        context: Dict,
        reminder_date: datetime,
        repeat: Optional[str] = None
    ) -> Dict:
        """
        Schedule a reminder notification for a future date.
        
        Args:
            event_type: Type of notification
            recipients: List of recipient emails
            context: Context data
            reminder_date: When to send the reminder
            repeat: Optional repeat pattern (daily, weekly)
        
        Returns:
            Dictionary with scheduling results
        """
        # In a real implementation, this would use a task queue (Celery, RQ, etc.)
        # For now, we'll store it in the database with a scheduled status
        template = self.message_templates.get(event_type)
        if not template:
            return {"success": False, "error": "Template not found"}
        
        message = template.format(**context)
        subject = self._get_subject(event_type, context)
        
        scheduled_notifications = []
        for recipient in recipients:
            notification = EmailNotification(
                notification_type=event_type,
                recipient_email=recipient,
                subject=subject,
                body=message,
                status="pending",
                sent_at=reminder_date,  # Store scheduled time
                related_entity_type=context.get("related_entity_type"),
                related_entity_id=context.get("related_entity_id")
            )
            self.db.add(notification)
            scheduled_notifications.append(notification)
        
        self.db.commit()
        
        return {
            "success": True,
            "scheduled_count": len(scheduled_notifications),
            "reminder_date": reminder_date.isoformat()
        }
    
    def get_user_behavior_profile(self, user_email: str) -> Dict:
        """
        Analyze user behavior to determine optimal reminder times.
        Tracks when users typically complete evaluations.
        
        Args:
            user_email: User email
        
        Returns:
            Dictionary with behavior profile including:
            - preferred_completion_hours: List of hours when user typically completes tasks
            - average_completion_time: Average days to complete after assignment
            - completion_pattern: 'early', 'on_time', 'late'
            - best_reminder_time: Optimal hour to send reminders
        """
        # Get user's historical evaluation completions
        completed_evaluations = (
            self.db.query(Evaluation)
            .join(Assignment)
            .filter(
                Assignment.rater_email == user_email,
                Evaluation.status == 'submitted',
                Evaluation.submitted_at.isnot(None)
            )
            .order_by(Evaluation.submitted_at.desc())
            .limit(20)  # Analyze last 20 completions
            .all()
        )
        
        if len(completed_evaluations) < 3:
            # Not enough data, return defaults
            return {
                "preferred_completion_hours": [9, 10, 11, 14, 15, 16],  # Business hours
                "average_completion_time": 7,  # Default: 7 days
                "completion_pattern": "unknown",
                "best_reminder_time": 10,  # 10 AM default
                "confidence": "low"
            }
        
        # Analyze completion times (hour of day)
        completion_hours = []
        completion_delays = []  # Days from assignment to completion
        
        for eval in completed_evaluations:
            if eval.submitted_at:
                completion_hours.append(eval.submitted_at.hour)
                
                # Calculate delay from assignment creation
                assignment = eval.assignment
                if assignment and assignment.created_at:
                    delay = (eval.submitted_at - assignment.created_at).days
                    completion_delays.append(delay)
        
        # Find most common completion hours (top 3)
        hour_counts = defaultdict(int)
        for hour in completion_hours:
            hour_counts[hour] += 1
        
        preferred_hours = sorted(
            hour_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        preferred_hours_list = [h[0] for h in preferred_hours]
        
        # Calculate average completion time
        avg_completion_time = statistics.mean(completion_delays) if completion_delays else 7
        
        # Determine completion pattern
        if avg_completion_time <= 3:
            pattern = "early"
        elif avg_completion_time <= 7:
            pattern = "on_time"
        else:
            pattern = "late"
        
        # Best reminder time: 2 hours before most common completion hour
        most_common_hour = preferred_hours[0][0] if preferred_hours else 10
        best_reminder_time = max(8, most_common_hour - 2)  # At least 8 AM
        
        return {
            "preferred_completion_hours": preferred_hours_list,
            "average_completion_time": round(avg_completion_time, 1),
            "completion_pattern": pattern,
            "best_reminder_time": best_reminder_time,
            "confidence": "high" if len(completed_evaluations) >= 10 else "medium"
        }
    
    def send_smart_reminder(
        self,
        user_email: str,
        pending_evaluations: List[Dict],
        cycle_id: int
    ) -> Dict:
        """
        Send a smart reminder based on user behavior profile.
        Only sends if it's an optimal time for the user.
        
        Args:
            user_email: User email
            pending_evaluations: List of pending evaluation assignments
            cycle_id: Current cycle ID
        
        Returns:
            Dictionary with reminder results
        """
        # Get user behavior profile
        behavior = self.get_user_behavior_profile(user_email)
        
        # Check if current time is optimal for this user
        current_hour = datetime.utcnow().hour
        is_optimal_time = (
            current_hour in behavior["preferred_completion_hours"] or
            current_hour == behavior["best_reminder_time"]
        )
        
        if not is_optimal_time:
            return {
                "success": False,
                "reason": "Not optimal time for user",
                "optimal_time": behavior["best_reminder_time"],
                "current_hour": current_hour
            }
        
        # Check if we should send reminder (avoid spam)
        if not self.should_notify("smart_reminder", user_email):
            return {
                "success": False,
                "reason": "Frequency limit reached"
            }
        
        # Prepare context
        context = {
            "pending_count": len(pending_evaluations),
            "user_email": user_email,
            "related_entity_type": "cycle",
            "related_entity_id": cycle_id
        }
        
        # Send reminder
        return self.send_notification(
            event_type="smart_reminder",
            recipients=[user_email],
            context=context,
            priority="normal"
        )
    
    def check_overdue_evaluations(
        self,
        cycle_id: int,
        escalation_days: int = 7
    ) -> Dict:
        """
        Check for overdue evaluations and send escalation alerts.
        
        Args:
            cycle_id: Evaluation cycle ID
            escalation_days: Days after which to escalate (default: 7)
        
        Returns:
            Dictionary with overdue evaluation details and alerts sent
        """
        cycle = self.db.query(Cycle).filter(Cycle.id == cycle_id).first()
        if not cycle or not cycle.end_date:
            return {
                "success": False,
                "error": "Cycle not found or no end date"
            }
        
        # Get all assignments without submitted evaluations
        pending_assignments = (
            self.db.query(Assignment)
            .outerjoin(Evaluation, Assignment.id == Evaluation.assignment_id)
            .filter(
                Assignment.cycle_id == cycle_id,
                Evaluation.id.is_(None)  # No evaluation submitted
            )
            .all()
        )
        
        today = datetime.utcnow().date()
        overdue_evaluations = []
        escalation_needed = []
        
        for assignment in pending_assignments:
            # Calculate days overdue (negative if not yet due)
            days_overdue = (today - cycle.end_date).days
            
            if days_overdue > 0:
                # Overdue
                overdue_evaluations.append({
                    "assignment_id": assignment.id,
                    "rater_email": assignment.rater_email,
                    "target_email": assignment.target_email,
                    "days_overdue": days_overdue
                })
                
                # Check if escalation needed
                if days_overdue >= escalation_days:
                    escalation_needed.append({
                        "assignment_id": assignment.id,
                        "rater_email": assignment.rater_email,
                        "target_email": assignment.target_email,
                        "days_overdue": days_overdue
                    })
        
        results = {
            "overdue_count": len(overdue_evaluations),
            "escalation_count": len(escalation_needed),
            "alerts_sent": []
        }
        
        # Send overdue alerts
        for overdue in overdue_evaluations:
            # Get target person name
            target_person = self.db.query(Person).filter(
                Person.email == overdue["target_email"]
            ).first()
            target_name = target_person.full_name if target_person else overdue["target_email"]
            
            context = {
                "target_name": target_name,
                "days_overdue": overdue["days_overdue"],
                "related_entity_type": "assignment",
                "related_entity_id": overdue["assignment_id"]
            }
            
            # Send overdue notification
            if overdue["days_overdue"] < escalation_days:
                # Regular overdue alert
                alert_result = self.send_notification(
                    event_type="evaluation_overdue",
                    recipients=[overdue["rater_email"]],
                    context=context,
                    priority="high"
                )
            else:
                # Escalation alert
                alert_result = self.send_notification(
                    event_type="evaluation_overdue_escalation",
                    recipients=[overdue["rater_email"]],
                    context=context,
                    priority="urgent"
                )
                
                # Also notify manager/department head
                rater_person = self.db.query(Person).filter(
                    Person.email == overdue["rater_email"]
                ).first()
                
                if rater_person and rater_person.department:
                    # Find department head (simplified - would need proper hierarchy)
                    managers = self.db.query(Person).filter(
                        Person.department == rater_person.department,
                        Person.role_title.ilike('%head%')
                    ).all()
                    
                    manager_emails = [m.email for m in managers]
                    if manager_emails:
                        escalation_context = {
                            "target_name": target_name,
                            "rater_name": rater_person.full_name,
                            "days_overdue": overdue["days_overdue"],
                            "related_entity_type": "assignment",
                            "related_entity_id": overdue["assignment_id"]
                        }
                        
                        self.send_notification(
                            event_type="evaluation_overdue_escalation",
                            recipients=manager_emails,
                            context=escalation_context,
                            priority="urgent"
                        )
            
            results["alerts_sent"].append({
                "assignment_id": overdue["assignment_id"],
                "rater_email": overdue["rater_email"],
                "alert_type": "escalation" if overdue["days_overdue"] >= escalation_days else "overdue",
                "result": alert_result
            })
        
        return results
    
    def send_due_soon_reminders(
        self,
        cycle_id: int,
        days_before: int = 3
    ) -> Dict:
        """
        Send reminders for evaluations due soon, using smart timing.
        
        Args:
            cycle_id: Evaluation cycle ID
            days_before: Days before deadline to send reminder (default: 3)
        
        Returns:
            Dictionary with reminder results
        """
        cycle = self.db.query(Cycle).filter(Cycle.id == cycle_id).first()
        if not cycle or not cycle.end_date:
            return {
                "success": False,
                "error": "Cycle not found or no deadline"
            }
        
        today = datetime.utcnow().date()
        days_remaining = (cycle.end_date - today).days
        
        if days_remaining > days_before:
            return {
                "success": False,
                "reason": f"Too early - {days_remaining} days remaining"
            }
        
        # Get pending assignments
        pending_assignments = (
            self.db.query(Assignment)
            .outerjoin(Evaluation, Assignment.id == Evaluation.assignment_id)
            .filter(
                Assignment.cycle_id == cycle_id,
                Evaluation.id.is_(None)
            )
            .all()
        )
        
        results = {
            "reminders_sent": 0,
            "reminders_skipped": 0,
            "details": []
        }
        
        # Group by rater to send smart reminders
        assignments_by_rater = defaultdict(list)
        for assignment in pending_assignments:
            assignments_by_rater[assignment.rater_email].append(assignment)
        
        for rater_email, assignments in assignments_by_rater.items():
            # Get user behavior profile
            behavior = self.get_user_behavior_profile(rater_email)
            
            # Check if optimal time
            current_hour = datetime.utcnow().hour
            is_optimal = (
                current_hour in behavior["preferred_completion_hours"] or
                current_hour == behavior["best_reminder_time"]
            )
            
            if not is_optimal:
                results["reminders_skipped"] += len(assignments)
                continue
            
            # Get target names
            target_names = []
            for assignment in assignments:
                target_person = self.db.query(Person).filter(
                    Person.email == assignment.target_email
                ).first()
                target_names.append(
                    target_person.full_name if target_person else assignment.target_email
                )
            
            context = {
                "target_name": ", ".join(target_names[:3]) + ("..." if len(target_names) > 3 else ""),
                "days_remaining": days_remaining,
                "pending_count": len(assignments),
                "related_entity_type": "cycle",
                "related_entity_id": cycle_id
            }
            
            # Send smart reminder
            reminder_result = self.send_notification(
                event_type="evaluation_due_soon",
                recipients=[rater_email],
                context=context,
                priority="normal"
            )
            
            if reminder_result["success"]:
                results["reminders_sent"] += 1
            else:
                results["reminders_skipped"] += 1
            
            results["details"].append({
                "rater_email": rater_email,
                "pending_count": len(assignments),
                "result": reminder_result
            })
        
        return results
