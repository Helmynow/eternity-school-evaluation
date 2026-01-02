"""
AI-powered category suggestions based on achievement description.
Simplified interface for category recommendation.
"""
from typing import Optional, Dict
from backend.ai_models.eom_category_recommender import EOMCategoryRecommender


class CategoryRecommender:
    """
    AI-powered category suggestions based on achievement description.
    Provides a simplified interface for EOM category recommendation.
    """
    
    def __init__(self):
        """Initialize the category recommender"""
        self.recommender = EOMCategoryRecommender()
    
    def suggest_category(self, achievement_text: str, nominee_role: Optional[str] = None) -> str:
        """
        Suggest EOM category based on achievement description.
        
        Args:
            achievement_text: The achievement description (e.g., "Led digital attendance reform and trained peers")
            nominee_role: Optional role/title of the nominee for better context
        
        Returns:
            Formatted string with category name and confidence score (e.g., "Outstanding Leadership (confidence: 4.7/5)")
        """
        if not achievement_text or not achievement_text.strip():
            return "No category suggested (confidence: 0.0/5)"
        
        # Get recommendation from the underlying recommender
        result = self.recommender.suggest_category(achievement_text, nominee_role)
        
        recommended_category = result.get('recommended_category')
        confidence_score = result.get('confidence_score', 0.0)
        
        if not recommended_category:
            return f"No category suggested (confidence: {confidence_score * 5:.1f}/5)"
        
        # Convert category value to display name
        category_display = self._format_category_name(recommended_category)
        
        # Convert confidence (0-1) to 0-5 scale
        confidence_5_scale = confidence_score * 5
        
        return f"{category_display} (confidence: {confidence_5_scale:.1f}/5)"
    
    def suggest_category_detailed(self, achievement_text: str, nominee_role: Optional[str] = None) -> Dict:
        """
        Get detailed category suggestion with full information.
        
        Args:
            achievement_text: The achievement description
            nominee_role: Optional role/title of the nominee
        
        Returns:
            Dictionary with:
            - category: Category name
            - confidence: Confidence score (0-5 scale)
            - confidence_raw: Raw confidence (0-1 scale)
            - all_scores: Scores for all categories
            - reasoning: Explanation of the recommendation
        """
        if not achievement_text or not achievement_text.strip():
            return {
                'category': None,
                'confidence': 0.0,
                'confidence_raw': 0.0,
                'all_scores': {},
                'reasoning': 'No achievement text provided'
            }
        
        result = self.recommender.suggest_category(achievement_text, nominee_role)
        
        recommended_category = result.get('recommended_category')
        confidence_raw = result.get('confidence_score', 0.0)
        confidence_5_scale = confidence_raw * 5
        
        category_display = self._format_category_name(recommended_category) if recommended_category else None
        
        return {
            'category': category_display,
            'category_value': recommended_category,
            'confidence': round(confidence_5_scale, 1),
            'confidence_raw': round(confidence_raw, 2),
            'all_scores': result.get('all_scores', {}),
            'reasoning': result.get('reasoning', '')
        }
    
    def _format_category_name(self, category_value: str) -> str:
        """
        Convert category enum value to display name.
        
        Args:
            category_value: Category enum value (e.g., "outstanding_leadership")
        
        Returns:
            Formatted category name (e.g., "Outstanding Leadership")
        """
        # Map category values to display names
        category_map = {
            'outstanding_leadership': 'Outstanding Leadership',
            'team_spirit': 'Team Spirit',
            'innovation': 'Innovation',
            'rising_star': 'Rising Star',
            'service_excellence': 'Service Excellence'
        }
        
        # Return formatted name or capitalize if not in map
        if category_value in category_map:
            return category_map[category_value]
        
        # Fallback: capitalize and replace underscores
        return category_value.replace('_', ' ').title()
