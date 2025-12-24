# WP9: Web Dashboard & Review Interface

**Status:** 🔴 Not Started  
**Owner:** Unassigned  
**Estimated Effort:** 7-10 days  
**GitHub Issue:** TBD

## 📋 Overview

Build a web-based dashboard for human review of story outlines and scripts, Show Blueprint management, and pipeline monitoring. This enables the critical **human approval gate** in the story generation workflow and provides a central interface for managing show data.

### Purpose
Enable human oversight and creative control in the episode generation pipeline through an intuitive web interface.

### Dependencies
- **WP1:** Foundation (data models)
- **WP6:** Pipeline Orchestrator (state management, approval workflow)
- **WP5:** Image Service (image upload/display for Show Blueprint)

### Blocks
- None (enhances existing CLI workflow)

---

## 🎯 Success Criteria

1. ✅ Human can review and approve/reject story outlines
2. ✅ Human can edit Show Blueprint (protagonist, world, characters) with image support
3. ✅ Real-time pipeline status updates via WebSocket
4. ✅ Script editor with audio preview
5. ✅ ConceptsHistory viewer shows covered topics
6. ✅ Multi-show support (switch between shows)
7. ✅ Responsive UI (desktop + tablet)

---

## 📐 Technical Architecture

### Stack Selection
- **Backend:** FastAPI (Python) - REST + WebSocket
- **Frontend:** React or Vue.js (TBD based on team preference)
- **State Management:** Redux/Pinia or Context API
- **UI Components:** shadcn/ui or Vuetify
- **Code Editor:** Monaco Editor (VS Code-style)
- **Image Upload:** Direct upload with preview

### Architecture Diagram

```
┌─────────────────────────────────────────┐
│          Frontend (React/Vue)           │
│  - Show Blueprint Editor                │
│  - Outline Approval Interface           │
│  - Script Editor                        │
│  - Pipeline Dashboard                   │
└────────────┬────────────────────────────┘
             │ HTTP + WebSocket
┌────────────┴────────────────────────────┐
│         FastAPI Backend                 │
│  - REST API (CRUD operations)           │
│  - WebSocket (real-time updates)        │
│  - File uploads (images)                │
└────────────┬────────────────────────────┘
             │
┌────────────┴────────────────────────────┐
│    Existing Services (from WP1, WP6)    │
│  - ShowBlueprintManager                 │
│  - PipelineOrchestrator                 │
│  - ImageService                         │
└─────────────────────────────────────────┘
```

---

## 🗂️ Directory Structure

```
src/dashboard/
├── backend/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── shows.py               # Show Blueprint CRUD
│   │   ├── episodes.py            # Episode management
│   │   ├── pipeline.py            # Pipeline control
│   │   └── websocket.py           # Real-time updates
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── show.py                # Pydantic schemas
│   │   ├── episode.py
│   │   └── pipeline.py
│   └── services/
│       ├── __init__.py
│       ├── show_service.py        # Business logic
│       ├── episode_service.py
│       └── pipeline_service.py
│
└── frontend/
    ├── public/
    │   └── index.html
    ├── src/
    │   ├── components/
    │   │   ├── ShowBlueprintEditor/
    │   │   │   ├── ProtagonistForm.tsx
    │   │   │   ├── WorldEditor.tsx
    │   │   │   ├── CharacterList.tsx
    │   │   │   └── ImageUploader.tsx
    │   │   ├── OutlineApproval/
    │   │   │   ├── OutlineViewer.tsx
    │   │   │   ├── BeatEditor.tsx
    │   │   │   └── ApprovalButtons.tsx
    │   │   ├── ScriptEditor/
    │   │   │   ├── CodeEditor.tsx
    │   │   │   └── AudioPreview.tsx
    │   │   └── PipelineDashboard/
    │   │       ├── StageProgress.tsx
    │   │       └── StatusIndicator.tsx
    │   ├── pages/
    │   │   ├── ShowsPage.tsx
    │   │   ├── EpisodesPage.tsx
    │   │   ├── OutlineReviewPage.tsx
    │   │   └── ShowBlueprintPage.tsx
    │   ├── hooks/
    │   │   ├── useWebSocket.ts
    │   │   └── useShowBlueprint.ts
    │   ├── api/
    │   │   └── client.ts              # API client
    │   ├── App.tsx
    │   └── main.tsx
    ├── package.json
    ├── vite.config.ts
    └── tsconfig.json
```

---

## ✅ Implementation Tasks

### Phase 1: Backend API (4 tasks)

#### Task 1.1: FastAPI Setup & Base Structure
**Effort:** 0.5 days

