"""
Example usage of the ParticipationAnalytics class.

This demonstrates how to:
1. Analyze participation rates by department and segment
2. View engagement trends over time
3. Detect outliers (departments with low participation)
4. Get predictions for future cycles
"""
from backend.participation_analytics import ParticipationAnalytics
from backend.database import get_db_session, Cycle


def example_analyze_participation():
    """Example of analyzing participation for a cycle."""
    
    db = get_db_session()
    
    try:
        # Get a cycle (example: cycle ID 1)
        cycle = db.query(Cycle).filter(Cycle.id == 1).first()
        
        if not cycle:
            print("No cycle found. Please create a cycle first.")
            return
        
        # Initialize analytics
        analytics = ParticipationAnalytics(db)
        
        # Analyze participation
        result = analytics.analyze_participation(cycle)
        
        print("=" * 80)
        print("PARTICIPATION ANALYSIS RESULTS")
        print("=" * 80)
        
        # Participation Rates
        print("\n1. PARTICIPATION RATES")
        print("-" * 80)
        
        overall = result['participation_rates']['overall']
        print(f"\nOverall Statistics:")
        print(f"  Total Assignments: {overall['total_assignments']}")
        print(f"  Completed: {overall['completed']}")
        print(f"  In Progress: {overall['in_progress']}")
        print(f"  Not Started: {overall['not_started']}")
        print(f"  Completion Rate: {overall['completion_rate']}%")
        print(f"  Participation Rate: {overall['participation_rate']}%")
        
        # By Department
        print(f"\nBy Department:")
        for dept, stats in result['participation_rates']['by_department'].items():
            print(f"  {dept}:")
            print(f"    Participation Rate: {stats['participation_rate']}%")
            print(f"    Completed: {stats['completed']}/{stats['total_assignments']}")
            print(f"    Unique People: {stats['unique_people']}")
        
        # By Segment
        print(f"\nBy Segment:")
        for segment, stats in result['participation_rates']['by_segment'].items():
            print(f"  {segment}:")
            print(f"    Participation Rate: {stats['participation_rate']}%")
            print(f"    Completed: {stats['completed']}/{stats['total_assignments']}")
            print(f"    Unique People: {stats['unique_people']}")
        
        # Engagement Trends
        print("\n2. ENGAGEMENT TRENDS")
        print("-" * 80)
        trends = result['engagement_trends']
        
        if trends.get('status') != 'insufficient_data':
            print(f"  Trend Direction: {trends['trend_direction']}")
            print(f"  Trend Strength: {trends['trend_strength']}%")
            print(f"  Total Evaluations: {trends['total_evaluations']}")
            print(f"  Submission Velocity: {trends['submission_velocity']} evaluations/day")
            print(f"  First Half Average: {trends['first_half_avg']} evaluations/day")
            print(f"  Second Half Average: {trends['second_half_avg']} evaluations/day")
            
            print(f"\n  Daily Submissions (last 5 days):")
            for day in trends['daily_submissions'][-5:]:
                print(f"    {day['date']}: {day['count']} evaluations")
        else:
            print(f"  {trends.get('message', 'Insufficient data for trend analysis')}")
        
        # Outlier Detection
        print("\n3. OUTLIER DETECTION")
        print("-" * 80)
        outliers = result['outlier_detection']
        
        print(f"  Threshold: {outliers['threshold']}%")
        print(f"  Low Participation Departments: {outliers['summary']['total_low_participation_departments']}")
        print(f"  Low Participation Segments: {outliers['summary']['total_low_participation_segments']}")
        print(f"  Statistical Outliers: {outliers['summary']['total_statistical_outliers']}")
        
        if outliers['low_participation_departments']:
            print(f"\n  Departments with Low Participation:")
            for dept in outliers['low_participation_departments']:
                print(f"    {dept['department']}:")
                print(f"      Participation Rate: {dept['participation_rate']}%")
                print(f"      Gap from Threshold: {dept['gap']}%")
                print(f"      Total Assignments: {dept['total_assignments']}")
        
        if outliers['statistical_outliers']:
            print(f"\n  Statistical Outliers:")
            for outlier in outliers['statistical_outliers']:
                print(f"    {outlier['type'].title()}: {outlier['name']}")
                print(f"      Participation Rate: {outlier['participation_rate']}%")
                print(f"      Mean: {outlier['mean']}%, Std Dev: {outlier['std_dev']}")
                print(f"      Deviation: {outlier['deviation']}%")
        
        # Predictions
        print("\n4. FUTURE PREDICTIONS")
        print("-" * 80)
        prediction = result['prediction']
        
        if prediction.get('status') != 'insufficient_data':
            print(f"  Current Participation Rate: {prediction['current_participation_rate']}%")
            print(f"  Average Historical Rate: {prediction['average_historical_rate']}%")
            print(f"  Trend: {prediction['trend']}%")
            print(f"  Predicted Next Cycle: {prediction['predicted_participation_rate']}%")
            print(f"  Confidence: {prediction['confidence']}%")
            
            print(f"\n  Historical Data:")
            for hist in prediction['historical_data'][:3]:  # Show last 3
                print(f"    {hist['cycle_code']}: {hist['participation_rate']}%")
            
            print(f"\n  Future Cycle Predictions:")
            for future in prediction['future_cycles']:
                print(f"    Cycle {future['cycle_number']}: {future['predicted_participation_rate']}% "
                      f"(confidence: {future['confidence']}%)")
            
            if prediction.get('recommendations'):
                print(f"\n  Recommendations:")
                for rec in prediction['recommendations']:
                    print(f"    - {rec}")
        else:
            print(f"  {prediction.get('message', 'Insufficient data for predictions')}")
        
        print("\n" + "=" * 80)
        
        return result
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def example_api_usage():
    """Example of using the API endpoint."""
    
    print("\n" + "=" * 80)
    print("API USAGE EXAMPLE")
    print("=" * 80)
    print("""
    To use the participation analytics via API:
    
    1. Start the FastAPI server:
       python -m backend.fastapi_app
    
    2. Make a GET request:
       curl http://localhost:8000/api/v2/analytics/participation/1
       
       Or in Python:
       import requests
       response = requests.get('http://localhost:8000/api/v2/analytics/participation/1')
       data = response.json()
    
    3. The response will include:
       - participation_rates: Rates by department and segment
       - engagement_trends: Trend analysis
       - outlier_detection: Low participation departments
       - prediction: Future cycle predictions
    """)


if __name__ == '__main__':
    # Run the example
    example_analyze_participation()
    
    # Show API usage
    example_api_usage()
