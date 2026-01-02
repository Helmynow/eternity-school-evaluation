"""
Email notification service for Eternity School Evaluation System.
Sends emails to winners, voters, evaluators, and other stakeholders.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from jinja2 import Template


class EmailService:
    """Service for sending email notifications"""

    def __init__(self):
        # Resend SMTP Configuration
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.resend.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "465"))
        self.smtp_user = os.getenv("SMTP_USER", "resend")
        # Never hardcode secrets. If SMTP_PASSWORD is not set, sending will be disabled/fail safely.
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@eternityschoolegypt.com")
        # Default to disabled unless explicitly enabled via env var.
        self.enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"

    def send_email(self, to_email: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
        """Send an email"""
        if not self.enabled:
            print(f"[EMAIL DISABLED] Would send to {to_email}: {subject}")
            return True

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

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #094773;">🎉 Congratulations, {winner_name}!</h1>
                <p>We are thrilled to inform you that you have been selected as the <strong>Employee of the Month</strong> in the <strong>{category}</strong> category for <strong>{cycle_name}</strong>.</p>
                <p>Your dedication, hard work, and commitment to excellence have been recognized by your colleagues and leadership team.</p>
                <div style="background-color: #E5F6DF; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>Category:</strong> {category}</p>
                    <p style="margin: 5px 0;"><strong>Cycle:</strong> {cycle_name}</p>
                </div>
                <p>Thank you for your outstanding contribution to Eternity School of Egypt!</p>
                <p>Best regards,<br>Eternity School Evaluation Team</p>
            </div>
        </body>
        </html>
        """

        return self.send_email(winner_email, subject, html_body)

    def send_voter_notification(
        self, voter_email: str, voter_name: str, cycle_name: str, voting_deadline: Optional[str] = None
    ) -> bool:
        """Send notification to voters"""
        subject = f"🗳️ EOM Voting Open - {cycle_name}"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #094773;">EOM Voting is Now Open</h1>
                <p>Dear {voter_name},</p>
                <p>The Employee of the Month voting for <strong>{cycle_name}</strong> is now open.</p>
                <p>Please log in to the EVALVision system to cast your vote.</p>
                {f'<p><strong>Voting Deadline:</strong> {voting_deadline}</p>' if voting_deadline else ''}
                <div style="background-color: #E5F6DF; padding: 15px; border-radius: 5px; margin: 20px 0; text-align: center;">
                    <a href="http://localhost:3000/eom/vote" style="background-color: #2C5B4C; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Cast Your Vote</a>
                </div>
                <p>Thank you for your participation!</p>
                <p>Best regards,<br>Eternity School Evaluation Team</p>
            </div>
        </body>
        </html>
        """

        return self.send_email(voter_email, subject, html_body)

    def send_evaluator_notification(
        self, evaluator_email: str, evaluator_name: str, target_name: str, cycle_name: str, deadline: Optional[str] = None
    ) -> bool:
        """Send notification to evaluators"""
        subject = f"📝 Evaluation Reminder - {cycle_name}"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #094773;">Evaluation Reminder</h1>
                <p>Dear {evaluator_name},</p>
                <p>This is a reminder that you have a pending evaluation for <strong>{target_name}</strong> in the <strong>{cycle_name}</strong> cycle.</p>
                {f'<p><strong>Deadline:</strong> {deadline}</p>' if deadline else ''}
                <div style="background-color: #E5F6DF; padding: 15px; border-radius: 5px; margin: 20px 0; text-align: center;">
                    <a href="http://localhost:3000/mre/evaluate" style="background-color: #094773; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Complete Evaluation</a>
                </div>
                <p>Thank you for your timely completion of evaluations!</p>
                <p>Best regards,<br>Eternity School Evaluation Team</p>
            </div>
        </body>
        </html>
        """

        return self.send_email(evaluator_email, subject, html_body)

    def send_objection_notification(
        self, admin_email: str, objector_name: str, nominee_name: str, reason: str, cycle_name: str
    ) -> bool:
        """Send notification about an objection"""
        subject = f"⚠️ Objection Submitted - EOM Nomination"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #C88167;">Objection Submitted</h1>
                <p>An objection has been submitted regarding an EOM nomination.</p>
                <div style="background-color: #F8F0E8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Objector:</strong> {objector_name}</p>
                    <p><strong>Nominee:</strong> {nominee_name}</p>
                    <p><strong>Cycle:</strong> {cycle_name}</p>
                    <p><strong>Reason:</strong></p>
                    <p style="background-color: white; padding: 10px; border-left: 3px solid #C88167;">{reason}</p>
                </div>
                <p>Please review this objection in the admin panel.</p>
                <div style="background-color: #E5F6DF; padding: 15px; border-radius: 5px; margin: 20px 0; text-align: center;">
                    <a href="http://localhost:3000/admin/objections" style="background-color: #2C5B4C; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Review Objection</a>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(admin_email, subject, html_body)
