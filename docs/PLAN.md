# Kids Curiosity Club - Project Plan

**Version:** 1.1  
**Last Updated:** December 26, 2025  
**Status:** Foundation In Progress (40% complete)

## 🎯 Project Vision

Build an AI-powered podcast generation system that creates **story-based educational adventures** featuring protagonist characters in their own universes. Each show (Oliver's STEM Adventures, Hannah's History Adventures) generates episodes where the protagonist goes on adventures that naturally teach educational concepts - similar to Purple Rocket or Snoop & Sniffy. The system uses **incremental story generation** with human review gates and maintains a **Show Blueprint** for continuity.

## 📋 MVP Scope

### In Scope
- ✅ **Multi-Show System**: Support for multiple shows (Oliver's STEM Adventures, Hannah's History Adventures)
- ✅ **Show Blueprint**: Centralized show data (protagonist + image, world description + images, characters + images, concepts covered)
- ✅ **Story Generation**: Incremental creation (ideation → outline → segments → scripts)
- ✅ **Human Review Gate**: Approval workflow after story outline generation
- ✅ **Audio Synthesis**: Multi-voice TTS (narrator + protagonist + supporting characters)
- ✅ **Audio Production**: Professional mixing with background music
- ✅ **Mock Services**: Cost-free development with realistic fixtures
- ✅ **CLI Interface**: Show management and episode creation commands
- ✅ **Web Dashboard**: Review interface for outlines, scripts, and show blueprint editing
- ✅ **Testing Infrastructure**: Comprehensive testing with gated real API calls

### Out of Scope (Post-MVP)
- ❌ Video generation and animation
- ❌ Character voice customization UI
- ❌ Automated publishing to platforms
- ❌ Advanced features (character evolution, fan contributions)

## 🏗️ System Architecture

### System Overview: Subsystem Design

The system is organized into **6 core subsystems** for modularity and parallel development:

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERFACE SUBSYSTEM                     │
│  ┌──────────────────┐         ┌──────────────────────────┐     │
│  │   CLI (WP7)      │         │  Web Dashboard (WP9)     │     │
│  │  - Show mgmt     │         │  - Outline approval      │     │
│  │  - Episode mgmt  │         │  - Blueprint editor      │     │
│  └────────┬─────────┘         └──────────┬───────────────┘     │
└───────────┼────────────────────────────────┼───────────────────┘
            │                                │
┌───────────┴────────────────────────────────┴───────────────────┐
│              ORCHESTRATION SUBSYSTEM (WP6)                      │
│  - Pipeline state machine (8 stages)                            │
│  - Human approval gate                                          │
│  - Service coordination                                         │
│  - Error handling & retry                                       │
└──┬────────┬──────────────┬────────────────┬─────────────────┬──┘
   │        │              │                │                 │
┌──┴────────┴──┐  ┌────────┴─────────┐  ┌──┴─────────────┐  │
│  SHOW MGMT   │  │ CONTENT GEN      │  │  AUDIO PROD    │  │
│  SUBSYSTEM   │  │ SUBSYSTEM        │  │  SUBSYSTEM     │  │
│              │  │                  │  │                │  │
│  WP1:        │  │  WP0: Prompts    │  │  WP3: TTS      │  │
│  Foundation  │  │  WP2: LLM Svcs   │  │  WP4: Mixer    │  │
│  - Blueprint │  │   • Ideation     │  │  WP5: Images   │  │
│    Manager   │  │   • Outline      │  │                │  │
│  - Models    │  │   • Segment      │  │                │  │
│  - Config    │  │   • Script       │  │                │  │
└──────┬───────┘  └──────────────────┘  └────────────────┘  │
       │                                                      │
