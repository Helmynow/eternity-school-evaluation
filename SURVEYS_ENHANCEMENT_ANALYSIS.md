# Surveys Feature Enhancement: Further Considerations Analysis

**Date**: January 5, 2026  
**Context**: Gap resolution for abandoned survey tracking, session timeout configuration, and admin analytics

---

## 1. Migration Strategy: Backfill abandoned_at Field

Three options for populating the new `abandoned_at` column for existing SurveyResponse records.

### Option A: Set NULL (Conservative Approach)

**What it does**: Leave all existing responses with `abandoned_at = NULL`. Only populate `abandoned_at` for surveys submitted after migration.

#### Pros ✅
- **Zero risk**: No data manipulation; purely additive schema change
- **Fast migration**: Single ALTER TABLE statement, no data processing
- **Audit-clean**: Preserves data integrity; clear distinction between old/new records
- **Reversible**: Can roll back without data loss
- **Simple queries**: Just filter `WHERE abandoned_at IS NULL` to identify old data
- **Performance**: Instant; no table locks or resource strain

#### Cons ❌
- **No historical data**: Cannot analyze abandonment patterns for past surveys
- **Analytics gap**: Completion rates will be artificially low (excludes old responses)
- **Incomplete story**: Can't identify if past surveys had abandonment issues
- **Misleading metrics**: Before/after comparisons impossible
- **Limited insights**: Miss feedback about pre-migration user behavior

**Best for**: Organizations wanting to start fresh; low priority on historical analysis

---

### Option B: Estimate from Timestamps & Session Patterns (Intelligent Backfill)

**What it does**: Use heuristics to infer abandonment from existing data:
- Compare `submitted_at` vs `created_at` (if < 30 seconds difference → likely abandoned)
- Check `session_id` patterns for incomplete sequences
- Analyze response text for incomplete entries ("N/A", empty fields, typos)
- Mark as abandoned if response lacks required fields

#### Pros ✅
- **Preserves history**: Historical abandonment patterns become visible
- **Rich analytics**: Pre/post migration comparisons show true trends
- **Behavioral insights**: Identify past pain points (e.g., "50% abandoned at Q5 in 2024")
- **Actionable**: Guide survey redesign based on actual historical behavior
- **Competitive advantage**: Understand user patterns competitors miss
- **No new surveys needed**: Immediate analytics without waiting for new data

#### Cons ❌
- **Estimation errors**: Heuristics may misclassify responses
  - False positives: Quick legitimate responses flagged as abandoned
  - False negatives: Truly abandoned but incomplete data marked as submitted
- **Complex logic**: Multiple rules to maintain; edge cases hard to predict
- **Performance risk**: Scanning millions of rows; potential table locks
- **Data quality issues**: Historical data may be incomplete/inconsistent
- **Audit concerns**: "Estimated" data may raise compliance questions
- **Maintenance burden**: Future schema changes require updating heuristics

**Confidence levels**:
- High confidence (>90%): `submitted_at - created_at < 5 seconds` AND `(empty required fields OR session incomplete)`
- Medium confidence (50-80%): Pattern matches single heuristic
- Low confidence (<50%): Ambiguous cases (e.g., user saved draft for 3 days, then submitted)

**Best for**: Organizations with rich historical data and strong analytics needs; willing to accept estimation uncertainty

---

### Option C: Require Fresh Surveys After Migration (Clean Slate)

**What it does**: Archive all pre-migration responses as "legacy". Only track abandonment for new surveys created post-migration. Provide migration API for schools to re-send surveys to respondents.

#### Pros ✅
- **Data clarity**: No guessing; all abandonment data is ground truth
- **Clean analytics**: Pre-migration noise eliminated; true baseline
- **Fresh consent**: Re-ask permission (GDPR-compliant, ethical)
- **Feature parity**: All respondents see updated survey UI/experience
- **Better data quality**: New surveys benefit from schema completeness
- **Stakeholder buy-in**: Can explain "comprehensive update" to schools
- **Rebuild engagement**: Re-engagement campaign improves response rates

