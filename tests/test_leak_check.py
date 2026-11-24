import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(ROOT, "skills", "arch-export", "scripts", "leak_check.py")
FIX = os.path.join(HERE, "fixtures", "leak_check")


def fx(name):
    return os.path.join(FIX, name)


class LeakCheckCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = self._tmp.name

    def write(self, name, text):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        return path

    def run_check(self, draft, tokens="tokens.txt", aliases="aliases.json", extra=()):
        def resolve(value, default_dir):
            if os.path.isabs(value):
                return value
            return os.path.join(default_dir, value)

        cmd = [
            sys.executable,
            SCRIPT,
            "--draft",
            resolve(draft, FIX),
            "--tokens",
            resolve(tokens, FIX),
            "--aliases",
            resolve(aliases, FIX),
        ]
        cmd.extend(extra)
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        out = proc.stdout.strip().splitlines()
        return proc.returncode, out[-1] if out else "", proc.stdout

    def assert_verdict(self, result, code, prefix):
        status, last, full = result
        self.assertEqual((status, last.split(":")[0]), (code, prefix), full)
        return full

    def shape_draft(self, body):
        return self.write("shape.md", "# Brief\n\nThe note says " + body + "\n")


class VerdictTests(LeakCheckCase):
    def test_clean_draft_passes(self):
        self.assert_verdict(self.run_check("clean.md"), 0, "PASS leak-check")

    def test_token_hit_fails_with_lines_and_counts(self):
        out = self.assert_verdict(self.run_check("token_leak.md"), 1, "FAIL leak-check")
        self.assertIn('"quillfox"', out)
        self.assertIn("count 2", out)
        self.assertIn("word-boundary 2", out)
        self.assertIn("lines 3, 4", out)

    def test_noise_line_with_reason_clears_token_hit(self):
        result = self.run_check("substring_noise.md", extra=["--noise", fx("noise_reason.tsv")])
        out = self.assert_verdict(result, 0, "PASS leak-check")
        self.assertIn("noise", out)
        self.assertIn("ordinary word inside maintenance", out)

    def test_same_hit_without_noise_file_fails(self):
        out = self.assert_verdict(self.run_check("substring_noise.md"), 1, "FAIL leak-check")
        self.assertIn('"nan"', out)
        self.assertIn("count 1", out)
        self.assertIn("word-boundary 0", out)

    def test_noise_line_without_reason_does_not_clear(self):
        result = self.run_check("substring_noise.md", extra=["--noise", fx("noise_noreason.tsv")])
        out = self.assert_verdict(result, 1, "FAIL leak-check")
        self.assertIn("empty reason", out)

    def test_alias_value_fails_and_noise_cannot_clear_it(self):
        self.assert_verdict(self.run_check("alias_leak.md"), 1, "FAIL leak-check")
        result = self.run_check("alias_leak.md", extra=["--noise", fx("noise_alias.tsv")])
        out = self.assert_verdict(result, 1, "FAIL leak-check")
        self.assertIn("alias values 1", out)
        self.assertIn("cannot clear", out)

    def test_nested_alias_values_fail(self):
        out = self.assert_verdict(self.run_check("alias_nested_leak.md"), 1, "FAIL leak-check")
        self.assertIn('"Frobnitz"', out)
        self.assertIn('"Gadgetron"', out)

    def test_underscore_keys_are_not_swept(self):
        draft = self.write(
            "notes.md",
            "# Brief\n\nThe words private-scratch-phrase and hidden-note-value appear.\n",
        )
        aliases = self.write(
            "a.json",
            '{"_note": "private-scratch-phrase", "Component C": {"_why": "hidden-note-value"}}',
        )
        self.assert_verdict(self.run_check(draft, aliases=aliases), 0, "PASS leak-check")

    def test_alias_keys_are_never_counted(self):
        draft = self.write("keys.md", "# Brief\n\nThe Component A role and Component B role.\n")
        self.assert_verdict(self.run_check(draft), 0, "PASS leak-check")

    def test_alias_value_match_is_case_insensitive(self):
        draft = self.write("case.md", "# Brief\n\nThe module is WIDGETFORGE.\n")
        self.assert_verdict(self.run_check(draft), 1, "FAIL leak-check")

    def test_own_artifact_hits_fail(self):
        out = self.assert_verdict(self.run_check("artifact_leak.md"), 1, "FAIL leak-check")
        self.assertIn("own artifacts 3", out)
        for name in (".arch/", "brief-api.md", "aliases.json"):
            self.assertIn('"%s"' % name, out)

    def test_custom_alias_filename_is_an_own_artifact(self):
        draft = self.write("custom.md", "# Brief\n\nThe map lives in secretmap.json here.\n")
        aliases = self.write("secretmap.json", '{"Component A": "WidgetForge"}')
        out = self.assert_verdict(self.run_check(draft, aliases=aliases), 1, "FAIL leak-check")
        self.assertIn('"secretmap.json"', out)

    def test_comment_and_blank_token_lines_are_skipped(self):
        tokens = self.write("t.txt", "# quillfox\n\n   \nzzzunused\n")
        draft = self.write("d.md", "# Brief\n\nThe quillfox word is here.\n")
        self.assert_verdict(self.run_check(draft, tokens=tokens), 0, "PASS leak-check")


