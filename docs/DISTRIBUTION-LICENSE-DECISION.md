# Distribution and license decision — AIS-19

Status: **OWNER APPROVED — personal / proprietary toolkit (D1-A)**.

This repository being publicly visible does not by itself choose a reuse license. This document intentionally does not add a LICENSE or grant reuse rights.

## Decision options

### A. Personal / proprietary toolkit

Intent: source is maintained primarily for the owner's use and distribution through the owner's runtime packages.

Implication: make the intended audience and no-grant posture explicit. Public visibility remains possible, but third-party reuse is not licensed beyond rights that apply by law/platform terms.

### B. Public reference, no general reuse grant

Intent: others may inspect the architecture and examples, but no broad permission to copy/modify/distribute is granted.

Implication: README/package metadata should state that the repository is published as reference material and that reuse requires permission.

### C. Reusable open-source library

Intent: allow third-party use/modification/distribution.

Implication: owner selects a specific license after considering desired attribution, patent, commercial-use and copyleft terms. Only then add the matching LICENSE and align README/package metadata.

## Owner decision — 2026-10-14

- chosen model: **A. Personal / proprietary toolkit**.
- chosen license/terms: **No general third-party reuse license granted**.
- intended audience: owner `aras-2003`, through the owner's runtime packages; existing public repository visibility and private Site audience are retained.
- commercial reuse: not authorized by a general grant; requires separate owner permission for owner-controlled material.
- redistribution/modification: no general grant; rights under applicable law and GitHub platform terms remain unaffected.
- attribution: no attribution-only permission is created by this decision.
- effective record date: **2026-10-14**; this documents the existing no-grant posture rather than relicensing historical versions.

Authorization: in the chat “Test | Iter 1”, the owner answered **“zgoda, wszędzie przyjmuję rekomendację”** to the concrete D1–D4 options recorded in [PR #344's exact decision file](https://github.com/aras-2003/skills-factory/blob/14a6e8087ee949693450979e24fd979222f18687/evals/results/iteration-01-safety-governance-2026-10/2026-10-13-owner-decisions.md). D1-A was the personal/proprietary recommendation. The decision applies only to owner-controlled original material; third-party licenses and imported assets retain their own terms.

Package metadata must not claim MIT, Apache-2.0 or another open-source license. No invented proprietary LICENSE text is added.
