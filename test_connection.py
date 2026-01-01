#!/usr/bin/env python3
"""Test database connection and application startup"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_database_connection():
    """Test database connection"""
    print("=" * 60)
    print("Testing Database Connection")
    print("=" * 60)
    
    try:
        from backend.database import Database, get_db_session
        
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            print("❌ DATABASE_URL not set in environment")
            return False
        
        print(f"✅ DATABASE_URL found ({len(db_url)} chars)")
        
        # Try to create a session
        try:
            from sqlalchemy import text
            with get_db_session() as db:
                # Test query
                result = db.execute(text("SELECT 1 as test")).fetchone()
                if result:
                    print("✅ Database connection successful!")
                    return True
                else:
                    print("⚠️  Database connection returned no result")
                    return False
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing database: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_fastapi_app():
    """Test FastAPI app initialization"""
    print("\n" + "=" * 60)
    print("Testing FastAPI Application")
    print("=" * 60)
    
    try:
        from backend.fastapi_app import app
        
        print(f"✅ FastAPI app imported successfully")
        print(f"✅ Found {len(app.routes)} routes")
        
        # Check for announcement endpoints
        announcement_routes = [r for r in app.routes if hasattr(r, 'path') and 'announcement' in r.path.lower()]
        print(f"✅ Found {len(announcement_routes)} announcement routes")
        
        return True
    except Exception as e:
        print(f"❌ FastAPI app test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_email_service():
    """Test email service configuration"""
    print("\n" + "=" * 60)
    print("Testing Email Service")
    print("=" * 60)
    
    try:
        from backend.email_service import EmailService
        
        email_service = EmailService()
        print(f"✅ EmailService initialized")
        print(f"   Server: {email_service.smtp_server}")
        print(f"   Port: {email_service.smtp_port}")
        print(f"   User: {email_service.smtp_user}")
        print(f"   Enabled: {email_service.enabled}")
        
        if email_service.smtp_server == 'smtp.resend.com':
            print("✅ Resend SMTP configured correctly")
        
        return True
    except Exception as e:
        print(f"❌ Email service test failed: {str(e)}")
        return False


def test_scheduler():
    """Test task scheduler"""
    print("\n" + "=" * 60)
    print("Testing Task Scheduler")
    print("=" * 60)
    
    try:
        from backend.task_scheduler import TaskScheduler
        
        scheduler = TaskScheduler()
        print("✅ TaskScheduler initialized")
        print(f"   Running: {scheduler.is_running}")
        
        return True
    except Exception as e:
        print(f"❌ Task scheduler test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Pre-Deployment Connection Test")
    print("=" * 60)
    print()
    
    results = []
    results.append(("Database Connection", test_database_connection()))
    results.append(("FastAPI App", test_fastapi_app()))
    results.append(("Email Service", test_email_service()))
    results.append(("Task Scheduler", test_scheduler()))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if not result:
            all_passed = False
    
    print()
    if all_passed:
        print("✅ All tests passed! Ready for deployment.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please fix issues before deploying.")
        sys.exit(1)
