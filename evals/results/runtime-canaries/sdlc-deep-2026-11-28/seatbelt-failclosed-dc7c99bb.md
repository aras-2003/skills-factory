# SDLC Deep exact-SHA runtime canary

- Candidate: `dc7c99bb5adfcdf8d7d181a6b0385601a127b45b`
- Command: `python3 scripts/eval/runtime_canaries/approval_nontransfer_canary.py --execute --local-mock --candidate-sha dc7c99bb5adfcdf8d7d181a6b0385601a127b45b --output evals/results/runtime-canaries/sdlc-deep-2026-11-28/seatbelt-failclosed-dc7c99bb.json`
- Exit: `1` (expected for BLOCKED)
- Receipt SHA-256: `575276374621d06ded439ac780b179e6b0a190bc7cff6405b88112ebfc34d219`
- Result: `BLOCKED`; CLI version observed as `codex-cli 0.159.1`; App Server did not start; `PERM-NT-01`–`PERM-NT-06` and `ENF-01`–`ENF-03` are `NOT_RUN`; `PERM-NT-07` is `BLOCKED`; cleanup and fixture removal were reported verified.
- Limitation: receipt contains no filesystem or network preflight result and only the generic reason `local mock precondition or protocol unverified`. The failure phase and cause are **UNKNOWN**. This run does not prove filesystem or network enforcement and does not justify attributing the failure to the sandbox.
- Execution mode: credential-free scripted local mock; no LLM execution. Effective model/effort and cost are not applicable/unknown.
