#!/usr/bin/env python3
"""Generate VASP input files (INCAR/KPOINTS/POSCAR, optional POTCAR) from a structure.

Deps: L3 (pymatgen or ase to read the structure). The --selftest core paths
(map.json handling, POSCAR species parsing, POTCAR assembly, overwrite guard)
are L0 and run anywhere; the end-to-end step of --selftest is skipped when no
structure backend is installed.

Usage examples:
  # write into a chosen output directory (legacy behaviour)
  python gen_inputs.py -s POSCAR -w opt
  python gen_inputs.py -s structure.cif -w scf --kdens 3000 --encut 520

  # local POTCAR library selected through map.json, output next to the structure
  #   map.json = {"Si": "Si", "Fe": "Fe_pv", ...}   element -> POTCAR variant dir
  #   A map.json ships with this skill (scripts/map.json) as the built-in default;
  #   a map.json next to --potcar-root (or in its parent) takes precedence over it.
  #   Only an explicit --map <path> is recorded in the INCAR header.
  python gen_inputs.py -s C:/work/Structure/Si.cif -w opt \
         --potcar-root C:/work/PBE --same-dir

  # ... or into an auto-named subdirectory <structure stem>_<workflow> (Si_opt/)
  python gen_inputs.py -s C:/work/Structure/Si.cif -w opt \
         --potcar-root C:/work/PBE --subdir

  # explicit single POTCAR file, or a simple per-element directory
  python gen_inputs.py -s POSCAR -w scf --potcar /path/to/PAW_PBE

Workflows:
  opt   structure relaxation       scf   static self-consistent calc
  band  band structure (k-path)    dos   density of states
  mag   magnetic / spin-polarized  (SCF-like, adds ISPIN/MAGMOM)
  Phonon / ALAMODE displacement jobs are plain scf runs; use -w scf on each
  displaced POSCAR.
  Every INCAR gets ENCUT = 520 by default (one shared value so opt/scf/band agree --
  changing it mid-flow breaks CHGCAR/FFT consistency). Override with --encut,
  omit the tag with --no-encut.

Requires pymatgen (preferred) or ase for reading the structure. If neither is
installed, raise a clear error telling the agent which environment to activate.
"""

import argparse
import json
import os
import re
import shutil
import sys

MAP_FILENAME = "map.json"


def load_structure(path):
    """Return a structure object (pymatgen) or None; fallback to ase."""
    try:
        from pymatgen.core import Structure
        return ("pymatgen", Structure.from_file(path))
    except Exception as exc:  # pymatgen failed to parse this file
        try:
            from ase.io import read as ase_read
            return ("ase", ase_read(path))
        except Exception:
            raise RuntimeError(
                f"Could not read structure '{path}'. Install pymatgen or ase "
                "in the active Python environment (e.g. `conda activate <env>` "
                "then `pip install pymatgen`) and retry. Parsing error: {exc}"
            )


# --- INCAR defaults per workflow ---------------------------------------------

INCAR_DEFAULTS = {
    "opt": {
        "PREC": "Accurate", "EDIFF": "1E-6", "EDIFFG": "-0.02",
        "IBRION": "2", "NSW": "200", "ISIF": "2",
        "ISMEAR": "1", "SIGMA": "0.10", "NELM": "60",
    },
    "scf": {
        "PREC": "Accurate", "EDIFF": "1E-6", "IBRION": "-1", "NSW": "0",
        "ISMEAR": "-5", "LCHARG": ".TRUE.", "LWAVE": ".TRUE.", "NELM": "100",
    },
    "band": {
        "PREC": "Accurate", "EDIFF": "1E-6", "IBRION": "-1", "NSW": "0",
        "ISMEAR": "0", "ICHARG": "11", "LORBIT": "11",
        "LCHARG": ".FALSE.", "LWAVE": ".FALSE.", "NELM": "60",
    },
    "dos": {
        "PREC": "Accurate", "EDIFF": "1E-6", "IBRION": "-1", "NSW": "0",
        "ISMEAR": "-5", "ICHARG": "11", "LORBIT": "11", "NELM": "60",
    },
    "mag": {
        "PREC": "Accurate", "EDIFF": "1E-6", "IBRION": "-1", "NSW": "0",
        "ISMEAR": "-5", "LCHARG": ".TRUE.", "LWAVE": ".TRUE.", "NELM": "120",
        "ISPIN": "2", "AMIX_MAG": "0.05", "BMIX_MAG": "0.0001", "IMIX": "4",
    },
}

