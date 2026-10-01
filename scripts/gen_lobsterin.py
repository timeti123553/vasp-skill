#!/usr/bin/env python3
"""Generate a LOBSTER input file (lobsterin) for COHP / COOP bonding analysis.

Consolidates the two helper scripts from the VASP+LOBSTER COHP article
(zhihu.com/p/668003243): list bond distances (get_bond_total) and write
lobsterin (get_cohpfile) — using the recommended "by element + bond length"
(cohpGenerator) approach instead of explicit per-atom pairs.

Usage:
  python scripts/gen_lobsterin.py -e -20 10 -s Ga As \\
      -z "Ga:4s,4p,4d" "As:4s,4p,4d" -d 2.483 2.485 -m 5
  python scripts/gen_lobsterin.py --list-bonds            # print bond-distance pairs
  python scripts/gen_lobsterin.py -e -20 10 -s Fe O -z "Fe:4s,4p,4d,5s" "O:2s,2p" -d 1.8 2.2 -m 0 --smearing 0.05

-m 5: tetrahedron smearing (assumes INCAR ISMEAR=-5) — no gaussianSmearingWidth.
-m 0: Gaussian smearing (INCAR ISMEAR=0/1) — writes gaussianSmearingWidth.

Requires pymatgen (Structure.from_file on POSCAR). Symlinks VASP files into the
output dir by default so lobster can run there.
"""

import argparse
import itertools
import os
import sys


def load_structure(struct_path):
    try:
        from pymatgen.core import Structure
    except ImportError:
        raise RuntimeError("This script needs pymatgen. Activate an env with it, "
                           "e.g. `conda activate <env>` then `pip install pymatgen`.")
    return Structure.from_file(struct_path)


def list_bonds(struct_path):
    """Print all pairwise distances grouped by rounded distance (get_bond_total)."""
    from collections import defaultdict
    import numpy as np
    struct = load_structure(struct_path)
    sites = list(struct.sites)
    idxs = [i + 1 for i in range(len(sites))]
    pairs = list(itertools.combinations(sites, 2))
    idx_pairs = list(itertools.combinations(idxs, 2))
    dist_map = defaultdict(list)
    for (a, b), (ia, ib) in zip(pairs, idx_pairs):
        d = struct.lattice.get_all_distances(a.frac_coords, b.frac_coords)[0][0]
        name = "%s%d-%s%d" % (str(a.specie), ia, str(b.specie), ib)
        dist_map[round(d, 3)].append(name)
    print("Note: --------------------")
    for i, s in enumerate(sites, 1):
        print("%-8d %-8s" % (i, s.specie))
    print("Note: --------------------")
    for d in sorted(dist_map):
        print("distance = %s, Number=%d" % (d, len(dist_map[d])))
        print("    " + "   ".join(dist_map[d]))
    return dist_map


def write_lobsterin(outdir, mode, cohp_energy, species, zval_dict, d_limit, struct, smearing):
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "lobsterin")
    lines = []
    lines.append("COHPstartEnergy  %s" % cohp_energy[0])
    lines.append("COHPendEnergy    %s" % cohp_energy[1])
    lines.append("usebasisset pbeVaspFit2015")
    if mode == 0:
        lines.append("gaussianSmearingWidth %s" % smearing)
    for sp in struct.types_of_specie:
        if sp.name in zval_dict:
            lines.append("basisfunctions %s %s" % (sp.name, zval_dict[sp.name]))
        else:
            print("Warning: no -z orbitals given for %s; basisfunctions omitted."
                  " Add it to get reliable COHP." % sp.name, file=sys.stderr)
    lines.append("cohpGenerator from %s to %s type %s type %s"
                 % (d_limit[0], d_limit[1], species[0], species[1]))
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("Wrote %s" % path)
    return path


def main():
    p = argparse.ArgumentParser(description="Generate a LOBSTER lobsterin file.")
    p.add_argument("--struct", default="POSCAR", help="path to POSCAR (default: ./POSCAR)")
    p.add_argument("--list-bonds", action="store_true",
                   help="only print all bond-distance pairs (get_bond_total)")
    p.add_argument("-e", "--cohp-energy", nargs=2, type=float,
                   metavar=("Emin", "Emax"), help="COHPstartEnergy COHPendEnergy")
    p.add_argument("-s", "--species", nargs=2, metavar=("El1", "El2"),
                   help="two element types for the bond")
    p.add_argument("-z", "--zval", nargs="+",
                   help="valence orbitals, e.g. -z 'Ga:4s,4p,4d' 'As:4s,4p,4d'")
    p.add_argument("-d", "--d-limit", nargs=2, type=float,
                   metavar=("dmin", "dmax"), help="bond-length range")
    p.add_argument("-m", "--mode", type=int, choices=[0, 5], default=5,
                   help="5: tetrahedron (ISMEAR=-5, default); 0: gaussian (ISMEAR=0/1)")
    p.add_argument("--smearing", type=float, default=0.05,
                   help="gaussianSmearingWidth when mode=0 (default 0.05)")
    p.add_argument("--outdir", default=None,
                   help="output dir (default: <El1>_<El2>_<dmin>_<dmax>)")
    p.add_argument("--no-link", action="store_true",
                   help="do not symlink VASP files into the output dir")
    args = p.parse_args()

    if args.list_bonds:
        list_bonds(args.struct)
        return

    if not (args.cohp_energy and args.species and args.d_limit):
        p.error("-e, -s and -d are required (or use --list-bonds)")

    struct = load_structure(args.struct)

    zval_dict = {}
    for entry in args.zval or []:
        if ":" in entry:
            el, orb = entry.split(":", 1)
            zval_dict[el.strip()] = " ".join(orb.split(","))
    if not zval_dict:
        print("Note: no -z orbitals provided; basisfunctions will be incomplete.",
              file=sys.stderr)

    outdir = args.outdir or "%s_%s_%s_%s" % (args.species[0], args.species[1],
                                             args.d_limit[0], args.d_limit[1])

    if not args.no_link:
        for fname in ["WAVECAR", "CONTCAR", "KPOINTS", "OUTCAR", "POTCAR", "vasprun.xml"]:
            if os.path.exists(fname):
                os.system("ln -s %s %s" % (os.path.abspath(fname),
                                           os.path.join(outdir, fname)))
            else:
                print("%s does not exist (symlink skipped)." % fname, file=sys.stderr)

    write_lobsterin(outdir, args.mode, args.cohp_energy, args.species,
                    zval_dict, args.d_limit, struct, args.smearing)

    print("Note: run `lobster-4.1.0` inside '%s' (needs WAVECAR). If no COHP/ICOHP "
          "is output, raise NBANDS in INCAR." % outdir)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Error: %s" % exc, file=sys.stderr)
        sys.exit(1)
