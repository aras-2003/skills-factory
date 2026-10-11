---
name: skills-factory-diagnostic
description: 'Confirm that the Skills Factory plugin is exposing bundled skills to
  ChatGPT or Codex. Use when the user explicitly asks to test, verify, diagnose, or
  confirm whether Skills Factory is active.

  '
metadata:
  owner: arkadiusz-kamrowski
  version: 1.0.1
  maturity: production
  risk: low
  last_reviewed: '2026-10-09'
---

# Arek Skills Diagnostic

## Purpose

Verify that the installed Skills Factory plugin exposes bundled skills to the runtime.

## Procedure

When invoked for an explicit plugin/skill availability test:

1. State exactly: `SKILLS_FACTORY_ACTIVE`.
2. List this skill name: `skills-factory-diagnostic`.
3. State that the runtime successfully loaded the skill instructions.
4. Do not claim that other skills are available unless they are actually visible to the runtime.

## Output contract

Keep the response to at most three short lines.
Use this exact three-line shape:
`SKILLS_FACTORY_ACTIVE`
`Loaded skill: skills-factory-diagnostic`
`Skill instructions loaded successfully.`

## Quality checks

- Do not emit the marker unless this skill was actually loaded.
- Do not infer availability from the plugin mention alone.
