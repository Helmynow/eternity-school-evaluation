"""
Advanced bias detection algorithms using machine learning approaches.
"""
import numpy as np
from typing import List, Dict, Tuple
from collections import defaultdict
from backend.database import Evaluation, Assignment, Person
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN


class AdvancedBiasAlgorithms:
    """Advanced ML-based bias detection"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def detect_outlier_ratings(self, cycle_id: int, contamination: float = 0.1) -> Dict:
        """
        Use Isolation Forest to detect outlier ratings that might indicate bias.
        Outliers could be unusually harsh or lenient ratings.
        """
        evaluations = self.db.query(Evaluation).join(Assignment).filter(
            Assignment.cycle_id == cycle_id,
            Evaluation.status == 'submitted',
            Evaluation.rating.isnot(None)
        ).all()
        
        if len(evaluations) < 20:
            return {'status': 'insufficient_data', 'message': 'Need at least 20 evaluations'}
        
        # Prepare features
        features = []
        eval_ids = []
        
        for eval in evaluations:
            assignment = self.db.query(Assignment).filter(
                Assignment.id == eval.assignment_id
            ).first()
            if assignment:
                # Features: rating, context encoding, target group encoding
                context_encoding = hash(assignment.rater_context) % 10
                group_encoding = hash(assignment.target_group) % 10
                
                features.append([
                    eval.rating,
                    context_encoding,
                    group_encoding
                ])
                eval_ids.append(eval.id)
        
        if len(features) < 20:
            return {'status': 'insufficient_data'}
        
        # Detect outliers
        iso_forest = IsolationForest(contamination=contamination, random_state=42)
        features_array = np.array(features)
        outlier_labels = iso_forest.fit_predict(features_array)
        
        outliers = []
        for i, label in enumerate(outlier_labels):
            if label == -1:  # Outlier
                eval = self.db.query(Evaluation).filter(Evaluation.id == eval_ids[i]).first()
                assignment = self.db.query(Assignment).filter(
                    Assignment.id == eval.assignment_id
                ).first()
                
                outliers.append({
                    'evaluation_id': eval_ids[i],
                    'rating': float(eval.rating),
                    'rater_email': assignment.rater_email if assignment else None,
                    'target_email': assignment.target_email if assignment else None,
                    'context': assignment.rater_context if assignment else None,
                    'features': features[i].tolist()
                })
        
        return {
            'status': 'analyzed',
            'total_evaluations': len(evaluations),
            'outliers_detected': len(outliers),
            'outlier_rate': len(outliers) / len(evaluations),
            'outliers': outliers
        }
    
    def detect_rating_clusters(self, cycle_id: int, eps: float = 0.5) -> Dict:
        """
        Use DBSCAN clustering to detect groups of similar rating patterns.
        Can identify cliques or groups with similar evaluation behaviors.
        """
        evaluations = self.db.query(Evaluation).join(Assignment).filter(
            Assignment.cycle_id == cycle_id,
            Evaluation.status == 'submitted',
            Evaluation.rating.isnot(None)
        ).all()
        
        if len(evaluations) < 20:
            return {'status': 'insufficient_data'}
        
        # Build rater-target rating matrix
        rater_target_ratings = defaultdict(lambda: defaultdict(list))
        
        for eval in evaluations:
            assignment = self.db.query(Assignment).filter(
                Assignment.id == eval.assignment_id
            ).first()
            if assignment:
                rater_target_ratings[assignment.rater_email][assignment.target_email].append(
                    eval.rating
                )
        
        # Create feature vectors for each rater (average rating they give to each target)
        raters = sorted(rater_target_ratings.keys())
        targets = sorted(set(
            target for rater_dict in rater_target_ratings.values()
            for target in rater_dict.keys()
        ))
        
        if len(raters) < 5 or len(targets) < 5:
            return {'status': 'insufficient_data'}
        
        feature_matrix = []
        for rater in raters:
            features = []
            for target in targets:
                if target in rater_target_ratings[rater]:
                    avg_rating = np.mean(rater_target_ratings[rater][target])
                    features.append(avg_rating)
                else:
                    features.append(0.0)  # No rating given
            feature_matrix.append(features)
        
        feature_matrix = np.array(feature_matrix)
        
        # Normalize features
        scaler = StandardScaler()
        feature_matrix_scaled = scaler.fit_transform(feature_matrix)
        
        # Cluster
        clustering = DBSCAN(eps=eps, min_samples=2)
        cluster_labels = clustering.fit_predict(feature_matrix_scaled)
        
        # Organize results
        clusters = defaultdict(list)
        noise = []
        
        for i, label in enumerate(cluster_labels):
            if label == -1:
                noise.append(raters[i])
            else:
                clusters[label].append(raters[i])
        
        return {
            'status': 'analyzed',
            'num_clusters': len(clusters),
            'noise_points': len(noise),
            'clusters': {str(k): v for k, v in clusters.items()},
            'noise': noise,
            'interpretation': 'Clusters may indicate groups with similar evaluation patterns'
        }
    
    def detect_reciprocal_bias(self, cycle_id: int) -> Dict:
        """
        Detect reciprocal bias - when person A rates person B highly,
        and person B also rates person A highly (mutual high ratings).
        """
        evaluations = self.db.query(Evaluation).join(Assignment).filter(
            Assignment.cycle_id == cycle_id,
            Evaluation.status == 'submitted',
            Evaluation.rating.isnot(None)
        ).all()
        
        if len(evaluations) < 10:
            return {'status': 'insufficient_data'}
        
        # Build rating dictionary
        ratings = {}
        for eval in evaluations:
            assignment = self.db.query(Assignment).filter(
                Assignment.id == eval.assignment_id
            ).first()
            if assignment:
                key = (assignment.rater_email, assignment.target_email)
                ratings[key] = eval.rating
        
        # Find reciprocal pairs
        reciprocal_pairs = []
        checked_pairs = set()
        
        for (rater, target), rating in ratings.items():
            reverse_key = (target, rater)
            if reverse_key in ratings and (rater, target) not in checked_pairs:
                reverse_rating = ratings[reverse_key]
                
                # Both rate each other highly (above 4.0 on 5-point scale)
                if rating >= 4.0 and reverse_rating >= 4.0:
                    reciprocal_pairs.append({
                        'person_a': rater,
                        'person_b': target,
                        'a_rates_b': float(rating),
                        'b_rates_a': float(reverse_rating),
                        'avg_rating': float((rating + reverse_rating) / 2)
                    })
                    checked_pairs.add((rater, target))
                    checked_pairs.add((target, rater))
        
        return {
            'status': 'analyzed',
            'reciprocal_pairs_count': len(reciprocal_pairs),
            'reciprocal_pairs': reciprocal_pairs,
            'interpretation': 'High mutual ratings may indicate reciprocal bias or genuine mutual respect'
        }
    
    def detect_systematic_bias_patterns(self, cycle_id: int) -> Dict:
        """
        Detect systematic bias patterns across the organization.
        Looks for patterns in how different groups rate each other.
        """
        evaluations = self.db.query(Evaluation).join(Assignment).filter(
            Assignment.cycle_id == cycle_id,
            Evaluation.status == 'submitted',
            Evaluation.rating.isnot(None)
        ).all()
        
        if len(evaluations) < 20:
            return {'status': 'insufficient_data'}
        
        # Group by rater context and target group
        context_group_ratings = defaultdict(list)
        
        for eval in evaluations:
            assignment = self.db.query(Assignment).filter(
                Assignment.id == eval.assignment_id
            ).first()
            if assignment:
                key = (assignment.rater_context, assignment.target_group)
                context_group_ratings[key].append(eval.rating)
        
        # Calculate statistics for each combination
        patterns = {}
        for (context, group), ratings in context_group_ratings.items():
            if len(ratings) >= 3:
                patterns[f"{context}->{group}"] = {
                    'count': len(ratings),
                    'mean': float(np.mean(ratings)),
                    'std': float(np.std(ratings)),
                    'median': float(np.median(ratings))
                }
        
        # Identify patterns
        overall_mean = np.mean([r for ratings in context_group_ratings.values() for r in ratings])
        
        high_patterns = []
        low_patterns = []
        
        for pattern_name, stats in patterns.items():
            if stats['mean'] > overall_mean + 0.5:
                high_patterns.append({
                    'pattern': pattern_name,
                    'mean_rating': stats['mean'],
                    'overall_mean': float(overall_mean),
                    'difference': stats['mean'] - overall_mean
                })
            elif stats['mean'] < overall_mean - 0.5:
                low_patterns.append({
                    'pattern': pattern_name,
                    'mean_rating': stats['mean'],
                    'overall_mean': float(overall_mean),
                    'difference': stats['mean'] - overall_mean
                })
        
        return {
            'status': 'analyzed',
            'overall_mean': float(overall_mean),
            'patterns': patterns,
            'high_rating_patterns': high_patterns,
            'low_rating_patterns': low_patterns,
            'interpretation': 'Systematic differences may indicate organizational bias patterns'
        }

