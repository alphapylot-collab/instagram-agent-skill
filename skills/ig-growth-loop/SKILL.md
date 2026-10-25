---
name: ig-growth-loop
description: Use when the user wants a measurable Instagram and Facebook growth strategy, weekly experiments, audience conversion analysis, or a path from a small audience toward one million followers.
---

# ig-growth-loop

Use this skill in either ChatGPT or Claude. It coordinates existing `ig-profile`, `ig-viral`, `ig-reel`, `ig-plan`, `ig-human`, and `ig-audit`, plus the new video CLI. Preserve the original skills and their "nothing is posted until yes" safeguard.

## Growth operating cycle

1. **Baseline:** Ask whose Instagram and Facebook accounts these are, their real current follower counts, target audience/location/language, niche, budget, conversion event, content rights, and weekly production capacity. Never assume a connection exists.
2. **Review:** Obtain consented Meta Insights exports or user-provided metrics, never scrape non-public profiles or simulate engagement. Normalize each platform separately using `examples/performance.example.json`; unknown fields must be null/omitted.
3. **Measure:** Run `python3 growth_studio.py analyze --input metrics.json --target 1000000 --goal-days 730`. Compare net follower growth, follower conversion per reach, saves/reach, shares/reach and outliers. Never imply a causal conclusion from a few posts.
4. **Hypothesize:** Select at most two creative variables per week (hook formula, first-frame visual, length, angle, CTA). Identify a measurable primary outcome (follows per reach) and guardrail (retention or negative feedback). Pre-register what success would mean.
5. **Create:** Produce 3–5 differentiated drafts using `ig-reel`, `ig-caption`, `ig-human`, and optionally `ig-video-studio`. Check accessibility, origin/rights, authenticity, local advertising laws, Meta branded-content policies, and disclosure if AI-generated.
6. **Review:** Show every draft, spend estimate and distribution plan to the owner. Wait for explicit approval. No scheduled/post/publish action is bundled into this foundation.
7. **Learn:** Re-import observed results at consistent elapsed post age; compare like with like. Save only user-approved lessons for the next cycle. Report sample size and uncertainty.
8. **Scale:** Only scale sustainable themes that attract authentic, relevant followers. Avoid purchased followers, follow/unfollow, mass DMs, engagement pods and platform scraping.

## Outcome

Report: baseline, posts measured, measured conversion rates, weekly net followers, best/worst evidence, two next hypotheses, production calendar, costs requiring approval, and honest confidence.

Going from 1,000 to 1,000,000 net followers requires 999,000 additional followers. A 730-day linear target averages about 1,368 per day; this is a planning benchmark, **not a forecast or promise**. Use observed growth data and adapt the horizon. Keep Instagram and Facebook separated in analytics rather than adding unlike metrics.
