# Complete Hybrid Identity Survey System

## Overview

The Complete Hybrid Identity Survey System provides a comprehensive solution for managing multiple identity modes in school surveys, enabling users to choose their preferred level of anonymity while maintaining data integrity and enabling meaningful analysis.

## System Architecture

### Core Components

1. **HybridIdentitySurveySystem** - Main system controller
2. **IdentityManager** - Flexible identity management
3. **SurveyEngine** - Advanced survey engine with mode-specific questions
4. **AnalyticsEngine** - Comprehensive analytics with mode-based analysis
5. **AIBiasDetector** - AI-powered bias detection
6. **PrivacyManager** - Privacy & security management
7. **ConsentTracker** - Consent tracking and management

## Identity Modes

### 1. Anonymous Mode
- **Privacy Level**: Maximum
- **Data Retention**: 90 days (auto-delete enabled)
- **Reveal Options**: Cannot reveal (must switch modes first)
- **Use Cases**: Sensitive feedback, discrimination reports, management concerns
- **Questions**: High-sensitivity questions only available in anonymous mode

### 2. Conditionally Anonymous Mode
- **Privacy Level**: High
- **Data Retention**: 180 days (anonymize after 150 days)
- **Reveal Options**: Conditional reveals with consent
- **Use Cases**: Feedback that may need follow-up, gradual trust building
- **Questions**: Includes conditional follow-up questions

### 3. Partially Identified Mode
- **Privacy Level**: Medium
- **Data Retention**: 365 days
- **Reveal Options**: Role and department only
- **Use Cases**: Department-specific feedback, role-based insights
- **Questions**: Standard questions with partial identification

### 4. Fully Identified Mode
- **Privacy Level**: Low
- **Data Retention**: 365 days
- **Reveal Options**: Full identity reveal
- **Use Cases**: Accountable feedback, actionable recommendations
- **Questions**: Includes accountability and follow-up questions

## API Endpoints

### Initialize Session

```http
POST /api/v2/hybrid-identity/initialize-session
```

**Request:**
```json
{
  "user_email": "teacher@example.com",
  "preferred_mode": "conditional",
  "survey_id": 1
}
```

**Response:**
```json
{
  "session_token": "abc123...",
  "mode": "conditional",
  "available_surveys": [...],
  "privacy_level": "high",
  "can_switch_modes": true,
  "consent_required": ["data_collection", "conditional_reveal", "follow_up_contact"],
  "session_expires_at": "2024-01-16T10:30:00Z"
}
```

### Create Survey Session

```http
POST /api/v2/hybrid-identity/create-survey-session?survey_type=comprehensive&session_token=abc123
```

**Response:**
```json
{
  "session_id": "survey_session_123",
  "user_id": "teacher@example.com",
  "anonymous_id": "anon_abc123",
  "identity_mode": "conditional",
  "survey_type": "comprehensive",
  "questions": [
    {
      "id": "cond_001",
      "category": "future_feedback",
      "question": "Would you be open to discussing this feedback in person if needed?",
      "type": "conditional",
      "reveal_trigger": "if_discussion_needed"
    }
  ],
  "response_constraints": {
    "can_edit": true,
    "can_delete": true,
    "edit_window_hours": 48,
    "traceability": "conditional"
  },
  "privacy_controls": {
    "data_encryption": "high",
    "access_logging": "standard",
    "data_sharing": "conditional"
  },
  "expires_at": "2024-01-16T10:30:00Z"
}
```

### Submit Survey Response

```http
POST /api/v2/hybrid-identity/submit-response
```

**Request:**
```json
{
  "session_token": "abc123",
  "responses": {
    "cond_001": {
      "willing_to_discuss": true,
      "contact_preference": "email"
    },
    "general_feedback": "Overall good school but needs improvement in communication"
  },
  "reveal_conditions": {
    "allow_hr_contact": true,
    "allow_principal_contact": false
  }
}
```

**Response:**
```json
{
  "response_id": "resp_123",
  "survey_session_id": "survey_session_123",
  "identity_mode": "conditional",
  "responses": {...},
  "processed_at": "2024-01-15T10:30:00Z",
  "sentiment_scores": {
    "overall_sentiment": "neutral",
    "positive_score": 0.5,
    "negative_score": 0.3,
    "neutral_score": 0.2
  },
  "themes_extracted": ["communication", "workplace_culture", "management"],
  "urgency_level": "medium",
  "reveal_conditions": {...},
  "traceability": "conditional"
}
```

### Switch Identity Mode

```http
POST /api/v2/hybrid-identity/switch-mode
```

**Request:**
```json
{
  "user_email": "teacher@example.com",
  "new_mode": "identified",
  "reason": "Want to provide actionable feedback"
}
```

**Response:**
```json
{
  "success": true,
  "new_mode": "identified",
  "data_affected": {
    "migration_required": true,
    "data_affected": ["responses", "preferences", "reveals"],
    "anonymization_needed": false,
    "identification_needed": true
  },
  "privacy_changes": {
    "encryption_level_changed": true,
    "access_control_changed": true,
    "data_sharing_changed": true
  },
  "consent_updates_required": ["full_identification"]
}
```

### Process Reveal Request

```http
POST /api/v2/hybrid-identity/process-reveal-request?user_email=teacher@example.com&reveal_type=conditional
```

**Response:**
```json
{
  "request_id": "req_123",
  "status": "pending",
  "cooling_off_period": 7,
  "next_steps": [
    "Wait for cooling off period",
    "Set reveal conditions",
    "Approve conditional reveal"
  ],
  "irreversible_warning": "Conditional reveal may become permanent based on conditions."
}
```

### Analyze Survey Data

```http
GET /api/v2/hybrid-identity/analyze-survey-data?survey_id=1
```

