#!/usr/bin/env python3
"""Leak check for an arch-export brief.

python leak_check.py --draft brief.md --tokens tokens.txt --aliases aliases.json
                     [--noise noise.tsv] [--hits-out hits.txt] [--baseline old-hits.txt]

The last stdout line is the verdict. PASS exits 0, FAIL exits 1, ERROR exits 2.
"""
import argparse
import bisect
import json
import os
import re
import sys

NAME = "leak-check"
MAX_LINES_SHOWN = 25

_URL_CHARS = r"[^\s<>\"'`()\[\]{}|*?]"
_PATH_SEG = r"[\w.@+~-]"

URL_RE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z][A-Za-z0-9+.\-]*://[^\s<>\"'`()\[\]{}|]+")
WIN_DRIVE_RE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]" + _URL_CHARS + r"+")
WIN_ROOTED_RE = re.compile(r"(?<![\w\\])\\{1,2}[\w.$-]+(?:\\[\w.$@~-]+)+")
WIN_RELATIVE_RE = re.compile(r"(?<![\w\\])[\w.$-]+(?:\\[\w.$@~-]+){2,}")
POSIX_ABS_RE = re.compile(r"(?<![\w/.:~\\-])/" + _PATH_SEG + r"+(?:/" + _PATH_SEG + r"*)*")
POSIX_DOT_RE = re.compile(r"(?<![\w/.\\-])(?:~|\.\.?)/" + _PATH_SEG + r"+(?:/" + _PATH_SEG + r"*)*")
POSIX_DEEP_RE = re.compile(r"(?<![\w/.\\-])[\w@+-][\w.@+-]*(?:/" + _PATH_SEG + r"+){2,}")
POSIX_FILE_RE = re.compile(
    r"(?<![\w/.\\-])[\w@+-][\w.@+-]*/[\w@+-]+\.[A-Za-z0-9]{1,5}(?![\w/])"
)
IPV4_RE = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d]|\.\d)")
HEX_PREFIX_RE = re.compile(r"(?<![0-9A-Za-z_])0[xX][0-9A-Fa-f]+(?![0-9A-Za-z_])")
HEX_RUN_RE = re.compile(r"(?<![0-9A-Za-z_])[0-9A-Fa-f]{8,}(?![0-9A-Za-z_])")

SHAPES = (
    ("url", URL_RE),
    ("path", WIN_DRIVE_RE),
    ("path", WIN_ROOTED_RE),
    ("path", WIN_RELATIVE_RE),
    ("path", POSIX_DOT_RE),
    ("path", POSIX_ABS_RE),
    ("path", POSIX_DEEP_RE),
    ("path", POSIX_FILE_RE),
    ("ipv4", IPV4_RE),
    ("hex", HEX_PREFIX_RE),
    ("hex", HEX_RUN_RE),
)
TRAILING_PUNCT = ".,;:!?"

THE_RE = re.compile(r"(?<!\w)the(?!\w)", re.IGNORECASE)
ARTIFACT_PATTERNS = (
    re.compile(r"\.arch[/\\]", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9])brief[\w.-]*\.md(?![\w])", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9])aliases[\w.-]*\.json(?![\w])", re.IGNORECASE),
)


class CheckError(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise CheckError("bad arguments: " + message)


def norm(text):
    return " ".join(text.lower().split())


def read_text(path, what):
    try:
        with open(path, "r", encoding="utf-8-sig") as handle:
            return handle.read()
    except UnicodeDecodeError:
        raise CheckError("%s file is not valid UTF-8: %s" % (what, path))
    except OSError as exc:
        raise CheckError("cannot read %s file %s (%s)" % (what, path, exc.strerror or exc))


def significant_lines(text):
    for number, line in enumerate(text.split("\n"), 1):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            yield number, line.rstrip("\r")


def load_tokens(path):
    seen = {}
    for _, line in significant_lines(read_text(path, "token")):
        token = line.strip()
        seen.setdefault(token.lower(), token)
    return list(seen.values())


def load_noise(path):
    reasons = {}
    ignored = []
    for number, line in significant_lines(read_text(path, "noise")):
        hit, _, reason = line.partition("\t")
        hit, reason = hit.strip(), reason.strip()
        if not hit:
            ignored.append("noise line %d has no hit text" % number)
        elif not reason:
            ignored.append("noise line %d ignored, empty reason: %s" % (number, hit))
        else:
            reasons[norm(hit)] = reason
    return reasons, ignored


def alias_values(node, out):
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, list):
        for item in node:
            alias_values(item, out)
    elif isinstance(node, dict):
        for key, value in node.items():
            if isinstance(key, str) and key.startswith("_"):
                continue
            alias_values(value, out)


