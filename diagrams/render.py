"""Render editable SVG from the reference case; use Inkscape and Pillow for WebP."""
from pathlib import Path
import html
import json
import subprocess
import sys
import tempfile

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from sweep import screen


def label(x, y, text, size=24, weight=500, color="#edf5ff", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color}" text-anchor="{anchor}">{html.escape(text)}</text>')


def rect(x, y, w, h, color, radius=14):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{color}"/>'


def line(x1, y1, x2, y2, color="#93a9c5", width=2, extra=""):
    return f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{color}" stroke-width="{width}" {extra}/>'


def save(name, height, bits):
    svg = HERE / f"{name}.svg"
    svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="960" height="{height}" '
                   f'viewBox="0 0 960 {height}"><g font-family="DejaVu Sans">'
                   + rect(0, 0, 960, height, "#111c30", 0) + "".join(bits) + '</g></svg>\n')
    with tempfile.TemporaryDirectory(dir=HERE) as tmp:
        png = Path(tmp) / "render.png"
        subprocess.run(["inkscape", str(svg), f"--export-filename={png}"], check=True)
        with Image.open(png) as image:
            image.convert("RGB").save(svg.with_suffix(".webp"), quality=87, method=6)


def shafts(data):
    row = next(x for x in screen(data) if x.ratio == 10)
    bits = [label(42, 58, "Follow the two shaft speeds", 38, 700),
            label(42, 98, "Reference example   |   N = 10:1", 24, color="#a9c5e5")]
    for x, title, inertia, speed in (
        (42, "Motor rotor", f'J = {data["rotor_kg_m2"]:g} kg·m²', f'{row.motor_rpm:g} rpm'),
        (355, "Gear input", f'J = {data["gear_input_kg_m2"]:g} kg·m²', f'{row.motor_rpm:g} rpm'),
        (668, "Output load", f'J = {data["output_load_kg_m2"]:g} kg·m²', f'{data["output_rpm"]:g} rpm'),
    ):
        bits += [rect(x, 135, 250, 136, "#243753"), label(x+16, 170, title, 27, 700),
                 label(x+16, 208, inertia, 23), label(x+16, 244, speed, 24, color="#84e3d6")]
    for x in (292, 605):
        bits += [line(x+6, 201, x+55, 201, "#84e3d6", 3),
                 f'<path d="M{x+55} 201l-13 -7v14z" fill="#84e3d6"/>']
    bits += [rect(42, 297, 876, 111, "#183b46"),
             label(64, 334, "Move the output inertia to the motor shaft", 26, 700),
             label(64, 377, f"0.04 ÷ 10² = {row.reflected_load:g} kg·m²  (output load only)", 28)]
    save("motor-inertia-shafts", 440, bits)


def torque_curve(data):
    left, right, top, bottom = 112, 881, 125, 400
    x = lambda n: left+(n-5)/25*(right-left)
    y = lambda v: bottom-v/.32*(bottom-top)
    bits = [label(42, 55, "More reduction can cost torque", 38, 700),
            label(42, 95, "Reference case: motor acceleration torque, N·m", 24, color="#a9c5e5")]
    for v in (0, .08, .16, .24, .32):
        bits += [line(left, y(v), right, y(v), "#324563"), label(left-14, y(v)+8, f"{v:.2f}", 21, anchor="end")]
    for n in (5, 10, 15, 20, 25, 30):
        bits += [line(x(n), bottom, x(n), bottom+6, "#a9c5e5"),
                 label(x(n), bottom+31, f"{n}:1", 22, anchor="middle")]
    bits += [line(left, top, left, bottom), line(left, bottom, right, bottom)]
    base = data["rotor_kg_m2"] + data["gear_input_kg_m2"]
    load = data["output_load_kg_m2"]
    accel = data["output_accel_rad_s2"]
    for c, f, start, caption in (
        ("#f9ca73", lambda n: accel * load / n, 42, "Output share"),
        ("#91baff", lambda n: accel * base * n, 287, "Motor + gear input"),
        ("#79f4c6", lambda n: accel * (base*n+load/n), 622, "Total torque"),
    ):
        points = " ".join(f"{x(n/10):.2f},{y(f(n/10)):.2f}" for n in range(50, 301))
        bits += [f'<polyline points="{points}" fill="none" stroke="{c}" stroke-width="4"/>',
                 line(start, 473, start+40, 473, c, 4), label(start+51, 481, caption, 22)]
    for row in screen(data):
        bits += [f'<circle cx="{x(row.ratio)}" cy="{y(row.acceleration_nm)}" r="6" fill="#79f4c6" stroke="#111c30" stroke-width="2"/>']
    save("motor-inertia-torque-sweep", 510, bits)


if __name__ == "__main__":
    config = json.loads((HERE.parent / "examples/reference.json").read_text())
    shafts(config)
    torque_curve(config)
