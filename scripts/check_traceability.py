#!/usr/bin/env python3
"""
CI-friendly checks for traceability artifacts under audit_artifacts/.

Goal: prevent "new UI controls / endpoints" from landing without being mapped to permissions/audit/tests.
This is intentionally lightweight and conservative.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def read_csv(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = [row for row in reader]
    return headers, rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate audit_artifacts traceability matrix")
    parser.add_argument("--repo-root", default=".", help="Path to repository root")
    parser.add_argument("--artifacts-dir", default="audit_artifacts", help="Artifacts directory (relative to repo root)")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    artifacts_dir = (repo_root / args.artifacts_dir).resolve()
    matrix_path = artifacts_dir / "ui_mapping_matrix.csv"

    errors: List[str] = []

    if not artifacts_dir.exists():
        errors.append(f"Missing artifacts directory: {artifacts_dir}")
    if not matrix_path.exists():
        errors.append(f"Missing traceability matrix: {matrix_path}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 2

    headers, rows = read_csv(matrix_path)
    required_cols = {"ui_route", "api_method", "api_path", "backend_ref", "permission_key"}
    missing_cols = sorted([c for c in required_cols if c not in set(headers)])
    if missing_cols:
        errors.append(f"ui_mapping_matrix.csv missing columns: {', '.join(missing_cols)}")
        print("\n".join(errors), file=sys.stderr)
        return 2

    for idx, row in enumerate(rows, start=2):  # header is line 1
        ui_route = (row.get("ui_route") or "").strip()
        api_path = (row.get("api_path") or "").strip()
        backend_ref = (row.get("backend_ref") or "").strip()
        perm = (row.get("permission_key") or "").strip()

        if not ui_route and not api_path:
            # allow blank rows if someone keeps templates, but discourage
            continue

        # If an API path is listed, it should resolve to a backend handler reference.
        # (Exceptions can be documented by leaving a note and setting backend_ref to "external".)
        if api_path and not backend_ref:
            errors.append(f"{matrix_path}:{idx} api_path has no backend_ref: {api_path}")

        # Enforce permission mapping for admin pages (highest risk)
        if ui_route.startswith("/admin"):
            if not perm:
                errors.append(f"{matrix_path}:{idx} admin route missing permission_key: {ui_route} ({api_path})")

    if errors:
        print("Traceability check failed:", file=sys.stderr)
        for e in errors:
            print(f"- {e}", file=sys.stderr)
        return 1

    print("Traceability check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

