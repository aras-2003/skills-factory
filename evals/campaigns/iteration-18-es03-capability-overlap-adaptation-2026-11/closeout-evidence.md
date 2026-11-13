# Iteration 18 / ES-03 closeout evidence

This record is bound to the exact Skills Factory main candidate and the exact private Site/Lab artifact below. It is evidence for #618, not a claim that the iteration is closed.

## Candidate identity

- Protected `main` SHA: `1d55767564bd092935c4d8a21fa0debc7a382db2` (verified from GitHub `branches/main` at 2026-11-13T19:10Z).
- Lab: `1.38.531+1d55767564bd`; payload SHA-256 `350723b32224f4efab35ac95eb0b208a7f718a782be1fad941cd2d5706d228d5`; artifact SHA-256 `3a58288a95e8e4046bbb32a6899df3e133f1b79c024821698757ad94039a9630`; catalog digest `b028e2387f1f81cf54f959d25879a2633d554e6044ae2f693bb644f7319a88b4`; canonical registry SHA-256 `cc977739b50c24b6fa3af9c3900e499fff1784caf84e62a9635f8f42cff85baf`.
- Site mirror SHA: `6e608c569ecc6048c3ac3de1e4eedd90d64a07cb`, generated and pushed by the official Sites workflow from that main SHA.
- Site version 134: `appgprj_6ac56f2116588191a4a1ebc682c97865~appgver_66db55ccb5a48191a547a842e050af72`.
- Latest private deployment: `appgdep_6af7615f76fc819184b570af6107c17f`, `succeeded`, environment revision 132. Owner-only access was retained.

## Offline validation

Executed on 2026-11-13 against the exact main SHA above, in the repository's locked Python environment:

| Command / suite | Result |
| --- | --- |
| `scripts/validate/validate_all.py` | Exit 0. Existing MEDIUM/LOW advisory findings remain; no blocking validator failure. |
| `python -m unittest discover -s scripts/engineering/tests -p 'test_*.py'` | 27 passed. Includes matcher duplicate, extension and conflict cases. |
| `python -m unittest discover -s scripts/security/tests -p 'test_*.py'` | 64 passed. Includes receipt binding/tamper, review authorization, dependency support and isolated proposal cases. |
| `python -m unittest discover -s scripts/package/tests -p 'test_*.py'` | 102 passed. |
| `scripts/eval/validate_routing.py` | `Natural routing fixtures: OK`. |
| `scripts/provenance/migrate.py --check` | `Provenance registry: OK (98 source records)`. |
| `scripts/package/build_lab_plugin.py --output .tmp/iter18-lab` | Built 79 skills, 19 workflow entrypoints and 42 runtime eval inputs. |
| `scripts/package/artifact_validation.py --lab .tmp/iter18-lab` | `Artifact validation: OK`. |
| `scripts/eval/validate_isolation.py --artifact .tmp/iter18-lab` | `Eval isolation: OK`. |

The matcher test source SHA-256 is `ec273f454ff2138be3df57adc6c042bf2856f3dd2f4ad7f5becb256f9b01dc99`; adaptation security test source SHA-256 is `5b30ee1107892e36cea7f774b18afd5e4224fef2556de8e488483cd99f348735`; routing cases SHA-256 is `df62ddd52f5e53d319bbf79b94b7388271f097c7e94ab99a8b9dc7ada0502d90`.

Static security review of `scripts/engineering/capability_overlap.py` (`cfc7f722f6459396850a00000b10996976aa44b6aaf62b193ce3e2a21a2ecfec`) and `scripts/security/propose_skill_adaptation.py` (`63a9b153ee33d3057c246156520a2ae46b83814443a27f122197b8a8821a9cd7`) found no subprocess, HTTP client, socket, `os.system` or dynamic `exec` use. The adapter writes only an isolated proposal directory; the security suite verifies rejection of canonical skill-tree writes, extra quarantine files and symlinks. This is a bounded source review plus tests, not a network-monitoring claim.

## Unchanged-domain probes

These were frozen in the acceptance matrix before the targeted executions:

