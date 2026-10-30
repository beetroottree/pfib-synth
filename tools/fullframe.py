"""Full-frame GIFs of one generated package: the whole sheet, as the microscope records it.

    python tools/fullframe.py PACKAGE_DIR OUT_DIR [--label NAME] [--width 960] [--step 2]

The showcase GIFs (showcase.py) zoom into a 224 px window of the layer with the
drift removed. These show the entire frame the way a real acquisition looks
when you page through it: the protective cap on top, the catalyst layer, the
support below, the frame drifting as the cut advances. Synthetic frames only.

Writes into OUT_DIR:
  <name>_frame.gif        the full frame, slice by slice, regions named at the side
  <name>_frame_truth.gif  the same frame above its exact truth (pore / solid / outside the layer)
  <name>_frame.png        one full-resolution frame, as a still
"""
import argparse, json
from pathlib import Path
import numpy as np, tifffile
from PIL import Image, ImageDraw, ImageFont

ap = argparse.ArgumentParser()
ap.add_argument("pkg"); ap.add_argument("out"); ap.add_argument("--label", default=None)
ap.add_argument("--width", type=int, default=960, help="GIF width in px (frames are downscaled)")
ap.add_argument("--step", type=int, default=2, help="use every STEP-th slice")
ap.add_argument("--colors", type=int, default=48, help="GIF palette size (the noise is what costs bytes)")
a = ap.parse_args()
pkg, out = Path(a.pkg), Path(a.out); out.mkdir(parents=True, exist_ok=True)
meta = json.loads((pkg / "stack.json").read_text())
name = a.label or meta["name"].replace("synth_", "")
stack = tifffile.imread(pkg / meta["stack_file"])
N, H, W = stack.shape
zs = list(range(0, N, a.step))
T = {z: np.array(Image.open(pkg / f"truth/masks/slice_{z:04d}.png")) for z in zs}
sc = a.width / W; w, h = a.width, int(round(H * sc))
BAR = 22
try:
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 13)
except OSError:
    font = ImageFont.load_default()


def small(arr, resample=Image.BILINEAR):
    return Image.fromarray(arr).resize((w, h), resample)


def regions(t):
    """(top, bottom) rows of the catalyst layer in this frame, from the truth."""
    rows = np.where((t != 128).mean(1) > 0.3)[0]
    return (int(rows[0]), int(rows[-1])) if len(rows) else (H // 3, 2 * H // 3)


def tag(d, x, y, s):
    tw = d.textlength(s, font=font)
    d.rectangle([x - 3, y - 2, x + tw + 3, y + 15], fill=(0, 0, 0)); d.text((x, y), s, fill=(235, 235, 235), font=font)


def caption(img, z, extra=""):
    canvas = Image.new("RGB", (w, img.height + BAR), (14, 15, 18)); canvas.paste(img, (0, 0))
    d = ImageDraw.Draw(canvas)
    d.text((8, img.height + 4), f"SYNTHETIC  {name}   slice {z + 1:>3} / {N}   frame {W} x {H} px{extra}", fill=(200, 205, 212), font=font)
    return canvas


def sides(img, t):
    d = ImageDraw.Draw(img); top, bot = regions(t)
    if top * sc > 22: tag(d, 8, max(4, int(top * sc / 2) - 8), "cap")
    tag(d, 8, int((top + bot) / 2 * sc) - 8, "porous layer (scored)")
    if (H - bot) * sc > 22: tag(d, 8, int((bot + (H - bot) / 2) * sc) - 8, "support")
    for r in (top, bot):                                   # thin tick at the layer edges, at the side only
        d.line([(0, int(r * sc)), (5, int(r * sc))], fill=(90, 200, 250), width=2)
    return img


def save(frames, fn, dur=90):
    fr = [f.convert("RGB").quantize(a.colors) for f in frames]
    fr[0].save(out / fn, save_all=True, append_images=fr[1:], duration=dur, loop=0, optimize=True)
    print(f"  {fn} {(out / fn).stat().st_size / 1e6:.1f} MB", flush=True)


plain, paired = [], []
for z in zs:
    im = sides(small(stack[z]).convert("RGB"), T[z])
    plain.append(caption(im, z))
    t = T[z]; tv = np.where(t == 0, 0, np.where(t == 255, 255, 96)).astype(np.uint8)
    tr = small(tv, Image.NEAREST).convert("RGB"); d = ImageDraw.Draw(tr)
    tag(d, 8, 6, "exact truth:  black pore   white solid   grey outside the layer")
    both = Image.new("RGB", (w, 2 * h + 4), (14, 15, 18)); both.paste(im, (0, 0)); both.paste(tr, (0, h + 4))
    paired.append(caption(both, z))
save(plain, f"{name}_frame.gif")
save(paired, f"{name}_frame_truth.gif")
Image.fromarray(stack[N // 2]).save(out / f"{name}_frame.png", optimize=True)
print(f"  {name}_frame.png {(out / f'{name}_frame.png').stat().st_size / 1e6:.1f} MB", flush=True)
