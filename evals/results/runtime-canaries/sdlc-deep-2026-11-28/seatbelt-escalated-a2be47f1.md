# SDLC Deep exact-SHA runtime canary (escalated local bind)

- Candidate: `a2be47f1393f414cd75f213222332d636e975618`
- Command: `python3 scripts/eval/runtime_canaries/approval_nontransfer_canary.py --execute --local-mock --candidate-sha a2be47f1393f414cd75f213222332d636e975618 --output /tmp/seatbelt-escalated-a2be47f1.json`
- Execution: escalated terminal path to allow an ephemeral loopback fixture bind on `127.0.0.1`; credential-free local mock, no auth, no LLM, no external network.
- Exit: `1` (BLOCKED)
- Receipt SHA-256: `37959ca252d707798ee0fbf4a1b8b763f052198cfe901d78b572cee3ab0fd6d4`
- Filesystem boundary: `PASS`; child entered; in-root marker write succeeded; outside create/append, symlink escape and `/tmp` alias were denied with `EPERM`; outside fixture stayed unchanged.
- Network boundary: `BLOCKED`; correlated IPv4 fixture HTTP was allowed; wrong-port TCP and UDP were denied; same-port other-local-IPv4 and IPv6 connections were `CONNECTED`. The other-local-IPv4 controller baseline did not correlate, so endpoint attribution remains unknown. Do not treat the IPv6 connection as the only exception.
- App Server did not start. Permission cases `PERM-NT-01`–`PERM-NT-06` and `ENF-01`–`ENF-03` are `NOT_RUN`; `PERM-NT-07` is `BLOCKED`. Cleanup and fixture removal were verified.
- Result: filesystem enforcement is observed for this candidate, but network isolation and permission-flow behavior remain unproven. Overall runtime acceptance is **BLOCKED**.
- Effective model/effort and cost: not applicable to the scripted local mock / `UNKNOWN` for cost.
