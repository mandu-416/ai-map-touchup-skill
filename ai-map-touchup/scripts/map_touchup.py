"""Fix AI-generated illustrated maps: erase wrong labels and route lines, redraw
dotted routes, rotate street names, add step badges and legend entries.

Usage:
  python -I map_touchup.py grid IN OUT x1,y1,x2,y2 [--scale 2]
      Zoomed crop with pixel-coordinate ticks, for reading exact positions.
  python -I map_touchup.py apply IN OUT SPEC.json
      Apply the ops in SPEC.json in order (see below).

SPEC.json is {"ops": [...]} and each op is one of:
  {"op": "strip_color", "rgb_min_diff": 25, "min_r": 110,
   "protect": [[x1,y1,x2,y2], ...], "grow": 2}
      Find pixels of the route colour (default: red, r-g and r-b above
      rgb_min_diff) outside the protect boxes and inpaint them away. Protect
      pins, legend swatches, red text and red buildings.
  {"op": "inpaint", "boxes": [[x1,y1,x2,y2], ...], "radius": 3}
      Inpaint small boxes (leftover dots, a label sitting on a road).
  {"op": "fill", "box": [x1,y1,x2,y2], "sample": [x1,y1,x2,y2]}
      Flat fill with the median colour of the sample box (default: the
      box border). Best for labels on flat blocks; inpainting large boxes smears.
  {"op": "text", "text": "범례", "xy": [x,y], "size": 22, "color": "#222",
   "anchor": "mm", "bold": true, "angle": 0}
      Write text. angle != 0 rotates it around xy (street names along roads).
  {"op": "route", "points": [[x,y], ...], "color": "#c62828", "style": "dots",
   "mid_arrow": true}
      Dotted (or "dash") polyline with an end arrow, plus a mid-route arrow
      so the direction is readable where legs meet.
  {"op": "badge", "text": "1 → 2", "xy": [x,y], "color": "#c62828"}
      Small rounded label naming a route leg.
  {"op": "legend_entry", "box": [x1,y1,x2,y2], "text": "= 3A 선택 시",
   "color": "#ef6c00"}
      A boxed legend line with a dotted swatch.
"""
import argparse
import json
import math
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = {
    True: ["C:/Windows/Fonts/malgunbd.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc",
           "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"],
    False: ["C:/Windows/Fonts/malgun.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc",
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"],
}


def font(size, bold=True):
    for path in FONTS[bold]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    sys.exit("No Korean font found; edit FONTS in map_touchup.py")


def to_cv(im):
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


def to_pil(arr):
    return Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB))


def median_colour(im, box):
    x1, y1, x2, y2 = box
    px = np.array(im.crop((x1, y1, x2, y2))).reshape(-1, 3)
    return tuple(int(v) for v in np.median(px, axis=0))


def border_box(box, pad=3):
    x1, y1, x2, y2 = box
    return (x1 - pad, y1 - pad, x2 + pad, y1)  # strip just above the box


# --- ops ---------------------------------------------------------------------

def op_strip_color(im, o):
    arr = to_cv(im)
    b, g, r = [arr[:, :, i].astype(int) for i in range(3)]
    diff, min_r = o.get("rgb_min_diff", 25), o.get("min_r", 110)
    mask = ((r - g > diff) & (r - b > diff) & (r > min_r)).astype(np.uint8) * 255
    for x1, y1, x2, y2 in o.get("protect", []):
        mask[y1:y2, x1:x2] = 0
    mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=o.get("grow", 2))
    # small radius + Navier-Stokes keeps road/block edges crisp; Telea with a
    # big radius smears white road colour into blocks
    return to_pil(cv2.inpaint(arr, mask, o.get("radius", 3), cv2.INPAINT_NS))


def op_inpaint(im, o):
    arr = to_cv(im)
    mask = np.zeros(arr.shape[:2], np.uint8)
    for x1, y1, x2, y2 in o["boxes"]:
        mask[y1:y2, x1:x2] = 255
    return to_pil(cv2.inpaint(arr, mask, o.get("radius", 3), cv2.INPAINT_NS))


def op_fill(im, o):
    box = o["box"]
    colour = o.get("rgb") or median_colour(im, o.get("sample") or border_box(box))
    ImageDraw.Draw(im).rectangle(box, fill=tuple(colour))
    return im


