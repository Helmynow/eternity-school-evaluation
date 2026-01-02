"""
Example usage of the BiasFreeSuggestions class.

This demonstrates how to:
1. Get bias-free EOM nomination suggestions
2. Identify underrepresented groups
3. Analyze recent winning patterns
4. Calculate demographic balance
"""
from ai_models.bias_free_suggestions import BiasFreeSuggestions
from backend.database import get_db_session, Cycle


def example_bias_free_suggestions():
    """Example of getting bias-free EOM nomination suggestions."""
    
    db = get_db_session()
    
    try:
        # Get a cycle (example: cycle ID 1)
        cycle = db.query(Cycle).filter(Cycle.id == 1).first()
        
        if not cycle:
            print("No cycle found. Please create a cycle first.")
            return
        
        # Initialize bias-free suggestions
        suggester = BiasFreeSuggestions(db)
        
        # Get suggestions for a specific department (optional)
        suggestions = suggester.suggest_candidates(
            department=None,  # None = all departments
            cycle_id=cycle.id,
            limit=10
        )
        
        print("=" * 80)
        print("BIAS-FREE EOM NOMINATION SUGGESTIONS")
        print("=" * 80)
        
        # Display underrepresented groups
        print("\n1. UNDERREPRESENTED GROUPS")
        print("-" * 80)
        underrepresented = suggester.identify_underrepresented_groups(cycle.id)
        
        if underrepresented['by_department']:
            print("\n  By Department:")
            for dept, info in underrepresented['by_department'].items():
                print(f"    {dept}:")
                print(f"      Representation Rate: {info['representation_rate']}%")
                print(f"      Expected Rate: {info['expected_rate']}%")
                print(f"      Gap: {info['gap']}%")
        
        if underrepresented['by_segment']:
            print("\n  By Segment:")
            for segment, info in underrepresented['by_segment'].items():
                print(f"    {segment}:")
                print(f"      Representation Rate: {info['representation_rate']}%")
                print(f"      Expected Rate: {info['expected_rate']}%")
                print(f"      Gap: {info['gap']}%")
        
        # Display recent winning patterns
        print("\n2. RECENT WINNING PATTERNS")
        print("-" * 80)
        recent_winners = suggester.get_recent_winning_patterns(cycle.id)
        
        print(f"  Total Winners: {recent_winners['total_winners']}")
        print(f"  Most Common Department: {recent_winners['patterns'].get('most_common_department', 'N/A')}")
        print(f"  Most Common Segment: {recent_winners['patterns'].get('most_common_segment', 'N/A')}")
        print(f"  Repeat Winner Rate: {recent_winners['patterns'].get('repeat_winner_rate', 0):.1f}%")
        
        if recent_winners['repeat_winners']:
            print(f"\n  Repeat Winners:")
            for repeat in recent_winners['repeat_winners'][:5]:
                print(f"    {repeat['email']}: {repeat['win_count']} wins")
        
        # Display suggestions
        print("\n3. CANDIDATE SUGGESTIONS (Top 10)")
        print("-" * 80)
        
        for i, suggestion in enumerate(suggestions, 1):
            candidate = suggestion['candidate']
            print(f"\n  {i}. {candidate['full_name']} ({candidate['email']})")
            print(f"     Department: {candidate.get('department', 'N/A')}")
            print(f"     Segment: {candidate.get('segment', 'N/A')}")
            print(f"     Overall Score: {suggestion['overall_score']:.3f}")
            print(f"     Novelty Factor: {suggestion['novelty_factor']:.3f}")
            print(f"     Representation Score: {suggestion['representation_score']:.3f}")
            
            # Performance metrics
            perf = suggestion.get('performance_metrics', {})
            if perf:
                print(f"     Avg Rating: {perf.get('avg_rating', 0):.2f}")
                print(f"     Rating Count: {perf.get('rating_count', 0)}")
                print(f"     Context Diversity: {perf.get('context_diversity', 0)}")
            
            # Bias indicators
            bias_indicators = suggestion.get('bias_indicators', {})
            if bias_indicators.get('repeat_winner_risk'):
                print(f"     ⚠️  Repeat Winner Risk: {bias_indicators.get('repeat_winner_count', 0)} previous wins")
            if bias_indicators.get('pattern_match_risk'):
                print(f"     ⚠️  Pattern Match Risk: Matches recent winning patterns")
            
            # Bias flags
            bias_flags = suggestion.get('bias_flags', [])
            if bias_flags:
                print(f"     Bias Flags:")
                for flag in bias_flags:
                    print(f"       - {flag}")
            
            # Recommended actions
            actions = suggestion.get('suggested_action', [])
            if actions:
                print(f"     Recommended Actions:")
                for action in actions:
                    print(f"       • {action}")
        
        print("\n" + "=" * 80)
        
        return suggestions
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def example_underrepresented_analysis():
    """Example of analyzing underrepresented groups."""
    
    db = get_db_session()
    
    try:
        suggester = BiasFreeSuggestions(db)
        
        # Get underrepresented groups
        underrepresented = suggester.identify_underrepresented_groups()
        
        print("=" * 80)
        print("UNDERREPRESENTED GROUPS ANALYSIS")
        print("=" * 80)
        
        print("\nDepartments needing better representation:")
        for dept, info in underrepresented['by_department'].items():
            print(f"  {dept}: {info['gap']}% below expected representation")
        
        print("\nSegments needing better representation:")
        for segment, info in underrepresented['by_segment'].items():
            print(f"  {segment}: {info['gap']}% below expected representation")
        
        print("\nRoles needing better representation:")
        for role, info in underrepresented['by_role'].items():
            print(f"  {role}: {info['gap']}% below expected representation")
        
        return underrepresented
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == '__main__':
    # Run examples
    print("Example 1: Bias-Free Suggestions")
    print("=" * 80)
    example_bias_free_suggestions()
    
    print("\n\nExample 2: Underrepresented Groups Analysis")
    print("=" * 80)
    example_underrepresented_analysis()
