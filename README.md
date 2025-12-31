# Eternity School Evaluation System

A comprehensive fair evaluation system for schools, featuring bias detection, weight matrix optimization, and AI-powered nomination suggestions.

## Features

- **Multi-Rater Evaluation (MRE)**: Assign and manage evaluation relationships
- **Employee of the Month (EOM)**: Nomination and voting system
- **Bias Detection**: Multiple algorithms to detect various types of bias
- **Weight Matrix Optimization**: Balance evaluation loads across raters and targets
- **AI-Powered Suggestions**: Intelligent nomination recommendations
- **Fairness Metrics**: Comprehensive metrics for evaluation balance

## Project Structure

```
eternity-school-evaluation/
├── backend/
│   ├── app.py                 # Flask API server
│   ├── database.py            # SQLAlchemy models and database connection
│   ├── bias_detection.py     # Bias detection algorithms
│   └── weight_matrix.py       # Weight matrix calculations
├── frontend/
│   ├── components/           # React components
│   │   ├── Dashboard.jsx
│   │   └── ui/               # UI components (Card, Button, etc.)
│   └── forms/                # Form components
│       ├── EvaluationForm.jsx
│       └── AssignmentForm.jsx
├── ai_models/
│   ├── nomination_suggestions.py  # AI nomination suggestions
│   └── bias_algorithms.py         # Advanced ML bias detection
└── tests/                     # Test suite
```

## Setup

### Backend

1. **Set up the project** (creates virtual environment, installs dependencies, and creates database tables):
   ```bash
   ./setup_db.sh
   ```
   
   This script will:
   - Create a Python virtual environment (`venv/`)
   - Install all required dependencies
   - Create database tables in your Supabase database
   
   **Note:** The `.env` file is already configured with your Supabase connection string.

2. **Run the Flask server**:
   ```bash
   ./run.sh
   ```
   
   Or manually:
   ```bash
   source venv/bin/activate
   cd backend
   python app.py
   ```

   The API will be available at `http://localhost:5000`

### Manual Setup (Alternative)

If you prefer to set up manually:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set database URL (or use .env file)
export DATABASE_URL="postgresql://postgres:oRyY5M5S5op6ARqi@db.ywcfqlyhesnikclesgpr.supabase.co:5432/postgres"

# Create database tables
python3 -c "from backend.database import Database; db = Database(); db.create_tables(); print('Tables created!')"

# Run the server
cd backend
python app.py
```

**Note:** The database connection uses environment variables loaded from `.env` file via `python-dotenv`.

### Frontend

1. Install dependencies (if using npm):
```bash
cd frontend
npm install
```

2. Start the development server (configure based on your frontend framework)

## API Endpoints

### Cycles
- `GET /api/cycles` - List all cycles
- `POST /api/cycles` - Create a new cycle
- `GET /api/cycles/<id>` - Get cycle details
- `PUT /api/cycles/<id>` - Update cycle
- `DELETE /api/cycles/<id>` - Delete cycle

### People
- `GET /api/people` - List all people
- `POST /api/people` - Create a new person

### Assignments
- `GET /api/assignments?cycle_id=<id>` - List assignments
- `POST /api/assignments` - Create assignment(s)

### Weight Matrix
- `GET /api/cycles/<id>/weight_matrix` - Get weight matrix and metrics
- `POST /api/cycles/<id>/weight_matrix/optimize` - Optimize weights
- `GET /api/cycles/<id>/weighted_scores?target_email=<email>` - Get final weighted evaluation scores
- `GET /api/cycles/<id>/validate_evaluations?target_email=<email>` - Validate evaluation requirements
- `POST /api/cycles/<id>/weight_matrix/update` - Update weight matrix

### Bias Detection
- `GET /api/cycles/<id>/bias` - Comprehensive bias report
- `GET /api/cycles/<id>/bias/<type>` - Specific bias type (role, recency, centrality, harshness, similarity, gender)
- `GET /api/cycles/<id>/360_bias_report` - Complete 360-degree bias detection report
- `GET /api/cycles/<id>/360_bias/target/<email>` - Bias summary for specific target
- `GET /api/cycles/<id>/weighted_score/<target_email>` - Calculate weighted score for a target
- `POST /api/calculate_weighted_score` - Calculate weighted score from provided scores and weights

### Evaluations
- `GET /api/evaluations?cycle_id=<id>` - List evaluations
- `POST /api/evaluations` - Create evaluation

### EOM Nomination Validation
- `POST /api/eom/validate` - Validate a single EOM nomination
- `POST /api/eom/validate/batch` - Validate multiple EOM nominations
- `GET /api/eom/<id>/validation_summary` - Get validation summary for an EOM cycle

## Complete 360-Degree Bias Detection System

The `Complete360BiasDetection` class provides comprehensive bias detection for 360-degree evaluations:

**Features:**
- **Structural Checks**: Validates 360-degree completeness (all perspectives represented)
- **Role-Based Bias**: Detects differences between manager, peer, direct report, and self ratings
- **Temporal Bias**: Identifies recency and primacy effects
- **Distribution Bias**: Detects centrality, harshness, and leniency patterns
- **Similarity Bias**: Identifies halo effect and inter-rater agreement issues
- **ML-Based Detection**: Uses advanced algorithms for outlier and pattern detection
- **Inter-Rater Reliability**: Measures agreement between raters
- **Context Balance**: Analyzes distribution across evaluation contexts

**API Endpoints:**
- `GET /api/cycles/<id>/360_bias_report` - Complete 360-degree bias report
- `GET /api/cycles/<id>/360_bias/target/<email>` - Bias summary for specific target

**Usage Example:**
```python
from backend.360_bias_detection import Complete360BiasDetection

