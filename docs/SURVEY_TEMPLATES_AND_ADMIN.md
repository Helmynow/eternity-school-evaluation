# Complete Survey Templates & Admin Dashboard

## Overview

The Complete Survey Template System provides comprehensive survey templates covering all aspects of school life, along with a powerful admin dashboard for system management and integration with HR and evaluation systems.

## Survey Templates

### Comprehensive School Survey

The system provides a complete school climate survey with 6+ sections:

1. **Physical Environment & Facilities**
   - Cafeteria quality
   - Classroom technology
   - Facility cleanliness
   - Parking allocation
   - Safety assessment

2. **Workplace Culture & Fairness**
   - Evaluation process fairness
   - Recognition frequency
   - Inclusion and diversity
   - Communication effectiveness
   - Collaboration quality

3. **Management & Leadership**
   - Direct manager effectiveness
   - Head of Department leadership
   - Principal communication
   - HR responsiveness
   - Decision-making transparency

4. **Inter-Departmental Collaboration**
   - Collaboration effectiveness
   - Communication quality
   - Conflict resolution

5. **Personal Wellbeing & Support**
   - Workload management
   - Support systems
   - Work-life balance
   - Stress levels

6. **School Improvement & Innovation**
   - Innovation openness
   - Priority areas
   - Improvement suggestions

### Identity-Specific Sections

- **Anonymous Mode**: Sensitive topics section (discrimination, harassment, retaliation)
- **Identified Mode**: Accountability section (action items, working groups)
- **Conditional Mode**: Future engagement section (discussion willingness, contact preferences)

## API Endpoints

### Survey Templates

#### Get Comprehensive Survey Template

```http
GET /api/v2/survey-templates/comprehensive?identity_mode=conditional
```

**Response:**
```json
{
  "survey_id": "eternity_comprehensive_20240115",
  "title": "Eternity School Complete Climate Survey",
  "description": "Comprehensive feedback about all aspects of school life",
  "estimated_time": "15-20 minutes",
  "identity_mode": "conditional",
  "sections": {
    "physical_environment": {
      "section_id": "physical_env",
      "title": "Physical Environment & Facilities",
      "questions": [...]
    },
    "workplace_culture": {...},
    "management_effectiveness": {...},
    "inter_departmental": {...},
    "personal_wellbeing": {...},
    "school_improvement": {...},
    "future_engagement": {...}
  },
  "total_questions": 35
}
```

#### Get Survey Section

```http
GET /api/v2/survey-templates/section/workplace_culture?identity_mode=anonymous
```

**Response:**
```json
{
  "section_id": "workplace_culture",
  "title": "Workplace Culture & Fairness",
  "description": "Your honest feedback about our work environment",
  "questions": [
    {
      "id": "fairness_001",
      "text": "Do you feel evaluation processes are fair and transparent?",
      "type": "rating_scale_with_explanation",
      "scale": ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
      "category": "fairness",
      "sensitivity": "medium",
      "anonymous_only": true,
      "required": true
    }
  ]
}
```

## Admin Dashboard

### Main Dashboard

```http
GET /api/v2/admin/dashboard?admin_id=admin@example.com
```

**Response:**
```json
{
  "dashboard_title": "Eternity School Survey System - Admin Dashboard",
  "last_updated": "2024-01-15T10:30:00Z",
  "overview_cards": [
    {
      "title": "Active Surveys",
      "value": 5,
      "change": "+12% from last month",
      "icon": "survey",
      "color": "blue"
    },
    {
      "title": "Response Rate",
      "value": "78.5%",
      "change": "+5% from last week",
      "icon": "responses",
      "color": "green"
    },
    {
      "title": "Bias Alerts",
      "value": 12,
      "change": "-3 from yesterday",
      "icon": "alert",
      "color": "orange"
    },
    {
      "title": "Fairness Score",
      "value": "85.5/100",
      "change": "+2 points this week",
      "icon": "fairness",
      "color": "purple"
    }
  ],
  "real_time_metrics": {
    "system_health": {
      "status": "healthy",
      "response_time": "145ms",
      "active_users": 234,
      "system_load": "normal"
    },
    "survey_activity": {
      "surveys_in_progress": 45,
      "completion_rate_last_hour": "78%",
      "most_active_time": "2:00 PM - 3:00 PM"
    },
    "identity_mode_distribution": {
      "anonymous": {"count": 156, "percentage": 45},
      "conditional": {"count": 134, "percentage": 38},
      "identified": {"count": 60, "percentage": 17}
    }
  },
  "identity_mode_analytics": {
    "honesty_analysis": {
      "anonymous": {"score": 8.7, "trend": "increasing"},
      "conditional": {"score": 7.8, "trend": "stable"},
      "identified": {"score": 6.9, "trend": "decreasing"}
    }
  },
  "action_items": [...],
  "charts_and_visualizations": {...}
}
```

