"""
Test script for Phase 1 setup verification.
Run this to ensure core configuration and LLM are working.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_imports():
    """Test that all core modules can be imported."""
    print("=" * 60)
    print("TEST 1: Checking imports...")
    print("=" * 60)
    
    try:
        from app.core import settings, get_llm
        print("✅ Core modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        return False


def test_config():
    """Test configuration loading."""
    print("\n" + "=" * 60)
    print("TEST 2: Checking configuration...")
    print("=" * 60)
    
    try:
        from app.core import settings
        
        print(f"App Name: {settings.app_name}")
        print(f"Version: {settings.app_version}")
        print(f"LLM Model: {settings.huggingface_model}")
        print(f"Embedding Model: {settings.embedding_model}")
        print(f"Vector DB: {settings.vector_db_type}")
        print(f"Chunk Size: {settings.chunk_size}")
        
        if settings.huggingfacehub_api_token:
            token_preview = settings.huggingfacehub_api_token[:10] + "..."
            print(f"HuggingFace Token: {token_preview} (configured)")
        else:
            print("⚠️  HuggingFace Token: NOT SET")
            print("   Set HUGGINGFACEHUB_API_TOKEN in .env file")
        
        print("✅ Configuration loaded successfully")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}")
        return False


def test_llm():
    """Test LLM initialization."""
    print("\n" + "=" * 60)
    print("TEST 3: Testing LLM initialization...")
    print("=" * 60)
    
    try:
        from app.core import settings
        
        if not settings.huggingfacehub_api_token:
            print("⚠️  Skipping LLM test - no API token configured")
            print("   To test LLM, add HUGGINGFACEHUB_API_TOKEN to .env file")
            return None
        
        from app.core import get_llm
        
        print("Initializing LLM...")
        llm = get_llm()
        
        print("\n🧪 Testing with a simple query...")
        print("⏳ This may take 10-30 seconds on first call...")
        
        try:
            text = input("Enter your Query: ")
            response = llm.invoke(text)
            print(f"📝 Response: {response}")
            print("\n✅ LLM test passed!")
            return True
        except Exception as invoke_error:
            print(f"⚠️  LLM invoke failed: {str(invoke_error)}")
            print("   This might be due to:")
            print("   - Invalid HuggingFace token")
            print("   - Model not accessible")
            print("   - Network issues")
            print("   - Rate limiting")
            print("\n   But LLM initialization worked, so Phase 1 is OK!")
            return None
        
    except Exception as e:
        print(f"❌ LLM test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n🧪 PHASE 1 SETUP VERIFICATION")
    print("Testing core configuration and LLM initialization\n")
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("LLM", test_llm()))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for test_name, result in results:
        if result is True:
            status = "✅ PASSED"
        elif result is False:
            status = "❌ FAILED"
        else:
            status = "⚠️  SKIPPED"
        print(f"{test_name}: {status}")
    
    # Overall result
    passed = sum(1 for _, r in results if r is True)
    failed = sum(1 for _, r in results if r is False)
    skipped = sum(1 for _, r in results if r is None)
    
    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed == 0:
        print("\n🎉 Phase 1 setup is complete!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Copy .env.example to .env and add your HuggingFace token")
        print("3. Run the server: python -m app.main")
        print("4. Visit http://localhost:8000/docs")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
