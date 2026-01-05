# Permissions + RLS overlay

This file is the human-readable overlay that answers: **“What is allowed where, and where is it enforced?”**

For raw exports of tables/policies/views, see:
- `audit_artifacts/db_tables.csv`
- `audit_artifacts/db_policies.csv`
- `audit_artifacts/db_views.csv`

## Route-level gates

| route | action | permission key | enforcement (UI/BE/DB) | notes |
|---|---|---|---|---|
| `/` | View dashboard | `auth:required` | UI (router), BE (JWT middleware) | Default app shell requires authenticated session. |
| `/mre/evaluate` | Submit evaluation | `auth:required` | UI, BE, DB | Backend now enforces “only submit for your own assignment”. |
| `/eom/*` | Nominate / vote / feedback | `role:ceo\|pnc\|department_head` | UI (useAuth), BE (`_require_eom_access`) | UI role must not be trusted for authorization. Backend is authoritative. |
| `/admin/*` | Admin operations | `role:ceo\|pnc` | UI (components), BE (`_require_admin_access`) | Router currently does not guard by role; each admin screen checks locally. |
| `/admin/settings` | Global settings | `role:ceo` | UI (component), BE (`_require_super_admin`) | Backend currently requires **super admin**; UI says CEO. Align role model. |
| `/admin/integration` | Integration setup/sync | `role:ceo` | UI (component), BE (RBAC) | Verify each integration endpoint checks admin role. |

## Data access (tables/views/RPC)

| entity | access | allowed roles | RLS policy names | risk | notes |
|---|---|---|---|---|---|
| `public.assignments` | Read own-as-rater | `authenticated` (scoped) | many (see `db_policies.csv`) | **High** | Backend reads directly; ensure all read APIs scope by authenticated user. |
| `public.evaluations` | Insert for own assignments | `authenticated` (scoped) | many | **High** | Backend enforces rater match on submission. Consider unique constraint to prevent duplicates. |
| `public.user_permissions` | Read own role/permissions | `authenticated` (scoped) | present | **High** | Must be the authoritative source of roles; do not accept role from `user_metadata`. |
| `public.system_settings` | Read/write | `super_admin` | present | **High** | Sensitive settings; restrict strictly, audit changes. |
| `public.audit_logs` | Read (admin) / write | `admin` | present | **High** | Ensure non-admin users cannot browse audit trail. |
| `public.ai_feedback` | (unknown) | (unknown) | **none detected** | **Medium** | RLS enabled with zero policies; confirm backend-only usage or add explicit deny/allow policies. |

