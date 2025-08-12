#!/bin/bash
# Marketing Agent API Startup Script
# Convenient script to start the API server with proper configuration

set -e  # Exit on any error

echo "🚀 Starting Marketing Agent API Server"
echo "========================================"

# Check if we're in the API directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Error: Must run this script from the API directory"
    echo "   cd API && ./start.sh"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not installed"
    exit 1
fi

# Check if requirements are installed
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "   ✅ Created .env file"
        echo "   ⚠️  Please edit .env and add your OPENAI_API_KEY"
    else
        echo "   ⚠️  No .env.example found. Please create .env manually"
    fi
fi

# Check for OpenAI API key
if [ -f ".env" ]; then
    source .env
    if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "sk-your-openai-api-key-here" ]; then
        echo "⚠️  Warning: OPENAI_API_KEY not set in .env file"
        echo "   The API will not work without a valid OpenAI API key"
        echo "   Please edit .env and set your OpenAI API key"
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

# Create storage directory
mkdir -p storage
echo "📁 Storage directory ready: ./storage"

# Set default environment variables
export API_HOST=${API_HOST:-"0.0.0.0"}
export API_PORT=${API_PORT:-8000}
export DEBUG=${DEBUG:-"true"}
export RELOAD=${RELOAD:-"true"}
export LOG_LEVEL=${LOG_LEVEL:-"INFO"}

echo ""
echo "🔧 Configuration:"
echo "   Host: $API_HOST"
echo "   Port: $API_PORT"
echo "   Debug: $DEBUG"
echo "   Reload: $RELOAD"
echo "   Log Level: $LOG_LEVEL"
echo ""

# Check if port is available
if lsof -Pi :$API_PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Warning: Port $API_PORT is already in use"
    echo "   Another process might be running on this port"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "🚀 Starting server..."
echo "   API Documentation: http://localhost:$API_PORT/docs"
echo "   API Status: http://localhost:$API_PORT/api/v1/health"
echo "   Stop server: Ctrl+C"
echo ""

# Start the server
if [ "$RELOAD" = "true" ]; then
    # Development mode with auto-reload
    exec uvicorn app.main:app \
        --host "$API_HOST" \
        --port "$API_PORT" \
        --reload \
        --log-level "$LOG_LEVEL"
else
    # Production mode
    exec uvicorn app.main:app \
        --host "$API_HOST" \
        --port "$API_PORT" \
        --log-level "$LOG_LEVEL" \
        --workers 4
fi
