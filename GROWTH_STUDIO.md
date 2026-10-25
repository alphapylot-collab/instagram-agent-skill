# Instagram Growth Studio — cross-client foundation

This is an **early, opt-in extension** of Jake Schincariol's MIT-licensed 13-skill pack. The original scripts, structure, and author credit remain. Contributions in this fork are by AlphaPylot Collab. The growth features do **not** guarantee followers.

## Current implementation (v1.1.0)

| Capability | Status | Notes |
| --- | --- | --- |
| Original 13 Instagram content skills | Preserved | Claude Code compatible; text SKILL.md also reusable in ChatGPT/Codex skill environments |
| Growth planning + performance import | Implemented offline | `ig-growth-loop` and JSON analytics CLI; Instagram and Facebook analyzed separately |
| Kling 3.0 text-to-video | Opt-in API adapter | Portrait 9:16, asynchronous task ID/status, separate `KLING_API_KEY` and provider billing |
| Gemini Omni Flash text-to-video | Opt-in API adapter | Portrait video to MP4 when inline video data is returned; separate `GEMINI_API_KEY` and provider billing |
| Google Flow | Manual bridge | Export a video from Flow UI, then inspect local MP4. No verified transferable Flow subscription/API |
| Meta insights OAuth sync | **Not implemented** | Requires Meta developer application, account authorization, permissions and secure token storage |
| Instagram/Facebook publishing | **Not implemented** | Requires separate IG/FB account integrations and per-post human approval |
| Automated A/B testing and growth dashboard | Planned | Current skill defines hypotheses; CLI computes descriptive metrics only |

## Install & use

**Claude Code:** Use the original `.claude-plugin/marketplace.json` marketplace and plugin as documented in the root README. This fork adds two skills under `skills/`.

**ChatGPT/Codex:** The root `plugin.json` is Agent Plugins 1.0 metadata. Import/install it in a host that supports portable plugins and local skill instructions. Repository presence alone does **not** install the plugin in your ChatGPT account, nor expose your API keys. The Python CLI runs in a user-controlled Python 3.10+ environment.

The CLI has no third-party Python dependency:

```sh
python3 growth_studio.py doctor
python3 growth_studio.py analyze --input examples/performance.example.json
python3 growth_studio.py video --provider kling --prompt "Cinematic 9:16 product shot, instant camera motion" --output kling-task.json
python3 growth_studio.py video --provider gemini --prompt "Portrait macro of a handmade ceramic cup" --output clip.mp4
```

The `video` commands above only **preview requests**, cannot spend credits, and do not call an API. To execute an actual provider call, configure the provider's API credential in your own environment and **explicitly add `--execute`**. The provider may charge. For example:

```sh
python3 growth_studio.py video --provider kling --prompt "A dancer in motion, cinematic portrait" --output task.json --execute
python3 growth_studio.py kling-status --task-id YOUR_TASK_ID --execute
```

Prefer your existing secret manager or shell environment; the command above is schematic. Never commit tokens or paste them into ChatGPT/Claude prompts. For Kling, save finished clips promptly; result URLs can expire. Gemini may return inline video data; this adapter does not implement asynchronous URI delivery.

Google Flow manual export:

```sh
python3 growth_studio.py flow-import --file my-flow-export.mp4
```

## Data model

The input is a JSON object with `account`, `platform` (exactly `instagram` or `facebook`), ISO `period_start`, `period_end`, `followers_start`, `followers_end`, and `posts`. Each post needs an `id`, and may include `format`, `hook`, `views`, `reach`, `shares`, `saves`, `follows`. Unknown metrics remain absent/null; zero views and unknown reach are **not** treated as interchangeable. Individual post follower-conversion requires known reach and follows. Inputs are the account owner's own permitted data or manually exported Meta insights.

No passwords, access tokens, or personal follower data are needed for offline analysis. Do not store tokens in Git, local logs, or video metadata.

## What remains to make this a genuinely connected growth agent

1. **Account onboarding:** Meta OAuth for Instagram professional accounts + Facebook Pages, account/Page linking and granular scopes. Audit tokens, refresh/revocation, encrypted at-rest storage, least privilege and consent.
2. **Analytics adapter:** Pull permitted account/media insights from Meta's Graph APIs, normalize to the same JSON schema and note unavailable metrics/platform-specific definitions.
3. **Publishing workflow:** Upload approved, compliant media for both IG and FB via their separate official flows; validate specs and rights, queue with idempotency, rate-limit awareness, scheduling, retries and human approve/reject.
4. **Creative automation:** Manage multi-shot assembly, captions, safe zones, image-to-video, voice/license options, review previews and provider cost/quotas.
5. **Experiment tracking:** Compare creative variants at equal post age and comparable reach, track cohorts, uncertainty and follower quality; avoid false causal claims.
6. **Dashboard:** Brand-level calendar, weekly creative board, spend caps and cumulative acquisition diagnostics.
7. **Production readiness:** Tenant isolation, audit logs, encryption, key rotation, delivery monitoring, failure replay and security tests.

## Rights and platform compliance

Do not scrape Instagram, buy followers, automate likes/follows or bulk DMs, impersonate people, copy competitor videos, or bypass login/restrictions. AI-generated visuals should not be presented as real testimonials or factual evidence when they are not. Human approval is required before spending money or publishing.

## Primary API references (verify current versions before deployment)

- Kling 3.0 text-to-video: https://kling.ai/document-api/apiReference/model/textToVideo
- Kling auth: https://kling.ai/document-api/api/get-started/authentication
- Gemini Omni Flash: https://ai.google.dev/gemini-api/docs/omni
- Instagram Insights: https://developers.facebook.com/documentation/instagram-platform/insights
- Instagram Content Publishing: https://developers.facebook.com/documentation/instagram-platform/content-publishing
- Facebook Reels Publishing: https://developers.facebook.com/documentation/video-api/guides/reels-publishing.md
