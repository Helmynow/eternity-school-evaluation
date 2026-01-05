# Data contracts per page

This is a reliability artifact: every page documents **reads/writes, APIs, permissions, and states**.

## Admin Dashboard (`/admin/dashboard`)

- **Reads**: `cycles`, `people`, `evaluations`, `survey_*`, `hybrid_identity_sessions`, `notifications`, `objections` (via backend aggregation)
- **Writes**: none (view-only)
- **API**:
  - `GET /api/v2/admin/dashboard`
  - `GET /api/v2/admin/dashboard/overview-cards`
  - `GET /api/v2/admin/dashboard/real-time-metrics`
  - `GET /api/v2/admin/dashboard/identity-analytics`
- **Permissions**: `role:ceo|pnc` (backend enforced)
- **States**:
  - Loading: dashboard skeleton
  - Empty: show “no active data” cards
  - Error: toast + fallback copy
  - Success: cards + metrics + tabs

## System Settings (`/admin/settings`)

- **Reads**: `system_settings`
- **Writes**: `system_settings`
- **API**:
  - `GET /api/v2/admin/settings`
  - `PUT /api/v2/admin/settings`
  - `POST /api/v2/admin/settings` (idempotent create/update)
- **Permissions**: `role:ceo` (UI), **`super_admin` (backend)** — align these semantics
- **States**:
  - Loading: form skeleton
  - Empty: initial settings missing → create path
  - Error: toast + keep last values
  - Success: optimistic UI + “saved” feedback

## MRE Evaluation (`/mre/evaluate`)

- **Reads**: `cycles`, `assignments`, `people`
- **Writes**: `evaluations`, `audit_logs`
- **API**:
  - `GET /api/v2/cycles/current`
  - `GET /api/v2/mre/assignments/{cycle_id}`
  - `POST /api/v2/mre/evaluations/process`
- **Permissions**: `auth:required` (submission scoped to authenticated rater)
- **States**:
  - Loading: cycle + assignment list
  - Empty: “no active cycle” / “no pending evaluations”
  - Error: toast; keep UI usable
  - Success: pending/completed lists + evaluation form

## EOM Nomination (`/eom/nominate`)

- **Reads**: `cycles`, `people`, `eom_*`, `eom_rotation_rules`
- **Writes**: `eom_nominees`, `eom_voters` (vote), `eom_feedback`, `audit_logs`, `objections`
- **API** (core):
  - `GET /api/v2/cycles/current`
  - `POST /api/v2/eom/nominations/validate`
  - `POST /api/v2/eom/nominations/submit`
  - `POST /api/v2/eom/vote`
  - `POST /api/v2/objections`
- **Permissions**: `role:ceo|pnc|department_head` (backend enforced)
- **States**:
  - Loading: cycle + eligibility fetch
  - Empty: “window closed” / “no eligible nominees”
  - Error: toast; allow retry
  - Success: submit nomination + vote flows

