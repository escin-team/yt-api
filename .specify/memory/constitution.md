<!--
  ============================================================================
  SYNC IMPACT REPORT
  ============================================================================
  Version Change: 1.1.0 → 2.0.0 (Major: testing requirements relaxed for POC)

  Modified Principles:
    - I. Test-First Development → I. POC-Focused Minimal Testing
    - Quality gates updated for optional tests

  Added Sections:
    - None

  Removed Sections:
    - TDD enforcement and coverage targets for POC scope

  Templates Status:
    ✅ plan-template.md - Localization note (正體中文)
    ✅ spec-template.md - Localization note (正體中文)
    ✅ tasks-template.md - Localization note (正體中文)
    ✅ checklist-template.md - Localization note (正體中文)
    ⚠️ commands directory not present; no command templates to update

  Follow-up TODOs: None
  ============================================================================
-->

# YTSearch Constitution

## Core Principles

### I. POC-Focused Minimal Testing

Because this project is a POC, testing is minimized to accelerate delivery:

- Automated tests are OPTIONAL; write only smoke checks when risk is high
- If tests are written, keep them minimal and targeted (smoke or happy-path)
- Manual verification MUST confirm core flows before sharing outputs
- Skip markers MUST NOT be used to hide known issues; log them instead
- When moving beyond POC, reinstate full testing per governance approval

**Rationale**: Prioritizes speed for POC while keeping a basic safety net and a
clear path to reintroduce stronger testing when the project matures.

### II. Clean Architecture

All code MUST follow modular, maintainable architecture principles:

- Code MUST be modular to improve readability and reusability
- Services MUST be independently testable and documented
- Dependencies MUST be explicit and injected, not implicit
- Mock only external dependencies (databases, APIs, file systems)
- Business logic MUST NOT be mocked in tests
- Clear separation between models, services, and interfaces

**Rationale**: Clean architecture enables independent testing, easier maintenance,
and clear boundaries between components.

### III. Explicit Over Implicit

All design decisions MUST favor explicitness:

- Configuration MUST be close to usage, not buried deep
- Parameter values MUST be visible directly
- Use whole words in naming (no cryptic abbreviations)
- Comments MUST explain "why" not "what"
- All inputs MUST be validated

**Rationale**: Explicit code is easier to understand, debug, and maintain.
New team members can understand the codebase without tribal knowledge.

### IV. Simplicity First

All solutions MUST favor simplicity:

- Start simple, follow YAGNI (You Aren't Gonna Need It)
- Prefer a few repeated lines over excessive abstraction
- No premature optimization
- Complexity MUST be justified in PR reviews
- Prefer arrow functions `=>`
- Prefer declarative over imperative where appropriate

**Rationale**: Simple code is easier to maintain, debug, and extend.
Complexity introduces bugs and cognitive overhead.

### V. Observability & Security

All code MUST be observable and secure:

- Structured logging MUST be used (logger, not print)
- All security events MUST be logged
- Sensitive information MUST be stored in environment variables
- All inputs MUST be validated to prevent injection attacks
- Error handling MUST be explicit with proper exception handling and user-safe messages
- API usage MUST respect platform policies (e.g., YouTube Terms of Service)

**Rationale**: Observable systems are debuggable. Secure systems protect user data
and prevent exploits.

### VI. Traditional Chinese Documentation (NON-NEGOTIABLE)

All documentation MUST be authored in Traditional Chinese, including outputs from
all `/speckit` commands and subsequent generated artifacts:

- Plans, specs, tasks, checklists, research, and quickstart files MUST use
  Traditional Chinese
- Code comments MAY remain in English when required for tooling, but prefer
  Traditional Chinese when feasible
- User-visible strings MUST follow project language requirements; default is
  Traditional Chinese unless product requirements state otherwise
- Backfill or newly created docs MUST avoid Simplified Chinese or mixed locale

**Rationale**: Consistent localization reduces ambiguity for the team and matches
expected deliverables for stakeholders.

## Domain Requirements: YouTube Keyword Metadata Search

YTSearch exists to search YouTube by keyword and return the best-matching video
metadata for downstream use:

- Primary outcome is metadata (e.g., title, description, channel, publish date,
  duration, view count, URL); no media downloading
- Ranking MUST prioritize relevance to provided keywords
- Results MUST respect YouTube Terms of Service and API quotas
- Data handling MUST avoid storing or distributing media content

**Rationale**: Clear domain focus ensures technical decisions align with the core
value of providing accurate YouTube metadata without policy violations.

## Technology Stack

**Primary Technologies**:

- **Backend Language**: Python 3.12+ (PEP 8, PEP 20, PEP 257 compliant)
- **Package Manager**: uv (replacing pip)
- **Testing Framework**: pytest with fixtures and parameterized tests
- **API Framework**: FastAPI with Pydantic validation
- **Shell**: zsh syntax for all terminal commands

**Dependency Management**:

- Use `pyproject.toml` for Python dependency management
- Pin dependencies to specific versions for reproducibility
- Use virtual environments (venv) to isolate project dependencies
- Regularly update dependencies and test for compatibility
- Prefer YouTube Data API or compliant services for search and metadata

**Code Standards**:

- PascalCase for types and enum values
- camelCase for functions, methods, properties, and local variables
- "double quotes" for user-visible strings
- 'single quotes' otherwise
- JSDoc style comments for functions, interfaces, enums, and classes

## Development Workflow

**Code Review Requirements**:

- All PRs MUST verify Constitution compliance
- Automated tests are OPTIONAL for POC; if present, they MUST pass
- Complexity additions MUST be justified
- All documentation changes MUST be in Traditional Chinese; reviewers MUST block
  non-compliant docs

**Quality Gates**:

1. Linting and formatting checks MUST pass
2. If automated tests exist, they MUST pass; otherwise manual smoke check is required
3. No test skip markers for hiding problems
4. Documentation and `/speckit` outputs MUST be in Traditional Chinese

**Version Control**:

- Follow clear branching strategy (Git Flow or Trunk-Based Development)
- Write concise and descriptive commit messages
- Use pull requests for code reviews

## Governance

This Constitution supersedes all other practices. Amendments require:

1. Documentation of proposed change
2. Review and approval by project maintainers
3. Migration plan for affected code/processes
4. Version increment according to semantic versioning:
   - MAJOR: Backward incompatible governance/principle changes
   - MINOR: New principle/section added or materially expanded
   - PATCH: Clarifications, wording, typo fixes

Documentation localization is enforced for all `/speckit` command outputs and
repository documentation.

All PRs and reviews MUST verify compliance with this Constitution.
Use `.github/instructions/` files for runtime development guidance.

**Version**: 2.0.0 | **Ratified**: 2025-12-06 | **Last Amended**: 2025-12-06
