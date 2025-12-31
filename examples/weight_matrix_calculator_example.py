"""
Example usage of WeightMatrixCalculator.
Demonstrates how to use the simplified weight matrix calculator.
"""
from backend.weight_matrix_calculator import WeightMatrixCalculator
from backend.weight_matrix_handler import WeightMatrixHandler


def example_basic_usage():
    """Basic usage example"""
    # Option 1: Use default weight matrix
    calculator = WeightMatrixCalculator()
    
    # Calculate weighted evaluation for academic target with CEO rater
    scores = {'overall': 4.5}
    weighted_score = calculator.calculate_weighted_evaluation(
        target_group='academic',
        rater_context='CEO',
        scores=scores
    )
    
    print(f"Academic target, CEO rater, score 4.5")
    print(f"Weighted score: {weighted_score}")
    # CEO weight is 1.0, so result should be 4.5
    
    # Calculate with P&C rater (weight 0.8)
    weighted_score_pc = calculator.calculate_weighted_evaluation(
        target_group='academic',
        rater_context='P&C',
        scores=scores
    )
    
    print(f"\nAcademic target, P&C rater, score 4.5")
    print(f"Weighted score: {weighted_score_pc}")
    # P&C weight is 0.8, so result should be 4.5 * 0.8 = 3.6


def example_multiple_domain_scores():
    """Example with multiple domain scores"""
    calculator = WeightMatrixCalculator()
    
    # Multiple domain scores
    scores = {
        'teaching': 4.0,
        'collaboration': 3.5,
        'leadership': 4.2,
        'innovation': 3.8
    }
    
    weighted_score = calculator.calculate_weighted_evaluation(
        target_group='academic',
        rater_context='CEO',
        scores=scores
    )
    
    print(f"\nMultiple domain scores: {scores}")
    print(f"Weighted score (CEO, weight 1.0): {weighted_score}")
    # Should be average of scores * 1.0 = (4.0 + 3.5 + 4.2 + 3.8) / 4 = 3.875


def example_custom_config():
    """Example with custom weight matrix configuration"""
    custom_config = {
        'academic': {
            'CEO': 1.0,
            'P&C': 0.8,
            'QA': 0.9,
            'peer_review': 0.7
        },
        'admin': {
            'CEO': 1.0,
            'P&C': 0.9,
            'QA': 0.7
        }
    }
    
    calculator = WeightMatrixCalculator(custom_config)
    
    scores = {'overall': 4.0}
    
    # Test different combinations
    combinations = [
        ('academic', 'CEO'),
        ('academic', 'P&C'),
        ('admin', 'QA'),
        ('unknown_group', 'CEO')  # Should use fallback
    ]
    
    print("\n" + "=" * 60)
    print("CUSTOM CONFIG EXAMPLES")
    print("=" * 60)
    
    for target_group, rater_context in combinations:
        weighted_score = calculator.calculate_weighted_evaluation(
            target_group=target_group,
            rater_context=rater_context,
            scores=scores
        )
        
        weight = calculator.get_weight(target_group, rater_context)
        print(f"\n{target_group} / {rater_context}:")
        print(f"  Weight: {weight}")
        print(f"  Score: {scores['overall']}")
        print(f"  Weighted Score: {weighted_score}")


def example_batch_processing():
    """Example of batch processing multiple evaluations"""
    calculator = WeightMatrixCalculator()
    
    evaluations = [
        {
            'target_group': 'academic',
            'rater_context': 'CEO',
            'scores': {'overall': 4.5}
        },
        {
            'target_group': 'academic',
            'rater_context': 'P&C',
            'scores': {'overall': 4.0}
        },
        {
            'target_group': 'admin',
            'rater_context': 'QA',
            'scores': {'overall': 3.8}
        },
        {
            'target_group': 'academic',
            'rater_context': 'peer_review',
            'scores': {
                'teaching': 4.0,
                'collaboration': 3.5,
                'leadership': 4.2
            }
        }
    ]
    
    results = calculator.calculate_weighted_evaluation_batch(evaluations)
    
    print("\n" + "=" * 60)
    print("BATCH PROCESSING RESULTS")
    print("=" * 60)
    
    for i, result in enumerate(results, 1):
        print(f"\nEvaluation {i}:")
        print(f"  Target Group: {result['target_group']}")
        print(f"  Rater Context: {result['rater_context']}")
        print(f"  Scores: {result['scores']}")
        print(f"  Weight Applied: {result['weight_applied']}")
        print(f"  Weighted Score: {result['weighted_score']:.2f}")


def example_apply_weights_directly():
    """Example of using apply_weights method directly"""
    calculator = WeightMatrixCalculator()
    
    # Example 1: Single weight value
    scores = {'teaching': 4.0, 'collaboration': 3.5}
    weights = 0.8
    
    result = calculator.apply_weights(scores, weights)
    print(f"\nScores: {scores}")
    print(f"Single weight: {weights}")
    print(f"Result: {result}")
    # Should be: (4.0 + 3.5) / 2 * 0.8 = 3.0
    
    # Example 2: Dictionary of weights
    scores2 = {
        'teaching': 4.0,
        'collaboration': 3.5,
        'leadership': 4.2
    }
    weights2 = {
        'teaching': 0.4,
        'collaboration': 0.3,
        'leadership': 0.3
    }
    
    result2 = calculator.apply_weights(scores2, weights2)
    print(f"\nScores: {scores2}")
    print(f"Weights: {weights2}")
    print(f"Result: {result2:.2f}")
    # Should be: 4.0*0.4 + 3.5*0.3 + 4.2*0.3 = 3.91


def example_update_config():
    """Example of updating weight matrix configuration"""
    calculator = WeightMatrixCalculator()
    
    print("\n" + "=" * 60)
    print("UPDATING CONFIGURATION")
    print("=" * 60)
    
    # Get original weight
    original_weight = calculator.get_weight('academic', 'CEO')
    print(f"\nOriginal weight for academic/CEO: {original_weight}")
    
    # Update weight
    calculator.update_config('academic', 'CEO', 1.2)
    new_weight = calculator.get_weight('academic', 'CEO')
    print(f"Updated weight for academic/CEO: {new_weight}")
    
    # Add new group and context
    calculator.update_config('new_group', 'new_context', 0.9)
    new_group_weight = calculator.get_weight('new_group', 'new_context')
    print(f"New group/context weight: {new_group_weight}")
    
    # Get full config
    config = calculator.get_config()
    print(f"\nConfig has {len(config)} target groups")


if __name__ == '__main__':
    print("=" * 60)
    print("WEIGHT MATRIX CALCULATOR EXAMPLES")
    print("=" * 60)
    
    example_basic_usage()
    example_multiple_domain_scores()
    example_custom_config()
    example_batch_processing()
    example_apply_weights_directly()
    example_update_config()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)

