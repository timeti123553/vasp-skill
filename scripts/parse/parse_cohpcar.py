#!/usr/bin/env python3
"""Parse a LOBSTER COHPCAR.lobster into CSV (energy, average COHP/ICOHP, optional pairs).

Deps: L0 (Python standard library only)

Input : COHPCAR.lobster  (LOBSTER COHP output; energies are already relative to E_F)
Output: <out>/cohp.csv -- energy plus average COHP / ICOHP per spin
        with --pairs: one COHP/ICOHP column pair per bond, when the pair count is known

Usage:
  python parse_cohpcar.py COHPCAR.lobster
  python parse_cohpcar.py COHPCAR.lobster --out results --pairs
  python parse_cohpcar.py --selftest

Exit codes: 0 = parsed; 1 = no numeric data found (not a crash); 2 = bad usage.

Layout: COHPCAR.lobster writes one row per energy point as
  E, [spin 1: avg COHP, avg ICOHP, then COHP/ICOHP per bond], [spin 2: same]
so the column count is 1 + n_spins * 2 * (1 + n_pairs). The header is used when
it names the pair and spin counts; otherwise the spin count is derived from the
column count, and an ambiguous count is reported instead of guessed.
"""

import argparse
import csv
import os
import re
import sys
import tempfile

NUM_RE = re.compile(r"^[-+]?(?:\d+\.?\d*|\.\d+)(?:[EeDd][-+]?\d+)?$")


def is_number(tok):
    return bool(NUM_RE.match(tok))


def to_float(tok):
    return float(tok.replace("D", "E").replace("d", "e"))


