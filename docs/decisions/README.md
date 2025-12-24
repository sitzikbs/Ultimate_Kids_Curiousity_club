# Architecture Decision Records (ADRs)

This directory contains architectural decision records documenting key technical decisions made during the project.

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [001](001-mock-first-architecture.md) | Mock-First Development Architecture | ✅ Accepted |
| [002](002-provider-abstraction.md) | Provider Abstraction Pattern | ✅ Accepted |
| [003](003-prompt-enhancement-layer.md) | Prompt Enhancement Layer | ✅ Accepted |
| [004](004-character-schema.md) | Character JSON Schema Design | ✅ Accepted |

## Format

Each ADR follows this structure:
- **Status**: Proposed, Accepted, Deprecated, Superseded
- **Context**: Problem statement and background
- **Decision**: What we decided to do
- **Consequences**: Trade-offs and implications
- **Alternatives Considered**: Other options evaluated

## Principles

1. **Document Significant Decisions**: Record decisions that impact architecture, not trivial choices
2. **Immutable**: Once accepted, ADRs are not edited (create new ADR to supersede)
3. **Concise**: Focus on decision rationale, not implementation details
4. **Timely**: Write ADR when decision is made, not retrospectively
