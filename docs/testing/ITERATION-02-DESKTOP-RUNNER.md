# ENG-08 / Iteration 02 — Desktop TEST adapter controller

Status: source implementation with executable synthetic fixture; real Desktop/Work model integration NOT_RUN.

Use the **external** Iteration 2 handoff ZIP/dir (not the Lab executor pack).
The Desktop case remains I02-240-local-runner with channel=desktop.
`scripts/eval/iteration02_desktop_runner.py` uses a separate Desktop-specific
control path and refuses Site, browser, Production and Lab cases.

## Operator handoff prerequisites

1. Run only on an OS-enforced disposable machine or container, with network,
   host secrets, user profiles, Drive, production accounts and stores inaccessible.
   The Python controller deliberately CANNOT establish the sandbox.
2. Obtain separate scope-specific approval for this synthetic TEST execution.
   The controller requires the approval flag plus a nonempty approval reference.
3. Independently observe an installed Desktop/Work runtime identity record:
   channel=desktop, attestation_status=verified, source_revision (40 hex),
   release_id, payload_content_sha256 (64 hex), tool_schema_digest (SHA-256),
   observed_at (timezone-aware and within 48h), observation_source (raw trace id).
   These JSON values are unauthenticated by this CLI: an independent assessor
   must inspect the actual Desktop/Work tool receipts.
4. Have an independently reviewed executable TEST adapter at an absolute path,
   with pinned full SHA-256, reading one JSON request from stdin and emitting
   one JSON response on stdout. It may use a sanctioned Desktop test client,
   but that provider binding is NOT supplied by this repository.

## Example source-only integration invocation (never against production)

    python scripts/eval/iteration02_desktop_runner.py \
      --external-pack .tmp/iteration02-external-handoff \
      --archive-root .tmp/iteration02-desktop-evidence \
      --installed-desktop-identity observed-desktop-identity.json \
      --case-id I02-240-local-runner --attempt 1 \
      --adapter /absolute/path/to/approved-test-adapter \
      --adapter-sha256 <64-hex> \
      --approval-reference <scoped-synthetic-TEST-authorization> \
      --approve-isolated-desktop-test

## Output

An atomic per-case/attempt directory contains record.json and optionally
adapter-response.json. Source, release, payload, adapter, installed-identity,
input and evaluator-rubric digests are pinned. The rubric text is never sent
to the adapter. Raw adapter bytes are retained for later independent review.
Repeated attempts do not re-execute. Missing/modified evidence, symlinked
archives, invalid provider identity or a crashed reservation fail closed.
Executor child receives a minimal environment and a bounded timeout.

The success label ADAPTER_REPORTED_EXECUTED_REVIEW_REQUIRED means an approved
adapter subprocess ran and **claimed** execution with nonempty steps.
It is NOT proof that a Desktop/Work model executed, that its behavior was
correct or that the installed identity is authentic. The receipt always states
provider_execution_authenticated=false, model_behavior_verdict=NOT_EVALUATED,
release_approved=false.

## Remaining before actual Desktop runtime PASS

- Provide an approved, independently instrumented Desktop/Work TEST adapter
  and identity trace; validate least-privilege network/OS isolation in situ.
- Capture raw per-tool model input, output and child execution steps from
  the approved provider; authenticate session id and full source identity.
- Pass raw output to an independent evaluator who holds the pinned rubric;
  translate verified observations into the canonical receipt/intake protocol.
- Validate crash/recovery and concurrent invocation using OS-isolated workers.
- Do not reuse a local fixture-process test as a model behavioral PASS.
