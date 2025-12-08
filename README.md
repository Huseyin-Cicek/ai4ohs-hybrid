# AI4OHS-HYBRID - Agentic HSSE/OHS Intelligence System

## Overview

AI4OHS-HYBRID is an offline-first OHS intelligence engine that combines:

- Agentic AI (PLAN -> ACT -> REFLECT -> CORRECT -> LEARN)
- RAG (Retrieval-Augmented Generation) with FAISS
- CAG (Compliance-Augmented Guardrails)
- Guarded inference (system prompt + SelfEvaluator/RewriteFlow)
- Llama.cpp local inference
- ML pipelines (risk prediction, incident classification)
- Annual & quarterly automated OHS reporting
- Zeus Voice Interface (offline)

Optimized for:
- Turkish OHS law (6331 + regulations)
- ISO 45001
- OSHA 29 CFR
- WB/IFC ESS1-ESS10
- High-compliance infra projects (e.g., TERRP)

---

## Directory Structure (Core Components)

```
src/
  agentic/
    planner_optimized.py
    self_evaluator.py
    self_eval_rewrite_flow.py
    guarded_inference.py
    task_graphs/
      annual_report_task_graph.py
  agents/
    annual_report_agent.py
  ai_ml/
    incident/incident_classifier.py
    risk_scoring/
      hazard_vectorizer.py
      risk_forecast_model.py
      risk_pipeline.py
    reporting/
      ohs_kpi_dashboard.py
      annual_ohs_report_generator.py
      integrated_kpi_risk_dashboard.py
      advanced_dashboard.py
  governance/
    audit_logger.py
    compliance_heatmap.py
    cag_rules_engine.py
  genai/rag/
    document_loader.py
    ocr_ingest.py
    chunker.py
  zeus_layer/
    listener.py
    startup_tasks.py
scripts/
  run_guarded_llama.py
  run_autonomy_cycle.py
```

---

## Key Components

### 1. Agentic Task Graph for Annual Reports
`src/agentic/task_graphs/annual_report_task_graph.py`
- DAG steps: load incidents -> load ESS/6331 -> compute KPI -> heatmap -> Word+Excel -> validate.
```python
from agentic.task_graphs.annual_report_task_graph import AnnualReportTaskGraph
result = AnnualReportTaskGraph().execute()
```

### 2. Integrated KPI + Risk Dashboard
- Combines TRIR/LTIFR/Severity + ML risk forecast (`integrated_kpi_risk_dashboard.py`).

### 3. Risk Pipeline
`UnifiedRiskPipeline` merges incident classification + hazard vectorization + ML risk forecast (XGBoost/MLP).

### 4. Annual Report Generator
Creates Word/Excel and KPI PNG (`ai_ml/reporting/annual_ohs_report_generator.py`).

### 5. Zeus Offline Voice Interface
Keyword triggers pipelines (`zeus_layer/listener.py`).

### 6. Self-Evaluation Rewrite Loop
`RewriteFlow` + `SelfEvaluator` auto-rewrites low-scoring outputs.

### 7. Guarded Inference (OHS Expert Persona)
- System prompt + guardrails + RAG context: `scripts/run_guarded_llama.py`
- Self-eval/auto-rewrite: `--self-eval --threshold 0.8`
- Prompt builder: `src/genai/prompting/ohs_prompt_builder.py`
- Llama client with ctx/timeout/retry: `src/agentic/llama_learning_integration/llama_client.py`

### 8. OCR -> RAG Ingest
- OCR-capable loader for images/PDF/docx: `src/genai/rag/document_loader.py`
- Direct OCR helper: `src/genai/rag/ocr_ingest.py`
- Plug screenshots into RAG ingest to “learn” from the screen.

### 9. Autonomous Cycle (Proposals)
- `scripts/run_autonomy_cycle.py`: SelfPlanning -> ACE dry-run -> SelfHealing -> SelfEvolving -> Approval queue (`AUTONOMY_CYCLE`).
- ACE/FERS writes to main repo only after ApprovalManager approval (`ACE_ALLOW_AUTO_APPLY` env to bypass; not recommended).

---

## Data Requirements

`data/analytics/` must contain:
- `incidents_annual.json`
- `ess_6331_items.json`

---

## Output Standards

All outputs must include:
- Safety-first hierarchy
- Compliance mapping (6331 / ISO 45001 / WB ESS)
- Residual risk assessment
- CAPA / Preventive actions
- Strictest rule wins; state uncertainty if data is missing