1. **Investment OS:** `scripts/validate/validate_investing.py` passed (15 skills, 7 workflows, 6 isolated evals, 20 relational entities); `test_business_lifecycle.py` passed 6 tests; `test_financial_quality.py` passed 3. Input hashes: validator `db0bca93c7d1b05b715a6217d5fd9dbec8d74e13ae4c8e05fd64c2935e651e05`, lifecycle `8fffce3e570b86e4739e3ca7d757a94d38df9faea9056a5569ee14959e3927e3`, financial quality `0bba42e7b2ca1669d3b336ee09243df72d487aacac0f04cb45d83725042ed868`.
2. **Presentation OS:** `scripts/validate/presentation_model.py` passed (`Canonical Presentation DeckSpec v1 valid`); `test_presentation_design_library.py` passed 7 tests. Input hashes: `ad60e275e0de1ff0fb9ce1eda903f419376a2e8f38b8b365f64cc116ad484a63`, `9960571dd0feff5c4d9c6af7dd4d56a68392b51af549ee546251cf929848ec2e`, respectively.

## GitHub checks

All checks below are completed successfully for exact main SHA `1d55767564bd092935c4d8a21fa0debc7a382db2`:

- [Validate skills](https://github.com/aras-2003/skills-factory/actions/runs/43484441780)
- [Domain integrity](https://github.com/aras-2003/skills-factory/actions/runs/43484441946)
- [Skills Factory Site CI](https://github.com/aras-2003/skills-factory/actions/runs/43484441976)
- [Lab packaging](https://github.com/aras-2003/skills-factory/actions/runs/43484441962)
- [Pages build and deployment](https://github.com/aras-2003/skills-factory/actions/runs/43484440845)

## Exact-version Site runtime smoke

`runtime_info`, `list_skills` and `load_skill("skill-development")` were invoked after version 134 deployment. The first two report attestation `verified`, mirror SHA `6e608c569ecc6048c3ac3de1e4eedd90d64a07cb`, canonical SHA `1d55767564bd092935c4d8a21fa0debc7a382db2`, release `1.38.531+1d55767564bd`, and 98 skills. The loaded skill has content SHA `aceeab54d8404d25dacdcb3aee90345481047e8061ffaf42774ecb61cd02da79`; its allow-listed `references/WORKFLOW.md` includes the exact `runtime_dependency_review` gate.

Unsigned MCP call receipts (tool receipts prove invocation/output identity, not an independent signature):

| Tool | Completed at UTC | Input SHA-256 | Output SHA-256 | Source revision |
| --- | --- | --- | --- | --- |
| `runtime_info` | 2026-11-13T19:27:50.016Z | `44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a` | `59c4e3c57b63e0089518db605ed50580a8936aa832725ca6ef48ecad7ede90d4` | `6e608c569ecc6048c3ac3de1e4eedd90d64a07cb` |
| `list_skills` | 2026-11-13T19:27:51.014Z | `44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a` | `ced7026d25ed81bc4148b422b34082e6a972ce627491f286b7a8198c46b0ff72` | `6e608c569ecc6048c3ac3de1e4eedd90d64a07cb` |
| `load_skill` | 2026-11-13T19:27:52.106Z | `5061cfee546e17080e19b27f0f52f682e8b96880d2ca7a4ff7d6852435db74a9` | `a8c612622de3d3307eea04e5297cce0c41b8be92773df4d1fddf4c1c056584c6` | `6e608c569ecc6048c3ac3de1e4eedd90d64a07cb` |

## Remaining acceptance gap

The frozen `workflows/skill-development/tests/cases.yaml` contains direct-positive, indirect-positive, near-miss-negative, competing-route, conflict and dependency-boundary prompts. Static fixture validation passes, and the exact package/runtime identity is proven. This Codex session can invoke Site MCP `list_skills` and `load_skill`, but exposes no host-selection trace for those prompts. A manual `load_skill` call is not evidence that the host model selected the route from a prompt, so row 18-11 remains `REVIEW_REQUIRED`; the four core routing prompts are not claimed as executed. The conflict route also requires three independent host-level executions if it is model-mediated. Do not close #618 or start #619 until this evidence is obtained or the frozen acceptance is formally clarified.
