#!/usr/bin/env python3
"""Summarize a VASP OUTCAR into JSON: key parameters, final energies, forces, warnings.

Deps: L0 (Python standard library only)

Input : OUTCAR
Output: <out>/outcar_summary.json
        <out>/outcar_forces.csv   (only with --forces; last TOTAL-FORCE block)

Usage:
  python parse_outcar.py OUTCAR
  python parse_outcar.py OUTCAR --out results --forces
  python parse_outcar.py --selftest

Exit codes: 0 = parsed; 1 = nothing parseable (not a crash); 2 = bad usage.

This is a fast keyword scan, not a full OUTCAR grammar: it reports only the
facts the skill's diagnosis flow needs. Absent fields are reported as null
instead of being guessed.
"""

import argparse
import json
import os
import re
import sys
import tempfile

NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[EeDd][-+]?\d+)?"

FATAL_HINTS = (
    "VERY BAD NEWS", "LAPACK", "ZPOTRF", "ZHEGV", "Error EDDDAV", "EDDDAV",
    "not enough memory", "PSMAXN", "ZBRENT", "internal error",
    "Sub-Space-Matrix is not hermitian", "DENTET",
)


def to_float(tok):
    if tok is None:
        return None
    try:
        return float(tok.strip().replace("D", "E").replace("d", "e"))
    except ValueError:
        return None


def first(pattern, text, group=1):
    m = re.search(pattern, text)
    return m.group(group) if m else None


def last(pattern, text, group=1):
    hits = re.findall(pattern, text)
    return hits[-1] if hits else None


