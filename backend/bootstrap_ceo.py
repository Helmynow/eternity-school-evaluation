"""
Bootstrap the CEO (first super admin) record in the `people` table.

The system's bootstrap super admin is derived from the database:
  - the first *active* row in `people` whose `role_title` contains "ceo" (or "chief executive"),
    ordered by `created_at` (then email).

This script ensures a CEO record exists so both:
  - the backend RBAC bootstrap logic, and
  - the Supabase RLS helper functions (ese_is_super_admin)
resolve correctly in production.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Optional

from sqlalchemy import create_engine, text


def _env(name: str) -> Optional[str]:
    value = os.getenv(name)
    return value.strip() if value else None


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _first_active_ceo_email(conn) -> Optional[str]:
    row = conn.execute(
        text(
            """
            select email
            from people
            where active is true
              and (
                lower(coalesce(role_title, '')) like '%ceo%'
                or lower(coalesce(role_title, '')) like '%chief executive%'
              )
            order by created_at asc nulls last, email asc
            limit 1
            """
        )
    ).fetchone()
    return row[0] if row else None


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Ensure the CEO record exists in `people` for super-admin bootstrap.")
    parser.add_argument("--email", default=_env("BOOTSTRAP_CEO_EMAIL"), help="CEO email (or set BOOTSTRAP_CEO_EMAIL).")
    parser.add_argument(
        "--full-name",
        default=_env("BOOTSTRAP_CEO_FULL_NAME"),
        help="CEO full name (or set BOOTSTRAP_CEO_FULL_NAME). Defaults to the email local-part.",
    )
    parser.add_argument(
        "--role-title",
        default=_env("BOOTSTRAP_CEO_ROLE_TITLE") or "CEO",
        help="Role title to set (default: CEO). Must contain 'CEO' to qualify for bootstrap.",
    )
    parser.add_argument(
        "--segment",
        default=_env("BOOTSTRAP_CEO_SEGMENT") or "whole_school",
        help="people.segment (default: whole_school). One of: national, international, whole_school.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=_bool_env("BOOTSTRAP_CEO_FORCE", False),
        help="Override any existing active CEO bootstrap by deactivating other CEO candidates.",
    )
    args = parser.parse_args(argv)

    email = (args.email or "").strip()
    if not email:
        print("Missing CEO email. Provide --email or set BOOTSTRAP_CEO_EMAIL.", file=sys.stderr)
        return 2

    full_name = (args.full_name or "").strip()
    if not full_name:
        full_name = email.split("@", 1)[0].replace(".", " ").replace("_", " ").strip() or email

    role_title = (args.role_title or "").strip() or "CEO"
    if "ceo" not in role_title.lower():
        print("role_title must contain 'CEO' to qualify for bootstrap (e.g., 'CEO', 'Chief Executive Officer').", file=sys.stderr)
        return 2

    segment = (args.segment or "").strip() or "whole_school"

    db_url = _env("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL is not set. Export DATABASE_URL before running this script.", file=sys.stderr)
        return 2

    engine = create_engine(db_url)

    with engine.begin() as conn:
        existing_bootstrap = _first_active_ceo_email(conn)
        if existing_bootstrap and existing_bootstrap.lower() != email.lower() and not args.force:
            print(
                "A different active CEO bootstrap already exists in `people`.\n"
                f"Existing bootstrap: {existing_bootstrap}\n"
                f"Requested bootstrap: {email}\n"
                "Refusing to override without --force (or BOOTSTRAP_CEO_FORCE=true).",
                file=sys.stderr,
            )
            return 3

        if args.force:
            # Ensure the requested CEO becomes the bootstrap by deactivating other CEO candidates.
            conn.execute(
                text(
                    """
                    update people
                    set active = false,
                        updated_at = now()
                    where active is true
                      and (
                        lower(coalesce(role_title, '')) like '%ceo%'
                        or lower(coalesce(role_title, '')) like '%chief executive%'
                      )
                      and lower(email) <> lower(:email)
                    """
                ),
                {"email": email},
            )

        conn.execute(
            text(
                """
                insert into people (email, full_name, role_title, segment, active)
                values (:email, :full_name, :role_title, cast(:segment as staff_segment), true)
                on conflict (email) do update
                  set full_name = excluded.full_name,
                      role_title = excluded.role_title,
                      segment = excluded.segment,
                      active = true,
                      updated_at = now()
                """
            ),
            {"email": email, "full_name": full_name, "role_title": role_title, "segment": segment},
        )

        final_bootstrap = _first_active_ceo_email(conn)

    if final_bootstrap and final_bootstrap.lower() == email.lower():
        print(f"✅ CEO bootstrap ensured: {final_bootstrap}")
        return 0

    print(
        "CEO record upserted, but it is not currently resolving as the bootstrap super admin.\n"
        f"Expected: {email}\n"
        f"Resolved: {final_bootstrap or '(none)'}\n"
        "Check for other active CEO candidates with earlier created_at and rerun with --force if appropriate.",
        file=sys.stderr,
    )
    return 4


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
