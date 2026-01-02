"""
Complete Survey Templates for Eternity School
Comprehensive survey template system covering all aspects of school life.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from backend.hybrid_identity_system import HybridIdentityMode


class EternitySchoolSurveyTemplates:
    """Complete survey templates covering all aspects of school life"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
        self.template_categories = self.load_template_categories()
        self.question_bank = self.load_question_bank()

    def load_template_categories(self) -> Dict:
        """Load template categories"""
        return {
            "physical_environment": "Physical Environment & Facilities",
            "workplace_culture": "Workplace Culture & Fairness",
            "management": "Management & Leadership",
            "inter_departmental": "Inter-Departmental Collaboration",
            "personal_wellbeing": "Personal Wellbeing & Support",
            "school_improvement": "School Improvement & Innovation",
            "sensitive_topics": "Sensitive Topics (Anonymous Only)",
            "accountability": "Accountability & Action Items (Identified Only)",
            "future_engagement": "Future Engagement (Conditional Only)",
        }

    def load_question_bank(self) -> Dict:
        """Load question bank from database or configuration"""
        # In production, load from database
        return {}

    def get_comprehensive_school_survey(self, identity_mode: str, survey_type: str = "comprehensive") -> Dict:
        """
        Get complete school climate survey based on identity mode.

        Args:
            identity_mode: Identity mode (anonymous, conditional, partial, identified)
            survey_type: Survey type (comprehensive, climate, feedback, etc.)

        Returns:
            Complete survey template with all sections
        """
        base_sections = {
            "physical_environment": self.get_physical_environment_section(identity_mode),
            "workplace_culture": self.get_workplace_culture_section(identity_mode),
            "management_effectiveness": self.get_management_section(identity_mode),
            "inter_departmental": self.get_interdepartmental_section(identity_mode),
            "personal_wellbeing": self.get_personal_wellbeing_section(identity_mode),
            "school_improvement": self.get_improvement_section(identity_mode),
        }

        # Add identity-specific sections
        if identity_mode == "anonymous":
            base_sections["sensitive_topics"] = self.get_sensitive_topics_section()
        elif identity_mode == "identified":
            base_sections["accountability"] = self.get_accountability_section()
        elif identity_mode == "conditional":
            base_sections["future_engagement"] = self.get_future_engagement_section()

        return {
            "survey_id": f"eternity_comprehensive_{datetime.utcnow().strftime('%Y%m%d')}",
            "title": "Eternity School Complete Climate Survey",
            "description": "Comprehensive feedback about all aspects of school life",
            "estimated_time": "15-20 minutes",
            "identity_mode": identity_mode,
            "sections": base_sections,
            "total_questions": sum(len(section.get("questions", [])) for section in base_sections.values()),
            "created_at": datetime.utcnow().isoformat(),
        }

    def get_physical_environment_section(self, identity_mode: str) -> Dict:
        """Physical environment and facilities feedback"""
        return {
            "section_id": "physical_env",
            "title": "Physical Environment & Facilities",
            "description": "Help us improve our physical spaces",
            "questions": [
                {
                    "id": "cafeteria_001",
                    "text": "How would you rate the cafeteria food quality?",
                    "type": "rating_scale",
                    "scale": ["Very Poor", "Poor", "Average", "Good", "Excellent"],
                    "category": "cafeteria",
                    "follow_up": "What specific improvements would you suggest?",
                    "conditional_show": identity_mode != "anonymous",
                    "required": False,
                },
                {
                    "id": "classroom_001",
                    "text": "Are your classrooms equipped with adequate technology?",
                    "type": "yes_no_details",
                    "category": "classrooms",
                    "details_prompt": "Please specify what technology is missing or inadequate",
                    "sensitivity": "low",
                    "required": True,
                },
                {
                    "id": "facilities_001",
                    "text": "Rate the cleanliness and maintenance of shared facilities",
                    "type": "multi_rating",
                    "sub_items": ["Restrooms", "Hallways", "Common Areas", "Outdoor Spaces"],
                    "scale": ["Very Poor", "Poor", "Average", "Good", "Excellent"],
                    "category": "facilities",
                    "required": True,
                },
                {
                    "id": "parking_001",
                    "text": "Is parking adequate and fairly allocated?",
                    "type": "rating_with_comments",
                    "category": "parking",
                    "show_if": identity_mode in ["identified", "conditional", "partial"],
                    "required": False,
                },
                {
                    "id": "safety_001",
                    "text": "How safe do you feel in the school environment?",
                    "type": "rating_scale",
                    "scale": ["Very Unsafe", "Unsafe", "Neutral", "Safe", "Very Safe"],
                    "category": "safety",
                    "required": True,
                },
            ],
        }

    def get_workplace_culture_section(self, identity_mode: str) -> Dict:
        """Workplace culture and fairness feedback"""
        return {
            "section_id": "workplace_culture",
            "title": "Workplace Culture & Fairness",
            "description": "Your honest feedback about our work environment",
            "questions": [
                {
                    "id": "fairness_001",
                    "text": "Do you feel evaluation processes are fair and transparent?",
                    "type": "rating_scale_with_explanation",
                    "scale": ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
                    "category": "fairness",
                    "sensitivity": "high" if identity_mode == "identified" else "medium",
                    "anonymous_only": identity_mode == "anonymous",
                    "required": True,
                },
                {
                    "id": "recognition_001",
                    "text": "How often do you feel your contributions are recognized?",
                    "type": "frequency_rating",
                    "scale": ["Never", "Rarely", "Sometimes", "Often", "Always"],
                    "category": "recognition",
                    "follow_up": "Can you share a recent example (good or bad)?",
                    "required": True,
                },
                {
                    "id": "inclusion_001",
                    "text": "Do you feel included and valued regardless of your background?",
                    "type": "yes_no_details",
                    "category": "inclusion",
                    "details_prompt": "Please share specific experiences that shaped your answer",
                    "sensitivity": "high",
                    "required": True,
                },
                {
                    "id": "communication_001",
                    "text": "Rate the effectiveness of communication from leadership",
                    "type": "multi_aspect_rating",
                    "aspects": ["Clarity", "Frequency", "Transparency", "Two-way communication"],
                    "scale": ["Very Poor", "Poor", "Average", "Good", "Excellent"],
                    "category": "communication",
                    "required": True,
                },
                {
                    "id": "collaboration_001",
                    "text": "How well do departments collaborate with each other?",
                    "type": "rating_scale",
                    "scale": ["Very Poorly", "Poorly", "Adequately", "Well", "Very Well"],
                    "category": "collaboration",
                    "required": True,
                },
            ],
        }

    def get_management_section(self, identity_mode: str) -> Dict:
        """Management and leadership effectiveness"""
        return {
            "section_id": "management",
            "title": "Management & Leadership Effectiveness",
            "description": "Evaluate your direct supervisors and school leadership",
            "questions": [
                {
                    "id": "direct_manager_001",
                    "text": "How effective is your direct manager in supporting your professional growth?",
                    "type": "comprehensive_rating",
                    "aspects": ["Support", "Communication", "Fairness", "Professional Development"],
                    "scale": ["Very Poor", "Poor", "Average", "Good", "Excellent"],
                    "category": "direct_management",
                    "manager_specific": True,
                    "required": True,
                },
                {
                    "id": "hod_001",
                    "text": "Rate your Head of Department's leadership effectiveness",
                    "type": "rating_with_examples",
                    "category": "department_leadership",
                    "examples_prompt": "Can you provide specific examples of their leadership?",
                    "show_if": identity_mode != "anonymous",
                    "required": False,
                },
                {
                    "id": "principal_001",
                    "text": "How well does the principal communicate the school's vision and direction?",
                    "type": "rating_scale",
                    "scale": ["Very Poorly", "Poorly", "Adequately", "Well", "Very Well"],
                    "category": "school_leadership",
                    "required": True,
                },
                {
                    "id": "hr_001",
                    "text": "Rate HR department's responsiveness to staff needs and concerns",
                    "type": "multi_rating",
                    "aspects": ["Response Time", "Helpfulness", "Problem Resolution", "Policy Clarity"],
                    "category": "hr_effectiveness",
                    "show_if": identity_mode != "anonymous",
                    "required": False,
                },
                {
                    "id": "decision_making_001",
                    "text": "How transparent and inclusive is the decision-making process?",
                    "type": "rating_scale",
                    "scale": [
                        "Not Transparent",
                        "Somewhat Transparent",
                        "Moderately Transparent",
                        "Transparent",
                        "Very Transparent",
                    ],
                    "category": "transparency",
                    "required": True,
                },
            ],
        }

    def get_interdepartmental_section(self, identity_mode: str) -> Dict:
        """Inter-departmental collaboration"""
        return {
            "section_id": "inter_departmental",
            "title": "Inter-Departmental Collaboration",
            "description": "Feedback on collaboration between departments",
            "questions": [
                {
                    "id": "collab_001",
                    "text": "How effective is collaboration between your department and others?",
                    "type": "rating_scale",
                    "scale": ["Very Ineffective", "Ineffective", "Neutral", "Effective", "Very Effective"],
                    "category": "collaboration",
                    "required": True,
                },
                {
                    "id": "communication_dept_001",
                    "text": "Rate inter-departmental communication",
                    "type": "multi_rating",
                    "aspects": ["Frequency", "Clarity", "Timeliness", "Relevance"],
                    "category": "communication",
                    "required": True,
                },
                {
                    "id": "conflict_resolution_001",
                    "text": "How well are conflicts between departments resolved?",
                    "type": "rating_scale",
                    "scale": ["Very Poorly", "Poorly", "Adequately", "Well", "Very Well"],
                    "category": "conflict_resolution",
                    "required": True,
                },
            ],
        }

    def get_personal_wellbeing_section(self, identity_mode: str) -> Dict:
        """Personal wellbeing and support"""
        return {
            "section_id": "personal_wellbeing",
            "title": "Personal Wellbeing & Support",
            "description": "Your personal wellbeing and support systems",
            "questions": [
                {
                    "id": "workload_001",
                    "text": "Is your workload manageable?",
                    "type": "rating_scale",
                    "scale": ["Unmanageable", "Difficult", "Manageable", "Comfortable", "Very Comfortable"],
                    "category": "workload",
                    "required": True,
                },
                {
                    "id": "support_001",
                    "text": "Do you feel supported in your role?",
                    "type": "yes_no_details",
                    "category": "support",
                    "details_prompt": "What support do you need that you're not receiving?",
                    "required": True,
                },
                {
                    "id": "work_life_balance_001",
                    "text": "How would you rate your work-life balance?",
                    "type": "rating_scale",
                    "scale": ["Very Poor", "Poor", "Average", "Good", "Excellent"],
                    "category": "work_life_balance",
                    "required": True,
                },
                {
                    "id": "stress_001",
                    "text": "How would you rate your stress levels at work?",
                    "type": "rating_scale",
                    "scale": ["Very Low", "Low", "Moderate", "High", "Very High"],
                    "category": "stress",
                    "sensitivity": "medium",
                    "required": True,
                },
            ],
        }

    def get_improvement_section(self, identity_mode: str) -> Dict:
        """School improvement and innovation"""
        return {
            "section_id": "school_improvement",
            "title": "School Improvement & Innovation",
            "description": "Your ideas for school improvement",
            "questions": [
                {
                    "id": "innovation_001",
                    "text": "How open is the school to new ideas and innovation?",
                    "type": "rating_scale",
                    "scale": ["Not Open", "Somewhat Open", "Moderately Open", "Open", "Very Open"],
                    "category": "innovation",
                    "required": True,
                },
                {
                    "id": "improvement_001",
                    "text": "What are the top 3 areas you think need improvement?",
                    "type": "priority_ranking",
                    "max_selections": 3,
                    "options": [
                        "Communication",
                        "Resources",
                        "Professional Development",
                        "Workplace Culture",
                        "Management",
                        "Facilities",
                        "Technology",
                        "Other",
                    ],
                    "category": "improvement",
                    "required": True,
                },
                {
                    "id": "suggestions_001",
                    "text": "What specific improvements would you like to see?",
                    "type": "open_text",
                    "category": "suggestions",
                    "required": False,
                },
            ],
        }

    def get_sensitive_topics_section(self) -> Dict:
        """Sensitive topics section (anonymous only)"""
        return {
            "section_id": "sensitive_topics",
            "title": "Sensitive Topics (Anonymous Only)",
            "description": "Your honest feedback on sensitive matters",
            "questions": [
                {
                    "id": "discrimination_001",
                    "text": "Have you experienced or witnessed any form of discrimination?",
                    "type": "yes_no_details",
                    "category": "discrimination",
                    "details_prompt": "Please describe the incident(s) if comfortable",
                    "sensitivity": "very_high",
                    "anonymous_only": True,
                    "required": False,
                },
                {
                    "id": "harassment_001",
                    "text": "Have you experienced or witnessed harassment in the workplace?",
                    "type": "yes_no_details",
                    "category": "harassment",
                    "sensitivity": "very_high",
                    "anonymous_only": True,
                    "required": False,
                },
                {
                    "id": "retaliation_001",
                    "text": "Do you fear retaliation for speaking up about concerns?",
                    "type": "yes_no_details",
                    "category": "retaliation",
                    "sensitivity": "very_high",
                    "anonymous_only": True,
                    "required": False,
                },
            ],
        }

    def get_accountability_section(self) -> Dict:
        """Accountability section (identified only)"""
        return {
            "section_id": "accountability",
            "title": "Accountability & Action Items",
            "description": "Specific actions you'd like to see taken",
            "questions": [
                {
                    "id": "actions_001",
                    "text": "What specific actions would you like to see taken based on your feedback?",
                    "type": "detailed_response",
                    "category": "actions",
                    "identified_only": True,
                    "follow_up_enabled": True,
                    "required": False,
                },
                {
                    "id": "accountability_001",
                    "text": "Are you willing to be part of a working group to address these issues?",
                    "type": "yes_no",
                    "category": "accountability",
                    "identified_only": True,
                    "required": False,
                },
            ],
        }

    def get_future_engagement_section(self) -> Dict:
        """Future engagement section (conditional only)"""
        return {
            "section_id": "future_engagement",
            "title": "Future Engagement",
            "description": "Your willingness to engage further",
            "questions": [
                {
                    "id": "discussion_001",
                    "text": "Would you be open to discussing this feedback in person if needed?",
                    "type": "conditional",
                    "category": "future_feedback",
                    "reveal_trigger": "if_discussion_needed",
                    "required": False,
                },
                {
                    "id": "follow_up_001",
                    "text": "How would you prefer to be contacted for follow-up?",
                    "type": "multiple_choice",
                    "options": ["Email", "Phone", "In-person meeting", "No follow-up"],
                    "category": "contact_preference",
                    "required": False,
                },
            ],
        }

    def get_template_by_category(self, category: str, identity_mode: str) -> Dict:
        """Get template for specific category"""
        templates = {
            "physical_environment": self.get_physical_environment_section,
            "workplace_culture": self.get_workplace_culture_section,
            "management": self.get_management_section,
            "inter_departmental": self.get_interdepartmental_section,
            "personal_wellbeing": self.get_personal_wellbeing_section,
            "school_improvement": self.get_improvement_section,
        }

        template_func = templates.get(category)
        if template_func:
            return template_func(identity_mode)
        return {}
