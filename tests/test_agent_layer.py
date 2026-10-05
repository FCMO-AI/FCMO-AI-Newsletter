from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "contracts" / "fixtures"


class AgentLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="agent-layer-")
        cls.out = Path(cls.temp.name) / "built"
        result = subprocess.run([sys.executable, str(ROOT / "tools/paper/build.py"), "--stories", str(FIXTURES / "stories.v2.json"), "--status", str(FIXTURES / "newsroom-status.fresh.json"), "--out", str(cls.out), "--base", "/FCMO-AI-Newsletter/"], cwd=ROOT, text=True, capture_output=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def clone(self, name):
        target = Path(self.temp.name) / name
        shutil.copytree(self.out, target)
        return target

    def assert_gate_fails(self, root):
        result = subprocess.run([sys.executable, "-m", "tools.gates.agent_layer", str(root)], cwd=ROOT, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("AGENT_LAYER FAIL", result.stderr + result.stdout)

    def test_gate_rejects_story_omitted_from_api_index(self):
        root = self.clone("missing-index")
        index_path = root / "api/v1/index.json"
        index = json.loads(index_path.read_text())
        index["stories"].pop()
        index_path.write_text(json.dumps(index))
        self.assert_gate_fails(root)

    def test_gate_rejects_story_missing_from_llms_full(self):
        root = self.clone("missing-llms")
        path = root / "llms-full.txt"
        story_id = next((root / "api/v1/stories").glob("*.json")).stem
        text = path.read_text().replace(f"`{story_id}`", f"`REMOVED-{story_id}`")
        path.write_text(text)
        self.assert_gate_fails(root)

    def test_gate_rejects_missing_story_markdown_twin(self):
        root = self.clone("missing-markdown")
        story_file = next((root / "api/v1/stories").glob("*.json"))
        record = json.loads(story_file.read_text())
        canonical = record["canonical_url"].replace("https://fcmo-ai.github.io/FCMO-AI-Newsletter/", "")
        route = Path(canonical)
        twin = root / route.parent / (route.name.rstrip("/") + ".md")
        twin.unlink()
        self.assert_gate_fails(root)

    def test_gate_rejects_api_schema_violation(self):
        root = self.clone("bad-schema")
        path = next((root / "api/v1/stories").glob("*.json"))
        record = json.loads(path.read_text())
        record.pop("language")
        path.write_text(json.dumps(record))
        self.assert_gate_fails(root)

    def test_gate_rejects_broken_agent_and_openapi_urls(self):
        for name, file, needle in (("bad-agent-url", "agent.json", "api_index"), ("bad-openapi-url", "api/v1/openapi.json", "servers")):
            with self.subTest(name=name):
                root = self.clone(name)
                path = root / file
                obj = json.loads(path.read_text())
                if needle == "api_index": obj["endpoints"][needle] = obj["base_url"] + "missing.json"
                else: obj["servers"][0]["url"] = obj["servers"][0]["url"] + "missing/"
                path.write_text(json.dumps(obj))
                self.assert_gate_fails(root)

    def test_mcp_tools_work_offline_against_built_fixture(self):
        story = next((self.out / "api/v1/stories").glob("*.json"))
        record = json.loads(story.read_text())
        api_index = json.loads((self.out / "api/v1/index.json").read_text())
        edition_date = api_index["editions"][0].rsplit("/", 1)[-1].removesuffix(".json")
        messages = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "get_story", "arguments": {"id": record["id"]}}},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "search", "arguments": {"query": record["title"].split()[0]}}},
            {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "get_edition", "arguments": {"date": edition_date}}},
            {"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "list_topics", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "latest", "arguments": {"limit": 2}}},
        ]
        result = subprocess.run(["node", str(ROOT / "tools/agent/mcp/server.mjs"), "--base", "https://fixture.invalid/FCMO-AI-Newsletter/", "--root", str(self.out)], input="\n".join(json.dumps(m) for m in messages) + "\n", text=True, capture_output=True, cwd=ROOT, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(rows), len(messages))
        self.assertEqual(rows[0]["result"]["serverInfo"]["name"], "fcmo-ai-newsletter")
        self.assertEqual(rows[2]["result"]["content"][0]["text"] and json.loads(rows[2]["result"]["content"][0]["text"])["id"], record["id"])
        self.assertTrue(json.loads(rows[3]["result"]["content"][0]["text"]))
        self.assertEqual(json.loads(rows[4]["result"]["content"][0]["text"])["id"], edition_date)
        self.assertTrue(json.loads(rows[5]["result"]["content"][0]["text"]))
        self.assertEqual(len(json.loads(rows[6]["result"]["content"][0]["text"])), 2)

    def test_story_page_advertises_markdown_json_and_jsonld(self):
        record = json.loads(next((self.out / "api/v1/stories").glob("*.json")).read_text())
        page = self.out / Path(record["canonical_url"].replace("https://fcmo-ai.github.io/FCMO-AI-Newsletter/", "")) / "index.html"
        html = page.read_text()
        self.assertIn('type="text/markdown"', html)
        self.assertIn('type="application/json"', html)
        self.assertIn('"@type":"NewsArticle"', html)


if __name__ == "__main__":
    unittest.main()
