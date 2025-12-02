# Secrets Management Policy – AI4OHS-HYBRID

## 1. Purpose
This document defines the mandatory rules and technical controls for handling sensitive credentials within the AI4OHS-HYBRID environment, covering API keys, encryption keys, tokens, environment variables, and authentication secrets.
The policy applies to local, offline, online, development, staging, and production environments.

## 2. Scope
This policy covers all secrets related to:
- OpenAI, Azure OpenAI, Ollama (local models)
- GitHub tokens & repository deploy tokens
- FastAPI internal service keys
- FAISS index protection keys (optional)
- Mevzuat scraper keys (if proxy required)
- File normalization workers (Zeus Layer)
- Windows Task Scheduler credentials
- Python environment variables (.env, .env.local)

## 3. Core Principles

### 3.1 Never Store Secrets in Git
The following MUST NOT be committed to Git under any circumstances:

- `.env`
- `.env.local`
- `*.key`
- `*.pem`
- `secrets.json`
- `logs/`
- `DataLake/`
- `DataWarehouse/`
- `model_weights/`

The repository `.gitignore` must enforce this. Any bypass is a violation of this policy.

### 3.2 Secrets Stay Local
Even in cloud-assisted mode, credential storage remains local-first:
- No cloud sync (OneDrive, iCloud, Google Drive)
- No MS Teams/Slack/Chat file sharing for raw secrets
- No email attachments with plaintext secrets

### 3.3 Least Privilege
Use the minimum permission level required.

Examples:
- GitHub → Use fine-grained tokens, not classic full-access PAT.
- OpenAI → Use project-scoped API keys.
- PowerShell tasks → Use local user context only.

### 3.4 Rotation
Every secret must be rotated:
- OpenAI / Azure: every 90 days
- GitHub tokens: every 60 days
- Local environment key (Zeus): every 180 days
- Dev environment token used for CI tasks: every 30 days

Rotation events are logged under:

`H:\DataWarehouse\ai4ohs-security\rotation-log.json`

## 4. Folder Structure for Secrets

Recommended structure:

```text
C:\vscode-projects\ai4ohs-hybrid\
│
├── .env                        # development keys only
├── .env.local                  # local machine secrets
├── secrets/
│   ├── encryption/
│   │   ├── aes_master.key
│   │   └── tokens.iv
│   ├── tokens/
│   │   ├── github_token.txt
│   │   ├── openai_key.txt
│   │   └── azure_openai_key.txt
│   ├── service/
│   │   ├── rag_api_key.txt
│   │   └── zeus_internal.key
│   └── metadata/
│       ├── rotation-history.json
│       └── fingerprint.json
```

The `secrets/` folder is never tracked by Git and must be covered by `.gitignore`.

## 5. Environment Variables

### 5.1 Required Variables

```text
OPENAI_API_KEY=
AZURE_OPENAI_KEY=
AZURE_OPENAI_ENDPOINT=
OLLAMA_API_KEY=
GITHUB_TOKEN=
RAG_INTERNAL_API_KEY=
FAISS_ENCRYPTION_KEY=
ZEUS_INTERNAL_KEY=
```

### 5.2 Optional Variables

```text
PROXY_URL=
LOG_LEVEL=
GPU_ACCELERATION=true/false
OFFLINE_MODE=true/false
```

These values are defined in `.env` or `.env.local` and injected via the Python settings loader. Raw keys must not be in source code.

## 6. Secure Storage Requirements

### 6.1 Windows DPAPI Protection
Local secrets are secured using a combination of:
- `cryptography.fernet` for symmetric encryption
- Windows DPAPI to protect the encryption key at OS level

Helper scripts:

```powershell
python scripts/security/encrypt.py "plain-secret"
python scripts/security/decrypt.py "cipher-text"
```

Raw secrets must never be written to logs or stored in plaintext files.

### 6.2 Access Control
Folder ACL rules:

- Owner: LocalUser (developer account)
- Read: LocalUser
- Write: LocalUser
- No access: Administrators, SYSTEM, NETWORK SERVICE, LOCAL SERVICE

PowerShell enforcement example:

```powershell
icacls secrets /inheritance:r /grant:r "$env:USERNAME:(OI)(CI)F"
```

## 7. Secrets in Automation (Zeus Layer)

### 7.1 Zeus Worker Requirements
- The worker uses tokens strictly in read-only mode.
- Secrets are loaded into memory only when needed and never logged.
- Voice/CLI outputs mask secrets:

`OPENAI_API_KEY = sk-***************************`

### 7.2 Scheduled Tasks
Windows Task Scheduler must:
- Run tasks under a local user account
- Avoid “Run whether user is logged on or not” patterns that require stored credentials
- Use environment variables or DPAPI for any required tokens

## 8. Transport Safety

### Forbidden Channels
- WhatsApp, Telegram, Signal, or similar chat apps
- Email (as plaintext or attachments)
- Screenshots containing secrets
- Public cloud notes

### Allowed Channels
- Encrypted USB drive (AES-256)
- Local encrypted vault (KeePassXC, BitLocker-protected drive)
- Windows DPAPI-secured storage

## 9. Compromise Handling Procedure

When a secret is suspected to be exposed:

1. Immediate Rotation
   - Regenerate the key/token (OpenAI, Azure, GitHub, internal).
2. Revoke Old Credentials
   - Remove from provider console and local `.env`.
3. Invalidate Active Sessions
   - For GitHub, revoke token sessions.
4. Scan Commit History
   - `git log -p | findstr /i "key token secret"`
5. Regenerate FAISS Encryption Key (if used)
   - If index-level secret leaked, rebuild the index with a new key.
6. Log the Incident
   - Append an entry to: `H:\DataWarehouse\ai4ohs-security\incident-log.json`.

## 10. Example .env Template

```text
# AI4OHS-HYBRID Base Configuration
OFFLINE_MODE=true
GPU_ACCELERATION=true

# API Keys (store locally, never commit!)
OPENAI_API_KEY=
AZURE_OPENAI_KEY=
AZURE_OPENAI_ENDPOINT=
OLLAMA_API_KEY=
GITHUB_TOKEN=

# Internal Services
RAG_INTERNAL_API_KEY=
ZEUS_INTERNAL_KEY=
FAISS_ENCRYPTION_KEY=
```

## 11. Enforcement
This policy is mandatory for all contributors and environments of AI4OHS-HYBRID.  
Violations result in:
- Immediate key/token revocation
- Local environment security review
- Mandatory rotation of related secrets

## 12. Change History
- v1.0 – Initial full version
- v1.1 – Added ACL rules and DPAPI requirement
- v1.2 – Integrated Zeus automation and rotation logging conventions
