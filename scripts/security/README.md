# Static skill source security scan

`scripts/security/scan_skills.py` performs a deterministic, offline scan of text sources under `skills/`, `runtime/`, `scripts/`, `workflows/`, `templates/` and `.github/workflows/` (excluding test/eval fixtures). It never imports or executes inspected code. It currently flags narrow patterns for remote shell pipes (including line continuations), invisible Unicode controls, decoded content passed directly to dynamic execution, credential-like literals, shell execution, credential-read/outbound-request combinations, obfuscation combined with execution, package installation hooks, and unpinned `requirements*.txt` entries.

High-severity findings fail the CI gate unless an exact `(rule_id, path, fingerprint)` waiver is present. Waivers require a reason and ISO date expiry in `waivers.yaml`; expired or malformed waivers block the scan. Medium findings remain visible in the receipt but do not fail the gate. CI keeps the JSON receipt as an artifact.

This is a triage control, not a proof of safety. It can miss obfuscated, generated, indirect, or context-dependent behavior and can flag benign code for review. Passing this scan does not establish runtime safety, permission approval, or security clearance. Rules should be expanded from reviewed false negatives and tested with mutation fixtures. Never add a waiver merely to make a build green.