#### Cons ❌
- **Operational burden**: Require school admins to re-launch surveys
- **Response fatigue**: Respondents asked to fill same survey twice
- **Time cost**: 4-8 weeks to collect equivalent new responses
- **Low adoption**: Schools may resist re-launching surveys (20-30% retry rate)
- **Lost context**: Can't correlate new vs old responses to same respondents
- **Analytics delay**: No abandonment metrics for 6+ weeks post-launch
- **Compliance risk**: Some respondents may refuse to re-consent

**Timeline**:
- Week 1-2: Notify schools of migration, provide re-launch tools
- Week 3-6: Schools re-send surveys to respondents
- Week 7+: Collect new responses with full abandonment tracking

**Best for**: Regulatory-sensitive contexts; low historical analysis priority; willingness to tolerate downtime

---

### Comparison Table

| Dimension | Option A (NULL) | Option B (Estimate) | Option C (Fresh Start) |
|-----------|---|---|---|
| **Implementation Speed** | ⚡ 1 hour | ⚠️ 2-3 days | ⚠️ 2-4 weeks |
| **Data Accuracy** | ✅ 100% (historical) | 🟡 70-85% | ✅ 100% (new data) |
| **Historical Insights** | ❌ None | ✅ Strong | ❌ None |
| **Operational Cost** | ✅ None | 🟡 High (QA effort) | ⚠️ High (admin + comms) |
| **Risk Level** | ✅ Zero | 🟡 Medium | 🟡 Medium |
| **User Impact** | ✅ None | ✅ None | ⚠️ Re-engagement required |
| **Compliance** | ✅ Clean | 🟡 "Estimated" label needed | ✅ Fresh consent |
| **Analytics Ready** | ❌ Immediate (incomplete) | ✅ Immediate (estimated) | ⚠️ Weeks 7+ (complete) |

---

### 🎯 Recommendation

**Hybrid Approach: Option A + Option B Selective**

1. **Default**: Use **Option A** (Set NULL for all existing responses)
2. **High-confidence backfill**: For surveys with clear incomplete patterns (e.g., submitted in <5 seconds with empty required fields), mark as `abandoned_at = submitted_at` with confidence score
3. **Flag uncertain data**: Add `abandoned_confidence` field (HIGH/MEDIUM/LOW/NULL)
4. **Separate reporting**: Show "historical + estimated" analytics separately from "verified post-migration"

**Implementation**:
```sql
-- Step 1: Add columns
ALTER TABLE survey_response ADD COLUMN abandoned_at TIMESTAMP NULL;
ALTER TABLE survey_response ADD COLUMN abandoned_confidence VARCHAR(10) DEFAULT NULL;

-- Step 2: Conservative backfill (high confidence only)
UPDATE survey_response 
SET abandoned_at = submitted_at, 
    abandoned_confidence = 'HIGH'
WHERE 
  (submitted_at - created_at) < INTERVAL '5 seconds'
  AND response_json->>'q1' IS NULL  -- missing required fields
  AND response_json->>'q2' IS NULL
  AND session_status IS NULL;

-- Step 3: NULL for all others
-- (already NULL by default)

-- Step 4: Track start date
ALTER TABLE survey_response ADD COLUMN started_at TIMESTAMP NOT NULL DEFAULT NOW();
```

**Benefits**:
- Safe (conservative by default)
- Some historical insight (high-confidence cases only)
- Clear data provenance (confidence field)
- Future-proof (all new responses are ground truth)
- Quick implementation (1-2 days)

---

## 2. Session Timeout Configuration ✅

**Status**: **AGREED & CONFIRMED**

### Environment Variable Approach

```env
# .env (development)
SURVEY_SESSION_TIMEOUT_MINUTES=30

# .env.production
SURVEY_SESSION_TIMEOUT_MINUTES=30

# .env.test
SURVEY_SESSION_TIMEOUT_MINUTES=5  # Faster for testing
```

