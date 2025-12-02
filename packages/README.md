# Offline Package Dropzone

This directory stores wheel artifacts for air-gapped environments.

1. Run `python scripts/dev/offline_package_export.py` on an Internet-connected machine.
2. Copy the generated `.whl` files and `checksums.sha256` into this directory.
3. Transfer the directory to the air-gapped target and install with:
   ```powershell
   python -m pip install --no-index --find-links=packages -r requirements.lock
   ```
4. Verify integrity before installation:
   ```bash
   sha256sum -c packages/checksums.sha256
   ```

Only the checksum manifest and this README are tracked in Git; wheel archives remain local.
