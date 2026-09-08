"""
Regression test for the renderMini() bug introduced in PR #1: the function body
was commented out but the call site (inside the main render loop) was left in
place, so every frame calls an undefined function and crashes.

This repo has no JS runtime or build tooling available (no node/npm, no
browser automation), so instead of executing the script, this test statically
checks that every live call to renderMini(...) is backed by a live (i.e. not
commented-out) function definition. That's a static approximation of "does
calling renderMini blow up", cheap enough to run with only python3.

Run: python3 tests/test_render_mini.py
"""
import re
import unittest
from pathlib import Path

INDEX_HTML = Path(__file__).resolve().parent.parent / "index.html"


def extract_inline_script(html: str) -> str:
    match = re.search(r"<script>(.*)</script>", html, re.DOTALL)
    assert match, "expected exactly one inline <script> block in index.html"
    return match.group(1)


def strip_js_comments(js: str) -> str:
    """Drop // line comments and /* */ block comments.

    Good enough for this file: the script contains no '//' inside string
    literals (e.g. no URLs), so a naive per-line strip doesn't false-positive.
    """
    js = re.sub(r"/\*.*?\*/", "", js, flags=re.DOTALL)
    lines = []
    for line in js.split("\n"):
        lines.append(re.sub(r"//.*$", "", line))
    return "\n".join(lines)


class RenderMiniRegressionTest(unittest.TestCase):
    def setUp(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.script = extract_inline_script(html)
        self.live_script = strip_js_comments(self.script)

    def test_render_mini_is_called(self):
        # Sanity check the test itself still applies to this codebase.
        calls = re.findall(r"\brenderMini\s*\(", self.live_script)
        self.assertGreater(
            len(calls), 0,
            "no live call to renderMini() found — if it was removed on "
            "purpose, delete this test too",
        )

    def test_every_render_mini_call_has_a_live_definition(self):
        calls = re.findall(r"\brenderMini\s*\(", self.live_script)
        has_live_definition = bool(
            re.search(r"\bfunction\s+renderMini\s*\(", self.live_script)
            or re.search(r"\bconst\s+renderMini\s*=", self.live_script)
        )
        self.assertTrue(
            has_live_definition,
            f"renderMini() is called {len(calls)} time(s) but has no live "
            "function definition (it may be commented out) — this will "
            "throw a ReferenceError in the render loop at runtime",
        )


if __name__ == "__main__":
    unittest.main()