def parse_force_block(text):
    """Return (rows, max_force, mean_force, drift) from the last TOTAL-FORCE block."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if "TOTAL-FORCE" in line:
            start = i
    if start is None:
        return [], None, None, None

    rows = []
    for line in lines[start + 1:]:
        stripped = line.strip()
        if not stripped:
            continue
        if set(stripped) <= set("- "):
            if rows:
                break
            continue
        toks = stripped.split()
        nums = [to_float(t) for t in toks]
        if len(toks) >= 6 and all(n is not None for n in nums[:6]):
            rows.append({"pos": nums[:3], "force": nums[3:6]})
        elif rows:
            break

    mags = [(r["force"][0] ** 2 + r["force"][1] ** 2 + r["force"][2] ** 2) ** 0.5 for r in rows]
    max_force = max(mags) if mags else None
    mean_force = (sum(mags) / len(mags)) if mags else None
    drift = None
    m = None
    for m in re.finditer(r"total drift:\s*(" + NUM + r")\s+(" + NUM + r")\s+(" + NUM + r")", text):
        pass
    if m:
        drift = [to_float(m.group(1)), to_float(m.group(2)), to_float(m.group(3))]
    return rows, max_force, mean_force, drift


def parse_text(text):
    rows, max_force, mean_force, drift = parse_force_block(text)

    titels = []
    for t in re.findall(r"TITEL\s*=\s*(.+)", text):
        t = t.strip()
        if t and t not in titels:
            titels.append(t)

    warnings = []
    for line in text.splitlines():
        if "WARNING" in line:
            s = line.strip()
            if s not in warnings and len(warnings) < 20:
                warnings.append(s)

    fatal = []
    for line in text.splitlines():
        if any(k in line for k in FATAL_HINTS):
            s = line.strip()
            if s not in fatal and len(fatal) < 10:
                fatal.append(s)

    # The magnetization table's 'tot' row ends with the total moment, e.g.
    #   tot      0.150   0.250   0.350   1.2345
    # so take the last number of the last 'tot' row (not the first).
    mag_total = None
    for m in re.finditer(r"^\s*tot\s+(.+)$", text, re.M):
        nums = [n for n in (to_float(t) for t in m.group(1).split()) if n is not None]
        if nums:
            mag_total = nums[-1]

    summary = {
        "version": first(r"vasp\.(\d+\.\d+\.\d+)", text),
        "prec": first(r"\bPREC\s*=\s*(\w+)", text),
        "encut_ev": to_float(first(r"\bENCUT\s*=\s*(" + NUM + r")", text)),
        "ediff": to_float(first(r"\bEDIFF\s*=\s*(" + NUM + r")", text)),
        "ediffg": to_float(first(r"\bEDIFFG\s*=\s*(" + NUM + r")", text)),
        "ispin": int(first(r"\bISPIN\s*=\s*(\d+)", text)) if first(r"\bISPIN\s*=\s*(\d+)", text) else None,
        "nkpts": int(first(r"\bNKPTS\s*=\s*(\d+)", text)) if first(r"\bNKPTS\s*=\s*(\d+)", text) else None,
        "nbands": int(first(r"\bNBANDS\s*=\s*(\d+)", text)) if first(r"\bNBANDS\s*=\s*(\d+)", text) else None,
        "nions": int(first(r"\bNIONS\s*=\s*(\d+)", text)) if first(r"\bNIONS\s*=\s*(\d+)", text) else None,
        "nelect": to_float(first(r"\bNELECT\s*=\s*(" + NUM + r")", text)),
        "potcar_titels": titels,
        "toten_ev": to_float(last(r"free\s+energy\s+TOTEN\s*=\s*(" + NUM + r")", text)),
        "energy_sigma0_ev": to_float(last(r"energy\(sigma->0\)\s*=\s*(" + NUM + r")", text)),
        "reached_required_accuracy": "reached required accuracy" in text,
        "elapsed_sec": to_float(last(r"Elapsed time \(sec\):\s*(" + NUM + r")", text)),
        "max_force_ev_ang": max_force,
        "mean_force_ev_ang": mean_force,
        "total_drift": drift,
        "total_magnetization": mag_total,
        "n_force_rows": len(rows),
        "warnings": warnings,
        "fatal_hint_lines": fatal,
    }
    return rows, summary


def main(argv=None):
    p = argparse.ArgumentParser(description="Summarize a VASP OUTCAR into JSON.")
    p.add_argument("outcar", nargs="?", default="OUTCAR", help="path to OUTCAR (default: ./OUTCAR)")
    p.add_argument("--out", default=".", help="output directory (created if missing)")
    p.add_argument("--forces", action="store_true", help="also write outcar_forces.csv")
    p.add_argument("--selftest", action="store_true", help="run the built-in self test and exit")
    args = p.parse_args(argv)

    if args.selftest:
        return selftest()

    if not os.path.isfile(args.outcar):
        print("Error: no such file: %s" % args.outcar, file=sys.stderr)
        return 2
    try:
        with open(args.outcar, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError as exc:
        print("Error: cannot read %s: %s" % (args.outcar, exc), file=sys.stderr)
        return 2

    rows, summary = parse_text(text)
    if not any(v not in (None, [], {}) for v in summary.values()):
        print("No OUTCAR facts found in %s" % args.outcar)
        return 1

    os.makedirs(args.out, exist_ok=True)
    json_path = os.path.join(args.out, "outcar_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)

    print("version=%s ENCUT=%s ISPIN=%s NKPTS=%s NBANDS=%s NIONS=%s"
          % (summary["version"], summary["encut_ev"], summary["ispin"],
             summary["nkpts"], summary["nbands"], summary["nions"]))
    print("TOTEN=%s eV  sigma->0=%s eV  accuracy_reached=%s  elapsed=%ss"
          % (summary["toten_ev"], summary["energy_sigma0_ev"],
             summary["reached_required_accuracy"], summary["elapsed_sec"]))
    if summary["max_force_ev_ang"] is not None:
        print("forces: %d row(s), max=%.6f eV/Ang  mean=%.6f eV/Ang"
              % (summary["n_force_rows"], summary["max_force_ev_ang"], summary["mean_force_ev_ang"]))
    if summary["fatal_hint_lines"]:
        print("fatal-looking lines: %d (see JSON)" % len(summary["fatal_hint_lines"]))
    print("wrote: %s" % json_path)

    if args.forces:
        csv_path = os.path.join(args.out, "outcar_forces.csv")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("ion,pos_x,pos_y,pos_z,fx,fy,fz\n")
            for i, r in enumerate(rows, 1):
                f.write("%d,%.8f,%.8f,%.8f,%.6f,%.6f,%.6f\n"
                        % (i, r["pos"][0], r["pos"][1], r["pos"][2],
                           r["force"][0], r["force"][1], r["force"][2]))
        print("wrote: %s" % csv_path)
    return 0


SELFTEST_SAMPLE = """ vasp.6.4.2 10Apr24 (build Aug 20 2025 12:00:00) complex

   ENCUT  =  520.0 eV
   ISPIN  =      2    spin polarized calculation
   NKPTS =      64   k-points in BZ
   NBANDS=     120
   NIONS =       4
   NELECT =      32.0000
   PREC   = Normal
   EDIFF  = 0.100000E-05
   EDIFFG = -.200000E-01

  TITEL  = PAW_PBE Fe 06Sep2000
  TITEL  = PAW_PBE O 08Apr2002

    POSITION                                       TOTAL-FORCE (eV/Angst)
    -----------------------------------------------------------------------------------
     0.0000000000   0.0000000000   0.0000000000      0.100000   0.200000   0.300000
     1.0000000000   1.0000000000   1.0000000000     -0.100000  -0.200000  -0.300000
    -----------------------------------------------------------------------------------
       total drift:                                0.000000    0.000000    0.000000

  FREE ENERGIE OF THE ION-ELECTRON SYSTEM (eV)
  ---------------------------------------------------
  free  energy   TOTEN  =       -45.123456 eV
  energy  without entropy=      -45.123456  energy(sigma->0) =     -45.123456

  magnetization (x)
      # of ion       s       p       d       tot
      ------------------------------------------
         1        0.100   0.200   0.300   0.600
      ------------------------------------------
         tot      0.150   0.250   0.350   1.2345

  General timing and accounting informations for this run:
  --------------------------------------------------------
  Total CPU time used (sec):      100.000
  Elapsed time (sec):             120.000

  WARNING: DENTET: not enough electrons
