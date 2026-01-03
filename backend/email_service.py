"""
Email notification service for Eternity School Evaluation System.
Sends emails to winners, voters, evaluators, and other stakeholders.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional, Dict, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


class EmailService:
    """Service for sending email notifications using Jinja2 templates"""

    def __init__(self):
        # Resend SMTP Configuration
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.resend.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "465"))
        self.smtp_user = os.getenv("SMTP_USER", "resend")
        # Never hardcode secrets. If SMTP_PASSWORD is not set, sending will be disabled/fail safely.
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@eternityschoolegypt.com")
        
        # Base URL for links (frontend URL)
        self.app_url = os.getenv("APP_URL", "http://localhost:3000").rstrip("/")

        # Enable email sending if explicitly enabled OR if SMTP is configured.
        enabled_env = os.getenv("EMAIL_ENABLED")
        if enabled_env is None:
            self.enabled = bool(self.smtp_password)
        else:
            self.enabled = enabled_env.lower() == "true"

        # Initialize Jinja2 Environment
        template_dir = Path(__file__).parent / "templates" / "email"
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"])
        )

    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a Jinja2 template"""
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            print(f"Error rendering template {template_name}: {e}")
            return ""

    def send_email(self, to_email: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
        """Send an email"""
        if not self.enabled:
            print(f"[EMAIL DISABLED] Would send to {to_email}: {subject}")
            return False

        if not self.smtp_user or not self.smtp_password:
            print(f"[EMAIL NOT CONFIGURED] Cannot send email to {to_email}")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email

            if text_body:
                msg.attach(MIMEText(text_body, "plain"))
            
            if html_body:
                msg.attach(MIMEText(html_body, "html"))

            # Use SSL for port 465, TLS for port 587
            if self.smtp_port == 465:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)

            return True
        except Exception as e:
            print(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_winner_notification(self, winner_email: str, winner_name: str, category: str, cycle_name: str) -> bool:
        """Send notification to EOM winner"""
        subject = f"🎉 Congratulations! You are the Employee of the Month - {category}"
        
        html_body = self._render_template("winner_notification.html", {
            "winner_name": winner_name,
            "category": category,
            "cycle_name": cycle_name
        })

        return self.send_email(winner_email, subject, html_body)

    def send_voter_notification(
        self, voter_email: str, voter_name: str, cycle_name: str, voting_deadline: Optional[str] = None
    ) -> bool:
        """Send notification to voters"""
        subject = f"🗳️ EOM Voting Open - {cycle_name}"
        
        html_body = self._render_template("voter_notification.html", {
            "voter_name": voter_name,
            "cycle_name": cycle_name,
            "voting_deadline": voting_deadline,
            "action_url": f"{self.app_url}/eom/vote"
        })

        return self.send_email(voter_email, subject, html_body)

    def send_evaluator_notification(
        self, evaluator_email: str, evaluator_name: str, target_name: str, cycle_name: str, deadline: Optional[str] = None
    ) -> bool:
        """Send notification to evaluators"""
        subject = f"📝 Evaluation Reminder - {cycle_name}"
        
        html_body = self._render_template("evaluator_notification.html", {
            "evaluator_name": evaluator_name,
            "target_name": target_name,
            "cycle_name": cycle_name,
            "deadline": deadline,
            "action_url": f"{self.app_url}/mre/evaluate"
        })

        return self.send_email(evaluator_email, subject, html_body)

    def send_objection_notification(
        self, admin_email: str, objector_name: str, nominee_name: str, reason: str, cycle_name: str
    ) -> bool:
        """Send notification about an objection"""
        subject = f"⚠️ Objection Submitted - EOM Nomination"
        
        html_body = self._render_template("objection_notification.html", {
            "objector_name": objector_name,
            "nominee_name": nominee_name,
            "reason": reason,
            "cycle_name": cycle_name,
            "action_url": f"{self.app_url}/admin/objections"
        })

        return self.send_email(admin_email, subject, html_body)

    def send_survey_invitation(
        self, user_email: str, user_name: str, survey_title: str, estimated_time: str, identity_mode: str, survey_id: int
    ) -> bool:
        """Send invitation to participate in a survey"""
        subject = f"📊 Invitation: {survey_title}"
        
        html_body = self._render_template("survey_invitation.html", {
            "user_name": user_name,
            "survey_title": survey_title,
            "estimated_time": estimated_time,
            "identity_mode": identity_mode,
            "action_url": f"{self.app_url}/survey/{survey_id}"
        })

        return self.send_email(user_email, subject, html_body)
