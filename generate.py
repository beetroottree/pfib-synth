#!/usr/bin/env python3
"""Generate a synthetic pFIB-SEM stack with exact ground truth.

    python generate.py comp_like                       # 118-frame package like the team's review packages
    python generate.py fibre_mat --frames 40 --width 512 --out out/quick
    python generate.py --list

A package holds the image stack (<name>_full.tif), the exact truth masks
(truth/masks/slice_NNNN.png: 0 pore, 255 solid, 128 outside the layer), start
masks from the threshold rule our labels came from, and stack.json / truth.json.
The masks use the team's 0/128/255 encoding, so eponge.io.export_to_classes
and the annotation tools read them unchanged.
"""
import argparse, json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# style = which real acquisition the microscope is calibrated to; family = how the material is built.
# These are the seven packages in the README, with their seeds.
PRESETS = {
    "comp_like":     dict(style="comp",     family="v5",       porosity=0.417, seed=20261040),
    "uncomp_like":   dict(style="uncomp",   family="v5",       porosity=0.558, seed=20261057),
    "pristine_like": dict(style="pristine", family="v5",       porosity=0.515, seed=20261074),
    "mudcrack":      dict(style="comp",     family="mudcrack", porosity=0.45,  seed=20261091),
    "fibre_mat":     dict(style="uncomp",   family="fibre",    porosity=0.62,  seed=20261108,
                          mat_kw={"r_med": 5.0, "rim": 1.5, "thick_frac": 0.12}),
    "fibre_coated":  dict(style="uncomp",   family="fibre",    porosity=0.60,  seed=20261125,
                          mat_kw={"r_med": 4.0, "rim": 1.2, "decorate": 2.0, "binder": 0.6}),
    "faceted":       dict(style="pristine", family="faceted",  porosity=0.22,  seed=20261142),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("material", nargs="?", choices=list(PRESETS))
    ap.add_argument("--list", action="store_true", help="show the presets")
    ap.add_argument("--frames", type=int, default=118, help="slices (real stacks: comp 354, uncomp 410, pristine 665)")
    ap.add_argument("--width", type=int, default=None, help="narrower frames for a quick look")
    ap.add_argument("--porosity", type=float, default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--out", default=None, help="output folder (default out/<material>)")
    a = ap.parse_args()
    if a.list or not a.material:
        for k, v in PRESETS.items():
            print(f"{k:<14} calibrated to {v['style']:<9} material {v['family']:<9} porosity {v['porosity']}")
        return
    p = PRESETS[a.material]
    cmd = [sys.executable, str(HERE / "pfibsynth" / "make_full.py"), "--style", p["style"], "--family", p["family"],
           "--porosity", str(a.porosity or p["porosity"]), "--seed", str(a.seed or p["seed"]),
           "--frames", str(a.frames), "--name", f"synth_{a.material}", "--out", a.out or str(HERE / "out" / a.material)]
    if a.width:
        cmd += ["--width", str(a.width)]
    if "mat_kw" in p:
        cmd += ["--mat-kw", json.dumps(p["mat_kw"])]
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
