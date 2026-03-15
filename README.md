# SHOP-BY-INTENTION FastAPI Interface

A REST API interface for the SHOP-BY-INTENTION AI shopping assistant system.

## 🚀 Quick Start

### 1. Install API Dependencies

```bash
# Install FastAPI and related dependencies
pip install fastapi uvicorn[standard] pydantic python-multipart
```

### 2. Start the API Server

```bash
# From the project root directory
python api/run_server.py
```

The server will start on `http://localhost:8000`

### 3. Access the Interface

- **Web Interface**: [http://localhost:8000/](http://localhost:8000/)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Interactive API**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## 📋 API Endpoints

### POST /api/shop
Process a shopping query through the agentic system.

**Request Body:**
```json
{
  "query": "I want a gaming laptop under $1500",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "user_query": "I want a gaming laptop under $1500",
  "final_intent": {
    "category": "laptop",
    "purpose": "gaming", 
    "budget": 1500,
    "preferences": [],
    "uncertainty": null
  },
  "final_cart": {
    "items": [...],
    "total_cost": 1200.0,
    "is_stable": true
  },
  "loop_count": 3,
  "processing_time": 15.23,
  "timestamp": "2026-03-14T12:00:00"
}
```

### GET /api/status
Get system status and component health.

**Response:**
```json
{
  "status": "operational",
  "timestamp": "2026-03-14T12:00:00",
  "uptime": "3600 seconds",
  "version": "1.0.0",
  "components": {
    "intent_agent": "operational",
    "retrieval_agent": "operational",
    "reasoning_agent": "operational",
    "cart_agent": "operational",
    "evaluation_agent": "operational",
    "loop_controller": "operational",
    "event_logger": "operational"
  }
}
```

### GET /api/events
Get event logs and statistics.

**Query Parameters:**
- `event_type` (optional): Filter by event type

**Response:**
```json
{
  "events": [...],
  "statistics": {
    "total_events": 150,
    "event_types": {...},
    "agents": {...},
    "time_range": {...}
  },
  "total_events": 150
}
```

### GET /api/events/types
Get all available event types.

### POST /api/benchmark
Run benchmark tests.

**Request Body (optional):**
```json
{
  "queries": ["query 1", "query 2", ...]
}
```

**Example Request Body:**
```json
{
  "queries": [
    "I want a tablet for digital art with an AMOLED screen",
    "I need an easy to use camera for photography",
    "I need a pair of lightweight headphones for travel with industry-leading ANC"
  ]
}
```

### GET /api/health
Simple health check endpoint.

## 🌐 Web Interface

The web interface provides an easy-to-use form for testing the shopping assistant:

1. **Enter your query** in the input field
2. **Click Search** to process the query
3. **View results** including:
   - Detected intent (category, purpose, budget, preferences)
   - Recommended products with details
   - Processing information (loops, time, etc.)

### Example Queries to Try:
- "I want a gaming laptop under $1500"
- "I need a cheap camera for photography"
- "I want a portable coding laptop"
- "Build a home office setup under $1000"

## 🔧 Development

### Running the Server Manually

```bash
# Start with uvicorn directly
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Or with Python
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Adding New Endpoints

1. Add the endpoint function in `api/main.py`
2. Use FastAPI decorators (`@app.get`, `@app.post`, etc.)
3. Define request/response models using Pydantic
4. Add proper error handling

### CORS Configuration

The API is configured to allow all origins for development. In production, update the CORS settings in `api/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Replace with your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📊 Monitoring

### Event Logs
The system logs all agentic events to `data/event_logs.jsonl`. You can access these through the `/api/events` endpoint.

### Performance Metrics
Each API response includes processing time and loop count information to help monitor system performance.

## 🔒 Security

- Input validation using Pydantic models
- Error handling to prevent information leakage
- CORS configuration for cross-origin requests
- Rate limiting can be added using FastAPI middleware

## 🚨 Troubleshooting

### Server Won't Start
1. Check that all dependencies are installed
2. Verify the conda environment is activated
3. Check that port 8000 is not in use

### API Requests Fail
1. Ensure the main SHOP-BY-INTENTION system is working
2. Check the Groq API key is configured
3. Verify the product catalog is loaded

### Frontend Not Loading
1. Check that the API server is running
2. Verify CORS settings if accessing from different domain
3. Check browser console for JavaScript errors

## 📝 License

This API interface is part of the SHOP-BY-INTENTION system.