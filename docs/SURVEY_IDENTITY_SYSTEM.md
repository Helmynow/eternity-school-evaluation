# Hybrid Identity Survey System

## Overview

The Hybrid Identity Survey System provides a flexible identity controller that allows users to choose between anonymous, identified, or conditional identity modes for surveys and evaluations. This system respects user privacy preferences while enabling controlled identity revelation when needed.

## Features

### 1. Flexible Identity Modes

Users can choose from three identity modes:

- **Anonymous**: Complete anonymity, no identity tracking
  - Maximum privacy level
  - Short data retention (90 days)
  - Cannot reveal identity (must revoke anonymity first)
  
- **Identified**: Full identification, standard tracking
  - Medium privacy level
  - Standard data retention (365 days)
  - Full reveal options available
  
- **Conditional**: Conditional reveal with consent-based options
  - High privacy level
  - Medium data retention (180 days)
  - Limited reveal options with consent

### 2. Identity Reveal Methods

When users are in identified or conditional mode, they can choose from multiple reveal methods:

- **Full**: Complete identity reveal (email, name, role, department)
- **Partial Role**: Reveal role/title only
- **Partial Department**: Reveal department only
- **Gradual**: Gradual reveal over time (starts with minimal info)
- **Consent-Based**: Reveal with explicit consent confirmation

### 3. Privacy Levels

The system automatically calculates privacy levels based on identity mode:

- **Maximum**: Anonymous mode
- **High**: Conditional mode
- **Medium**: Identified mode
- **Low**: Full identification with complete tracking

### 4. Data Retention Policies

Automatic data retention policies based on identity mode:

- **Anonymous**: 90 days, auto-delete enabled
- **Conditional**: 180 days, anonymize after 150 days
- **Identified**: 365 days, standard retention

## API Endpoints

### Set Identity Preference

```http
POST /api/v2/survey/identity/preference
```

**Request Body:**
```json
{
  "user_email": "user@example.com",
  "preference": "conditional",  // "anonymous", "identified", or "conditional"
  "survey_id": 1  // Optional: survey-specific preference
}
```