### Real-Time Metrics

```http
GET /api/v2/admin/dashboard/real-time-metrics
```

### Identity Analytics

```http
GET /api/v2/admin/dashboard/identity-analytics
```

## HR & Evaluation Integration

### Setup HR Integration

```http
POST /api/v2/integration/hr/setup
```

**Request:**
```json
{
  "hr_system_url": "https://hr.eternity.edu/api",
  "api_key": "your_api_key",
  "real_time_sync": false,
  "webhook_url": "https://survey.eternity.edu/webhooks/hr",
  "ip_whitelist": ["192.168.1.0/24"]
}
```

**Response:**
```json
{
  "hr_sync": {
    "staff_sync": {
      "direction": "bidirectional",
      "frequency": "daily",
      "fields_mapped": {...}
    },
    "evaluation_sync": {...},
    "permissions_sync": {...}
  },
  "evaluation_bridge": {
    "survey_to_evaluation": {
      "anonymous_feedback": {
        "weight_in_evaluation": 0.3
      },
      "identified_feedback": {
        "weight_in_evaluation": 0.4
      }
    }
  },
  "data_flow": {...},
  "security_protocols": {...},
  "monitoring": {...}
}
```

### Evaluation Data Bridge

```http
GET /api/v2/integration/evaluation-bridge
```

**Response:**
```json
{
  "survey_to_evaluation": {
    "anonymous_feedback": {
      "processing": "aggregate_and_anonymize",
      "integration_method": "bias_adjusted_ratings",
      "weight_in_evaluation": 0.3,
      "presentation": "department_level_insights"
    },
    "identified_feedback": {
      "processing": "direct_integration_with_consent",
      "integration_method": "weighted_evaluation_scores",
      "weight_in_evaluation": 0.4
    },
    "conditional_feedback": {
      "processing": "conditional_integration",
      "integration_method": "context_aware_weighting",
      "weight_in_evaluation": 0.35
    }
  },
  "evaluation_to_survey": {
    "performance_data": {
      "usage": "survey_personalization",
      "anonymization": "role_based_anonymization"
    }
  }
}
```

### Sync Staff Data

```http
POST /api/v2/integration/sync/staff
```

**Request:**
```json
[
  {
    "employee_id": "EMP001",
    "full_name": "John Doe",
    "department_code": "MATH",
    "job_title": "Mathematics Teacher",
    "supervisor_id": "MGR001",
    "hire_date": "2020-01-15",
    "employment_status": "active"
  }
]
```

### Sync Evaluation Data

```http
POST /api/v2/integration/sync/evaluation
```

**Request:**
```json
{
  "type": "survey_completion",
  "survey_id": 1,
  "user_id": "teacher@example.com",
  "results": {...}
}
```

## System Setup

### Complete System Setup

```http
POST /api/v2/system/setup
```

**Request:**
```json
{
  "hr_sync_enabled": true,
  "hr_sync_frequency": "daily",
  "real_time_sync": false,
  "environment": "production"
}
```

