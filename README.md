# AI4OHS-HYBRID — Dual-Mode OHS Intelligence Engine

**RAG + CAG + Compliance Guardrails + Offline/Online Execution + Local Automations (Zeus Layer)**
AI4OHS-HYBRID, yüksek uyumluluk gerektiren altyapı projeleri (World Bank / IFC ESS, ISO 45001, OSHA, Türk 6331 Sayılı Kanun ve ilgili yönetmelikler) için tasarlanmış **tamamen yerel çalışabilir (offline-first)** bir OHS bilgi sistemi ve otomasyon platformudur.

Platform; ETL → Staging → Processing → RAG → CAG → Automation akışını uçtan uca yönetir ve tüm OHS/HSSE dokümantasyonunu tek bir bütünleşik yapıda işler.

---

# 1. General Overview

AI4OHS-HYBRID aşağıdaki beş ana katmandan oluşur:

| Layer                                     | Description                                                                                           |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **RAG – Retrieval-Augmented Generation**  | FAISS tabanlı lokal vektör arama motoru. Tüm OHS/EHS verisi offline erişilebilir.                     |
| **CAG – Compliance-Augmented Generation** | ISO 45001, ISO 14001, OSHA 29 CFR, Türk 6331 Kanunu ve WB/IFC ESS için rule-based validasyon sistemi. |
| **ETL Pipelines**                         | 00_ingest → 01_staging → 02_processing → 03_rag süreçleriyle embedding + index üretimi.               |
| **Zeus Automation Layer**                 | Voice-trigger (“Hey Zeus”), FFMP, background workers.                                                 |
| **Dual Execution Mode**                   | İnternet bağlantısız %100 offline veya cloud destekli online çalışma.                                 |

## Core Features

-   Offline-first RAG search (FAISS)
-   CAG rule engine with deterministic validation
-   Python 3.11.9 full support
-   GPU-accelerated semantic search (CUDA 12.x)
-   Automated ingestion & chunking
-   Voice-assisted automation (Zeus Listener)
-   OHS/HSSE compliance enforcement
-   VSCode-integrated pipelines
-   Deterministic environment with pinned requirements

---

# 2. Repository Structure

```
AI4OHS-HYBRID/
├── src/
│   ├── pipelines/
│   ├── ohs/api/
│   └── utils/
├── scripts/
│   ├── dev/
│   ├── tools/
│   └── offline_hooks/
├── docs/
│   ├── ai4ohs_overview.md
│   ├── perf_stability_quickstart.md
│   ├── dev_env_quickstart.md
│   ├── compliance/
│   ├── data/
│   ├── automation/
│   └── background/
├── logs/
├── DataLake/
├── DataWarehouse/
├── .vscode/
├── requirements.txt
├── .env
└── README.md
```

---

# 3. Pipelines & API Usage

## 3.1 Full ETL Pipeline Execution

```powershell
python src/pipelines/00_ingest/run.py
python src/pipelines/01_staging/run.py
python src/pipelines/02_processing/run.py
python src/pipelines/03_rag/run.py
```

Tek komut:

```powershell
python scripts/dev/run_all_pipelines.py
```

## 3.2 Start Local API

```powershell
uvicorn src.ohs.api.main:app --reload --host 127.0.0.1 --port 8000
```

---

# 4. Offline / Online Configuration

| Variable                | Description              |
| ----------------------- | ------------------------ |
| `OFFLINE_MODE=true`     | İnternet olmadan çalışır |
| `GPU_ACCELERATION=true` | CUDA varsa hızlanır      |
| `EMBEDDING_MODEL`       | all-MiniLM-L12-v2        |
| `RERANKER_MODEL`        | ms-marco-MiniLM-L-6-v2   |

---

# 5. Developer Tools (Zeus Layer)

### Zeus Listener

-   Hey Zeus ile tetiklenebilir
-   Pipelines çalıştırır
-   Status bildirimi yapar

### Auto ML Worker

-   Yeni dokümanları normalize eder
-   TF-IDF + cluster summary üretir
-   `logs/dev/zeus_ml_summary.json`

### FFMP

-   File normalization
-   Duplicate detection
-   Backup management

---

# 6. Compliance / Guardrails (CAG Layer)

### Validations

-   ISO 45001 / ISO 14001
-   OSHA 29 CFR
-   Türk 6331 Kanunu
-   Dünya Bankası ESS1–ESS10

### Features

-   Regex + keyword + structural rule engine
-   LLM-free deterministic validation
-   Severity scoring
-   Non-compliant öneri bloklama

---

# 7. Contributing & Git Rules

### Allowed

-   `src/*`
-   `scripts/*`
-   `docs/*`

### Forbidden

-   `logs/`
-   `DataLake/`
-   `.env`, `.env.local`
-   Model weights

### Commit Format

```
feat:
fix:
docs:
refactor:
pipeline:
api:
```

---

# 8. Development Environment

### Python 3.11.9 Recommended

### Create venv

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### VSCode Integration

-   Ruff + Black format
-   Minimap off
-   Heavy watchers disabled

---

# 9. Requirements Summary

### Includes

-   FAISS
-   Transformers + Sentence-Transformers
-   Torch CUDA stack
-   NLP/RAG utils
-   FastAPI / Uvicorn
-   Dev tools (Black, Ruff, Pytest)

Install:

```powershell
pip install -r requirements.txt --index-url https://download.pytorch.org/whl/cu121
```

---

# 10. FAISS Index Architecture

```
DataWarehouse/ai4hsse-clean/faiss/
├── index.faiss
├── index.pkl
├── metadata.json
└── embeddings/
```

Rebuild triggers:

-   New regulations
-   New incidents
-   Model update
-   Hash mismatch

---

# 11. Secrets Management

Never commit:

```
.env
.env.local
secrets/
logs/
DataLake/
DataWarehouse/
```

Encrypted using:

-   DPAPI + Fernet

---

# 12. System Health

-   API: `/health`
-   Worker: `logs/health.json`
-   Zeus markers: ok / degraded / down

---

# 13. Roadmap

-   Multi-index RAG
-   Offline YOLO hazard detection
-   Expanded CAG registry
-   Autonomous worker execution

---

# 14. License

Internal proprietary AI4OHS-HYBRID system.

---

# 15. Contact

AI4OHS-HYBRID System Architect

Specialized Competencies

-   Occupational Health & Safety (OHS / HSSE) system design
-   World Bank / IFC ESS safeguard integration
-   ISO 45001 & ISO 14001 compliant management systems
-   Risk & compliance assessment for large-scale infrastructure projects
-   RAG + CAG hybrid AI safety engines
-   Offline-first data pipelines & FAISS vector indexing
-   Python + VSCode + GPU-accelerated ML workflows
-   Field-level safety operations & incident analysis integration

Role in the AI4OHS-HYBRID Project

-   End-to-end architecture design
-   Compliance-driven guardrail model development
-   ETL & data governance framework
-   System performance & stability optimization
-   Zeus Automation Layer conceptual design
-   Standards, regulatory mapping, and HSSE dataset structuring
-   Full dual-mode (offline/online) operational design
