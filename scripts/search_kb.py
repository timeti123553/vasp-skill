#!/usr/bin/env python3
"""Search the vasp.skill knowledge base for a keyword and print matching snippets.

Used by the skill's error-diagnosis flow: when an error message isn't directly
matched by errors.md, run this to locate related knowledge across the built-in
catalog (errors.md, workflows.md) and the user's article library (articles/).

Usage:
  python scripts/search_kb.py "<keyword>"                 # case-insensitive substring
  python scripts/search_kb.py "Sub-Space-Matrix"          # example
  python scripts/search_kb.py "RMM-DIIS" --context 3
  python scripts/search_kb.py "AMIX|BMIX" --regex         # regex mode
  python scripts/search_kb.py --selftest                  # self test
  python scripts/search_kb.py "nbj" --file errors.md      # restrict to one file

Search scope: SKILL.md, references/*.md, references/articles/**/*, scripts/*.
Pure stdlib (no pymatgen required), so it runs in any Python.
"""

import argparse
import os
import re
import sys


def skill_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def iter_text_files(root, only_name=None):
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.startswith("."):
                continue
            full = os.path.join(dirpath, fn)
            if only_name and os.path.basename(full) != only_name:
                continue
            if full.lower().endswith((".md", ".txt", ".py", ".log", ".rst")):
                yield full


def highlight(line, pat, n=0):
    """Return line with match wrapped in brackets; fall back to plain line."""
    m = pat.search(line)
    if not m:
        return line
    s, e = m.start(), m.end()
    return "%s[%s]%s" % (line[:s], line[s:e], line[e:])


def main():
    p = argparse.ArgumentParser(description="Search the vasp.skill knowledge base.")
    p.add_argument("query", nargs="?", help="keyword or regex to search for")
    p.add_argument("--context", type=int, default=1,
                   help="lines of context before/after each match (default 1)")
    p.add_argument("--regex", action="store_true", help="treat query as a regex")
    p.add_argument("--file", help="restrict search to a specific file name (e.g. errors.md)")
    p.add_argument("--max", type=int, default=40,
                   help="max matches to print per file (default 40)")
    p.add_argument("--selftest", action="store_true",
                   help="run the built-in self test and exit")
    args = p.parse_args()

    if args.selftest:
        return selftest()
    if args.query is None:
        p.error("a query is required")

    root = skill_root()
    # literal substring by default: metacharacters such as '(', '|' or '\\D'
    # appear in real VASP error strings and must not be treated as regex syntax.
    expr = args.query if args.regex else re.escape(args.query)
    pat = re.compile(expr, re.IGNORECASE)

    results = []  # (relpath, lineno, line)
    for full in iter_text_files(root, only_name=args.file):
        rel = os.path.relpath(full, root).replace("\\", "/")
        try:
            with open(full, "r", encoding="utf-8", errors="replace") as f:
                lines = f.read().splitlines()
        except OSError:
            continue
        count = 0
        for i, line in enumerate(lines):
            if pat.search(line):
                results.append((rel, i + 1, line))
                count += 1
                if count >= args.max:
                    break

    if not results:
        print("No matches for: %s" % args.query)
        sys.exit(1)

    # Group by file
    by_file = {}
    for rel, ln, line in results:
        by_file.setdefault(rel, []).append((ln, line))

    print("Matches for '%s' (in %d file(s)):" % (args.query, len(by_file)))
    for rel in by_file:
        hits = by_file[rel]
        print("\n== %s  (%d hit%s) ==" % (rel, len(hits), "" if len(hits) == 1 else "s"))
        printed = 0
        for ln, line in hits:
            lo = max(1, ln - args.context)
            hi = min(len(_lines(rel, root)), ln + args.context)
            snippet = _lines(rel, root)[lo - 1:hi]
            for j, sl in enumerate(snippet):
                absln = lo + j
                mark = ">>" if absln == ln else "  "
                print("%s%4d  %s" % (mark, absln, highlight(sl, pat)))
            printed += 1
            if printed >= args.max:
                print("... (truncated)")
                break


_cache = {}


def _lines(rel, root):
    if rel not in _cache:
        full = os.path.join(root, rel)
        try:
            with open(full, "r", encoding="utf-8", errors="replace") as f:
                _cache[rel] = f.read().splitlines()
        except OSError:
            _cache[rel] = []
    return _cache[rel]


def selftest():
    checks = [
        ("literal metacharacters match", bool(re.search(re.escape("astype(float)"),
                                                        "df1 = df[1].astype(float)"))),
        ("literal does not match other text", re.search(re.escape("astype(float)"),
                                                        "astypefloat") is None),
        ("pipe is literal by default", re.search(re.escape("AMIX|BMIX"), "AMIX=0.2") is None),
        ("regex mode still available", bool(re.search("AMIX|BMIX", "AMIX=0.2 BMIX=0.0001"))),
        ("backslash-D is literal", bool(re.search(re.escape("LOOP\\D: cpu time"),
                                                  "re.findall(LOOP\\D: cpu time, t)"))),
    ]
    failed = [name for name, ok in checks if not ok]
    if failed:
        print("selftest FAIL: %s" % ", ".join(failed))
        return 1

    # end to end against this skill tree: a token that exists, and one that cannot.
    # main() reads sys.argv itself, so swap it for the duration of each run.
    saved = sys.argv

    def run_once(args):
        sys.argv = ["search_kb.py"] + args
        try:
            main()
            return 0
        except SystemExit as exc:
            return exc.code or 0
        finally:
            sys.argv = saved

    rc_hit = run_once(["RMM-DIIS", "--context", "0"])
    # build the miss probe at run time: a literal would be found in this file itself
    miss = "zzz" + "-definitely-absent-" + "9f3a"
    rc_miss = run_once([miss, "--context", "0"])
    if rc_hit != 0 or rc_miss != 1:
        print("selftest FAIL: end-to-end exit codes hit=%s miss=%s (expected 0 and 1)"
              % (rc_hit, rc_miss))
        return 1
    print("selftest OK: literal-by-default matching, --regex available, exit codes correct")
    return 0


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Error: %s" % exc, file=sys.stderr)
        sys.exit(1)
