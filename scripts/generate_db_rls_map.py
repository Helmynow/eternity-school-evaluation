#!/usr/bin/env python3
"""
Generate a DB schema/RLS overview by scanning SQL migrations (best-effort).

This script intentionally avoids needing DB credentials and does not execute SQL.

Outputs (default under ./audit_artifacts):
- db_tables.csv: tables discovered in migrations
- db_policies.csv: RLS policies discovered in migrations
- db_views.csv: views discovered in migrations (flags security_invoker/definer where detectable)
- db_rls_report.md: human-readable summary with actionable warnings
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


@dataclass(frozen=True)
class TableDef:
    schema: str
    name: str
    file: str
    line: int


@dataclass(frozen=True)
class PolicyDef:
    schema: str
    table: str
    name: str
    command: str
    roles: str
    file: str
    line: int


@dataclass(frozen=True)
class ViewDef:
    schema: str
    name: str
    security: str  # unknown|definer|invoker
    file: str
    line: int


CREATE_TABLE = re.compile(
    r"""create\s+table\s+(if\s+not\s+exists\s+)?(?:(?P<schema>[a-zA-Z_][\w]*)\.)?(?P<table>[a-zA-Z_][\w]*)""",
    re.IGNORECASE,
)
ALTER_TABLE_ENABLE_RLS = re.compile(
    r"""alter\s+table\s+(if\s+exists\s+)?(?:(?P<schema>[a-zA-Z_][\w]*)\.)?(?P<table>[a-zA-Z_][\w]*)\s+enable\s+row\s+level\s+security""",
    re.IGNORECASE,
)
CREATE_POLICY = re.compile(
    r"""create\s+policy\s+(?P<name>"[^"]+"|[a-zA-Z_][\w]*)\s+on\s+(?:(?P<schema>[a-zA-Z_][\w]*)\.)?(?P<table>[a-zA-Z_][\w]*)""",
    re.IGNORECASE,
)
POLICY_FOR = re.compile(r"""\bfor\s+(select|insert|update|delete)\b""", re.IGNORECASE)
POLICY_TO = re.compile(r"""\bto\s+([^;]+?)(?:\s+using|\s+with\s+check|;|$)""", re.IGNORECASE)

CREATE_VIEW = re.compile(
    r"""create\s+(or\s+replace\s+)?view\s+(?:(?P<schema>[a-zA-Z_][\w]*)\.)?(?P<view>[a-zA-Z_][\w]*)""",
    re.IGNORECASE,
)
ALTER_VIEW = re.compile(
    r"""alter\s+view\s+(if\s+exists\s+)?(?:(?P<schema>[a-zA-Z_][\w]*)\.)?(?P<view>[a-zA-Z_][\w]*)""",
    re.IGNORECASE,
)
SECURITY_DEFINER = re.compile(r"""\bsecurity\s+definer\b""", re.IGNORECASE)
SECURITY_INVOKER = re.compile(r"""\bsecurity\s+invoker\b""", re.IGNORECASE)
SECURITY_INVOKER_SETTING = re.compile(r"""\bsecurity_invoker\s*=\s*true\b""", re.IGNORECASE)

STATEMENT_START = re.compile(
    r"""^\s*(create\s+table|create\s+policy|create\s+(or\s+replace\s+)?view|alter\s+table|alter\s+view)\b""",
    re.IGNORECASE,
)


def iter_sql_files(root: Path) -> List[Path]:
    if not root.exists():
        return []
    return sorted(root.glob("**/*.sql"))


