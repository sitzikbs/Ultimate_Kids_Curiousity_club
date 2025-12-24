# Kids Curiosity Club - Project Plan

**Version:** 1.0  
**Last Updated:** December 23, 2025  
**Status:** Planning Complete, Ready for Implementation

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
**GitHub Issue:** TBD

**Key Deliverables:**
- Template system with Jinja2 for show context injection
- Enhancement methods for ideation, outline, segment, script stages
- Prompt versioning and A/B testing capability
- Integration with Show Blueprint data (protagonist, world, characters, concepts)

**Why This Matters:** LLMs need rich context to generate consistent stories. This service automatically injects protagonist values, world rules, covered concepts, and show theme into prompts for each generation stage.

---

### WP1: Foundation
**Purpose:** Core data models, configuration, and Show Blueprint management  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**GitHub Issue:** TBD

**Key Deliverables:**
- Pydantic models (Show, ShowBlueprint, Protagonist, WorldDescription, Character, Episode, StorySegment, Script, etc.)
- Configuration system with mock/real provider switching
- ShowBlueprintManager for loading/validating show data
- Image path support for protagonist, world, characters
- ConceptsHistory tracking to avoid repetition

**Dependencies:** None  
**Blocks:** All other work packages

---

### WP2: LLM Service
**Purpose:** Story content generation through incremental stages  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**GitHub Issue:** TBD