def load_alias_values(path):
    try:
        data = json.loads(read_text(path, "alias map"))
    except ValueError as exc:
        raise CheckError("alias map is not valid JSON: %s (%s)" % (path, exc))
    values = []
    alias_values(data, values)
    seen = {}
    for value in values:
        value = value.strip()
        if value:
            seen.setdefault(value.lower(), value)
    return list(seen.values())


class Draft:
    def __init__(self, text):
        self.text = text
        self.lines = text.split("\n")
        self.starts = []
        offset = 0
        for line in self.lines:
            self.starts.append(offset)
            offset += len(line) + 1

    def line_of(self, offset):
        return bisect.bisect_right(self.starts, offset)


class Hit:
    def __init__(self, text, kind):
        self.text = text
        self.kind = kind
        self.count = 0
        self.word = None
        self.lines = []

    def add_line(self, number):
        self.count += 1
        if number not in self.lines:
            self.lines.append(number)


def sweep_literals(draft, literals, kind):
    hits = {}
    for literal in literals:
        escaped = re.escape(literal)
        matches = list(re.finditer(escaped, draft.text, re.IGNORECASE))
        if not matches:
            continue
        hit = Hit(literal, kind)
        for match in matches:
            hit.add_line(draft.line_of(match.start()))
        hit.word = len(re.findall(r"(?<!\w)" + escaped + r"(?!\w)", draft.text, re.IGNORECASE))
        hits[norm(literal)] = hit
    return hits


def valid_ipv4(text):
    return all(int(part) <= 255 for part in text.split("."))


def sweep_shapes(draft):
    hits = {}
    for number, line in enumerate(draft.lines, 1):
        work = line
        for kind, regex in SHAPES:
            for match in list(regex.finditer(work)):
                text = match.group(0).rstrip(TRAILING_PUNCT)
                if kind == "ipv4" and not valid_ipv4(text):
                    continue
                if kind == "hex" and not text.lower().startswith("0x"):
                    if not re.search(r"[A-Fa-f]", text):
                        continue
                if not text:
                    continue
                key = norm(text)
                hit = hits.get(key)
                if hit is None:
                    hit = hits[key] = Hit(text, kind)
                hit.add_line(number)
                span = match.span()
                work = work[: span[0]] + " " * (span[1] - span[0]) + work[span[1]:]
    return hits


def sweep_artifacts(draft, aliases_path):
    hits = {}
    patterns = list(ARTIFACT_PATTERNS)
    name = os.path.basename(aliases_path)
    if name:
        patterns.append(re.compile(re.escape(name), re.IGNORECASE))
    for number, line in enumerate(draft.lines, 1):
        for regex in patterns:
            for match in regex.finditer(line):
                key = norm(match.group(0))
                hit = hits.get(key)
                if hit is None:
                    hit = hits[key] = Hit(match.group(0), "artifact")
                hit.add_line(number)
    return hits


def fmt_lines(lines):
    shown = ", ".join(str(n) for n in lines[:MAX_LINES_SHOWN])
    extra = len(lines) - MAX_LINES_SHOWN
    return shown + (" (+%d more)" % extra if extra > 0 else "")


def describe(hit):
    parts = ['"%s"' % hit.text, "count %d" % hit.count]
    if hit.word is not None:
        parts.append("word-boundary %d" % hit.word)
    parts.append("lines %s" % fmt_lines(hit.lines))
    if hit.kind not in ("token", "alias", "artifact"):
        parts.insert(0, hit.kind)
    return "  ".join(parts)


