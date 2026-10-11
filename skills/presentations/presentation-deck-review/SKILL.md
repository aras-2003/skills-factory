---
name: presentation-deck-review
description: >
  Critique a real or draft presentation for strategy, audience fit, evidence integrity, narrative and visual craft; rank specific defects and guide targeted revision. Use before final delivery or after deck changes; do not confuse an opinion score with verified rendered output.
metadata:
  owner: arkadiusz-kamrowski
  version: "0.1.0"
  maturity: draft
  risk: medium
  last_reviewed: "2026-10-09"
---

# Presentation Deck Review

## Purpose
Independently challenge whether this deck changes the intended audience's mind/decision with credible evidence and competent presentation design. Own presentation editorial/design review and fidelity to domain conclusions; **do not certify strategy quality** based on slide polish or replace domain strategy-review controls.

## Preconditions
A sufficient brief and story plus actual deck evidence (rendered screenshots/slide text and source ledger when available). If only an outline exists, review only the outline and mark visual verification unrun.

## Procedure
1. **Audience outcome test:** can a real target reader say what decision/behavior is requested and why now? Is the ask specific and feasible? For a teaching/keynote profile, substitute the intended learning/engagement outcome.
2. **Story test:** read action titles alone. Check logic, transitions, key objection, alternate choices, recommendation proportional to evidence, slide role and appendix balance. Flag the most fragile underlying assumption and send decision-material challenges to the domain owner; no automatic praise or independent selection of a new strategy.
3. **Evidence/ethics test:** inspect claim-ledger mapping and contradicting sources. Block fabricated numbers, causal overreach, unlicensed assets, secret leakage, misleading axes and false affiliations.
4. **Actual visual test:** inspect render screenshots or visual tool output per slide (overview montage plus all crowded/high-risk slides). Assess hierarchy, contrast, alignment, whitespace, typographic legibility at projection/mobile/leave-behind size, chart choices, source line, accessibility, brand coherence, visual consistency, layout variety and purposeful motion.
5. Classify each defect with `slide_id, severity(CRITICAL|MAJOR|MINOR), dimension, observed_evidence, correction, verification_method`. Separate observed defect from suspected issue; never call absent tool render a visual PASS.
6. Conduct adversarial **communication** review: what would a skeptical audience member misunderstand or distrust? For a strategic recommendation, check fidelity against its Strategy decision/evidence pack. If upstream strategy challenge/review was not actually performed, record `DOMAIN_VALIDATION=NOT_RUN` or `BLOCKED`; presentation QA is not proof of good strategic choices. Escalate absent/contradictory options upstream and do not rewrite a sound argument for style preference.
7. Send **targeted** corrections to the responsible owner: strategic assumption/option → Strategy OS; source-to-slide fidelity → evidence; communication narrative → storyline; exhibit → exhibit design; visual execution → authoring. Re-render changed slides plus affected neighboring slides; check regressions.
8. Iterate within a bounded cycle; default two editorial revisions then deliberate escalation if same material blocker persists. Stop when critical/major issues are resolved with evidence, or status `REVIEW_REQUIRED / BLOCKED` remains explicit. No guarantee from iteration count or decorative composite score.

## Decision rules
A single critical misleading claim, privacy leak, missing required diagram, unreadable slide or absent requested editable artifact blocks release regardless of average score.
A draft outline may pass `STORY_REVIEW` while `RENDER_REVIEW=NOT_RUN`; neither is `DECK_VERIFIED`.
Prefer a complete correction ledger to subjective scoring. Independent second reviewer/model where practical; never invent second-review results.

## Inputs
Brief, approved story, evidence ledger, actual artifact/screenshot receipts, design tokens and prior defects.

## Output contract
`DeckReview{brief_fit,storyline_state,source_decision_fidelity,domain_validation_state,upstream_review_required[],evidence_state,visual_state,editability_state,findings[],required_fixes,changes_verified,rerun_needed,final_state}`.
Final states `APPROVED_FOR_VERIFICATION | REVIEW_REQUIRED | BLOCKED | NOT_RUN`.

## Failure/uncertainty
If screenshots are not available, state cannot verify layout/legibility; request render or treat review partial. If no access to original data, mark material claims unverified instead of guessing.

## Quality checks
- [ ] Every critical/major defect has slide ID and remedy.
- [ ] Observed rendered evidence differentiated from proposals.
- [ ] Corrects real risks instead of maximizing a cosmetic score.
- [ ] Actual revisions verified against regressions.
