# Zeus Listener & Health Markers

## Overview
The Zeus automation layer offers a voice-driven command surface that lets field teams start core maintenance routines without touching a keyboard. Everything runs offline and communicates state through the local filesystem so the platform keeps working on sites with zero connectivity. This guide explains how the listener works, what it can trigger, and how downstream tooling reads the health markers it writes.

## Voice Command Loop
- `scripts/dev/zeus_listener.py` spawns an offline speech recognizer (Vosk + PyAudio) and waits for the wake phrase `"Zeus"`.
- After the wake phrase, the listener matches the spoken command against the built-in `COMMANDS` map (for example `"run pipelines"`, `"start api"`, `"format code"`, `"show status"`).
- Commands execute via `subprocess.run` or `subprocess.Popen` so they inherit the same virtual environment as the CLI.
- Each interaction appends a timestamped line to `logs/dev/zeus_commands.log`, which doubles as both an audit trail and a quick debugging source if a spoken command misfires.
- The listener never sends audio off-device. Both the acoustic model and command interpreter live in the repo, keeping the workflow 100% offline.

## Health Marker Files
The listener surfacing status information relies on the health marker helper at `scripts/dev/zeus_main.py`. That script manages three mutually exclusive files inside `logs/system/`:

| Status | File | Meaning |
| --- | --- | --- |
| Healthy | `logs/system/health.ok` | Pipelines and supporting services operate nominally. |
| Degraded | `logs/system/health.degraded` | System works but needs attention (for example stale pipelines or background retries). |
| Down | `logs/system/health.down` | Automation should be treated as unavailable. |

Only one marker exists at a time. Writing a new status deletes the other two files. Each marker contains a small JSON payload:

```json
{
	"status": "ok",
	"timestamp": "2025-03-14T13:55:12",
	"message": "optional human-readable context"
}
```

Top-level utilities, dashboards, or shell scripts read these files directly to decide whether to run pipelines, alert operators, or halt risky automation. Because the files live on disk, the state survives process crashes and even full system reboots.

### CLI Usage
Run the helper directly to update or inspect the markers:

```powershell
python scripts/dev/zeus_main.py --status ok --message "Pipelines finished"
python scripts/dev/zeus_main.py --status degraded --message "02_processing stale"
python scripts/dev/zeus_main.py --show
```

- `--status` (choices: `ok`, `degraded`, `down`) writes the matching marker and removes the others.
- `--message` attaches optional context that appears in the JSON payload.
- `--show` prints the current marker JSON after any updates. When invoked with no arguments the script simply prints the existing payload or reports that no marker exists.

The listener uses the same helper to answer prompts like `"Zeus, show status"`, so spoken queries and manual CLI invocations stay in sync.

## Typical Voice Commands
- `"Zeus, run pipelines"` → executes `scripts/dev/run_all_pipelines.py` and flips the health marker to `degraded` until the pipelines rewrite it back to `ok`.
- `"Zeus, start api"` → launches `uvicorn src.ohs.api.main:app --reload --host 127.0.0.1 --port 8000` in the background.
- `"Zeus, format code"` → runs `ruff`, `black`, and `isort` in sequence.
- `"Zeus, show status"` → reads the active marker file and speaks back the JSON payload.

You can extend the listener by adding entries to the `COMMANDS` dictionary. Keep the commands idempotent because the voice loop may repeat them when it cannot confidently classify the audio.

## Operational Tips
- Rotate `logs/dev/zeus_commands.log` periodically if you capture thousands of voice interactions.
- Keep the Vosk model files under `models/` to avoid runtime downloads—this is essential for offline deployments.
- When health markers disagree with reality, re-run `scripts/dev/zeus_main.py --status ...` manually to recover from a crash or stale state.
- Pair the health markers with external watchdogs (for example Task Scheduler or systemd) to alert supervisors if the automation stays `down` for too long.

## Summary
The Zeus listener offers an offline, hands-free control surface for pipeline management. It publishes health through simple JSON files that any tooling can read instantly, making it easy to integrate with monitors or dashboards without spinning up network services.