### Implementation

**Backend (FastAPI)**:
```python
# backend/config.py
import os
from datetime import timedelta

SURVEY_SESSION_TIMEOUT_MINUTES = int(
    os.getenv('SURVEY_SESSION_TIMEOUT_MINUTES', '30')
)
SESSION_TIMEOUT = timedelta(minutes=SURVEY_SESSION_TIMEOUT_MINUTES)

# Usage in HybridIdentitySurveySystem
class HybridIdentitySurveySystem:
    def __init__(self):
        self.session_timeout = SESSION_TIMEOUT
    
    def check_session_timeout(self, session_id: str) -> bool:
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        elapsed = datetime.utcnow() - session['last_activity']
        return elapsed > self.session_timeout  # True if timed out
    
    def mark_session_abandoned(self, session_id: str):
        session = self.sessions[session_id]
        session['status'] = 'abandoned'
        session['abandoned_at'] = datetime.utcnow()
        # Persist to DB
        db.session.query(SurveyResponse).filter(
            SurveyResponse.session_id == session_id
        ).update({'abandoned_at': session['abandoned_at']})
        db.session.commit()
```

**Per-School Customization** (optional future):
```python
# Allow schools to override global timeout
class SchoolSurveyConfig(Base):
    school_id = Column(String)
    session_timeout_minutes = Column(Integer, nullable=True)  # Override global

def get_session_timeout_for_school(school_id: str) -> timedelta:
    config = db.query(SchoolSurveyConfig).filter_by(school_id=school_id).first()
    minutes = config.session_timeout_minutes if config else SURVEY_SESSION_TIMEOUT_MINUTES
    return timedelta(minutes=minutes)
```

### Monitoring

```python
# Add metrics
class SurveyMetrics:
    @staticmethod
    def log_session_timeout(survey_id: str, session_id: str, timeout_minutes: int):
        logger.info(
            f"session_timeout",
            extra={
                'survey_id': survey_id,
                'session_id': session_id,
                'timeout_minutes': timeout_minutes,
                'timestamp': datetime.utcnow()
            }
        )
```

**✅ This approach is simple, scalable, and maintainable.**

---

## 3. Analytics Dashboard: Complete Chart Specifications

### Admin Endpoint: `/api/v2/surveys/admin/abandonment-analytics`

**Authentication**: `_require_admin_access` middleware  
**Parameters**:
- `survey_id` (optional): Filter to single survey
- `date_range` (optional): "7d", "30d", "90d", default "30d"
- `include_estimations` (optional): Boolean, show estimated vs verified, default false

**Response Structure**:
```json
{
  "summary": { ... },
  "charts": {
    "completion_funnel": { ... },
    "abandonment_timeline": { ... },
    "dropout_heatmap": { ... },
    "time_to_abandon": { ... },
    "identity_mode_impact": { ... },
    "response_completion_status": { ... },
    "department_completion_rates": { ... },
    "session_duration_distribution": { ... }
  },
  "generated_at": "2026-01-05T14:30:00Z",
  "data_confidence": "HIGH|MEDIUM|LOW"
}
```

---

### 📊 Chart 1: Completion Funnel

**Type**: Waterfall/Funnel Chart  
**Purpose**: Show where respondents drop off  
**Data**:
```json
{
  "type": "funnel",
  "title": "Survey Completion Funnel",
  "stages": [
    {
      "name": "Invited",
      "count": 500,
      "percentage": 100
    },
    {
      "name": "Started (Q1-Q5)",
      "count": 450,
      "percentage": 90,
      "dropout": 50
    },
    {
      "name": "Mid Survey (Q6-Q15)",
      "count": 380,
      "percentage": 76,
      "dropout": 70
    },
    {
      "name": "Near End (Q16-Q20)",
      "count": 320,
      "percentage": 64,
      "dropout": 60
    },
    {
      "name": "Completed",
      "count": 280,
      "percentage": 56,
      "dropout": 40
    }
  ],
  "completion_rate": 0.56,
  "abandonment_rate": 0.44
}
```

