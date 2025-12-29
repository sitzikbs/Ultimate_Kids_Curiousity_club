# API Documentation

## Ultimate Kids Curiosity Club Dashboard API

This document provides comprehensive documentation for the REST API and WebSocket endpoints of the Ultimate Kids Curiosity Club dashboard backend.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required for local development. Future versions may include API key or OAuth authentication.

## API Endpoints

### Health Check

#### GET /health

Check the health status of the API server.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

---

## Show Endpoints

### List All Shows

#### GET /api/shows

Retrieve a list of all available shows.

**Response:**
```json
[
  {
    "show_id": "oliver",
    "title": "Oliver's STEM Adventures",
    "description": "Explore the amazing world of inventions and STEM!",
    "theme": "STEM education through hands-on invention and problem-solving",
    "created_at": "2024-01-15T10:00:00Z"
  }
]
```

**Example:**
```bash
curl http://localhost:8000/api/shows
```

---

### Get Show Details

#### GET /api/shows/{show_id}

Retrieve complete blueprint details for a specific show.

**Path Parameters:**
- `show_id` (string): Unique identifier for the show

**Response:**
```json
{
  "show": {
    "show_id": "oliver",
    "title": "Oliver's STEM Adventures",
    "description": "Explore the amazing world of inventions and STEM!",
    "theme": "STEM education",
    "narrator_voice_config": {
      "provider": "mock",
      "voice_id": "mock_narrator"
    },
    "created_at": "2024-01-15T10:00:00Z"
  },
  "protagonist": {
    "name": "Oliver the Inventor",
    "age": 8,
    "description": "An energetic 8-year-old boy...",
    "values": ["curiosity", "creativity", "persistence"],
    "catchphrases": ["Let's figure it out!", "Gizmos ready!"],
    "backstory": "To understand how things work...",
    "image_path": null,
    "voice_config": {
      "provider": "mock",
      "voice_id": "mock_oliver"
    }
  },
  "world": {
    "setting": "A friendly suburban town...",
    "rules": [
      "No magic — solutions come from curiosity and experimentation."
    ],
    "atmosphere": "Creative, experimental, and encouraging",
    "locations": []
  },
  "characters": [],
  "concepts_history": {
    "concepts": [],
    "last_updated": "2024-01-15T10:00:00Z"
  },
  "episodes": []
}
```

**Example:**
```bash
curl http://localhost:8000/api/shows/oliver
```

---

### Update Show Blueprint

#### PUT /api/shows/{show_id}

Update the protagonist or world description for a show.

**Path Parameters:**
- `show_id` (string): Unique identifier for the show

**Request Body:**
```json
{
  "protagonist": {
    "name": "Oliver the Inventor",
    "age": 9,
    "description": "Updated description",
    "values": ["curiosity", "creativity"],
    "voice_config": {
      "provider": "mock",
      "voice_id": "mock_oliver"
    }
  },
  "world": {
    "setting": "Updated setting",
    "rules": ["Updated rule"],
    "atmosphere": "Updated atmosphere"
  }
}
```

**Note:** Both `protagonist` and `world` are optional. Include only what you want to update.

**Response:** Returns the updated show blueprint (same format as GET /api/shows/{show_id})

**Example:**
```bash
curl -X PUT http://localhost:8000/api/shows/oliver \
  -H "Content-Type: application/json" \
  -d '{
    "protagonist": {
      "name": "Oliver the Inventor",
      "age": 9,
      "description": "An energetic boy",
      "values": ["curiosity"],
      "voice_config": {"provider": "mock", "voice_id": "oliver"}
    }
  }'
```

---

## Episode Endpoints

### List Episodes for a Show

#### GET /api/shows/{show_id}/episodes

Retrieve all episodes for a specific show.

**Path Parameters:**
- `show_id` (string): Unique identifier for the show

**Response:**
```json
[
  {
    "episode_id": "ep001_rockets",
    "show_id": "oliver",
    "topic": "How Rockets Work",
    "title": "Blast Off!",
    "current_stage": "APPROVED",
    "approval_status": "approved",
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T11:00:00Z"
  }
]
```

**Example:**
```bash
curl http://localhost:8000/api/shows/oliver/episodes
```

---

### Get Episode Details

#### GET /api/episodes/{episode_id}

Retrieve complete details for a specific episode, including outline and scripts.

**Path Parameters:**
- `episode_id` (string): Unique identifier for the episode

**Response:**
```json
{
  "episode_id": "ep001_rockets",
  "show_id": "oliver",
  "topic": "How Rockets Work",
  "title": "Blast Off!",
  "current_stage": "APPROVED",
  "approval_status": "approved",
  "approval_feedback": "Great episode!",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T11:00:00Z",
  "outline": {
    "hook": "Oliver discovers a toy rocket...",
    "discovery": "He learns about Newton's laws...",
    "challenge": "Building his own rocket...",
    "resolution": "Successful launch!",
    "lesson_learned": "Action and reaction...",
    "key_moments": ["Discovery", "Building", "Launch"],
    "educational_concepts": ["Newton's Third Law"],
    "age_appropriate_notes": "Uses simple analogies"
  },
  "segments": [],
  "scripts": [],
  "audio_path": null
}
```

