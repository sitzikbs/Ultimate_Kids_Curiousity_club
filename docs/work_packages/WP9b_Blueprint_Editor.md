# WP9b: Show Blueprint Editor UI

**Parent WP**: WP9 (Web Dashboard)  
**Status**: ⏳ Not Started  
**Dependencies**: WP9a (Backend API), WP5 (Image Service)  
**Estimated Effort**: 2-3 days  
**Owner**: TBD  
**Subsystem:** User Interface

## 📋 Overview

Build the Show Blueprint editing interface: show list page, protagonist editor, world editor, character management, and concept tracking. Uses vanilla JavaScript with Tailwind CSS for styling.

**Key Deliverables**:
- Show list page with search/filter
- Protagonist profile editor with image upload
- World description editor with location images
- Character management (add/edit/delete)
- Concepts covered timeline
- Responsive design (desktop/tablet)

## 🎯 High-Level Tasks

### Task 9b.1: Show List Page
Create landing page showing all available shows.

**Subtasks**:
- [ ] 9b.1.1: Create `website/index.html` with show grid layout
- [ ] 9b.1.2: Fetch shows from `GET /api/shows` endpoint
- [ ] 9b.1.3: Display show cards with thumbnail, title, episode count
- [ ] 9b.1.4: Add search bar for filtering shows
- [ ] 9b.1.5: Add "Create New Show" button (future feature)
- [ ] 9b.1.6: Link each show card to blueprint editor

**Expected Outputs**:
- `website/index.html` with show list
- `website/js/shows.js` with fetch logic
- Responsive grid layout (Tailwind)

### Task 9b.2: Protagonist Editor
Build protagonist profile editing UI.

**Subtasks**:
- [ ] 9b.2.1: Create `website/blueprint.html` with tabbed interface
- [ ] 9b.2.2: Add "Protagonist" tab with form fields
- [ ] 9b.2.3: Fields: name, age, description, values (list), catchphrases, backstory
- [ ] 9b.2.4: Add image upload preview
- [ ] 9b.2.5: Add voice config selector (voice_id, language)
- [ ] 9b.2.6: Implement save button (PUT /api/shows/{show_id})
- [ ] 9b.2.7: Add validation (required fields, age range)

**Expected Outputs**:
- Protagonist tab in blueprint editor
- Image preview and upload handling
- Form validation with error messages

### Task 9b.3: World Editor
Build world description and location management UI.

**Subtasks**:
- [ ] 9b.3.1: Add "World" tab to blueprint editor
- [ ] 9b.3.2: Fields: setting, rules (list), atmosphere
- [ ] 9b.3.3: Add locations section (name, description, image_path)
- [ ] 9b.3.4: Add "Add Location" button for dynamic list
- [ ] 9b.3.5: Implement location image upload
- [ ] 9b.3.6: Add remove button for each location
- [ ] 9b.3.7: Save world data to backend

**Expected Outputs**:
- World tab with rich text editing
- Dynamic location management
- Multiple image uploads

### Task 9b.4: Character Management
Build supporting character CRUD interface.

**Subtasks**:
- [ ] 9b.4.1: Add "Characters" tab to blueprint editor
- [ ] 9b.4.2: Display character list with cards
- [ ] 9b.4.3: Add "New Character" modal form
- [ ] 9b.4.4: Fields: name, role, description, personality, image_path, voice_config
- [ ] 9b.4.5: Implement edit and delete buttons
- [ ] 9b.4.6: Add character image upload
- [ ] 9b.4.7: Save characters to backend

**Expected Outputs**:
- Characters tab with card layout
- Modal form for add/edit
- Delete confirmation dialog

### Task 9b.5: Concepts Tracking
Display educational concepts covered timeline.

**Subtasks**:
- [ ] 9b.5.1: Add "Concepts" tab to blueprint editor
- [ ] 9b.5.2: Fetch concepts_covered.json from backend
- [ ] 9b.5.3: Display timeline view (most recent first)
- [ ] 9b.5.4: Show concept name, episode link, date covered
- [ ] 9b.5.5: Add search/filter by concept name
- [ ] 9b.5.6: Make it read-only (updated automatically by system)

**Expected Outputs**:
- Concepts tab with timeline view
- Episode linking
- Search functionality

### Task 9b.6: Testing & Polish
Test UI interactions and add polish.

**Subtasks**:
- [ ] 9b.6.1: Test form validation on all tabs
- [ ] 9b.6.2: Test image upload and preview
- [ ] 9b.6.3: Test save/cancel workflows
- [ ] 9b.6.4: Add loading spinners for API calls
- [ ] 9b.6.5: Add success/error toast notifications
- [ ] 9b.6.6: Test responsive design on tablet/mobile

**Expected Outputs**:
- Smooth UX with feedback
- Error handling for API failures
- Mobile-friendly layout

## 🧪 Testing Strategy

- **Manual Testing**: Click through all tabs and forms
- **Browser Testing**: Chrome, Firefox, Safari
- **Responsive Testing**: Desktop, tablet, mobile viewports
- **API Testing**: Test with real backend endpoints

## ✅ Definition of Done

- [ ] All tabs load and display data correctly
- [ ] Forms validate input before saving
- [ ] Images upload and display properly
- [ ] Responsive design works on tablet/mobile
- [ ] Loading states and error handling in place
- [ ] No console errors in browser

## 🔗 Related Work Packages

- **WP9a**: Provides backend API endpoints
- **WP5**: Image service for upload handling
- **WP9c**: Will add approval workflow UI
