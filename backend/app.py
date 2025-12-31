"""
Main Flask application for the Eternity School Evaluation System.
"""
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from backend.database import Database, Cycle, Person, Assignment, Evaluation, EOMCycle, EOMNominee
from backend.weight_matrix import WeightMatrix
from backend.weight_matrix_handler import WeightMatrixHandler
from backend.bias_detection import BiasDetector
from backend.eom_validation import EOMNominationValidator
from backend.360_bias_detection import Complete360BiasDetection
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Initialize database
db = Database()
db_session = db.get_session()

@app.route('/')
def index():
    """Home page"""
    return jsonify({
        'message': 'Eternity School Evaluation System API',
        'version': '1.0.0',
        'endpoints': {
            'cycles': '/api/cycles',
            'people': '/api/people',
            'assignments': '/api/assignments',
            'evaluations': '/api/evaluations',
            'weight_matrix': '/api/cycles/<id>/weight_matrix',
            'bias_detection': '/api/cycles/<id>/bias'
        }
    })


# Cycles endpoints
@app.route('/api/cycles', methods=['GET', 'POST'])
def cycles():
    """Get all cycles or create a new cycle"""
    if request.method == 'GET':
        cycles = db_session.query(Cycle).all()
        return jsonify([{
            'id': c.id,
            'code': c.code,
            'name': c.name,
            'start_date': c.start_date.isoformat() if c.start_date else None,
            'end_date': c.end_date.isoformat() if c.end_date else None,
            'status': c.status
        } for c in cycles])
    
    elif request.method == 'POST':
        data = request.json
        cycle = Cycle(
            code=data['code'],
            name=data.get('name'),
            start_date=datetime.fromisoformat(data['start_date']) if data.get('start_date') else None,
            end_date=datetime.fromisoformat(data['end_date']) if data.get('end_date') else None,
            status=data.get('status', 'draft')
        )
        db_session.add(cycle)
        db_session.commit()
        return jsonify({'id': cycle.id, 'message': 'Cycle created'}), 201


@app.route('/api/cycles/<int:cycle_id>', methods=['GET', 'PUT', 'DELETE'])
def cycle_detail(cycle_id):
    """Get, update, or delete a specific cycle"""
    cycle = db_session.query(Cycle).filter(Cycle.id == cycle_id).first()
    
    if not cycle:
        return jsonify({'error': 'Cycle not found'}), 404
    
    if request.method == 'GET':
        return jsonify({
            'id': cycle.id,
            'code': cycle.code,
            'name': cycle.name,
            'start_date': cycle.start_date.isoformat() if cycle.start_date else None,
            'end_date': cycle.end_date.isoformat() if cycle.end_date else None,
            'status': cycle.status
        })
    
    elif request.method == 'PUT':
        data = request.json
        if 'name' in data:
            cycle.name = data['name']
        if 'status' in data:
            cycle.status = data['status']
        if 'start_date' in data:
            cycle.start_date = datetime.fromisoformat(data['start_date'])
        if 'end_date' in data:
            cycle.end_date = datetime.fromisoformat(data['end_date'])
        db_session.commit()
        return jsonify({'message': 'Cycle updated'})
    
    elif request.method == 'DELETE':
        db_session.delete(cycle)
        db_session.commit()
        return jsonify({'message': 'Cycle deleted'})


# People endpoints
@app.route('/api/people', methods=['GET', 'POST'])
def people():
    """Get all people or create a new person"""
    if request.method == 'GET':
        people = db_session.query(Person).filter(Person.active == True).all()
        return jsonify([{
            'email': p.email,
            'full_name': p.full_name,
            'role_title': p.role_title,
            'department': p.department,
            'hire_date': p.hire_date.isoformat() if p.hire_date else None
        } for p in people])
    
    elif request.method == 'POST':
        data = request.json
        person = Person(
            email=data['email'],
            full_name=data['full_name'],
            role_title=data.get('role_title'),
            department=data.get('department'),
            hire_date=datetime.fromisoformat(data['hire_date']) if data.get('hire_date') else None
        )
        db_session.add(person)
        db_session.commit()
        return jsonify({'message': 'Person created'}), 201


