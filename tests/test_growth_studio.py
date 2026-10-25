import argparse
import base64
import json
import os
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import growth_studio


SAMPLE = {
    "account": "test_brand",
    "platform": "instagram",
    "period_start": "2026-10-01",
    "period_end": "2026-10-11",
    "followers_start": 1000,
    "followers_end": 1100,
    "posts": [
        {"id": "1", "format": "reel", "hook": "truth",
         "views": 1000, "reach": 500, "shares": 15,
         "follows": 10},
        {"id": "2", "format": "reel", "hook": "story",
         "views": 3000, "reach": 1000, "shares": 20,
         "follows": 2},
        {"id": "3", "reach": 0},
    ],
}


class GrowthStudioTests(unittest.TestCase):
    def test_growth_math_and_ranking(self):
        report = growth_studio.analyze(SAMPLE, target=2000, goal_days=100)
        self.assertEqual(report["net_new_followers"], 100)
        self.assertEqual(report["observed_followers_per_day"], 10)
        self.assertEqual(report["required_followers_per_day"], 9)
        self.assertEqual(report["median_views"], 2000)
        self.assertEqual(report["posts_ranked_by_follower_conversion"][0]["id"], "1")
        self.assertIsNone(report["posts_ranked_by_follower_conversion"][-1]["follows_per_reach"])
        self.assertIn("Under 10", report["evidence"])

    def test_missing_not_zero_and_no_division_by_zero(self):
        report = growth_studio.analyze(SAMPLE)
        unknown = next(p for p in report["posts_ranked_by_follower_conversion"]
                       if p["id"] == "3")
        self.assertIsNone(unknown["shares_per_reach"])
        self.assertIsNone(unknown["view_outlier_multiple"])

    def test_validation(self):
        with self.assertRaises(growth_studio.GrowthStudioError):
            growth_studio.analyze({**SAMPLE, "period_end": "2026-09-01"})
        with self.assertRaises(growth_studio.GrowthStudioError):
            growth_studio.analyze({**SAMPLE, "followers_end": -1})
        with self.assertRaises(growth_studio.GrowthStudioError):
            growth_studio.kling_payload("test", duration=16)

    def test_kling_portrait_payload(self):
        payload = growth_studio.kling_payload("Urban garden", 10, "9:16")
        self.assertEqual(payload["settings"]["aspect_ratio"], "9:16")
        self.assertFalse(payload["settings"]["multi_shot"])

    def test_gemini_video_decode(self):
        response = {"steps": [
            {"type": "model_output", "content": [
                {"type": "video", "data": base64.b64encode(b"movie").decode()}
            ]}
        ]}
        self.assertEqual(growth_studio.extract_gemini_video(response), b"movie")
        with self.assertRaises(growth_studio.GrowthStudioError):
            growth_studio.extract_gemini_video({"steps": []})

    def test_dry_run_does_not_call_provider(self):
        args = argparse.Namespace(provider="kling", prompt="A sunrise",
                                  duration=5, aspect="9:16", execute=False,
                                  output="task.json")
        with patch.object(growth_studio, "send_json") as send:
            plan = growth_studio.generate_video(args)
            send.assert_not_called()
        self.assertEqual(plan["mode"], "preview_only")

    def test_paid_call_requires_key(self):
        args = argparse.Namespace(provider="gemini", prompt="A sunrise",
                                  duration=5, aspect="9:16", execute=True,
                                  output="movie.mp4")
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(growth_studio.GrowthStudioError):
                growth_studio.generate_video(args)

    def test_import_flow_mp4(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "flow.mp4"
            path.write_bytes(b"sample media")
            result = growth_studio.flow_import(str(path))
            self.assertEqual(result["size_bytes"], 12)
            self.assertEqual(result["provider"], "flow_manual")


if __name__ == "__main__":
    unittest.main()
