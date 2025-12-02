# AI4OHS‑HYBRID — Performance & Stability Checklist
**Version:** 2025-11-10 • **Scope:** VS Code + GitHub Copilot • **Principles:** Offline‑first • Deterministic • Filesystem IPC • Production‑grade

This checklist is the copy‑paste‑ready execution plan to stabilize, harden, and document AI4OHS‑HYBRID. It is ordered by **criticality** and aligned with **Phase 1→5** delivery.

---

## 🔹 Phase 1 — Foundation & Stability Layer (Critical)
**Goal:** Deterministic offline operation, share‑nothing processes, file‑based IPC, safe writes.

### Tasks
1. **State Manager (Three‑Tier State Model)** — `src/core/state_manager.py`  
   - Implements **Stamps (When?) + Logs (What?) + Cache (Already?)**
   - Provides `get_stamp/set_stamp`, `append_log(jsonl)`, `cache_get/cache_set`

2. **Atomic Write Utility** — `src/utils/io_safe.py`  
   - Temp file write + `os.replace` rename (POSIX‑safe; Windows‑safe)  
   - `safe_write_text(path, data)`, `safe_write_bytes(path, data)`

3. **Append‑Only Logs** — `src/core/logs/append_only_log.py`  
   - JSON Lines with monotonic timestamp; no overwrite, only append  
   - `append(record: dict)`, `tail(n)`, rotation hook

4. **Idempotency & Retries** — `src/utils/retry.py`  
   - Exponential backoff, jitter, deduplication via content hash stamp  
   - Decorator: `@retry_idempotent(max_tries=3, backoff=0.5)`

5. **Offline‑First Settings** — `src/config/settings.py` & `.env.example`  
   - `OFFLINE_MODE=true` default, no network calls allowed in pipelines  
   - Guard: raise if external dependency attempted in offline mode

6. **Filesystem IPC Layout** — `logs/_ipc/`  
   - Folders: `_ipc/queue`, `_ipc/state`, `_ipc/tmp`  
   - Queue file schema: `{"task":"stage_00_ingest","args":{},"created":"ISO8601"}`

7. **Process Isolation Test** — `tests/test_process_isolation.py`  
   - Start/stop each process independently; verify no shared mutable state

8. **In‑Memory Cache** — `src/core/cache.py`  
   - LRU for metadata & rule lookups; TTL support

9. **Rotation & Archiving** — `src/core/rotate.py`  
   - Log & metrics file rotation by size/date; moves archives to `logs/archive/`

10. **Resource Monitor** — `src/core/monitor.py`  
    - Periodic CPU/RAM/Disk sampling; emits JSON lines to `logs/system/metrics.jsonl`

**Output:** Stable offline base; deterministic, crash‑safe operations.

---

## 🔹 Phase 2 — Compliance‑Augmented Generation (CAG) (Critical)
**Goal:** Deterministic, rule‑based compliance validator with cross‑standard mapping and traceability.

### Tasks
11. **Rule Registry (YAML/JSON)** — `src/cag/rules/`  
    - Categories: Excavation, Confined Space, Fire Safety, Electrical, PPE, Training, Documentation, Incident Reporting

12. **Regex/Keyword Validator** — `src/cag/validator.py`  
    - Deterministic checks (no LLM); structural matchers; per‑rule context

13. **Cross‑Standard Map** — `src/cag/standards_map.json`  
    - **ISO 45001 ↔ WB/IFC ESS ↔ OSHA ↔ TR 6331** (bidirectional)

14. **Conflict Hierarchy** — `src/cag/standards_hierarchy.json`  
    - Precedence table (project‑specific, editable): e.g., ESS > ISO > OSHA > TR 6331 (adjust per governance)

15. **Traceability Matrix Generator** — `src/cag/trace_matrix.py`  
    - Output: `rule_id → sources[] → severity → remediation`

16. **Severity & Remediation** — `src/cag/severity_model.py`  
    - Critical/Major/Minor; templated fix instructions

17. **CAG Reports** — `src/cag/report.py`  
    - Writes `logs/compliance/violations_YYYYMMDD.json` and `.txt` summary

18. **Unit Tests (CAG)** — `tests/test_cag_rules.py`  
    - Coverage for each category, severity mapping, conflict resolution

**Output:** Full offline compliance validation with actionable remediation.

---

## 🔹 Phase 3 — Zeus Automation Layer (Critical)
**Goal:** Watcher‑driven orchestration, auto‑recovery, thread‑safe operations.

### Tasks
19. **Zeus Controller** — `scripts/dev/zeus_main.py`  
    - Boot supervisor; loads settings; starts watchers and workers

20. **Hot Folder Watcher** — `scripts/dev/zeus_watcher.py`  
    - Watchdog on ingress folders; enqueue tasks into `_ipc/queue`

21. **Auto‑Recovery** — `scripts/dev/zeus_recovery.py`  
    - Detects partial runs; replays last safe checkpoint via stamps

22. **Runtime Integration** — `scripts/dev/zeus_runtime.py`  
    - Wires `state_manager`, `validator`, pipelines (00→03)

