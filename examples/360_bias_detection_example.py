"""
Example usage of Complete 360-Degree Bias Detection System.
"""
from backend.database import Database
from backend.bias_detection_360 import Complete360BiasDetection


def main():
    # Initialize database
    db = Database()
    db_session = db.get_session()
    
    # Example: Generate complete bias report for cycle ID 1
    cycle_id = 1
    
    # Create detector
    detector = Complete360BiasDetection(db_session)
    
    # Generate complete report
    print("=== Generating Complete 360-Degree Bias Report ===")
    report = detector.generate_complete_report(cycle_id)
    
    print(f"\nCycle ID: {report.cycle_id}")
    print(f"Overall Bias Score: {report.overall_bias_score:.3f}")
    print(f"Bias Level: {detector._score_to_level(report.overall_bias_score)}")
    print(f"Total Evaluations: {report.total_evaluations}")
    print(f"Total Raters: {report.total_raters}")
    print(f"Total Targets: {report.total_targets}")
    print(f"Findings Count: {len(report.findings)}")
    
    # Display findings
    print("\n=== Bias Findings ===")
    for i, finding in enumerate(report.findings, 1):
        print(f"\n{i}. {finding.bias_type.upper()} ({finding.severity.upper()})")
        print(f"   Score: {finding.score:.3f}")
        print(f"   Description: {finding.description}")
        if finding.affected_raters:
            print(f"   Affected Raters: {len(finding.affected_raters)}")
        if finding.affected_targets:
            print(f"   Affected Targets: {len(finding.affected_targets)}")
        print(f"   Recommendations:")
        for rec in finding.recommendations:
            print(f"     - {rec}")
    
    # Display context coverage
    print("\n=== Context Coverage ===")
    for context, data in report.context_coverage.items():
        print(f"{context}:")
        print(f"  Total Assignments: {data['total_assignments']}")
        print(f"  Unique Targets: {data['unique_targets']}")
        print(f"  Avg per Target: {data['avg_evaluations_per_target']:.2f}")
    
    # Display statistical summary
    print("\n=== Statistical Summary ===")
    stats = report.statistical_summary
    print(f"Mean Rating: {stats.get('mean_rating', 0):.2f}")
    print(f"Std Rating: {stats.get('std_rating', 0):.2f}")
    print(f"Min Rating: {stats.get('min_rating', 0):.2f}")
    print(f"Max Rating: {stats.get('max_rating', 0):.2f}")
    print(f"Median Rating: {stats.get('median_rating', 0):.2f}")
    
    # Display overall recommendations
    print("\n=== Overall Recommendations ===")
    for i, rec in enumerate(report.recommendations, 1):
        print(f"{i}. {rec}")
    
    # Example: Get bias summary for specific target
    print("\n=== Target-Specific Analysis ===")
    target_email = 'teacher1@eternity.edu'
    target_summary = detector.get_bias_summary_by_target(cycle_id, target_email)
    
    if target_summary.get('status') == 'analyzed':
        print(f"\nTarget: {target_summary['target_email']}")
        print(f"Total Evaluations: {target_summary['total_evaluations']}")
        print(f"Mean Rating: {target_summary['mean_rating']:.2f}")
        print(f"Is Complete 360: {target_summary['is_complete_360']}")
        print(f"Missing Contexts: {target_summary.get('missing_contexts', [])}")
        print(f"Inter-Rater Reliability: {target_summary['inter_rater_reliability']['interpretation']}")
        
        print("\nContext Breakdown:")
        for context, data in target_summary['context_breakdown'].items():
            print(f"  {context}:")
            print(f"    Count: {data['count']}")
            print(f"    Mean: {data['mean']:.2f}")
            print(f"    Std: {data['std']:.2f}")
    
    # Export to dictionary (for API responses)
    print("\n=== Export Report ===")
    export_data = detector.export_report_to_dict(report)
    print(f"Exported report with {len(export_data['findings'])} findings")
    print(f"Findings by type: {export_data['findings_by_type']}")
    print(f"Findings by severity: {export_data['findings_by_severity']}")
    
    # Clean up
    db_session.close()


if __name__ == '__main__':
    main()