```python
# src/dashboard/backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import shows, episodes, pipeline, websocket

app = FastAPI(title="Kids Curiosity Club Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(shows.router, prefix="/api/shows", tags=["shows"])
app.include_router(episodes.router, prefix="/api/episodes", tags=["episodes"])
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["pipeline"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
```

**Acceptance Criteria:**
- FastAPI server runs on port 8000
- CORS configured for frontend
- Health check endpoint `/health` returns 200

---

#### Task 1.2: Show Blueprint API Endpoints
**Effort:** 1 day

```python
# src/dashboard/backend/routers/shows.py
from fastapi import APIRouter, UploadFile, File
from ..schemas.show import ShowResponse, ProtagonistUpdate, WorldUpdate
from ..services.show_service import ShowService

router = APIRouter()
show_service = ShowService()

@router.get("", response_model=list[ShowResponse])
async def list_shows():
    """Get all shows."""
    return show_service.list_shows()

@router.get("/{show_id}", response_model=ShowResponse)
async def get_show(show_id: str):
    """Get Show Blueprint details."""
    return show_service.get_show(show_id)

@router.patch("/{show_id}/protagonist")
async def update_protagonist(show_id: str, data: ProtagonistUpdate):
    """Update protagonist data."""
    return show_service.update_protagonist(show_id, data)

@router.post("/{show_id}/protagonist/image")
async def upload_protagonist_image(show_id: str, file: UploadFile = File(...)):
    """Upload protagonist image."""
    return await show_service.upload_protagonist_image(show_id, file)

@router.patch("/{show_id}/world")
async def update_world(show_id: str, data: WorldUpdate):
    """Update world description."""
    return show_service.update_world(show_id, data)

@router.get("/{show_id}/concepts")
async def get_concepts_history(show_id: str):
    """Get educational concepts already covered."""
    return show_service.get_concepts_history(show_id)

@router.get("/{show_id}/characters")
async def list_characters(show_id: str):
    """Get all supporting characters."""
    return show_service.list_characters(show_id)
```

**Acceptance Criteria:**
- GET `/api/shows` returns list of shows
- GET `/api/shows/{id}` returns full Show Blueprint
- PATCH `/api/shows/{id}/protagonist` updates protagonist data
- POST `/api/shows/{id}/protagonist/image` uploads and saves image
- GET `/api/shows/{id}/concepts` returns concepts_covered.json

---

#### Task 1.3: Episode & Outline API Endpoints
**Effort:** 1 day

```python
# src/dashboard/backend/routers/episodes.py
from fastapi import APIRouter
from ..schemas.episode import EpisodeResponse, OutlineApproval
from ..services.episode_service import EpisodeService

router = APIRouter()
episode_service = EpisodeService()

@router.get("", response_model=list[EpisodeResponse])
async def list_episodes(show_id: str | None = None):
    """List episodes, optionally filtered by show."""
    return episode_service.list_episodes(show_id)

@router.get("/{episode_id}", response_model=EpisodeResponse)
async def get_episode(episode_id: str):
    """Get episode details."""
    return episode_service.get_episode(episode_id)

@router.get("/{episode_id}/outline")
async def get_outline(episode_id: str):
    """Get story outline for review."""
    return episode_service.get_outline(episode_id)

@router.post("/{episode_id}/outline/approve")
async def approve_outline(episode_id: str, approval: OutlineApproval):
    """Approve or reject outline with optional edits."""
    return episode_service.process_approval(episode_id, approval)

@router.get("/{episode_id}/scripts")
async def get_scripts(episode_id: str):
    """Get generated scripts."""
    return episode_service.get_scripts(episode_id)
```

**Acceptance Criteria:**
- GET `/api/episodes?show_id=oliver` filters by show
- GET `/api/episodes/{id}/outline` returns YAML outline
- POST `/api/episodes/{id}/outline/approve` triggers pipeline continuation
- GET `/api/episodes/{id}/scripts` returns scripts with speaker tags

---

#### Task 1.4: WebSocket for Real-Time Updates
**Effort:** 1 day

```python
# src/dashboard/backend/routers/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import json

router = APIRouter()

# Connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, episode_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[episode_id] = websocket
    
    def disconnect(self, episode_id: str):
        self.active_connections.pop(episode_id, None)
    
    async def send_update(self, episode_id: str, message: dict):
        websocket = self.active_connections.get(episode_id)
        if websocket:
            await websocket.send_json(message)

manager = ConnectionManager()

@router.websocket("/pipeline/{episode_id}")
async def pipeline_updates(websocket: WebSocket, episode_id: str):
    """Stream real-time pipeline status updates."""
    await manager.connect(episode_id, websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(episode_id)

# Hook into PipelineOrchestrator to call manager.send_update()
```