"""


def selftest():
    rows, s = parse_text(SELFTEST_SAMPLE)
    checks = [
        ("version", s["version"] == "6.4.2"),
        ("encut", s["encut_ev"] == 520.0),
        ("ediff", abs(s["ediff"] - 1e-6) < 1e-12),
        ("ediffg", abs(s["ediffg"] + 0.02) < 1e-12),
        ("ispin", s["ispin"] == 2),
        ("nkpts", s["nkpts"] == 64),
        ("nbands", s["nbands"] == 120),
        ("nions", s["nions"] == 4),
        ("toten", abs(s["toten_ev"] + 45.123456) < 1e-6),
        ("sigma0", abs(s["energy_sigma0_ev"] + 45.123456) < 1e-6),
        ("accuracy flag false", s["reached_required_accuracy"] is False),
        ("elapsed", s["elapsed_sec"] == 120.0),
        ("force rows", s["n_force_rows"] == 2),
        ("max force", abs(s["max_force_ev_ang"] - 0.374165739) < 1e-6),
        ("drift", s["total_drift"] == [0.0, 0.0, 0.0]),
        ("mag total", abs(s["total_magnetization"] - 1.2345) < 1e-9),
        ("titels", "PAW_PBE Fe 06Sep2000" in s["potcar_titels"]),
        ("warning caught", any("DENTET" in w for w in s["warnings"])),
    ]
    failed = [name for name, ok in checks if not ok]
    if failed:
        print("selftest FAIL: %s" % ", ".join(failed))
        return 1
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "OUTCAR")
        with open(src, "w", encoding="utf-8") as f:
            f.write(SELFTEST_SAMPLE)
        rc = main([src, "--out", d, "--forces"])
        if rc != 0 or not os.path.isfile(os.path.join(d, "outcar_summary.json")) \
                or not os.path.isfile(os.path.join(d, "outcar_forces.csv")):
            print("selftest FAIL: end-to-end run returned %s" % rc)
            return 1
    print("selftest OK: 18 checks, JSON + forces CSV written")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
