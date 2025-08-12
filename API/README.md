# 🚀 Marketing Agent API

FastAPI-based web service that wraps the Marketing Chat Agent for public consumption.

## 🎯 Features

- **Async Processing**: Handle long-running campaign generation (25-30s) without blocking
- **Real-time Updates**: WebSocket support for live progress tracking  
- **Task Management**: Background job processing with status tracking
- **File Delivery**: Generated images, emails, and social posts via secure URLs
- **Rate Limiting**: Built-in protection against abuse
- **Auto Documentation**: Swagger/OpenAPI docs at `/docs`

## 🏗️ Architecture

```
FastAPI Server → Background Tasks → Marketing Agent → File Storage → Response
     ↓                ↓                    ↓               ↓
  REST API      Task Queue         LangGraph Flow    Generated Assets
```

## 📡 API Endpoints

### Campaign Management
- `POST /api/v1/campaigns` - Create new marketing campaign
- `GET /api/v1/campaigns/{id}` - Get campaign details and results
- `GET /api/v1/campaigns/{id}/status` - Check processing status
- `GET /api/v1/campaigns/{id}/files/{filename}` - Download generated files
- `WebSocket /api/v1/campaigns/{id}/stream` - Real-time progress updates

### Service Management  
- `GET /api/v1/health` - Health check endpoint
- `GET /api/v1/status` - Service status and metrics
- `GET /docs` - Interactive API documentation

## 🚀 Quick Start

```bash
# Install dependencies
cd API
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your OpenAI API key

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access documentation
open http://localhost:8000/docs
```

## 📊 Usage Example

```python
import requests

# Create campaign
response = requests.post("http://localhost:8000/api/v1/campaigns", json={
    "user_input": "promote fitness tracker on instagram email for health enthusiasts",
    "options": {
        "channels": ["instagram", "email"],
        "include_images": True,
        "dry_run": False
    }
})

campaign_id = response.json()["campaign_id"]

# Check status
status = requests.get(f"http://localhost:8000/api/v1/campaigns/{campaign_id}/status")
print(f"Progress: {status.json()['progress']['percentage']}%")

# Get final results  
results = requests.get(f"http://localhost:8000/api/v1/campaigns/{campaign_id}")
print("Campaign completed:", results.json())
```

## 🔐 Authentication

API uses simple API key authentication:

```python
headers = {"X-API-Key": "your-api-key-here"}
requests.post("http://localhost:8000/api/v1/campaigns", headers=headers, json=data)
```

## 📁 Project Structure

```
API/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── routes/              # API endpoint definitions
│   │   ├── campaigns.py     # Campaign management endpoints
│   │   ├── health.py        # Health check endpoints
│   │   └── websockets.py    # WebSocket endpoints
│   ├── models/              # Pydantic request/response models
│   │   ├── campaign.py      # Campaign data models
│   │   └── responses.py     # API response models
│   ├── services/            # Business logic services
│   │   ├── campaign_service.py  # Campaign processing logic
│   │   ├── task_manager.py     # Background task management
│   │   └── file_service.py     # File handling and serving
│   ├── utils/               # Utility functions
│   │   ├── auth.py          # Authentication helpers
│   │   ├── config.py        # Configuration management
│   │   └── logging.py       # Logging setup
│   └── storage/             # Generated files storage
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
├── docker-compose.yml      # Multi-service setup
└── .env.example           # Environment variables template
```

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build individual container
docker build -t marketing-api .
docker run -p 8000:8000 marketing-api
```

## 📈 Monitoring & Scaling

- **Health Checks**: `/api/v1/health` endpoint for load balancer checks
- **Metrics**: Built-in request/response time tracking
- **Logging**: Structured logging for production monitoring
- **Horizontal Scaling**: Stateless design allows multiple instances
- **Background Workers**: Separate worker processes for campaign generation

## 🔧 Configuration

Key environment variables:

```bash
# Core Settings
OPENAI_API_KEY=sk-your-openai-key
API_HOST=0.0.0.0
API_PORT=8000

# Security
API_KEY_HEADER=X-API-Key
ALLOWED_ORIGINS=*
RATE_LIMIT_PER_MINUTE=60

# Storage
FILE_STORAGE_PATH=./storage
FILE_URL_PREFIX=http://localhost:8000/api/v1/campaigns

# Background Processing  
MAX_CONCURRENT_CAMPAIGNS=5
CAMPAIGN_TIMEOUT_SECONDS=300
```
