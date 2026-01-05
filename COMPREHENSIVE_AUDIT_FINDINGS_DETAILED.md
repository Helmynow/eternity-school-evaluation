# Detailed Audit Findings & Code Fixes
## Eternity School Evaluation System

---

## CRITICAL FIX #1: Add Soft Delete Support

### Files to Modify:
- [backend/database.py](backend/database.py)
- [supabase/migrations/20240101000000_initial_schema.sql](supabase/migrations/20240101000000_initial_schema.sql)

### Migration SQL:
```sql
-- Add soft delete columns to all tables
ALTER TABLE cycles ADD COLUMN deleted_at TIMESTAMP NULL;
ALTER TABLE cycles ADD COLUMN deleted_by VARCHAR(255) REFERENCES people(email) ON DELETE SET NULL;

ALTER TABLE people ADD COLUMN deleted_at TIMESTAMP NULL;
ALTER TABLE people ADD COLUMN deleted_by VARCHAR(255) REFERENCES people(email) ON DELETE SET NULL;

ALTER TABLE assignments ADD COLUMN deleted_at TIMESTAMP NULL;
ALTER TABLE assignments ADD COLUMN deleted_by VARCHAR(255) REFERENCES people(email) ON DELETE SET NULL;

ALTER TABLE evaluations ADD COLUMN deleted_at TIMESTAMP NULL;
ALTER TABLE evaluations ADD COLUMN deleted_by VARCHAR(255) REFERENCES people(email) ON DELETE SET NULL;

ALTER TABLE eom_nominees ADD COLUMN deleted_at TIMESTAMP NULL;
ALTER TABLE eom_nominees ADD COLUMN deleted_by VARCHAR(255) REFERENCES people(email) ON DELETE SET NULL;

-- Add index for queries
CREATE INDEX IF NOT EXISTS idx_cycles_deleted AT ON cycles(deleted_at);
CREATE INDEX IF NOT EXISTS idx_people_deleted ON people(deleted_at);
CREATE INDEX IF NOT EXISTS idx_assignments_deleted ON assignments(deleted_at);
CREATE INDEX IF NOT EXISTS idx_evaluations_deleted ON evaluations(deleted_at);
CREATE INDEX IF NOT EXISTS idx_eom_nominees_deleted ON eom_nominees(deleted_at);
```

### Python Model Updates:
```python
# In each Base model class, add:
from datetime import datetime

class Cycle(Base):
    # ... existing columns ...
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String(255), ForeignKey("people.email"), nullable=True)
    
    def soft_delete(self, deleted_by_email: str):
        """Soft delete the record"""
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by_email
    
    def restore(self):
        """Restore soft-deleted record"""
        self.deleted_at = None
        self.deleted_by = None

# Add soft-delete filter to all queries:
@classmethod
def active(cls):
    """Return all active (non-deleted) records"""
    return db.query(cls).filter(cls.deleted_at.is_(None))
```

---

## CRITICAL FIX #2: Fix Cascade Delete Risk

### Current Issue:
```python
# BAD - allows accidental data loss
cycle_id = Column(Integer, ForeignKey("cycles.id"), nullable=False)
```

### Fix in database.py:
```python
# GOOD - prevents deletion of referenced cycles
cycle_id = Column(
    Integer, 
    ForeignKey("cycles.id", ondelete="RESTRICT"),  # Prevent cascade
    nullable=False
)

# GOOD - allow deletion, but set to NULL (for non-critical data)
weight_matrix_id = Column(
    Integer, 
    ForeignKey("weight_matrices.id", ondelete="SET NULL"),
    nullable=True
)
```

### Apply to these columns in [backend/database.py](backend/database.py):

**Assignment model (lines 310-320):**
```python
class Assignment(Base):
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True)
    cycle_id = Column(
        Integer, 
        ForeignKey("cycles.id", ondelete="RESTRICT"),
        nullable=False
    )
    rater_email = Column(
        String(255), 
        ForeignKey("people.email", ondelete="CASCADE"),
        nullable=False
    )
    target_email = Column(
        String(255), 
        ForeignKey("people.email", ondelete="CASCADE"),
        nullable=False
    )
    weight_matrix_id = Column(
        Integer, 
        ForeignKey("weight_matrices.id", ondelete="SET NULL"),
        nullable=True
    )
```

