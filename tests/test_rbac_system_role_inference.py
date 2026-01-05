from types import SimpleNamespace
from unittest.mock import Mock

from backend.rbac_system import RBACSystem


def _make_db_with_role_title(role_title: str | None):
    db = Mock()
    query = db.query.return_value
    query.filter.return_value.first.return_value = SimpleNamespace(role_title=role_title)
    return db


def test_get_user_role_ceo_requires_explicit_ceo_title():
    db = _make_db_with_role_title("Director of Operations")
    rbac = RBACSystem(db)
    assert rbac.get_user_role("director@example.com") == "staff"

    db = _make_db_with_role_title("Chief Executive Officer")
    rbac = RBACSystem(db)
    assert rbac.get_user_role("ceo@example.com") == "ceo"


def test_get_user_role_hr_maps_to_pnc():
    db = _make_db_with_role_title("HR Director")
    rbac = RBACSystem(db)
    assert rbac.get_user_role("hr@example.com") == "pnc"

    db = _make_db_with_role_title("People & Culture Manager")
    rbac = RBACSystem(db)
    assert rbac.get_user_role("pnc@example.com") == "pnc"


def test_get_user_role_department_leadership_maps_to_department_head():
    db = _make_db_with_role_title("School Principal")
    rbac = RBACSystem(db)
    assert rbac.get_user_role("principal@example.com") == "department_head"

    db = _make_db_with_role_title("Department Head - Math")
    rbac = RBACSystem(db)
    assert rbac.get_user_role("head@example.com") == "department_head"


def test_get_user_role_defaults_to_staff():
    db = _make_db_with_role_title(None)
    rbac = RBACSystem(db)
    assert rbac.get_user_role("unknown@example.com") == "staff"

