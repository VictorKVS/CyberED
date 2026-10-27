# PIONEER-04 — GATE-1 contract (prototype)

PIONEER prepares `handoff-gate1.json` in READY_FOR_REVIEW. No deployment is allowed by this status.

The handoff binds the project and revision to SHA-256 fingerprints of architecture, security model, and source catalog. TIMA must reject missing approvals, mismatched fingerprints and unapproved revisions.

`check_gate1` validates approval **metadata only**. It does not authenticate approvers, verify digital signatures, implement authorization, or grant permission to deploy. Production approval requires a trusted identity system, signed approval and independent enforcement in TIMA. Test fixtures that say APPROVED are not real authorization.

Run from PIONEER-00:
```powershell
python gate1.py
python -m unittest discover -s tests -v
```

Do not commit real approvals, credentials or sensitive infrastructure details.