**Visualization**: Waterfall bars showing absolute dropoff at each stage + cumulative %

---

### 📊 Chart 2: Abandonment Timeline

**Type**: Line Chart with Area  
**Purpose**: Track abandonment patterns over survey duration (time-based)  
**Data**:
```json
{
  "type": "line_area",
  "title": "Survey Abandonment Over Time",
  "x_axis": "Minutes Spent in Survey",
  "y_axis": "Number of Respondents",
  "series": [
    {
      "name": "Active Respondents",
      "data": [
        { "minutes": 0, "count": 500 },
        { "minutes": 2, "count": 480 },
        { "minutes": 5, "count": 450 },
        { "minutes": 10, "count": 380 },
        { "minutes": 15, "count": 320 },
        { "minutes": 20, "count": 280 }
      ],
      "color": "green"
    },
    {
      "name": "Abandoned Sessions",
      "data": [
        { "minutes": 0, "count": 0 },
        { "minutes": 2, "count": 20 },
        { "minutes": 5, "count": 50 },
        { "minutes": 10, "count": 120 },
        { "minutes": 15, "count": 180 },
        { "minutes": 20, "count": 220 }
      ],
      "color": "red"
    }
  ],
  "median_time_to_abandon_minutes": 7.5
}
```

**Visualization**: Stacked area chart showing active vs abandoned over survey duration

---

### 📊 Chart 3: Question-Level Dropout Heatmap

**Type**: Heatmap  
**Purpose**: Identify which specific questions cause abandonment  
**Data**:
```json
{
  "type": "heatmap",
  "title": "Dropout Heatmap: Abandonment by Question",
  "matrix": [
    {
      "question_id": "q1",
      "question_text": "How satisfied are you with the physical environment?",
      "completions": 500,
      "dropouts": 20,
      "dropout_rate": 0.04,
      "avg_time_seconds": 30
    },
    {
      "question_id": "q5",
      "question_text": "Describe any safety concerns you've observed",
      "completions": 450,
      "dropouts": 70,
      "dropout_rate": 0.16,
      "avg_time_seconds": 120
    },
    {
      "question_id": "q10",
      "question_text": "Rate staff collaboration effectiveness",
      "completions": 380,
      "dropouts": 120,
      "dropout_rate": 0.32,
      "avg_time_seconds": 200
    },
    {
      "question_id": "q15",
      "question_text": "Describe management blind spots",
      "completions": 320,
      "dropouts": 180,
      "dropout_rate": 0.56,
      "avg_time_seconds": 300
    }
  ],
  "critical_questions": [
    {
      "question_id": "q15",
      "dropout_rate": 0.56,
      "recommendation": "Consider making optional or providing write-in examples"
    }
  ]
}
```

**Visualization**: Color-coded heatmap (green=low dropout, red=high dropout) with question text labels

---

### 📊 Chart 4: Time-to-Abandon Distribution

**Type**: Histogram / Box Plot  
**Purpose**: Understand typical abandonment timing  
**Data**:
```json
{
  "type": "histogram",
  "title": "When Respondents Abandon Surveys",
  "bins": [
    {
      "range": "0-2 min",
      "count": 15,
      "percentage": 3.8
    },
    {
      "range": "2-5 min",
      "count": 35,
      "percentage": 8.9
    },
    {
      "range": "5-10 min",
      "count": 85,
      "percentage": 21.6
    },
    {
      "range": "10-15 min",
      "count": 120,
      "percentage": 30.5
    },
    {
      "range": "15-20 min",
      "count": 95,
      "percentage": 24.2
    },
    {
      "range": "20+ min",
      "count": 43,
      "percentage": 10.9
    }
  ],
  "statistics": {
    "median_minutes": 11.2,
    "mean_minutes": 12.4,
    "std_dev_minutes": 4.8,
    "min_minutes": 0.1,
    "max_minutes": 28.5
  }
}
```

