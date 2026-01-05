# Audit artifacts

This folder contains **traceability** artifacts that tie UI routes → frontend controls → backend handlers → database entities → permissions/audit/tests.

These files are intended to be **versioned with the code** and kept up to date.

## Regenerate

From the repo root:

```bash
python3 scripts/generate_ui_map.py --repo-root .
python3 scripts/generate_db_rls_map.py --repo-root .
```

## CI enforcement

CI runs a lightweight check to ensure admin routes are mapped to a `permission_key` and that every `api_path` resolves to a `backend_ref`:

```bash
python3 scripts/check_traceability.py --repo-root .
```

## Key files

- `ui_routes.csv`: routes discovered from `frontend/src/App.jsx`
- `ui_route_api.csv`: best-effort mapping of route → API calls (static scan)
- `ui_mapping_matrix.csv`: the living traceability matrix (manual columns are preserved across regeneration)
- `ui-map.puml`: PlantUML route graph
- `db_tables.csv`, `db_policies.csv`, `db_views.csv`, `db_rls_report.md`: schema/RLS scan (from migrations)
- `policies_map.md`: human-curated route/control → permission overlay
- `data_contracts.md`: per-page data contracts (reads/writes + states)
- `audit_report.md`: prioritized findings and remediation plan