def op_text(im, o):
    f = font(o.get("size", 22), o.get("bold", True))
    colour, anchor, angle = o.get("color", "#222222"), o.get("anchor", "mm"), o.get("angle", 0)
    if not angle:
        ImageDraw.Draw(im).text(tuple(o["xy"]), o["text"], font=f, fill=colour, anchor=anchor)
        return im
    w = int(f.getlength(o["text"])) + 20
    h = o.get("size", 22) + 16
    tile = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((w // 2, h // 2), o["text"], font=f, fill=colour, anchor="mm")
    tile = tile.rotate(angle, expand=True, resample=Image.BICUBIC)
    x, y = o["xy"]
    im.paste(tile, (int(x - tile.width / 2), int(y - tile.height / 2)), tile)
    return im


def _arrow(d, p, q, colour, size):
    a = math.atan2(q[1] - p[1], q[0] - p[0])
    d.polygon([q, (q[0] - size * math.cos(a - .45), q[1] - size * math.sin(a - .45)),
               (q[0] - size * math.cos(a + .45), q[1] - size * math.sin(a + .45))], fill=colour)


def op_route(im, o):
    d = ImageDraw.Draw(im)
    pts = [tuple(p) for p in o["points"]]
    colour, style = o.get("color", "#c62828"), o.get("style", "dots")
    r, gap = o.get("dot_radius", 5), o.get("gap", 15)
    total = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
    carry, walked, mid_done = 0.0, 0.0, not o.get("mid_arrow", True)
    for a, b in zip(pts, pts[1:]):
        seg = math.dist(a, b)
        if seg == 0:
            continue
        s = carry
        while s <= seg:
            x, y = a[0] + (b[0] - a[0]) * s / seg, a[1] + (b[1] - a[1]) * s / seg
            if style == "dash":
                e = min(seg, s + gap * 0.6)
                x2, y2 = a[0] + (b[0] - a[0]) * e / seg, a[1] + (b[1] - a[1]) * e / seg
                d.line([(x, y), (x2, y2)], fill=colour, width=r)
            else:
                d.ellipse([x - r, y - r, x + r, y + r], fill=colour)
            s += gap
        carry = s - seg
        if not mid_done and walked + seg >= total / 2 and seg > 40:
            t = (total / 2 - walked) / seg
            _arrow(d, a, (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), colour, 18)
            mid_done = True
        walked += seg
    _arrow(d, pts[-2], pts[-1], colour, o.get("arrow_size", 20))
    return im


def op_badge(im, o):
    d = ImageDraw.Draw(im)
    f = font(o.get("size", 17))
    colour = o.get("color", "#c62828")
    l, t, r, b = d.textbbox(tuple(o["xy"]), o["text"], font=f, anchor="mm")
    d.rounded_rectangle((l - 7, t - 4, r + 7, b + 4), 8, fill="white", outline=colour, width=2)
    d.text(tuple(o["xy"]), o["text"], font=f, fill=colour, anchor="mm")
    return im


def op_legend_entry(im, o):
    d = ImageDraw.Draw(im)
    x1, y1, x2, y2 = o["box"]
    cy = (y1 + y2) // 2
    d.rounded_rectangle((x1, y1, x2, y2), 10, fill="white", outline="#555555", width=2)
    for i in range(4):
        x = x1 + 14 + i * 13
        d.ellipse([x - 4, cy - 4, x + 4, cy + 4], fill=o.get("color", "#ef6c00"))
    d.text((x1 + 66, cy), o["text"], font=font(o.get("size", 19), False), fill="#222222", anchor="lm")
    return im


OPS = {"strip_color": op_strip_color, "inpaint": op_inpaint, "fill": op_fill, "text": op_text,
       "route": op_route, "badge": op_badge, "legend_entry": op_legend_entry}


def apply(args):
    spec = json.load(open(args.spec, encoding="utf-8"))
    im = Image.open(args.src).convert("RGB")
    for i, o in enumerate(spec["ops"]):
        if o["op"] not in OPS:
            sys.exit(f"op {i}: unknown op {o['op']!r}")
        im = OPS[o["op"]](im, o)
    im.save(args.dst, quality=93)
    print(f"{len(spec['ops'])} ops -> {args.dst}")


def grid(args):
    x1, y1, x2, y2 = (int(v) for v in args.box.split(","))
    s = args.scale
    im = Image.open(args.src).convert("RGB").crop((x1, y1, x2, y2))
    im = im.resize((im.width * s, im.height * s), Image.NEAREST)
    d = ImageDraw.Draw(im)
    step = 20 * s
    for i in range(0, im.width, step):
        d.line([(i, 0), (i, 6)], fill="black")
        d.text((i + 2, 7), str(x1 + i // s), fill="black")
    for j in range(0, im.height, step):
        d.line([(0, j), (6, j)], fill="black")
        d.text((8, j), str(y1 + j // s), fill="black")
    im.save(args.dst)
    print(f"grid {args.box} x{s} -> {args.dst}")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("grid"); g.add_argument("src"); g.add_argument("dst"); g.add_argument("box")
    g.add_argument("--scale", type=int, default=2)
    a = sub.add_parser("apply"); a.add_argument("src"); a.add_argument("dst"); a.add_argument("spec")
    args = p.parse_args()
    {"grid": grid, "apply": apply}[args.cmd](args)


if __name__ == "__main__":
    main()
