import json
import tempfile
from pathlib import Path
import unittest

from labelling.src import openai_batches, tasks
from labelling.src.config import MAPPINGS_DIR


class PromptLoaderTests(unittest.TestCase):
    def test_loads_prompts_from_markdown_directory(self) -> None:
        prompts = openai_batches.load_prompts()
        expected_keys = {
            "classify_direct_driver",
            "classify_region",
            "classify_taxa",
            "classify_study",
            "classify_ecosystem_typology",
            "classify_threats",
        }
        self.assertTrue(expected_keys.issubset(prompts.keys()))
        for key in expected_keys:
            cfg = prompts[key]
            self.assertIsInstance(cfg["system_prompt"], str)
            self.assertGreater(len(cfg["system_prompt"].strip()), 0)
            self.assertIsInstance(cfg.get("structured_output"), dict)

    def test_loads_legacy_json_bundle(self) -> None:
        legacy_path = MAPPINGS_DIR / "prompts_zero.json"
        if not legacy_path.exists():
            self.skipTest("Legacy prompts_zero.json not present")
        prompts = openai_batches.load_prompts(legacy_path)
        self.assertIn("classify_direct_driver", prompts)


class TaskRequestBuilderTests(unittest.TestCase):
    def test_build_requests_for_all_tasks(self) -> None:
        prompts = openai_batches.load_prompts()
        doc = {
            "UT": "UT-TEST-1",
            "title": "Example title",
            "abstract": "Example abstract",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            for task_name in tasks.available_task_names():
                task = tasks.get_task(task_name)
                dest = base / f"{task_name}-requests.jsonl"
                built = task.build_requests_file([doc], dest, prompts=prompts)
                self.assertTrue(built.exists())
                lines = built.read_text(encoding="utf-8").splitlines()
                self.assertGreaterEqual(len(lines), 1)
                payload = json.loads(lines[0])
                self.assertEqual(payload.get("custom_id"), doc["UT"])
                if isinstance(task, tasks.SimpleTask):
                    body = payload.get("body") or {}
                    inputs = body.get("input") or []
                    self.assertGreaterEqual(len(inputs), 1)
                    self.assertEqual(inputs[0].get("content"), prompts[task.prompt_key]["system_prompt"])
                else:
                    self.assertIn("article_text", payload)


if __name__ == "__main__":
    unittest.main()