**Acceptance Criteria:**
- WebSocket connects on `/ws/pipeline/{episode_id}`
- Sends JSON updates: `{"stage": "OUTLINING", "progress": 0.5, "status": "running"}`
- Handles disconnections gracefully
- PipelineOrchestrator broadcasts status changes

---

### Phase 2: Frontend Foundation (3 tasks)

#### Task 2.1: Project Setup & Routing
**Effort:** 0.5 days

```typescript
// src/dashboard/frontend/src/main.tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App'
import ShowsPage from './pages/ShowsPage'
import ShowBlueprintPage from './pages/ShowBlueprintPage'
import EpisodesPage from './pages/EpisodesPage'
import OutlineReviewPage from './pages/OutlineReviewPage'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<ShowsPage />} />
          <Route path="shows/:showId" element={<ShowBlueprintPage />} />
          <Route path="episodes" element={<EpisodesPage />} />
          <Route path="episodes/:episodeId/outline" element={<OutlineReviewPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
)
```

**Acceptance Criteria:**
- React + Vite project initialized
- React Router configured
- All pages accessible via URL

---

#### Task 2.2: API Client & WebSocket Hook
**Effort:** 1 day

```typescript
// src/dashboard/frontend/src/api/client.ts
const API_BASE = "http://localhost:8000/api";

export const api = {
  shows: {
    list: () => fetch(`${API_BASE}/shows`).then(r => r.json()),
    get: (id: string) => fetch(`${API_BASE}/shows/${id}`).then(r => r.json()),
    updateProtagonist: (id: string, data: any) =>
      fetch(`${API_BASE}/shows/${id}/protagonist`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      }),
    uploadImage: (id: string, file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return fetch(`${API_BASE}/shows/${id}/protagonist/image`, {
        method: "POST",
        body: formData,
      });
    },
  },
  episodes: {
    list: (showId?: string) =>
      fetch(`${API_BASE}/episodes${showId ? `?show_id=${showId}` : ""}`).then(r => r.json()),
    getOutline: (id: string) =>
      fetch(`${API_BASE}/episodes/${id}/outline`).then(r => r.json()),
    approveOutline: (id: string, approval: any) =>
      fetch(`${API_BASE}/episodes/${id}/outline/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(approval),
      }),
  },
};

// src/dashboard/frontend/src/hooks/useWebSocket.ts
import { useEffect, useState } from 'react';

interface PipelineUpdate {
  stage: string;
  progress: number;
  status: string;
}

