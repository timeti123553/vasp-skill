#!/usr/bin/env python3
"""Parse a VASP OSZICAR into machine-readable convergence data.

Deps: L0 (Python standard library only)

Input : an OSZICAR file (or any file containing OSZICAR-style blocks)
Output: <out>/oszicar.csv -- one row per electronic / ionic / MD step
        columns: kind,ionic_step,elec_step,algo,E,dE,d_eps,ncg,rms,rms_c,F,E0,dE_ionic,mag,T,S

Usage:
  python parse_oszicar.py OSZICAR
  python parse_oszicar.py OSZICAR --out results --json
  python parse_oszicar.py --selftest

Exit codes: 0 = parsed at least one row; 1 = nothing parseable (not a crash);
            2 = bad usage.

Note: convergence is NOT decided here -- this script only extracts numbers.
`ionic_step` is the ionic (or MD) step the electronic rows belong to.
"""

import argparse
import csv
import json
import os
import re
import sys
import tempfile

NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[EeDd][-+]?\d+)?"
RE_ELEC = re.compile(r"^\s*([A-Za-z][A-Za-z0-9]*)\s*:\s*(\d+)\s+(" + NUM + r")\s+(" + NUM +
                     r")\s+(" + NUM + r")\s+(\d+)\s+(" + NUM + r")(?:\s+(" + NUM + r"))?")
RE_IONIC = re.compile(r"^\s*(\d+)\s+F=\s*(" + NUM + r")\s+E0=\s*(" + NUM +
                      r")\s+d\s*E\s*=\s*(" + NUM + r")(?:\s+mag=\s*(" + NUM + r"))?")
RE_MD = re.compile(r"^\s*(\d+)\s+T=\s*(" + NUM + r")\s+E=\s*(" + NUM +
                   r")\s+F=\s*(" + NUM + r")(?:\s+S=\s*(" + NUM + r"))?")

FIELDS = ["kind", "ionic_step", "elec_step", "algo", "E", "dE", "d_eps", "ncg",
          "rms", "rms_c", "F", "E0", "dE_ionic", "mag", "T", "S"]


def to_float(tok):
    """Parse a Fortran-style number ('-.12345E+02', '1.0D-03') or return None."""
    if tok is None:
        return None
    t = tok.strip().replace("D", "E").replace("d", "e")
    try:
        return float(t)
    except ValueError:
        return None


def blank_row():
    return dict((k, None) for k in FIELDS)


def parse_text(text):
    """Return (rows, summary). Each row is a dict over FIELDS."""
    rows = []
    ionic_step = None
    elec_step = 0

    for line in text.splitlines():
        low = line.lower()
        if "ncg" in low and "rms(c)" in low:      # electronic-step table header
            elec_step = 0
            continue

        m = RE_ELEC.match(line)
        if m:
            elec_step += 1
            r = blank_row()
            r.update(kind="electronic", ionic_step=ionic_step, elec_step=elec_step,
                     algo=m.group(1), E=to_float(m.group(3)), dE=to_float(m.group(4)),
                     d_eps=to_float(m.group(5)), ncg=int(m.group(6)),
                     rms=to_float(m.group(7)), rms_c=to_float(m.group(8)))
            rows.append(r)
            continue

        m = RE_IONIC.match(line)
        if m:
            ionic_step = int(m.group(1))
            elec_step = 0
            r = blank_row()
            r.update(kind="ionic", ionic_step=ionic_step, elec_step=0,
                     F=to_float(m.group(2)), E0=to_float(m.group(3)),
                     dE_ionic=to_float(m.group(4)), mag=to_float(m.group(5)))
            rows.append(r)
            continue

        m = RE_MD.match(line)
        if m:
            ionic_step = int(m.group(1))
            r = blank_row()
            r.update(kind="md", ionic_step=ionic_step, T=to_float(m.group(2)),
                     E=to_float(m.group(3)), F=to_float(m.group(4)), S=to_float(m.group(5)))
            rows.append(r)

    return rows, summarize(rows)


