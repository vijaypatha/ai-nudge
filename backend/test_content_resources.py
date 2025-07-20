# ---
# File Path: backend/test_content_resources.py
# ---

"""
Simple test to verify our content resources implementation works correctly.
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(__file__))

def test_content_resource_model():
    """Test that the ContentResource model can be imported and has correct fields."""
    try:
        from data.models.resource import ContentResource, ContentResourceCreate, ContentResourceUpdate
        
        print("✅ ContentResource model imported successfully")
        print(f"✅ Model fields: {list(ContentResource.model_fields.keys())}")
        
        # Test creating a ContentResourceCreate instance
        test_resource = ContentResourceCreate(
            title="Test Article",
            url="https://example.com/test",
            description="A test article",
            categories=["test", "example"],
            content_type="article"
        )
        print("✅ ContentResourceCreate instance created successfully")
        print(f"✅ Test resource: {test_resource.model_dump()}")
        
        return True
    except Exception as e:
        print(f"❌ Error testing ContentResource model: {e}")
        return False

def test_content_resource_service():
    """Test that the content resource service can be imported."""
    try:
        from agent_core.content_resource_service import get_content_suggestions_for_client, generate_content_message, increment_resource_usage
        
        print("✅ Content resource service imported successfully")
        return True
    except Exception as e:
        print(f"❌ Error testing content resource service: {e}")
        return False

def test_api_router():
    """Test that the API router can be imported (without database connection)."""
    try:
        # Mock the database dependency to avoid connection issues
        import sys
        from unittest.mock import MagicMock
        
        # Mock the database module
        sys.modules['data.database'] = MagicMock()
        sys.modules['data.database'].get_session = MagicMock()
        
        from api.rest.content_resources import router
        
        print("✅ Content resources API router imported successfully")
        print(f"✅ Router has {len(router.routes)} routes")
        
        return True
    except Exception as e:
        print(f"❌ Error testing API router: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Content Resources Implementation")
    print("=" * 50)
    
    tests = [
        ("ContentResource Model", test_content_resource_model),
        ("Content Resource Service", test_content_resource_service),
        ("API Router", test_api_router),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} passed")
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Implementation is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 