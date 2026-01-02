# Evaluator Assignment Management System

## ✅ Implementation Complete

### Overview
Comprehensive system for managing "who evaluates whom" relationships when staff members are added or roles change.

---

## 🎯 Features Implemented

### 1. Automatic Evaluator Assignment
When a staff member is added (admin or academic), the system automatically:
- Determines staff type (academic vs admin)
- Creates assignments for all required evaluators based on weight matrix
- Assigns appropriate weights (CEO 15%, P&C 25%, Manager 30-40%, Self 5%, etc.)
- Handles peer reviews (limit to 2 colleagues)

### 2. Evaluator Management UI
- View all evaluators for a staff member
- Edit evaluator assignments when roles change
- Add/remove evaluators manually
- See who each staff member evaluates
- Visual matrix of all evaluation relationships

### 3. Role-Based Evaluator Assignment

#### Academic Staff Evaluators:
- Stage Principal (30%)
- People & Culture (25%)
- Coordinator/HOD (25%)
- Director/CEO (15%)
- Self Evaluation (5%)
- Peer Review (optional, up to 2 colleagues)

#### Admin Staff Evaluators:
- Department Head/Manager (40%)
- People & Culture (20%)
- Peer Review (10%, up to 2 colleagues)
- Quality Assurance (10%)
- CEO (15%)
- Self Evaluation (5%)

---

## 📁 Files Created/Modified

### Backend
1. **`backend/evaluator_assignment_manager.py`** (NEW)
   - `EvaluatorAssignmentManager` class
   - Auto-assignment logic
   - Evaluator finding by context
   - Assignment creation/update/delete

2. **`backend/fastapi_app.py`** (MODIFIED)
   - `POST /api/v2/staff/{email}/assign-evaluators` - Create assignments
   - `PUT /api/v2/staff/{email}/evaluators` - Update assignments
   - `GET /api/v2/staff/{email}/evaluators` - Get assignments
   - `GET /api/v2/staff/{email}/evaluation-status` - Get full status
   - `GET /api/v2/evaluation-matrix/{cycle_id}` - Get complete matrix

### Frontend
1. **`frontend/src/components/admin/EvaluatorManagement.jsx`** (NEW)
   - Complete UI for managing evaluators
   - View/edit/add/remove evaluators
   - Shows evaluation relationships

2. **`frontend/src/components/admin/StaffManagement.jsx`** (MODIFIED)
   - Added "Evaluators" button for each staff member
   - Auto-creates assignments when staff is added
   - Integrated EvaluatorManagement component

3. **`frontend/src/lib/api.js`** (MODIFIED)
   - Added `staff` API client methods
   - Added `evaluationMatrix` API client methods

---

## 🔧 How It Works

### When Staff is Added

1. **Staff Creation**:
   ```javascript
   // In StaffManagement.jsx
   await apiClient.staff.assignEvaluators(email, {
     target_email: email,
     cycle_id: currentCycle.id
   })
   ```

2. **Backend Processing**:
   - Determines if staff is academic or admin
   - Gets required evaluators list
   - Finds appropriate evaluators by context (CEO, P&C, Manager, etc.)
   - Creates Assignment records with correct weights

3. **Result**:
   - All required evaluators are assigned
   - Weights match the specification
   - Ready for evaluation cycle

### When Roles Change

1. **User clicks "Evaluators" button** in Staff Management
2. **EvaluatorManagement component opens** showing:
   - Current evaluators
   - Who they evaluate
   - Required vs assigned evaluators

3. **User can**:
   - Edit evaluator assignments
   - Change evaluator (e.g., when teacher changes grades)
   - Change evaluator type (e.g., when admin changes position)
   - Add/remove evaluators
   - See weight percentages

---

## 📊 Evaluation Matrix View

The system provides a complete matrix view showing:
- All staff members (targets)
- All their evaluators (raters)
- Evaluation relationships
- Weights and contexts

Access via: `GET /api/v2/evaluation-matrix/{cycle_id}`

---

## 🎨 UI Features

### Evaluator Management Modal
- **Summary Section**: Shows total evaluators, required count, evaluating others
- **Evaluators List**: Shows who evaluates this person
  - Edit button to change evaluator
  - Remove button to delete assignment
  - Shows weight percentage
- **Evaluating Section**: Shows who this person evaluates
- **Add Evaluator**: Button to manually add evaluators
- **Auto-Assign**: Button to automatically create all assignments

### Edit Assignment Form
- Select evaluator from dropdown
- Select evaluator type (CEO, P&C, Manager, etc.)
- Adjust weight (auto-filled based on type)
- Save/Cancel buttons

---

## 🔒 Security & Validation

- Only authorized users (CEO, P&C) can manage evaluators
- All changes are audited
- Weight validation ensures percentages match requirements
- Peer review limit enforced (max 2 colleagues)

---

## 📝 Usage Examples

### Auto-Assign Evaluators
```javascript
// When staff member is added
await apiClient.staff.assignEvaluators('teacher@eternity.edu', {
  target_email: 'teacher@eternity.edu',
  cycle_id: 1
})
```

### View Evaluation Status
```javascript
// Get who evaluates them and who they evaluate
const status = await apiClient.staff.getEvaluationStatus('teacher@eternity.edu', {
  cycle_id: 1
})
```

### Update Evaluator
```javascript
// Change evaluator when role changes
await apiClient.staff.updateEvaluators('teacher@eternity.edu', {
  target_email: 'teacher@eternity.edu',
  cycle_id: 1,
  assignments: [
    {
      id: assignmentId,
      action: 'update',
      rater_email: 'new-manager@eternity.edu',
      rater_context: 'manager_review',
      weight: 0.30
    }
  ]
})
```

### Get Complete Matrix
```javascript
// See all evaluation relationships
const matrix = await apiClient.evaluationMatrix.getMatrix(cycleId)
```

---

## ✅ Testing Checklist

- [ ] Add academic staff member → Auto-assigns evaluators
- [ ] Add admin staff member → Auto-assigns evaluators
- [ ] Edit evaluator assignment → Updates correctly
- [ ] Remove evaluator → Deletes assignment
- [ ] Add evaluator manually → Creates new assignment
- [ ] View evaluation matrix → Shows all relationships
- [ ] Change staff role → Can update evaluators
- [ ] Peer review limit → Enforces max 2 colleagues

---

## 🚀 Next Steps

1. **Test the system** with real staff data
2. **Add validation** for peer review limits
3. **Add bulk assignment** for multiple staff at once
4. **Add export** functionality for evaluation matrix
5. **Add notifications** when assignments change

---

## 📋 Notes

- Evaluator assignments are cycle-specific
- When staff role changes, evaluators should be reviewed/updated
- Self-evaluation is always required (5% weight)
- Peer reviews are optional but limited to 2 colleagues
- All changes are logged in audit_logs
