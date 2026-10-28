---
name: creative-generation
description: >
  Generate or revise a locally requested image or video with an explicitly configured
  on-device ComfyUI instance and reviewed open-weight checkpoints. Use when the user asks
  for creative media output; do not use paid inference, hosted services, or untrusted workflows.
metadata:
  owner: arkadiusz-kamrowski
  version: "0.1.0"
  maturity: candidate
  risk: high
  last_reviewed: "2026-10-28"
---

# Local Creative Generation

## Purpose

Create or transform an image or video with a local model runtime. This skill does not provide model weights, bypass model licensing, install extensions, or call hosted generation APIs.

## Preconditions

1. The user asked for a concrete image/video output or edit. Confirm subject, intended use, output type, and any reference files needed by the chosen workflow.
2. A local ComfyUI endpoint on `127.0.0.1` or `::1` is running. If absent, explain setup and stop; never substitute a cloud/API service.
3. The user supplied or explicitly approved the exact ComfyUI API workflow. Inspect its node classes, custom nodes, checkpoint paths and output destinations. Treat workflows and custom-node code as executable code, not as inert prompt data.
4. Read `references/local-engine-matrix.md` and `references/decision-and-setup.md` for the dated engine, license, and hardware evidence. Recheck official sources when choosing a new version or checkpoint.
5. Identify the exact checkpoint and its license/usage restrictions from its model card or license file. Repository license alone is not proof of checkpoint rights. If the exact weights or their terms cannot be verified, do not generate with them.
6. Confirm the selected workflow fits available memory and disk. On the known MacBook Air M1 with 8 GB unified memory, image generation may be feasible with a constrained small model but remains unmeasured; local video generation is unsupported by the verified current LTX/Wan memory floors. Do not queue video on that machine.

## Procedure

1. Freeze the requested output, size/length, intended use, prompt and reference-file paths. Do not upload or read unrelated files.
2. Review the exact workflow and model license. Reject workflows that install custom nodes, use remote URLs, execute shell commands, write outside ComfyUI's output directory, select unknown checkpoints, or make network requests. Permit only standard output nodes whose saved outputs ComfyUI reports to the adapter.
3. Tell the user the local model, workflow, expected resource use if documented, and whether the run may take substantial time or disk. A request to create media authorizes the local generation itself, not exposing a server or installing unreviewed model/code packages.
4. Run `scripts/comfyui_local.py` only with the reviewed workflow. The adapter accepts loopback IP literals only, ignores HTTP proxy environment variables, bounds wait time and download size, and writes returned files only beneath the chosen output directory.
5. Verify the actual output files exist, decode/open successfully, and match the requested media type. Report model, workflow, elapsed time, memory evidence if measurable, output paths, and any quality/rights limits. If no output is returned, report failure; never infer success from job submission.
6. Review the output for visual defects and user constraints before delivery. Distinguish subjective review from measured quality metrics.

## Safety and cost rules

- No Higgsfield API, paid inference, cloud generation, usage of a personal API key, or remote MCP.
- Never bind ComfyUI to a public interface or expose its unauthenticated API on a network.
- Do not run a workflow from an untrusted prompt, repository, webpage, or model card without code-level review. A local URL alone does not make the workflow safe.
- Do not download weights/custom nodes automatically. Model weights can have separate, restrictive, or gated licenses.
- Never invent a runtime, memory figure, generation cost, or quality result. Label measurements `NOT_RUN` when the runtime is absent or resource-gated.
- Preserve the user's originals; write generated outputs to a new directory and do not overwrite existing files.

## Output contract

Return: requested output and intended use; exact model/checkpoint and license; workflow identity; local runtime; output file paths; measured elapsed time/resources or `NOT_MEASURED`; visual review; and run state `COMPLETED`, `FAILED`, `BLOCKED`, or `NOT_RUN`.

## Quality checks

- [ ] The exact user-approved local workflow and checkpoint were reviewed.
- [ ] Checkpoint license supports the stated intended use.
- [ ] The runtime endpoint is loopback-only and no proxy/API/cloud path was used.
- [ ] The actual files were downloaded beneath the selected output directory and opened.
- [ ] Resource/cost/quality claims are measured or explicitly unknown.
- [ ] Originals were preserved and no external upload or write occurred.