23. **Metrics Collector** — `logs/zeus_metrics.jsonl`  
    - Aggregates per‑task timing, pass/fail, resource stats

24. **Pipelines Runner** — `scripts/dev/run_all_pipelines.py`  
    - Sequential 00→03; exit codes; warning aggregation

25. **PowerShell Launcher** — `scripts/dev/run_all_pipelines.ps1`  
    - Colorized; Task Scheduler friendly

26. **Thread Safety Utilities** — `src/core/thread_lock.py`  
    - File locks & cross‑process mutex abstraction

27. **Error/Warning Aggregator** — `src/utils/error_collector.py`  
    - Structured warnings; attaches to reports

**Output:** Autonomous orchestration with safe recovery and metrics.

---

## 🔹 Phase 4 — Error Handling & Observability (High)
**Goal:** Fail‑gracefully, inspect‑everywhere, test‑first reliability.

### Tasks
28. **Central Error Handler** — `src/utils/error_handler.py`  
    - Uniform exceptions; rich context; log integration

29. **Warnings Collector** — `src/utils/warnings.py`  
    - Collects non‑fatal anomalies; emits JSONL

30. **Graceful Missing/Corrupt Handling** — `src/core/validator.py`  
    - Validates inputs; quarantines unsafe files

31. **Unix‑Inspectable Logs** — `logs/system/`  
    - JSON Lines compatible with `tail`, `grep`, `jq`

32. **Self‑Test CLI** — `src/selfcheck.py`  
    - `python -m src.selfcheck` runs smoke checks

33. **Offline‑Mode Tests** — `tests/test_offline_mode.py`  
    - Assert no network/socket calls when offline

34. **CI: pytest + coverage** — `.vscode/tasks.json` & `tests/`  
    - VS Code task to run tests & produce `coverage.xml`

**Output:** Errors are visible, recoverable, and measurable.

---

## 🔹 Phase 5 — Docs, Templates & Copilot Enablement (High)
**Goal:** One‑click onboarding, consistent conventions, Copilot‑aware context.

### Tasks
35. **This Checklist File** — `docs/dev_checklist_performance_stability.md` (you are here)

36. **README: Quick Reference Matrix** — `README.md`  
    - Summarize phases, entry points, scripts, and logs

37. **Best Practices (5 Buckets)** — `docs/best_practices.md`  
    - OHS, Data, Logs, Security, Automation

38. **Examples Pack** — `docs/examples/`  
    - JSON schemas, log samples, file paths

39. **Architecture Overview** — `docs/system_architecture.md`  
    - Zeus + CAG + RAG overview diagram & narrative

40. **Dev Env Guide** — `docs/dev_env_setup.md`  
    - Cross‑platform specifics (Windows/Linux), zero‑config

41. **Copilot Context** — `.vscode/settings.json`  
    - Include `docs/` and `src/` key files for better suggestions

**Output:** Developer‑ready, well‑documented repository.

---

## 🧠 Key Implementation Principles
- **Offline‑First:** Default to `OFFLINE_MODE=true`; forbid network IO in pipelines.
- **Filesystem IPC:** `_ipc/queue|state|tmp` as the only coordination channel.
- **Determinism:** Append‑only logs, atomic write, idempotent runners.
- **Process Isolation:** Share‑nothing architecture; independent failure domains.
- **Observability:** JSONL logs everywhere; human‑inspectable with standard tools.
- **Security‑by‑Design:** Whitelist inputs; validate; quarantine when in doubt.

---

## 📌 Quick Reference Matrix
| Area | File/Path | Command/Hook | Notes |
|------|-----------|--------------|-------|
| Run all pipelines | `scripts/dev/run_all_pipelines.py` | `python scripts/dev/run_all_pipelines.py` | Sequential 00→03 with exit codes |
| Self‑test | `src/selfcheck.py` | `python -m src.selfcheck` | Smoke check for config/paths |
| Zeus supervisor | `scripts/dev/zeus_main.py` | `python scripts/dev/zeus_main.py` | Starts watchers & workers |
| CAG validate | `src/cag/validator.py` | Imported by pipelines | Deterministic rules |
| Metrics | `logs/system/metrics.jsonl` | `tail -f ...` | JSONL, jq‑friendly |
| IPC queue | `logs/_ipc/queue/` | File drop | Hot‑folder trigger |

---

## 🧪 Minimal TDD Snippets
```python
# tests/test_process_isolation.py
def test_independent_processes():
    # spawn workers, ensure no shared globals are mutated
    assert True
```

```python
# tests/test_offline_mode.py
def test_offline_guard_blocks_network_calls():
    # monkeypatch socket/http libs to raise if used
    assert True
```

---

## ✅ Definition of Done (Per Phase)
- **P1:** Offline‑first enforced; atomic writes; append‑only logs; IPC folders live.
- **P2:** CAG rules loaded; validator passes tests; violations report emitted.
- **P3:** Zeus watcher triggers pipelines; recovery replays checkpoints.
- **P4:** `selfcheck` green; errors/warnings visible; quarantine active.
- **P5:** Docs complete; Copilot context configured; examples available.
