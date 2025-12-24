# Work Package Dependency Graph

This document shows the execution phases and parallelization strategy for all Work Packages.

## Phase Breakdown

### Phase 1: Foundation (Can all run in parallel)
- **WP1a**: Core Data Models (1-2 days)
- **WP1b**: Configuration System (1 day)
- **WP8**: Testing Infrastructure (ongoing)

**Parallelization**: All 3 can start immediately and run in parallel.

---

### Phase 2: Storage & Services (After Phase 1)
- **WP0**: Prompt Enhancement (2 days) - Depends on: WP1a, WP1b
- **WP1c**: Show Blueprint Manager (2 days) - Depends on: WP1a, WP1b
- **WP1d**: Episode Storage (1-2 days) - Depends on: WP1a, WP1b
- **WP3**: TTS Service (2 days) - Depends on: WP1a, WP1b
- **WP5**: Image Service (1-2 days) - Depends on: WP1a, WP1b
- **WP10a**: Website (1.5-2 days) - No dependencies (static site)

**Parallelization**: All 6 can run in parallel after Phase 1 completes.

---

### Phase 3: Integration Layer (After Phase 2)
- **WP1e**: Testing & Validation (1 day) - Depends on: WP1a, WP1b, WP1c, WP1d
- **WP2a**: Provider & LLM Early Stages (2-3 days) - Depends on: WP0, WP1a, WP1b
- **WP7a**: Show Management CLI (1-2 days) - Depends on: WP1c
- **WP9a**: Dashboard Backend API (1.5-2 days) - Depends on: WP1c

**Parallelization**: All 4 can run in parallel after their dependencies complete.

---

### Phase 4: Content Generation (After Phase 3)
- **WP2b**: Segment & Script Generation (2 days) - Depends on: WP2a
- **WP4**: Audio Mixer (2 days) - Depends on: WP3
- **WP9b**: Blueprint Editor UI (2-3 days) - Depends on: WP9a, WP5

**Parallelization**: All 3 can run in parallel.

---

### Phase 5: Orchestration Core (After Phase 4)
- **WP6a**: State Machine & Approval (2-3 days) - Depends on: WP0, WP1c, WP2a, WP2b

**Parallelization**: Single critical path item.

---

### Phase 6: Orchestration Integration (After Phase 5)
- **WP6b**: Reliability & Integration (2 days) - Depends on: WP6a, WP3, WP4, WP5

**Parallelization**: Single critical path item.

---

### Phase 7: User Interfaces (After Phase 6)
- **WP7b**: Episode Commands CLI (1-2 days) - Depends on: WP6a, WP6b, WP7a
- **WP9c**: Approval Dashboard UI (2-3 days) - Depends on: WP9a, WP9b, WP6a, WP6b

**Parallelization**: Both can run in parallel.

---

### Phase 8: Distribution (After Phase 7)
- **WP10b**: Podcast Distribution (2-2.5 days) - Depends on: WP6b, WP7b

**Parallelization**: Single item.

---

## Visual Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1: Foundation (ALL PARALLEL)                             │
├─────────────────────────────────────────────────────────────────┤
│  WP1a: Core Models                                              │
│  WP1b: Configuration                                            │
│  WP8:  Testing (ongoing)                                        │
└────────────┬───────────────────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 2: Storage & Services (ALL PARALLEL after Phase 1)       │
├─────────────────────────────────────────────────────────────────┤
│  WP0:   Prompt Enhancement                                      │
│  WP1c:  Show Blueprint Manager                                  │
│  WP1d:  Episode Storage                                         │
│  WP3:   TTS Service                                             │
│  WP5:   Image Service                                           │
│  WP10a: Website (static)                                        │
└────┬────────┬────────┬────────┬────────┬──────────────────────┘
     │        │        │        │        │
     ↓        ↓        ↓        ↓        ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 3: Integration Layer (PARALLEL)                          │
├─────────────────────────────────────────────────────────────────┤
│  WP1e: Testing & Validation                                     │
│  WP2a: LLM Provider & Early Stages                              │
│  WP7a: Show Management CLI                                      │
│  WP9a: Dashboard Backend API                                    │
└────┬────────┬────────┬────────┬─────────────────────────────────┘
     │        │        │        │
     ↓        ↓        ↓        ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 4: Content Generation (PARALLEL)                         │
