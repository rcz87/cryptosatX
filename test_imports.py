#!/usr/bin/env python3
"""Test script to check if all required dependencies are available for Replit deployment"""

import sys

def test_import(module_name):
    """Test if a module can be imported"""
    try:
        __import__(module_name)
        print(f"✅ {module_name}: Available")
        return True
    except ImportError as e:
        print(f"❌ {module_name}: Not available - {e}")
        return False

def main():
    """Test all required dependencies"""
    print("🔍 Testing CryptoSatX Dependencies for Replit Deployment")
    print("=" * 60)
    print(f"Python version: {sys.version}")
    print()
    
    # Core dependencies
    print("📦 Core Dependencies:")
    core_deps = [
        "fastapi",
        "uvicorn", 
        "httpx",
        "pydantic",
        "python_dotenv"
    ]
    
    core_ok = all(test_import(dep) for dep in core_deps)
    print()
    
    # Enhancement dependencies
    print("🚀 Enhancement Dependencies:")
    enhance_deps = [
        "redis",
        "asyncpg",
        "aiosqlite", 
        "prometheus_client",
        "slowapi",
        "psutil"
    ]
    
    enhance_ok = all(test_import(dep) for dep in enhance_deps)
    print()
    
    # ML dependencies
    print("🤖 Machine Learning Dependencies:")
    ml_deps = [
        "sklearn",
        "numpy", 
        "pandas",
        "joblib"
    ]
    
    ml_ok = all(test_import(dep) for dep in ml_deps)
    print()
    
    # Security dependencies
    print("🔐 Security Dependencies:")
    security_deps = [
        "jwt",
        "cryptography",
        "passlib"
    ]
    
    security_ok = all(test_import(dep) for dep in security_deps)
    print()
    
    # Alert dependencies
    print("📢 Alert Dependencies:")
    alert_deps = [
        "aiohttp",
        "aiosmtplib"
    ]
    
    alert_ok = all(test_import(dep) for dep in alert_deps)
    print()
    
    # Replit specific
    print("🔄 Replit Dependencies:")
    replit_ok = test_import("replit")
    print()
    
    # Summary
    print("📊 DEPLOYMENT READINESS SUMMARY")
    print("=" * 60)
    
    all_ok = core_ok and enhance_ok and ml_ok and security_ok and alert_ok and replit_ok
    
    if all_ok:
        print("🎉 ALL DEPENDENCIES AVAILABLE - Ready for Replit deployment!")
        print("✅ Core functionality: OK")
        print("✅ Enhanced features: OK") 
        print("✅ ML capabilities: OK")
        print("✅ Security features: OK")
        print("✅ Alert system: OK")
        print("✅ Replit integration: OK")
    else:
        print("⚠️  SOME DEPENDENCIES MISSING - Install with:")
        if not core_ok:
            print("   pip install fastapi uvicorn httpx pydantic python-dotenv")
        if not enhance_ok:
            print("   pip install redis asyncpg aiosqlite prometheus-client slowapi psutil")
        if not ml_ok:
            print("   pip install scikit-learn numpy pandas joblib")
        if not security_ok:
            print("   pip install PyJWT cryptography passlib[bcrypt]")
        if not alert_ok:
            print("   pip install aiohttp aiosmtplib")
        if not replit_ok:
            print("   pip install replit")
    
    print()
    print("🚀 To deploy to Replit:")
    print("1. Run: pip install -r requirements.txt")
    print("2. Set environment variables in Replit Secrets")
    print("3. Click 'Run' button in Replit")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
