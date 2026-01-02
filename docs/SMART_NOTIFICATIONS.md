# Smart Notification System

## Overview

The Smart Notification System provides intelligent, behavior-based reminders and escalation alerts for the Eternity School Evaluation System. It learns from user behavior patterns to send reminders at optimal times and automatically escalates overdue evaluations.

## Features

### 1. Smart Reminders Based on User Behavior

The system analyzes each user's historical completion patterns to determine the best time to send reminders.

**How it works:**
- Tracks when users typically complete evaluations (hour of day)
- Calculates average completion time (days from assignment to submission)
- Identifies completion patterns: "early", "on_time", or "late"
- Determines optimal reminder time (2 hours before most common completion hour)

**Example:**
```python
# Get user behavior profile
GET /api/v2/notifications/user-behavior/{user_email}

# Response:
{
    "preferred_completion_hours": [9, 10, 14, 15],
    "average_completion_time": 5.2,
    "completion_pattern": "on_time",
    "best_reminder_time": 8,
    "confidence": "high"
}
```

**Send smart reminders:**
```python
POST /api/v2/notifications/smart-reminder/{cycle_id}?user_email={email}

# Only sends if current time is optimal for the user
```

### 2. Smart Notifications Based on User Preferences

Users can customize notification preferences:
- **Enable/disable** specific notification types
- **Set frequency limits**: immediate, daily, weekly
- **Configure quiet hours**: No notifications during specified hours
- **Automatic spam prevention**: Prevents duplicate notifications

**Default Preferences:**
- Bias alerts: Immediate, quiet hours 10 PM - 8 AM
- Deadline reminders: Daily, quiet hours 10 PM - 8 AM
- EOM winner announcements: Immediate, no quiet hours
- Evaluation submissions: Disabled by default

### 3. Escalation Alerts for Overdue Evaluations

Automatically detects and escalates overdue evaluations with increasing urgency.

**Escalation Levels:**
1. **Overdue Alert** (1-6 days overdue):
   - Sent to rater
   - Priority: High
   - Subject: "⚠️ Evaluation Overdue"

2. **Escalation Alert** (7+ days overdue):
   - Sent to rater (URGENT priority)
   - Also sent to manager/department head
   - Subject: "🚨 URGENT: Evaluation Overdue - Escalation"

**API Endpoint:**
```python
POST /api/v2/notifications/check-overdue/{cycle_id}?escalation_days=7

# Response:
{
    "overdue_count": 5,
    "escalation_count": 2,
    "alerts_sent": [
        {
            "assignment_id": 123,
            "rater_email": "teacher@example.com",
            "alert_type": "escalation",
            "result": {...}
        }
    ]
}
```

### 4. Due Soon Reminders

Sends reminders for evaluations due soon, using smart timing based on user behavior.

**API Endpoint:**
```python
POST /api/v2/notifications/due-soon-reminders/{cycle_id}?days_before=3

# Only sends if:
# - Within days_before of deadline
# - Current time is optimal for user (based on behavior profile)
```

## Notification Types

### New Notification Types Added:

1. **`evaluation_overdue`**: Sent when evaluation is overdue
   - Template: "⚠️ URGENT: Evaluation for {target_name} is overdue by {days_overdue} day(s). Please complete immediately."

2. **`evaluation_overdue_escalation`**: Sent when evaluation is severely overdue
   - Template: "🚨 ESCALATION: Evaluation for {target_name} is {days_overdue} days overdue. Manager notified."

3. **`smart_reminder`**: Behavior-based reminder
   - Template: "Reminder: You have {pending_count} pending evaluation(s). Based on your typical completion time, now is a good time to complete them."

4. **`evaluation_due_soon`**: Pre-deadline reminder
   - Template: "Evaluation for {target_name} is due in {days_remaining} day(s). Complete it at your convenience."

## Implementation Details

### User Behavior Analysis

The system analyzes the last 20 completed evaluations to build a behavior profile:

```python
def get_user_behavior_profile(user_email: str) -> Dict:
    # Analyzes:
    # - Completion hours (most common times)
    # - Average completion delay
    # - Completion pattern (early/on_time/late)
    # - Optimal reminder time
```

### Smart Reminder Logic

```python
def send_smart_reminder(user_email, pending_evaluations, cycle_id):
    # 1. Get user behavior profile
    behavior = get_user_behavior_profile(user_email)
    
    # 2. Check if current time is optimal
    current_hour = datetime.utcnow().hour
    is_optimal = (
        current_hour in behavior["preferred_completion_hours"] or
        current_hour == behavior["best_reminder_time"]
    )
    
    # 3. Only send if optimal time
    if is_optimal:
        send_notification(...)
```

### Escalation Logic

```python
def check_overdue_evaluations(cycle_id, escalation_days=7):
    # 1. Find all pending assignments past deadline
    # 2. Calculate days overdue
    # 3. Send overdue alerts (< escalation_days)
    # 4. Send escalation alerts (>= escalation_days)
    # 5. Notify managers for escalated items
```

## Usage Examples

### 1. Get User Behavior Profile

```python
import requests

response = requests.get(
    "http://localhost:8000/api/v2/notifications/user-behavior/teacher@example.com"
)
profile = response.json()

print(f"Best reminder time: {profile['best_reminder_time']}:00")
print(f"Completion pattern: {profile['completion_pattern']}")
```

### 2. Send Smart Reminders

```python
# Send smart reminders for all users in a cycle
response = requests.post(
    "http://localhost:8000/api/v2/notifications/smart-reminder/1"
)
result = response.json()

print(f"Reminders sent: {result['reminders_sent']}")
print(f"Reminders skipped: {result['reminders_skipped']}")
```

### 3. Check Overdue Evaluations

```python
# Check and send escalation alerts
response = requests.post(
    "http://localhost:8000/api/v2/notifications/check-overdue/1?escalation_days=7"
)
result = response.json()

print(f"Overdue: {result['overdue_count']}")
print(f"Escalated: {result['escalation_count']}")
```

### 4. Send Due Soon Reminders

```python
# Send reminders 3 days before deadline
response = requests.post(
    "http://localhost:8000/api/v2/notifications/due-soon-reminders/1?days_before=3"
)
result = response.json()

print(f"Reminders sent: {result['reminders_sent']}")
```

## Scheduled Tasks

For production use, set up scheduled tasks to run:

1. **Daily Smart Reminders** (e.g., 8 AM):
   ```python
   POST /api/v2/notifications/smart-reminder/{active_cycle_id}
   ```

2. **Daily Overdue Check** (e.g., 9 AM):
   ```python
   POST /api/v2/notifications/check-overdue/{active_cycle_id}
   ```

3. **Due Soon Reminders** (e.g., 10 AM, 3 days before deadline):
   ```python
   POST /api/v2/notifications/due-soon-reminders/{active_cycle_id}?days_before=3
   ```

## Benefits

1. **Reduced Notification Fatigue**: Only sends reminders at optimal times
2. **Improved Completion Rates**: Behavior-based timing increases response rates
3. **Automatic Escalation**: Ensures overdue items are addressed
4. **Personalized Experience**: Adapts to each user's work patterns
5. **Manager Visibility**: Escalations keep managers informed

## Future Enhancements

- Machine learning to predict completion likelihood
- A/B testing for reminder timing optimization
- Integration with calendar systems for scheduling
- Mobile push notifications
- In-app notification center
- Notification analytics dashboard