├─────────────────────────────────────────────────────────────────┤
│  WP2b: Segment & Script Generation                              │
│  WP4:  Audio Mixer                                              │
│  WP9b: Blueprint Editor UI                                      │
└────┬────────┬────────┬─────────────────────────────────────────┘
     │        │        │
     └────────┴────┬───┘
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 5: Orchestration Core                                    │
├─────────────────────────────────────────────────────────────────┤
│  WP6a: State Machine & Approval                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 6: Orchestration Integration                             │
├─────────────────────────────────────────────────────────────────┤
│  WP6b: Reliability & Integration                                │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 7: User Interfaces (PARALLEL)                            │
├─────────────────────────────────────────────────────────────────┤
│  WP7b: Episode Commands CLI                                     │
│  WP9c: Approval Dashboard UI                                    │
└────┬────────┬───────────────────────────────────────────────────┘
     └────────┴─────────┐
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 8: Distribution                                           │
├─────────────────────────────────────────────────────────────────┤
│  WP10b: Podcast Distribution                                    │
└─────────────────────────────────────────────────────────────────┘
```

## Maximum Parallelization Strategy

### Week 1: Foundation
- **Day 1-2**: Start WP1a, WP1b, WP8 (3 agents in parallel)
- **Result**: Core models and config ready

### Week 2: Services Layer
- **Day 3-5**: Start WP0, WP1c, WP1d, WP3, WP5, WP10a (6 agents in parallel)
- **Result**: All foundation services ready

### Week 3: Integration & Content
- **Day 6-8**: Start WP1e, WP2a, WP7a, WP9a (4 agents in parallel)
- **Day 8-10**: Start WP2b, WP4, WP9b (3 agents in parallel)
- **Result**: Content generation and basic UIs ready

### Week 4: Orchestration
- **Day 11-13**: Start WP6a (1 agent)
- **Day 13-15**: Start WP6b (1 agent)
- **Result**: Full pipeline operational

### Week 5: Final UIs & Distribution
- **Day 16-18**: Start WP7b, WP9c (2 agents in parallel)
- **Day 18-20**: Start WP10b (1 agent)
- **Result**: Complete system with distribution

## Critical Path

The **critical path** (longest sequential chain) is:
```
WP1a → WP1c → WP2a → WP2b → WP6a → WP6b → WP7b → WP10b
```

**Estimated critical path duration**: ~16-20 days

With parallelization, the actual calendar time can be reduced to **~3-4 weeks** if multiple agents work simultaneously.

## Dependencies Matrix

| WP | Depends On | Phase | Can Parallelize With |
|----|-----------|-------|---------------------|
| WP1a | None | 1 | WP1b, WP8 |
| WP1b | None | 1 | WP1a, WP8 |
| WP8 | None | 1 | WP1a, WP1b |
| WP0 | WP1a, WP1b | 2 | WP1c, WP1d, WP3, WP5, WP10a |
| WP1c | WP1a, WP1b | 2 | WP0, WP1d, WP3, WP5, WP10a |
| WP1d | WP1a, WP1b | 2 | WP0, WP1c, WP3, WP5, WP10a |
| WP3 | WP1a, WP1b | 2 | WP0, WP1c, WP1d, WP5, WP10a |
| WP5 | WP1a, WP1b | 2 | WP0, WP1c, WP1d, WP3, WP10a |
| WP10a | None | 2 | WP0, WP1c, WP1d, WP3, WP5 |
| WP1e | WP1a, WP1b, WP1c, WP1d | 3 | WP2a, WP7a, WP9a |
| WP2a | WP0, WP1a, WP1b | 3 | WP1e, WP7a, WP9a |
| WP7a | WP1c | 3 | WP1e, WP2a, WP9a |
| WP9a | WP1c | 3 | WP1e, WP2a, WP7a |
| WP2b | WP2a | 4 | WP4, WP9b |
| WP4 | WP3 | 4 | WP2b, WP9b |
| WP9b | WP9a, WP5 | 4 | WP2b, WP4 |
| WP6a | WP0, WP1c, WP2a, WP2b | 5 | None (critical) |
| WP6b | WP6a, WP3, WP4, WP5 | 6 | None (critical) |
| WP7b | WP6a, WP6b, WP7a | 7 | WP9c |
| WP9c | WP9a, WP9b, WP6a, WP6b | 7 | WP7b |
| WP10b | WP6b, WP7b | 8 | None (final) |

## Ready to Start Now

These Work Packages have **no dependencies** and can be started immediately:
- ✅ **WP1a**: Core Data Models
- ✅ **WP1b**: Configuration System
- ✅ **WP8**: Testing Infrastructure
- ✅ **WP10a**: Website (static site)

**Recommendation**: Start with WP1a and WP1b as they unlock the most downstream work.