# Assignments endpoints
@app.route('/api/assignments', methods=['GET', 'POST'])
def assignments():
    """Get all assignments or create new assignments"""
    if request.method == 'GET':
        cycle_id = request.args.get('cycle_id', type=int)
        query = db_session.query(Assignment)
        if cycle_id:
            query = query.filter(Assignment.cycle_id == cycle_id)
        
        assignments = query.all()
        return jsonify([{
            'id': a.id,
            'cycle_id': a.cycle_id,
            'rater_email': a.rater_email,
            'target_email': a.target_email,
            'target_group': a.target_group,
            'rater_context': a.rater_context,
            'weight': a.weight
        } for a in assignments])
    
    elif request.method == 'POST':
        data = request.json
        if isinstance(data, list):
            # Bulk create
            assignments = []
            for item in data:
                assignment = Assignment(
                    cycle_id=item['cycle_id'],
                    rater_email=item['rater_email'],
                    target_email=item['target_email'],
                    target_group=item.get('target_group'),
                    rater_context=item.get('rater_context'),
                    weight=item.get('weight', 1.0)
                )
                assignments.append(assignment)
                db_session.add(assignment)
            db_session.commit()
            return jsonify({'message': f'{len(assignments)} assignments created'}), 201
        else:
            # Single create
            assignment = Assignment(
                cycle_id=data['cycle_id'],
                rater_email=data['rater_email'],
                target_email=data['target_email'],
                target_group=data.get('target_group'),
                rater_context=data.get('rater_context'),
                weight=data.get('weight', 1.0)
            )
            db_session.add(assignment)
            db_session.commit()
            return jsonify({'id': assignment.id, 'message': 'Assignment created'}), 201