detector = Complete360BiasDetection(db_session)
report = detector.generate_complete_report(cycle_id=1)

print(f"Overall Bias Score: {report.overall_bias_score}")
print(f"Findings: {len(report.findings)}")
for finding in report.findings:
    print(f"- {finding.bias_type}: {finding.description}")
    print(f"  Recommendations: {finding.recommendations}")
```

## Bias Detection Types

1. **Role Bias**: Differences in ratings based on role relationships
2. **Recency Bias**: Correlation between submission timing and ratings (enhanced with early/late comparison)
3. **Centrality Bias**: Tendency to avoid extreme ratings
4. **Harshness/Leniency Bias**: Individual rater tendencies
5. **Similarity Bias (Halo Effect)**: Detects if raters give consistently similar scores across all domains
6. **Gender Bias**: Gender-based rating differences (requires gender data)
7. **Reciprocal Bias**: Mutual high ratings between pairs (in advanced algorithms)
8. **Systematic Patterns**: Organization-wide bias patterns (in advanced algorithms)
9. **Structural Incompleteness**: Missing required 360-degree perspectives
10. **Inter-Rater Reliability**: Agreement between multiple raters
11. **Context Imbalance**: Uneven distribution across evaluation contexts

## Weight Matrix

The weight matrix system ensures:
- Balanced evaluation loads across raters
- Fair distribution of evaluations per target
- Optimal coverage of evaluation relationships
- Identification of imbalanced assignments

### Weight Matrix Handler

The `WeightMatrixHandler` class provides comprehensive weight matrix functionality:

**Features:**
- Applies weights based on target group (academic/admin/peers/etc.) and rater context (CEO/P&C/QA/etc.)
- Calculates final weighted evaluation scores
- Validates minimum/maximum evaluation requirements
- Supports custom weight matrices

**Usage Example:**
```python
from backend.weight_matrix_handler import WeightMatrixHandler

# Initialize handler
handler = WeightMatrixHandler(cycle_id=1, db_session=db_session)

# Calculate final weighted scores
final_scores = handler.calculate_final_scores()

# Validate evaluations
validation = handler.validate_evaluations()
if not validation.is_valid:
    print("Validation errors:", validation.errors)

# Get weight for specific combination
weight = handler.get_weight('academic', 'CEO')  # Returns 1.0

# Update weight matrix
handler.update_weight_matrix('academic', 'P&C', 0.9)
```

**Default Weight Matrix:**
- Academic targets: CEO (1.0), P&C (0.8), QA (0.9)
- Admin targets: CEO (1.0), P&C (0.9), QA (0.7)
- Weights can be customized per target group and rater context

## EOM Nomination Validation

The `EOMNominationValidator` class provides comprehensive validation for Employee of the Month nominations:

**Validation Rules:**
1. **Rotation Rules**: Ensures one win per term (prevents same person winning multiple times in same term)
2. **Attendance Validation**: Checks attendance records (requires minimum 90% attendance rate)
3. **Duplicate Prevention**: Prevents duplicate nominations per category in the same cycle
4. **Leader Limits**: Leaders can only nominate once per category per cycle
5. **Additional Checks**: Validates person exists, is active, prevents self-nomination warnings

**Usage Example:**
```python
from backend.eom_validation import EOMNominationValidator

# Initialize validator
validator = EOMNominationValidator(db_session)

# Validate a nomination
result = validator.validate_nomination(
    nominee_email='teacher@eternity.edu',
    eom_cycle_id=1,
    nominated_by='principal@eternity.edu',
    category='academic',
    check_attendance=True
)

if result.is_valid:
    print("Nomination is valid!")
else:
    print("Errors:", result.errors)
    print("Warnings:", result.warnings)
```

**Database Models Added:**
- `EOMWinner`: Tracks EOM winners by term and category
- `Attendance`: Attendance records for validation
- `EOMNominee.category`: Category field for nominations

## Testing

Run tests with pytest:
```bash
pytest tests/
```

## License

[Your License Here]

