#!/bin/bash
# CryptoSatX Quick Fix Script for HTTP 403 Blocking
# Usage: ./quick_fix.sh

set -e

echo "========================================"
echo "🔧 CryptoSatX HTTP 403 Fix Script"
echo "========================================"
echo ""

# 1. Check .env exists
echo "📝 Step 1: Checking .env file..."
if [ ! -f .env ]; then
    echo "   ❌ .env not found"
    if [ -f .env.example ]; then
        echo "   📄 Creating .env from .env.example..."
        cp .env.example .env
        # Ensure API_KEYS is empty for public access
        if ! grep -q "^API_KEYS=" .env; then
            echo "API_KEYS=" >> .env
        fi
        echo "   ✅ .env created with public access (API_KEYS empty)"
    else
        echo "   ⚠️  .env.example not found, creating minimal .env..."
        cat > .env << 'EOF'
# Minimal configuration for fixing HTTP 403
API_KEYS=
BASE_URL=https://guardiansofthetoken.org
PORT=8000
DATABASE_URL=sqlite:///cryptosatx.db
AUTO_SCAN_ENABLED=false
EOF
        echo "   ✅ Minimal .env created"
    fi
else
    echo "   ✅ .env exists"
    # Check if API_KEYS is set to empty
    if grep -q "^API_KEYS=.\+" .env; then
        echo "   ⚠️  Warning: API_KEYS is not empty. For public access, it should be:"
        echo "      API_KEYS="
        echo ""
        read -p "   Set API_KEYS to empty for public access? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sed -i 's/^API_KEYS=.*/API_KEYS=/' .env
            echo "   ✅ API_KEYS set to empty (public access)"
        fi
    else
        echo "   ✅ API_KEYS is empty (public access enabled)"
    fi
fi
echo ""

# 2. Clear Python cache
echo "🗑️  Step 2: Clearing Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo "   ✅ Cache cleared"
echo ""

# 3. Check Python and dependencies
echo "📦 Step 3: Checking dependencies..."
if command -v python3 &> /dev/null; then
    echo "   ✅ Python3 found: $(python3 --version)"
else
    echo "   ❌ Python3 not found! Please install Python 3.11+"
    exit 1
fi

if [ -f requirements.txt ]; then
    echo "   📦 Installing/updating dependencies..."
    pip install -q -r requirements.txt 2>&1 | grep -v "Requirement already satisfied" || true
    echo "   ✅ Dependencies ready"
else
    echo "   ⚠️  requirements.txt not found"
fi
echo ""

# 4. Test app import
echo "🧪 Step 4: Testing application..."
if python3 -c "import sys; sys.path.insert(0, '.'); from app.main import app" 2>/dev/null; then
    echo "   ✅ Application loads successfully"
else
    echo "   ⚠️  Application import failed (dependencies may be missing)"
    echo "      Run: pip install -r requirements.txt"
fi
echo ""

# 5. Check port
echo "🔍 Step 5: Checking port 8000..."
if lsof -i :8000 &> /dev/null; then
    echo "   ⚠️  Port 8000 is already in use"
    echo "   Current process:"
    lsof -i :8000 | tail -1
    echo ""
    read -p "   Kill existing process and restart? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        PID=$(lsof -t -i :8000)
        kill $PID 2>/dev/null || true
        sleep 2
        echo "   ✅ Process killed"
    fi
else
    echo "   ✅ Port 8000 available"
fi
echo ""

# 6. Display next steps
echo "========================================"
echo "✅ Fix Completed!"
echo "========================================"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Start the server:"
echo "   python3 main.py"
echo ""
echo "2. Test locally (in another terminal):"
echo "   curl -X POST http://localhost:8000/invoke \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"operation\": \"health.check\"}'"
echo ""
echo "3. Test externally:"
echo "   python test_rpc_accessibility.py"
echo ""
echo "4. Check for these in startup logs:"
echo "   ✅ 'API_KEYS: ✗ (public mode)'"
echo "   ✅ 'Uvicorn running on http://0.0.0.0:8000'"
echo ""
echo "5. If still getting 403:"
echo "   - Check Replit deployment settings"
echo "   - Check Cloudflare firewall rules"
echo "   - See FIX_BLOCKING_GUIDE.md for details"
echo ""
echo "========================================"

# Offer to start server
echo ""
read -p "Start server now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Starting server..."
    echo ""
    python3 main.py
else
    echo "✅ Ready to start manually!"
    echo "   Run: python3 main.py"
fi