def summarize(rows):
    ionic = [r for r in rows if r["kind"] == "ionic"]
    md = [r for r in rows if r["kind"] == "md"]
    last = (ionic or md or [None])[-1]
    return {
        "n_ionic": len(ionic),
        "n_electronic": len([r for r in rows if r["kind"] == "electronic"]),
        "n_md": len(md),
        "last_step": None if last is None else {
            "kind": last["kind"], "ionic_step": last["ionic_step"],
            "F": last["F"], "E0": last["E0"], "mag": last["mag"], "T": last["T"]},
    }


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main(argv=None):
    p = argparse.ArgumentParser(description="Parse a VASP OSZICAR into CSV/JSON.")
    p.add_argument("oszicar", nargs="?", default="OSZICAR", help="path to OSZICAR (default: ./OSZICAR)")
    p.add_argument("--out", default=".", help="output directory (created if missing)")
    p.add_argument("--json", action="store_true", help="also write oszicar.json with rows + summary")
    p.add_argument("--selftest", action="store_true", help="run the built-in self test and exit")
    args = p.parse_args(argv)

    if args.selftest:
        return selftest()

    if not os.path.isfile(args.oszicar):
        print("Error: no such file: %s" % args.oszicar, file=sys.stderr)
        return 2
    try:
        with open(args.oszicar, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError as exc:
        print("Error: cannot read %s: %s" % (args.oszicar, exc), file=sys.stderr)
        return 2

    rows, summary = parse_text(text)
    if not rows:
        print("No OSZICAR rows found in %s" % args.oszicar)
        return 1

    os.makedirs(args.out, exist_ok=True)
    csv_path = os.path.join(args.out, "oszicar.csv")
    write_csv(csv_path, rows)
    print("parsed %d ionic / %d electronic / %d MD row(s)"
          % (summary["n_ionic"], summary["n_electronic"], summary["n_md"]))
    last = summary["last_step"]
    if last:
        print("last step: %s %s  F=%s E0=%s mag=%s"
              % (last["kind"], last["ionic_step"], last["F"], last["E0"], last["mag"]))
    print("wrote: %s" % csv_path)
    if args.json:
        json_path = os.path.join(args.out, "oszicar.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"summary": summary, "rows": rows}, f, indent=2, sort_keys=True)
        print("wrote: %s" % json_path)
    return 0


SELFTEST_SAMPLE = """       N       E                     dE             d eps       ncg     rms          rms(c)
DAV:   1    -0.451234567890E+02   -0.45123E+02   -0.12345E-03   640   0.123E+00    0.456E-01
DAV:   2    -0.451234567890E+02   -0.10000E-05   -0.10000E-06   600   0.123E-04
   1 F= -.45123456E+02 E0= -.45123456E+02  d E =0.000000E+00
       N       E                     dE             d eps       ncg     rms          rms(c)
DAV:   1    -0.452000000000E+02   -0.45200E+02   -0.12345E-03   640   0.123E+00    0.456E-01
   2 F= -.45200000E+02 E0= -.45200000E+02  d E =-0.76543210E-01 mag=     1.2345
   3 T=  1000. E= -.45200000E+02 F= -.45200000E+02 S=  0.12345E+00
"""


def selftest():
    rows, summary = parse_text(SELFTEST_SAMPLE)
    ionic = [r for r in rows if r["kind"] == "ionic"]
    checks = [
        ("n_ionic == 2", summary["n_ionic"] == 2),
        ("n_electronic == 3", summary["n_electronic"] == 3),
        ("n_md == 1", summary["n_md"] == 1),
        ("ionic[0].F", ionic and abs(ionic[0]["F"] + 45.123456) < 1e-6),
        ("ionic[1].mag", len(ionic) > 1 and abs(ionic[1]["mag"] - 1.2345) < 1e-9),
        ("ionic[1].dE_ionic", len(ionic) > 1 and abs(ionic[1]["dE_ionic"] + 0.07654321) < 1e-9),
        ("elec rows attach to ionic step", all(
            r["ionic_step"] in (None, 1, 2) for r in rows if r["kind"] == "electronic")),
    ]
    failed = [name for name, ok in checks if not ok]
    if failed:
        print("selftest FAIL: %s" % ", ".join(failed))
        return 1
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "OSZICAR")
        with open(src, "w", encoding="utf-8") as f:
            f.write(SELFTEST_SAMPLE)
        rc = main([src, "--out", d, "--json"])
        if rc != 0 or not os.path.isfile(os.path.join(d, "oszicar.csv")):
            print("selftest FAIL: end-to-end run returned %s" % rc)
            return 1
    print("selftest OK: 2 ionic / 3 electronic / 1 MD row, CSV+JSON written")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
