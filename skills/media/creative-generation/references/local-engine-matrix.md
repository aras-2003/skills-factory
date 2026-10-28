# Local engine and checkpoint evidence

Snapshot date: 2026-10-28. These sources bound the candidate; they are not a benchmark on the user's machine.

## Runtime

- **ComfyUI** is the candidate adapter target because it exposes a local HTTP queue/history/output interface and supports image/video workflows. This adapter consumes a reviewed API-format workflow; the user must install ComfyUI and select/install the graph and models themselves. It does not install models or custom nodes.
- **Current user machine:** MacBook Air 10,1, Apple M1, 8 GB unified memory. No ComfyUI or DiffusionBee installation was found in the inspected environment. Image/video E2E is therefore `NOT_RUN` until a local runtime and exact checkpoint are available.
- Apple's MLX Swift Stable Diffusion example documents a constrained path that may run below 4 GB available memory (typically on machines with at least 6 GB total), but it warns that generation can exit under memory pressure. Its documented checkpoint is SDXL Turbo; do not treat this as a result for ComfyUI or a quality benchmark.
- Lightricks LTX Desktop supports local video only on Apple Silicon with at least 15 GB free RAM; otherwise it uses API-only mode. That local threshold cannot be met on an 8 GB machine.
- Apple's MLX Wan2.1 example reports about 10 GB RAM for the 1.3B T2V model at 81 frames (unquantized), while the upstream Wan2.1 model card reports 8.19 GB VRAM for its CUDA setup. Those figures do not show a successful local video run on an 8 GB unified-memory M1.

## Checkpoint rights and resource limits

| Checkpoint | Task | License evidence | Resource evidence | Disposition |
|---|---|---|---|---|
| `stabilityai/sdxl-turbo` | Text-to-image | The reviewed `LICENSE.md` is Stability AI Community License Agreement (2024-07-05): commercial use is conditionally allowed, requires registration, and ends above US$1M annual revenue; distribution has attribution/notice terms. Review the exact checkpoint's license before use. | Apple's memory-constrained SDXL Turbo example uses MLX Swift, not this ComfyUI adapter; no latency or image-quality measurement on this M1. | Candidate for a separate MLX image experiment after checking personal-use terms; not executable through this ComfyUI adapter as-is. |
| `Wan-AI/Wan2.1-T2V-1.3B` | Text-to-video | Upstream Wan2.1 says Apache-2.0; inspect the exact checkpoint repository before use. | Apple MLX example reports ~10 GB RAM for 81 frames unquantized; above this machine's total 8 GB. | Not suitable for this machine absent a measured, legal quantized workflow. |
| `Lightricks/LTX-2.3` | Text/image-to-video | Model card uses LTX-2 Community License Agreement, not an unrestricted OSI license. Review its exact terms for each intended use. | LTX Desktop's local-generation floor is ≥15 GB free RAM on Apple Silicon. | Not suitable for this machine. |

## Cost model

With an already installed local runtime and lawful weights, inference has no per-request API charge. Electricity, disk, model download bandwidth, setup time and any future hardware are separate; no generation was run, so their values are `NOT_MEASURED`. Never present “free software” as zero total cost or claim model weights are commercially unrestricted without reading their exact license.
