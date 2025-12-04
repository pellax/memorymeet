#!/bin/bash
# ================================================================================================
# 🛑 STOP SCRIPT - Detiene todos los servicios de desarrollo
# ================================================================================================

echo "================================================================================"
echo "🛑 Stopping M2PRD-001 Development Services"
echo "================================================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to stop service
stop_service() {
    local name=$1
    local pid_file="/tmp/m2prd_${name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 $pid 2>/dev/null; then
            echo -e "${BLUE}🛑 Stopping $name (PID: $pid)...${NC}"
            kill $pid 2>/dev/null
            sleep 1
            if kill -0 $pid 2>/dev/null; then
                echo -e "${RED}   Force killing $name...${NC}"
                kill -9 $pid 2>/dev/null
            fi
            echo -e "${GREEN}✅ $name stopped${NC}"
        else
            echo -e "${BLUE}   $name not running${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${BLUE}   $name PID file not found${NC}"
    fi
}

# Stop services
stop_service "Mock n8n Server"
stop_service "Gatekeeper Backend"

# Clean up any remaining processes
echo ""
echo -e "${BLUE}🧹 Cleaning up...${NC}"

# Kill any remaining uvicorn processes on our ports
lsof -ti:8002 | xargs kill -9 2>/dev/null || true
lsof -ti:5678 | xargs kill -9 2>/dev/null || true

echo -e "${GREEN}✅ All services stopped${NC}"
echo ""
echo "================================================================================"