**EOMCycle model (lines 360-375):**
```python
class EOMCycle(Base):
    __tablename__ = "eom_cycles"
    
    id = Column(Integer, primary_key=True)
    cycle_id = Column(
        Integer, 
        ForeignKey("cycles.id", ondelete="RESTRICT"),  # Prevent cycle deletion
        nullable=False
    )
```

**EOMNominee model (lines 390-410):**
```python
class EOMNominee(Base):
    __tablename__ = "eom_nominees"
    
    id = Column(Integer, primary_key=True)
    eom_cycle_id = Column(
        Integer, 
        ForeignKey("eom_cycles.id", ondelete="CASCADE"),  # Allow cycle deletion
        nullable=False
    )
```

---

## CRITICAL FIX #3: Add Transaction Isolation for Nominations

### File: [backend/fastapi_app.py](backend/fastapi_app.py#L597-L710)

**Current Code (BUGGY):**
```python
@app.post("/api/v2/eom/nominations/submit", response_model=EOMNominationResponse)
async def submit_eom_nomination(nomination: EOMNominationRequest, ...):
    # Validate (check passes)
    validation_result = validator.validate_nomination(...)
    if not validation_result.is_valid:
        return error_response
    
    # RACE CONDITION WINDOW: Another request can submit same nomination here
    
    eom_nominee = EOMNominee(...)  # Duplicate possible
    db.add(eom_nominee)
    db.commit()
```

**Fixed Code:**
```python
@app.post("/api/v2/eom/nominations/submit", response_model=EOMNominationResponse)
async def submit_eom_nomination(nomination: EOMNominationRequest, ...):
    try:
        # Use database transaction to prevent race conditions
        db.begin()  # Start transaction
        
        # Re-validate within transaction (gets latest data)
        existing = db.query(EOMNominee).filter(
            EOMNominee.eom_cycle_id == resolved_eom_cycle_id,
            EOMNominee.nominee_email == nomination.nominee_email,
            EOMNominee.nominated_by == nominator_email,
            EOMNominee.deleted_at.is_(None),  # Ignore soft-deleted
        ).with_for_update().first()  # Lock row
        
        if existing:
            db.rollback()
            return EOMNominationResponse(
                nomination_id=0,
                is_valid=False,
                errors=["This nomination has already been submitted"],
                warnings=[],
                details={}
            )
        
        # Validate full nomination
        validation_result = validator.validate_nomination(...)
        if not validation_result.is_valid:
            db.rollback()
            return error_response
        
        # Create nomination
        eom_nominee = EOMNominee(
            eom_cycle_id=resolved_eom_cycle_id,
            nominee_email=nomination.nominee_email,
            nominated_by=nominator_email,
            nomination_reason=nomination.nomination_reason,
            category=nomination.category,
            rotation_eligible=True,
            votes_received=0,
        )
        
        db.add(eom_nominee)
        db.commit()  # Atomically commit or rollback
        db.refresh(eom_nominee)
        
        return success_response
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error submitting nomination: {str(e)}")
```

---

## CRITICAL FIX #4: Enforce Category Validation

### File: [backend/fastapi_app.py](backend/fastapi_app.py#L620-L660)

**Current Code (BUGGY):**
```python
# Auto-suggest category if not provided
if not nomination.category and nomination.nomination_reason:
    suggestion = recommender.suggest_category(nomination.nomination_reason, nominee_role)
    if suggestion.get("recommended_category"):
        # Map and assign
        nomination.category = category_map[suggestion["recommended_category"]]
    # If mapping fails or no suggestion, category stays None → DB constraint violation
```

**Fixed Code:**
```python
# Ensure category is always set
if not nomination.category:
    if nomination.nomination_reason:
        # Try to auto-suggest
        suggestion = recommender.suggest_category(nomination.nomination_reason, nominee_role)
        if suggestion.get("recommended_category") and suggestion.get("confidence_score", 0) > 0.5:
            try:
                suggested_cat = suggestion["recommended_category"]
                # Normalize category string
                category_upper = suggested_cat.upper().replace(" ", "_")
                category_map = {
                    "OUTSTANDING_LEADERSHIP": EOMCategory.OUTSTANDING_LEADERSHIP,
                    "TEAM_SPIRIT": EOMCategory.TEAM_SPIRIT,
                    "INNOVATION": EOMCategory.INNOVATION,
                    "RISING_STAR": EOMCategory.RISING_STAR,
                    "SERVICE_EXCELLENCE": EOMCategory.SERVICE_EXCELLENCE,
                }
                nomination.category = category_map.get(category_upper)
            except (KeyError, AttributeError, TypeError):
                nomination.category = None
    
    # If still None, reject submission
    if not nomination.category:
        raise HTTPException(
            status_code=422,
            detail="Category is required. Please specify a category or nomination reason for auto-suggestion."
        )
```