# Weight matrix endpoints
@app.route('/api/cycles/<int:cycle_id>/weight_matrix', methods=['GET'])
def weight_matrix(cycle_id):
    """Get weight matrix and fairness metrics for a cycle"""
    try:
        wm = WeightMatrix(cycle_id, db_session)
        matrix = wm.build_matrix()
        metrics = wm.calculate_fairness_metrics()
        
        return jsonify({
            'cycle_id': cycle_id,
            'matrix': matrix.tolist(),
            'rater_indices': wm.rater_indices,
            'target_indices': wm.target_indices,
            'metrics': metrics
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cycles/<int:cycle_id>/weight_matrix/optimize', methods=['POST'])
def optimize_weight_matrix(cycle_id):
    """Optimize weight matrix for better balance"""
    try:
        data = request.json or {}
        target_load = data.get('target_load')
        
        wm = WeightMatrix(cycle_id, db_session)
        optimized = wm.optimize_weights(target_load)
        imbalanced = wm.get_imbalanced_assignments()
        
        return jsonify({
            'cycle_id': cycle_id,
            'optimized_matrix': optimized.tolist(),
            'imbalanced_assignments': imbalanced
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Bias detection endpoints
@app.route('/api/cycles/<int:cycle_id>/bias', methods=['GET'])
def bias_detection(cycle_id):
    """Get comprehensive bias analysis for a cycle"""
    try:
        detector = BiasDetector(db_session)
        report = detector.comprehensive_bias_report(cycle_id)
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cycles/<int:cycle_id>/bias/<bias_type>', methods=['GET'])
def specific_bias(cycle_id, bias_type):
    """Get specific bias type analysis"""
    try:
        detector = BiasDetector(db_session)
        
        bias_methods = {
            'role': detector.detect_role_bias,
            'recency': detector.detect_recency_bias,
            'centrality': detector.detect_centrality_bias,
            'harshness': detector.detect_harshness_bias,
            'similarity': detector.detect_similarity_bias,
            'gender': detector.detect_gender_bias
        }
        
        if bias_type not in bias_methods:
            return jsonify({'error': f'Unknown bias type: {bias_type}'}), 400
        
        result = bias_methods[bias_type](cycle_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cycles/<int:cycle_id>/weighted_score/<target_email>', methods=['GET'])
def weighted_score(cycle_id, target_email):
    """Calculate weighted score for a specific target"""
    try:
        detector = BiasDetector(db_session)
        result = detector.calculate_weighted_score_by_assignment(cycle_id, target_email)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/calculate_weighted_score', methods=['POST'])
def calculate_weighted_score():
    """Calculate weighted score from provided scores and weights"""
    try:
        data = request.json
        scores = data.get('scores', {})
        weights = data.get('weights', {})
        
        detector = BiasDetector(db_session)
        weighted_score = detector.calculate_weighted_score(scores, weights)
        
        return jsonify({
            'weighted_score': weighted_score,
            'scores': scores,
            'weights': weights
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cycles/<int:cycle_id>/weighted_scores', methods=['GET'])
def get_weighted_scores(cycle_id):
    """Get final weighted evaluation scores for a cycle"""
    try:
        target_email = request.args.get('target_email')
        handler = WeightMatrixHandler(cycle_id, db_session)
        result = handler.export_scores_to_dict(target_email)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cycles/<int:cycle_id>/validate_evaluations', methods=['GET'])
def validate_evaluations(cycle_id):
    """Validate evaluation requirements for a cycle"""
    try:
        target_email = request.args.get('target_email')
        handler = WeightMatrixHandler(cycle_id, db_session)
        validation = handler.validate_evaluations(target_email)
        
        return jsonify({
            'is_valid': validation.is_valid,
            'errors': validation.errors,
            'warnings': validation.warnings
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cycles/<int:cycle_id>/weight_matrix/update', methods=['POST'])
def update_weight_matrix(cycle_id):
    """Update weight matrix for a cycle"""
    try:
        data = request.json
        target_group = data.get('target_group')
        rater_context = data.get('rater_context')
        weight = data.get('weight')
        
        if not all([target_group, rater_context, weight is not None]):
            return jsonify({'error': 'Missing required fields: target_group, rater_context, weight'}), 400
        
        handler = WeightMatrixHandler(cycle_id, db_session)
        handler.update_weight_matrix(target_group, rater_context, weight)
        
        return jsonify({
            'message': 'Weight matrix updated',
            'weight_matrix': handler.get_weight_matrix()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# EOM Nomination Validation endpoints
@app.route('/api/eom/validate', methods=['POST'])
def validate_eom_nomination():
    """Validate a single EOM nomination"""
    try:
        data = request.json
        nominee_email = data.get('nominee_email')
        eom_cycle_id = data.get('eom_cycle_id')
        nominated_by = data.get('nominated_by')
        category = data.get('category')
        check_attendance = data.get('check_attendance', True)
        
        if not all([nominee_email, eom_cycle_id, nominated_by]):
            return jsonify({
                'error': 'Missing required fields: nominee_email, eom_cycle_id, nominated_by'
            }), 400
        
        validator = EOMNominationValidator(db_session)
        result = validator.validate_nomination(
            nominee_email=nominee_email,
            eom_cycle_id=eom_cycle_id,
            nominated_by=nominated_by,
            category=category,
            check_attendance=check_attendance
        )
        
        return jsonify({
            'is_valid': result.is_valid,
            'errors': result.errors,
            'warnings': result.warnings,
            'details': result.details
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/eom/validate/batch', methods=['POST'])
def validate_eom_nominations_batch():
    """Validate multiple EOM nominations"""
    try:
        data = request.json
        nominations = data.get('nominations', [])
        eom_cycle_id = data.get('eom_cycle_id')
        
        if not nominations or not eom_cycle_id:
            return jsonify({
                'error': 'Missing required fields: nominations, eom_cycle_id'
            }), 400
        
        validator = EOMNominationValidator(db_session)
        results = validator.validate_batch_nominations(nominations, eom_cycle_id)
        
        # Convert results to JSON-serializable format
        serialized_results = {}
        for email, result in results.items():
            serialized_results[email] = {
                'is_valid': result.is_valid,
                'errors': result.errors,
                'warnings': result.warnings,
                'details': result.details
            }
        
        return jsonify({
            'results': serialized_results,
            'summary': {
                'total': len(results),
                'valid': sum(1 for r in results.values() if r.is_valid),
                'invalid': sum(1 for r in results.values() if not r.is_valid)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/eom/<int:eom_cycle_id>/validation_summary', methods=['GET'])
def get_eom_validation_summary(eom_cycle_id):
    """Get validation summary for an EOM cycle"""
    try:
        validator = EOMNominationValidator(db_session)
        summary = validator.get_validation_summary(eom_cycle_id)
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Complete 360-Degree Bias Detection endpoints
@app.route('/api/cycles/<int:cycle_id>/360_bias_report', methods=['GET'])
def get_360_bias_report(cycle_id):
    """Get complete 360-degree bias detection report"""
    try:
        detector = Complete360BiasDetection(db_session)
        report = detector.generate_complete_report(cycle_id)
        export_data = detector.export_report_to_dict(report)
        return jsonify(export_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cycles/<int:cycle_id>/360_bias/target/<target_email>', methods=['GET'])
def get_target_bias_summary(cycle_id, target_email):
    """Get bias summary for a specific target"""
    try:
        detector = Complete360BiasDetection(db_session)
        summary = detector.get_bias_summary_by_target(cycle_id, target_email)
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Evaluations endpoints
@app.route('/api/evaluations', methods=['GET', 'POST'])
def evaluations():
    """Get all evaluations or create a new evaluation"""
    if request.method == 'GET':
        assignment_id = request.args.get('assignment_id', type=int)
        cycle_id = request.args.get('cycle_id', type=int)
        
        query = db_session.query(Evaluation)
        if assignment_id:
            query = query.filter(Evaluation.assignment_id == assignment_id)
        elif cycle_id:
            query = query.join(Assignment).filter(Assignment.cycle_id == cycle_id)
        
        evaluations = query.all()
        return jsonify([{
            'id': e.id,
            'assignment_id': e.assignment_id,
            'submitted_at': e.submitted_at.isoformat() if e.submitted_at else None,
            'rating': e.rating,
            'comments': e.comments,
            'status': e.status
        } for e in evaluations])
    
    elif request.method == 'POST':
        data = request.json
        evaluation = Evaluation(
            assignment_id=data['assignment_id'],
            rating=data.get('rating'),
            comments=data.get('comments'),
            status=data.get('status', 'draft')
        )
        db_session.add(evaluation)
        db_session.commit()
        return jsonify({'id': evaluation.id, 'message': 'Evaluation created'}), 201


if __name__ == '__main__':
    # Create tables if they don't exist
    db.create_tables()
    
    # Run the app
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

