"""
Example usage of the CategoryRecommender class.

This demonstrates how to:
1. Get category suggestions from achievement descriptions
2. Get detailed category recommendations with confidence scores
"""
from ai_models.category_recommender import CategoryRecommender


def example_basic_suggestion():
    """Example of basic category suggestion."""
    
    recommender = CategoryRecommender()
    
    # Example from user query
    achievement = "Led digital attendance reform and trained peers"
    suggestion = recommender.suggest_category(achievement)
    
    print("=" * 80)
    print("CATEGORY RECOMMENDATION EXAMPLE")
    print("=" * 80)
    print(f"\nAchievement: {achievement}")
    print(f"Suggested Category: {suggestion}")
    
    return suggestion


def example_multiple_achievements():
    """Example of suggesting categories for multiple achievements."""
    
    recommender = CategoryRecommender()
    
    achievements = [
        "Led digital attendance reform and trained peers",
        "Organized peer tutoring among teachers and eased inter-department tension",
        "Developed a student feedback dashboard for the lesson plan",
        "Reworked an entire classroom setup within two weeks of hire",
        "Zero late marks, submits reports early, no task reminders needed"
    ]
    
    print("\n" + "=" * 80)
    print("MULTIPLE ACHIEVEMENT EXAMPLES")
    print("=" * 80)
    
    for achievement in achievements:
        suggestion = recommender.suggest_category(achievement)
        print(f"\nAchievement: {achievement}")
        print(f"Suggested: {suggestion}")


def example_detailed_suggestion():
    """Example of getting detailed category suggestion."""
    
    recommender = CategoryRecommender()
    
    achievement = "Led digital attendance reform and trained peers"
    detailed = recommender.suggest_category_detailed(achievement)
    
    print("\n" + "=" * 80)
    print("DETAILED CATEGORY RECOMMENDATION")
    print("=" * 80)
    print(f"\nAchievement: {achievement}")
    print(f"\nDetailed Results:")
    print(f"  Category: {detailed['category']}")
    print(f"  Confidence: {detailed['confidence']}/5")
    print(f"  Raw Confidence: {detailed['confidence_raw']}")
    print(f"  Reasoning: {detailed['reasoning']}")
    
    if detailed['all_scores']:
        print(f"\n  All Category Scores:")
        for category, score in sorted(detailed['all_scores'].items(), key=lambda x: x[1], reverse=True):
            print(f"    {category}: {score:.2f}")
    
    return detailed


def example_with_role_context():
    """Example of suggesting category with role context."""
    
    recommender = CategoryRecommender()
    
    achievement = "Led digital attendance reform and trained peers"
    
    # Without role context
    suggestion1 = recommender.suggest_category(achievement)
    
    # With role context (teacher)
    suggestion2 = recommender.suggest_category(achievement, nominee_role="Teacher")
    
    # With role context (administrator)
    suggestion3 = recommender.suggest_category(achievement, nominee_role="Administrator")
    
    print("\n" + "=" * 80)
    print("CATEGORY SUGGESTION WITH ROLE CONTEXT")
    print("=" * 80)
    print(f"\nAchievement: {achievement}")
    print(f"\nWithout role context: {suggestion1}")
    print(f"With role 'Teacher': {suggestion2}")
    print(f"With role 'Administrator': {suggestion3}")


if __name__ == '__main__':
    # Run examples
    print("Example 1: Basic Category Suggestion")
    example_basic_suggestion()
    
    print("\n\nExample 2: Multiple Achievements")
    example_multiple_achievements()
    
    print("\n\nExample 3: Detailed Suggestion")
    example_detailed_suggestion()
    
    print("\n\nExample 4: With Role Context")
    example_with_role_context()
