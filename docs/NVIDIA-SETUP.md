# NVIDIA tutor: model decision and setup

Research checked 11 September 2026. No account-specific quota or credential was inspected, and no authenticated provider request was run while preparing this kit.

## 1. Initial recommendation

Use **`nvidia/nemotron-3-super-120b-a12b`** as the first model to evaluate for this demo. NVIDIA currently lists a free prototype endpoint, and its official reference describes chat/RAG capability and configurable reasoning. This is a practical starting selection, not an experimentally proved “best quantum tutor”; evaluate it against the lesson-specific test set before accepting it. [Catalog](https://build.nvidia.com/nvidia/nemotron-3-super-120b-a12b), [model reference](https://docs.api.nvidia.com/nim/reference/nvidia-nemotron-3-super-120b-a12b).

Do not choose a larger model just because it appears in the catalog. A catalog download is not necessarily a free hosted endpoint. Do not automatically switch to a different model when this one fails; the alternative must pass the same tutor checks and be configured explicitly.

## 2. Free access and future production

The hosted API trial is limited to testing/evaluation under NVIDIA's trial terms; those terms distinguish trial access from production subscriptions. Account quotas, access duration, and availability can vary. A model's downloadable license permitting commercial use does not make the hosted trial unrestricted. [NVIDIA trial terms](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf), [NVIDIA access FAQ](https://docs.api.nvidia.com/nim/docs/product).

Therefore: use available trial access for an internal demo, show graceful quota fallback, and choose a suitable hosted subscription/provider or properly licensed self-hosted deployment for the production service. Self-hosting a large model is not free infrastructure. Hosted NVIDIA API usage does not require a GPU on the learner's computer or the web server.

Do not advertise a particular number of free credits or requests/minute without checking the actual account. Track application limits separately from provider limits.

## 3. Key setup

1. Open the model's official catalog page and sign in/create the required NVIDIA developer account.
2. Use Generate/Get API Key and complete any account verification shown there.
3. Put the key in ignored `backend/.env` as `NVIDIA_API_KEY` or in the host's secret settings. Never share it in Claude chat or commit it.
4. Set the model ID and base URL from the official page, then run the backend's explicit provider smoke-test command after Claude implements it.

The official quickstart explains account/key setup. UI labels may change; follow the current official page. [NVIDIA API quickstart](https://docs.api.nvidia.com/nim/docs/api-quickstart).

## 4. Adapter contract

Base URL: `https://integrate.api.nvidia.com/v1`  
Endpoint: `POST /chat/completions` relative to that base.  
Authorization: Bearer key, server-side only.  
Initial model: `nvidia/nemotron-3-super-120b-a12b`.

Use HTTP through httpx and isolate provider-specific fields in one adapter. Send system policy, trusted context envelope, and user request as distinct messages/data. Do not spoof a developer message with learner text.

Begin with documented model sampling settings: temperature 1.0, top_p 0.95. Treat these as model defaults, not a guarantee of factuality. The model reference documents reasoning on/off via the chat template. Check the **hosted endpoint's accepted request syntax** before setting `enable_thinking`; a self-hosted chat-template option is not automatically a supported hosted JSON field. Record the working settings in a provider capability manifest and the smoke-test evidence. [Official model reference](https://docs.api.nvidia.com/nim/reference/nvidia-nemotron-3-super-120b-a12b).

Proposed normal-answer budget: bounded context around 6,000 tokens, up to 1,024 visible answer tokens, and a 45-second total request deadline. If reasoning consumes the completion budget, configure a verified non-thinking mode or separate documented budget rather than silently truncating replies. Do not display private reasoning fields or `<think>` traces; malformed/truncated final output should use a fallback.

Do not assume JSON-schema response mode, tool calling, or streaming works just because another compatible API supports it. Test the actual model endpoint. The application response schema is mandatory even if the provider output requires parsing/repair. One bounded retry is allowed; repeated invalid output falls back to authored help.

## 5. Knowledge is not training

The model does not permanently learn the repository's Markdown when an API key is created. Implement retrieval:

**Approved Markdown → versioned passages → topic/concept filtering → relevant snippets → prompt context → validated cited answer.**

Store factual course knowledge separately from learner memory. Learner memory contains submitted evidence, selected topic/run, conversation scope, and demonstrated misconceptions. It is not a transcript dumped into every prompt and is never a substitute for source material.

The supplied `chapter-1.md` is a starting knowledge file, not the full assessment source and not a promise of zero hallucinations. Expand it using the approved researched lesson material. Never index the full engineering blueprint or answer key into the learner tutor.

## 6. Modes and honest labels

| Mode | Allowed environment | User-facing behavior |
|---|---|---|
| `nvidia` | Development/internal evaluation with configured key; production only with a suitable service arrangement | Real provider answer after validation |
| `authored` | Any environment | Clearly labeled authored course help; no claim of a live AI response |
| `fake` | Automated tests only | Deterministic fixtures; application must reject this mode outside test |

Missing keys must never trigger a fake live response. A configuration diagnostic can indicate key missing/invalid without exposing it. Production configuration must not silently use an internal-evaluation trial mode.

## 7. Live verification required from Claude

Implement an opt-in `uv run --frozen python -m app.tools.tutor_smoke` command. It reads environment locally, calls the real configured model, and prints only model/status/latency plus a non-sensitive sample result. It must not print credentials or private test keys. Ordinary CI does not run this command.

Then run the acceptance document's live tutor question set and record answer quality, citations, scope behavior, failure rate, and latency. A passing mocked test does not establish live model quality. If quota or credentials are unavailable, report **Live NVIDIA verification pending** while completing all independent work.
