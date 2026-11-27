# Frozen test plan — bounded handoff validator task

Candidate C4: `6690ff6475b317774c845bc496da18a2c5928ece`  
Baseline main-parent: `e4f96cc7c0e2b139c59f72d0b69bc880504b08a4`  
Issue links: #748, #768

| Case | Fixture and assertion | Result |
|---|---|---|
| `DH-RO-01` | Valid Executor and Reviewer `PASS`, each with a nonempty changed path; assert `ValueError`. | RED on C1 (both subcases); PASS on C4. |
| `DH-RO-02` | Valid Executor and Reviewer `PASS` with empty paths; assert accepted. | PASS on C4. |
| `DH-RO-03` | Valid Executor and Reviewer `FAIL` with a nonempty path, failed case, and nonzero command; assert path is retained. | PASS on C4. |
| `DH-DEV-01` | Valid Developer `PASS` with a nonempty path; assert accepted and path retained. | Added after independent-review finding; PASS on C4. |
| `DH-SHA-01` | Real C1 result SHA supplied to `validate_result` with trusted expected C4 SHA; task, role, case, and fixture policy otherwise valid. | Fresh-thread resume probe rejected C1 with `candidate SHA mismatch`. |
| `DH-MAN-01` | Refresh the existing continuation source pins only for changed support bytes; verify historical hashes and release fields remain unchanged. | Governance test passed on C4 (6/6). |

Executor commands on C4:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_delegation_handoff.FixturePolicyContractTests -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_delegation_handoff -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.governance.test_sdlc_architecture_source_example -v
```

The recorded scope is those tests only; these results do not establish the broader E2E campaign or production acceptance.
