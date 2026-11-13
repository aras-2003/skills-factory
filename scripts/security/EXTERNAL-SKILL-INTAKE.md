# External skill intake

`external_skill_intake.py` inventories and quarantines candidate skills. It does not install or promote them. Treat the receipt as evidence for human review, not as a safety certificate.

## Local directory

```sh
python scripts/security/external_skill_intake.py \
  --source /path/to/candidate \
  --quarantine .tmp/external-skill-quarantine \
  --receipt .tmp/intake-receipt.json \
  --manifest .tmp/intake-manifest.json
```

## Local ZIP bundle

```sh
python scripts/security/external_skill_intake.py \
  --source /path/to/candidate.zip \
  --subdir skills/example \
  --quarantine .tmp/external-skill-quarantine \
  --receipt .tmp/intake-receipt.json \
  --manifest .tmp/intake-manifest.json
```

The `--subdir` option is optional. A source must contain at least one `SKILL.md`. ZIP members are read and validated before a read-only quarantine copy is made. Files use canonical relative paths, bounded sizes, and individual SHA-256 hashes. The command refuses links, unsafe paths, conflicting aliases, unsupported compression, and archives outside fixed limits.

## Pinned GitHub repository

```sh
python scripts/security/external_skill_intake.py \
  --github-repo owner/repository \
  --commit 0123456789abcdef0123456789abcdef01234567 \
  --subdir path/to/skill \
  --quarantine .tmp/external-skill-quarantine \
  --receipt .tmp/intake-receipt.json \
  --manifest .tmp/intake-manifest.json
```

Use a full 40-character commit SHA. Branch names, tags, shortened hashes, arbitrary hosts, embedded credentials, and redirects outside the GitHub API/codeload allowlist are refused. Requests and downloaded archives have bounded sizes and timeouts. CI uses a mocked transport; tests never download arbitrary external content.

## Review and authorization

The receipt and manifest are deterministic for identical source bytes. `inventory_sha256` covers sorted canonical paths, sizes, and file hashes. The initial license decision is `UNKNOWN` or `REVIEW_REQUIRED`; finding a LICENSE or author string never approves reuse. Static scan results are triage signals. Discovery does not execute candidate scripts, imports, prompt instructions, dependency hooks, or network operations. All candidates remain `NOT_AUTHORIZED`.

An explicit reviewer record must reference the receipt digest, inventory digest, exact repository and commit, reviewer identity, timezone-bearing review time, rationale, license decision, security decision, and evidence references. The validator accepts a review only when both decisions are explicitly `APPROVED` and every identity matches. Any changed commit, path, file size, or file hash changes the receipt/inventory identity and invalidates the review. A valid review does not import, install, or promote content.

Example reviewer record shape (create only after reviewing the exact receipt):

```json
{
  "schema_version": 1,
  "receipt_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
  "inventory_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
  "source": {"repository": "owner/repository", "commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
  "reviewer": "reviewer identity",
  "reviewed_at": "2026-11-13T12:00:00Z",
  "rationale": "What was checked and why the decision is justified.",
  "license_decision": "REVIEW_REQUIRED",
  "security_decision": "REVIEW_REQUIRED",
  "license_evidence_reference": "evidence location",
  "security_evidence_reference": "evidence location"
}
```

The receipt schema is the file root; the manifest and review schemas are available at `$defs/manifest` and `$defs/review` in `scripts/validate/schemas/external-skill-intake.schema.json`. Replace synthetic digest examples with values from the exact receipt before validating a real review. A successful intake still requires security, license, provenance, compatibility, and human import reviews under the applicable workflow. It does not establish that content is safe or licensed for redistribution.