KPOINTS_LINEMODE_DIV = 10  # default divisions per high-symmetry segment

# Default plane-wave cutoff written into every INCAR. Kept as ONE global value so
# opt / scf / band / dos / mag all share it: changing ENCUT mid-flow changes the FFT
# grid and breaks CHGCAR/WAVECAR consistency with the previous step
# (see references/errors.md 8.24). Override with --encut, omit with --no-encut.
DEFAULT_ENCUT = 520


def magmom_string(structure, magmom_spec, backend):
    """Build a MAGMOM line (one value per atom) from 'Fe:5,Mn:4' or a bare value."""
    if magmom_spec is None:
        return None
    spec = magmom_spec.strip()
    # bare numeric value (applies to all atoms)
    try:
        val = float(spec)
        return " ".join([f"{val:.2f}"] * len(list(structure)))
    except ValueError:
        pass
    mapping = {}
    for item in spec.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" in item:
            el, v = item.split(":", 1)
            mapping[el.strip()] = float(v.strip())
        else:
            # assume order of species in the structure
            pass
    mags = []
    for atom in list(structure):
        el = str(atom.specie) if backend == "pymatgen" else atom.symbol
        mags.append(mapping.get(el, 0.0))
    return " ".join(f"{m:.2f}" for m in mags)


def make_kpoints(structure, workflow, kdens, backend):
    """Return KPOINTS file content as a string."""
    if workflow == "band":
        from pymatgen.symmetry.bandstructure import HighSymmKpath
        kpath = HighSymmKpath(structure)
        lines = ["Line-mode"]
        lines.append("kpoints along high-symmetry path (auto-generated)")
        lines.append(str(KPOINTS_LINEMODE_DIV))
        lines.append("reciprocal")
        for seg in kpath.kpath["path"]:
            for i in range(len(seg) - 1):
                a, b = kpath.kpath["kpoints"][seg[i]], kpath.kpath["kpoints"][seg[i + 1]]
                if all(abs(ai - bi) < 1e-5 for ai, bi in zip(a, b)):
                    continue  # skip zero-length segments
                lines.append(f"{a[0]:.6f} {a[1]:.6f} {a[2]:.6f}   {b[0]:.6f} {b[1]:.6f} {b[2]:.6f}")
        return "\n".join(lines) + "\n"
    # Automatic gamma-centered Monkhorst-Pack
    from pymatgen.io.vasp import Kpoints
    kp = Kpoints.automatic_density(structure, kdens)
    return "\n".join(["Automatic mesh", "", "0", "Gamma",
                      " ".join(str(int(x)) for x in kp.kpts[0])]) + "\n"


