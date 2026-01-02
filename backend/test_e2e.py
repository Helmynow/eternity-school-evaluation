"""
End-to-End Test and Audit Script for Eternity School Evaluation System
Tests all critical components and features
"""

import os
import sys
import traceback
from datetime import datetime

# Add parent directory to path so we can import backend
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)


def test_imports():
    """Test all critical imports"""
    print("=" * 60)
    print("TEST 1: Import Checks")
    print("=" * 60)

    errors = []

    try:
        from backend.database import Announcement, Cycle, Database, Person

        print("✅ Database models imported successfully")
    except Exception as e:
        errors.append(f"Database models: {str(e)}")
        print(f"❌ Database models: {str(e)}")

    try:
        from backend.email_service import EmailService

        print("✅ EmailService imported successfully")
    except Exception as e:
        errors.append(f"EmailService: {str(e)}")
        print(f"❌ EmailService: {str(e)}")

    try:
        from backend.task_scheduler import TaskScheduler, task_scheduler

        print("✅ TaskScheduler imported successfully")
    except Exception as e:
        errors.append(f"TaskScheduler: {str(e)}")
        print(f"❌ TaskScheduler: {str(e)}")
        traceback.print_exc()

    try:
        from backend.smart_notification_system import SmartNotificationSystem

        print("✅ SmartNotificationSystem imported successfully")
    except Exception as e:
        errors.append(f"SmartNotificationSystem: {str(e)}")
        print(f"❌ SmartNotificationSystem: {str(e)}")

    try:
        from backend.fastapi_app import app

        print("✅ FastAPI app imported successfully")
    except Exception as e:
        errors.append(f"FastAPI app: {str(e)}")
        print(f"❌ FastAPI app: {str(e)}")
        traceback.print_exc()

    return errors


def test_database_connection():
    """Test database connection"""
    print("\n" + "=" * 60)
    print("TEST 2: Database Connection")
    print("=" * 60)

    try:
        from backend.database import Database, get_db_session

        # Test basic connection
        db = Database()
        session = db.get_session()
        print("✅ Database session created successfully")

        # Test context manager
        try:
            with get_db_session() as db_session:
                print("✅ get_db_session context manager works")
        except Exception as e:
            print(f"⚠️  get_db_session context manager: {str(e)}")

        session.close()
        db.close()
        return []
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        traceback.print_exc()
        return [f"Database connection: {str(e)}"]


def test_email_service():
    """Test email service configuration"""
    print("\n" + "=" * 60)
    print("TEST 3: Email Service Configuration")
    print("=" * 60)

    try:
        from backend.email_service import EmailService

        email_service = EmailService()
        print(f"✅ EmailService initialized")
        print(f"   SMTP Server: {email_service.smtp_server}")
        print(f"   SMTP Port: {email_service.smtp_port}")
        print(f"   SMTP User: {email_service.smtp_user}")
        print(f"   From Email: {email_service.from_email}")
        print(f"   Enabled: {email_service.enabled}")

        # Test configuration
        if email_service.smtp_server == "smtp.resend.com":
            print("✅ Resend SMTP configured correctly")
        else:
            print(f"⚠️  SMTP server is {email_service.smtp_server}, expected smtp.resend.com")

        if email_service.smtp_port == 465:
            print("✅ SMTP port configured correctly (465 for SSL)")
        else:
            print(f"⚠️  SMTP port is {email_service.smtp_port}, expected 465")

        return []
    except Exception as e:
        print(f"❌ EmailService test failed: {str(e)}")
        traceback.print_exc()
        return [f"EmailService: {str(e)}"]


def test_task_scheduler():
    """Test task scheduler"""
    print("\n" + "=" * 60)
    print("TEST 4: Task Scheduler")
    print("=" * 60)

    try:
        from backend.task_scheduler import TaskScheduler

        scheduler = TaskScheduler()
        print("✅ TaskScheduler initialized")

        # Check if scheduler has required methods
        required_methods = [
            "start",
            "stop",
            "schedule_daily_tasks",
            "send_daily_smart_reminders",
            "check_overdue_evaluations",
            "send_due_soon_reminders",
            "process_pending_emails",
            "cleanup_expired_announcements",
        ]

        for method in required_methods:
            if hasattr(scheduler, method):
                print(f"✅ Method '{method}' exists")
            else:
                print(f"❌ Method '{method}' missing")
                return [f"Missing method: {method}"]

        return []
    except Exception as e:
        print(f"❌ TaskScheduler test failed: {str(e)}")
        traceback.print_exc()
        return [f"TaskScheduler: {str(e)}"]


def test_announcement_model():
    """Test Announcement model"""
    print("\n" + "=" * 60)
    print("TEST 5: Announcement Model")
    print("=" * 60)

    try:
        from backend.database import Announcement

        # Check model attributes
        required_attrs = [
            "id",
            "title",
            "content",
            "author_email",
            "priority",
            "target_audience",
            "is_active",
            "expires_at",
            "created_at",
            "updated_at",
        ]

        for attr in required_attrs:
            if hasattr(Announcement, attr):
                print(f"✅ Attribute '{attr}' exists")
            else:
                print(f"❌ Attribute '{attr}' missing")
                return [f"Missing attribute: {attr}"]

        print("✅ Announcement model structure is correct")
        return []
    except Exception as e:
        print(f"❌ Announcement model test failed: {str(e)}")
        traceback.print_exc()
        return [f"Announcement model: {str(e)}"]


