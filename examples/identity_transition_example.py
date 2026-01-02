"""
Example usage of the IdentityTransitionManager class.

This demonstrates how to:
1. Transition anonymous users to identified users
2. Link anonymous survey responses to identified accounts
3. Handle consent requirements and grace periods
4. Verify and complete transitions
"""
from backend.identity_transition_manager import IdentityTransitionManager
from backend.database import get_db_session


def example_anonymous_to_identified_transition():
    """Example of transitioning an anonymous user to identified."""
    
    db = get_db_session()
    
    try:
        # Initialize manager
        manager = IdentityTransitionManager(db_session=db)
        
        # Anonymous user wants to reveal identity
        anonymous_id = "anon_session_abc123"  # Session ID or cookie ID
        user_id = "user@example.com"  # User email
        
        print("=" * 80)
        print("ANONYMOUS TO IDENTIFIED TRANSITION")
        print("=" * 80)
        
        # Initiate transition
        result = manager.transition_to_identified(
            anonymous_id=anonymous_id,
            user_id=user_id,
            survey_id=None  # Optional: limit to specific survey
        )
        
        print(f"\nTransition Status: {result['status']}")
        
        if result['status'] == 'success':
            print(f"\n1. Transition Token:")
            print(f"   Token: {result['transition_token']}")
            
            print(f"\n2. Previous Responses:")
            responses = result['previous_responses']
            print(f"   Status: {responses['status']}")
            print(f"   Linked Count: {responses['linked_count']}")
            if responses.get('response_ids'):
                print(f"   Response IDs: {responses['response_ids']}")
            
            print(f"\n3. Consent Required:")
            consent = result['consent_required']
            print(f"   Confirmation Required: {consent['confirmation_required']}")
            print(f"   Cooling Period: {consent['cooling_period_days']} days")
            print(f"   Consent Items:")
            for item in consent['consent_items']:
                print(f"     - {item['description']} (Required: {item['required']})")
            
            print(f"\n4. Grace Period:")
            grace = result['grace_period']
            print(f"   Start: {grace['start_date']}")
            print(f"   End: {grace['end_date']}")
            print(f"   Duration: {grace['duration_days']} days")
            print(f"   Can Revert: {grace['can_revert']}")
        else:
            print(f"\nError: {result.get('message', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def example_verify_and_complete_transition():
    """Example of verifying and completing a transition token."""
    
    db = get_db_session()
    
    try:
        manager = IdentityTransitionManager(db_session=db)
        
        # Get a transition token (from previous example)
        anonymous_id = "anon_session_abc123"
        user_id = "user@example.com"
        
        transition_result = manager.transition_to_identified(anonymous_id, user_id)
        
        if transition_result['status'] == 'success':
            token = transition_result['transition_token']
            
            print("\n" + "=" * 80)
            print("VERIFY AND COMPLETE TRANSITION")
            print("=" * 80)
            
            # Verify token
            print(f"\n1. Verifying Token: {token[:20]}...")
            verification = manager.verify_transition_token(token)
            
            if verification['valid']:
                print(f"   ✓ Token is valid")
                print(f"   Anonymous ID: {verification['anonymous_id']}")
                print(f"   User ID: {verification['user_id']}")
                print(f"   Expires: {verification['expires_at']}")
                
                # Complete transition
                print(f"\n2. Completing Transition...")
                completion = manager.complete_transition(token)
                
                print(f"   Status: {completion['status']}")
                print(f"   Message: {completion['message']}")
            else:
                print(f"   ✗ Token is invalid: {verification['message']}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def example_revert_transition():
    """Example of reverting a transition during grace period."""
    
    db = get_db_session()
    
    try:
        manager = IdentityTransitionManager(db_session=db)
        
        # Create a transition
        anonymous_id = "anon_session_abc123"
        user_id = "user@example.com"
        
        transition_result = manager.transition_to_identified(anonymous_id, user_id)
        
        if transition_result['status'] == 'success':
            token = transition_result['transition_token']
            
            print("\n" + "=" * 80)
            print("REVERT TRANSITION (GRACE PERIOD)")
            print("=" * 80)
            
            # Revert transition
            print(f"\nReverting transition with token: {token[:20]}...")
            revert_result = manager.revert_transition(token)
            
            print(f"Status: {revert_result['status']}")
            print(f"Message: {revert_result['message']}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == '__main__':
    # Run examples
    print("Example 1: Anonymous to Identified Transition")
    example_anonymous_to_identified_transition()
    
    print("\n\nExample 2: Verify and Complete Transition")
    example_verify_and_complete_transition()
    
    print("\n\nExample 3: Revert Transition")
    example_revert_transition()
