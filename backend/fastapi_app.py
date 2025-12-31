"""
FastAPI application for Eternity School Evaluation System.
Provides high-performance API endpoints for evaluation processing.
"""
from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum
import io
import csv
import json
from sqlalchemy.orm import Session

from backend.database import (
    Database, Cycle, Person, Assignment, Evaluation, EOMCycle, EOMNominee, 
    EOMCategory, StaffSegment, ActionType as DBActionType
)
from backend.eom_validation import EOMNominationValidator
from backend.eom_rotation_manager import EOMRotationManager
from backend.weight_matrix_handler import WeightMatrixHandler
from backend.360_bias_detection import Complete360BiasDetection
from backend.context_aware_bias_detection import ContextAware360BiasDetection
from backend.academic_admin_scoring import AcademicAdminScoring
from backend.optimized_evaluation_calculator import OptimizedEvaluationCalculator
from backend.audit_logger import AuditLogger

# Initialize FastAPI app
app = FastAPI(
    title="Eternity School Evaluation System API",
    description="FastAPI endpoints for evaluation processing, bias detection, and reporting",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_db():
    """Dependency to get database session"""
    db = Database()
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


# ============================================================================
# Pydantic Models
# ============================================================================

class EOMNominationRequest(BaseModel):
    """Request model for EOM nomination submission"""
    nominee_email: EmailStr
    eom_cycle_id: int
    nominated_by: EmailStr
    nomination_reason: Optional[str] = None
    category: Optional[EOMCategory] = None
    check_attendance: bool = True
    
    class Config:
        use_enum_values = True


class EOMNominationResponse(BaseModel):
    """Response model for EOM nomination"""
    nomination_id: int
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    details: Dict[str, Any]


class MREEvaluationRequest(BaseModel):
    """Request model for MRE evaluation submission"""
    assignment_id: int
    rating: float = Field(..., ge=1.0, le=5.0, description="Rating from 1.0 to 5.0")
    comments: Optional[str] = None
    domain_scores: Optional[Dict[str, float]] = None
    status: str = "submitted"
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ['draft', 'submitted', 'reviewed']:
            raise ValueError('Status must be draft, submitted, or reviewed')
        return v


class MREEvaluationResponse(BaseModel):
    """Response model for MRE evaluation"""
    evaluation_id: int
    assignment_id: int
    rating: float
    weighted_rating: float
    weight_applied: float
    target_email: str
    rater_email: str
    target_group: str
    rater_context: str
    status: str


class BiasReportRequest(BaseModel):
    """Request model for bias detection report"""
    cycle_id: int
    include_target_analysis: bool = False
    target_email: Optional[EmailStr] = None


class BiasReportResponse(BaseModel):
    """Response model for bias detection report"""
    cycle_id: int
    overall_bias_score: float
    bias_level: str
    total_evaluations: int
    total_raters: int
    total_targets: int
    findings_count: int
    findings_by_type: Dict[str, int]
    findings_by_severity: Dict[str, int]
    findings: List[Dict[str, Any]]
    context_coverage: Dict[str, Any]
    statistical_summary: Dict[str, Any]
    recommendations: List[str]
    generated_at: str


class CEOReportRequest(BaseModel):
    """Request model for CEO report export"""
    cycle_id: int
    format: str = Field("csv", regex="^(csv|json|excel)$")
    include_bias_analysis: bool = True
    include_weighted_scores: bool = True
    segment_filter: Optional[StaffSegment] = None


# ============================================================================
# EOM Nomination Endpoints
# ============================================================================

@app.post("/api/v2/eom/nominations/submit", response_model=EOMNominationResponse)
async def submit_eom_nomination(
    nomination: EOMNominationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Submit an EOM nomination with comprehensive validation.
    
    Validates:
    - Rotation rules (one win per term)
    - Attendance records
    - Duplicate nominations
    - Leader nomination limits
    """
    try:
        # Initialize validator
        validator = EOMNominationValidator(db)
        audit_logger = AuditLogger(db)
        
        # Validate nomination
        validation_result = validator.validate_nomination(
            nominee_email=nomination.nominee_email,
            eom_cycle_id=nomination.eom_cycle_id,
            nominated_by=nomination.nominated_by,
            category=nomination.category.value if nomination.category else None,
            check_attendance=nomination.check_attendance
        )
        
        # If validation fails, return error response
        if not validation_result.is_valid:
            return EOMNominationResponse(
                nomination_id=0,
                is_valid=False,
                errors=validation_result.errors,
                warnings=validation_result.warnings,
                details=validation_result.details
            )
        
        # Create nomination if valid
        eom_nominee = EOMNominee(
            eom_cycle_id=nomination.eom_cycle_id,
            nominee_email=nomination.nominee_email,
            nominated_by=nomination.nominated_by,
            nomination_reason=nomination.nomination_reason,
            category=nomination.category,  # EOMCategory enum
            rotation_eligible=True,
            votes_received=0
        )
        
        db.add(eom_nominee)
        db.commit()
        db.refresh(eom_nominee)
        
        # Log audit trail
        background_tasks.add_task(
            audit_logger.log_create,
            "eom_nominee",
            eom_nominee.id,
            nomination.nominated_by,
            f"Submitted EOM nomination for {nomination.nominee_email}"
        )
        
        return EOMNominationResponse(
            nomination_id=eom_nominee.id,
            is_valid=True,
            errors=[],
            warnings=validation_result.warnings,
            details={
                **validation_result.details,
                'nomination_id': eom_nominee.id,
                'created_at': eom_nominee.created_at.isoformat() if hasattr(eom_nominee, 'created_at') else None
            }
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error submitting nomination: {str(e)}")


@app.post("/api/v2/eom/nominations/validate")
async def validate_eom_nomination(
    nomination: EOMNominationRequest,
    db: Session = Depends(get_db)
):
    """
    Validate an EOM nomination without submitting it.
    Uses comprehensive rotation rules validation.
    Useful for pre-submission validation.
    """
    try:
        validator = EOMNominationValidator(db)
        
        validation_result = validator.validate_nomination(
            nominee_email=nomination.nominee_email,
            eom_cycle_id=nomination.eom_cycle_id,
            nominated_by=nomination.nominated_by,
            category=nomination.category.value if nomination.category else None,
            check_attendance=nomination.check_attendance
        )
        
        return {
            "is_valid": validation_result.is_valid,
            "errors": validation_result.errors,
            "warnings": validation_result.warnings,
            "details": validation_result.details
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating nomination: {str(e)}")


@app.post("/api/v2/eom/nominations/batch-validate")
async def validate_batch_nominations(
    nominations: List[EOMNominationRequest],
    eom_cycle_id: int = Query(..., description="EOM cycle ID for all nominations"),
    db: Session = Depends(get_db)
):
    """Validate multiple EOM nominations at once"""
    try:
        validator = EOMNominationValidator(db)
        
        nomination_dicts = [
            {
                'nominee_email': n.nominee_email,
                'nominated_by': n.nominated_by,
                'category': n.category.value if n.category else None
            }
            for n in nominations
        ]
        
        results = validator.validate_batch_nominations(nomination_dicts, eom_cycle_id)
        
        return {
            "total_nominations": len(nominations),
            "valid_count": sum(1 for r in results.values() if r.is_valid),
            "invalid_count": sum(1 for r in results.values() if not r.is_valid),
            "results": {
                email: {
                    "is_valid": result.is_valid,
                    "errors": result.errors,
                    "warnings": result.warnings
                }
                for email, result in results.items()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating batch nominations: {str(e)}")


# ============================================================================
# EOM Rotation Rule Management Endpoints
# ============================================================================

class RotationRuleRequest(BaseModel):
    """Request model for creating/updating rotation rules"""
    category: EOMCategory
    cycle_id: int
    cooldown_period: int = 3
    max_wins_per_period: int = 1
    period_type: str = "year"  # 'year', 'quarter', 'month'
    is_active: bool = True


class RotationRuleUpdateRequest(BaseModel):
    """Request model for updating rotation rules"""
    cooldown_period: Optional[int] = None
    max_wins_per_period: Optional[int] = None
    period_type: Optional[str] = None
    is_active: Optional[bool] = None


class EligibilityCheckRequest(BaseModel):
    """Request model for checking nominee eligibility"""
    nominee_email: EmailStr
    category: EOMCategory
    eom_cycle_id: int


@app.post("/api/v2/eom/rotation-rules/create")
async def create_rotation_rule(
    rule: RotationRuleRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new rotation rule for a category.
    """
    try:
        validator = EOMNominationValidator(db)
        
        created_rule = validator.create_rotation_rule(
            category=rule.category,
            cycle_id=rule.cycle_id,
            cooldown_period=rule.cooldown_period,
            max_wins_per_period=rule.max_wins_per_period,
            period_type=rule.period_type,
            is_active=rule.is_active
        )
        
        return {
            "rule_id": created_rule.id,
            "category": created_rule.category.value,
            "cooldown_period": created_rule.cooldown_period,
            "max_wins_per_period": created_rule.max_wins_per_period,
            "period_type": created_rule.period_type,
            "is_active": created_rule.is_active,
            "message": "Rotation rule created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating rotation rule: {str(e)}")


@app.put("/api/v2/eom/rotation-rules/{rule_id}")
async def update_rotation_rule(
    rule_id: int,
    rule_update: RotationRuleUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update an existing rotation rule.
    """
    try:
        validator = EOMNominationValidator(db)
        
        updated_rule = validator.update_rotation_rule(
            rule_id=rule_id,
            cooldown_period=rule_update.cooldown_period,
            max_wins_per_period=rule_update.max_wins_per_period,
            period_type=rule_update.period_type,
            is_active=rule_update.is_active
        )
        
        return {
            "rule_id": updated_rule.id,
            "category": updated_rule.category.value,
            "cooldown_period": updated_rule.cooldown_period,
            "max_wins_per_period": updated_rule.max_wins_per_period,
            "period_type": updated_rule.period_type,
            "is_active": updated_rule.is_active,
            "message": "Rotation rule updated successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating rotation rule: {str(e)}")


@app.get("/api/v2/eom/rotation-rules/cycle/{cycle_id}")
async def get_rotation_rules_for_cycle(
    cycle_id: int,
    category: Optional[EOMCategory] = None,
    active_only: bool = Query(True, description="Only return active rules"),
    db: Session = Depends(get_db)
):
    """
    Get all rotation rules for a cycle.
    """
    try:
        validator = EOMNominationValidator(db)
        
        rules = validator.get_rotation_rules_for_cycle(
            cycle_id=cycle_id,
            category=category,
            active_only=active_only
        )
        
        return {
            "cycle_id": cycle_id,
            "total_rules": len(rules),
            "rules": [
                {
                    "id": rule.id,
                    "category": rule.category.value,
                    "cooldown_period": rule.cooldown_period,
                    "max_wins_per_period": rule.max_wins_per_period,
                    "period_type": rule.period_type,
                    "is_active": rule.is_active,
                    "created_at": rule.created_at.isoformat() if hasattr(rule, 'created_at') else None
                }
                for rule in rules
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving rotation rules: {str(e)}")


@app.post("/api/v2/eom/rotation-rules/check-eligibility")
async def check_nominee_eligibility(
    request: EligibilityCheckRequest,
    db: Session = Depends(get_db)
):
    """
    Check if a nominee is eligible for nomination based on rotation rules.
    """
    try:
        validator = EOMNominationValidator(db)
        
        eligibility = validator.check_nominee_rotation_eligibility(
            nominee_email=request.nominee_email,
            category=request.category,
            eom_cycle_id=request.eom_cycle_id
        )
        
        return eligibility
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking eligibility: {str(e)}")


@app.get("/api/v2/eom/rotation-rules/eligible-nominees/{eom_cycle_id}")
async def get_eligible_nominees(
    eom_cycle_id: int,
    category: EOMCategory = Query(..., description="Category to check"),
    db: Session = Depends(get_db)
):
    """
    Get list of all eligible nominees for a category in an EOM cycle.
    """
    try:
        manager = EOMRotationManager(db)
        
        eligible = manager.get_eligible_nominees(
            eom_cycle_id=eom_cycle_id,
            category=category
        )
        
        return {
            "eom_cycle_id": eom_cycle_id,
            "category": category.value,
            "total_eligible": len(eligible),
            "nominees": eligible
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving eligible nominees: {str(e)}")


@app.get("/api/v2/eom/rotation-rules/ineligible-nominees/{eom_cycle_id}")
async def get_ineligible_nominees(
    eom_cycle_id: int,
    category: EOMCategory = Query(..., description="Category to check"),
    db: Session = Depends(get_db)
):
    """
    Get list of ineligible nominees with reasons.
    """
    try:
        manager = EOMRotationManager(db)
        
        ineligible = manager.get_ineligible_nominees(
            eom_cycle_id=eom_cycle_id,
            category=category
        )
        
        return {
            "eom_cycle_id": eom_cycle_id,
            "category": category.value,
            "total_ineligible": len(ineligible),
            "nominees": ineligible
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving ineligible nominees: {str(e)}")


@app.post("/api/v2/eom/rotation-rules/setup-defaults/{cycle_id}")
async def setup_default_rotation_rules(
    cycle_id: int,
    categories: Optional[List[EOMCategory]] = None,
    db: Session = Depends(get_db)
):
    """
    Set up default rotation rules for a cycle.
    """
    try:
        manager = EOMRotationManager(db)
        
        rules = manager.setup_default_rules(
            cycle_id=cycle_id,
            categories=categories
        )
        
        return {
            "cycle_id": cycle_id,
            "rules_created": len(rules),
            "rules": [
                {
                    "id": rule.id,
                    "category": rule.category.value,
                    "cooldown_period": rule.cooldown_period,
                    "max_wins_per_period": rule.max_wins_per_period,
                    "period_type": rule.period_type
                }
                for rule in rules
            ],
            "message": f"Created {len(rules)} default rotation rules"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting up default rules: {str(e)}")


@app.get("/api/v2/eom/rotation-rules/analytics/{cycle_id}")
async def get_rotation_analytics(
    cycle_id: int,
    category: Optional[EOMCategory] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive rotation analytics for a cycle.
    """
    try:
        validator = EOMNominationValidator(db)
        
        analytics = validator.get_rotation_analytics(
            cycle_id=cycle_id,
            category=category,
            start_date=start_date,
            end_date=end_date
        )
        
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving analytics: {str(e)}")


@app.get("/api/v2/eom/rotation-rules/nominee-history/{nominee_email}")
async def get_nominee_rotation_history(
    nominee_email: str,
    category: Optional[EOMCategory] = None,
    db: Session = Depends(get_db)
):
    """
    Get complete rotation history for a nominee.
    """
    try:
        validator = EOMNominationValidator(db)
        
        history = validator.get_nominee_rotation_history(
            nominee_email=nominee_email,
            category=category
        )
        
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving nominee history: {str(e)}")


@app.get("/api/v2/eom/rotation-rules/summary/{cycle_id}")
async def get_rotation_summary(
    cycle_id: int,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive rotation summary for a cycle.
    """
    try:
        manager = EOMRotationManager(db)
        
        summary = manager.get_rotation_summary(cycle_id=cycle_id)
        
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving rotation summary: {str(e)}")


@app.post("/api/v2/eom/rotation-rules/update-eligibility-flags/{eom_cycle_id}")
async def update_rotation_eligibility_flags(
    eom_cycle_id: int,
    db: Session = Depends(get_db)
):
    """
    Update rotation_eligible flags for all nominees in an EOM cycle.
    """
    try:
        manager = EOMRotationManager(db)
        
        result = manager.update_rotation_eligibility_flags(eom_cycle_id=eom_cycle_id)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating eligibility flags: {str(e)}")


# ============================================================================
# MRE Evaluation Endpoints
# ============================================================================

@app.post("/api/v2/mre/evaluations/process", response_model=MREEvaluationResponse)
async def process_mre_evaluation(
    evaluation: MREEvaluationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Process an MRE evaluation with automatic weight calculation.
    
    Features:
    - Applies weight matrix based on target group and rater context
    - Calculates weighted rating
    - Stores domain-specific scores if provided
    """
    try:
        # Get assignment to determine weights
        assignment = db.query(Assignment).filter(
            Assignment.id == evaluation.assignment_id
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Get cycle for weight matrix handler
        cycle = db.query(Cycle).filter(Cycle.id == assignment.cycle_id).first()
        if not cycle:
            raise HTTPException(status_code=404, detail="Cycle not found")
        
        # Initialize weight matrix handler
        weight_handler = WeightMatrixHandler(assignment.cycle_id, db)
        
        # Get weight for this assignment
        weight = weight_handler.get_weight(
            target_group=assignment.target_group,
            rater_context=assignment.rater_context
        )
        
        # Calculate weighted rating
        weighted_rating = evaluation.rating * weight
        
        # Create evaluation record
        eval_record = Evaluation(
            assignment_id=evaluation.assignment_id,
            rating=evaluation.rating,
            weighted_rating=weighted_rating,
            comments=evaluation.comments,
            domain_scores=evaluation.domain_scores,
            status=evaluation.status
        )
        
        db.add(eval_record)
        db.commit()
        db.refresh(eval_record)
        
        # Get rater and target emails
        rater_email = assignment.rater_email
        target_email = assignment.target_email
        
        # Log audit trail
        audit_logger = AuditLogger(db)
        background_tasks.add_task(
            audit_logger.log_submit,
            "evaluation",
            eval_record.id,
            rater_email,
            f"Processed MRE evaluation for {target_email} with weighted rating {weighted_rating:.2f}"
        )
        
        return MREEvaluationResponse(
            evaluation_id=eval_record.id,
            assignment_id=evaluation.assignment_id,
            rating=evaluation.rating,
            weighted_rating=weighted_rating,
            weight_applied=weight,
            target_email=target_email,
            rater_email=rater_email,
            target_group=assignment.target_group,
            rater_context=assignment.rater_context,
            status=eval_record.status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing evaluation: {str(e)}")


@app.get("/api/v2/mre/evaluations/{cycle_id}/weighted-scores")
async def get_weighted_scores(
    cycle_id: int,
    target_email: Optional[EmailStr] = None,
    db: Session = Depends(get_db)
):
    """
    Get weighted evaluation scores for a cycle.
    Optionally filter by target email.
    """
    try:
        weight_handler = WeightMatrixHandler(cycle_id, db)
        
        if target_email:
            # Get scores for specific target
            scores = weight_handler.calculate_final_scores()
            target_scores = scores.get(target_email)
            
            if not target_scores:
                raise HTTPException(status_code=404, detail=f"No scores found for {target_email}")
            
            return {
                "target_email": target_email,
                "scores": target_scores
            }
        else:
            # Get all scores
            scores = weight_handler.calculate_final_scores()
            return {
                "cycle_id": cycle_id,
                "total_targets": len(scores),
                "scores": scores
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting weighted scores: {str(e)}")


# ============================================================================
# Bias Detection Endpoints
# ============================================================================

@app.post("/api/v2/bias/reports/generate", response_model=BiasReportResponse)
async def generate_bias_report(
    request: BiasReportRequest,
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive 360-degree bias detection report.
    
    Includes:
    - Structural completeness checks
    - Role-based bias
    - Temporal bias
    - Distribution bias
    - Similarity bias
    - ML-based pattern detection
    - Inter-rater reliability
    """
    try:
        detector = Complete360BiasDetection(db)
        
        # Generate complete report
        report = detector.generate_complete_report(request.cycle_id)
        
        # Export to dictionary format
        export_data = detector.export_report_to_dict(report)
        
        # If target-specific analysis requested
        if request.include_target_analysis and request.target_email:
            target_summary = detector.get_bias_summary_by_target(
                request.cycle_id,
                request.target_email
            )
            export_data['target_analysis'] = target_summary
        
        return BiasReportResponse(**export_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating bias report: {str(e)}")


@app.get("/api/v2/bias/reports/{cycle_id}")
async def get_bias_report(
    cycle_id: int,
    include_target_analysis: bool = False,
    target_email: Optional[EmailStr] = None,
    db: Session = Depends(get_db)
):
    """Get bias detection report for a cycle (GET endpoint)"""
    request = BiasReportRequest(
        cycle_id=cycle_id,
        include_target_analysis=include_target_analysis,
        target_email=target_email
    )
    return await generate_bias_report(request, db)


@app.get("/api/v2/bias/reports/{cycle_id}/target/{target_email}")
async def get_target_bias_summary(
    cycle_id: int,
    target_email: EmailStr,
    db: Session = Depends(get_db)
):
    """Get bias summary for a specific target"""
    try:
        detector = Complete360BiasDetection(db)
        summary = detector.get_bias_summary_by_target(cycle_id, target_email)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting target bias summary: {str(e)}")


# ============================================================================
# Context-Aware 360-Degree Bias Detection Endpoints
# ============================================================================

@app.post("/api/v2/bias/360/context-aware-report/{cycle_id}")
async def generate_context_aware_360_report(
    cycle_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive context-aware 360-degree bias detection report.
    
    Analyzes bias across multiple rater contexts with:
    - Context-specific bias detection
    - Cross-context comparisons
    - Context consistency analysis
    - Context-specific patterns
    - Multi-context statistical analysis
    """
    try:
        detector = ContextAware360BiasDetection(db)
        
        report = detector.generate_context_aware_report(cycle_id=cycle_id)
        
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating context-aware report: {str(e)}")


@app.get("/api/v2/bias/360/context-analysis/{cycle_id}/target/{email}")
async def get_target_context_analysis(
    cycle_id: int,
    email: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed context-specific analysis for a target.
    
    Returns:
    - Ratings breakdown by context
    - Consistency across contexts
    - Missing contexts
    - Context-specific statistics
    """
    try:
        detector = ContextAware360BiasDetection(db)
        
        analysis = detector.get_target_context_analysis(
            cycle_id=cycle_id,
            target_email=email
        )
        
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving target context analysis: {str(e)}")


@app.get("/api/v2/bias/360/context-comparison/{cycle_id}")
async def get_context_comparison(
    cycle_id: int,
    context1: Optional[str] = Query(None, description="First context to compare"),
    context2: Optional[str] = Query(None, description="Second context to compare"),
    db: Session = Depends(get_db)
):
    """
    Get detailed comparison between two rater contexts.
    
    If contexts not specified, returns comparison for all context pairs.
    """
    try:
        detector = ContextAware360BiasDetection(db)
        
        # Generate full report to get cross-context analyses
        report = detector.generate_context_aware_report(cycle_id=cycle_id)
        
        if context1 and context2:
            # Filter to specific pair
            comparisons = [
                comp for comp in report.get('cross_context_analyses', [])
                if (comp['context_pair'][0] == context1 and comp['context_pair'][1] == context2)
                or (comp['context_pair'][0] == context2 and comp['context_pair'][1] == context1)
            ]
            return {
                'context_pair': [context1, context2],
                'comparisons': comparisons
            }
        else:
            # Return all comparisons
            return {
                'all_comparisons': report.get('cross_context_analyses', []),
                'context_coverage': report.get('context_coverage', {})
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving context comparison: {str(e)}")


@app.get("/api/v2/bias/360/context-coverage/{cycle_id}")
async def get_context_coverage_analysis(
    cycle_id: int,
    db: Session = Depends(get_db)
):
    """
    Get context coverage analysis for a cycle.
    
    Returns:
    - Coverage statistics per context
    - Missing required contexts
    - Balance across contexts
    - Recommendations for improvement
    """
    try:
        detector = ContextAware360BiasDetection(db)
        
        report = detector.generate_context_aware_report(cycle_id=cycle_id)
        
        return {
            'context_coverage': report.get('context_coverage', {}),
            'statistical_summary': report.get('statistical_summary', {}),
            'coverage_findings': [
                f for f in report.get('findings', [])
                if f.get('bias_type') in [
                    'missing_required_contexts',
                    'insufficient_context_coverage',
                    'context_imbalance'
                ]
            ],
            'recommendations': [
                r for r in report.get('recommendations', [])
                if 'context' in r.lower() or 'coverage' in r.lower()
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving context coverage: {str(e)}")


# ============================================================================
# Academic vs Admin Weighted Scoring Endpoints
# ============================================================================

@app.get("/api/v2/scoring/academic-admin/{cycle_id}/score/{email}")
async def get_staff_weighted_score(
    cycle_id: int,
    email: str,
    staff_type: Optional[str] = Query(None, description="Override staff type (academic/admin)"),
    db: Session = Depends(get_db)
):
    """
    Get weighted score for a specific staff member (academic or admin).
    
    Returns detailed breakdown including:
    - Raw and weighted averages
    - Context-specific scores
    - Final weighted score
    """
    try:
        scorer = AcademicAdminScoring(db)
        
        score = scorer.calculate_weighted_score(
            cycle_id=cycle_id,
            target_email=email,
            staff_type=staff_type
        )
        
        return {
            'cycle_id': cycle_id,
            'target_email': email,
            'staff_type': score.staff_type,
            'total_evaluations': score.total_evaluations,
            'raw_average': score.raw_average,
            'weighted_average': score.weighted_average,
            'final_score': score.final_score,
            'context_breakdown': score.context_breakdown,
            'score_components': score.score_components
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating weighted score: {str(e)}")


@app.get("/api/v2/scoring/academic-admin/{cycle_id}/batch")
async def get_batch_weighted_scores(
    cycle_id: int,
    staff_type: Optional[str] = Query(None, description="Filter by staff type (academic/admin)"),
    target_emails: Optional[str] = Query(None, description="Comma-separated list of emails"),
    db: Session = Depends(get_db)
):
    """
    Get weighted scores for multiple staff members.
    
    Can filter by staff type or specific emails.
    """
    try:
        scorer = AcademicAdminScoring(db)
        
        email_list = None
        if target_emails:
            email_list = [e.strip() for e in target_emails.split(',')]
        
        scores = scorer.calculate_batch_scores(
            cycle_id=cycle_id,
            staff_type=staff_type,
            target_emails=email_list
        )
        
        return {
            'cycle_id': cycle_id,
            'staff_type': staff_type or 'all',
            'total_scores': len(scores),
            'scores': scorer.export_scores_to_dict(scores)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating batch scores: {str(e)}")


@app.get("/api/v2/scoring/academic-admin/{cycle_id}/compare")
async def compare_academic_vs_admin(
    cycle_id: int,
    db: Session = Depends(get_db)
):
    """
    Compare scoring between academic and admin staff.
    
    Returns:
    - Statistics for both staff types
    - Differences and analysis
    - Recommendations for fairness
    """
    try:
        scorer = AcademicAdminScoring(db)
        
        comparison = scorer.compare_academic_vs_admin(cycle_id=cycle_id)
        
        return {
            'cycle_id': cycle_id,
            'academic_stats': comparison.academic_stats,
            'admin_stats': comparison.admin_stats,
            'differences': comparison.differences,
            'recommendations': comparison.recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing academic vs admin: {str(e)}")


@app.get("/api/v2/scoring/academic-admin/{cycle_id}/distribution")
async def get_score_distribution(
    cycle_id: int,
    staff_type: Optional[str] = Query(None, description="Filter by staff type (academic/admin)"),
    db: Session = Depends(get_db)
):
    """
    Get score distribution for academic or admin staff.
    
    Returns distribution statistics and histogram data.
    """
    try:
        scorer = AcademicAdminScoring(db)
        
        distribution = scorer.get_score_distribution(
            cycle_id=cycle_id,
            staff_type=staff_type
        )
        
        return distribution
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting score distribution: {str(e)}")


@app.get("/api/v2/scoring/academic-admin/{cycle_id}/validate")
async def validate_evaluations(
    cycle_id: int,
    staff_type: str = Query(..., description="Staff type to validate (academic/admin)"),
    db: Session = Depends(get_db)
):
    """
    Validate that evaluations meet minimum/maximum requirements for a staff type.
    
    Returns validation results with errors and warnings.
    """
    try:
        scorer = AcademicAdminScoring(db)
        
        validation = scorer.validate_evaluations(
            cycle_id=cycle_id,
            staff_type=staff_type
        )
        
        return validation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating evaluations: {str(e)}")


@app.get("/api/v2/scoring/academic-admin/weight-matrices")
async def get_weight_matrices(
    db: Session = Depends(get_db)
):
    """
    Get the weight matrices for academic and admin staff.
    
    Returns both matrices for reference.
    """
    try:
        scorer = AcademicAdminScoring(db)
        
        return {
            'academic': scorer.ACADEMIC_WEIGHT_MATRIX,
            'admin': scorer.ADMIN_WEIGHT_MATRIX,
            'min_evaluations': scorer.MIN_EVALUATIONS,
            'max_evaluations': scorer.MAX_EVALUATIONS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving weight matrices: {str(e)}")


# ============================================================================
# Optimized Evaluation Calculation Endpoints (for 200+ staff)
# ============================================================================

@app.get("/api/v2/scoring/optimized/batch/{cycle_id}")
async def get_optimized_batch_scores(
    cycle_id: int,
    staff_type: Optional[str] = Query(None, description="Filter by staff type (academic/admin)"),
    target_emails: Optional[str] = Query(None, description="Comma-separated list of emails"),
    db: Session = Depends(get_db)
):
    """
    Get optimized batch scores for multiple staff members (optimized for 200+ staff).
    
    Uses bulk queries and vectorized operations for maximum performance.
    """
    try:
        calculator = OptimizedEvaluationCalculator(db)
        
        email_list = None
        if target_emails:
            email_list = [e.strip() for e in target_emails.split(',')]
        
        scores = calculator.calculate_batch_scores_optimized(
            cycle_id=cycle_id,
            staff_type=staff_type,
            target_emails=email_list
        )
        
        return {
            'cycle_id': cycle_id,
            'staff_type': staff_type or 'all',
            'total_scores': len(scores),
            'scores': [
                {
                    'target_email': s.target_email,
                    'staff_type': s.staff_type,
                    'total_evaluations': s.total_evaluations,
                    'raw_average': s.raw_average,
                    'weighted_average': s.weighted_average,
                    'final_score': s.final_score,
                    'context_breakdown': s.context_breakdown
                }
                for s in scores
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating optimized batch scores: {str(e)}")


@app.get("/api/v2/scoring/optimized/statistics/{cycle_id}")
async def get_optimized_statistics(
    cycle_id: int,
    staff_type: Optional[str] = Query(None, description="Filter by staff type (academic/admin)"),
    db: Session = Depends(get_db)
):
    """
    Get aggregate statistics for all scores in a cycle (optimized for large datasets).
    """
    try:
        calculator = OptimizedEvaluationCalculator(db)
        
        stats = calculator.get_score_statistics(
            cycle_id=cycle_id,
            staff_type=staff_type
        )
        
        return {
            'cycle_id': cycle_id,
            'staff_type': staff_type or 'all',
            'statistics': stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")


@app.get("/api/v2/scoring/optimized/compare/{cycle_id}")
async def compare_optimized(
    cycle_id: int,
    db: Session = Depends(get_db)
):
    """
    Compare academic vs admin scoring using optimized bulk processing.
    """
    try:
        calculator = OptimizedEvaluationCalculator(db)
        
        comparison = calculator.compare_academic_vs_admin_optimized(cycle_id=cycle_id)
        
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing scores: {str(e)}")


# ============================================================================
# CEO Report Export Endpoints
# ============================================================================

@app.post("/api/v2/reports/ceo/export")
async def export_ceo_report(
    request: CEOReportRequest,
    db: Session = Depends(get_db)
):
    """
    Export evaluation results for CEO reports.
    
    Supports multiple formats:
    - CSV: Comma-separated values
    - JSON: Structured JSON data
    - Excel: Excel spreadsheet (requires openpyxl)
    
    Includes:
    - Evaluation summaries
    - Weighted scores
    - Bias analysis (optional)
    - Segment breakdowns
    """
    try:
        # Get cycle
        cycle = db.query(Cycle).filter(Cycle.id == request.cycle_id).first()
        if not cycle:
            raise HTTPException(status_code=404, detail="Cycle not found")
        
        # Get all evaluations for this cycle
        evaluations = db.query(Evaluation).join(Assignment).filter(
            Assignment.cycle_id == request.cycle_id,
            Evaluation.status == 'submitted'
        ).all()
        
        if not evaluations:
            raise HTTPException(status_code=404, detail="No evaluations found for this cycle")
        
        # Build report data
        report_data = []
        
        for eval in evaluations:
            assignment = db.query(Assignment).filter(
                Assignment.id == eval.assignment_id
            ).first()
            
            if not assignment:
                continue
            
            # Apply segment filter if specified
            if request.segment_filter:
                target_person = db.query(Person).filter(
                    Person.email == assignment.target_email
                ).first()
                if not target_person or target_person.segment != request.segment_filter:
                    continue
            
            # Get person details
            target_person = db.query(Person).filter(
                Person.email == assignment.target_email
            ).first()
            rater_person = db.query(Person).filter(
                Person.email == assignment.rater_email
            ).first()
            
            row = {
                'cycle_code': cycle.code,
                'target_email': assignment.target_email,
                'target_name': target_person.full_name if target_person else 'Unknown',
                'target_role': target_person.role_title if target_person else 'Unknown',
                'target_segment': target_person.segment.value if target_person and hasattr(target_person, 'segment') else 'Unknown',
                'target_group': assignment.target_group,
                'rater_email': assignment.rater_email,
                'rater_name': rater_person.full_name if rater_person else 'Unknown',
                'rater_role': rater_person.role_title if rater_person else 'Unknown',
                'rater_context': assignment.rater_context,
                'rating': eval.rating,
                'weighted_rating': eval.weighted_rating if eval.weighted_rating else eval.rating,
                'weight': assignment.weight,
                'status': eval.status,
                'submitted_at': eval.submitted_at.isoformat() if eval.submitted_at else None
            }
            
            if request.include_weighted_scores and eval.domain_scores:
                row['domain_scores'] = json.dumps(eval.domain_scores)
            
            report_data.append(row)
        
        # Generate bias analysis if requested
        bias_data = None
        if request.include_bias_analysis:
            try:
                detector = Complete360BiasDetection(db)
                bias_report = detector.generate_complete_report(request.cycle_id)
                bias_data = detector.export_report_to_dict(bias_report)
            except Exception as e:
                # Don't fail the whole export if bias analysis fails
                bias_data = {"error": str(e)}
        
        # Format response based on requested format
        if request.format == "csv":
            return generate_csv_response(report_data, bias_data, cycle.code)
        elif request.format == "json":
            return {
                "cycle_id": request.cycle_id,
                "cycle_code": cycle.code,
                "export_date": datetime.utcnow().isoformat(),
                "total_evaluations": len(report_data),
                "evaluations": report_data,
                "bias_analysis": bias_data
            }
        elif request.format == "excel":
            return generate_excel_response(report_data, bias_data, cycle.code)
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use csv, json, or excel")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting CEO report: {str(e)}")


def generate_csv_response(report_data: List[Dict], bias_data: Optional[Dict], cycle_code: str):
    """Generate CSV response"""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=report_data[0].keys() if report_data else [])
    writer.writeheader()
    writer.writerows(report_data)
    
    # Add bias summary if available
    if bias_data:
        output.write("\n\n=== BIAS ANALYSIS SUMMARY ===\n")
        output.write(f"Overall Bias Score: {bias_data.get('overall_bias_score', 'N/A')}\n")
        output.write(f"Bias Level: {bias_data.get('bias_level', 'N/A')}\n")
        output.write(f"Total Findings: {bias_data.get('findings_count', 0)}\n")
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=ceo_report_{cycle_code}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        }
    )


def generate_excel_response(report_data: List[Dict], bias_data: Optional[Dict], cycle_code: str):
    """Generate Excel response (requires openpyxl)"""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Evaluation Results"
        
        # Write headers
        if report_data:
            headers = list(report_data[0].keys())
            ws.append(headers)
            
            # Style headers
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF")
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
            
            # Write data
            for row in report_data:
                ws.append([row.get(h, '') for h in headers])
        
        # Add bias analysis sheet if available
        if bias_data:
            ws_bias = wb.create_sheet("Bias Analysis")
            ws_bias.append(["Metric", "Value"])
            ws_bias.append(["Overall Bias Score", bias_data.get('overall_bias_score', 'N/A')])
            ws_bias.append(["Bias Level", bias_data.get('bias_level', 'N/A')])
            ws_bias.append(["Total Findings", bias_data.get('findings_count', 0)])
            ws_bias.append(["Total Evaluations", bias_data.get('total_evaluations', 0)])
        
        # Save to bytes
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=ceo_report_{cycle_code}_{datetime.utcnow().strftime('%Y%m%d')}.xlsx"
            }
        )
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Excel export requires openpyxl. Install with: pip install openpyxl"
        )


@app.get("/api/v2/reports/ceo/{cycle_id}")
async def get_ceo_report(
    cycle_id: int,
    format: str = Query("json", regex="^(csv|json|excel)$"),
    include_bias_analysis: bool = True,
    include_weighted_scores: bool = True,
    segment_filter: Optional[StaffSegment] = None,
    db: Session = Depends(get_db)
):
    """Get CEO report (GET endpoint)"""
    request = CEOReportRequest(
        cycle_id=cycle_id,
        format=format,
        include_bias_analysis=include_bias_analysis,
        include_weighted_scores=include_weighted_scores,
        segment_filter=segment_filter
    )
    return await export_ceo_report(request, db)


# ============================================================================
# Health Check
# ============================================================================

@app.get("/api/v2/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Eternity School Evaluation System API",
        "version": "2.0.0",
        "framework": "FastAPI",
        "endpoints": {
            "eom_nominations": "/api/v2/eom/nominations",
            "mre_evaluations": "/api/v2/mre/evaluations",
            "bias_reports": "/api/v2/bias/reports",
            "ceo_reports": "/api/v2/reports/ceo",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

