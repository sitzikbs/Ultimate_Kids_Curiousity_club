# Kids Curiosity Club - Documentation

**Last Updated:** December 21, 2025

## Overview

This directory contains comprehensive planning and technical documentation for the AI-powered **story-based educational podcast** generation system. The system creates adventures featuring protagonist characters (Oliver for STEM, Hannah for History) that naturally teach concepts - similar to Purple Rocket or Snoop & Sniffy.

**Key Architecture:** Multi-show system with **Show Blueprint** (centralized show data), incremental story generation (outline → segments → scripts), and human approval gate after outlining.

## Documentation Structure

### 📋 Core Planning
- **[PLAN.md](PLAN.md)** - High-level project plan, MVP scope, work package summaries
- **[PROGRESS.md](PROGRESS.md)** - Aggregated status tracking across all work packages
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Developer workflow guide, branching strategy, testing

### 📦 Work Packages
- **[work_packages/](work_packages/)** - Detailed specifications for each deliverable module
  - Each WP includes: goals, hierarchical tasks, interface specs, testing requirements
  - See [work_packages/README.md](work_packages/README.md) for index

### 🏗️ Architecture Decisions
- **[decisions/](decisions/)** - Architectural Decision Records (ADRs)
  - Documents significant design choices with context and rationale
  - See [decisions/README.md](decisions/README.md) for index

## Quick Start

1. **Understand the Project**: Start with [PLAN.md](PLAN.md)
2. **Check Status**: Review [PROGRESS.md](PROGRESS.md)
3. **Pick a Task**: Browse [work_packages/](work_packages/) and check GitHub issues
4. **Follow Workflow**: Read [DEVELOPMENT.md](DEVELOPMENT.md)
5. **Understand Decisions**: Reference [decisions/](decisions/) for design rationale

## Work Package Overview

| WP | Name | Status | Dependencies |
|----|------|--------|--------------|
| WP0 | Prompt Enhancement Service | 🔴 Not Started | None |
| WP1 | Foundation (Models, Config, Show Blueprint) | 🔴 Not Started | None |
| WP2 | LLM Services (Ideation, Outline, Segment, Script) | 🔴 Not Started | WP0, WP1 |
| WP3 | TTS Service | 🔴 Not Started | WP1 |
| WP4 | Audio Mixer | 🔴 Not Started | WP1 |
| WP5 | Image Service | 🔴 Not Started | WP1 |
| WP6 | Orchestrator (with Human Approval Gate) | 🔴 Not Started | WP1-5 |
| WP7 | CLI (Show & Episode Management) | 🔴 Not Started | WP1, WP6 |
| WP8 | Testing Infrastructure | 🔴 Not Started | All |
| WP9 | Web Dashboard (Outline Review & Show Blueprint Editor) | 🔴 Not Started | WP1, WP5, WP6 |

**Legend:**
- 🔴 Not Started
- 🟡 In Progress
- 🟢 Complete

## Contributing

1. Assign yourself to a GitHub issue linked to a WP or task
2. Create feature branch: `feature/wp{N}-{task-name}`
3. Follow development workflow in [DEVELOPMENT.md](DEVELOPMENT.md)
4. Update task checkboxes in WP document as you progress
5. Ensure tests pass before PR
6. Link PR to GitHub issue

## Key Concepts

- **Story-Based Format**: Protagonists go on adventures that teach concepts (NOT interviews/discussions)
- **Show Blueprint**: Centralized show data (protagonist + image, world + images, characters + images, concepts_covered.json)
- **Incremental Generation**: Ideation → Outline → Segments → Scripts (4 LLM stages)
- **Human Approval Gate**: Required review after story outline generation
- **Mock-First Development**: All services have mock implementations for cost-free testing
- **Provider Abstraction**: AI services (LLM, TTS, Image) are swappable via configuration
- **Modular Services**: Each WP is independently testable and developable

## Resources

- **GitHub Issues**: [Track WP assignments and progress](../../issues)
- **Cost Tracking**: See WP8 for fixture generation and test cost management
- **Character Schema**: Defined in WP1, used throughout pipeline
- **Testing Strategy**: Unit (mocks) → Service (gated) → E2E (confirmed)

## Questions?

- Review relevant ADR in [decisions/](decisions/)
- Check WP specifications in [work_packages/](work_packages/)
- Refer to interface contracts in [work_packages/INTERFACES.md](work_packages/INTERFACES.md)

---

**Next Steps:**
1. Read [PLAN.md](PLAN.md) for project overview
2. Check [work_packages/README.md](work_packages/README.md) for available tasks
3. Review [DEVELOPMENT.md](DEVELOPMENT.md) for workflow
