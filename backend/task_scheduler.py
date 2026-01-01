"""
Task Scheduler for Eternity School Evaluation System.
Handles automated email sending, notifications, and reminders.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import logging
from typing import Optional
from sqlalchemy.orm import Session

from backend.database import get_db_session, Cycle, EOMCycle, Assignment, Evaluation, EmailNotification, Person
from backend.email_service import EmailService
from backend.smart_notification_system import SmartNotificationSystem

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Manages scheduled tasks for the evaluation system"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.email_service = EmailService()
        self.is_running = False
    
    def start(self):
        """Start the scheduler"""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("Task scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Task scheduler stopped")
    
    def schedule_daily_tasks(self):
        """Schedule all daily recurring tasks"""
        # Daily smart reminders at 8 AM
        self.scheduler.add_job(
            self.send_daily_smart_reminders,
            trigger=CronTrigger(hour=8, minute=0),
            id='daily_smart_reminders',
            replace_existing=True
        )
        
        # Daily overdue check at 9 AM
        self.scheduler.add_job(
            self.check_overdue_evaluations,
            trigger=CronTrigger(hour=9, minute=0),
            id='daily_overdue_check',
            replace_existing=True
        )
        
        # Due soon reminders at 10 AM
        self.scheduler.add_job(
            self.send_due_soon_reminders,
            trigger=CronTrigger(hour=10, minute=0),
            id='daily_due_soon_reminders',
            replace_existing=True
        )
        
        # Process pending emails every 5 minutes
        self.scheduler.add_job(
            self.process_pending_emails,
            trigger=IntervalTrigger(minutes=5),
            id='process_pending_emails',
            replace_existing=True
        )
        
        # Clean up expired announcements daily at midnight
        self.scheduler.add_job(
            self.cleanup_expired_announcements,
            trigger=CronTrigger(hour=0, minute=0),
            id='cleanup_expired_announcements',
            replace_existing=True
        )
        
        logger.info("Daily tasks scheduled")
    
    def send_daily_smart_reminders(self):
        """Send smart reminders for active cycles"""
        try:
            with get_db_session() as db:
                # Get current active cycles
                active_cycles = db.query(Cycle).filter(
                    Cycle.is_active == True
                ).all()
                
                notification_system = SmartNotificationSystem(db)
                
                for cycle in active_cycles:
                    try:
                        # Send smart reminders for this cycle
                        notification_system.send_smart_reminders_for_cycle(cycle.id)
                        logger.info(f"Sent smart reminders for cycle {cycle.id}")
                    except Exception as e:
                        logger.error(f"Error sending smart reminders for cycle {cycle.id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error in send_daily_smart_reminders: {str(e)}")
    
    def check_overdue_evaluations(self):
        """Check for overdue evaluations and send escalation alerts"""
        try:
            with get_db_session() as db:
                # Get active cycles
                active_cycles = db.query(Cycle).filter(
                    Cycle.is_active == True
                ).all()
                
                notification_system = SmartNotificationSystem(db)
                
                for cycle in active_cycles:
                    try:
                        # Check overdue evaluations
                        overdue = db.query(Assignment).join(Evaluation).filter(
                            Assignment.cycle_id == cycle.id,
                            Evaluation.submitted_at.is_(None),
                            Assignment.created_at < datetime.utcnow() - timedelta(days=cycle.deadline_days or 7)
                        ).all()
                        
                        for assignment in overdue:
                            days_overdue = (datetime.utcnow() - assignment.created_at).days - (cycle.deadline_days or 7)
                            if days_overdue > 0:
                                # Send escalation alert
                                notification_system.send_notification(
                                    event_type="evaluation_overdue",
                                    recipients=[assignment.rater_email],
                                    context={
                                        "target_name": assignment.target.full_name if assignment.target else assignment.target_email,
                                        "days_overdue": days_overdue,
                                        "cycle_name": cycle.name,
                                        "deadline": cycle.end_date.isoformat() if cycle.end_date else None
                                    },
                                    priority="urgent"
                                )
                        
                        logger.info(f"Checked overdue evaluations for cycle {cycle.id}")
                    except Exception as e:
                        logger.error(f"Error checking overdue for cycle {cycle.id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error in check_overdue_evaluations: {str(e)}")
    
    def send_due_soon_reminders(self):
        """Send reminders for evaluations due soon (3 days before deadline)"""
        try:
            with get_db_session() as db:
                # Get active cycles
                active_cycles = db.query(Cycle).filter(
                    Cycle.is_active == True
                ).all()
                
                notification_system = SmartNotificationSystem(db)
                
                for cycle in active_cycles:
                    if not cycle.end_date:
                        continue
                    
                    days_until_deadline = (cycle.end_date - datetime.utcnow().date()).days
                    
                    if 1 <= days_until_deadline <= 3:
                        # Get pending assignments
                        pending = db.query(Assignment).filter(
                            Assignment.cycle_id == cycle.id
                        ).join(Evaluation, isouter=True).filter(
                            Evaluation.id.is_(None)
                        ).all()
                        
                        for assignment in pending:
                            notification_system.send_notification(
                                event_type="deadline_approaching",
                                recipients=[assignment.rater_email],
                                context={
                                    "task": f"Evaluation for {assignment.target.full_name if assignment.target else assignment.target_email}",
                                    "deadline": cycle.end_date.isoformat(),
                                    "days_remaining": days_until_deadline,
                                    "cycle_name": cycle.name
                                },
                                priority="high"
                            )
                        
                        logger.info(f"Sent due soon reminders for cycle {cycle.id}")
        except Exception as e:
            logger.error(f"Error in send_due_soon_reminders: {str(e)}")
    
    def process_pending_emails(self):
        """Process pending email notifications from the database"""
        try:
            with get_db_session() as db:
                # Get pending emails that should be sent now
                pending_emails = db.query(EmailNotification).filter(
                    EmailNotification.status == 'pending',
                    EmailNotification.sent_at <= datetime.utcnow()
                ).limit(50).all()
                
                for email_notification in pending_emails:
                    try:
                        # Send email
                        success = self.email_service.send_email(
                            to_email=email_notification.recipient_email,
                            subject=email_notification.subject,
                            html_body=email_notification.body
                        )
                        
                        if success:
                            email_notification.status = 'sent'
                            email_notification.sent_at = datetime.utcnow()
                        else:
                            email_notification.status = 'failed'
                            email_notification.error_message = "Failed to send email"
                        
                        db.commit()
                        logger.info(f"Processed email notification {email_notification.id}: {email_notification.status}")
                    except Exception as e:
                        logger.error(f"Error processing email {email_notification.id}: {str(e)}")
                        email_notification.status = 'failed'
                        email_notification.error_message = str(e)
                        db.commit()
        except Exception as e:
            logger.error(f"Error in process_pending_emails: {str(e)}")
    
    def cleanup_expired_announcements(self):
        """Deactivate expired announcements"""
        try:
            from backend.database import Announcement
            
            with get_db_session() as db:
                expired = db.query(Announcement).filter(
                    Announcement.is_active == True,
                    Announcement.expires_at.isnot(None),
                    Announcement.expires_at < datetime.utcnow()
                ).all()
                
                for announcement in expired:
                    announcement.is_active = False
                
                db.commit()
                logger.info(f"Deactivated {len(expired)} expired announcements")
        except Exception as e:
            logger.error(f"Error in cleanup_expired_announcements: {str(e)}")
    
    def send_smart_reminders_for_cycle(self, cycle_id: int):
        """Send smart reminders for a specific cycle"""
        try:
            with get_db_session() as db:
                notification_system = SmartNotificationSystem(db)
                # Get pending assignments for this cycle
                pending = db.query(Assignment).filter(
                    Assignment.cycle_id == cycle_id
                ).join(Evaluation, isouter=True).filter(
                    Evaluation.id.is_(None)
                ).all()
                
                for assignment in pending:
                    # Get user behavior profile
                    try:
                        profile = notification_system.get_user_behavior_profile(assignment.rater_email)
                        # Send reminder if it's the right time
                        notification_system.send_notification(
                            event_type="evaluation_due",
                            recipients=[assignment.rater_email],
                            context={
                                "target_name": assignment.target.full_name if assignment.target else assignment.target_email,
                                "cycle_name": db.query(Cycle).filter(Cycle.id == cycle_id).first().name if db.query(Cycle).filter(Cycle.id == cycle_id).first() else "Current Cycle",
                                "deadline": db.query(Cycle).filter(Cycle.id == cycle_id).first().end_date.isoformat() if db.query(Cycle).filter(Cycle.id == cycle_id).first() and db.query(Cycle).filter(Cycle.id == cycle_id).first().end_date else None
                            },
                            priority="normal"
                        )
                    except Exception as e:
                        logger.error(f"Error sending reminder to {assignment.rater_email}: {str(e)}")
        except Exception as e:
            logger.error(f"Error sending smart reminders for cycle {cycle_id}: {str(e)}")


# Global scheduler instance
task_scheduler = TaskScheduler()