**Visualization**: Histogram bars with overlay of normal distribution curve

---

### 📊 Chart 5: Identity Mode Impact on Completion

**Type**: Grouped Bar Chart  
**Purpose**: Compare completion rates by anonymity mode  
**Data**:
```json
{
  "type": "grouped_bar",
  "title": "Completion Rate by Identity Mode",
  "categories": [
    {
      "mode": "Anonymous",
      "color": "blue",
      "total_started": 250,
      "completed": 180,
      "abandoned": 70,
      "completion_rate": 0.72,
      "avg_time_minutes": 13.2
    },
    {
      "mode": "Conditional Anonymous",
      "color": "green",
      "total_started": 150,
      "completed": 96,
      "abandoned": 54,
      "completion_rate": 0.64,
      "avg_time_minutes": 14.5
    },
    {
      "mode": "Partially Identified",
      "color": "yellow",
      "total_started": 75,
      "completed": 42,
      "abandoned": 33,
      "completion_rate": 0.56,
      "avg_time_minutes": 15.8
    },
    {
      "mode": "Fully Identified",
      "color": "red",
      "total_started": 25,
      "completed": 8,
      "abandoned": 17,
      "completion_rate": 0.32,
      "avg_time_minutes": 11.2
    }
  ],
  "insight": "Anonymous mode has highest completion rate (+40% vs fully identified)"
}
```

**Visualization**: Grouped bars (blue=completed, red=abandoned) per mode

---

### 📊 Chart 6: Response Completion Status Breakdown

**Type**: Donut Chart  
**Purpose**: Overall survey status distribution  
**Data**:
```json
{
  "type": "donut",
  "title": "Survey Response Status Distribution",
  "segments": [
    {
      "label": "Completed",
      "value": 280,
      "percentage": 56,
      "color": "green"
    },
    {
      "label": "Abandoned (Timeout)",
      "value": 120,
      "percentage": 24,
      "color": "red"
    },
    {
      "label": "Abandoned (Manual Exit)",
      "value": 100,
      "percentage": 20,
      "color": "orange"
    }
  ],
  "total": 500,
  "legend_position": "right"
}
```

**Visualization**: Donut chart with percentage labels + legend

---

### 📊 Chart 7: Department-Level Completion Rates

**Type**: Horizontal Bar Chart  
**Purpose**: Identify departmental differences in response patterns  
**Data**:
```json
{
  "type": "horizontal_bar",
  "title": "Completion Rate by Department",
  "departments": [
    {
      "name": "Academic",
      "started": 150,
      "completed": 110,
      "abandoned": 40,
      "completion_rate": 0.73,
      "avg_time_minutes": 12.8
    },
    {
      "name": "Administrative",
      "started": 120,
      "completed": 84,
      "abandoned": 36,
      "completion_rate": 0.70,
      "avg_time_minutes": 13.1
    },
    {
      "name": "Support Staff",
      "started": 100,
      "completed": 52,
      "abandoned": 48,
      "completion_rate": 0.52,
      "avg_time_minutes": 14.5
    },
    {
      "name": "Leadership",
      "started": 30,
      "completed": 18,
      "abandoned": 12,
      "completion_rate": 0.60,
      "avg_time_minutes": 11.2
    }
  ],
  "best_performing": "Academic (73%)",
  "needs_attention": "Support Staff (52%)"
}
```

**Visualization**: Horizontal bars sorted by completion rate (descending)

---

### 📊 Chart 8: Session Duration Distribution

