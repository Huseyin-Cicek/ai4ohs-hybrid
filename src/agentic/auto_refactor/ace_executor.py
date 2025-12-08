import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .ace_config import ACEConfig
from .fers_refactor_planner import FullEvolutionaryRefactorPlanner
from governance.approval_manager import ApprovalManager


class ACEExecutor:
    """
    ACEExecutor – Orchestrates the ACE/FERS refactor pipeline.

    Responsibilities:
    - Load configuration via ACEConfig (settings.yaml + global_profile + CLI override)
    - Discover target Python files for refactoring
    - Ask FERS planner for evolutionary refactor patches
    - Prepare sandbox repo and apply patches there
    - Run pytest in sandbox
    - If tests pass: apply patches to main repo (unless dry-run)
    - Track auto-merge threshold via a small state file
    """

    def __init__(
        self,
        project_root: str,
        config: Optional[ACEConfig] = None,
        profile_override: Optional[str] = None,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        # Onay yoneticisi (ana depoya yazmadan once zorunlu onay icin)
        self.approver = ApprovalManager()
        self.auto_apply = str(os.getenv("ACE_ALLOW_AUTO_APPLY", "false")).lower() in (
            "1",
            "true",
            "yes",
        )

        # ACEConfig yükle / bağla
        if config is None:
            self.config = ACEConfig(
                project_root=str(self.project_root),
                profile_override=profile_override,
            )
        else:
            # Dışarıdan gelen config için de profil uygulansın
            self.config = config
            self.config.apply_profile(profile_override)

        self.ace_cfg: Dict[str, Any] = self.config.get_ace_block()
        self.fers_cfg: Dict[str, Any] = self.config.get_fers_block()

        # FERS planner
        self.planner = FullEvolutionaryRefactorPlanner(config=self.fers_cfg)

        # Sandbox dizini
        self.sandbox_dir = self.project_root / self.ace_cfg.get("sandbox_dir", "sandbox_repo")
        self.processed_log = self.project_root / "logs" / "ace" / "processed_files.jsonl"

        # Auto-merge threshold
        self.auto_merge_threshold: int = int(self.ace_cfg.get("auto_merge_threshold", 3))
        self.state_file = self.project_root / ".ace_state.json"

        # Llama / timeout parametreleri
        self.llama_timeout_sec: int = int(self.ace_cfg.get("llama_timeout_sec", 40))

    # ------------------------------------------------------------------
    # PUBLIC ENTRYPOINT
    # ------------------------------------------------------------------
    def run_full_refactor_cycle(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Runs the full ACE/FERS cycle:
        1) Auto-sync settings.yaml (if changed)
        2) Discover target files
        3) Ask FERS for patches
        4) Prepare sandbox and apply patches
        5) Run pytest
        6) Depending on tests result:
           - Apply patches to main repo (if not dry-run)
           - Update auto-merge state
        """
        # 1) settings.yaml değişmişse yeniden yükle/profili uygula
        self.config.auto_sync()
        self.ace_cfg = self.config.get_ace_block()
        self.fers_cfg = self.config.get_fers_block()

        print("1) Kod analizi + refactor planı oluşturuluyor...")

        target_files = self._discover_target_files()
        if not target_files:
            return {
                "status": "NO_FILES",
                "applied_patches": 0,
                "errors": "No candidate files found.",
            }

        # 2) FERS planner'dan patch planı iste
        patches = self._plan_patches(target_files)

        if not patches:
            print("[ACE] Planner patch üretmedi.")
            return {
                "status": "NO_CHANGES",
                "applied_patches": 0,
            }

        print("2) Sandbox repo hazırlanıyor...")
        self._prepare_sandbox()

        print("3) Patch'ler uygulanıyor...")
        applied_in_sandbox = self._apply_patches_in_sandbox(patches)

        if applied_in_sandbox == 0:
            return {
                "status": "NO_CHANGES",
                "applied_patches": 0,
                "errors": "No patches applied in sandbox.",
            }

        print("4) Testler çalıştırılıyor (pytest)...")
        test_ok, test_output = self._run_pytest_in_sandbox()

        if not test_ok:
            # Testler başarısız → main repo'ya patch uygulanmaz
            self._update_merge_state(success=False)
            self._log_processed(target_files, status="tests_failed", details=test_output)
            return {
                "status": "FAIL_TESTS",
                "applied_patches": 0,
                "errors": test_output,
            }

        # Testler başarılı
        if dry_run:
            print("[ACE] Dry-run modunda: patch'ler main repo'ya uygulanmayacak.")
            self._update_merge_state(success=True)
            self._log_processed(target_files, status="dry_run_passed", details="pytest_passed")
            return {
                "status": "DRY_RUN_OK",
                "applied_patches": applied_in_sandbox,
                "errors": "",
            }

        # Testler başarılı → main repo'ya uygula
        # Testler basarili ancak auto-apply kapali: onay bekle
        if not self.auto_apply:
            proposal = {
                "patches": patches,
                "sandbox_result": {"applied": applied_in_sandbox, "tests": "passed"},
            }
            approval_id = self.approver.register_proposal(
                proposal_type="ACE_PATCHES", proposal_content=proposal
            )
            self._update_merge_state(success=True)
            self._log_processed(target_files, status="awaiting_approval", details=approval_id)
            return {
                "status": "AWAITING_APPROVAL",
                "approval_id": approval_id,
                "applied_patches": 0,
                "errors": "",
            }

        applied_main = self._apply_patches_in_main_repo(patches)
        merge_info = self._update_merge_state(success=True)
        self._log_processed(target_files, status="applied", details=merge_info)

        result_status = "APPLIED"
        if merge_info.get("auto_merge_ready"):
            result_status = "APPLIED_AUTO_MERGE_READY"

        return {
            "status": result_status,
            "applied_patches": applied_main,
            "merge_state": merge_info,
        }

    # ------------------------------------------------------------------
    #  DISCOVER PYTHON FILES
    # ------------------------------------------------------------------
    def _discover_target_files(self) -> List[Path]:
        """
        Discover target Python files under project_root for refactoring.
        Simple strategy:
        - Include: src/**/*.py
        - Exclude: tests, sandbox_repo, .venv, build caches
        """
        src_root = self.project_root / "src"
        if not src_root.exists():
            return []

        max_files_raw = self.ace_cfg.get("max_files_per_run", 8)
        max_files = int(max_files_raw) if str(max_files_raw).isdigit() else -1
        files: List[Path] = []
        processed = self._load_processed_set()

        for path in src_root.rglob("*.py"):
            rel = path.relative_to(self.project_root)
            s = str(rel).replace("\\", "/")

            if any(
                bad in s
                for bad in (
                    "/tests/",
                    "/test_",
                    "sandbox_repo/",
                    ".venv/",
                    "__pycache__/",
                )
            ):
                continue

            size = path.stat().st_size if path.exists() else 0
            if size == 0:
                continue

            files.append(path)

        # Öncelik: hiç işlenmemiş dosya önce, ardından küçük boyut
        def _key(p: Path):
            rel = str(p.relative_to(self.project_root)).replace("\\", "/")
            return (rel in processed, p.stat().st_size if p.exists() else 0)

        files.sort(key=_key)

        selected = files if max_files <= 0 else files[:max_files]
        print(
            f"[ACE] Found {len(files)} candidate files, "
            f"selecting first {len(selected)} (max {max_files})."
        )
        return selected

    # ------------------------------------------------------------------
    #  ASK FERS FOR PATCHES
    # ------------------------------------------------------------------
    def _plan_patches(self, files: List[Path]) -> List[Dict[str, Any]]:
        """
        Delegate to FERS planner to produce evolutionary patch plan.
        Expects planner.plan_evolution() to return a list of:
        { "file": "relative/path.py", "new_code": "..." }
        """
        rel_files = [{"rel_path": str(f.relative_to(self.project_root))} for f in files]
        try:
            rel_files = self.planner._assign_evolution_weights(rel_files)
        except Exception:
            rel_files = [rf["rel_path"] for rf in rel_files]

        print(f"[ACE] FERS'e gönderilen dosya sayısı: {len(rel_files)}")
        try:
            patches = self.planner.plan_evolution(rel_files)
        except Exception as exc:  # noqa: BLE001
            print(f"[ACE][ERROR] FERS planner exception: {exc}")
            return []

        if not patches:
            print("[ACE] FERS patch planı boş döndürdü.")
            return []

        print(f"[ACE] FERS toplam {len(patches)} patch üretti.")
        return patches

    # ------------------------------------------------------------------
    #  SANDBOX PREP
    # ------------------------------------------------------------------
    def _prepare_sandbox(self) -> None:
        def _handle_readonly(func, path, excinfo):
            try:
                os.chmod(path, 0o700)
                func(path)
            except Exception:
                pass

        if self.sandbox_dir.exists():
            shutil.rmtree(self.sandbox_dir, ignore_errors=False, onerror=_handle_readonly)
            if self.sandbox_dir.exists():
                # Son bir temizlik denemesi
                shutil.rmtree(self.sandbox_dir, ignore_errors=True)

        def _ignore(path: str, names: List[str]) -> List[str]:
            ignore_list: List[str] = []
            for n in names:
                if n in {".git", ".venv", "sandbox_repo", "__pycache__"}:
                    ignore_list.append(n)
            return ignore_list

        shutil.copytree(
            self.project_root,
            self.sandbox_dir,
            ignore=_ignore,
        )

    # ------------------------------------------------------------------
    #  APPLY PATCHES IN SANDBOX
    # ------------------------------------------------------------------
    def _apply_patches_in_sandbox(self, patches: List[Dict[str, Any]]) -> int:
        count = 0
        for item in patches:
            rel_path = item.get("file")
            new_code = item.get("new_code")

            if not rel_path or new_code is None:
                continue

            target = self.sandbox_dir / rel_path
            if not target.parent.exists():
                target.parent.mkdir(parents=True, exist_ok=True)

            try:
                target.write_text(new_code, encoding="utf-8")
                count += 1
            except Exception as exc:  # noqa: BLE001
                print(f"[ACE][WARN] Sandbox patch apply failed for {rel_path}: {exc}")

        return count

    # ------------------------------------------------------------------
    #  APPLY PATCHES IN MAIN REPO
    # ------------------------------------------------------------------
    def _apply_patches_in_main_repo(self, patches: List[Dict[str, Any]]) -> int:
        count = 0
        for item in patches:
            rel_path = item.get("file")
            new_code = item.get("new_code")

            if not rel_path or new_code is None:
                continue

            target = self.project_root / rel_path
            if not target.parent.exists():
                target.parent.mkdir(parents=True, exist_ok=True)

            try:
                target.write_text(new_code, encoding="utf-8")
                count += 1
            except Exception as exc:  # noqa: BLE001
                print(f"[ACE][WARN] Main repo patch apply failed for {rel_path}: {exc}")

        return count

    # ------------------------------------------------------------------
    #  RUN PYTEST IN SANDBOX
    # ------------------------------------------------------------------
    def _run_pytest_in_sandbox(self) -> (bool, str):
        """
        Runs pytest in the sandbox repository.
        Returns (ok: bool, output: str)
        """
        cmd = ["pytest", "-q"]
        timeout = int(self.ace_cfg.get("max_test_runtime_sec", 180))

        try:
            proc = subprocess.run(
                cmd,
                cwd=self.sandbox_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return False, f"pytest timeout after {timeout} seconds"
        except FileNotFoundError:
            return False, "pytest not found in environment"

        output = proc.stdout or ""
        ok = proc.returncode == 0
        if not ok:
            print("[ACE][TEST] pytest FAILED:")
            print(output)
        else:
            print("[ACE][TEST] pytest PASSED.")

        return ok, output

    # ------------------------------------------------------------------
    #  AUTO-MERGE STATE
    # ------------------------------------------------------------------
    def _load_state(self) -> Dict[str, Any]:
        if not self.state_file.exists():
            return {"merge_success_count": 0}
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {"merge_success_count": 0}

    def _save_state(self, state: Dict[str, Any]) -> None:
        try:
            self.state_file.write_text(
                json.dumps(state, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[ACE][WARN] Cannot save state file: {exc}")

    def _update_merge_state(self, success: bool) -> Dict[str, Any]:
        """
        Tracks how many consecutive successful runs we have.
        If threshold reached, marks as auto-merge ready (informational).
        """
        state = self._load_state()
        threshold = self.auto_merge_threshold

        if success:
            state["merge_success_count"] = int(state.get("merge_success_count", 0)) + 1
        else:
            state["merge_success_count"] = 0

        auto_merge_ready = success and state["merge_success_count"] >= threshold

        state["auto_merge_ready"] = auto_merge_ready
        state["last_update_ts"] = time.time()

        self._save_state(state)

        if auto_merge_ready:
            print(
                f"[ACE] Auto-merge threshold reached "
                f"({state['merge_success_count']} >= {threshold}). "
                "Patches considered stable for automatic merge."
            )

        return state

    # ------------------------------------------------------------------
    #  PROCESSED FILE LOGGING
    # ------------------------------------------------------------------
    def _load_processed_set(self) -> set[str]:
        if not self.processed_log.exists():
            return set()
        paths: set[str] = set()
        try:
            for line in self.processed_log.read_text(encoding="utf-8").splitlines():
                try:
                    rec = json.loads(line)
                    for rel in rec.get("files", []):
                        paths.add(rel)
                except json.JSONDecodeError:
                    continue
        except OSError:
            return set()
        return paths

    def _log_processed(self, files: List[Path], status: str, details: Any) -> None:
        try:
            self.processed_log.parent.mkdir(parents=True, exist_ok=True)
            rels = [str(f.relative_to(self.project_root)).replace("\\", "/") for f in files]
            entry = {
                "ts": time.time(),
                "status": status,
                "files": rels,
                "details": details,
            }
            with self.processed_log.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry) + "\n")
        except Exception:
            # Logging failure should not break pipeline
            pass