def _read_lines(path: Path) -> List[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []


def _norm_ident(ident: Optional[str]) -> str:
    if not ident:
        return ""
    return ident.strip().strip('"')


def _normalize_sql(stmt: str) -> str:
    # Collapse whitespace/newlines for regex parsing
    return " ".join(stmt.split())


def iter_statements(lines: Sequence[str]) -> Iterable[Tuple[int, str]]:
    """
    Yield (start_line, statement_text) for likely DDL statements.

    We only accumulate statements that start with a DDL keyword and end at the next semicolon.
    This catches multi-line CREATE POLICY statements found in DO $$ blocks.
    """

    in_stmt = False
    stmt_start_line = 0
    buf: List[str] = []

    for idx, line in enumerate(lines, start=1):
        if not in_stmt:
            if not STATEMENT_START.search(line):
                continue
            in_stmt = True
            stmt_start_line = idx
            buf = [line]
            if ";" in line:
                yield stmt_start_line, "\n".join(buf)
                in_stmt = False
                buf = []
            continue

        buf.append(line)
        if ";" in line:
            yield stmt_start_line, "\n".join(buf)
            in_stmt = False
            buf = []


def scan_migrations(repo_root: Path, migration_dirs: Sequence[Path]) -> Tuple[List[TableDef], Set[Tuple[str, str]], List[PolicyDef], List[ViewDef]]:
    tables: List[TableDef] = []
    rls_enabled: Set[Tuple[str, str]] = set()
    policies: List[PolicyDef] = []
    views_by_name: Dict[Tuple[str, str], ViewDef] = {}

    for migrations_dir in migration_dirs:
        for sql_file in iter_sql_files(migrations_dir):
            rel = str(sql_file.relative_to(repo_root))
            lines = _read_lines(sql_file)

            for start_line, stmt in iter_statements(lines):
                normalized = _normalize_sql(stmt)

                m_table = CREATE_TABLE.search(normalized)
                if m_table:
                    schema = _norm_ident(m_table.group("schema")) or "public"
                    table = _norm_ident(m_table.group("table"))
                    tables.append(TableDef(schema=schema, name=table, file=rel, line=start_line))

                m_rls = ALTER_TABLE_ENABLE_RLS.search(normalized)
                if m_rls:
                    schema = _norm_ident(m_rls.group("schema")) or "public"
                    table = _norm_ident(m_rls.group("table"))
                    rls_enabled.add((schema, table))

                m_policy = CREATE_POLICY.search(normalized)
                if m_policy:
                    name = _norm_ident(m_policy.group("name"))
                    schema = _norm_ident(m_policy.group("schema")) or "public"
                    table = _norm_ident(m_policy.group("table"))
                    cmd_match = POLICY_FOR.search(normalized)
                    cmd = (cmd_match.group(1).upper() if cmd_match else "ALL").upper()
                    to_match = POLICY_TO.search(normalized)
                    roles = (to_match.group(1).strip() if to_match else "PUBLIC") or "PUBLIC"
                    policies.append(
                        PolicyDef(
                            schema=schema,
                            table=table,
                            name=name,
                            command=cmd,
                            roles=roles,
                            file=rel,
                            line=start_line,
                        )
                    )

                m_view = CREATE_VIEW.search(normalized)
                if m_view:
                    schema = _norm_ident(m_view.group("schema")) or "public"
                    view = _norm_ident(m_view.group("view"))
                    security = "unknown"
                    if SECURITY_DEFINER.search(normalized):
                        security = "definer"
                    if SECURITY_INVOKER.search(normalized):
                        security = "invoker"
                    views_by_name[(schema, view)] = ViewDef(schema=schema, name=view, security=security, file=rel, line=start_line)

                m_alter_view = ALTER_VIEW.search(normalized)
                if m_alter_view:
                    schema = _norm_ident(m_alter_view.group("schema")) or "public"
                    view = _norm_ident(m_alter_view.group("view"))
                    existing = views_by_name.get((schema, view))
                    security = existing.security if existing else "unknown"
                    if SECURITY_INVOKER_SETTING.search(normalized):
                        security = "invoker"
                    views_by_name[(schema, view)] = ViewDef(
                        schema=schema,
                        name=view,
                        security=security,
                        file=existing.file if existing else rel,
                        line=existing.line if existing else start_line,
                    )

    return tables, rls_enabled, policies, sorted(views_by_name.values(), key=lambda v: (v.schema, v.name))


def write_csv(path: Path, headers: Sequence[str], rows: Iterable[Sequence[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(list(headers))
        for row in rows:
            writer.writerow(list(row))


def write_report(
    path: Path,
    *,
    tables: List[TableDef],
    rls_enabled: Set[Tuple[str, str]],
    policies: List[PolicyDef],
    views: List[ViewDef],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    policy_count: Dict[Tuple[str, str], int] = {}
    for p in policies:
        key = (p.schema, p.table)
        policy_count[key] = policy_count.get(key, 0) + 1

    unique_tables = {(t.schema, t.name) for t in tables}
    public_tables = sorted([t for t in unique_tables if t[0] == "public"])

    missing_rls = [t for t in public_tables if t not in rls_enabled]
    tables_no_policies = [t for t in public_tables if policy_count.get(t, 0) == 0]

    lines: List[str] = []
    lines.append("# DB / RLS Audit (migration scan)")
    lines.append("")
    lines.append("This report is generated by scanning SQL migrations. It does **not** execute SQL.")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Tables found: {len(unique_tables)}")
    lines.append(f"- Policies found: {len(policies)}")
    lines.append(f"- Views found: {len(views)}")
    lines.append("")
    lines.append("## High-signal checks")
    if missing_rls:
        lines.append("### Public tables missing RLS (potential exposure)")
        for schema, table in missing_rls:
            lines.append(f"- `{schema}.{table}` (policies: {policy_count.get((schema, table), 0)})")
        lines.append("")
        lines.append("Action: enable RLS + add explicit policies for each role/action.")
        lines.append("")
    else:
        lines.append("- ✅ No public tables detected without RLS (based on migrations).")
        lines.append("")

    if tables_no_policies:
        lines.append("### Public tables with RLS enabled but zero policies (default deny unless bypass)")
        for schema, table in tables_no_policies:
            lines.append(f"- `{schema}.{table}`")
        lines.append("")
        lines.append("Action: confirm this is intentional. For client access, add explicit SELECT policies at minimum.")
        lines.append("")
    else:
        lines.append("- ✅ No public tables detected with zero RLS policies.")
        lines.append("")

    definer_views = [v for v in views if v.security == "definer"]
    if definer_views:
        lines.append("### Views detected as SECURITY DEFINER (risk: privilege escalation)")
        for v in definer_views:
            lines.append(f"- `{v.schema}.{v.name}` ({v.file}:{v.line})")
        lines.append("")
        lines.append("Action: prefer SECURITY INVOKER views + explicit RLS policies on underlying tables.")
        lines.append("")
    else:
        lines.append("- ✅ No SECURITY DEFINER views detected (based on migrations).")
        lines.append("")

    lines.append("## Tables")
    for schema, table in sorted(public_tables):
        rls = "enabled" if (schema, table) in rls_enabled else "NOT enabled"
        lines.append(f"- `{schema}.{table}` — RLS: {rls}; policies: {policy_count.get((schema, table), 0)}")
    lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate DB/RLS maps by scanning SQL migrations")
    parser.add_argument("--repo-root", default=".", help="Path to repository root")
    parser.add_argument("--out-dir", default="audit_artifacts", help="Output directory (relative to repo root)")
    parser.add_argument(
        "--migrations-dir",
        action="append",
        default=[],
        help="Migration directory to scan (can be passed multiple times). Defaults to supabase/migrations.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_dir = (repo_root / args.out_dir).resolve()

    if args.migrations_dir:
        migration_dirs = [Path(p).resolve() if Path(p).is_absolute() else (repo_root / p).resolve() for p in args.migrations_dir]
    else:
        migration_dirs = [(repo_root / "supabase" / "migrations").resolve()]

    tables, rls_enabled, policies, views = scan_migrations(repo_root, migration_dirs)

    write_csv(
        out_dir / "db_tables.csv",
        headers=("schema", "table", "file", "line"),
        rows=((t.schema, t.name, t.file, str(t.line)) for t in sorted(tables, key=lambda x: (x.schema, x.name, x.file, x.line))),
    )
    write_csv(
        out_dir / "db_policies.csv",
        headers=("schema", "table", "policy", "command", "roles", "file", "line"),
        rows=((p.schema, p.table, p.name, p.command, p.roles, p.file, str(p.line)) for p in sorted(policies, key=lambda x: (x.schema, x.table, x.name, x.line))),
    )
    write_csv(
        out_dir / "db_views.csv",
        headers=("schema", "view", "security", "file", "line"),
        rows=((v.schema, v.name, v.security, v.file, str(v.line)) for v in views),
    )
    write_report(out_dir / "db_rls_report.md", tables=tables, rls_enabled=rls_enabled, policies=policies, views=views)

    print(f"[OK] Wrote artifacts to: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

