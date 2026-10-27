# Executive Role Evaluator — Hard Output Gate Regression

Date: 2026-09-30  
Previous version: 1.0.1  
Candidate fix: 1.0.2

## Runtime finding

Explicit role-impact routing worked correctly, but the runtime still produced narrative before the required Decision/Confidence summary.

## Root cause hypothesis

The previous contract described Decision and Confidence as mandatory fields, but treated their placement as template guidance rather than a hard execution gate.

## Fix

Version 1.0.2 makes the first decision block mandatory and ordered:
1. Decision
2. Confidence
3. Role archetype
4. Role Quality
5. Candidate Fit
6. Career Value
7. Risk

No prose, caveat, source note or table may precede it.

## Regression acceptance

PASS only if role-evaluation responses begin with the mandatory block. Unsupported numeric fields must say `insufficient evidence` rather than being omitted or fabricated.

Disposition: **APPROVE WITH NATIVE RUNTIME FOLLOW-UP**
