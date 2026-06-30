"""Unit tests for app.rca.repos — read-only repo access + path safety."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.rca import repos
from tests.rca_helpers import init_repo, commit, make_settings


class RepoPathSafetyTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.settings = make_settings(self.root)
        init_repo(self.root, "svc", {"a.py": "x = 1\n"})
        commit(self.root / "svc", "init")

    def tearDown(self):
        self._tmp.cleanup()

    def test_valid_repo_resolves(self):
        self.assertTrue(repos.repo_path(self.settings, "svc").is_dir())

    def test_traversal_rejected(self):
        for bad in ["..", "../svc", "svc/../svc", "/etc", "a/b"]:
            with self.assertRaises(repos.RepoAccessError):
                repos.repo_path(self.settings, bad)

    def test_resolve_in_repo_escape_rejected(self):
        # Escapes that leave the repo dir must raise; a path that stays inside
        # (even via ..) is allowed because it resolves back under the repo.
        for escape in ["../other/x.py", "../../etc/passwd", "/etc/passwd"]:
            with self.assertRaises(repos.RepoAccessError):
                repos.resolve_in_repo(self.settings, "svc", escape)
        # sanity: an in-repo path that uses .. but stays inside is fine
        ok = repos.resolve_in_repo(self.settings, "svc", "src/../a.py")
        self.assertTrue(str(ok).endswith("/svc/a.py"))

    def test_list_repos(self):
        self.assertEqual(repos.list_repos(self.settings), ["svc"])


class RepoReadTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.settings = make_settings(self.root)
        body = "\n".join(f"line {i}" for i in range(1, 51)) + "\n"
        self.repo = init_repo(self.root, "svc", {
            "src/app.py": body,
            "src/util.py": "def helper():\n    return TOKEN_VALUE\n",
        })
        self.sha = commit(self.repo, "RFT-101 add helper and lines")

    def tearDown(self):
        self._tmp.cleanup()

    def test_read_file_slice(self):
        out = repos.read_file(self.settings, "svc", "src/app.py", 5, 7)
        self.assertEqual(out["start"], 5)
        self.assertEqual(out["end"], 7)
        self.assertIn("5\tline 5", out["content"])
        self.assertIn("7\tline 7", out["content"])
        self.assertNotIn("line 8", out["content"])

    def test_read_missing_file_raises(self):
        with self.assertRaises(repos.RepoAccessError):
            repos.read_file(self.settings, "svc", "nope.py")

    def test_grep_fixed_string(self):
        hits = repos.grep(self.settings, "svc", "TOKEN_VALUE")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["path"], "src/util.py")
        self.assertEqual(hits[0]["line"], 2)

    def test_grep_regex(self):
        hits = repos.grep(self.settings, "svc", r"def .*\(\):", is_regex=True)
        self.assertTrue(any(h["path"] == "src/util.py" for h in hits))

    def test_head_and_log(self):
        self.assertEqual(repos.head_sha(self.settings, "svc"), self.sha)
        log = repos.git_log(self.settings, "svc", limit=5)
        self.assertEqual(log[0]["sha"], self.sha)
        self.assertIn("RFT-101", log[0]["subject"])

    def test_blame(self):
        blame = repos.git_blame(self.settings, "svc", "src/util.py", 1, 2)
        self.assertEqual(len(blame), 2)
        self.assertEqual(blame[0]["sha"], self.sha)
        self.assertIn("helper", blame[0]["content"])


if __name__ == "__main__":
    unittest.main()
