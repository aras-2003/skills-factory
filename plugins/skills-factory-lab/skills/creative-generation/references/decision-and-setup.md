# Decision and local setup notes

Snapshot date: 2026-10-28. Recheck vendor docs and exact model licenses before use.

## Decision

- **Higgsfield free tier:** not a dependable free route for this task. The official help page says free access is limited to a small model set and has no credits; the current pricing page marks commercial use unavailable on Free. The website's limited free access does not make the full proprietary image/video catalog free.
- **Higgsfield API/MCP:** excluded by the user's local-only decision. API requests require a prefunded USD balance (official docs state a $5 minimum top-up, pay-per-image/per-second video); MCP generations deduct plan credits and do not use free generations. No paid request was made.
- **`wide-trace/open-higgsfield`:** do not adopt. Its README describes an online studio and a self-hostable UI that requires the user's platform key. Generation runs through remote Higgsfield endpoints; media inputs are uploaded to Vercel Blob as public URLs. The public repository file listing has no root `LICENSE`, and its issue tracker has an open license question. “Open source” in its README is not sufficient license evidence. It is not local inference and does not remove model charges, provider terms, or key risk.
- **Local route:** ComfyUI Desktop is the practical supported starting point for Apple Silicon, but it is only an orchestrator. It does not make model weights free of restrictions, and it does not establish that a chosen workflow fits 8 GB RAM. The local adapter in this candidate accepts only a loopback IP, blocks redirects, and never installs custom nodes or checkpoints.

## Setup and safe first run

1. Install ComfyUI Desktop only from the official Comfy-Org release/documentation links below. Use its official macOS package; do not run shell installers copied from a model page or third-party “one-click” bundle.
2. Start ComfyUI and verify that its API is reachable at `http://127.0.0.1:8188`. Do not expose the unauthenticated API on a LAN or public interface. This adapter intentionally rejects `localhost`, hostnames, HTTPS and non-loopback addresses.
3. Choose one exact checkpoint. Review that checkpoint's model card and full license for the intended personal or commercial use, required notices, and any gating terms. Record the repository revision and license file hash with the run.
4. Obtain an API-format workflow from a trusted source or build it yourself. Review every node class, custom node, model path, URL, file operation, and output destination. Do not install custom nodes for the first run.
5. Before queueing, check free memory, disk space, dimensions, frame count and expected output size. On this 8 GB M1, video is blocked by the verified LTX/Wan resource evidence; image generation remains an unmeasured experiment. Start with the smallest lawful image workflow and stop if macOS reports memory pressure.
6. Run the reviewed JSON with `python3 skills/media/creative-generation/scripts/comfyui_local.py workflow.json --output-dir creative-output --timeout 900`. The workflow must be ComfyUI API prompt format. The adapter writes only returned outputs into the selected new directory; inspect and open each file before delivery.
7. Record model/version/license, workflow hash, elapsed time, peak memory if measurable, output dimensions, failures and review notes. Until an image and a video have each completed and been inspected on supported hardware, report their E2E state as `NOT_RUN`.

## Cost accounting

Local inference has no per-generation API charge once a lawful local runtime and weights are installed. This is not zero total cost. Measure energy as `GPU/system energy (kWh) × the user's electricity rate`; report hardware cost separately as the user's actual purchase price and an explicitly stated useful-life/output assumption. Add one-time storage and download costs if they are billed. No successful run, tariff or hardware budget is available in this task, so cost per 10 images and per video is `NOT_MEASURED`; do not substitute a fabricated number.

## Sources

- [ComfyUI Desktop official repository and install notes](https://github.com/Comfy-Org/desktop)
- [ComfyUI official system requirements](https://github.com/sd-comfyui/docs.comfy.org/blob/main/installation/system_requirements.mdx)
- [Higgsfield plan/free-tier help](https://higgsfield.ai/creator-hub/help-center/plans/how-do-higgsfield-plans-work)
- [Higgsfield current pricing and commercial-use comparison](https://higgsfield.ai/pricing)
- [Higgsfield API billing](https://higgsfield.ai/creator-hub/help-center/integrations/what-is-the-higgsfield-api)
- [Higgsfield MCP/free-generation credit rules](https://higgsfield.ai/creator-hub/help-center/credits/how-credits-work)
- [Higgsfield official-platform identity](https://higgsfield.ai/creator-hub/help-center/getting-started/official-higgsfield-platforms)
- [`wide-trace/open-higgsfield` source and README](https://github.com/wide-trace/open-higgsfield)
- [`wide-trace/open-higgsfield` license question](https://github.com/wide-trace/open-higgsfield/issues/2)
- [Apple MLX Swift Stable Diffusion example](https://github.com/ml-explore/mlx-swift-examples/tree/main/Applications/StableDiffusionExample)
- [Apple MLX Wan2.1 example](https://github.com/ml-explore/mlx-examples/tree/main/video/wan2.1)
- [LTX Desktop requirements](https://github.com/Lightricks/LTX-Desktop/blob/main/README.md)
- [SDXL Turbo exact license, pinned reviewed revision `ef0d007`](https://huggingface.co/stabilityai/sdxl-turbo/blob/ef0d007d296a24f621ab6d376e7055eb6116877b/LICENSE.md)
- [Wan2.1 upstream license and guidance](https://github.com/Wan-Video/Wan2.1)
- [LTX-2.3 checkpoint license](https://huggingface.co/Lightricks/LTX-2.3)
