"""
Zeus File Sanitizer - Automated file organization with deduplication
Responsibilities:
- NO stamp operations (doesn't track pipeline timing)
- WRITE logs (file moves, deduplication events)
- OWN cache (SHA-256 hash deduplication)
- Supports both files and folders dropped into the dropzone
- Validates file types and sizes before processing
- Quarantines suspicious files
"""

import hashlib
import json
import mimetypes
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Add project root to path
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))


class FileSanitizer(FileSystemEventHandler):
    """Zero-config file sanitizer with deduplication and validation."""

    # Security limits
    MAX_FILE_SIZE_MB = 100
    MAX_FOLDER_SIZE_MB = 500

    # Allowed MIME types (whitelist)
    ALLOWED_MIME_PREFIXES = (
        "application/pdf",
        "application/vnd.openxmlformats-officedocument",
        "application/msword",
        "image/",
        "text/",
        "application/json",
    )

    def __init__(self, dropzone: Path, sources_root: Path):
        self.dropzone = dropzone
        self.sources_root = sources_root
        self.dropzone.mkdir(parents=True, exist_ok=True)

        # Log file (WRITE responsibility)
        self.log_file = Path("logs") / "dev" / "sanitizer.log"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Quarantine directory
        self.quarantine_dir = sources_root / "_quarantine"
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)

        # Cache file (OWN responsibility)
        self.cache_file = sources_root / ".sanitizer_history.json"
        self._cache: Dict[str, dict] = self._load_cache()

        # Target directory mapping (optimized for common types)
        self.target_map = {
            "application/pdf": "pdfs",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "documents",
            "application/msword": "documents",
            "image/": "images",
            "text/plain": "text",
            "application/json": "json",
            "text/csv": "csv",
        }

        # Processing statistics
        self.stats = {
            "files_processed": 0,
            "folders_processed": 0,
            "duplicates_skipped": 0,
            "quarantined": 0,
            "errors": 0,
        }

    def _log(self, event_type: str, message: str, details: Optional[str] = None):
        """Append event to log (WRITE responsibility)."""
        timestamp = datetime.now().isoformat()
        detail_str = f" | {details}" if details else ""
        line = f"[{timestamp}] {event_type:8s}: {message}{detail_str}\n"

        try:
            with self.log_file.open("a", encoding="utf-8") as f:
                f.write(line)
        except Exception as e:
            print(f"[LOG ERROR] Failed to write log: {e}")
            print(f"[LOG ENTRY] {line.strip()}")

    def _load_cache(self) -> dict:
        """Load deduplication cache with corruption recovery."""
        if not self.cache_file.exists():
            self._log("INFO", "Cache file not found, starting with empty cache")
            return {}

        try:
            content = self.cache_file.read_text(encoding="utf-8")
            cache = json.loads(content)
            self._log("INFO", f"Loaded cache with {len(cache)} entries")
            return cache
        except json.JSONDecodeError as e:
            self._log("WARNING", f"Corrupt cache file: {e}, backing up and recreating")
            # Backup corrupt file
            backup_dir = self.cache_file.parent / "_corrupt_backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = (
                backup_dir / f"{self.cache_file.stem}_{int(time.time())}{self.cache_file.suffix}"
            )
            try:
                self.cache_file.rename(backup_path)
                self._log("INFO", f"Backed up corrupt cache to {backup_path}")
            except Exception as backup_err:
                self._log("ERROR", f"Failed to backup corrupt cache: {backup_err}")
            return {}
        except Exception as e:
            self._log("ERROR", f"Failed to load cache: {e}")
            return {}

    def _save_cache(self) -> bool:
        """Save cache atomically (OWN responsibility - WRITE)."""
        try:
            # Atomic write: temp file + rename
            temp_file = self.cache_file.with_suffix(".tmp")
            temp_file.write_text(
                json.dumps(self._cache, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            temp_file.replace(self.cache_file)
            return True
        except Exception as e:
            self._log("ERROR", f"Failed to save cache: {e}")
            # Clean up temp file
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            return False

    def _compute_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash for deduplication (chunked reading)."""
        hasher = hashlib.sha256()
        try:
            with file_path.open("rb") as f:
                while chunk := f.read(1024 * 1024):  # 1MB chunks
                    hasher.update(chunk)
            return f"sha256:{hasher.hexdigest()}"
        except Exception as e:
            self._log("ERROR", f"Hash computation failed for {file_path.name}: {e}")
            raise

    def _sanitize_filename(self, filename: str) -> str:
        """Clean filename (lowercase, underscores, safe chars only)."""
        # Convert to lowercase
        clean = filename.lower()
        # Replace spaces with underscores
        clean = clean.replace(" ", "_")
        # Remove unsafe characters (keep alphanumeric, underscore, dash, dot)
        clean = "".join(c for c in clean if c.isalnum() or c in "._-")
        # Collapse consecutive separators
        while "__" in clean or "--" in clean:
            clean = clean.replace("__", "_").replace("--", "-")
        # Remove leading/trailing separators
        clean = clean.strip("_-")
        # Limit length (Windows MAX_PATH considerations)
        if len(clean) > 255:
            name, ext = clean.rsplit(".", 1) if "." in clean else (clean, "")
            clean = name[:250] + ("." + ext if ext else "")
        return clean

    def _validate_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate file before processing.
        Returns (is_valid, reason_if_invalid)
        """
        # Check file size
        try:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > self.MAX_FILE_SIZE_MB:
                return (
                    False,
                    f"File exceeds max size: {size_mb:.1f}MB > {self.MAX_FILE_SIZE_MB}MB",
                )
        except Exception as e:
            return (False, f"Cannot read file size: {e}")

        # Check MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            return (False, "Unknown MIME type")

        # Check against whitelist
        if not any(
            mime_type.startswith(prefix.rstrip("/")) for prefix in self.ALLOWED_MIME_PREFIXES
        ):
            return (False, f"Unauthorized MIME type: {mime_type}")

        return (True, None)

    def _validate_folder(self, folder_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate folder before processing.
        Returns (is_valid, reason_if_invalid)
        """
        try:
            # Calculate total folder size
            total_size = sum(f.stat().st_size for f in folder_path.rglob("*") if f.is_file())
            size_mb = total_size / (1024 * 1024)

            if size_mb > self.MAX_FOLDER_SIZE_MB:
                return (
                    False,
                    f"Folder exceeds max size: {size_mb:.1f}MB > {self.MAX_FOLDER_SIZE_MB}MB",
                )

            return (True, None)
        except Exception as e:
            return (False, f"Cannot validate folder: {e}")

    def _quarantine_item(self, item_path: Path, reason: str):
        """Move suspicious item to quarantine."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            quarantine_name = f"{item_path.stem}_{timestamp}{item_path.suffix}"
            quarantine_path = self.quarantine_dir / quarantine_name

            shutil.move(str(item_path), str(quarantine_path))

            # Write quarantine metadata
            meta_file = quarantine_path.with_suffix(".quarantine.json")
            meta_file.write_text(
                json.dumps(
                    {
                        "original_path": str(item_path),
                        "reason": reason,
                        "timestamp": datetime.now().isoformat(),
                        "type": "folder" if item_path.is_dir() else "file",
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            self._log("QUARANTINE", f"{item_path.name} → {quarantine_path.name}", details=reason)
            self.stats["quarantined"] += 1
        except Exception as e:
            self._log("ERROR", f"Failed to quarantine {item_path.name}: {e}")

    def _determine_target(self, file_path: Path) -> Path:
        """Determine target directory based on MIME type."""
        mime_type, _ = mimetypes.guess_type(str(file_path))

        if not mime_type:
            return self.sources_root / "unknown"

        # Check exact match
        if mime_type in self.target_map:
            return self.sources_root / self.target_map[mime_type]

        # Check prefix match (e.g., "image/")
        for prefix, target_dir in self.target_map.items():
            if mime_type.startswith(prefix.rstrip("/")):
                return self.sources_root / target_dir

        return self.sources_root / "unknown"

    def process_file(self, file_path: Path):
        """Process individual file with validation and deduplication."""
        if not file_path.exists():
            self._log("WARNING", f"File disappeared before processing: {file_path.name}")
            return

        try:
            # Validate file
            is_valid, reason = self._validate_file(file_path)
            if not is_valid:
                self._quarantine_item(file_path, reason)
                return

            # Compute hash for deduplication
            file_hash = self._compute_hash(file_path)

            # Check cache (OWN responsibility - READ)
            if file_hash in self._cache:
                existing = self._cache[file_hash]
                self._log(
                    "DUPLICATE",
                    f"{file_path.name} (hash match)",
                    details=f"Original: {existing.get('original_path', 'unknown')}",
                )
                file_path.unlink()  # Delete duplicate
                self.stats["duplicates_skipped"] += 1
                return

            # Sanitize filename
            clean_name = self._sanitize_filename(file_path.name)
            if not clean_name:
                self._quarantine_item(file_path, "Filename sanitization resulted in empty string")
                return

            # Determine target directory
            target_dir = self._determine_target(file_path)
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / clean_name

            # Handle filename collision
            counter = 1
            while target_path.exists():
                name, ext = clean_name.rsplit(".", 1) if "." in clean_name else (clean_name, "")
                if ext:
                    target_path = target_dir / f"{name}_{counter}.{ext}"
                else:
                    target_path = target_dir / f"{name}_{counter}"
                counter += 1

            # Move file
            shutil.move(str(file_path), str(target_path))

            # Update cache (OWN responsibility - WRITE)
            self._cache[file_hash] = {
                "original_path": str(file_path.resolve()),
                "target_path": str(target_path.resolve()),
                "timestamp": datetime.now().isoformat(),
                "size_bytes": target_path.stat().st_size,
            }
            self._save_cache()

            # Log success
            self._log("MOVED", f"{file_path.name} → {target_path.relative_to(self.sources_root)}")
            self.stats["files_processed"] += 1

        except Exception as e:
            self._log("ERROR", f"Failed to process file {file_path.name}: {e}")
            self.stats["errors"] += 1

    def process_folder(self, folder_path: Path):
        """Process folder by moving atomically to appropriate location."""
        if not folder_path.exists():
            self._log("WARNING", f"Folder disappeared before processing: {folder_path.name}")
            return

        try:
            # Validate folder
            is_valid, reason = self._validate_folder(folder_path)
            if not is_valid:
                self._quarantine_item(folder_path, reason)
                return

            # Sanitize folder name
            clean_name = self._sanitize_filename(folder_path.name)
            if not clean_name:
                self._quarantine_item(
                    folder_path, "Folder name sanitization resulted in empty string"
                )
                return

            # Target: folders go to a dedicated directory
            target_dir = self.sources_root / "folders"
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / clean_name

            # Handle name collision
            counter = 1
            while target_path.exists():
                target_path = target_dir / f"{clean_name}_{counter}"
                counter += 1

            # Move folder atomically
            shutil.move(str(folder_path), str(target_path))

            # Log success
            self._log(
                "MOVED",
                f"[FOLDER] {folder_path.name} → {target_path.relative_to(self.sources_root)}",
            )
            self.stats["folders_processed"] += 1

        except Exception as e:
            self._log("ERROR", f"Failed to process folder {folder_path.name}: {e}")
            self.stats["errors"] += 1

    def scan_and_process(self):
        """Scan dropzone and process all items (files and folders)."""
        items = list(self.dropzone.glob("*"))

        if not items:
            print("No items in dropzone")
            return

        print(f"\nFound {len(items)} items in dropzone")
        for item in items:
            if item.is_file():
                print(f"- File   : {item.name}")
                self.process_file(item)
            elif item.is_dir():
                print(f"- Folder : {item.name}")
                self.process_folder(item)

        # Print statistics
        print("\nProcessing Statistics:")
        print(f"  Files processed    : {self.stats['files_processed']}")
        print(f"  Folders processed  : {self.stats['folders_processed']}")
        print(f"  Duplicates skipped : {self.stats['duplicates_skipped']}")
        print(f"  Quarantined        : {self.stats['quarantined']}")
        print(f"  Errors             : {self.stats['errors']}")

    def on_created(self, event):
        """Handle new file/folder in dropzone."""
        path = Path(event.src_path)

        # Ignore temporary/system files
        if path.name.startswith(".") or path.name.startswith("~"):
            return

        if path.is_file():
            self.process_file(path)
        elif path.is_dir():
            self.process_folder(path)

    def watch(self, interval: int = 5):
        """
        Watch dropzone for new items with configurable polling interval.

        Uses a blocking loop; intended to be run under a supervisor (Task Scheduler,
        service wrapper, or manually from terminal). Ensures observer is always
        stopped and joined, and statistics are printed on exit.
        """
        observer = Observer()
        observer.schedule(self, str(self.dropzone), recursive=False)
        observer.start()

        print(f"\nFile Sanitizer monitoring: {self.dropzone}")
        print(f"Polling interval: {interval} seconds")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                time.sleep(interval)
        except KeyboardInterrupt:
            self._log("INFO", "Sanitizer stopped by user")
            print("\nFile Sanitizer stopped.")
        except Exception as e:
            # Log unexpected errors and re-raise so an external supervisor
            # (e.g., Task Scheduler) can detect failure and restart.
            self._log("ERROR", f"Unexpected error in watch loop: {e}")
            print(f"\nFile Sanitizer crashed: {e}")
            raise
        finally:
            observer.stop()
            observer.join()

            # Print final statistics
            print("\nFinal Statistics:")
            print(f"  Files processed    : {self.stats['files_processed']}")
            print(f"  Folders processed  : {self.stats['folders_processed']}")
            print(f"  Duplicates skipped : {self.stats['duplicates_skipped']}")
            print(f"  Quarantined        : {self.stats['quarantined']}")
            print(f"  Errors             : {self.stats['errors']}")


def main():
    """Main entry point."""
    import os

    raw_root = os.getenv("RAW_ROOT", r"H:/DataLake/ai4hsse-raw")
    dropzone = Path(raw_root) / "00_sources" / "_dropzone"
    sources_root = Path(raw_root) / "00_sources"

    # Fallback to workspace DataLake if H: not available
    if not Path(raw_root).exists():
        raw_root = project_root / "DataLake" / "ai4hsse-raw"
        dropzone = raw_root / "00_sources" / "_dropzone"
        sources_root = raw_root / "00_sources"

    sanitizer = FileSanitizer(dropzone, sources_root)

    # Process existing items first
    sanitizer.scan_and_process()

    # Start watching for new items
    sanitizer.watch(interval=5)


if __name__ == "__main__":
    main()
