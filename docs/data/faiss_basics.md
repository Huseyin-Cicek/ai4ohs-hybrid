# FAISS Basics – AI4OHS-HYBRID

## 1. Purpose

This document explains how FAISS is used inside AI4OHS-HYBRID for high‑performance offline semantic search within OHS, HSSE, compliance and regulatory datasets.

## 2. Role of FAISS in the System

FAISS is the **local vector index engine** powering RAG search.
It enables:

- Offline semantic retrieval (no cloud dependency)
- Multi-index separation (OHS, EHS, regulations, incidents)
- GPU‑accelerated vector search (optional)
- Deterministic recall for compliance tasks

## 3. Index Structure

AI4OHS-HYBRID uses the following directory model:

```
H:\DataWarehouse\aii4hsse-clean│
├── faiss/
│   ├── index.faiss
│   ├── index.pkl
│   ├── metadata.json
│   └── embeddings/
│       ├── chunk_000001.npy
│       ├── chunk_000002.npy
│       └── ...
```

- `index.faiss`: FAISS binary index
- `index.pkl`: tokenizer + embedding metadata
- `metadata.json`: document/chunk mapping
- `embeddings/`: raw vector files

## 4. Embedding Model

Default offline embedding model:

```
sentence-transformers/all-MiniLM-L12-v2
```

Configurable via:

```
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L12-v2
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
```

## 5. Pipeline Flow (00 → 03)

### 5.1 00_ingest

- PDFs, DOCX, XLSX, images collected
- Sanitization (FFMP rules)
- Copied into DataLake

### 5.2 01_staging

- Text extraction
- OCR if needed
- Temporary staging JSON output

### 5.3 02_processing

- Chunking (500–1200 tokens)
- Embedding generation
- Metadata assignment

### 5.4 03_rag

- Build FAISS index
- Save index + metadata
- Validate dimensionality consistency

## 6. Query Flow

1. User asks → RAG engine receives text
2. Embed query using same embedding model
3. Search FAISS index
4. Return top‑k results
5. (Optional) Cross‑encoder reranking
6. CAG guardrail validation
7. Final answer

## 7. GPU Acceleration

If CUDA is available:

```
GPU_ACCELERATION=true
```

FAISS automatically uses:

- `IndexFlatIP` GPU variant
- or `IndexIVFFlat` GPU‑enabled version

Speed gain: **15×–30×** for large datasets.

## 8. Consistency Rules

To prevent index corruption:

- Same model must be used for:
  - embeddings
  - query encoder
  - index build
- Index versioning enforced:
  ```
  index_v1.faiss
  index_v2.faiss
  ```
- Metadata hash stored to detect tampering

## 9. Backup Strategy

Daily scheduled backup via Zeus:

```
H:\DataWarehouse\Backups\faiss\YYYY-MM-DD\index.faiss
H:\\DataWarehouse\Backups\faiss\YYYY-MM-DD\metadata.json
```

## 10. Index Rebuild Triggers

Index must be rebuilt if:

- New regulation pack added (e.g., Turkish Law updates)
- New incident/OHS logs ingested
- Model updated
- Corrupted embedding chunk detected
- Hash mismatch in metadata

## 11. Validation Tests

Automatic tests run after each rebuild:

- Embedding dimensionality match
- Vector count match
- Metadata index alignment
- Recall test on sample queries
- Stress test with 10k queries

## 12. CLI Commands

### Rebuild index

```
python src/pipelines/03_rag/run.py
```

### Inspect metadata

```
python tools/show_faiss_info.py
```

### Search test

```
python tools/query_test.py "confined space permit"
```

## 13. Security Notes

- FAISS index can optionally be encrypted using:
  ```
  FAISS_ENCRYPTION_KEY
  ```
- Never store index backups on cloud storage
- Hash recorded in:
  ```
  faiss/metadata.json
  ```

## 14. Change History

- v1.0 – Base FAISS usage documented
- v1.1 – Added GPU rules, rebuild triggers
- v1.2 – Added security + hashing + backup strategy
