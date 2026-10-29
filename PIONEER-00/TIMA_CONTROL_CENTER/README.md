# TIMA Control Center v0.1 (prototype)

Local Windows inventory UI: http://127.0.0.1:8093

## Launch
1. Install Python 3 if not already available.
2. Download this directory from GitHub (Code > Download ZIP, or git clone).
3. Run START_TIMA.cmd.
4. Open http://127.0.0.1:8093 and click "1 · Запустить обследование".

The server is bound to 127.0.0.1 and runs a fixed allowlist of passive inventory commands. No AIDA64 process is launched yet. No active LAN scan, VM creation or Docker changes.

## Reports and GitHub
Raw reports are written to reports/inventory_<job>.json and are intentionally gitignored. They may include hostname, software inventory, network details, IP addresses and other sensitive data. **Never commit raw reports to a public repository.** Review and redact locally, then commit a safe summary to reports-public/ manually. No Git credentials or tokens are requested by the web app.

## Status
Prototype only. Not yet tested on the user's Windows host. No auto-publish. AIDA64 Extreme is detected but its command-line reporting is not yet validated.