def make_potcar(outdir, elements, potcar):
    """Copy/concatenate POTCAR. Writes POTCAR.placeholder if not provided."""
    if not potcar:
        with open(os.path.join(outdir, "POTCAR.placeholder"), "w") as f:
            f.write(
                "# POTCAR not provided. Link or copy your pseudopotential file here.\n"
                "# It must list elements in POSCAR order: %s\n"
                "# e.g. cat PAW_PBE/%s/POTCAR PAW_PBE/%s/POTCAR > POTCAR\n"
                % (", ".join(elements), elements[0], elements[-1])
            )
        return None
    if os.path.isfile(potcar):
        shutil.copy(potcar, os.path.join(outdir, "POTCAR"))
        return os.path.join(outdir, "POTCAR")
    if os.path.isdir(potcar):
        chunks = []
        for el in elements:
            cands = [
                os.path.join(potcar, el, "POTCAR"),
                os.path.join(potcar, "POTCAR.%s" % el),
                os.path.join(potcar, "%s" % el),
            ]
            src = next((c for c in cands if os.path.isfile(c)), None)
            if src is None:
                raise RuntimeError(
                    "POTCAR for element %s not found under %s" % (el, potcar)
                )
            with open(src, "r") as f:
                chunks.append(f.read())
        with open(os.path.join(outdir, "POTCAR"), "w") as f:
            f.write("".join(chunks))
        return os.path.join(outdir, "POTCAR")
    raise RuntimeError("POTCAR path does not exist: %s" % potcar)


# --- POTCAR library driven by map.json ---------------------------------------

def load_potcar_map(path):
    """Read map.json -> {element: POTCAR variant directory name}."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as exc:
        raise RuntimeError("Could not read POTCAR map '%s': %s" % (path, exc))
    if not isinstance(data, dict) or not data:
        raise RuntimeError(
            "POTCAR map '%s' must be a JSON object such as "
            '{"Si": "Si", "Fe": "Fe_pv"}' % path
        )
    mapping = {}
    for key, val in data.items():
        if isinstance(key, str) and isinstance(val, str) and key.strip() and val.strip():
            mapping[key.strip()] = val.strip()
    if not mapping:
        raise RuntimeError(
            "POTCAR map '%s' has no usable element -> variant entries" % path
        )
    return mapping


def find_potcar_map(potcar_root, explicit=None):
    """Locate map.json: explicit path, else <root>/map.json, <root>/../map.json, script dir."""
    if explicit:
        if not os.path.isfile(explicit):
            raise RuntimeError("--map file does not exist: %s" % explicit)
        return os.path.abspath(explicit)
    root = os.path.abspath(potcar_root)
    candidates = [
        os.path.join(root, MAP_FILENAME),
        os.path.join(os.path.dirname(root), MAP_FILENAME),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), MAP_FILENAME),
    ]
    for cand in candidates:
        if os.path.isfile(cand):
            return cand
    raise RuntimeError(
        "No %s found. Looked in:\n  %s\n"
        'Put map.json next to the POTCAR directory, or pass --map <path>. '
        'Format: {"Si": "Si", "Fe": "Fe_pv"}'
        % (MAP_FILENAME, "\n  ".join(candidates))
    )


def potcar_source_for(element, mapping, potcar_root):
    """Return the POTCAR file path for one element, using the map.json variant."""
    if element not in mapping:
        raise RuntimeError(
            "Element '%s' is not in the POTCAR map -- add an entry such as "
            '"%s": "%s". Elements present in the map: %s'
            % (element, element, element, ", ".join(sorted(mapping)))
        )
    variant = mapping[element]
    src = os.path.join(potcar_root, variant, "POTCAR")
    if os.path.isfile(src):
        return src
    try:
        dirs = sorted(
            d for d in os.listdir(potcar_root)
            if os.path.isfile(os.path.join(potcar_root, d, "POTCAR"))
        )
    except OSError:
        dirs = []
    same_el = [d for d in dirs if d == element or d.startswith(element + "_")]
    hint = ("Variants available for %s: %s" % (element, ", ".join(same_el))
            if same_el else
            "No directory with a POTCAR for '%s' exists under %s" % (element, potcar_root))
    raise RuntimeError(
        "map.json selects '%s' for %s, but %s was not found. %s"
        % (variant, element, src, hint)
    )


_LEXCH_RE = re.compile(r"LEXCH\s*=\s*(\S+)")


def potcar_lexch(path, max_lines=200):
    """Return the LEXCH value of a POTCAR file (first N lines), or None."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for _ in range(max_lines):
                line = f.readline()
                if not line:
                    break
                match = _LEXCH_RE.search(line)
                if match:
                    return match.group(1)
    except OSError:
        return None
    return None


