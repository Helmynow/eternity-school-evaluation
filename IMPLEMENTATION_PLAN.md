# Implementation Plan - Feature Enhancements

## Priority 1: Super Admin & RBAC System

### 1.1 Super Admin for ahelmy@eternityschoolegypt.com
- Create `UserPermission` model for time-based permissions
- Add `grant_permission()` and `revoke_permission()` endpoints
- Super admin can manage all user roles and permissions
- No time limits (unlimited permissions)

### 1.2 Backend RBAC Enforcement
- Add permission decorators to all endpoints
- Check permissions before allowing actions
- Log all permission changes in audit log

## Priority 2: Evaluation Weight Enforcement

### 2.1 Weight Validation
- Enforce CEO: 15%, P&C: 25%, Manager: 30-40%, Self: 5%
- Validate peer limits ("2 colleagues" rule)
- Add validation in `weight_matrix_handler.py` and `academic_admin_scoring.py`

## Priority 3: EOM Categories Update

### 3.1 Category Mapping
Current → Desired:
- OUTSTANDING_LEADERSHIP → Leadership
- TEAM_SPIRIT → Teamwork  
- INNOVATION → Innovation (keep)
- RISING_STAR → Excellence in Teaching
- SERVICE_EXCELLENCE → (merge into others or keep)

## Priority 4: MRE Anonymous Peer Reviews

### 4.1 Anonymity for MRE
- Extend `hybrid_identity_system.py` to support MRE evaluations
- Add anonymous peer review option in MRE evaluation flow
- Ensure anonymity is enforced at database level

## Priority 5: Scheduler-Based Automation

### 5.1 Notification Scheduler
- Add APScheduler or Celery for task scheduling
- Wire up email templates from `email_service.py`
- Schedule notifications from `smart_notification_system.py`
- Add cron-like scheduling for recurring tasks

## Priority 6: Results Center

### 6.1 Complete Results Center
- Enhance `AdminDashboard.jsx` and `Reports.jsx`
- Add all CEO export endpoints
- Create comprehensive results visualization

## Priority 7: Tech Stack Updates

### 7.1 Frontend Tech Stack
- Add TypeScript support
- Integrate shadcn/ui components
- Add framer-motion for animations
- Replace toast with sonner

---

## Implementation Order

1. ✅ Super Admin & RBAC (Critical for security)
2. ✅ Weight Enforcement (Core functionality)
3. ✅ EOM Categories (Data consistency)
4. ⏳ MRE Anonymity (Feature enhancement)
5. ⏳ Scheduler (Automation)
6. ⏳ Results Center (UI completion)
7. ⏳ Tech Stack (Modernization)