def parse_text(text):
    """Return (rows, meta). rows are lists of floats; meta describes the layout."""
    header_pairs = re.search(r"No\.\s*of\s*COHP\s*pairs\s*:\s*(\d+)", text, re.I)
    header_spins = re.search(r"No\.\s*of\s*spins\s*:\s*(\d+)", text, re.I)

    rows = []
    for line in text.splitlines():
        toks = line.split()
        if len(toks) >= 3 and all(is_number(t) for t in toks):
            rows.append([to_float(t) for t in toks])

    if not rows:
        return [], {"n_points": 0, "n_cols": 0, "n_spins": None, "n_pairs": None,
                    "layout": "no numeric data"}

    n_cols = len(rows[0])
    widths = sorted(set(len(r) for r in rows))
    rows = [r for r in rows if len(r) == n_cols]

    n_spins = int(header_spins.group(1)) if header_spins else None
    n_pairs = int(header_pairs.group(1)) if header_pairs else None

    if n_spins is None:
        if (n_cols - 1) % 4 == 0 and n_cols > 3 and (n_pairs is None or (n_cols - 1) // 4 == n_pairs + 1):
            n_spins = 2
        elif (n_cols - 1) % 2 == 0:
            n_spins = 1
        else:
            n_spins = None

    if n_pairs is None and n_spins in (1, 2) and (n_cols - 1) % (2 * n_spins) == 0:
        n_pairs = (n_cols - 1) // (2 * n_spins) - 1

    layout = ("%d spin(s) x (1 + %s pair(s))" % (n_spins, n_pairs)
              if n_spins and n_pairs is not None else "unknown layout")
    meta = {"n_points": len(rows), "n_cols": n_cols, "n_spins": n_spins,
            "n_pairs": n_pairs, "layout": layout, "row_widths_seen": widths}

    icohp_at_ef = None
    if n_spins in (1, 2):
        nearest = min(rows, key=lambda r: abs(r[0]))
        icohp_at_ef = nearest[2]
    meta["icohp_at_ef"] = icohp_at_ef
    meta["energy_range"] = [rows[0][0], rows[-1][0]]
    return rows, meta


def header_and_row(row, n_spins, n_pairs):
    out = {"energy": row[0]}
    idx = 1
    spin_names = ["up", "dn"] if n_spins == 2 else [None]
    for si, sname in enumerate(spin_names):
        suffix = "" if sname is None else "_" + sname
        out["avg_cohp" + suffix] = row[idx]
        out["avg_icohp" + suffix] = row[idx + 1]
        idx += 2
        if n_pairs:
            for pi in range(n_pairs):
                out["pair%02d_cohp%s" % (pi + 1, suffix)] = row[idx]
                out["pair%02d_icohp%s" % (pi + 1, suffix)] = row[idx + 1]
                idx += 2
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description="Parse COHPCAR.lobster into CSV.")
    p.add_argument("cohpcar", nargs="?", default="COHPCAR.lobster",
                   help="path to COHPCAR.lobster (default: ./COHPCAR.lobster)")
    p.add_argument("--out", default=".", help="output directory (created if missing)")
    p.add_argument("--pairs", action="store_true",
                   help="also emit per-bond COHP/ICOHP columns (needs a known pair count)")
    p.add_argument("--selftest", action="store_true", help="run the built-in self test and exit")
    args = p.parse_args(argv)

    if args.selftest:
        return selftest()

    if not os.path.isfile(args.cohpcar):
        print("Error: no such file: %s" % args.cohpcar, file=sys.stderr)
        return 2
    try:
        with open(args.cohpcar, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError as exc:
        print("Error: cannot read %s: %s" % (args.cohpcar, exc), file=sys.stderr)
        return 2

    rows, meta = parse_text(text)
    if not rows:
        print("No COHP data rows found in %s" % args.cohpcar)
        return 1

    os.makedirs(args.out, exist_ok=True)
    csv_path = os.path.join(args.out, "cohp.csv")
    n_spins = meta["n_spins"] or 1
    n_pairs = meta["n_pairs"] if args.pairs else None
    records = [header_and_row(r, n_spins, n_pairs) for r in rows]
    fields = list(records[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for rec in records:
            w.writerow(rec)

    print("layout: %s (%d column(s), %d energy point(s))"
          % (meta["layout"], meta["n_cols"], meta["n_points"]))
    print("energy range: %s .. %s eV" % (meta["energy_range"][0], meta["energy_range"][1]))
    if meta["icohp_at_ef"] is not None:
        print("ICOHP at E_F (nearest energy point): %.6f" % meta["icohp_at_ef"])
    if len(meta["row_widths_seen"]) > 1:
        print("warning: rows with other column counts were skipped: %s" % meta["row_widths_seen"])
    print("wrote: %s" % csv_path)
    return 0


SELFTEST_SAMPLE = """COHPCAR.lobster
No. of COHP pairs: 2
No. of spins: 1
  -5.00000   0.10000  -0.10000   0.05000  -0.05000   0.05000  -0.05000
   0.00000   0.20000  -0.20000   0.10000  -0.10000   0.10000  -0.10000
   5.00000   0.30000  -0.30000   0.15000  -0.15000   0.15000  -0.15000
"""


def selftest():
    rows, meta = parse_text(SELFTEST_SAMPLE)
    checks = [
        ("n_points", meta["n_points"] == 3),
        ("n_cols", meta["n_cols"] == 7),
        ("n_spins", meta["n_spins"] == 1),
        ("n_pairs", meta["n_pairs"] == 2),
        ("icohp_at_ef", meta["icohp_at_ef"] == -0.2),
        ("first energy", rows[0][0] == -5.0),
    ]
    failed = [name for name, ok in checks if not ok]
    if failed:
        print("selftest FAIL: %s" % ", ".join(failed))
        return 1

    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "COHPCAR.lobster")
        with open(src, "w", encoding="utf-8") as f:
            f.write(SELFTEST_SAMPLE)
        rc = main([src, "--out", d, "--pairs"])
        path = os.path.join(d, "cohp.csv")
        if rc != 0 or not os.path.isfile(path):
            print("selftest FAIL: end-to-end run returned %s" % rc)
            return 1
        with open(path, "r", encoding="utf-8") as f:
            head = f.readline().strip()
        if "pair01_cohp" not in head or "pair02_icohp" not in head:
            print("selftest FAIL: per-pair columns missing: %s" % head)
            return 1
    print("selftest OK: 1 spin x (1 + 2 pairs), ICOHP(E_F) = -0.200000")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