export function useWebSocket(episodeId: string) {
  const [update, setUpdate] = useState<PipelineUpdate | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/pipeline/${episodeId}`);
    
    ws.onopen = () => setConnected(true);
    ws.onmessage = (event) => setUpdate(JSON.parse(event.data));
    ws.onclose = () => setConnected(false);
    
    return () => ws.close();
  }, [episodeId]);

  return { update, connected };
}
```

**Acceptance Criteria:**
- API client makes successful requests
- WebSocket hook connects and receives updates
- Type-safe API methods

---

#### Task 2.3: UI Component Library Setup
**Effort:** 0.5 days

Install and configure component library (shadcn/ui or Vuetify)

**Acceptance Criteria:**
- Button, Input, Card, Dialog components available
- Consistent theming applied
- Monaco Editor integrated for code editing

---

### Phase 3: Show Blueprint Editor (3 tasks)

#### Task 3.1: Protagonist Editor with Image Upload
**Effort:** 1 day

```typescript
// src/dashboard/frontend/src/components/ShowBlueprintEditor/ProtagonistForm.tsx
import { useState } from 'react';
import { api } from '../../api/client';

export function ProtagonistForm({ showId, protagonist }: Props) {
  const [name, setName] = useState(protagonist.name);
  const [description, setDescription] = useState(protagonist.description);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState(protagonist.image_path);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  const handleSave = async () => {
    await api.shows.updateProtagonist(showId, { name, description });
    if (imageFile) {
      await api.shows.uploadImage(showId, imageFile);
    }
  };

  return (
    <div className="protagonist-form">
      <input type="text" value={name} onChange={(e) => setName(e.target.value)} />
      <textarea value={description} onChange={(e) => setDescription(e.target.value)} />
      
      <div className="image-upload">
        <img src={imagePreview || '/placeholder.png'} alt="Protagonist" />
        <input type="file" accept="image/*" onChange={handleImageChange} />
      </div>
      
      <button onClick={handleSave}>Save Changes</button>
    </div>
  );
}
```

**Acceptance Criteria:**
- Form displays protagonist data
- Image upload with preview
- Saves changes to backend

---

#### Task 3.2: World Description Editor
**Effort:** 1 day

Markdown editor for world.md with image embedding support

**Acceptance Criteria:**
- Markdown preview rendered
- Can insert image paths
- Images display inline
- Saves to world.md

---

#### Task 3.3: Character List with Images
**Effort:** 1 day

Display supporting characters from `characters/` directory

**Acceptance Criteria:**
- Lists all characters with images
- Can add new character
- Can edit existing character
- Images upload and display

---

### Phase 4: Outline Approval Interface (3 tasks)

#### Task 4.1: Outline Viewer
**Effort:** 1 day

```typescript
// src/dashboard/frontend/src/components/OutlineApproval/OutlineViewer.tsx
export function OutlineViewer({ outline }: { outline: StoryOutline }) {
  return (
    <div className="outline-viewer">
      <h2>{outline.title}</h2>
      <p className="concept">{outline.educational_concept}</p>
      
      <div className="beats">
        {outline.story_beats.map((beat, idx) => (
          <div key={idx} className="beat">
            <h3>{beat.title}</h3>
            <p>{beat.description}</p>
            <ul>
              {beat.key_moments.map((moment, i) => (
                <li key={i}>{moment}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Acceptance Criteria:**
- Displays story beats clearly
- Shows educational concept
- Readable formatting

---

#### Task 4.2: Beat Editor (Optional Edits)
**Effort:** 1 day

Allow inline editing of story beats before approval

**Acceptance Criteria:**
- Click beat to edit
- Can modify title, description, key_moments
- Changes included in approval payload

---

#### Task 4.3: Approval Buttons & Workflow
**Effort:** 0.5 days

```typescript
export function ApprovalButtons({ episodeId, outline }: Props) {
  const [feedback, setFeedback] = useState("");

  const handleApprove = async () => {
    await api.episodes.approveOutline(episodeId, {
      approved: true,
      edited_outline: outline,
    });
    // Navigate to pipeline dashboard
  };

  const handleReject = async () => {
    await api.episodes.approveOutline(episodeId, {
      approved: false,
      feedback,
    });
  };

  return (
    <div className="approval-actions">
      <textarea 
        placeholder="Optional feedback..." 
        value={feedback} 
        onChange={(e) => setFeedback(e.target.value)} 
      />
      <button className="approve" onClick={handleApprove}>✓ Approve & Continue</button>
      <button className="reject" onClick={handleReject}>✗ Reject</button>
    </div>
  );
}
```

**Acceptance Criteria:**
- Approve button triggers pipeline continuation
- Reject button stops pipeline
- Feedback sent to backend
- UI updates after action

---

### Phase 5: Script Editor & Audio Preview (2 tasks)

#### Task 5.1: Script Editor with Monaco
**Effort:** 1 day

Code editor for viewing/editing generated scripts

**Acceptance Criteria:**
- Monaco Editor displays script
- Syntax highlighting for speaker tags
- Can edit and save changes

---

#### Task 5.2: Audio Preview Player
**Effort:** 1 day

Play generated audio segments

**Acceptance Criteria:**
- Lists audio segments
- Play/pause controls
- Shows speaker for each segment
- Can jump to specific segment

---

### Phase 6: Pipeline Dashboard (2 tasks)

#### Task 6.1: Stage Progress Indicator
**Effort:** 1 day

```typescript
// src/dashboard/frontend/src/components/PipelineDashboard/StageProgress.tsx
import { useWebSocket } from '../../hooks/useWebSocket';

export function StageProgress({ episodeId }: { episodeId: string }) {
  const { update, connected } = useWebSocket(episodeId);

  const stages = ["IDEATION", "OUTLINING", "APPROVAL", "SEGMENT", "SCRIPT", "AUDIO", "MIXING"];

  return (
    <div className="pipeline-progress">
      {stages.map((stage) => (
        <div 
          key={stage}
          className={`stage ${update?.stage === stage ? 'active' : ''}`}
        >
          {stage}
        </div>
      ))}
      {update && <div className="progress-bar" style={{ width: `${update.progress * 100}%` }} />}
    </div>
  );
}
```

**Acceptance Criteria:**
- Shows all pipeline stages
- Highlights current stage
- Updates in real-time via WebSocket

---

#### Task 6.2: Episode List with Status
**Effort:** 0.5 days

Table showing all episodes with current status

**Acceptance Criteria:**
- Lists episodes
- Shows status (pending_approval, in_progress, complete, failed)
- Click to view details
- Filter by show

---

### Phase 7: Testing & Polish (1 task)

#### Task 7.1: Integration Testing
**Effort:** 1 day

- E2E tests with Playwright
- API endpoint tests
- WebSocket connection tests
- Image upload tests

**Acceptance Criteria:**
- All critical flows tested
- No console errors
- Responsive on tablet/desktop

---

## 🧪 Testing Strategy

### Backend Tests
```python
# tests/dashboard/test_shows_api.py
def test_list_shows(client):
    response = client.get("/api/shows")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_upload_protagonist_image(client):
    with open("tests/fixtures/oliver.png", "rb") as f:
        response = client.post(
            "/api/shows/oliver/protagonist/image",
            files={"file": ("oliver.png", f, "image/png")}
        )
    assert response.status_code == 200
    assert "image_path" in response.json()
```

### Frontend Tests
```typescript
// tests/components/OutlineViewer.test.tsx
import { render, screen } from '@testing-library/react';
import { OutlineViewer } from '../src/components/OutlineApproval/OutlineViewer';

test('displays story beats', () => {
  const outline = { /* mock data */ };
  render(<OutlineViewer outline={outline} />);
  expect(screen.getByText(outline.story_beats[0].title)).toBeInTheDocument();
});
```

---

## 📊 Progress Tracking

| Phase | Task | Status | Owner |
|-------|------|--------|-------|
| **Phase 1: Backend** | | | |
| | FastAPI Setup | 🔴 Not Started | |
| | Show Blueprint API | 🔴 Not Started | |
| | Episode & Outline API | 🔴 Not Started | |
| | WebSocket | 🔴 Not Started | |
| **Phase 2: Frontend** | | | |
| | Project Setup | 🔴 Not Started | |
| | API Client | 🔴 Not Started | |
| | UI Components | 🔴 Not Started | |
| **Phase 3: Show Blueprint** | | | |
| | Protagonist Editor | 🔴 Not Started | |
| | World Editor | 🔴 Not Started | |
| | Character List | 🔴 Not Started | |
| **Phase 4: Outline Approval** | | | |
| | Outline Viewer | 🔴 Not Started | |
| | Beat Editor | 🔴 Not Started | |
| | Approval Buttons | 🔴 Not Started | |
| **Phase 5: Script & Audio** | | | |
| | Script Editor | 🔴 Not Started | |
| | Audio Preview | 🔴 Not Started | |
| **Phase 6: Pipeline Dashboard** | | | |
| | Stage Progress | 🔴 Not Started | |
| | Episode List | 🔴 Not Started | |
| **Phase 7: Testing** | | | |
| | Integration Tests | 🔴 Not Started | |

---

## 🔗 Integration Points

### With WP1 (Foundation)
```python
from src.foundation.show_blueprint import ShowBlueprintManager
from src.foundation.models import Show, Protagonist, Episode

# Dashboard backend uses these directly
show_manager = ShowBlueprintManager()
show = show_manager.load_show("oliver")
```

### With WP6 (Orchestrator)
```python
from src.orchestrator.pipeline import PipelineOrchestrator, PipelineStatus

# Dashboard triggers pipeline after approval
pipeline = PipelineOrchestrator()
await pipeline.resume_after_approval(episode_id, approved_outline)

# Dashboard listens to status updates
def on_status_change(episode_id: str, status: PipelineStatus):
    # Broadcast via WebSocket
    await websocket_manager.send_update(episode_id, status.dict())

pipeline.register_listener(on_status_change)
```

---

## 🚀 Deployment

### Development
```bash
# Backend
cd src/dashboard/backend
uvicorn main:app --reload --port 8000

# Frontend
cd src/dashboard/frontend
npm run dev  # Vite on port 5173
```

### Production
- Backend: Deploy FastAPI with gunicorn/uvicorn
- Frontend: Build static assets, serve with nginx
- WebSocket: Ensure sticky sessions or shared state (Redis)

---

## 📚 Documentation

### User Guide
- How to review outlines
- How to edit Show Blueprint
- How to interpret pipeline stages

### Developer Guide
- API endpoint reference
- WebSocket message format
- Component architecture

---

## 🔮 Future Enhancements

- **Rich Text Editor:** WYSIWYG for world descriptions
- **Version History:** Track changes to Show Blueprint
- **Collaboration:** Multiple users reviewing simultaneously
- **Audio Waveform:** Visual representation of audio segments
- **Bulk Operations:** Approve/reject multiple episodes
- **Analytics:** Track approval rates, common rejections