**Type**: Box Plot / Violin Plot  
**Purpose**: Understand typical survey completion time vs abandonment time  
**Data**:
```json
{
  "type": "box_plot",
  "title": "Survey Duration: Completed vs Abandoned",
  "distributions": [
    {
      "group": "Completed Surveys",
      "color": "green",
      "statistics": {
        "min": 8.5,
        "q1": 11.2,
        "median": 13.8,
        "q3": 16.4,
        "max": 28.5,
        "mean": 14.2,
        "std_dev": 3.8
      },
      "sample_size": 280,
      "outliers": 8
    },
    {
      "group": "Abandoned Surveys",
      "color": "red",
      "statistics": {
        "min": 0.1,
        "q1": 5.2,
        "median": 9.8,
        "q3": 14.1,
        "max": 27.3,
        "mean": 10.4,
        "std_dev": 6.2
      },
      "sample_size": 220,
      "outliers": 12
    }
  ],
  "insight": "Completed surveys take 4 minutes longer on average (14.2 vs 10.4 min)"
}
```

**Visualization**: Box plots side-by-side showing distribution difference

---

### 📊 Chart 9: Abandonment Trend Over Time (Optional)

**Type**: Time Series Line Chart  
**Purpose**: Track abandonment rates weekly/daily to identify trends  
**Data**:
```json
{
  "type": "time_series",
  "title": "Weekly Abandonment Rate Trend",
  "period": "7d",
  "data_points": [
    {
      "week": "2026-01-01",
      "abandonment_rate": 0.42,
      "total_responses": 85,
      "abandoned_count": 36,
      "avg_completion_time_minutes": 13.2
    },
    {
      "week": "2026-01-08",
      "abandonment_rate": 0.44,
      "total_responses": 92,
      "abandoned_count": 41,
      "avg_completion_time_minutes": 12.8
    },
    {
      "week": "2026-01-15",
      "abandonment_rate": 0.40,
      "total_responses": 88,
      "abandoned_count": 35,
      "avg_completion_time_minutes": 14.1
    }
  ],
  "trend": "stable",
  "trend_direction": "slightly_decreasing"
}
```

**Visualization**: Line chart with trend indicator (↓ improving)

---

## Summary: Which Charts to Build First

### Phase 1 (MVP - Critical Insights)
1. ✅ **Completion Funnel** (Chart 1) - Shows where the biggest problems are
2. ✅ **Dropout Heatmap** (Chart 3) - Identifies problem questions
3. ✅ **Identity Mode Impact** (Chart 5) - Shows if anonymity is the issue

### Phase 2 (Enhanced Analytics)
4. **Response Status Breakdown** (Chart 6) - Overall health snapshot
5. **Department Completion Rates** (Chart 7) - Departmental insights
6. **Time-to-Abandon Distribution** (Chart 4) - Behavioral patterns

### Phase 3 (Advanced)
7. **Session Duration Distribution** (Chart 8) - Predictive modeling
8. **Abandonment Timeline** (Chart 2) - Detailed temporal analysis
9. **Trend Analysis** (Chart 9) - Long-term trend monitoring

---

## Implementation Timeline

| Item | Timeline | Priority |
|------|----------|----------|
| Migration (Option A + selective B) | 1-2 days | 🔴 CRITICAL |
| Session timeout env var | 1 day | 🔴 CRITICAL |
| API endpoint `/api/v2/surveys/admin/abandonment-analytics` | 2-3 days | 🔴 CRITICAL |
| Phase 1 Charts (Funnel, Heatmap, Identity Mode) | 3-4 days | 🔴 CRITICAL |
| Phase 2 Charts (Status, Department, Duration) | 3-4 days | 🟡 HIGH |
| Phase 3 Charts (Timeline, Trends) | 2-3 days | 🟢 MEDIUM |
| **Total** | **12-17 days** | |

---

## Next Steps

1. ✅ **Approve migration strategy** (Hybrid: Option A + selective Option B)
2. ✅ **Confirm session timeout approach** (env var, 30min default, per-school optional)
3. ✅ **Review analytics charts** (9 charts across 3 phases)
4. Start Phase 1 implementation (migration + API + 3 core charts)

