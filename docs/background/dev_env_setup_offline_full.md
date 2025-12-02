# Developer Environment Setup

This document covers both standard online setup and the offline (air-gapped) workflow that relies on pre-downloaded Python wheels.

## 1. Online Developer Setup (Connected Workstations)

1. Clone the repository and change into the project directory.
2. Run the bootstrap helper that provisions a virtual environment, installs dependencies, and registers VS Code tasks:
   ```powershell
   pwsh -File scripts/bootstrap.ps1
   ```
   ```bash
   ./scripts/bootstrap.sh
   ```
3. (Optional) Install pre-commit hooks manually if you skipped the bootstrap script:
   ```bash
   .venv/bin/pre-commit install
   ```
4. Run the default tasks or formatters using the VS Code task palette (`Terminal > Run Task`) or directly from the command line.

## 2. Offline / Air-Gapped Workflow

When the target workstation has no internet access, prepare all Python artifacts on an online helper machine and transfer them over removable media.

### 2.1 Export Packages on a Connected Machine

1. Ensure you have an up-to-date Python toolchain on the connected machine (Python 3.10+ recommended).
2. From the repository root, run the export helper. It downloads every wheel specified in `requirements.lock` (or `requirements.txt` as a fallback) and builds a checksum manifest:
   ```bash
   python scripts/dev/offline_package_export.py
   ```
3. Optional flags:
   - `--clear` removes any existing wheels before downloading.
   - `--requirements path\to\custom.txt` mirrors a specific requirements file.
   - `--extra-index-url https://your.mirror/simple` adds additional package indexes.
4. After the command succeeds, confirm that `packages/` contains:
   - `*.whl` files for each dependency.
   - `checksums.sha256` with SHA-256 hashes.
   - `README.md` describing the transfer procedure.

### 2.2 Transfer Artifacts to the Offline Machine

1. Copy the entire `packages/` directory (including checksums) to removable media.
2. On the air-gapped workstation, place the directory in the project root (`<repo>/packages`).
3. Optionally verify integrity before installation:
   ```bash
   cd packages
   # Linux / macOS
   sha256sum -c checksums.sha256
   # Windows (PowerShell 7+)
   Get-FileHash *.whl -Algorithm SHA256 | Format-Table
   ```

### 2.3 Install Dependencies Offline

1. Create or reuse the virtual environment (bootstrap scripts support `--skip-download` by virtue of using local wheels if present).
2. Install packages using the mirrored wheels:
   ```bash
   python -m pip install --no-index --find-links packages -r requirements.lock
   ```
   If `requirements.lock` is unavailable, use `requirements.txt`.
3. Run `pre-commit install` if hooks are desired.
4. Execute `pytest` or the VS Code tasks to validate the environment.

### 2.4 Updating Packages

- Re-run `offline_package_export.py` whenever dependencies change.
- Replace the `packages/` contents on the offline host and re-install using the same `pip install --no-index` command.
- Always re-verify checksums after copying to ensure integrity.

## 3. Troubleshooting

- **Missing Wheels:** Re-export after clearing the directory with `--clear` to avoid stale artifacts.
- **Checksum Mismatch:** Recopy the affected wheels or regenerate the bundle.
- **Pip Cannot Find Package:** Confirm the wheel exists in `packages/` and that you are pointing pip to the directory with `--find-links`.
- **Python Version Differences:** Export wheels on a machine that matches the offline interpreter (same major/minor version and platform).

Following these workflows ensures both online and air-gapped developers can set up the project reliably with the same vetted dependency set.
