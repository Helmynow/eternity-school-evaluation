#!/usr/bin/env python3
"""
Generate a lightweight UI↔API traceability map from code.

Outputs (default under ./audit_artifacts):
- ui_routes.csv: discovered frontend routes and their component file(s)
- api_endpoints.csv: discovered backend FastAPI endpoints (decorators)
- ui_route_api.csv: best-effort route→API mapping (static scan)
- ui_mapping_matrix.csv: a starter traceability matrix you can fill in (permissions/RLS/tests)
- ui-map.puml: a simple PlantUML diagram listing routes and API calls

Design goals:
- No external deps (stdlib only)
- Best-effort parsing; safe to run repeatedly
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


@dataclass(frozen=True)
class RouteHit:
    path: str
    file: str
    line: int
    component: Optional[str]
    component_file: Optional[str]


@dataclass(frozen=True)
class ApiEndpoint:
    method: str
    path: str
    file: str
    line: int


@dataclass(frozen=True)
class RouteApiHit:
    ui_route: str
    api_method: str
    api_path: str
    ui_ref: str
    call_ref: str


FASTAPI_DECORATOR = re.compile(r"""^\s*@(?:app|router)\.(get|post|put|patch|delete)\(\s*["']([^"']+)["']""", re.IGNORECASE)

ROUTE_ELEMENT = re.compile(
    r"""<Route[^>]*\bpath\s*=\s*["']([^"']+)["'][^>]*\belement\s*=\s*\{?\s*<([A-Za-z0-9_]+)"""
)
ROUTE_ELEMENT_ALT = re.compile(r"""<Route[^>]*\bpath\s*=\s*["']([^"']+)["'][^>]*>""")

LAZY_IMPORT = re.compile(r"""^\s*const\s+([A-Za-z0-9_]+)\s*=\s*lazy\(\(\)\s*=>\s*import\(\s*['"]([^'"]+)['"]\s*\)\s*\)""")
STATIC_IMPORT = re.compile(r"""^\s*import\s+(.+?)\s+from\s+['"]([^'"]+)['"]\s*;?\s*$""")

APICLIENT_CALL = re.compile(r"""\bapiClient\.([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)\b""")
RAW_API_CALL = re.compile(
    r"""\bapi\.(get|post|put|patch|delete)\(\s*([`"'])(/api/v2/[^`"']+)\2""",
    re.IGNORECASE,
)

APICLIENT_DEF = re.compile(
    r"""^\s*([A-Za-z0-9_]+)\s*:\s*\([^)]*\)\s*=>\s*api\.(get|post|put|patch|delete)\(\s*([`"'])(/api/v2/[^`"']+)\3""",
    re.IGNORECASE,
)
OBJECT_OPEN = re.compile(r"""^\s*([A-Za-z0-9_]+)\s*:\s*\{\s*$""")
OBJECT_CLOSE = re.compile(r"""^\s*\}\s*,?\s*$""")


def _read_lines(path: Path) -> List[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []


def write_csv(path: Path, headers: Sequence[str], rows: Iterable[Sequence[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(list(headers))
        for row in rows:
            writer.writerow(list(row))


def resolve_relative_import(base_file: Path, import_path: str) -> Optional[Path]:
    if not import_path.startswith("."):
        return None
    base_dir = base_file.parent
    candidate = (base_dir / import_path).resolve()
    if candidate.is_file():
        return candidate
    # Try extensions
    for ext in (".js", ".jsx", ".ts", ".tsx"):
        p = candidate.with_suffix(ext)
        if p.is_file():
            return p
    # Try index files
    if candidate.is_dir():
        for ext in (".js", ".jsx", ".ts", ".tsx"):
            p = candidate / f"index{ext}"
            if p.is_file():
                return p
    return None


def canonicalize_path(path: str) -> str:
    """
    Normalize paths so frontend template strings and backend {params} compare reliably.
    """

    p = path.strip()
    p = re.sub(r"""\$\{[^}]+\}""", "{param}", p)
    p = re.sub(r"""\{[^}]+\}""", "{param}", p)
    return p


def parse_api_client_definitions(api_file: Path) -> Dict[Tuple[str, str], Tuple[str, str, int]]:
    """
    Return mapping: (group, method) -> (HTTP_METHOD, /api/v2/path, line)
    """
    lines = _read_lines(api_file)
    stack: List[str] = []
    mapping: Dict[Tuple[str, str], Tuple[str, str, int]] = {}

    for idx, raw in enumerate(lines, start=1):
        line = raw.split("//", 1)[0]
        open_match = OBJECT_OPEN.match(line)
        if open_match:
            stack.append(open_match.group(1))
            continue
        if OBJECT_CLOSE.match(line):
            if stack:
                stack.pop()
            continue

        leaf = APICLIENT_DEF.match(line)
        if not leaf:
            continue
        method_name = leaf.group(1)
        http_method = leaf.group(2).upper()
        api_path = leaf.group(4)

        # stack contains e.g. ["apiClient", "eom"] (depending on where we start); normalize to last segment as group.
        group = ""
        for key in reversed(stack):
            if key == "apiClient":
                continue
            group = key
            break
        if not group:
            # Fallback: treat as top-level
            group = "root"

        mapping[(group, method_name)] = (http_method, api_path, idx)

    return mapping


def find_backend_endpoints(repo_root: Path) -> List[ApiEndpoint]:
    backend_dir = repo_root / "backend"
    if not backend_dir.exists():
        return []

    endpoints: List[ApiEndpoint] = []
    seen: Set[Tuple[str, str, str, int]] = set()
    for file_path in sorted(backend_dir.glob("**/*.py")):
        lines = _read_lines(file_path)
        for idx, line in enumerate(lines, start=1):
            match = FASTAPI_DECORATOR.match(line)
            if not match:
                continue
            method = match.group(1).upper()
            path = match.group(2).strip()
            rel = str(file_path.relative_to(repo_root))
            key = (method, path, rel, idx)
            if key in seen:
                continue
            seen.add(key)
            endpoints.append(ApiEndpoint(method=method, path=path, file=rel, line=idx))
    return endpoints


def find_routes_from_app(repo_root: Path) -> List[RouteHit]:
    app_file = repo_root / "frontend" / "src" / "App.jsx"
    if not app_file.exists():
        return []

    lines = _read_lines(app_file)
    lazy_map: Dict[str, str] = {}
    for idx, line in enumerate(lines, start=1):
        m = LAZY_IMPORT.match(line)
        if not m:
            continue
        comp, import_path = m.group(1), m.group(2)
        # Resolve to a file under frontend/src
        resolved = resolve_relative_import(app_file, import_path)
        if resolved:
            lazy_map[comp] = str(resolved.relative_to(repo_root))

    hits: List[RouteHit] = []
    for idx, line in enumerate(lines, start=1):
        m = ROUTE_ELEMENT.search(line)
        if m:
            path = m.group(1).strip()
            component = m.group(2).strip()
            hits.append(
                RouteHit(
                    path=path,
                    file=str(app_file.relative_to(repo_root)),
                    line=idx,
                    component=component,
                    component_file=lazy_map.get(component),
                )
            )
            continue

        m2 = ROUTE_ELEMENT_ALT.search(line)
        if m2:
            path = m2.group(1).strip()
            hits.append(RouteHit(path=path, file=str(app_file.relative_to(repo_root)), line=idx, component=None, component_file=None))
    # Deduplicate by path+line
    seen: Set[Tuple[str, int]] = set()
    out: List[RouteHit] = []
    for h in hits:
        key = (h.path, h.line)
        if key in seen:
            continue
        seen.add(key)
        out.append(h)
    return out


def build_import_closure(repo_root: Path, entry_file: Path, *, max_depth: int = 3, max_files: int = 50) -> List[Path]:
    """
    Follow local relative imports from an entry file to capture apiClient usage in hooks/helpers.
    Keeps traversal small and conservative.
    """

    visited: Set[Path] = set()
    queue: List[Tuple[Path, int]] = [(entry_file.resolve(), 0)]

    while queue:
        file_path, depth = queue.pop(0)
        if file_path in visited:
            continue
        visited.add(file_path)
        if len(visited) >= max_files or depth >= max_depth:
            continue

        lines = _read_lines(file_path)
        for line in lines:
            m = STATIC_IMPORT.match(line)
            if not m:
                continue
            import_path = m.group(2)
            resolved = resolve_relative_import(file_path, import_path)
            if not resolved:
                continue
            try:
                resolved.relative_to(repo_root / "frontend" / "src")
            except Exception:
                continue
            queue.append((resolved, depth + 1))

    return sorted(visited)


def find_route_api_usage(
    repo_root: Path, routes: List[RouteHit], api_client_map: Dict[Tuple[str, str], Tuple[str, str, int]]
) -> List[RouteApiHit]:
    hits: List[RouteApiHit] = []
    for r in routes:
        if not r.component_file:
            continue
        component_path = repo_root / r.component_file
        if not component_path.exists():
            continue

        closure_files = build_import_closure(repo_root, component_path)
        for f in closure_files:
            # Avoid treating the API client definition file as "usage" for every route.
            # Real usage is detected via apiClient.<group>.<method> calls in feature code.
            if f.as_posix().endswith("/frontend/src/lib/api.js"):
                continue
            rel = str(f.relative_to(repo_root))
            lines = _read_lines(f)
            for idx, line in enumerate(lines, start=1):
                for m in APICLIENT_CALL.finditer(line):
                    group, method_name = m.group(1), m.group(2)
                    mapped = api_client_map.get((group, method_name))
                    if not mapped:
                        continue
                    http_method, api_path, api_def_line = mapped
                    hits.append(
                        RouteApiHit(
                            ui_route=r.path,
                            api_method=http_method,
                            api_path=api_path,
                            ui_ref=f"{r.file}:{r.line}",
                            call_ref=f"{rel}:{idx}",
                        )
                    )
                m2 = RAW_API_CALL.search(line)
                if m2:
                    hits.append(
                        RouteApiHit(
                            ui_route=r.path,
                            api_method=m2.group(1).upper(),
                            api_path=m2.group(3),
                            ui_ref=f"{r.file}:{r.line}",
                            call_ref=f"{rel}:{idx}",
                        )
                    )
    # Deduplicate
    seen: Set[Tuple[str, str, str, str]] = set()
    out: List[RouteApiHit] = []
    for h in hits:
        key = (h.ui_route, h.api_method, h.api_path, h.call_ref)
        if key in seen:
            continue
        seen.add(key)
        out.append(h)
    return out


def write_puml(path: Path, routes: List[RouteHit], api_hits: List[RouteApiHit]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    lines.append("@startuml")
    lines.append("title UI ↔ API Map")
    lines.append("left to right direction")
    lines.append("skinparam shadowing false")
    lines.append("")
    lines.append('package "Routes" {')
    for r in sorted({h.path for h in routes}):
        safe_id = f"route_{abs(hash(r)) % 10_000_000}"
        lines.append(f'  ["{r}"] as {safe_id}')
    lines.append("}")
    lines.append("")
    lines.append('package "API Calls (from frontend)" {')
    for api in sorted({h.api_path for h in api_hits}):
        safe_id = f"api_{abs(hash(api)) % 10_000_000}"
        lines.append(f'  ["{api}"] as {safe_id}')
    lines.append("}")
    lines.append("")
    for h in api_hits:
        r_id = f"route_{abs(hash(h.ui_route)) % 10_000_000}"
        a_id = f"api_{abs(hash(h.api_path)) % 10_000_000}"
        lines.append(f"{r_id} --> {a_id} : {h.api_method}")
    lines.append("@enduml")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_existing_matrix(path: Path) -> Dict[Tuple[str, str, str], Dict[str, str]]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except Exception:
        return {}

    preserved: Dict[Tuple[str, str, str], Dict[str, str]] = {}
    for row in rows:
        ui_route = (row.get("ui_route") or "").strip()
        api_method = (row.get("api_method") or "").strip().upper()
        api_path = (row.get("api_path") or "").strip()
        if not ui_route or not api_method or not api_path:
            continue
        key = (ui_route, api_method, canonicalize_path(api_path))
        preserved[key] = {
            "feature": (row.get("feature") or "").strip(),
            "permission_key": (row.get("permission_key") or "").strip(),
            "rls_tables": (row.get("rls_tables") or "").strip(),
            "rls_notes": (row.get("rls_notes") or "").strip(),
            "audit_event": (row.get("audit_event") or "").strip(),
            "tests": (row.get("tests") or "").strip(),
            "notes": (row.get("notes") or "").strip(),
        }
    return preserved


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate UI/API traceability artifacts")
    parser.add_argument("--repo-root", default=".", help="Path to repository root")
    parser.add_argument("--out-dir", default="audit_artifacts", help="Output directory (relative to repo root)")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_dir = (repo_root / args.out_dir).resolve()

    routes = find_routes_from_app(repo_root)
    endpoints = find_backend_endpoints(repo_root)

    api_file = repo_root / "frontend" / "src" / "lib" / "api.js"
    api_client_map: Dict[Tuple[str, str], Tuple[str, str, int]] = {}
    if api_file.exists():
        api_client_map = parse_api_client_definitions(api_file)

    route_api = find_route_api_usage(repo_root, routes, api_client_map)

    write_csv(
        out_dir / "ui_routes.csv",
        headers=("path", "component", "component_file", "file", "line"),
        rows=((r.path, r.component or "", r.component_file or "", r.file, str(r.line)) for r in routes),
    )
    write_csv(
        out_dir / "api_endpoints.csv",
        headers=("method", "path", "file", "line"),
        rows=((e.method, e.path, e.file, str(e.line)) for e in endpoints),
    )
    write_csv(
        out_dir / "ui_route_api.csv",
        headers=("ui_route", "api_method", "api_path", "ui_ref", "call_ref"),
        rows=((h.ui_route, h.api_method, h.api_path, h.ui_ref, h.call_ref) for h in route_api),
    )

    endpoint_index: Dict[Tuple[str, str], str] = {}
    for e in endpoints:
        key = (e.method.upper(), canonicalize_path(e.path))
        endpoint_index.setdefault(key, f"{e.file}:{e.line}")

    # Starter traceability matrix rows (route→api)
    matrix_headers = (
        "feature",
        "ui_route",
        "ui_component",
        "ui_file",
        "ui_ref",
        "api_method",
        "api_path",
        "backend_ref",
        "permission_key",
        "rls_tables",
        "rls_notes",
        "audit_event",
        "tests",
        "notes",
    )
    existing = read_existing_matrix(out_dir / "ui_mapping_matrix.csv")

    matrix_rows: List[Tuple[str, ...]] = []
    seen_matrix: Set[Tuple[str, str, str]] = set()
    for h in route_api:
        matrix_key = (h.ui_route, h.api_method, canonicalize_path(h.api_path))
        if matrix_key in seen_matrix:
            continue
        seen_matrix.add(matrix_key)
        # Try to locate the route definition to fill component/file
        route_def = next((r for r in routes if r.path == h.ui_route), None)
        component = route_def.component if route_def else ""
        ui_file = route_def.component_file if route_def and route_def.component_file else (route_def.file if route_def else "")
        backend_ref = endpoint_index.get((h.api_method, canonicalize_path(h.api_path)), "")

        preserved = existing.get((h.ui_route, h.api_method, canonicalize_path(h.api_path)), {})

        default_perm = ""
        if h.ui_route.startswith("/admin"):
            default_perm = "role:ceo|pnc"
            if h.ui_route in ("/admin/settings", "/admin/integration"):
                default_perm = "role:ceo"
        matrix_rows.append(
            (
                preserved.get("feature", ""),
                h.ui_route,
                component or "",
                ui_file or "",
                h.ui_ref,
                h.api_method,
                h.api_path,
                backend_ref,
                preserved.get("permission_key", "") or default_perm,
                preserved.get("rls_tables", ""),
                preserved.get("rls_notes", ""),
                preserved.get("audit_event", ""),
                preserved.get("tests", ""),
                preserved.get("notes", ""),
            )
        )

    write_csv(out_dir / "ui_mapping_matrix.csv", headers=matrix_headers, rows=matrix_rows)
    write_puml(out_dir / "ui-map.puml", routes=routes, api_hits=route_api)

    print(f"[OK] Wrote artifacts to: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