**Key Deliverables:**
- Provider abstraction (OpenAI, Anthropic, Mock)
- IdeationService: topic → story concept
- OutlineService: concept → reviewable story beats
- SegmentGenerationService: outline → detailed segments (what happens)
- ScriptGenerationService: segments → narration + dialogue (how it's told)
- Validation: age-appropriate content checking

**Dependencies:** WP0 (Prompt Enhancement), WP1 (Foundation)  
**Blocks:** WP6 (Orchestrator)

---

### WP3: TTS Service
**Purpose:** Text-to-speech audio synthesis for narrator and character voices  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**GitHub Issue:** TBD

**Key Deliverables:**
- Provider abstraction (ElevenLabs, Google TTS, OpenAI TTS, Mock)
- Audio segment synthesis with voice mapping
- Voice listing and configuration
- Support for narrator + protagonist + supporting character voices

**Dependencies:** WP1 (Foundation)  
**Blocks:** WP6 (Orchestrator)

---

### WP4: Audio Mixer
**Purpose:** Professional audio composition and mixing  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**GitHub Issue:** TBD

**Key Deliverables:**
- Segment sequencing with timing
- Background music generation/layering
- Sound effects at markers
- MP3 export with ID3 metadata

**Dependencies:** WP1 (Foundation)  
**Blocks:** WP6 (Orchestrator)

---

### WP5: Image Service
**Purpose:** Show Blueprint image management and optional generation  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**GitHub Issue:** TBD

**Key Deliverables:**
- Image loading and validation (protagonist, world, characters)
- Optional character/world image generation (Flux, DALL-E)
- Image format conversion and optimization
- Mock image provider
- Image path management in Show Blueprint

**Dependencies:** WP1 (Foundation)  
**Blocks:** WP6 (Orchestrator), WP9 (Dashboard)

---

### WP6: Pipeline Orchestrator
**Purpose:** Coordinate services for end-to-end episode generation with human review  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**GitHub Issue:** TBD

**Key Deliverables:**
- State machine managing pipeline stages (IDEATION → OUTLINING → APPROVAL → SEGMENT → SCRIPT → AUDIO → MIXING)
- Human approval gate after OUTLINING stage
- Checkpointing and resume capability
- Service integration with factory pattern
- Show Blueprint context injection at each stage
- ConceptsHistory update after completion
- Error handling and retry logic

**Dependencies:** WP0, WP1, WP2, WP3, WP4, WP5  
**Blocks:** WP7 (CLI), WP9 (Dashboard)

---

### WP7: CLI Interface
**Purpose:** Command-line interface for show and episode management  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**GitHub Issue:** TBD

**Key Deliverables:**
- Show management commands (`shows list`, `shows create`, `shows init`, `shows info`)
- Show Blueprint commands (`shows characters`, `shows concepts`, `shows suggest-topics`)
- Episode commands (`episodes create`, `episodes list`, `episodes resume`)
- Testing commands (`test tts`, `test llm`)
- Progress tracking and status display

**Dependencies:** WP6 (Orchestrator)  
**Blocks:** None

---

### WP8: Testing Infrastructure
**Purpose:** Comprehensive testing with cost controls  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**GitHub Issue:** TBD

**Key Deliverables:**
- Test fixtures (LLM responses, audio samples, images, story outlines)
- Fixture generation scripts
- Pytest markers and gated tests
- Cost tracking and reporting
- Automated progress tracking
- Story format validation

**Dependencies:** All work packages  
**Ongoing:** Developed alongside other WPs

---

### WP9: Web Dashboard & Review Interface
**Purpose:** Human review interface for outlines, scripts, and Show Blueprint management  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**GitHub Issue:** TBD

**Key Deliverables:**
- FastAPI backend with REST + WebSocket APIs
- React/Vue frontend with rich editor
- Show Blueprint editor (protagonist, world, characters with images)
- Outline approval interface (approve/reject/edit story beats)
- Script editor with audio preview
- Episode pipeline dashboard with progress tracking
- ConceptsHistory viewer (topics already covered)
- Real-time pipeline status updates

**Dependencies:** WP1 (Foundation), WP6 (Orchestrator), WP5 (Image Service)  
**Blocks:** None (enhances workflow)

**Estimated Effort:** 7-10 days

---

### WP10: Website & Distribution
**Purpose:** Public-facing website and podcast distribution pipeline  
**Owner:** Unassigned  
**Status:** 🔴 Not Started  
**GitHub Issue:** TBD

**Key Deliverables:**
- Static website with episode listings (already built, ported from old repo)
- Podcast hosting integration (Transistor.fm, Buzzsprout, or RSS.com)
- RSS feed generation and management
- Automated episode metadata upload
- Audio player integration on website
- Podcast directory submission (Apple, Spotify, Google)
- Analytics and SEO optimization

**Dependencies:** WP6 (Orchestrator - produces final MP3s)  
**Blocks:** None (distribution layer)

**Estimated Effort:** 3-4 days

**Why This Matters:** The content generation pipeline is useless without distribution. This WP handles the "last mile" - getting finished episodes to listeners on their preferred platforms.

---

## 🔄 Work Package Dependencies

```
        WP0 (Prompt)
           ↓
        WP1 (Foundation)
           ↓
    ┌──────┼──────┬──────┐
    ↓      ↓      ↓      ↓
   WP2    WP3    WP4    WP5
  (LLM)  (TTS) (Mixer) (Image)
    └──────┼──────┴──────┘
           ↓
        WP6 (Orchestrator)
           ↓
     ┌─────┼─────┬─────────┐
     ↓     ↓     ↓         ↓
   WP7  WP9   WP10     WP8 (Ongoing)
  (CLI) (Dash) (Website)
```

**Development Sequence:**
1. **Phase 1:** WP0 + WP1 (Foundation)
2. **Phase 2:** WP2, WP3, WP4, WP5 (Can be parallelized)
3. **Phase 3:** WP6 (Integration)
4. **Phase 4:** WP7 + WP9 (CLI + Dashboard)
5. **Ongoing:** WP8 (Testing throughout)

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
- WP1: 3-4 days (Show Blueprint models + management)
- WP2: 4-5 days (4 LLM services: Ideation, Outline, Segment, Script)
- WP3: 2-3 days
- WP4: 2-3 days
- WP5: 1-2 days
- WP6: 3-4 days (Human approval gate + pipeline stages)
- WP7: 2-3 days
- WP9: 7-10 days (Web dashboard)
- WP8: Ongoing

**Total:** ~4-6 weeks for MVP

**With parallel development (multiple agents):**
- Phase 1: 3-4 days (WP0 + WP1)
- Phase 2: 4-5 days (WP2-5 parallel)
- Phase 3: 3-4 days (WP6)
- Phase 4: 7-10 days (WP7 + WP9 parallel)

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
