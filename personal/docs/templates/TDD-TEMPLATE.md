# Technical Design Document — [Project Name]

> **Status**: Draft | In Review | Approved
> **Author**: [Name]
> **Last Updated**: [Date]
> **Depends on**: PRD.md (must be approved first)

## 1. Architecture Overview
<!-- High-level system design. Describe the main components and how they interact. -->

## 2. Component Design

### 2.1 Data Ingestion Layer
<!-- How data enters the system. APIs, scraping, file uploads, etc. -->

### 2.2 Processing & Transformation Layer
<!-- How raw data becomes usable. Cleaning, enrichment, normalization. -->

### 2.3 Analytical / Business Logic Layer
<!-- Core logic that produces value. Algorithms, scoring, filtering, ML models. -->

### 2.4 Storage Layer
<!-- Where and how data is persisted. Database schema, file storage, caching. -->

### 2.5 Presentation Layer
<!-- How results reach the user. Dashboard, CLI output, notifications, API. -->

## 3. Technology Stack
| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Language | | |
| Framework | | |
| Database | | |
| APIs | | |
| Libraries | | |

## 4. Data Flow Diagram
<!-- Describe or illustrate the flow: data source → ingestion → processing → storage → output -->

## 5. Security Considerations
<!-- API key management, data sensitivity, access control, rate limiting. -->

## 6. Error Handling Strategy
<!-- How does each component handle failures? Retries, fallbacks, alerting. -->

## 7. Configuration & Environment
<!-- What environment variables, config files, or secrets are needed? -->

## 8. Extensibility Notes
<!-- How is this designed to accommodate future expansion (medium-term goals from PRD)? -->

## 9. Commercial-Option Architecture Checklist

Per CLAUDE.md's "architecture choices that preserve commercial option value" — at ~5-10% upfront effort, these decisions keep the commercial path open. Confirm each for this project. Unchecked items must be explicitly flagged as commercial-option risk at the design gate.

- [ ] **Multi-tenant data model**: `user_id` / `tenant_id` on every table. Single-tenant in PoC/MVP; activated in Beta. — Where applied: [describe or reference schema section]
- [ ] **Domain primitives as first-class data**: What makes this product different lives in the schema, not view-layer logic. — Primitives: [list]
- [ ] **Plugin / registry interfaces at every external boundary**: Parsers, data sources, ML clients are registered through an interface, not selected by `if source == "X"`. — Interfaces: [list]
- [ ] **Abstracted ML / LLM clients**: Model imports use the abstract interface only. Provider swaps touch only the client module. — Interface: [name]
- [ ] **Configuration over hardcoding**: Categories, rules, thresholds, labels, seed data live in config or database rows. — Config location: [path]
- [ ] **Forward-compatible schema decisions**: Schema choices made now to avoid later migrations (e.g., nullable fields for future multi-user, soft-delete columns). — Decisions: [list]

## 10. Commercial-Signal Instrument — Technical Design

Referenced from PRD §4. Describe the technical implementation:
- **Where the signal is recorded**: [file/table]
- **Data captured per event**: [fields]
- **Retrieval path**: [command, query, or dashboard widget]
- **Storage cost estimate**: [rough; confirm it is genuinely cheap]
