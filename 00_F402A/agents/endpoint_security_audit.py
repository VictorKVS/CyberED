#!/usr/bin/env python3
"""CyberED FATHER: read-only endpoint posture collector. Python 3.10+; stdlib only.
No privilege elevation, remediation, networking, password hashes, or file contents.
Use only on systems you own or are authorized to assess.
"""
import argparse, datetime, json, os, platform, re, shutil, subprocess, sys
from pathlib import Path

COMMANDS = {
    "Windows": {
        "identity": ["whoami", "/groups"],
        "accounts_policy": ["net", "accounts"],
        "audit_policy": ["auditpol", "/get", "/category:*"],
        "firewall": ["netsh", "advfirewall", "show", "allprofiles"],
        "defender": ["powershell", "-NoProfile", "-NonInteractive", "-Command",
                     "Get-MpComputerStatus | Select-Object AMServiceEnabled,AntivirusEnabled,RealTimeProtectionEnabled,AntispywareEnabled | ConvertTo-Json -Compress"],
        "bitlocker": ["powershell", "-NoProfile", "-NonInteractive", "-Command",
                      "Get-BitLockerVolume | Select-Object MountPoint,VolumeStatus,ProtectionStatus | ConvertTo-Json -Compress"],
    },
    "Linux": {
        "identity": ["id"],
        "kernel": ["uname", "-a"],
        "os_release": ["cat", "/etc/os-release"],
        "audit_service": ["systemctl", "is-active", "auditd"],
        "firewall_nft": ["nft", "list", "ruleset"],
        "firewall_ufw": ["ufw", "status"],
        "listening_ports": ["ss", "-lnt"],
        "login_policy": ["grep", "-E", "^(PASS_MAX_DAYS|PASS_MIN_DAYS|PASS_WARN_AGE|UMASK)", "/etc/login.defs"],
        "package_updates": ["apt-cache", "policy"],
    },
}
# Remove command output that may include local identifiers; store metadata instead by default.
SENSITIVE = {"identity", "os_release", "kernel", "listening_ports", "firewall_nft", "login_policy"}
def collect(command, timeout=12, include_details=False):
    if shutil.which(command[0]) is None:
        return {"status": "unavailable"}
    try:
        proc = subprocess.run(command, capture_output=True, text=True, errors="replace",
                              timeout=timeout, shell=False, stdin=subprocess.DEVNULL)
        result = {"status": "ok" if proc.returncode == 0 else "error",
                  "returncode": proc.returncode}
        if include_details:
            output = proc.stdout[:12000]
            # Still treat details as sensitive; do not transmit automatically.
            result["stdout"] = output
            result["stderr"] = proc.stderr[:2000]
        return result
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    except (OSError, ValueError) as exc:
        return {"status": "error", "error_type": type(exc).__name__}

def main():
    p = argparse.ArgumentParser(description="CyberED local read-only security audit")
    p.add_argument("--out", default="cybered-audit.json")
    p.add_argument("--include-details", action="store_true",
                   help="Include raw command output: may contain sensitive system data")
    args = p.parse_args()
    os_family = "Windows" if os.name == "nt" else "Linux" if sys.platform.startswith("linux") else None
    if os_family is None:
        p.error("Only Windows and Linux are supported")
    results = {}
    for name, command in COMMANDS[os_family].items():
        # Without explicit opt-in do not collect potentially sensitive details.
        if name in SENSITIVE and not args.include_details:
            results[name] = {"status": "skipped_sensitive", "hint": "Use --include-details on an approved lab machine"}
        else:
            results[name] = collect(command, include_details=args.include_details)
    report = {
        "schema": "cybered.endpoint.audit.v0.1",
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "os_family": os_family, "os_version": platform.release(),
        "mode": "read_only", "raw_details_included": args.include_details,
        "checks": results,
        "limitations": ["Command availability and permissions vary",
                        "No certification or regulatory compliance claim",
                        "No actual permission changes performed"]
    }
    out = Path(args.out).expanduser().resolve()
    if out.exists():
        raise SystemExit("Refusing to overwrite existing report: " + str(out))
    with out.open("x", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    if os.name != "nt":
        os.chmod(out, 0o600)
    print("Saved:", out)
    print("Completed:", sum(x["status"] == "ok" for x in results.values()), "/", len(results))
if __name__ == "__main__":
    main()
