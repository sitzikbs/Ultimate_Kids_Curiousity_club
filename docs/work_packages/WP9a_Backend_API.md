# WP9a: Dashboard Backend & API

**Parent WP**: WP9 (Web Dashboard)  
**Status**: ⏳ Not Started  
**Dependencies**: WP1 (Foundation), WP1c (Blueprint Manager)  
**Estimated Effort**: 1.5-2 days  
**Owner**: TBD  
**Subsystem:** User Interface

## 📋 Overview

Build the backend foundation for the web dashboard: FastAPI server with REST endpoints, WebSocket support for real-time updates, and static file serving. This provides the API layer that the frontend will consume.

**Key Deliverables**:
- FastAPI application with CORS support
- REST endpoints for show/episode data
- WebSocket endpoint for real-time updates
- Static file serving for HTML/CSS/JS
- API documentation (auto-generated)

## 🎯 High-Level Tasks

### Task 9a.1: Backend Setup
Set up FastAPI server with middleware and configuration.

**Subtasks**:
- [ ] 9a.1.1: Create `src/api/` directory structure
- [ ] 9a.1.2: Initialize FastAPI app with CORS middleware
- [ ] 9a.1.3: Add Uvicorn configuration for hot reload
- [ ] 9a.1.4: Configure static file serving from `website/` directory
- [ ] 9a.1.5: Add health check endpoint `/health`
- [ ] 9a.1.6: Add API documentation at `/docs` (auto-generated)

**Expected Outputs**:
- `src/api/main.py` with FastAPI app
- `src/api/config.py` with server settings
- Health check and docs endpoints working

### Task 9a.2: Show & Episode REST Endpoints
Create API routes for show and episode data retrieval.

**Subtasks**:
- [ ] 9a.2.1: Create `GET /api/shows` - List all shows
- [ ] 9a.2.2: Create `GET /api/shows/{show_id}` - Show Blueprint details
- [ ] 9a.2.3: Create `PUT /api/shows/{show_id}` - Update Show Blueprint
- [ ] 9a.2.4: Create `GET /api/shows/{show_id}/episodes` - List episodes
- [ ] 9a.2.5: Create `GET /api/episodes/{episode_id}` - Episode details
- [ ] 9a.2.6: Create `PUT /api/episodes/{episode_id}/outline` - Update outline
- [ ] 9a.2.7: Create `POST /api/episodes/{episode_id}/approve` - Approve/reject outline

**Expected Outputs**:
- `src/api/routes/shows.py` with show endpoints
- `src/api/routes/episodes.py` with episode endpoints
- Pydantic models for request/response validation

### Task 9a.3: WebSocket for Real-Time Updates
Implement WebSocket endpoint for live pipeline status updates.

**Subtasks**:
- [ ] 9a.3.1: Create WebSocket endpoint `/ws`
- [ ] 9a.3.2: Implement connection manager for multiple clients
- [ ] 9a.3.3: Add event broadcasting system
- [ ] 9a.3.4: Integrate with episode status changes
- [ ] 9a.3.5: Add heartbeat/ping-pong for connection health

**Expected Outputs**:
- `src/api/websocket.py` with WebSocket handler
- Event types: `episode_status_changed`, `progress_update`
- Connection pooling for multiple clients

### Task 9a.4: Testing & Documentation
Test API endpoints and document usage.

**Subtasks**:
- [ ] 9a.4.1: Write unit tests for all endpoints
- [ ] 9a.4.2: Write WebSocket client test
- [ ] 9a.4.3: Add integration tests with ShowBlueprintManager
- [ ] 9a.4.4: Document API usage in README
- [ ] 9a.4.5: Add example curl commands

**Expected Outputs**:
- `tests/api/test_routes.py` with endpoint tests
- `tests/api/test_websocket.py` with WS tests
- `docs/API.md` with usage examples

## 🧪 Testing Strategy

- **Unit Tests**: Mocked ShowBlueprintManager and EpisodeStorage
- **Integration Tests**: Real file I/O with test fixtures
- **WebSocket Tests**: Multiple client connections
- **Load Tests**: Concurrent request handling

## ✅ Definition of Done

- [ ] All endpoints return correct status codes
- [ ] WebSocket broadcasts events correctly
- [ ] API documentation auto-generated at `/docs`
- [ ] All tests passing (>90% coverage)
- [ ] No CORS errors when accessing from browser
- [ ] Static files served correctly

## 🔗 Related Work Packages

- **WP1c**: Provides ShowBlueprintManager for data access
- **WP9b**: Frontend will consume these APIs
- **WP9c**: Will extend with approval workflow endpoints
