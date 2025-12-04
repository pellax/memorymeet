#!/bin/bash
# ================================================================================================
# 🚀 QUICK START SCRIPT - Inicio rápido del entorno de desarrollo
# ================================================================================================

set -e  # Exit on error

echo "================================================================================"
echo "🚀 M2PRD-001 SaaS - Quick Start Development Environment"
echo "================================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ================================================================================================
# 🔍 CHECK PREREQUISITES
# ================================================================================================

echo -e "${BLUE}🔍 Checking prerequisites...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 found:${NC} $(python3 --version)"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found${NC}"
    echo -e "${BLUE}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate venv
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"

# Check .env file
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    if [ -f "backend/.env.example" ]; then
        echo -e "${BLUE}📋 Copying .env.example to .env...${NC}"
        cp backend/.env.example backend/.env
        echo -e "${GREEN}✅ .env file created${NC}"
        echo -e "${YELLOW}💡 IMPORTANT: Edit backend/.env and configure your settings${NC}"
    else
        echo -e "${RED}❌ .env.example not found${NC}"
        exit 1
    fi
fi

# Install dependencies
echo ""
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r backend/requirements.txt 2>/dev/null || {
    echo -e "${RED}❌ Error installing dependencies${NC}"
    echo -e "${YELLOW}💡 Creating requirements.txt...${NC}"
    cat > backend/requirements.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
httpx==0.25.2
python-multipart==0.0.6
EOF
    pip install -q -r backend/requirements.txt
}
echo -e "${GREEN}✅ Dependencies installed${NC}"

# ================================================================================================
# 🏗️ DISPLAY CONFIGURATION
# ================================================================================================

echo ""
echo "================================================================================"
echo "⚙️  CONFIGURATION STATUS"
echo "================================================================================"

# Check environment variables
if grep -q "N8N_WEBHOOK_URL=\"\"" backend/.env 2>/dev/null || ! grep -q "N8N_WEBHOOK_URL" backend/.env 2>/dev/null; then
    echo -e "${YELLOW}⚠️  N8N_WEBHOOK_URL not configured${NC}"
    echo -e "${BLUE}   Will use mock n8n server${NC}"
    USE_MOCK_N8N=true
else
    echo -e "${GREEN}✅ N8N_WEBHOOK_URL configured${NC}"
    USE_MOCK_N8N=false
fi

# ================================================================================================
# 🚀 START SERVICES
# ================================================================================================

echo ""
echo "================================================================================"
echo "🚀 STARTING SERVICES"
echo "================================================================================"
echo ""

# Function to start service in background
start_service() {
    local name=$1
    local command=$2
    local port=$3
    local log_file=$4
    
    echo -e "${BLUE}🔄 Starting $name on port $port...${NC}"
    $command > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "/tmp/m2prd_${name}.pid"
    
    # Wait for service to be ready
    sleep 2
    
    if kill -0 $pid 2>/dev/null; then
        echo -e "${GREEN}✅ $name started (PID: $pid)${NC}"
        echo -e "${BLUE}   Logs: $log_file${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to start $name${NC}"
        cat "$log_file"
        return 1
    fi
}

# Create logs directory
mkdir -p logs

# Start Mock n8n Server (if needed)
if [ "$USE_MOCK_N8N" = true ]; then
    echo ""
    start_service "Mock n8n Server" \
        "python backend/tests/mocks/mock_n8n_server.py" \
        "5678" \
        "logs/mock_n8n.log"
    
    # Update .env to use mock server
    if ! grep -q "N8N_WEBHOOK_URL=\"http://localhost:5678" backend/.env 2>/dev/null; then
        sed -i 's|N8N_WEBHOOK_URL=""|N8N_WEBHOOK_URL="http://localhost:5678/webhook/process-meeting"|' backend/.env 2>/dev/null || true
    fi
fi

# Start Gatekeeper Backend
echo ""
start_service "Gatekeeper Backend" \
    "uvicorn backend.app.main:app --host 0.0.0.0 --port 8002" \
    "8002" \
    "logs/gatekeeper.log"

# ================================================================================================
# 📊 DISPLAY SUMMARY
# ================================================================================================

echo ""
echo "================================================================================"
echo "✅ DEVELOPMENT ENVIRONMENT READY"
echo "================================================================================"
echo ""
echo -e "${GREEN}🎉 All services are running!${NC}"
echo ""
echo "📍 Service URLs:"
echo ""
if [ "$USE_MOCK_N8N" = true ]; then
    echo -e "   🧪 Mock n8n Server:     http://localhost:5678"
    echo -e "      Webhook endpoint:    http://localhost:5678/webhook/process-meeting"
    echo -e "      Health check:        http://localhost:5678/health"
    echo ""
fi
echo -e "   💰 Gatekeeper Backend:  http://localhost:8002"
echo -e "      API Docs:            http://localhost:8002/docs"
echo -e "      Health check:        http://localhost:8002/health"
echo ""
echo "📊 Logs:"
echo ""
if [ "$USE_MOCK_N8N" = true ]; then
    echo -e "   Mock n8n:            logs/mock_n8n.log"
fi
echo -e "   Gatekeeper:          logs/gatekeeper.log"
echo ""
echo "🛑 To stop all services:"
echo -e "   ${BLUE}./scripts/stop_dev.sh${NC}"
echo ""
echo "📖 Next steps:"
echo ""
echo -e "   1. Open API docs: ${BLUE}http://localhost:8002/docs${NC}"
echo -e "   2. Test webhook trigger: Send POST to /api/v1/consumption/process/start"
if [ "$USE_MOCK_N8N" = true ]; then
    echo -e "   3. Watch mock n8n logs: ${BLUE}tail -f logs/mock_n8n.log${NC}"
fi
echo -e "   4. Run tests: ${BLUE}pytest backend/tests/ -v${NC}"
echo ""
echo "================================================================================"

# Keep script running and show logs
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

trap 'echo ""; echo "Stopping services..."; ./scripts/stop_dev.sh; exit 0' INT TERM

# Tail logs
tail -f logs/gatekeeper.log
