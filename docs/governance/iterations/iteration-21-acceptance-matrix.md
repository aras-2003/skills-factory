# Iteration 21 acceptance matrix

This matrix is part of the proposed scope lock for #704. No row is PASS until execution evidence is attached to the exact candidate.

| Row ID | Issue / criterion | Layer + case ID / definition | Required / N/A rationale | Candidate SHA + artifact digest | Surface/model/tools | Input/rubric hashes | Execution state | Verdict | Receipt/output/trace + run time | Reviewer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 21-AC01-T01 | #704 AC-01 | Offline: canonical grammar and required/conditional section matrix are versioned and each element has a plain-language purpose. | Required | Pending | Repository source | Test revision | NOT_RUN | — | Pending | Owner-delegated Codex review |
| 21-AC02-T02a | #704 AC-02 | Offline positive fixture: valid XML body with substantive content passes. | Required | Pending | Local validator | Fixture hash | NOT_RUN | — | Pending | Owner-delegated Codex review |
| 21-AC02-T02b | #704 AC-02 | Offline negative fixture: malformed XML fails with file and location. | Required | Pending | Local validator | Fixture hash | NOT_RUN | — | Pending | Owner-delegated Codex review |
| 21-AC02-T02c | #704 AC-02 | Offline negative fixture: missing required section fails with file and location. | Required | Pending | Local validator | Fixture hash | NOT_RUN | — | Pending | Owner-delegated Codex review |
| 21-AC02-T02d | #704 AC-02 | Offline negative fixture: empty or dummy-only section fails with file and location. | Required | Pending | Local validator | Fixture hash | NOT_RUN | — | Pending | Owner-delegated Codex review |
| 21-AC02-T02e | #704 AC-02 | Offline negative fixtures: duplicate and unknown structural elements fail with file and location. | Required | Pending | Local validator | Fixture hashes | NOT_RUN | — | Pending | Owner-delegated Codex review |
| 21-AC02-T02f | #704 AC-02 | Offline negative fixture: literal or untrusted text that violates the grammar fails clearly without being treated as instructions by the validator. | Required | Pending | Local validator | Fixture hash | NOT_RUN | — | Pending | Owner-delegated Codex review |
| 21-AC03-T03 | #704 AC-03 | Offline: authoring template has substantive XML examples and valid unchanged YAML frontmatter / Markdown packaging. | Required | Pending | YAML + template validator | Test revision | NOT_RUN | — | Pending | Owner-delegated Codex review |
| 21-AC04-T04 | #704 AC-04 | Offline: existing representative skill fixtures and the full repository validator pass; changed tests fail when their assertions are intentionally violated. | Required | Pending | Repository CI | Test revision | NOT_RUN | — | Pending | Owner-delegated Codex review |
| 21-AC04-S01 | Iteration shared sentinel | Offline: YAML frontmatter and catalog registration remain valid. | Required | Pending | Repository CI | Test revision | NOT_RUN | — | Pending | Owner-delegated Codex review |
| 21-AC04-S02 | Iteration shared sentinel | Offline: trigger descriptions and routing registrations for unchanged skills remain unchanged. | Required | Pending | Repository CI | Test revision | NOT_RUN | — | Pending | Owner-delegated Codex review |
| 21-AC04-S03 | Iteration shared sentinel | Offline: tool permission declarations remain unchanged. | Required | Pending | Repository CI | Test revision | NOT_RUN | — | Pending | Owner-delegated Codex review |
| 21-AC04-S04 | Iteration shared sentinel | Offline: evaluator-only rubrics and fixtures remain excluded from distributable artifacts. | Required | Pending | Repository CI | Test revision | NOT_RUN | — | Pending | Owner-delegated Codex review |
| 21-AC04-S05 | Iteration shared sentinel | Offline: package manifest and catalog generation remain deterministic and include no unintended skill changes. | Required | Pending | Repository CI | Test revision | NOT_RUN | — | Pending | Owner-delegated Codex review |
| 21-AC04-R01 | Iteration rotating probe | Offline unchanged source probe: `skills/web-design/accessibility-gate/SKILL.md`; compare canonical source and generated Lab package hashes. | Required | Pending | Repository CI | Source + artifact hashes | NOT_RUN | — | Pending | Owner-delegated Codex review |
| 21-AC04-R02 | Iteration rotating probe | Offline unchanged source probe: `skills/investing/fundamental-intelligence/SKILL.md`; compare canonical source and generated Lab package hashes. | Required | Pending | Repository CI | Source + artifact hashes | NOT_RUN | — | Pending | Owner-delegated Codex review |
| 21-AC05-T05 | #704 AC-05 | Offline documentation review: static validation is clearly separated from model behavior, loader/channel compatibility and release acceptance. | Required | Pending | Documentation review | Test revision | NOT_RUN | — | Pending | Owner-delegated Codex review |
| 21-AC05-RUNTIME | #704 AC-05 | Runtime/model behavior and cross-channel compatibility. | N/A: no skill instructions, runtime loaders, permissions, routing, package contents or release behavior change in this tooling-only increment. #682 retains these as mandatory future acceptance. | N/A | N/A | N/A | NOT_RUN | N/A pending review | Scope rationale in iteration record | Owner-delegated Codex review |

## Inventory and execution totals

| Layer / surface | Required distinct scenarios | Planned executions / repetitions | Executed PASS | Executed FAIL | NOT_RUN / BLOCKED / REVIEW_REQUIRED | Reviewed N/A | Evidence compatibility |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Offline parser/authoring fixtures | 7 | 1 each: positive, malformed, missing, empty/dummy, duplicate/unknown, literal/untrusted, frontmatter/template | 0 | 0 | 7 | 0 | Pending exact candidate |
| Offline shared sentinels | 5 | 1 each in PR and final-main CI | 0 | 0 | 5 | 0 | Pending exact candidate |
| Offline rotating probes | 2 | 1 each in PR and final-main CI | 0 | 0 | 2 | 0 | Pending exact candidate |
| Documentation review | 1 | 1 per candidate | 0 | 0 | 1 | 0 | Pending exact candidate |
| Runtime/model compatibility | 0 | 0 | 0 | 0 | 0 | 1 | N/A rationale requires reviewer acceptance |