**Example:**
```bash
curl http://localhost:8000/api/episodes/ep001_rockets
```

---

### Update Episode Outline

#### PUT /api/episodes/{episode_id}/outline

Update the story outline for an episode.

**Path Parameters:**
- `episode_id` (string): Unique identifier for the episode

**Request Body:**
```json
{
  "outline": {
    "hook": "Oliver discovers a toy rocket...",
    "discovery": "He learns about Newton's laws...",
    "challenge": "Building his own rocket...",
    "resolution": "Successful launch!",
    "lesson_learned": "Action and reaction...",
    "key_moments": ["Discovery", "Building", "Launch"],
    "educational_concepts": ["Newton's Third Law"],
    "age_appropriate_notes": "Uses simple analogies"
  }
}
```

**Response:** Returns the updated episode details

**Example:**
```bash
curl -X PUT http://localhost:8000/api/episodes/ep001_rockets/outline \
  -H "Content-Type: application/json" \
  -d '{
    "outline": {
      "hook": "Updated hook...",
      "discovery": "Updated discovery...",
      "challenge": "Updated challenge...",
      "resolution": "Updated resolution...",
      "lesson_learned": "Updated lesson...",
      "key_moments": ["Moment 1"],
      "educational_concepts": ["Concept 1"],
      "age_appropriate_notes": "Updated notes"
    }
  }'
```

---

### Approve/Reject Episode

#### POST /api/episodes/{episode_id}/approve

Approve or reject an episode outline for production.

**Path Parameters:**
- `episode_id` (string): Unique identifier for the episode

**Request Body:**
```json
{
  "approved": true,
  "feedback": "Great episode! Ready for production."
}
```

**Response:** Returns the updated episode details with new approval status

**Example - Approve:**
```bash
curl -X POST http://localhost:8000/api/episodes/ep001_rockets/approve \
  -H "Content-Type: application/json" \
  -d '{
    "approved": true,
    "feedback": "Excellent episode!"
  }'
```

**Example - Reject:**
```bash
curl -X POST http://localhost:8000/api/episodes/ep001_rockets/approve \
  -H "Content-Type: application/json" \
  -d '{
    "approved": false,
    "feedback": "Needs more educational content."
  }'
```

---

## WebSocket Endpoint

### Real-Time Updates

#### WS /ws

Connect to receive real-time updates about episode status changes and progress.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected to WebSocket');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};
```

**Event Types:**

1. **episode_status_changed**
   ```json
   {
     "event_type": "episode_status_changed",
     "data": {
       "episode_id": "ep001_rockets",
       "show_id": "oliver",
       "old_stage": "PENDING",
       "new_stage": "APPROVED"
     },
     "timestamp": "2024-01-15T11:00:00Z"
   }
   ```

2. **progress_update**
   ```json
   {
     "event_type": "progress_update",
     "data": {
       "episode_id": "ep001_rockets",
       "show_id": "oliver",
       "stage": "AUDIO_SYNTHESIS",
       "progress": 75.0,
       "message": "Generating audio..."
     },
     "timestamp": "2024-01-15T11:05:00Z"
   }
   ```

3. **ping** (Heartbeat)
   ```json
   {
     "event_type": "ping",
     "timestamp": "2024-01-15T11:00:30Z"
   }
   ```

**Client Response to Ping:**
```javascript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.event_type === 'ping') {
    // Respond with pong
    ws.send(JSON.stringify({ event_type: 'pong' }));
  }
};
```

---

## Auto-Generated Documentation

The API also provides auto-generated interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Error Responses

The API uses standard HTTP status codes:

- **200 OK**: Request succeeded
- **400 Bad Request**: Invalid request data
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

**Error Response Format:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Running the API Server

### Development Mode

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the server with hot reload
python -m api.main

# Or use uvicorn directly
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
# Set reload to false in .env or environment variable
export API_RELOAD=false

# Run with uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Configuration

The API can be configured via environment variables (prefixed with `API_`):

```bash
# Server settings
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# CORS settings
API_CORS_ORIGINS=["http://localhost:3000", "*"]
API_CORS_CREDENTIALS=true

# Static files
API_WEBSITE_DIR=website

# WebSocket
API_WS_HEARTBEAT_INTERVAL=30
```

---

## Testing

Run the API tests:

```bash
# Run all API tests
pytest tests/api/

# Run specific test file
pytest tests/api/test_routes.py

# Run with coverage
pytest tests/api/ --cov=api --cov-report=html
```

---

## Rate Limiting

Currently, no rate limiting is implemented. Future versions may include:
- Per-IP rate limiting
- API key-based quotas
- WebSocket connection limits

---

## CORS Configuration

By default, CORS is configured to allow:
- Origins: `http://localhost:3000`, `http://localhost:8000`, and all origins (`*`)
- Credentials: Enabled
- Methods: All methods
- Headers: All headers

Adjust these settings in `src/api/config.py` or via environment variables for production use.