**Response:**
```json
{
  "overall_metrics": {
    "total_responses": 150,
    "completion_rate": 0.85,
    "average_sentiment": 0.6,
    "response_quality": 0.75
  },
  "identity_mode_analysis": {
    "anonymous": {
      "response_count": 45,
      "average_sentiment": 0.4,
      "honesty_indicator": {
        "honesty_score": 0.92,
        "confidence_level": "high",
        "interpretation": "Anonymous feedback shows high honesty levels"
      },
      "critical_issues": ["communication", "workplace_culture"],
      "suggestion_quality": 0.8
    },
    "conditional": {
      "response_count": 60,
      "average_sentiment": 0.6,
      "honesty_indicator": {
        "honesty_score": 0.75,
        "confidence_level": "medium"
      }
    },
    "identified": {
      "response_count": 45,
      "average_sentiment": 0.7,
      "honesty_indicator": {
        "honesty_score": 0.65,
        "confidence_level": "medium",
        "potential_biases": ["social_desirability", "fear_of_repercussion"]
      }
    },
    "mode_comparison": {
      "honesty_by_mode": {...},
      "issue_depth_by_mode": {...},
      "constructiveness_by_mode": {...},
      "sensitivity_by_mode": {...}
    }
  },
  "bias_analysis": {...},
  "trend_analysis": {...},
  "predictive_insights": [...],
  "actionable_recommendations": [...]
}
```

## System Capabilities

### Identity Management

✅ **4 Identity Modes**: Anonymous, Conditional, Partial, Full  
✅ **Dynamic Switching**: Change modes during survey  
✅ **Conditional Revealing**: User-controlled reveal conditions  
✅ **Gradual Trust Building**: Start anonymous, reveal when ready  
✅ **Mode History Tracking**: Complete audit trail of mode changes

### Survey Intelligence

✅ **Mode-Specific Questions**: Different questions per identity mode  
✅ **AI-Powered Routing**: Smart question selection  
✅ **Sentiment Analysis**: Real-time sentiment scoring  
✅ **Urgency Detection**: Automatic urgency classification  
✅ **Theme Extraction**: Automatic theme identification  
✅ **Response Constraints**: Mode-specific editing and deletion rules

### Bias Detection & Fairness

✅ **Real-Time Bias Detection**: Detects all types of evaluation bias  
✅ **Voter Pattern Analysis**: Analyzes individual voter tendencies  
✅ **Fair Score Generation**: Creates bias-adjusted fair evaluations  
✅ **Transparency Reports**: Explains how fairness was achieved  
✅ **Mode-Based Honesty Analysis**: Compares honesty across modes

### Privacy & Security

✅ **Cryptographic Anonymity**: Secure anonymous identities  
✅ **Granular Consent**: Detailed consent management  
✅ **Audit Trails**: Complete audit logging  
✅ **Compliance Ready**: GDPR and local regulation compliant  
✅ **Data Retention Policies**: Automatic data lifecycle management  
✅ **Right to be Forgotten**: Complete data deletion support

### Analytics & Insights

✅ **Mode-Based Analysis**: Compare anonymous vs identified feedback  
✅ **Honesty Indicators**: Measure truthfulness by identity mode  
✅ **Predictive Insights**: Predict future trends and issues  
✅ **Actionable Recommendations**: Generate specific improvement suggestions  
✅ **Trend Analysis**: Identify patterns over time  
✅ **Department Insights**: Department-specific analysis

## Usage Example

```python
from backend.hybrid_identity_system import HybridIdentitySurveySystem

# Initialize system
hybrid_system = HybridIdentitySurveySystem(db_session)

# User chooses conditional anonymity
session_data = hybrid_system.initialize_user_session(
    user_id="teacher@example.com",
    preferred_mode="conditional"
)

# Create survey session
survey_session = hybrid_system.survey_engine.create_survey_session(
    user_profile=session_data,
    survey_type="school_climate_comprehensive"
)

# Submit responses
mock_responses = {
    "session_id": survey_session["session_id"],
    "responses": {
        "cond_001": {"willing_to_discuss": True},
        "general_feedback": "Good school but needs improvement"
    }
}

processed_response = hybrid_system.survey_engine.process_response(
    response_data=mock_responses,
    identity_mode=HybridIdentityMode.CONDITIONALLY_ANONYMOUS
)

# Analyze all survey data
analytics_results = hybrid_system.analytics_engine.analyze_survey_data(
    survey_data=hybrid_system.get_all_survey_data(),
    identity_breakdown=hybrid_system.get_identity_breakdown()
)
```

## Integration with Existing Systems

The Hybrid Identity Survey System integrates seamlessly with:

- **Survey Identity Manager**: Core identity preference management
- **Conditional Anonymity Engine**: Conditional reveal scenarios
- **Smart Notification System**: Notifications for reveals and mode changes
- **Bias Detection System**: Comprehensive bias analysis
- **Analytics Engine**: Mode-based analytics and insights

## Best Practices

1. **Default to Conditional**: Start users in conditional mode for flexibility
2. **Respect User Choice**: Always honor user's identity mode preference
3. **Clear Communication**: Explain privacy implications of each mode
4. **Gradual Trust Building**: Allow users to start anonymous and reveal later
5. **Comprehensive Analytics**: Use mode-based analysis to understand feedback patterns
6. **Bias Awareness**: Account for honesty differences across modes
7. **Privacy First**: Always prioritize user privacy and data protection

## Future Enhancements

- Machine learning for optimal mode recommendations
- Advanced sentiment analysis with NLP
- Real-time bias detection during survey completion
- Predictive analytics for issue prevention
- Integration with external survey platforms
- Mobile app support
- Advanced consent management with granular permissions