---

## CRITICAL FIX #5: Add Duplicate Vote Prevention

### File: [supabase/migrations/](supabase/migrations/)

**SQL Migration:**
```sql
-- Prevent duplicate votes in same EOM cycle
ALTER TABLE eom_voters 
ADD CONSTRAINT unique_voter_per_cycle UNIQUE (eom_cycle_id, voter_email);

-- Better: Track individual votes per nominee
-- Add this column to eom_voters:
ALTER TABLE eom_voters ADD COLUMN nominee_email VARCHAR(255) REFERENCES people(email) ON DELETE CASCADE;

-- Then add unique constraint on (cycle, voter, nominee):
ALTER TABLE eom_voters 
DROP CONSTRAINT unique_voter_per_cycle;

ALTER TABLE eom_voters 
ADD CONSTRAINT unique_vote_per_nominee UNIQUE (eom_cycle_id, voter_email, nominee_email);
```

**Python Code in [backend/fastapi_app.py](backend/fastapi_app.py#L814-L860):**

```python
@app.post("/api/v2/eom/vote")
async def vote_eom(
    vote: EOMVoteRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        voter_email = _require_eom_access(request, db)
        
        # Check if this person can vote
        eom_cycle = db.query(EOMCycle).filter(EOMCycle.id == vote.eom_cycle_id).first()
        if not eom_cycle:
            raise HTTPException(status_code=404, detail="EOM cycle not found")
        
        # Verify nominee exists and is in this cycle
        nominee = db.query(EOMNominee).filter(
            EOMNominee.eom_cycle_id == vote.eom_cycle_id,
            EOMNominee.nominee_email == vote.nominee_email,
            EOMNominee.deleted_at.is_(None),
        ).first()
        
        if not nominee:
            raise HTTPException(status_code=404, detail="Nominee not found in this cycle")
        
        # Check for duplicate vote (prevents duplicates)
        existing_vote = db.query(EOMVoter).filter(
            EOMVoter.eom_cycle_id == vote.eom_cycle_id,
            EOMVoter.voter_email == voter_email,
            EOMVoter.nominee_email == vote.nominee_email,
        ).first()
        
        if existing_vote:
            raise HTTPException(
                status_code=409,
                detail="You have already voted for this nominee in this cycle"
            )
        
        # Record vote
        eom_voter = EOMVoter(
            eom_cycle_id=vote.eom_cycle_id,
            voter_email=voter_email,
            nominee_email=vote.nominee_email,
        )
        
        db.add(eom_voter)
        
        # Increment vote count
        nominee.votes_received += 1
        
        db.commit()
        
        return {
            "message": "Vote recorded successfully",
            "eom_cycle_id": vote.eom_cycle_id,
            "nominee_email": vote.nominee_email,
            "votes_received": nominee.votes_received,
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error recording vote: {str(e)}")
```

---

## HIGH PRIORITY FIX #6: Add Pagination

### File: [backend/fastapi_app.py](backend/fastapi_app.py#L780-L820)

**Current Code (BUGGY):**
```python
@app.get("/api/v2/eom/nominations/cycle/{cycle_id}")
async def list_eom_nominations_for_cycle(cycle_id: int, ...):
    nominations = (
        db.query(EOMNominee)
        .filter(EOMNominee.eom_cycle_id == cycle_id)
        .all()  # Loads ALL rows
    )
```

**Fixed Code:**
```python
from typing import Optional

class PaginationParams(BaseModel):
    skip: int = 0
    limit: int = 50
    
    @field_validator('limit')
    @classmethod
    def limit_must_be_reasonable(cls, v):
        if v > 1000:
            raise ValueError('limit must be <= 1000')
        if v < 1:
            raise ValueError('limit must be >= 1')
        return v

@app.get("/api/v2/eom/nominations/cycle/{cycle_id}")
async def list_eom_nominations_for_cycle(
    cycle_id: int,
    skip: int = 0,
    limit: int = 50,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """
    List EOM nominations with pagination.
    
    Query params:
    - skip: Number of records to skip (default: 0)
    - limit: Max records to return (default: 50, max: 1000)
    """
    try:
        # Validate pagination params
        if skip < 0 or limit < 1 or limit > 1000:
            raise HTTPException(status_code=422, detail="Invalid pagination parameters")
        
        # Get total count
        total = db.query(EOMNominee).filter(
            EOMNominee.eom_cycle_id == cycle_id,
            EOMNominee.deleted_at.is_(None),
        ).count()
        
        # Get paginated results
        nominations = (
            db.query(EOMNominee)
            .filter(
                EOMNominee.eom_cycle_id == cycle_id,
                EOMNominee.deleted_at.is_(None),
            )
            .order_by(EOMNominee.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return {
            "items": [
                {
                    "id": n.id,
                    "nominee_email": n.nominee_email,
                    "nominee_name": n.nominee_person.full_name if n.nominee_person else None,
                    "category": n.category.value if n.category else None,
                    "votes_received": n.votes_received,
                    "created_at": n.created_at.isoformat(),
                }
                for n in nominations
            ],
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total,
                "has_more": (skip + limit) < total,
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching nominations: {str(e)}")
```

---

## HIGH PRIORITY FIX #7: Consistent API Error Responses

### File: [backend/fastapi_app.py](backend/fastapi_app.py)

**Create a response envelope:**
```python
from enum import Enum
from typing import Any, List, Optional

class ErrorSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class APIError(BaseModel):
    code: str  # e.g., "validation_error", "not_found"
    message: str
    severity: ErrorSeverity = ErrorSeverity.ERROR
    details: Optional[dict] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class APIResponse(BaseModel):
    """Standard API response envelope"""
    success: bool
    data: Optional[Any] = None
    error: Optional[APIError] = None
    meta: Optional[dict] = None  # pagination, timing, etc.

# Use consistently across all endpoints
@app.post("/api/v2/eom/nominations/submit")
async def submit_eom_nomination(...):
    try:
        # ... code ...
        return APIResponse(
            success=True,
            data={
                "nomination_id": eom_nominee.id,
                "nominee_email": eom_nominee.nominee_email,
                "category": eom_nominee.category.value,
            }
        )
    except ValueError as e:
        return APIResponse(
            success=False,
            error=APIError(
                code="validation_error",
                message=str(e),
                severity=ErrorSeverity.ERROR,
            )
        ), 422
    except Exception as e:
        return APIResponse(
            success=False,
            error=APIError(
                code="internal_error",
                message="An unexpected error occurred",
                severity=ErrorSeverity.ERROR,
            )
        ), 500
```

---

## HIGH PRIORITY FIX #8: Add Request Timeout on Frontend

### File: [frontend/src/lib/api.js](frontend/src/lib/api.js#L98-L165)

**Current Code (BUGGY):**
```javascript
const api = axios.create({
  baseURL: apiBaseURL,
  // Missing timeout
})
```

**Fixed Code:**
```javascript
const api = axios.create({
  baseURL: apiBaseURL,
  timeout: 30000,  // 30 second timeout
  headers: {
    'Content-Type': 'application/json',
    'X-Request-ID': () => generateRequestId(),  // Unique ID per request
  },
})

// Helper to generate unique request ID
function generateRequestId() {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

// Enhanced request interceptor with timeout tracking
api.interceptors.request.use(
  (config) => {
    config.metadata = {
      startTime: performance.now(),
    }
    
    // Log request in development
    if (import.meta.env.DEV) {
      console.debug(`[API] ${config.method.toUpperCase()} ${config.url}`)
    }
    
    return config
  },
  (error) => Promise.reject(error)
)

// Enhanced error handler for timeouts
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      // Timeout occurred
      console.error('Request timeout:', error.config.url)
      toast.error('Request timeout. The server is taking too long to respond. Please try again.')
      return Promise.reject({
        ...error,
        isTimeout: true,
        message: 'Request timeout after 30 seconds',
      })
    }
    return Promise.reject(error)
  }
)
```

---

## HIGH PRIORITY FIX #9: Add Logging to Critical Operations

### File: [backend/fastapi_app.py](backend/fastapi_app.py)

```python
import logging

logger = logging.getLogger(__name__)

# In each critical endpoint:

@app.post("/api/v2/eom/vote")
async def vote_eom(vote: EOMVoteRequest, request: Request, db: Session = Depends(get_db)):
    voter_email = _require_eom_access(request, db)
    logger.info(f"User {voter_email} voting for {vote.nominee_email}")
    
    try:
        # ... validation ...
        logger.debug(f"Vote validation passed for {vote.nominee_email}")
        
        # ... database operations ...
        db.commit()
        
        logger.info(f"Vote recorded: {voter_email} → {vote.nominee_email}")
        return success_response
        
    except Exception as e:
        logger.error(f"Vote error for {voter_email}: {str(e)}", exc_info=True)
        db.rollback()
        raise

@app.post("/api/v2/mre/evaluations/process")
async def submit_mre_evaluation(eval_data: MREEvaluationRequest, ...):
    rater_email = _require_authenticated_email(request)
    assignment = db.query(Assignment).filter(...).first()
    
    logger.info(f"Evaluation submission: {rater_email} → {assignment.target_email}")
    
    try:
        # Calculate weight
        weight = assignment.weight
        weighted_rating = eval_data.rating * weight
        
        logger.debug(f"Weight calculation: rating={eval_data.rating}, weight={weight}, weighted={weighted_rating}")
        
        # ... save evaluation ...
        db.commit()
        
        logger.info(f"Evaluation saved: ID={evaluation.id}, weighted_rating={weighted_rating}")
        return success_response
        
    except Exception as e:
        logger.error(f"Evaluation error: {str(e)}", exc_info=True)
        db.rollback()
        raise
```

---

## HIGH PRIORITY FIX #10: Assign Notification on Evaluation Assignment

### File: [backend/fastapi_app.py](backend/fastapi_app.py#L1189-L1255)

```python
@app.post("/api/v2/staff/{email}/assign-evaluators")
async def assign_evaluators(
    email: str,
    assignment_data: Dict,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create evaluation assignments for a staff member.
    Automatically notifies assigned evaluators.
    """
    try:
        admin_email = _require_admin_access(request, db)
        
        # Get target person
        target = db.query(Person).filter(Person.email == email).first()
        if not target:
            raise HTTPException(status_code=404, detail="Staff member not found")
        
        # Create assignments
        assignments = assignment_manager.create_assignments_for_staff(
            email,
            assignment_data.get("cycle_id"),
            assignment_data.get("evaluator_overrides")
        )
        
        # Send notifications to assigned evaluators
        notification_system = SmartNotificationSystem(db)
        for assignment in assignments:
            rater = db.query(Person).filter(Person.email == assignment.rater_email).first()
            
            background_tasks.add_task(
                notification_system.notify_evaluation_assignment,
                assignment_id=assignment.id,
                rater_email=assignment.rater_email,
                rater_name=rater.full_name if rater else assignment.rater_email,
                target_email=target.email,
                target_name=target.full_name,
                cycle_id=assignment.cycle_id,
            )
        
        logger.info(f"Created {len(assignments)} assignments for {email}, notifications sent")
        
        return {
            "message": f"Assigned {len(assignments)} evaluators",
            "assignments_created": len(assignments),
            "assignment_ids": [a.id for a in assignments],
        }
        
    except Exception as e:
        logger.error(f"Error assigning evaluators: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error assigning evaluators: {str(e)}")
```

---

## IMPLEMENTATION CHECKLIST

- [ ] CRITICAL Fix #1: Soft delete columns added
- [ ] CRITICAL Fix #2: Cascade delete constraints updated
- [ ] CRITICAL Fix #3: Transaction isolation on nominations
- [ ] CRITICAL Fix #4: Category validation enforced
- [ ] CRITICAL Fix #5: Duplicate vote prevention
- [ ] HIGH Fix #6: Pagination implemented
- [ ] HIGH Fix #7: Consistent API responses
- [ ] HIGH Fix #8: Frontend request timeout
- [ ] HIGH Fix #9: Logging added to operations
- [ ] HIGH Fix #10: Assignment notifications
- [ ] Run migrations on test environment
- [ ] Run full test suite
- [ ] Test with 50+ concurrent users
- [ ] Deploy to staging
- [ ] Smoke tests on staging
- [ ] Deploy to production
- [ ] Monitor for errors post-deployment

---

**Next Document:** See [COMPREHENSIVE_AUDIT_REPORT.md](COMPREHENSIVE_AUDIT_REPORT.md) for full findings
