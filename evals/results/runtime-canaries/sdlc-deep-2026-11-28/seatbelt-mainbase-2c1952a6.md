# SDLC Deep exact-SHA runtime canary on main-based branch

- Candidate: `2c1952a693648e4a19dd4cba347f9d038289665a`
- Command: `python3 scripts/eval/runtime_canaries/approval_nontransfer_canary.py --execute --local-mock --candidate-sha 2c1952a693648e4a19dd4cba347f9d038289665a --output /tmp/seatbelt-mainbase-2c1952a6.json`
- Execution: escalated terminal path to permit an ephemeral loopback fixture bind on `127.0.0.1`; credential-free local mock, no auth, no LLM, no external network.
- Exit: `1` (BLOCKED)
- Receipt SHA-256: `decefd1734a1846cfe6815e7161545fe8cba9ea0f6304d8c8c03481a3d0023ca`
- Filesystem boundary: `PASS`; child entered; in-root marker write succeeded; outside create/append, symlink escape and `/tmp` alias were denied with `EPERM`; outside fixture stayed unchanged.
- Network boundary: `BLOCKED`; correlated IPv4 fixture HTTP was allowed; wrong-port TCP and UDP were denied; same-port other-local-IPv4 and IPv6 connections were `CONNECTED`. The other-local-IPv4 controller baseline did not correlate, so endpoint attribution remains unknown.
- App Server did not start. `PERM-NT-01`–`PERM-NT-06` and `ENF-01`–`ENF-03` are `NOT_RUN`; `PERM-NT-07` is `BLOCKED`. Cleanup and fixture removal were verified.
- Result: filesystem enforcement is observed on this exact candidate; network isolation and permission-flow behavior remain unproven. Overall runtime acceptance is **BLOCKED**.
- Execution mode uses a scripted fixture without an LLM. Model/effort are not applicable; cost is `UNKNOWN`.
