# Executive Role Evaluator — Runtime Regression Review

Date: 2026-09-30  
Previous version: 1.0.0  
Candidate fix: 1.0.1

## Observed runtime behavior

### Test A — inflated CTO
Reasoning quality passed: the runtime challenged title inflation, authority gaps and vendor-heavy operating model.

Regression:
- decision/confidence were implicit rather than explicit;
- the full output contract was not followed consistently.

Fix:
- add compact output mode;
- require explicit Decision and Confidence whenever the evaluator triggers.

### Test B — factual Kelvion research
Research quality passed, but the answer drifted from company facts into unsolicited CTO-role interpretation because prior career context was present.

Regression:
- boundary between `company-context-research` and `executive-role-evaluator` was too weak.

Fix:
- evaluator now requires explicit role-evaluation intent;
- pure company research must not append career implications;
- new `company-context-research` skill owns factual company research and hands off only on explicit role-impact requests.

## Release disposition

**APPROVE 1.0.1 WITH NATIVE ROUTING FOLLOW-UP**

Required runtime checks:
1. pure company research does not trigger evaluator behavior;
2. explicit role-impact question does trigger evaluator;
3. simple role evaluation starts with explicit Decision and Confidence;
4. CV tailoring remains outside evaluator.
