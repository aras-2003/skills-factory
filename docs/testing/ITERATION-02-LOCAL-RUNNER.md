# Iteration 2 / ENG-08 — Local Lab Runner (controller-only)

**Status: source implementation ready for CI, actual Desktop/Work Lab E2E NOT_RUN.**
This complements rather than replaces scripts/eval/campaign.py, scripts/eval/receipt.py,
iteration02_handoff.py and iteration02_result_intake.py. Historical external
Drive/write authorization has not been carried into this component.

## Supported flow

1. Obtain a **source-locked Lab candidate** from CI or build_lab_plugin.py.
   The one-command controller can prepare its executor pack through the
   existing iteration02_handoff.py protocol when
   --lab-candidate-dir is supplied; or use a previously prepared, pinned pack.
2. Install the pack in a **disposable, approved, network-/secret-restricted
   TEST environment**. The runner cannot enforce an external OS sandbox.
3. Provide an **absolute path and SHA-256 digest** for a reviewed executable
   adapter. Adapter receives one JSON request over stdin, without rubrics or
   private data. It returns a JSON object on stdout containing: case_id,
   attempt, source_revision, execution_state and structured steps. The external
   adapter must bind a real model/tool session, capture real traces, and
   enforce its own TEST isolation.
4. Run one case/attempt and archive a unique observation:

   ~~~bash
   python scripts/eval/iteration02_local_runner.py \
     --pack .tmp/iteration02-test-handoff \
     --lab-candidate-dir .tmp/lab \
     --archive-root .tmp/iteration02-observations \
     --case-id I02-240-local-runner --attempt 1 \
     --adapter /absolute/approved/test-executor \
     --adapter-sha256 <verified-64-hex> \
     --approve-isolated-lab-exec
   ~~~

   Never use Production, real user accounts, connected Drive, Supabase or
   Site/browser/desktop lanes. Only frozen lab cases may be dispatched.
5. For each attempt the controller creates
   runs/<case-id>/<attempt>/record.json plus adapter-response.json when the
   adapter response was valid. Both preserve source/release/payload, adapter,
   input and output digests. The controller never assigns model PASS.
6. Independent evaluator must review real provider tool steps, exact runtime
   identity, output, client display if applicable, and frozen rubric. Only
   then may a validated provider/evaluator observation be translated into
   iteration02_result_intake.py or the canonical receipt.py/campaign.py
   evidence contract. An executed local subprocess does not prove model execution.

## Safety and replay semantics

- Explicit approval flag and full executable SHA-256 pin are mandatory.
- The child gets a minimal environment without copied cloud credentials.
  This is defense in depth, NOT OS-enforced isolation: the operator must use
  a sandbox whose network/filesystem are restricted.
- Only regular locked inputs, matching prompt digest, exact Lab release, and
  valid attempt ranges are accepted. No symlinks or external prompts.
- The attempt directory is atomically reserved. Repeat calls never rerun.
  A completed attempt returns ALREADY_ARCHIVED_NO_REEXECUTION; a previously
  blocked attempt returns PRIOR_BLOCKED_NO_REEXECUTION. Crashes that leave
  incomplete evidence require manual recovery.
- Timeout and response-size caps, no shell expansion, explicit error states.
  A claimed model execution with no tool steps remains BLOCKED_ADAPTER.
- Tests exercise a real temporary subprocess fixture, NOT a model.

## Remaining #240 acceptance

| Criterion | Current implementation | Remaining |
| --- | --- | --- |
| One command prepares, executes, archives | Existing pack prepare + local controller archive | Combined pack preparation + isolated fixture adapter execution implemented; approved real model adapter pending, PARTIAL |
| Resume does not duplicate run | Atomic attempt reservation and regression tests | Multi-process crash/recovery smoke |
| Unassisted executor cannot see rubric | Prompt-only pack; rubric SHA only | Real model input/trace inspection |
| CLI and Desktop separate receipts | CLI adapter observations only | Actual Desktop/Work runtime trace |
| No inherited external-write rights | Minimal child env, Lab-only case restriction | Approved OS-level TEST sandbox |
| Canonical receipt/campaign integration | Pinned digests and independent-review handoff | Independently validated receipt import |

No claim of iteration Done, actual model runtime PASS, deployment or permission
to access external systems is made by the controller.