class ShapeTests(LeakCheckCase):
    def assert_shape_fails(self, body, expected):
        result = self.run_check(self.shape_draft(body))
        out = self.assert_verdict(result, 1, "FAIL leak-check")
        self.assertIn('"%s"' % expected, out)
        self.assertIn("shapes 1", out)

    def test_url(self):
        self.assert_shape_fails("see https://example.test/docs/page?id=7 for it.", "https://example.test/docs/page?id=7")

    def test_posix_path(self):
        self.assert_shape_fails("config at /opt/vendor/conf here.", "/opt/vendor/conf")

    def test_windows_path(self):
        self.assert_shape_fails("config at C:\\Tools\\vendor\\conf here.", "C:\\Tools\\vendor\\conf")

    def test_ipv4(self):
        self.assert_shape_fails("host 10.20.30.40 is busy.", "10.20.30.40")

    def test_hex_prefixed(self):
        self.assert_shape_fails("the magic is 0xDEADBEEF here.", "0xDEADBEEF")

    def test_hex_run(self):
        self.assert_shape_fails("the digest is a1b2c3d4e5f6 here.", "a1b2c3d4e5f6")

    def test_resolution_is_not_hex(self):
        self.assert_verdict(self.run_check(self.shape_draft("a 1920x1080 panel.")), 0, "PASS leak-check")

    def test_prose_slashes_and_plain_numbers_are_not_shapes(self):
        draft = self.shape_draft("read/write and I/O of 16777216 rows, version 1.2.3.")
        self.assert_verdict(self.run_check(draft), 0, "PASS leak-check")

    def test_octets_above_255_are_not_an_address(self):
        self.assert_verdict(self.run_check(self.shape_draft("build 300.1.2.3 ok.")), 0, "PASS leak-check")

    def test_shape_hit_cleared_by_noise_with_reason(self):
        draft = self.shape_draft("host 10.20.30.40 is busy.")
        noise = self.write("n.tsv", "10.20.30.40\tdocumentation example address\n")
        out = self.assert_verdict(self.run_check(draft, extra=["--noise", noise]), 0, "PASS leak-check")
        self.assertIn("documentation example address", out)

    def test_url_is_one_hit_not_url_plus_path(self):
        out = self.assert_verdict(
            self.run_check(self.shape_draft("see https://example.test/a/b/c now.")), 1, "FAIL leak-check"
        )
        self.assertIn("shapes 1", out)