**Response:**
```json
{
  "mode": "conditional",
  "mode_enum": "conditional",
  "reveal_options": {
    "can_reveal": true,
    "options": [
      {
        "method": "consent_based",
        "description": "Reveal with explicit consent",
        "available": true
      },
      {
        "method": "gradual",
        "description": "Gradual reveal over time",
        "available": true
      }
    ],
    "message": "Conditional mode: Limited reveal options with consent"
  },
  "privacy_level": "high",
  "data_retention": {
    "retention_days": 180,
    "auto_delete": false,
    "anonymize_after": 150,
    "policy_type": "conditional"
  },
  "anonymous_mode": false,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Handle Identity Reveal

```http
POST /api/v2/survey/identity/reveal
```

**Request Body:**
```json
{
  "user_email": "user@example.com",
  "method": "consent_based",  // "full", "partial_role", "partial_department", "gradual", "consent_based"
  "target": "manager@example.com",  // Optional: who to reveal to
  "consent": true,  // Required for consent_based
  "conditions": {  // Optional: conditions for conditional reveals
    "purpose": "performance_review",
    "duration": "30_days"
  },
  "revoke_anonymity": false,  // Set to true to switch from anonymous mode
  "survey_id": 1
}
```

**Response:**
```json
{
  "can_reveal": true,
  "reveal_method": "consent_based",
  "partial_reveal": {
    "available": true,
    "options": [...]
  },
  "revoke_anonymity": null,
  "reveal_executed": {
    "success": true,
    "reveal_data": {
      "user_id": "user@example.com",
      "method": "consent_based",
      "timestamp": "2024-01-15T10:30:00Z",
      "revealed_info": {
        "email": "user@example.com",
        "full_name": "John Doe",
        "consent_confirmed": true
      }
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Get Identity Status

```http
GET /api/v2/survey/identity/status/{user_email}?survey_id=1
```

**Response:**
```json
{
  "user_id": "user@example.com",
  "current_mode": "conditional",
  "anonymous_mode": false,
  "privacy_level": "high",
  "reveal_options": {
    "can_reveal": true,
    "options": [...]
  },
  "retention_policy": {
    "retention_days": 180,
    "auto_delete": false,
    "anonymize_after": 150,
    "policy_type": "conditional"
  }
}
```

### Revoke Anonymity

```http
POST /api/v2/survey/identity/revoke-anonymity?user_email=user@example.com&survey_id=1
```

**Response:**
```json
{
  "success": true,
  "message": "Anonymity revoked successfully",
  "new_mode": "conditional",
  "reveal_options": {
    "can_reveal": true,
    "options": [...]
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Usage Examples

### Example 1: Set Anonymous Mode

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v2/survey/identity/preference",
    json={
        "user_email": "teacher@example.com",
        "preference": "anonymous",
        "survey_id": 1
    }
)

result = response.json()
print(f"Mode: {result['mode']}")
print(f"Privacy Level: {result['privacy_level']}")
print(f"Retention: {result['data_retention']['retention_days']} days")
```

### Example 2: Conditional Reveal with Consent

```python
# First, set conditional mode
requests.post(
    "http://localhost:8000/api/v2/survey/identity/preference",
    json={
        "user_email": "teacher@example.com",
        "preference": "conditional"
    }
)

# Then, reveal with consent
response = requests.post(
    "http://localhost:8000/api/v2/survey/identity/reveal",
    json={
        "user_email": "teacher@example.com",
        "method": "consent_based",
        "consent": True,
        "target": "principal@example.com"
    }
)

result = response.json()
if result["can_reveal"]:
    print("Identity revealed successfully")
    print(f"Method: {result['reveal_method']}")
```

### Example 3: Gradual Reveal

```python
response = requests.post(
    "http://localhost:8000/api/v2/survey/identity/reveal",
    json={
        "user_email": "teacher@example.com",
        "method": "gradual"
    }
)

result = response.json()
reveal_data = result["reveal_executed"]["reveal_data"]
print(f"Initial reveal: {reveal_data['revealed_info']}")
print(f"Next reveal date: {reveal_data.get('next_reveal_date')}")
```

## Database Schema

### survey_identity_preferences

Stores user identity preferences (global or survey-specific).

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| user_email | VARCHAR(255) | User email (FK to people) |
| survey_id | INTEGER | Survey ID (NULL = global preference) |
| identity_mode | VARCHAR(20) | anonymous, identified, conditional |
| privacy_level | VARCHAR(20) | maximum, high, medium, low |
| retention_days | INTEGER | Data retention period |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### survey_identity_reveals

Tracks identity reveals for audit and compliance.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| user_email | VARCHAR(255) | User email (FK to people) |
| survey_id | INTEGER | Survey ID (optional) |
| reveal_method | VARCHAR(50) | Reveal method used |
| revealed_info | JSONB | What information was revealed |
| target | VARCHAR(255) | Who the reveal was for |
| consent_confirmed | BOOLEAN | Consent confirmation |
| next_reveal_date | TIMESTAMP | For gradual reveals |
| created_at | TIMESTAMP | Creation timestamp |

## Implementation Details

### SurveyIdentityManager Class

The core class that manages identity preferences and reveals.

**Key Methods:**

- `set_identity_preference()`: Set user's identity mode
- `handle_identity_reveal()`: Process identity reveal requests
- `get_identity_status()`: Get current identity status
- `process_revoke_anonymity()`: Revoke anonymity and switch modes
- `verify_reveal_conditions()`: Verify reveal conditions are met
- `get_reveal_options()`: Get available reveal options
- `calculate_privacy_level()`: Calculate privacy level
- `set_retention_policy()`: Set data retention policy

### Privacy and Security

- **Row Level Security (RLS)**: Users can only access their own preferences and reveals
- **Service Role**: Full access for system operations
- **Audit Trail**: All reveals are logged for compliance
- **Consent Tracking**: Explicit consent confirmation for consent-based reveals

### Integration with Surveys

The identity system integrates with the existing survey system:

- Survey-specific preferences override global preferences
- Identity mode affects how survey responses are stored
- Reveal options are available per survey
- Gradual reveals can be scheduled per survey

## Best Practices

1. **Default to Conditional**: When no preference is set, default to conditional mode (safer than full identified)

2. **Respect User Choice**: Always respect user's identity preference and don't force reveals

3. **Clear Communication**: Inform users about privacy implications of each mode

4. **Consent Management**: Always require explicit consent for consent-based reveals

5. **Audit Logging**: Log all identity reveals for compliance and transparency

6. **Data Retention**: Automatically enforce retention policies based on identity mode

## Conditional Anonymity Engine

The Conditional Anonymity Engine extends the identity system with advanced conditional reveal scenarios.

### Features

1. **Reveal After Survey**: Automatically reveal identity after survey completion + cooling period
2. **Reveal to Specific People**: Reveal to specific recipients (HR, Principal, etc.) with partial reveal options
3. **Time-Based Reveal**: Schedule reveals based on time (e.g., 30 days after submission)
4. **Consent-Based Reveal**: Require explicit consent before revealing

### API Endpoints

#### Process Conditional Reveal

```http
POST /api/v2/survey/identity/conditional-reveal
```

**Request Body:**
```json
{
  "user_email": "user@example.com",
  "reveal_after_survey": {
    "enabled": true,
    "cooling_period_days": 7,
    "auto_reveal": false
  },
  "reveal_to_specific_people": {
    "enabled": true,
    "recipients": ["hr_manager@example.com", "principal@example.com"],
    "partial_reveal": true,
    "require_consent": true
  },
  "notify_before_reveal": true,
  "notify_after_reveal": true,
  "survey_id": 1
}
```

**Response:**
```json
{
  "reveal_conditions": {
    "valid": true,
    "errors": [],
    "warnings": [],
    "conditions": {
      "reveal_after_survey": {
        "enabled": true,
        "cooling_period_days": 7,
        "auto_reveal": false,
        "conditions": ["survey_completed", "cooling_period_passed"]
      },
      "reveal_to_specific_people": {
        "enabled": true,
        "recipients": ["hr_manager@example.com", "principal@example.com"],
        "partial_reveal": true,
        "require_consent": true
      }
    }
  },
  "trigger_events": {
    "active_triggers": [
      "survey_completed",
      "cooling_period_passed",
      "manual_request"
    ],
    "trigger_config": {
      "survey_completion": {
        "trigger": "survey_completed",
        "survey_id": 1,
        "next_trigger": "cooling_period_passed",
        "cooling_period_days": 7,
        "auto_reveal": false
      }
    }
  },
  "notification_preferences": {
    "rules": ["before_reveal", "after_reveal", "on_condition_met"],
    "preferences": {
      "before_reveal": {
        "enabled": true,
        "days_before": 1,
        "message": "Your identity will be revealed in {days} day(s)."
      }
    }
  },
  "status": "configured",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Check Trigger Conditions

```http
GET /api/v2/survey/identity/conditional-reveal/check-triggers/{user_email}?survey_id=1
```

**Response:**
```json
{
  "triggers_met": ["cooling_period_passed"],
  "actions_required": ["request_confirmation"],
  "status": "active"
}
```

#### Execute Conditional Reveal

```http
POST /api/v2/survey/identity/conditional-reveal/execute/{user_email}?trigger=cooling_period_passed&survey_id=1
```

**Response:**
```json
{
  "success": true,
  "trigger": "cooling_period_passed",
  "reveal_method": "partial",
  "recipients": ["hr_manager@example.com", "principal@example.com"],
  "results": [
    {
      "success": true,
      "recipient": "hr_manager@example.com",
      "revealed_info": {
        "role_title": "Teacher",
        "department": "Mathematics"
      },
      "partial": true
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Trigger Events

- **survey_completed**: Survey has been completed by user
- **cooling_period_passed**: Cooling period has elapsed after survey completion
- **time_based**: Time-based reveal date has been reached
- **manual_request**: User manually requests reveal
- **consent_received**: Explicit consent has been received
- **admin_approval**: Admin has approved the reveal

### Notification Rules

- **before_reveal**: Notify user before identity is revealed
- **after_reveal**: Notify user after identity has been revealed
- **on_condition_met**: Notify when a condition is met
- **reminder**: Periodic reminders about conditional reveal settings

### Cooling Periods

Default cooling periods:
- **default**: 7 days
- **sensitive**: 14 days (for sensitive surveys)
- **performance**: 30 days (for performance reviews)
- **anonymous**: 0 days (no cooling period for anonymous mode)

## Future Enhancements

- Machine learning for optimal privacy level recommendations
- Advanced consent management with granular permissions
- Integration with external identity providers
- Privacy dashboard for users
- Automated anonymization workflows
- Compliance reporting (GDPR, CCPA)
- Automated trigger monitoring and execution
- Advanced notification scheduling