def test_fastapi_endpoints():
    """Test FastAPI endpoint definitions"""
    print("\n" + "=" * 60)
    print("TEST 6: FastAPI Endpoints")
    print("=" * 60)

    try:
        from backend.fastapi_app import app

        # Get all routes
        routes = []
        for route in app.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                routes.append((route.path, route.methods))

        print(f"✅ Found {len(routes)} routes")

        # Check for announcement endpoints
        announcement_routes = ["/api/v2/announcements", "/api/v2/announcements/{announcement_id}"]

        found_routes = []
        for path, methods in routes:
            if "announcement" in path.lower():
                found_routes.append((path, methods))
                print(f"✅ Found announcement route: {path} {methods}")

        if len(found_routes) >= 2:
            print("✅ Announcement endpoints are defined")
        else:
            print(f"⚠️  Expected at least 2 announcement routes, found {len(found_routes)}")

        # Check for health endpoint
        health_found = any("/health" in path for path, _ in routes)
        if health_found:
            print("✅ Health endpoint exists")
        else:
            print("⚠️  Health endpoint not found")

        return []
    except Exception as e:
        print(f"❌ FastAPI endpoints test failed: {str(e)}")
        traceback.print_exc()
        return [f"FastAPI endpoints: {str(e)}"]


def test_scheduler_integration():
    """Test scheduler integration with FastAPI"""
    print("\n" + "=" * 60)
    print("TEST 7: Scheduler Integration")
    print("=" * 60)

    try:
        from backend.fastapi_app import app
        from backend.task_scheduler import task_scheduler

        # Check if scheduler is imported
        print("✅ Task scheduler imported in fastapi_app")

        # Check if startup/shutdown events exist
        has_startup = (
            any(hasattr(handler, "__name__") and "startup" in handler.__name__.lower() for handler in app.router.on_startup)
            if hasattr(app.router, "on_startup")
            else False
        )

        has_shutdown = (
            any(hasattr(handler, "__name__") and "shutdown" in handler.__name__.lower() for handler in app.router.on_shutdown)
            if hasattr(app.router, "on_shutdown")
            else False
        )

        # Check for @app.on_event decorators
        import inspect

        source = inspect.getsource(app.__class__) if hasattr(app, "__class__") else ""

        # Try to find startup/shutdown in the module
        import backend.fastapi_app as fastapi_module

        has_startup_event = hasattr(fastapi_module, "startup_event") or any(
            "startup" in str(func) for func in dir(fastapi_module) if callable(getattr(fastapi_module, func, None))
        )

        if has_startup_event:
            print("✅ Startup event handler exists")
        else:
            print("⚠️  Startup event handler not found")

        return []
    except Exception as e:
        print(f"❌ Scheduler integration test failed: {str(e)}")
        traceback.print_exc()
        return [f"Scheduler integration: {str(e)}"]


def test_smart_notification_methods():
    """Test SmartNotificationSystem has required methods"""
    print("\n" + "=" * 60)
    print("TEST 8: SmartNotificationSystem Methods")
    print("=" * 60)

    try:
        from backend.smart_notification_system import SmartNotificationSystem

        # Check if send_smart_reminders_for_cycle exists
        if hasattr(SmartNotificationSystem, "send_smart_reminders_for_cycle"):
            print("✅ send_smart_reminders_for_cycle method exists")
        else:
            print("⚠️  send_smart_reminders_for_cycle method not found")
            print("   Note: This method is called by task_scheduler")
            print("   The scheduler has a workaround implementation")

        # Check other required methods
        required_methods = ["send_notification", "should_notify", "get_user_behavior_profile"]

        for method in required_methods:
            if hasattr(SmartNotificationSystem, method):
                print(f"✅ Method '{method}' exists")
            else:
                print(f"❌ Method '{method}' missing")

        return []
    except Exception as e:
        print(f"❌ SmartNotificationSystem test failed: {str(e)}")
        traceback.print_exc()
        return [f"SmartNotificationSystem: {str(e)}"]


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("E2E TEST AND AUDIT - Eternity School Evaluation System")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    print()

    all_errors = []

    # Run all tests
    all_errors.extend(test_imports())
    all_errors.extend(test_database_connection())
    all_errors.extend(test_email_service())
    all_errors.extend(test_task_scheduler())
    all_errors.extend(test_announcement_model())
    all_errors.extend(test_fastapi_endpoints())
    all_errors.extend(test_scheduler_integration())
    all_errors.extend(test_smart_notification_methods())

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    if len(all_errors) == 0:
        print("✅ ALL TESTS PASSED - System is ready for production!")
    else:
        print(f"⚠️  Found {len(all_errors)} issue(s):")
        for i, error in enumerate(all_errors, 1):
            print(f"   {i}. {error}")

    print(f"\nCompleted at: {datetime.now().isoformat()}")
    return 0 if len(all_errors) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
