#!/usr/bin/env python3
"""Growth Studio: opt-in video generation and evidence-based creator analytics.

Python standard library only. No posting, liking, following or messaging actions.
External video API calls require --execute and may incur provider charges.
"""
from __future__ import annotations

import argparse
import base64
from datetime import date
import json
import os
from pathlib import Path
import statistics
import sys
from urllib import error, parse, request


KLING_ENDPOINT = "https://api-singapore.klingai.com/text-to-video/kling-3.0"
KLING_TASKS = "https://api-singapore.klingai.com/tasks"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
GEMINI_MODEL = "gemini-omni-1.1-flash"


class GrowthStudioError(Exception):
    """An expected user-facing error without credentials in its message."""


def nonnegative(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise GrowthStudioError(f"{name} must be a non-negative number")
    return value


def optional_metric(post, field):
    value = post.get(field)
    return None if value is None else nonnegative(value, field)


def ratio(numerator, denominator):
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return round(numerator / denominator, 6)


def days_between(first, last):
    try:
        elapsed = (date.fromisoformat(last) - date.fromisoformat(first)).days
    except (ValueError, TypeError) as exc:
        raise GrowthStudioError("period_start and period_end must be ISO dates") from exc
    if elapsed < 1:
        raise GrowthStudioError("period_end must follow period_start")
    return elapsed


def analyze(dataset, target=1_000_000, goal_days=730):
    """Analyze the account's own observed numbers; missing metrics stay null."""
    if not isinstance(dataset, dict):
        raise GrowthStudioError("analytics input must be a JSON object")
    required = ("account", "platform", "period_start", "period_end",
                "followers_start", "followers_end", "posts")
    missing = [name for name in required if name not in dataset]
    if missing:
        raise GrowthStudioError("missing fields: " + ", ".join(missing))
    if dataset["platform"] not in ("instagram", "facebook"):
        raise GrowthStudioError("platform must be instagram or facebook")
    if not isinstance(dataset["account"], str) or not dataset["account"].strip():
        raise GrowthStudioError("account must be a nonempty string")
    start = nonnegative(dataset["followers_start"], "followers_start")
    end = nonnegative(dataset["followers_end"], "followers_end")
    if not isinstance(dataset["posts"], list):
        raise GrowthStudioError("posts must be a list")
    nonnegative(target, "target")
    if goal_days < 1:
        raise GrowthStudioError("goal_days must be positive")
    period_days = days_between(dataset["period_start"], dataset["period_end"])
    rows = []
    view_counts = []
    for index, post in enumerate(dataset["posts"]):
        if not isinstance(post, dict) or not post.get("id"):
            raise GrowthStudioError(f"post {index + 1} must have an id")
        views = optional_metric(post, "views")
        reach = optional_metric(post, "reach")
        shares = optional_metric(post, "shares")
        saves = optional_metric(post, "saves")
        follows = optional_metric(post, "follows")
        if views is not None:
            view_counts.append(views)
        rows.append({
            "id": str(post["id"]),
            "format": str(post.get("format", "unknown")),
            "hook": str(post.get("hook", "unknown")),
            "views": views,
            "reach": reach,
            "shares": shares,
            "saves": saves,
            "follows": follows,
            "shares_per_reach": ratio(shares, reach),
            "saves_per_reach": ratio(saves, reach),
            "follows_per_reach": ratio(follows, reach),
        })
    median_views = statistics.median(view_counts) if view_counts else None
    for row in rows:
        row["view_outlier_multiple"] = ratio(row["views"], median_views)
    ranked = sorted(rows, key=lambda row: (
        row["follows_per_reach"] is not None,
        row["follows_per_reach"] if row["follows_per_reach"] is not None else -1,
        row["shares_per_reach"] if row["shares_per_reach"] is not None else -1,
    ), reverse=True)
    net = end - start
    observed_daily = round(net / period_days, 2)
    needed_daily = round(max(target - end, 0) / goal_days, 2)
    can_compare = sum(row["follows_per_reach"] is not None for row in rows) >= 10
    return {
        "account": dataset["account"],
        "platform": dataset["platform"],
        "period_days": period_days,
        "followers_start": start,
        "followers_end": end,
        "net_new_followers": net,
        "observed_followers_per_day": observed_daily,
        "target_followers": target,
        "target_horizon_days": goal_days,
        "required_followers_per_day": needed_daily,
        "daily_gap": round(needed_daily - observed_daily, 2),
        "post_count": len(rows),
        "median_views": median_views,
        "posts_ranked_by_follower_conversion": ranked,
        "evidence": (
            "Enough measured posts for exploratory comparison; correlation is not causation."
            if can_compare else
            "Under 10 posts with both reach and follows: collect more data before pattern claims."
        ),
        "next_action": (
            "Compare creative hypotheses within similar audience and distribution conditions."
            if can_compare else
            "Record reach, follows, shares and hook for the next 10 posts; then reassess."
        ),
    }


def kling_payload(prompt, duration=5, aspect="9:16"):
    if len(prompt) > 3072:
        raise GrowthStudioError("Kling prompt exceeds 3072 characters")
    if duration not in range(3, 16):
        raise GrowthStudioError("Kling 3.0 duration must be 3-15 seconds")
    return {
        "prompt": prompt,
        "settings": {"resolution": "720p", "aspect_ratio": aspect,
                     "duration": duration, "audio": "off", "multi_shot": False},
    }


def gemini_payload(prompt, aspect="9:16"):
    return {
        "model": GEMINI_MODEL,
        "input": prompt,
        "response_format": {"type": "video", "aspect_ratio": aspect},
    }


def send_json(url, payload=None, headers=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = request.Request(
        url, data=data, method="GET" if payload is None else "POST",
        headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        # Never echo URL query keys, authorization headers or response body.
        raise GrowthStudioError(f"provider request failed (HTTP {exc.code})") from exc
    except (error.URLError, TimeoutError, ValueError) as exc:
        raise GrowthStudioError("provider request failed or returned invalid JSON") from exc


def extract_gemini_video(response):
    """Support the REST model_output structure; do not presume a video always exists."""
    for step in response.get("steps", []):
        if step.get("type") == "model_output":
            for content in step.get("content", []):
                if content.get("type") == "video" and content.get("data"):
                    return base64.b64decode(content["data"], validate=True)
    raise GrowthStudioError("Gemini returned no inline video; check model availability and response")


def generate_video(args):
    if not args.prompt.strip():
        raise GrowthStudioError("prompt must be nonempty")
    if args.aspect not in ("9:16", "16:9"):
        raise GrowthStudioError("aspect must be 9:16 or 16:9")
    if args.provider == "kling":
        payload = kling_payload(args.prompt, args.duration, args.aspect)
        endpoint = KLING_ENDPOINT
        key_var = "KLING_API_KEY"
    else:
        payload = gemini_payload(args.prompt, args.aspect)
        endpoint = GEMINI_ENDPOINT
        key_var = "GEMINI_API_KEY"
    if not args.execute:
        return {"mode": "preview_only", "provider": args.provider,
                "endpoint": endpoint, "payload": payload,
                "may_incur_charges_if_executed": True,
                "requires": key_var}
    key = os.getenv(key_var)
    if not key:
        raise GrowthStudioError(f"set {key_var} before executing")
    headers = ({"Authorization": "Bearer " + key} if args.provider == "kling"
               else {"x-goog-api-key": key})
    output = Path(args.output)
    expected_suffix = ".json" if args.provider == "kling" else ".mp4"
    if output.suffix.lower() != expected_suffix:
        raise GrowthStudioError(f"{args.provider} output must use {expected_suffix}")
    if output.exists():
        raise GrowthStudioError("output already exists; choose another filename")
    response = send_json(endpoint, payload, headers)
    if args.provider == "kling":
        if response.get("code") != 0 or not response.get("data", {}).get("id"):
            raise GrowthStudioError("Kling did not return a valid task id")
        if output.suffix.lower() != ".json":
            raise GrowthStudioError("Kling task output must be a .json filename")
        record = {"provider": "kling", "task_id": response["data"]["id"],
                  "status": response["data"].get("status"),
                  "note": "Async task. Check using kling-status; no video is saved yet."}
        output.write_text(json.dumps(record, indent=2), encoding="utf-8")
        return record
    if output.suffix.lower() != ".mp4":
        raise GrowthStudioError("Gemini output must be a .mp4 filename")
    try:
        video = extract_gemini_video(response)
    except (ValueError, KeyError) as exc:
        raise GrowthStudioError("Gemini returned invalid video data") from exc
    if not video:
        raise GrowthStudioError("Gemini returned an empty video")
    output.write_bytes(video)
    return {"provider": "gemini", "video": str(output), "size_bytes": len(video),
            "status": "saved"}


def kling_status(task_id, execute):
    if not task_id or not task_id.isalnum():
        raise GrowthStudioError("task id must be alphanumeric")
    if not execute:
        return {"mode": "preview_only", "provider": "kling", "task_id": task_id,
                "requires": "KLING_API_KEY"}
    key = os.getenv("KLING_API_KEY")
    if not key:
        raise GrowthStudioError("set KLING_API_KEY before querying")
    response = send_json(
        KLING_TASKS + "?" + parse.urlencode({"task_ids": task_id}),
        headers={"Authorization": "Bearer " + key})
    if response.get("code") != 0 or not isinstance(response.get("data"), list):
        raise GrowthStudioError("Kling returned an unexpected task response")
    return {"tasks": [
        {"id": item.get("id"), "status": item.get("status"),
         "outputs": item.get("outputs", []), "message": item.get("message")}
        for item in response["data"] if isinstance(item, dict)
    ]}


def flow_import(file):
    source = Path(file)
    if not source.is_file() or source.suffix.lower() != ".mp4":
        raise GrowthStudioError("Flow export must be an existing .mp4 file")
    return {"provider": "flow_manual", "file": str(source.resolve()),
            "size_bytes": source.stat().st_size,
            "status": "verified_local_export",
            "note": "No Google Flow API or subscription credits were used."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Show available integrations without exposing secrets")
    video = commands.add_parser("video", help="Preview or request paid provider video")
    video.add_argument("--provider", choices=("kling", "gemini"), required=True)
    video.add_argument("--prompt", required=True)
    video.add_argument("--aspect", default="9:16")
    video.add_argument("--duration", type=int, default=5)
    video.add_argument("--output", default="video.mp4")
    video.add_argument("--execute", action="store_true", help="Send provider request; may incur charges")
    status = commands.add_parser("kling-status", help="Query asynchronous Kling task")
    status.add_argument("--task-id", required=True)
    status.add_argument("--execute", action="store_true")
    flow = commands.add_parser("flow-import", help="Verify a manually exported Flow MP4")
    flow.add_argument("--file", required=True)
    audit = commands.add_parser("analyze", help="Summarize observed Instagram/Facebook performance")
    audit.add_argument("--input", required=True)
    audit.add_argument("--target", type=int, default=1_000_000)
    audit.add_argument("--goal-days", type=int, default=730)
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            result = {
                "kling_api_configured": bool(os.getenv("KLING_API_KEY")),
                "gemini_api_configured": bool(os.getenv("GEMINI_API_KEY")),
                "flow": "manual_mp4_export_only",
                "meta": "user_export_import_only; OAuth/publishing not connected",
                "publication": "disabled; human approval required",
            }
        elif args.command == "video":
            result = generate_video(args)
        elif args.command == "kling-status":
            result = kling_status(args.task_id, args.execute)
        elif args.command == "flow-import":
            result = flow_import(args.file)
        else:
            result = analyze(json.loads(Path(args.input).read_text(encoding="utf-8")),
                             args.target, args.goal_days)
    except (GrowthStudioError, OSError, json.JSONDecodeError) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
