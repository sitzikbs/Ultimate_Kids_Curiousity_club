# WP9c: Outline Approval & Pipeline Dashboard

**Parent WP**: WP9 (Web Dashboard)  
**Status**: ⏳ Not Started  
**Dependencies**: WP9a (Backend API), WP9b (Blueprint Editor), WP6 (Orchestrator)  
**Estimated Effort**: 2-3 days  
**Owner**: TBD  
**Subsystem:** User Interface

## 📋 Overview

Build the episode workflow UI: outline approval interface, pipeline status dashboard, real-time progress updates via WebSocket, and episode management. This is the core operational interface for episode production.

**Key Deliverables**:
- Outline approval UI with inline editing
- Pipeline status dashboard with stage indicators
- Real-time progress updates (WebSocket)
- Episode list with filtering
- Approval history tracking

## 🎯 High-Level Tasks

### Task 9c.1: Outline Approval UI
Build interface for reviewing and approving story outlines.

**Subtasks**:
- [ ] 9c.1.1: Create `website/approval.html` for outline review
- [ ] 9c.1.2: Fetch episode in AWAITING_APPROVAL stage
- [ ] 9c.1.3: Display story beats in readable format
- [ ] 9c.1.4: Add inline editing for beat titles/descriptions
- [ ] 9c.1.5: Add "Approve", "Reject", "Edit & Approve" buttons
- [ ] 9c.1.6: Implement feedback text area for rejection
- [ ] 9c.1.7: Send approval decision to POST /api/episodes/{id}/approve
- [ ] 9c.1.8: Show confirmation modal before final approval

**Expected Outputs**:
- Outline review page with beat editor
- Approval workflow with feedback
- Confirmation dialogs

### Task 9c.2: Pipeline Status Dashboard
Create dashboard showing all episodes and their pipeline stages.

**Subtasks**:
- [ ] 9c.2.1: Create `website/dashboard.html` with episode table
- [ ] 9c.2.2: Fetch episodes from GET /api/shows/{show_id}/episodes
- [ ] 9c.2.3: Display columns: Episode, Topic, Stage, Progress, Actions
- [ ] 9c.2.4: Add stage indicator badges (color-coded)
- [ ] 9c.2.5: Show progress bar for current stage
- [ ] 9c.2.6: Add filter dropdown (All, In Progress, Awaiting Approval, Complete)
- [ ] 9c.2.7: Add "View Details" button linking to episode page
- [ ] 9c.2.8: Add "Retry" button for FAILED episodes

**Expected Outputs**:
- Dashboard with episode table
- Stage indicators and progress bars
- Filtering and sorting

### Task 9c.3: Real-Time Updates (WebSocket)
Integrate WebSocket for live pipeline status updates.

**Subtasks**:
- [ ] 9c.3.1: Create WebSocket client in `website/js/websocket.js`
- [ ] 9c.3.2: Connect to ws://localhost:8000/ws on page load
- [ ] 9c.3.3: Listen for `episode_status_changed` events
- [ ] 9c.3.4: Update stage badges in real-time
- [ ] 9c.3.5: Update progress bars when progress_update received
- [ ] 9c.3.6: Show toast notification for stage changes
- [ ] 9c.3.7: Add connection status indicator (online/offline)
- [ ] 9c.3.8: Implement reconnection logic on disconnect

**Expected Outputs**:
- WebSocket client with auto-reconnect
- Live UI updates without refresh
- Connection status indicator

### Task 9c.4: Episode Details Page
Build detailed episode view with full history.

**Subtasks**:
- [ ] 9c.4.1: Create `website/episode.html` for episode details
- [ ] 9c.4.2: Display episode metadata (topic, title, created_at)
- [ ] 9c.4.3: Show full outline with story beats
- [ ] 9c.4.4: Display generated scripts (if available)
- [ ] 9c.4.5: Show audio player for final MP3 (if available)
- [ ] 9c.4.6: Add checkpoint history timeline
- [ ] 9c.4.7: Show approval history (approver, timestamp, feedback)
- [ ] 9c.4.8: Add download buttons for scripts and audio

**Expected Outputs**:
- Episode details page with full data
- Audio player integration
- Checkpoint timeline view

### Task 9c.5: Testing & Integration
Test end-to-end workflow and integrate with backend.

**Subtasks**:
- [ ] 9c.5.1: Test full approval workflow (approve/reject/edit)
- [ ] 9c.5.2: Test WebSocket updates with multiple browser tabs
- [ ] 9c.5.3: Test pipeline dashboard with various episode states
- [ ] 9c.5.4: Test episode filtering and sorting
- [ ] 9c.5.5: Test error handling (network failures, WebSocket disconnects)
- [ ] 9c.5.6: Add integration tests with real orchestrator
- [ ] 9c.5.7: Test responsive design on tablet

**Expected Outputs**:
- All workflows tested end-to-end
- Error handling validated
- Integration with orchestrator confirmed

## 🧪 Testing Strategy

- **Manual Testing**: Complete approval workflow end-to-end
- **WebSocket Testing**: Multiple browser tabs for real-time updates
- **Integration Testing**: With running orchestrator and backend
- **Error Testing**: Network failures, WebSocket disconnects

## ✅ Definition of Done

- [ ] Outline approval workflow works correctly
- [ ] Pipeline dashboard shows accurate episode states
- [ ] WebSocket updates UI in real-time
- [ ] Episode details page displays all data
- [ ] Filtering and sorting work properly
- [ ] Error handling graceful for all failure modes
- [ ] Responsive design tested on tablet

## 🔗 Related Work Packages

- **WP9a**: Backend API provides episode data
- **WP9b**: Blueprint editor for show context
- **WP6**: Orchestrator manages pipeline states
- **WP7b**: CLI alternative for approval workflow
