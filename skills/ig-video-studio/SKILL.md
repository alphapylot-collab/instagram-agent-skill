---
name: ig-video-studio
description: Use when the user wants to turn an Instagram/Facebook Reel script into a video with Kling AI, Gemini Omni Flash, or a manually exported Google Flow video.
---

# ig-video-studio

Orchestrate **original** vertical 9:16 video production for Instagram and Facebook. Work in ChatGPT or Claude: first generate a storyboard using the existing `ig-reel` skill, then hand the shots to the user's chosen provider.

1. Ask for brand, target audience, exact hook, message, voice, runtime, and provider. Do not invent facts, testimonials, or performance numbers.
2. Separate a 5–15 second video-generation shot from the final multi-shot Reel. Warn that Kling 3.0 clips can be shorter than the target full Reel. Suggest manual or editor-based assembly.
3. Draft a camera-ready prompt: subject, action, first-frame movement, shot/camera, lighting, brand palette, a safe space for captions, and restrictions against deceptive synthetic testimonials.
4. Preview the provider request **without making a billable call**:

   `python3 growth_studio.py video --provider kling --prompt "..." --duration 5 --output kling-task.json`

   or

   `python3 growth_studio.py video --provider gemini --prompt "..." --output reel.mp4`

5. Only after explicit permission for a chargeable video request and confirmation that the user's separate developer API key is configured, add `--execute`. Never read, print, log, or request secrets inside chat.
6. Kling returns an asynchronous task ID in the JSON file. Query it with `python3 growth_studio.py kling-status --task-id ID --execute`, and download finished assets manually from returned secure URLs. Gemini saves an MP4 when the API returns inline video.
7. Google Flow subscription is **not a general API credential**. If the user generates in the Flow UI, export the MP4, then verify with `python3 growth_studio.py flow-import --file exported.mp4`. Do not claim the skill spent Flow credits or automated its UI.
8. Human reviews visuals, music rights, caption accuracy, synthetic-media disclosure requirements, and platform specs before any upload. This skill **never publishes**.

For setup and source links see `GROWTH_STUDIO.md`. Providers may require separate paid API access; no subscriptions or tokens are shared between ChatGPT and Claude.
