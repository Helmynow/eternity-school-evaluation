"""
EOM Category Recommender
Suggests the most suitable EOM category based on achievement text using keyword matching and sentiment analysis.
"""

import re
from collections import Counter
from typing import Dict, List, Tuple

from backend.database import EOMCategory


class EOMCategoryRecommender:
    """Recommends EOM categories based on achievement text analysis"""

    achievement_keywords = {
        EOMCategory.OUTSTANDING_LEADERSHIP: [
            "led",
            "lead",
            "managed",
            "initiated",
            "coordinated",
            "directed",
            "supervised",
            "mentored",
            "guided",
            "oversaw",
            "organized",
            "strategic",
            "vision",
            "decision",
            "delegated",
            "empowered",
            "inspired",
            "motivated",
            "team leader",
            "project lead",
        ],
        EOMCategory.TEAM_SPIRIT: [
            "helped",
            "supported",
            "colleagues",
            "collaborated",
            "teamwork",
            "cooperation",
            "assisted",
            "worked together",
            "partnership",
            "unified",
            "synergy",
            "coordination",
            "shared",
            "contributed",
            "team player",
            "cross-functional",
            "interdepartmental",
        ],
        EOMCategory.INNOVATION: [
            "improved",
            "streamlined",
            "automated",
            "innovated",
            "created",
            "developed",
            "designed",
            "implemented",
            "optimized",
            "enhanced",
            "transformed",
            "revolutionized",
            "pioneered",
            "breakthrough",
            "cutting-edge",
            "creative solution",
            "new approach",
            "process improvement",
            "efficiency",
            "productivity",
        ],
        EOMCategory.RISING_STAR: [
            "new employee",
            "new to the school",
            "first 6 months",
            "quickly adapted",
            "exceeded expectations",
            "eagerness",
            "initiative",
            "new hire",
            "recently joined",
            "fast learner",
            "quickly integrated",
            "early success",
        ],
        EOMCategory.SERVICE_EXCELLENCE: [
            "punctual",
            "reliable",
            "consistent",
            "dependable",
            "on time",
            "never late",
            "high standard",
            "minimal supervision",
            "self-directed",
            "proactive",
            "zero late marks",
            "submits early",
            "no reminders needed",
            "excellent attendance",
        ],
    }

    # Additional context patterns for better matching
    context_patterns = {
        EOMCategory.OUTSTANDING_LEADERSHIP: [
            r"\b(led|managed|directed)\s+\w+\s+(team|project|initiative|program)",
            r"\b(mentored|coached|guided)\s+\w+\s+(staff|colleagues|team)",
            r"\b(strategic|vision|decision-making)",
        ],
        EOMCategory.TEAM_SPIRIT: [
            r"\b(worked\s+with|collaborated\s+with|partnered\s+with)",
            r"\b(team\s+effort|joint\s+project|cross-functional)",
            r"\b(supported|assisted|helped)\s+\w+\s+(colleagues|team|department)",
        ],
        EOMCategory.INNOVATION: [
            r"\b(developed|created|designed)\s+\w+\s+(system|process|solution|tool)",
            r"\b(improved|enhanced|optimized)\s+\w+\s+(efficiency|productivity|process)",
            r"\b(automated|streamlined|simplified)",
        ],
        EOMCategory.RISING_STAR: [
            r"\b(new\s+employee|new\s+to\s+the\s+school|first\s+\d+\s+months)",
            r"\b(quickly\s+adapted|exceeded\s+expectations|early\s+success)",
        ],
        EOMCategory.SERVICE_EXCELLENCE: [
            r"\b(punctual|reliable|consistent|dependable)",
            r"\b(zero\s+late|never\s+late|on\s+time|excellent\s+attendance)",
        ],
    }

    def __init__(self):
        """Initialize the recommender"""
        pass

    def suggest_category(self, achievement_text: str, nominee_role: str = None) -> Dict:
        """
        Suggest the most suitable EOM category based on achievement text.

        Args:
            achievement_text: The achievement description or nomination reason
            nominee_role: Optional role/title of the nominee for context

        Returns:
            Dictionary with:
                - recommended_category: The top recommended category
                - confidence_score: Confidence level (0-1)
                - all_scores: Scores for all categories
                - reasoning: Explanation of the recommendation
        """
        if not achievement_text or not achievement_text.strip():
            return {
                "recommended_category": None,
                "confidence_score": 0.0,
                "all_scores": {},
                "reasoning": "No achievement text provided",
            }

        # Normalize text
        text_lower = achievement_text.lower()

        # Calculate scores for each category
        scores = {}
        for category, keywords in self.achievement_keywords.items():
            score = self._calculate_relevance(text_lower, keywords, category)
            scores[category] = score

        # Apply role-based adjustments
        if nominee_role:
            scores = self._apply_role_adjustments(scores, nominee_role, text_lower)

        # Get sentiment score (positive sentiment increases confidence)
        sentiment_score = self._analyze_sentiment(achievement_text)

        # Find top category
        if not scores or max(scores.values()) == 0:
            return {
                "recommended_category": None,
                "confidence_score": 0.0,
                "all_scores": scores,
                "reasoning": "No clear category match found",
            }

        top_category = max(scores.items(), key=lambda x: x[1])
        recommended_category = top_category[0]
        base_score = top_category[1]

        # Adjust confidence based on sentiment and score gap
        confidence = min(1.0, base_score * 0.7 + sentiment_score * 0.3)

        # Check if there's a clear winner (score gap > 0.2)
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_scores) > 1:
            score_gap = sorted_scores[0][1] - sorted_scores[1][1]
            if score_gap < 0.1:
                confidence *= 0.8  # Reduce confidence if scores are close

        # Generate reasoning
        reasoning = self._generate_reasoning(recommended_category, scores, sentiment_score)

        return {
            "recommended_category": (
                recommended_category.value if hasattr(recommended_category, "value") else str(recommended_category)
            ),
            "confidence_score": round(confidence, 2),
            "all_scores": {k.value if hasattr(k, "value") else str(k): round(v, 2) for k, v in scores.items()},
            "reasoning": reasoning,
        }

    def _calculate_relevance(self, text: str, keywords: List[str], category: EOMCategory) -> float:
        """Calculate relevance score for a category based on keyword matching"""
        score = 0.0
        matches = []

        # Exact keyword matching
        for keyword in keywords:
            # Word boundary matching for better accuracy
            pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
            matches_found = len(re.findall(pattern, text))
            if matches_found > 0:
                score += matches_found * 0.1
                matches.append(keyword)

        # Pattern matching for context
        if category in self.context_patterns:
            for pattern in self.context_patterns[category]:
                if re.search(pattern, text, re.IGNORECASE):
                    score += 0.3

        # Bonus for multiple keyword matches
        if len(matches) > 1:
            score += 0.2

        # Normalize score (max around 1.0)
        return min(1.0, score)

    def _analyze_sentiment(self, text: str) -> float:
        """
        Simple sentiment analysis.
        Returns a score between 0 (negative) and 1 (positive).
        """
        positive_words = [
            "excellent",
            "outstanding",
            "exceptional",
            "remarkable",
            "impressive",
            "dedicated",
            "committed",
            "passionate",
            "enthusiastic",
            "proactive",
            "successful",
            "achieved",
            "accomplished",
            "exceeded",
            "surpassed",
            "improved",
            "enhanced",
            "positive",
            "effective",
            "efficient",
            "valuable",
            "significant",
            "meaningful",
            "impactful",
            "transformative",
        ]

        negative_words = [
            "failed",
            "unsuccessful",
            "poor",
            "inadequate",
            "ineffective",
            "problem",
            "issue",
            "challenge",
            "difficulty",
            "struggle",
        ]

        text_lower = text.lower()

        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        # Calculate sentiment score
        total_words = len(text.split())
        if total_words == 0:
            return 0.5  # Neutral

        positive_ratio = positive_count / max(total_words, 1)
        negative_ratio = negative_count / max(total_words, 1)

        # Base sentiment (0.5 = neutral)
        sentiment = 0.5 + (positive_ratio * 0.4) - (negative_ratio * 0.4)

        return max(0.0, min(1.0, sentiment))

    def _apply_role_adjustments(self, scores: Dict, role: str, text: str) -> Dict:
        """Apply role-based adjustments to scores"""
        role_lower = role.lower() if role else ""

        # Academic roles are more likely to be Outstanding Leadership or Innovation
        if any(term in role_lower for term in ["teacher", "instructor", "professor", "academic"]):
            scores[EOMCategory.OUTSTANDING_LEADERSHIP] = scores.get(EOMCategory.OUTSTANDING_LEADERSHIP, 0) * 1.1
            scores[EOMCategory.INNOVATION] = scores.get(EOMCategory.INNOVATION, 0) * 1.1

        # Admin roles are more likely to be Outstanding Leadership or Service Excellence
        if any(term in role_lower for term in ["admin", "administrator", "manager", "coordinator"]):
            scores[EOMCategory.OUTSTANDING_LEADERSHIP] = scores.get(EOMCategory.OUTSTANDING_LEADERSHIP, 0) * 1.2
            scores[EOMCategory.SERVICE_EXCELLENCE] = scores.get(EOMCategory.SERVICE_EXCELLENCE, 0) * 1.1

        # Support roles are more likely to be Service Excellence or Team Spirit
        if any(term in role_lower for term in ["support", "assistant", "helper", "technician"]):
            scores[EOMCategory.SERVICE_EXCELLENCE] = scores.get(EOMCategory.SERVICE_EXCELLENCE, 0) * 1.2
            scores[EOMCategory.TEAM_SPIRIT] = scores.get(EOMCategory.TEAM_SPIRIT, 0) * 1.1

        return scores

    def _generate_reasoning(self, category: EOMCategory, scores: Dict, sentiment: float) -> str:
        """Generate human-readable reasoning for the recommendation"""
        category_name = category.value if hasattr(category, "value") else str(category)
        top_score = scores.get(category, 0)

        reasons = []

        if top_score > 0.5:
            reasons.append(f"Strong keyword matches for {category_name}")
        elif top_score > 0.3:
            reasons.append(f"Moderate keyword matches for {category_name}")

        if sentiment > 0.7:
            reasons.append("Highly positive sentiment in achievement description")
        elif sentiment < 0.4:
            reasons.append("Lower sentiment detected - may need review")

        # Check for close competitors
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_scores) > 1 and sorted_scores[1][1] > 0.3:
            second_category = sorted_scores[1][0]
            second_name = second_category.value if hasattr(second_category, "value") else str(second_category)
            reasons.append(f"Also consider: {second_name} (score: {sorted_scores[1][1]:.2f})")

        if not reasons:
            return f"Recommended {category_name} based on text analysis"

        return f"Recommended {category_name}. " + ". ".join(reasons) + "."

    def get_category_suggestions(self, achievement_text: str, top_n: int = 3) -> List[Tuple[str, float]]:
        """
        Get top N category suggestions with scores.

        Returns:
            List of tuples (category_name, score) sorted by score descending
        """
        result = self.suggest_category(achievement_text)
        all_scores = result["all_scores"]

        sorted_categories = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_categories[:top_n]