class ErrorTests(LeakCheckCase):
    def test_empty_token_file_is_an_error(self):
        self.assert_verdict(self.run_check("clean.md", tokens="empty_tokens.txt"), 2, "ERROR leak-check")

    def test_comment_only_token_file_is_an_error(self):
        self.assert_verdict(self.run_check("clean.md", tokens="comment_tokens.txt"), 2, "ERROR leak-check")

    def test_draft_without_the_is_an_error(self):
        result = self.run_check("no_the.md")
        out = self.assert_verdict(result, 2, "ERROR leak-check")
        self.assertIn("'the'", out)

    def test_missing_draft_is_an_error(self):
        self.assert_verdict(self.run_check("does-not-exist.md"), 2, "ERROR leak-check")

    def test_missing_token_file_is_an_error(self):
        self.assert_verdict(self.run_check("clean.md", tokens="nope.txt"), 2, "ERROR leak-check")

    def test_missing_alias_file_is_an_error(self):
        self.assert_verdict(self.run_check("clean.md", aliases="nope.json"), 2, "ERROR leak-check")

    def test_invalid_alias_json_is_an_error(self):
        aliases = self.write("bad.json", "{not json")
        self.assert_verdict(self.run_check("clean.md", aliases=aliases), 2, "ERROR leak-check")

    def test_missing_noise_file_is_an_error(self):
        result = self.run_check("clean.md", extra=["--noise", os.path.join(self.tmp, "nope.tsv")])
        self.assert_verdict(result, 2, "ERROR leak-check")

    def test_missing_baseline_file_is_an_error(self):
        result = self.run_check("clean.md", extra=["--baseline", os.path.join(self.tmp, "nope.txt")])
        self.assert_verdict(result, 2, "ERROR leak-check")

    def test_directory_as_draft_is_an_error(self):
        self.assert_verdict(self.run_check(FIX), 2, "ERROR leak-check")

    def test_non_utf8_draft_is_an_error(self):
        path = os.path.join(self.tmp, "latin.md")
        with open(path, "wb") as handle:
            handle.write(b"the caf\xe9\n")
        self.assert_verdict(self.run_check(path), 2, "ERROR leak-check")

    def test_unwritable_hits_out_is_an_error(self):
        result = self.run_check("clean.md", extra=["--hits-out", self.tmp])
        self.assert_verdict(result, 2, "ERROR leak-check")

    def test_missing_required_argument_is_an_error(self):
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--draft", fx("clean.md")], capture_output=True, text=True
        )
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertTrue(proc.stdout.strip().splitlines()[-1].startswith("ERROR leak-check:"))

    def test_unknown_flag_is_an_error(self):
        result = self.run_check("clean.md", extra=["--bogus"])
        self.assert_verdict(result, 2, "ERROR leak-check")


class HitsFileTests(LeakCheckCase):
    def test_hits_out_is_sorted_unique_lowercase(self):
        draft = self.write(
            "h.md",
            "# Brief\n\nThe QuillFox and quillfox and ZORBLAXINDEX at 10.20.30.40 and WidgetForge.\n",
        )
        hits = os.path.join(self.tmp, "hits.txt")
        result = self.run_check(draft, extra=["--hits-out", hits])
        self.assert_verdict(result, 1, "FAIL leak-check")
        with open(hits, encoding="utf-8") as handle:
            lines = handle.read().splitlines()
        self.assertEqual(lines, ["10.20.30.40", "quillfox", "widgetforge", "zorblaxindex"])

    def test_hits_out_written_on_pass_with_noise(self):
        hits = os.path.join(self.tmp, "hits.txt")
        result = self.run_check(
            "substring_noise.md", extra=["--noise", fx("noise_reason.tsv"), "--hits-out", hits]
        )
        self.assert_verdict(result, 0, "PASS leak-check")
        with open(hits, encoding="utf-8") as handle:
            self.assertEqual(handle.read().splitlines(), ["nan"])

    def test_hits_out_not_written_on_error(self):
        hits = os.path.join(self.tmp, "hits.txt")
        self.run_check("clean.md", tokens="empty_tokens.txt", extra=["--hits-out", hits])
        self.assertFalse(os.path.exists(hits))

    def test_baseline_prints_only_new_hits(self):
        old = self.write("old.txt", "quillfox\n")
        draft = self.write("b.md", "# Brief\n\nThe quillfox and zorblaxindex words.\n")
        result = self.run_check(draft, extra=["--baseline", old])
        out = self.assert_verdict(result, 1, "FAIL leak-check")
        self.assertIn('"zorblaxindex"', out.lower())
        self.assertNotIn('"quillfox"', out.lower())
        self.assertIn("1 new since baseline, 1 already in baseline", out)

    def test_baseline_with_every_hit_known_prints_no_hit_lines(self):
        old = self.write("old.txt", "quillfox\n")
        draft = self.write("b.md", "# Brief\n\nThe quillfox word.\n")
        result = self.run_check(draft, extra=["--baseline", old])
        out = self.assert_verdict(result, 1, "FAIL leak-check")
        self.assertNotIn("  HIT", out)
        self.assertIn("0 new since baseline, 1 already in baseline", out)


if __name__ == "__main__":
    unittest.main()