┌──────┴──────────────────────────────────────────────────────┴──┐
│                    STORAGE SUBSYSTEM                            │
│  data/                                                          │
│  ├── shows/{show-id}/                                           │
│  │   ├── show.yaml, protagonist.json, world.md                 │
│  │   ├── characters/*.json                                     │
│  │   ├── concepts_covered.json                                 │
│  │   └── episodes/{ep-id}/                                     │
│  └── assets/ (audio, images)                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Show Blueprint Structure

Each show has a centralized blueprint containing:
```
data/shows/{show-id}/
├── show.yaml              # Show metadata, theme, narrator config
├── protagonist.json       # Main character + value system + image_path
├── world.md              # Setting, rules, atmosphere (with image_paths)
├── characters/           # Supporting cast
│   ├── robbie_robot.json (with image_path)
│   └── professor_nova.json (with image_path)
├── concepts_covered.json # Educational history (avoid repetition)
└── episodes/             # Generated episodes
    └── ep001_rockets/
        ├── episode.json
        ├── outline.yaml
        ├── segments.json
        ├── scripts.json
        └── final_audio.mp3
```

### Data Flow: Episode Generation Pipeline

```
┌─────────────┐
│ User Input  │ Show ID + Topic
└──────┬──────┘
       ↓
┌──────┴──────────────────────────────────────────────┐
│ SHOW MANAGEMENT SUBSYSTEM                           │
│ Load Show Blueprint → Inject context                │
└──────┬──────────────────────────────────────────────┘
       ↓
┌──────┴──────────────────────────────────────────────┐
│ CONTENT GENERATION SUBSYSTEM                        │
│                                                      │
│ IDEATION ────────→ Story concept (2-3 paragraphs)   │
│       ↓                                              │
│ OUTLINING ───────→ Story beats (reviewable)         │
│       ↓                                              │
│ ⏸️  HUMAN APPROVAL (via Dashboard/CLI)              │
│       ↓                                              │
│ SEGMENT_GEN ─────→ Detailed segments (what happens) │
│       ↓                                              │
│ SCRIPT_GEN ──────→ Narration + dialogue scripts     │
└──────┬──────────────────────────────────────────────┘
       ↓
┌──────┴──────────────────────────────────────────────┐
│ AUDIO PRODUCTION SUBSYSTEM                          │
│                                                      │
│ TTS SYNTHESIS ───→ Audio segments (MP3s)            │
│       ↓                                              │
│ AUDIO MIXING ────→ Final episode (with music/FX)    │
└──────┬──────────────────────────────────────────────┘
       ↓
┌──────┴──────────────────────────────────────────────┐
│ STORAGE SUBSYSTEM                                   │
│ Save: final_audio.mp3 + Update concepts_covered.json│
└─────────────────────────────────────────────────────┘
```

### Subsystem Responsibilities

| Subsystem | Work Packages | Responsibilities | Can Develop in Parallel? |
|-----------|---------------|------------------|--------------------------|
| **Storage** | WP1 | Data models, file I/O, Show Blueprint management | ❌ (foundation for all) |
| **Show Management** | WP1 | Load/save blueprints, manage concepts, validate data | ❌ (foundation for all) |
| **Content Generation** | WP0, WP2 | Prompt enhancement, 4 LLM services | ✅ (after WP1) |
| **Audio Production** | WP3, WP4, WP5 | TTS, mixing, image handling | ✅ (after WP1) |
| **Orchestration** | WP6 | Pipeline coordination, approval workflow | ❌ (needs all services) |
| **User Interface** | WP7, WP9 | CLI commands, web dashboard | ✅ (after WP6) || **Distribution** | WP10 | Website, podcast hosting, RSS feeds, episode publishing | ✅ (infrastructure parallel, integration after WP6) |
### Integration Points Between Subsystems

```
Show Management ←→ Content Generation
  • Provides: ShowBlueprint, ConceptsHistory
  • Receives: Updated concepts after completion

Content Generation ←→ Orchestration
  • Provides: Story stages (concept, outline, segments, scripts)
  • Receives: Approval status from human review

Audio Production ←→ Orchestration
  • Provides: Audio segments, final MP3
  • Receives: Scripts to synthesize

User Interface ←→ Orchestration
  • Provides: User commands, approval decisions
  • Receives: Pipeline status, outlines for review

Storage ←→ All Subsystems
  • Central persistent layer for all data
```

### Parallel Development Strategy

**Phase 1: Foundation (Sequential)**
- Week 1: WP0 + WP1 (Must complete first - all subsystems depend on this)

**Phase 2: Service Subsystems (Parallel - 3 teams)**
- Week 2-3: 
  - Team A: WP2 (Content Generation - 4 LLM services)
  - Team B: WP3 + WP4 (Audio Production - TTS + Mixer)
  - Team C: WP5 (Image Service)

**Phase 3: Orchestration (Sequential)**
- Week 3-4: WP6 (Pipeline orchestrator - integrates all services)

**Phase 4: User Interfaces (Parallel - 2 teams)**
- Week 4-5:
  - Team A: WP7 (CLI)
  - Team B: WP9 (Web Dashboard)

**Phase 5: Distribution (Post-MVP)**
- Week 6: WP10 (Website integration, podcast hosting, RSS feeds)

**Ongoing: Testing (WP8)** - Embedded in all phases

## 📦 Work Packages Overview

### WP0: Prompt Enhancement Service
**Purpose:** Enrich topic inputs with Show Blueprint context for story generation  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**Estimated Effort:** 1-2 days

**Key Deliverables:**
- Template system with Jinja2 for show context injection
- Enhancement methods for ideation, outline, segment, script stages
- Prompt versioning and A/B testing capability
- Integration with Show Blueprint data (protagonist, world, characters, concepts)

**Dependencies:** None  
**Blocks:** WP2a, WP2b, WP6a

**Why This Matters:** LLMs need rich context to generate consistent stories. This service automatically injects protagonist values, world rules, covered concepts, and show theme into prompts for each generation stage.

---

### WP1: Foundation & Data Models
**Purpose:** Core data models, configuration, and Show Blueprint management (critical path)  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**Estimated Effort:** 5-6 days (all sub-WPs combined)

This work package is broken into 5 sub-packages for parallel development:

#### WP1a: Core Models (Show Blueprint + Episode)
**Purpose:** Pydantic data models for Show Blueprint and episode structures  
**Owner:** @copilot  
**Status:** 🟢 Complete  
**Estimated Effort:** 1-2 days

**Key Deliverables:**
- ✅ Show Blueprint models (Show, Protagonist, WorldDescription, Character, ConceptsHistory)
- ✅ Episode models (Episode, StoryOutline, StoryBeat, StorySegment, Script, ScriptBlock)
- ✅ PipelineStage enum and validation rules
- ✅ 24 passing tests covering all models
- ✅ Full type hints and JSON schema support

**GitHub Issue:** #61  
**Completed:** December 26, 2025  
**Dependencies:** None  
**Unblocked:** WP1b, WP1c, WP1d, WP1e, WP2a, WP6a, WP7a, WP9a

---

#### WP1b: Configuration (Settings & Config)
**Purpose:** Centralized settings and configuration system  
**Owner:** @copilot  
**Status:** 🟢 Complete  
**Estimated Effort:** 1 day

**Key Deliverables:**
- ✅ Settings class with environment-based configuration (pydantic-settings)
- ✅ Mock mode toggle for development
- ✅ API key management with .env support
- ✅ Provider preferences (LLM, TTS, Image)
- ✅ Storage path configuration
- ✅ 11 passing tests covering all configuration scenarios

**GitHub Issue:** #62  
**Completed:** December 26, 2025  
**Dependencies:** WP1a (complete)  
**Unblocked:** WP1c, WP1d, WP2a, WP3, WP4, WP5, WP6a

---

#### WP1c: Blueprint Manager (ShowBlueprintManager)
**Purpose:** Show Blueprint loading, saving, and management system  
**Owner:** Unassigned  
**Status:** 🔴 Not Started (Ready to start)  
**Estimated Effort:** 2 days

**Key Deliverables:**
- ShowBlueprintManager with CRUD operations
- Show Blueprint loading/saving from disk
- Concepts tracking and management
- Show templates (Oliver, Hannah)
- Character and world management

**Dependencies:** WP1a (complete ✅), WP1b (complete ✅)  
**Blocks:** WP2a, WP6a, WP7a, WP9a, WP9b

---

#### WP1d: Storage (Episode Storage + Error Handling)
**Purpose:** File-based storage for episodes and error handling infrastructure  
**Owner:** Unassigned  
**Status:** 🔴 Not Started (Ready to start)  
**Estimated Effort:** 1-2 days

**Key Deliverables:**
- EpisodeStorage class for save/load operations
- Checkpoint saving/loading for pipeline resumption
- Custom exception hierarchy
- Error context tracking and retry decorators
- Atomic writes and file locking

**Dependencies:** WP1a (complete ✅), WP1b (complete ✅)  
**Blocks:** WP6a, WP6b, WP7b

---

#### WP1e: Testing & Validation
**Purpose:** Validation utilities and comprehensive testing infrastructure  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**Estimated Effort:** 1 day

**Key Deliverables:**
- Custom Pydantic types (DurationMinutes, AgeRange, VocabularyLevel)
- File path validators
- Content validators (profanity, age-appropriate checking)
- Test suite for foundation components
- Test fixtures and helpers

**Dependencies:** WP1a, WP1b, WP1c, WP1d  
**Blocks:** WP2a, WP2b, WP8

---

### WP2: LLM Services & Story Generation
**Purpose:** Story content generation through incremental stages  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**Estimated Effort:** 4-5 days (all sub-WPs combined)

This work package is broken into 2 sub-packages:

#### WP2a: Provider Abstraction, Ideation & Outline Generation
**Purpose:** LLM provider abstraction and first two story generation stages  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**Estimated Effort:** 2-3 days

**Key Deliverables:**
- Provider abstraction layer (OpenAI, Anthropic, Mock)
- IdeationService: topic → story concept
- OutlineService: concept → reviewable story beats
- Provider factory and retry logic
- Mock provider with fixture-based responses

**Dependencies:** WP0, WP1a, WP1b  
**Blocks:** WP2b, WP6a

---

#### WP2b: Segment Generation, Script Generation & Cost Tracking
**Purpose:** Final story generation stages with cost monitoring  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**Estimated Effort:** 2 days

**Key Deliverables:**
- SegmentGenerationService: outline → detailed segments
- ScriptGenerationService: segments → narration + dialogue scripts
- Response parsing and Pydantic validation
- Cost tracking and token usage monitoring
- Integration tests for end-to-end LLM pipeline

**Dependencies:** WP2a  
**Blocks:** WP6a, WP6b

---

### WP3: TTS Service
**Purpose:** Text-to-speech audio synthesis for narrator and character voices  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**Estimated Effort:** 2-3 days

**Key Deliverables:**
- Provider abstraction (ElevenLabs, Google TTS, OpenAI TTS, Mock)
- Audio segment synthesis with voice mapping
- Voice listing and configuration
- Support for narrator + protagonist + supporting character voices

**Dependencies:** WP1a, WP1b  
**Blocks:** WP6b

---

### WP4: Audio Mixer
**Purpose:** Professional audio composition and mixing  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**Estimated Effort:** 2-3 days

**Key Deliverables:**
- Segment sequencing with timing
- Background music generation/layering
- Sound effects at markers
- MP3 export with ID3 metadata

**Dependencies:** WP1a, WP1b  
**Blocks:** WP6b

---

### WP5: Image Service
**Purpose:** Show Blueprint image management and optional generation  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**Estimated Effort:** 1-2 days

**Key Deliverables:**
- Image loading and validation (protagonist, world, characters)
- Optional character/world image generation (Flux, DALL-E)
- Image format conversion and optimization
- Mock image provider
- Image path management in Show Blueprint

**Dependencies:** WP1a, WP1b  
**Blocks:** WP6b, WP9b

---

### WP6: Pipeline Orchestrator
**Purpose:** Coordinate services for end-to-end episode generation with human review  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**Estimated Effort:** 3-4 days (all sub-WPs combined)

This work package is broken into 2 sub-packages:

#### WP6a: State Machine & Workflow
**Purpose:** Core pipeline state machine with approval workflow  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**Estimated Effort:** 1.5-2 days

**Key Deliverables:**
- State machine for 8 pipeline stages with approval gate
- Human approval workflow (pause, review, approve/reject)
- Show Blueprint context injection at each stage
- State transition validation and progression logic
- Event emission for UI notifications

**Dependencies:** WP0, WP1a, WP1b, WP1c, WP2a  
**Blocks:** WP6b, WP7a, WP7b, WP9a, WP9c

---

#### WP6b: Reliability & Recovery
**Purpose:** Production-ready reliability features for pipeline  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**Estimated Effort:** 1.5-2 days

**Key Deliverables:**
- Checkpoint save/restore functionality
- Error handling and retry logic
- Progress tracking and logging
- Service integration (TTS, Audio Mixer, Image Manager)
- Resume-from-any-stage capability
- Integration testing with mock and real services

**Dependencies:** WP6a, WP3, WP4, WP5, WP2b  
**Blocks:** WP7b, WP9c

---

### WP7: CLI Interface
**Purpose:** Command-line interface for show and episode management  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**Estimated Effort:** 2-4 days (all sub-WPs combined)

This work package is broken into 2 sub-packages:

#### WP7a: Show Commands
**Purpose:** CLI interface for show management and Show Blueprint viewing  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**Estimated Effort:** 1-2 days

**Key Deliverables:**
- Show management commands (list, create, init, info)
- Show Blueprint commands (characters, concepts, suggest-topics)
- Character management within shows
- Interactive prompts for show creation
- Formatted terminal output with rich

**Dependencies:** WP1a, WP1b, WP1c  
**Blocks:** WP7b

---

#### WP7b: Episode Commands
**Purpose:** CLI interface for episode creation and approval workflow  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**Estimated Effort:** 1-2 days

**Key Deliverables:**
- Episode management commands (create, resume, list, approve, reject)
- Approval workflow integration
- Configuration commands (show, set-provider, toggle-mock)
- Progress visualization with rich (progress bars, spinners, cost tracking)
- Interactive prompts for episode creation

**Dependencies:** WP1a, WP1b, WP1d, WP6a, WP6b, WP7a  
**Blocks:** None

---

### WP8: Testing Infrastructure
**Purpose:** Comprehensive testing with cost controls  
**Owner:** @copilot  
**Status:** 🟢 Complete  
**Estimated Effort:** Ongoing throughout all WPs

**Key Deliverables:**
- ✅ Pytest configuration (pytest.ini, .coveragerc, custom markers: unit, integration, real_api, slow, benchmark)
- ✅ Comprehensive fixture system (characters, episodes, services, audio)
- ✅ Mock provider fixtures (LLM JSON responses, silent MP3s, placeholder images)
- ✅ Cost tracking utilities with budget enforcement ($10 limit)
- ✅ Real API test templates with gating
- ✅ Integration test placeholders (ready for implementation)
- ✅ CI/CD pipeline (GitHub Actions, Python 3.10-3.12, matrix testing)
- ✅ Quality gates (pre-commit hooks, ruff, mypy)
- ✅ Performance benchmarking (pytest-benchmark)
- ✅ Comprehensive documentation (TESTING_GUIDE.md, REAL_API_TESTS.md)

**Test Results:**
- 60 tests passing (25 infrastructure + 24 models + 11 config)
- 21 skipped tests (16 integration placeholders + 3 real API + 3 benchmark placeholders - 1 benchmark running)
- All quality checks passing (lint, format, type check, coverage)

**GitHub Issue:** #85  
**Completed:** December 26, 2025  
**Dependencies:** All work packages (for integration tests)  
**Blocks:** None (developed alongside other WPs)

---

### WP9: Web Dashboard & Review Interface
**Purpose:** Human review interface for outlines, scripts, and Show Blueprint management  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**Estimated Effort:** 5.5-8 days (all sub-WPs combined)

This work package is broken into 3 sub-packages:

#### WP9a: Dashboard Backend & API
**Purpose:** FastAPI server with REST endpoints and WebSocket support  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**Estimated Effort:** 1.5-2 days

**Key Deliverables:**
- FastAPI application with CORS support
- REST endpoints for show/episode data
- WebSocket endpoint for real-time updates
- Static file serving for HTML/CSS/JS
- API documentation (auto-generated)

**Dependencies:** WP1a, WP1b, WP1c  
**Blocks:** WP9b, WP9c

---

#### WP9b: Show Blueprint Editor UI
**Purpose:** Show Blueprint editing interface  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**Estimated Effort:** 2-3 days

**Key Deliverables:**
- Show list page with search/filter
- Protagonist profile editor with image upload
- World description editor with location images
- Character management (add/edit/delete)
- Concepts covered timeline
- Responsive design (desktop/tablet)

**Dependencies:** WP9a, WP5  
**Blocks:** WP9c

---

#### WP9c: Outline Approval & Pipeline Dashboard
**Purpose:** Episode workflow UI with approval interface  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**Estimated Effort:** 2-3 days

**Key Deliverables:**
- Outline approval UI with inline editing
- Pipeline status dashboard with stage indicators
- Real-time progress updates (WebSocket)
- Episode list with filtering
- Approval history tracking

**Dependencies:** WP9a, WP9b, WP6a, WP6b  
**Blocks:** None

---

### WP10: Website & Distribution
**Purpose:** Public-facing website and podcast distribution pipeline  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**Estimated Effort:** 3.5-4.5 days (all sub-WPs combined)

This work package is broken into 2 sub-packages:

#### WP10a: Website & SEO
**Purpose:** Static website with episode listings and SEO optimization  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**Estimated Effort:** 1.5-2 days

**Key Deliverables:**
- Episode listing pages with audio player
- Episode metadata schema and JSON data files
- SEO optimization (Schema.org, social media tags, sitemap)
- Analytics verification and event tracking
- Website deployment and hosting configuration

**Dependencies:** None (can start independently)  
**Blocks:** None

---

#### WP10b: Podcast Distribution & Hosting
**Purpose:** Podcast hosting integration and RSS feed management  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**Estimated Effort:** 2-2.5 days

**Key Deliverables:**
- Podcast hosting integration (Transistor.fm, Buzzsprout, or RSS.com)
- Automated episode metadata upload
- RSS feed generation and management (RSS 2.0 + iTunes tags)
- Publication orchestrator for multi-platform coordination
- Podcast directory submissions (Apple, Spotify, Google)
- CI/CD pipeline for automated publishing

**Dependencies:** WP6a, WP6b (produces final MP3s), WP7b  
**Blocks:** None

**Why This Matters:** The content generation pipeline is useless without distribution. This WP handles the "last mile" - getting finished episodes to listeners on their preferred platforms.

---

## 🔄 Work Package Dependencies

```
           WP0 (Prompt)
              ↓
        ┌─────┴─────┐
        ↓           ↓
   WP1a (Models)  WP2a (Provider+Ideation+Outline)
        ↓           ↓
   WP1b (Config)  WP2b (Segment+Script+Cost)
        ↓
   WP1c (Blueprint Manager)
        ↓
   WP1d (Storage)
        ↓
   WP1e (Testing)
        ↓
    ┌───┴───┬──────┬──────┐
    ↓       ↓      ↓      ↓
   WP3    WP4    WP5   WP6a (State Machine)
  (TTS) (Mixer) (Image)    ↓
    └───┬───┴──────┴───→ WP6b (Reliability)
                          ↓
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
    WP7a (Show)      WP9a (Backend)    WP10a (Website)
        ↓                 ↓                 ↓
    WP7b (Episode)   WP9b (Blueprint)  WP10b (Distribution)
                          ↓
                     WP9c (Approval)
                          
                     WP8 (Testing - Ongoing)
```

**Development Sequence:**
1. **Phase 1 (Sequential - 5-6 days):** WP0 + WP1 (all sub-WPs: 1a→1b→1c→1d→1e)
2. **Phase 2 (Parallel - 4-5 days):** 
   - Team A: WP2a → WP2b (LLM Services)
   - Team B: WP3 + WP4 (Audio Production)
   - Team C: WP5 (Image Service)
3. **Phase 3 (Sequential - 3-4 days):** WP6a → WP6b (Orchestrator)
4. **Phase 4 (Parallel - 5.5-8 days):**
   - Team A: WP7a → WP7b (CLI)
   - Team B: WP9a → WP9b → WP9c (Dashboard)
   - Team C: WP10a + WP10b (Distribution)
5. **Ongoing:** WP8 (Testing throughout all phases)

## 💰 Cost Management

### Development Cost Strategy
- **Mock-first development:** All services have mock providers (FREE)
- **Gated real API tests:** Require explicit confirmation
- **Cost tracking:** Every API call logged with provider/model/cost
- **Budget limits:** Configurable per test run

### Estimated Costs

**Fixture Generation (One-time):**
- LLM fixtures: ~$2-3 (story outlines, segments, scripts)
- TTS fixtures: ~$2-3 (narrator + character audio samples)
- Image fixtures: ~$1-2 (protagonist, world, characters)
- **Total:** ~$5-10

**Per Episode (Real APIs):**
- Story generation: ~$1-2 (GPT-4/Claude for ideation → outline → segments → scripts)
- Audio synthesis: ~$3-5 (ElevenLabs for narrator + character voices)
- Images: ~$0.50-1 (optional character/world images)
- **Total:** ~$5-8 per episode

**Testing Strategy:**
- Unit tests: FREE (mocks only)
- Service tests: ~$1-2 per service (one-time validation)
- E2E tests: ~$5-10 per run (full pipeline)

## 📊 Success Criteria

### MVP Complete When:
- [x] All work packages 0-9 complete
- [x] Multi-show system working with Show Blueprint
- [x] Can generate complete story-based episode from topic
- [x] Human approval workflow functional
- [x] Incremental generation (outline → segments → scripts) working
- [x] Show Blueprint management working (protagonist, world, characters, concepts)
- [x] Mock services enable free development
- [x] Real APIs tested and working
- [x] CLI functional for all core operations
- [x] Web dashboard for review and editing
- [x] >80% test coverage
- [x] Documentation complete

### Quality Gates:
- All unit tests pass (mocks)
- At least one successful E2E test with real APIs
- Story quality verified manually (narrative coherence, educational value)
- Protagonist personality evident in output
- Show Blueprint continuity maintained across episodes
- Cost per episode within budget

## 🚀 Timeline Estimate

**Assuming serial development by one developer:**
- WP0: 1-2 days
- WP1: 5-6 days total
  - WP1a: 1-2 days (Core Models)
  - WP1b: 1 day (Configuration)
  - WP1c: 2 days (Blueprint Manager)
  - WP1d: 1-2 days (Storage)
  - WP1e: 1 day (Testing)
- WP2: 4-5 days total
  - WP2a: 2-3 days (Provider, Ideation, Outline)
  - WP2b: 2 days (Segment, Script, Cost)
- WP3: 2-3 days (TTS)
- WP4: 2-3 days (Audio Mixer)
- WP5: 1-2 days (Image Service)
- WP6: 3-4 days total
  - WP6a: 1.5-2 days (State Machine)
  - WP6b: 1.5-2 days (Reliability)
- WP7: 2-4 days total
  - WP7a: 1-2 days (Show Commands)
  - WP7b: 1-2 days (Episode Commands)
- WP9: 5.5-8 days total
  - WP9a: 1.5-2 days (Backend API)
  - WP9b: 2-3 days (Blueprint Editor)
  - WP9c: 2-3 days (Approval Dashboard)
- WP10: 3.5-4.5 days total
  - WP10a: 1.5-2 days (Website & SEO)
  - WP10b: 2-2.5 days (Podcast Distribution)
- WP8: Ongoing

**Total:** ~4-6 weeks for MVP

**With parallel development (multiple agents):**
- Phase 1: 5-6 days (WP0 + WP1a→1e sequential)
- Phase 2: 4-5 days (WP2a→2b, WP3+4, WP5 parallel)
- Phase 3: 3-4 days (WP6a→6b sequential)
- Phase 4: 5.5-8 days (WP7a→7b, WP9a→9b→9c, WP10a+10b parallel)

**Total:** ~3-4 weeks with 4 parallel agents

## 📚 Key Documentation

- **[Work Packages](work_packages/)** - Detailed specifications
- **[Interfaces](work_packages/INTERFACES.md)** - Service contracts
- **[Development Guide](DEVELOPMENT.md)** - Workflow and standards
- **[Progress Tracking](PROGRESS.md)** - Current status
- **[ADRs](decisions/)** - Design decisions

## 🎓 Learning Resources

**For Contributors:**
- [Pydantic Documentation](https://docs.pydantic.dev/) - Data validation
- [FastAPI Guide](https://fastapi.tiangolo.com/) - API framework
- [Typer CLI](https://typer.tiangolo.com/) - CLI building
- [pytest Guide](https://docs.pytest.org/) - Testing framework

**AI Service APIs:**
- [OpenAI API](https://platform.openai.com/docs)
- [Anthropic API](https://docs.anthropic.com/)
- [ElevenLabs API](https://elevenlabs.io/docs)
- [Google Cloud TTS](https://cloud.google.com/text-to-speech/docs)

---

**Next Steps:** Review [DEVELOPMENT.md](DEVELOPMENT.md) and pick a work package from [work_packages/README.md](work_packages/README.md)