def run(args):
    out = []

    tokens = load_tokens(args.tokens)
    if not tokens:
        raise CheckError("token file has no tokens: %s" % args.tokens)
    draft = Draft(read_text(args.draft, "draft"))
    values = load_alias_values(args.aliases)
    noise, noise_ignored = ({}, [])
    if args.noise:
        noise, noise_ignored = load_noise(args.noise)
    baseline = None
    if args.baseline:
        baseline = set()
        for _, line in significant_lines(read_text(args.baseline, "baseline")):
            baseline.add(norm(line))
    if not THE_RE.search(draft.text):
        raise CheckError("control failed, the word 'the' is absent from the draft: %s" % args.draft)

    out.append(
        "control ok: %d tokens, %d alias values, %d draft lines" % (len(tokens), len(values), len(draft.lines))
    )
    for message in noise_ignored:
        out.append("warning: " + message)

    passes = (
        ("tokens", sweep_literals(draft, tokens, "token"), True),
        ("shapes", sweep_shapes(draft), True),
        ("alias values", sweep_literals(draft, values, "alias"), False),
        ("own artifacts", sweep_artifacts(draft, args.aliases), False),
    )

    all_keys = set()
    unresolved = {}
    new_unresolved = 0
    noise_count = 0
    known_unresolved = 0
    for name, hits, clearable in passes:
        out.append("")
        out.append("== %s: %d unique hits ==" % (name, len(hits)))
        for key in sorted(hits):
            hit = hits[key]
            all_keys.add(key)
            is_new = baseline is None or key not in baseline
            cleared = clearable and key in noise
            if cleared:
                noise_count += 1
            else:
                unresolved[name] = unresolved.get(name, 0) + 1
                if is_new:
                    new_unresolved += 1
                else:
                    known_unresolved += 1
            if not is_new:
                continue
            if cleared:
                out.append("  noise  " + describe(hit) + "  reason: " + noise[key])
            else:
                note = ""
                if not clearable and key in noise:
                    note = "  (noise entry cannot clear this pass)"
                out.append("  HIT  " + describe(hit) + note)
        if baseline is not None and any(
            key in baseline for key in hits
        ):
            out.append("  (hits already in the baseline are not shown)")

    if args.hits_out:
        try:
            with open(args.hits_out, "w", encoding="utf-8", newline="\n") as handle:
                handle.write("".join(key + "\n" for key in sorted(all_keys)))
        except OSError as exc:
            raise CheckError("cannot write hits file %s (%s)" % (args.hits_out, exc.strerror or exc))

    out.append("")
    total = sum(unresolved.values())
    if total:
        breakdown = ", ".join("%s %d" % (name, unresolved[name]) for name in sorted(unresolved))
        verdict = "FAIL %s: %d unresolved hits (%s), %d noise" % (NAME, total, breakdown, noise_count)
        if baseline is not None:
            verdict += ", %d new since baseline, %d already in baseline" % (new_unresolved, known_unresolved)
        out.append(verdict)
        return out, 1
    out.append("PASS %s: no unresolved hits, %d noise" % (NAME, noise_count))
    return out, 0


def main(argv=None):
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        parser = Parser(description=__doc__, allow_abbrev=False)
        parser.add_argument("--draft", required=True)
        parser.add_argument("--tokens", required=True)
        parser.add_argument("--aliases", required=True)
        parser.add_argument("--noise")
        parser.add_argument("--hits-out", dest="hits_out")
        parser.add_argument("--baseline")
        args = parser.parse_args(argv)
        lines, code = run(args)
    except CheckError as exc:
        print("ERROR %s: %s" % (NAME, exc))
        return 2
    except Exception as exc:  # a crash must read as ERROR, never as a pass
        print("ERROR %s: unexpected %s: %s" % (NAME, type(exc).__name__, exc))
        return 2
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main())