**Response:**
```json
{
  "setup_complete": true,
  "configuration_summary": {
    "1. survey_templates": {"status": "configured"},
    "2. identity_system": {"status": "configured"},
    "3. admin_dashboard": {"status": "configured"},
    "4. hr_integration": {"status": "configured"},
    "5. evaluation_integration": {"status": "configured"},
    "6. monitoring_setup": {"status": "configured"},
    "7. testing_validation": {"status": "completed"},
    "8. deployment": {"status": "deployed"}
  },
  "go_live_checklist": [...],
  "training_materials": {
    "admin_guide": "/docs/admin-guide.pdf",
    "user_guide": "/docs/user-guide.pdf",
    "video_tutorials": [...]
  },
  "support_contacts": {...}
}
```

### Go-Live Checklist

```http
GET /api/v2/system/go-live-checklist
```

## Features Summary

### Survey Templates

✅ **50+ Questions** across 6+ sections  
✅ **Mode-Specific Questions** based on identity mode  
✅ **Sensitive Topics** section for anonymous mode  
✅ **Accountability** section for identified mode  
✅ **Future Engagement** section for conditional mode  
✅ **Comprehensive Coverage** of all school aspects

### Admin Dashboard

✅ **Real-Time Metrics** - System health and activity  
✅ **Overview Cards** - Key metrics at a glance  
✅ **Identity Analytics** - Mode-based analysis  
✅ **Bias Detection Summary** - Bias alerts and trends  
✅ **Action Items** - Prioritized tasks  
✅ **Charts & Visualizations** - Data visualization  
✅ **Admin Tools** - System management utilities

### HR Integration

✅ **Bidirectional Sync** - Two-way data synchronization  
✅ **Evaluation Bridge** - Survey-to-evaluation integration  
✅ **Security Protocols** - OAuth2, encryption, audit logging  
✅ **Real-Time Sync** - Optional real-time synchronization  
✅ **Error Handling** - Robust error handling and retry logic

### Evaluation Integration

✅ **Weight Mapping** - Different weights for each identity mode  
✅ **Bias Adjustment** - Bias-adjusted ratings integration  
✅ **Context-Aware Weighting** - Conditional feedback weighting  
✅ **Data Privacy** - Respects identity mode privacy levels

## Usage Examples

### Get Survey Template

```python
import requests

response = requests.get(
    "http://localhost:8000/api/v2/survey-templates/comprehensive",
    params={"identity_mode": "conditional"}
)

survey = response.json()
print(f"Survey: {survey['title']}")
print(f"Total questions: {survey['total_questions']}")
print(f"Sections: {list(survey['sections'].keys())}")
```

### Get Admin Dashboard

```python
response = requests.get(
    "http://localhost:8000/api/v2/admin/dashboard",
    params={"admin_id": "admin@example.com"}
)

dashboard = response.json()
print(f"Active surveys: {dashboard['overview_cards'][0]['value']}")
print(f"Response rate: {dashboard['overview_cards'][1]['value']}")
print(f"Bias alerts: {dashboard['overview_cards'][2]['value']}")
```

### Setup HR Integration

```python
response = requests.post(
    "http://localhost:8000/api/v2/integration/hr/setup",
    json={
        "hr_system_url": "https://hr.eternity.edu/api",
        "api_key": "your_key",
        "real_time_sync": False
    }
)

integration = response.json()
print(f"HR sync configured: {integration['hr_sync']['staff_sync']['direction']}")
```

## Best Practices

1. **Start with Conditional Mode**: Default to conditional for maximum flexibility
2. **Use Comprehensive Survey**: Use comprehensive template for full feedback
3. **Monitor Admin Dashboard**: Regularly check metrics and action items
4. **Configure HR Integration**: Set up HR sync for seamless data flow
5. **Review Bias Alerts**: Regularly review and address bias detection alerts
6. **Track Identity Analytics**: Monitor honesty and quality by identity mode

## System Capabilities

✅ **Complete Survey Templates  
✅ **Comprehensive Admin Dashboard  
✅ **HR System Integration  
✅ **Evaluation System Bridge  
✅ **Real-Time Monitoring  
✅ **Bias Detection Integration  
✅ **Identity Mode Analytics  
✅ **System Setup & Configuration