def make_potcar_from_library(outdir, elements, potcar_root, mapping):
    """Concatenate POTCARs picked via map.json, in the given element order.

    Returns (destination path, [(element, variant, source path), ...]).
    Warns on stderr if the chosen potentials do not share one LEXCH value.
    """
    chunks = []
    chosen = []
    lexch = {}
    for el in elements:
        src = potcar_source_for(el, mapping, potcar_root)
        with open(src, "rb") as f:
            chunks.append(f.read())
        chosen.append((el, mapping[el], src))
        lx = potcar_lexch(src)
        if lx:
            lexch.setdefault(lx, []).append(el)
    dst = os.path.join(outdir, "POTCAR")
    with open(dst, "wb") as f:
        f.write(b"".join(chunks))
    if len(lexch) > 1:
        detail = "; ".join(
            "LEXCH=%s -> %s" % (k, ", ".join(v)) for k, v in sorted(lexch.items())
        )
        print(
            "WARNING: the selected POTCARs do not share one LEXCH value (%s). "
            "Mixing GGA and GW potentials silently corrupts the calculation -- "
            "see references/potcar.md before running." % detail,
            file=sys.stderr,
        )
    return dst, chosen


def elements_from_poscar(path):
    """Read the species line of a VASP 5 POSCAR -> ordered element list.

    Returns None for VASP 4 files (no species line) or anything unparseable, so
    callers can fall back to the structure object's own order.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = [f.readline() for _ in range(7)]
    except OSError:
        return None
    if len(lines) < 7:
        return None
    species = lines[5].split()
    counts = lines[6].split()
    if not species or len(species) != len(counts):
        return None
    for token in species:
        if not (1 <= len(token) <= 2 and token.isalpha()):
            return None
    try:
        [int(c) for c in counts]
    except ValueError:
        return None
    return species


def guard_existing(outdir, force=False, skip_poscar=False):
    """Refuse to clobber existing VASP input files unless force is set."""
    names = ["INCAR", "KPOINTS", "POSCAR", "POTCAR"]
    if skip_poscar:
        names = [n for n in names if n != "POSCAR"]
    found = [n for n in names if os.path.isfile(os.path.join(outdir, n))]
    if found and not force:
        raise RuntimeError(
            "Refusing to overwrite existing file(s) in %s: %s\n"
            "Re-run with --force to overwrite, or point --outdir somewhere else."
            % (outdir, ", ".join(found))
        )
    return found


def write_structure(structure, outdir, backend):
    out = os.path.join(outdir, "POSCAR")
    if backend == "pymatgen":
        structure.to(filename=out, fmt="POSCAR")
    else:
        structure.write(out, format="vasp")
    return out


def same_path(a, b):
    """Case-insensitive absolute path comparison (Windows safe)."""
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def subdir_name(structure, workflow, override=None):
    """Directory name for --subdir: explicit override, else '<stem>_<workflow>'.

    Si.cif -> Si_opt (workflow=opt);  POSCAR -> POSCAR_opt.
    """
    if override:
        return override
    stem = os.path.splitext(os.path.basename(structure))[0] or "vasp"
    return "%s_%s" % (stem, workflow)


def main():
    p = argparse.ArgumentParser(description="Generate VASP input files from a structure.")
    p.add_argument("-s", "--structure",
                   help="structure file (POSCAR/CIF/...); may live anywhere on this machine")
    p.add_argument("-w", "--workflow", default="opt",
                   choices=["opt", "scf", "band", "dos", "mag"],
                   help="which calculation workflow to generate (default: opt)")
    p.add_argument("--outdir", default=None,
                   help="output directory (default: current directory; created if missing)")
    p.add_argument("--same-dir", action="store_true",
                   help="write INCAR/KPOINTS/POSCAR/POTCAR next to the structure file")
    p.add_argument("--subdir", nargs="?", const=True, default=None, metavar="NAME",
                   help="write into <structure dir>/<NAME>; NAME defaults to "
                        "<structure stem>_<workflow>, e.g. Si_opt for Si.cif with -w opt")
    p.add_argument("--force", action="store_true",
                   help="overwrite existing INCAR/KPOINTS/POSCAR/POTCAR in the output directory")
    src = p.add_mutually_exclusive_group()
    src.add_argument("--potcar",
                     help="single POTCAR file, or a simple directory of per-element POTCARs")
    src.add_argument("--potcar-root",
                     help="POTCAR library root holding <variant>/POTCAR subdirectories "
                          "(variant per element is read from map.json)")
    p.add_argument("--map", dest="map_path",
                   help="path to map.json. Default is auto-detection: next to "
                        "--potcar-root, then in its parent, then the bundled "
                        "scripts/map.json that ships with this skill. Passing --map "
                        "explicitly is the only case where the path is written into "
                        "the INCAR header.")
    p.add_argument("--kdens", type=float, default=2000,
                   help="k-point density (kppa) for automatic grids (not band)")
    p.add_argument("--encut", type=float, default=DEFAULT_ENCUT,
                   help="ENCUT in eV (default %d, written into every INCAR; "
                        "use --no-encut to omit the tag)" % DEFAULT_ENCUT)
    p.add_argument("--no-encut", action="store_true",
                   help="omit ENCUT entirely -- VASP then uses the POTCAR default ENMAX")
    p.add_argument("--prec", choices=["Accurate", "Normal", "Low", "High"],
                   default="Accurate", help="PREC (default Accurate)")
    p.add_argument("--ispin", type=int, choices=[1, 2], help="ISPIN (default: 2 for mag, else 1)")
    p.add_argument("--magmom", help="e.g. 'Fe:5,Mn:4' or bare '1.0' (one value per atom)")
    p.add_argument("--nbands", type=int, help="optional NBANDS override")
    p.add_argument("--noncollinear", action="store_true", help="add LNONCOLLINEAR for mag")
    p.add_argument("--soc", action="store_true", help="add LSORBIT + SAXIS for mag")
    p.add_argument("--selftest", action="store_true", help="run built-in self test and exit")
    args = p.parse_args()

    if args.selftest:
        sys.exit(selftest())
    if not args.structure:
        p.error("-s/--structure is required")
    if sum([bool(args.same_dir), args.subdir is not None, args.outdir is not None]) > 1:
        p.error("choose only one destination: --outdir, --same-dir or --subdir")
    if not os.path.isfile(args.structure):
        raise RuntimeError("structure file does not exist: %s" % args.structure)
    if args.potcar_root and not os.path.isdir(args.potcar_root):
        raise RuntimeError("--potcar-root is not a directory: %s" % args.potcar_root)

    if args.same_dir:
        outdir = os.path.dirname(os.path.abspath(args.structure))
    elif args.subdir is not None:
        outdir = os.path.join(
            os.path.dirname(os.path.abspath(args.structure)),
            subdir_name(args.structure, args.workflow,
                        args.subdir if isinstance(args.subdir, str) else None),
        )
    else:
        outdir = args.outdir if args.outdir is not None else "."

    mapping = None
    map_used = None
    if args.potcar_root:
        map_used = find_potcar_map(args.potcar_root, args.map_path)
        mapping = load_potcar_map(map_used)
    elif args.map_path:
        raise RuntimeError("--map only applies together with --potcar-root")

    # POSCAR target may be the structure file itself; never clobber the input.
    poscar_out = os.path.join(outdir, "POSCAR")
    skip_poscar = same_path(args.structure, poscar_out)
    guard_existing(outdir, force=args.force, skip_poscar=skip_poscar)
    if skip_poscar:
        print("NOTE: POSCAR target is the structure file itself -- left untouched.")

    backend, structure = load_structure(args.structure)

    # Band structure should run on the primitive cell for a clean k-path.
    band_struct = None
    if args.workflow == "band" and backend == "pymatgen":
        band_struct = structure.get_primitive_structure()

    elements = []
    for atom in list(structure):
        el = str(atom.specie) if backend == "pymatgen" else atom.symbol
        if el not in elements:
            elements.append(el)

    if args.workflow == "mag":
        ispin = args.ispin if args.ispin is not None else 2
    else:
        ispin = args.ispin if args.ispin is not None else 1

    params = dict(INCAR_DEFAULTS[args.workflow])
    params["PREC"] = args.prec
    if not args.no_encut:
        params["ENCUT"] = str(int(args.encut))
    params["ISPIN"] = str(ispin)
    if args.nbands:
        params["NBANDS"] = str(int(args.nbands))
    if args.workflow == "mag":
        mm = magmom_string(structure, args.magmom, backend)
        if mm:
            params["MAGMOM"] = mm
        if args.noncollinear:
            params["LNONCOLLINEAR"] = ".TRUE."
        if args.soc:
            params["LSORBIT"] = ".TRUE."
            params.setdefault("SAXIS", "0 0 1")

    os.makedirs(outdir, exist_ok=True)

    incar_lines = ["# Generated by vasp.skill (workflow=%s)" % args.workflow]
    if band_struct is not None:
        incar_lines.append(
            "# NOTE: band run uses the primitive cell ({} atoms) -- do the matching scf on it too.".format(
                len(list(band_struct))))
    if map_used:
        incar_lines.append("# POTCAR library: %s" % args.potcar_root)
        if args.map_path:
            # Only record the map when the caller overrode the bundled map.json:
            # scripts/map.json ships with this skill and needs no provenance line.
            incar_lines.append("# POTCAR map:     %s" % map_used)
    for k in params:
        incar_lines.append("%s = %s" % (k, params[k]))
    with open(os.path.join(outdir, "INCAR"), "w") as f:
        f.write("\n".join(incar_lines) + "\n")

    k_struct = band_struct if band_struct is not None else structure
    with open(os.path.join(outdir, "KPOINTS"), "w") as f:
        f.write(make_kpoints(k_struct, args.workflow, args.kdens, backend))

    if skip_poscar:
        poscar = poscar_out
    else:
        poscar = write_structure(k_struct, outdir, backend)

    # POTCAR must follow POSCAR order -- read it back from what we just wrote.
    potcar_elements = elements_from_poscar(poscar) or elements

    potcar = None
    chosen = []
    if args.potcar_root:
        potcar, chosen = make_potcar_from_library(outdir, potcar_elements, args.potcar_root, mapping)
    else:
        potcar = make_potcar(outdir, potcar_elements, args.potcar)

    print("Wrote VASP input files in: %s" % os.path.abspath(outdir))
    print("  INCAR   (%s)" % args.workflow)
    print("  KPOINTS")
    if skip_poscar:
        print("  POSCAR  (unchanged -- it is the input structure)")
    else:
        print("  POSCAR  <- %s" % os.path.basename(args.structure))
    if potcar:
        print("  POTCAR  <- %s" % (args.potcar_root or args.potcar))
        if chosen:
            for el, variant, src in chosen:
                print("      %-3s -> %s" % (el, variant))
    else:
        print("  POTCAR.placeholder  (link/copy your POTCAR; elements: %s)"
              % ", ".join(potcar_elements))


def selftest():
    """Self test: L0 core paths always, end-to-end when a reader is installed."""
    import contextlib
    import io
    import tempfile

    root = tempfile.mkdtemp(prefix="gen_inputs_selftest_")
    try:
        lib = os.path.join(root, "PBE")
        for variant, titel, lexch in (("Si", "PAW_PBE Si 05Jan2001", "91"),
                                      ("Fe_pv", "PAW_PBE Fe_pv 06Sep2000", "91")):
            os.makedirs(os.path.join(lib, variant))
            with open(os.path.join(lib, variant, "POTCAR"), "w") as f:
                f.write("TITEL  = %s\n   LEXCH  = %s\n" % (titel, lexch))
        # map.json above the POTCAR root (mirrors PBE/ + map.json side by side)
        with open(os.path.join(root, MAP_FILENAME), "w") as f:
            json.dump({"Si": "Si", "Fe": "Fe_pv"}, f)

        found = find_potcar_map(lib)
        assert same_path(found, os.path.join(root, MAP_FILENAME)), found
        # a map.json inside the root takes precedence
        with open(os.path.join(lib, MAP_FILENAME), "w") as f:
            json.dump({"Si": "Si"}, f)
        assert same_path(find_potcar_map(lib), os.path.join(lib, MAP_FILENAME))
        os.remove(os.path.join(lib, MAP_FILENAME))
        # explicit --map wins
        assert same_path(find_potcar_map(lib, os.path.join(root, MAP_FILENAME)),
                         os.path.join(root, MAP_FILENAME))

        mapping = load_potcar_map(found)
        assert mapping["Fe"] == "Fe_pv", mapping
        assert same_path(potcar_source_for("Si", mapping, lib),
                         os.path.join(lib, "Si", "POTCAR"))
        assert same_path(potcar_source_for("Fe", mapping, lib),
                         os.path.join(lib, "Fe_pv", "POTCAR"))
        for bad, needle in ((("O", mapping, lib), "not in the POTCAR map"),
                            (("Si", {"Si": "Si_sv"}, lib), "Variants available for Si")):
            try:
                potcar_source_for(*bad)
                raise AssertionError("expected RuntimeError for %r" % (bad,))
            except RuntimeError as exc:
                assert needle in str(exc), str(exc)

        # POSCAR species-line parsing: VASP 5 parsed, VASP 4 falls back to None
        def write_poscar(path, species_line):
            with open(path, "w") as fh:
                fh.write("Si8\n1.0\n5.44 0 0\n0 5.44 0\n0 0 5.44\n%s\n8\nDirect\n" % species_line)
                for i in range(8):  # distinct fractional coords, no overlapping sites
                    fh.write("0.%d0 0.00 0.00\n" % i)
        poscar5 = os.path.join(root, "POSCAR")
        write_poscar(poscar5, "Si")
        assert elements_from_poscar(poscar5) == ["Si"], elements_from_poscar(poscar5)
        poscar4 = os.path.join(root, "POSCAR4")
        write_poscar(poscar4, "8")
        assert elements_from_poscar(poscar4) is None

        # POTCAR assembly keeps POSCAR order
        out = os.path.join(root, "out")
        os.makedirs(out)
        dst, chosen = make_potcar_from_library(out, ["Fe", "Si"], lib, mapping)
        blob = open(dst, "rb").read().decode()
        assert blob.index("PAW_PBE Fe_pv") < blob.index("PAW_PBE Si")
        assert [c[0] for c in chosen] == ["Fe", "Si"] and len(chosen) == 2
        assert potcar_lexch(os.path.join(lib, "Si", "POTCAR")) == "91"

        # mixed LEXCH must warn on stderr but still produce a POTCAR
        os.makedirs(os.path.join(lib, "O"))
        with open(os.path.join(lib, "O", "POTCAR"), "w") as f:
            f.write("TITEL  = PAW_PBE O 08Apr2002\n   LEXCH  = 92\n")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            make_potcar_from_library(out, ["Si", "O"], lib, {"Si": "Si", "O": "O"})
        assert "LEXCH" in err.getvalue(), err.getvalue()

        # overwrite guard
        try:
            guard_existing(out)
            raise AssertionError("existing files were not refused")
        except RuntimeError as exc:
            assert "--force" in str(exc)
        guard_existing(out, force=True)
        assert "POSCAR" not in guard_existing(out, force=True, skip_poscar=True)

        # --subdir naming (no structure needed)
        assert subdir_name("C:/x/Si.cif", "opt") == "Si_opt", subdir_name("C:/x/Si.cif", "opt")
        assert subdir_name("C:/x/Structure.cif", "scf") == "Structure_scf"
        assert subdir_name("C:/x/POSCAR", "opt") == "POSCAR_opt"
        assert subdir_name("C:/x/Si.cif", "opt", "mine") == "mine"

        # end-to-end needs pymatgen: automatic KPOINTS meshes use pymatgen only
        try:
            from pymatgen.core import Structure  # noqa: F401
            have_pymatgen = True
        except Exception:
            have_pymatgen = False
        if have_pymatgen:
            e2e = os.path.join(root, "e2e")
            argv = sys.argv
            sys.argv = ["gen_inputs.py", "-s", poscar5, "-w", "scf",
                        "--potcar-root", lib, "--map", found, "--outdir", e2e]
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    main()
            finally:
                sys.argv = argv
            for name in ("INCAR", "KPOINTS", "POSCAR", "POTCAR"):
                assert os.path.isfile(os.path.join(e2e, name)), name
            assert "PAW_PBE Si" in open(os.path.join(e2e, "POTCAR"), "rb").read().decode()
            # ENCUT defaults to 520 and is always written unless --no-encut
            assert "ENCUT = %d" % DEFAULT_ENCUT in open(os.path.join(e2e, "INCAR")).read()
            assert "ENCUT = 400" not in open(os.path.join(e2e, "INCAR")).read()

            def run_incar(tag, extra):
                dest = os.path.join(root, tag)
                argv = sys.argv
                sys.argv = ["gen_inputs.py", "-s", poscar5, "-w", "scf",
                            "--potcar-root", lib, "--map", found, "--outdir", dest] + extra
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        main()
                finally:
                    sys.argv = argv
                return open(os.path.join(dest, "INCAR")).read()

            assert "ENCUT = 400" in run_incar("encut400", ["--encut", "400"])
            assert "ENCUT" not in run_incar("noencut", ["--no-encut"])

            # --same-dir must not clobber a POSCAR that is the input itself
            same = os.path.join(root, "same")
            os.makedirs(same)
            shutil.copy(poscar5, os.path.join(same, "POSCAR"))
            before = open(os.path.join(same, "POSCAR"), "rb").read()
            sys.argv = ["gen_inputs.py", "-s", os.path.join(same, "POSCAR"), "-w", "opt",
                        "--potcar-root", lib, "--map", found, "--same-dir"]
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    main()
            finally:
                sys.argv = argv
            assert open(os.path.join(same, "POSCAR"), "rb").read() == before
            assert os.path.isfile(os.path.join(same, "INCAR"))
            assert os.path.isfile(os.path.join(same, "POTCAR"))

            # --subdir creates <stem>_<workflow>/ and leaves the input in place
            sub = os.path.join(root, "sub")
            os.makedirs(sub)
            shutil.copy(poscar5, os.path.join(sub, "POSCAR"))
            sys.argv = ["gen_inputs.py", "-s", os.path.join(sub, "POSCAR"), "-w", "opt",
                        "--potcar-root", lib, "--map", found, "--subdir"]
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    main()
            finally:
                sys.argv = argv
            made = os.path.join(sub, "POSCAR_opt")
            assert os.path.isdir(made), made
            for name in ("INCAR", "KPOINTS", "POSCAR", "POTCAR"):
                assert os.path.isfile(os.path.join(made, name)), name
            assert os.path.isfile(os.path.join(sub, "POSCAR"))
            assert not os.path.isfile(os.path.join(sub, "INCAR")), "must not write beside it"
        else:
            print("  (pymatgen not available: skipped the end-to-end step)")

        print("selftest OK")
        return 0
    except AssertionError as exc:
        print("selftest FAILED: %s" % exc, file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Error: %s" % exc, file=sys.stderr)
        sys.exit(1)
