# AI4OHS-HYBRID Migration Plan

## Objective
This document outlines the step-by-step migration plan to transition the existing AI4OHS-HYBRID structure into the new Agentic AI–aligned directory schema.

---

## Phase 0 – Cleanup & Standardization
### Tasks
- Normalize directory structure.
- Move all RAG-related code into `src/genai/rag/`.
- Move compliance/guardrail logic into `src/governance/`.
- Consolidate YAML configs under `config/`.
- Organize domain knowledge into `knowledge/` as .md sources.

### Deliverables
- Clean folder structure
- Unified config files
- Standard naming conventions

---

## Phase 1 – Core GenAI + RAG Stabilization
### Tasks
- Implement unified LLM client architecture.
- Define RAG pipelines (incident, checklist, gap analysis).
- Configure FAISS index builder.
- Standardize prompt templates.

### Deliverables
- Stable RAG engine
- Tested LLM clients
- Prompt library

---

## Phase 2 – Compliance & Governance (CAG Layer)
### Tasks
- Implement rule-based CAG engine.
- Integrate 6331, IFC ESS, ISO 45001 into rules.
- Add safety filters to block unsafe recommendations.
- Add audit logging for traceability.

### Deliverables
- CAG validation layer
- Safety policy enforcement
- Mevzuat-backed response chain

---

## Phase 3 – AI Agents Layer
### Tasks
- Build modular agents (Incident, Checklist, Reporting).
- Add tool-calling functions (Excel, Docx, notifications).
- Add orchestration router for task selection.

### Deliverables
- Autonomous task agents
- Tool library
- Multi-agent orchestration

---

## Phase 4 – Agentic AI Layer (Planning, Memory, Self-Reflection)
### Tasks
- Implement planning module (ReAct / CoT / ToT).
- Add short-term and long-term memory.
- Integrate self-evaluation and error recovery.
- Add rollback mechanisms.

### Deliverables
- Self-correcting agent system
- Memory-supported workflows
- Multi-step planning capability

---

## Phase 5 – Monitoring & Observability
### Tasks
- Add telemetry (latency, token usage, error tracking).
- Add tracing (end-to-end chain visibility).
- Build governance dashboard.
- Document risk & safety model.

### Deliverables
- Full observability stack
- Audit-ready logs
- Governance policy documentation

---

## Final Outcomes
- Fully modular, agent-ready AI4OHS-HYBRID architecture.
- Compliant with 6331, IFC ESS, ISO 45001.
- Safe, stable, traceable GenAI + Agentic AI foundation.
