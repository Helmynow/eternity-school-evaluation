# End-to-end system audit (UI ↔ API ↔ DB ↔ permissions)

Generated/updated: 2026-01-03

## Stack snapshot

- **Frontend**: Vite + React 18 + React Router + Tailwind; Supabase Auth session used to obtain JWT.
- **Backend**: FastAPI (`backend/fastapi_app.py`) with JWT middleware + optional API key; RBAC via `backend/rbac_system.py`.
- **Database**: Postgres (Supabase). Migrations live in `supabase/migrations/`.
- **CI**: GitHub Actions for Python lint/tests.

## Traceability artifacts

- UI route inventory + route→API map: `audit_artifacts/ui_routes.csv`, `audit_artifacts/ui_route_api.csv`
- Traceability matrix (living): `audit_artifacts/ui_mapping_matrix.csv`
- DB/RLS scan: `audit_artifacts/db_rls_report.md` + CSV exports
- PlantUML route diagram: `audit_artifacts/ui-map.puml`

## Findings (prioritized)

### P0 — Password recovery redirect hardening (fixed)

- **Issue**: Password recovery redirect was derived from the request `Host` header, which can be abused via Host header injection to send users reset links pointing at attacker-controlled domains.
- **Fix applied**: In production, redirect origin is now derived from `ALLOWED_ORIGINS` only (and errors if missing).
- **Files**: `backend/fastapi_app.py`

### P0 — RBAC role inference over-privileged “director” titles (fixed)

- **Issue**: `RBACSystem.get_user_role()` treated any `role_title` containing “director” as `ceo`.
- **Fix applied**: CEO inference now requires explicit “CEO”/“Chief Executive”; HR/P&C titles map to `pnc`; department leadership titles map to `department_head`.
- **Files**: `backend/rbac_system.py`, `tests/test_rbac_system_role_inference.py`

### P0 — SQLAlchemy enum binding mismatched Supabase enums (fixed)

- **Issue**: Supabase enums use lowercase values (e.g. `staff_segment`: `national`, `action_type`: `create`). SQLAlchemy was persisting enum **names** (e.g. `NATIONAL`, `CREATE`), causing runtime write failures.
- **Fix applied**: Added `pg_enum()` helper and migrated relevant model columns to persist enum **values** for:
  - `staff_segment`, `action_type`, `eom_category`, `permission_type`, `rotation_period_type`
- **Files**: `backend/database.py`, `backend/rbac_system.py`

### P0 — MRE assignments route mismatch (fixed)

- **Issue**: Frontend calls `GET /api/v2/mre/assignments/{cycleId}` but backend did not implement it.
- **Fix applied**: Added `GET /api/v2/mre/assignments/{cycle_id}` returning assignments for the authenticated rater.
- **Files**: `backend/fastapi_app.py`

### P0 — MRE evaluation submission authorization gap (fixed)

- **Issue**: `POST /api/v2/mre/evaluations/process` accepted an `assignment_id` without verifying the caller is the assignment’s `rater_email`.
- **Fix applied**: Enforced “caller email must match `Assignment.rater_email`” (super admin bypass only).
- **Files**: `backend/fastapi_app.py`

### P1 — Role trust model mismatch (UI vs backend)

- Frontend derives role from `user_metadata.role` and heuristic email matching (`frontend/src/lib/supabase.js`), which **must not** be treated as authoritative for permissions.
- Backend uses DB-backed RBAC (`RBACSystem`) and already enforces admin/EOM access in multiple endpoints.
- **Action**:
  - Treat UI role as *display only*.
  - Ensure all sensitive endpoints use `_require_authenticated_email` + RBAC checks (or per-user scoping).
  - Consider removing role inference from `user_metadata` or switching to `app_metadata` + server-controlled role assignment.

### P1 — Supabase RLS posture

From `audit_artifacts/db_rls_report.md`:
- ✅ All public tables detected have RLS enabled (based on migrations).
- ⚠️ `public.ai_feedback` has RLS enabled but **zero policies** (default deny unless bypass role).
- **Action**: confirm `ai_feedback` is backend-only; otherwise add explicit policies.

### P2 — Route-level admin guards are not centralized

- `frontend/src/App.jsx` only gates on “logged in”.
- Each admin page separately renders “Access Denied” UI.
- **Action**: add a shared `<ProtectedRoute requiredRole=...>` (or similar) to reduce accidental exposure + improve UX consistency.

## Recommended next steps

1. **Harden the role source of truth**: move to DB-backed roles only; prevent users from self-assigning privileged roles via metadata.
2. **Audit write endpoints** for per-user scoping (pattern: verify `request.state.user_email` matches target entity owner).
3. **Add audit events** for sensitive writes in `ui_mapping_matrix.csv` (admin settings updates, imports, permissions grants).
4. **Keep the matrix current**: run generators + CI check on every PR.
