"""Screen fixed gear ratios for one ideal rigid rotary axis. No motor I/O."""
import argparse
from dataclasses import dataclass
import json
import math
from pathlib import Path


def number(name, value, low, high):
    if (type(value) not in (int, float) or not low <= value <= high):
        raise ValueError(f"{name} must be a finite number in [{low:g}, {high:g}]")
    return float(value)


@dataclass(frozen=True)
class Row:
    ratio: float
    reflected_load: float
    inertia_ratio: float
    motor_rpm: float
    acceleration_nm: float
    failed: tuple[str, ...]


def screen(data):
    """Return rows sorted by ratio; 'failed' contains independent screen flags."""
    fields = {
        "rotor_kg_m2": (1e-12, 1e4),
        "gear_input_kg_m2": (0, 1e4),
        "output_load_kg_m2": (0, 1e4),
        "output_rpm": (1e-6, 1e6),
        "output_accel_rad_s2": (1e-6, 1e8),
        "max_inertia_ratio": (1e-6, 1e8),
        "max_motor_rpm": (1e-6, 1e8),
        "max_acceleration_nm": (1e-9, 1e12),
    }
    if not isinstance(data, dict) or data.keys() != fields.keys() | {"ratios"}:
        raise ValueError("expected exactly the JSON keys shown in examples/reference.json")
    cfg = {key: number(key, data[key], *bounds) for key, bounds in fields.items()}
    ratios = data["ratios"]
    if not isinstance(ratios, list) or not 1 <= len(ratios) <= 1000:
        raise ValueError("ratios must contain between 1 and 1000 numbers")
    ratios = sorted(number("ratio (motor speed / output speed)", n, 1, 1e4) for n in ratios)
    if len(set(ratios)) != len(ratios):
        raise ValueError("gear ratios must be distinct")
    rows = []
    for n in ratios:
        reflected = cfg["output_load_kg_m2"] / n**2
        driven = cfg["gear_input_kg_m2"] + reflected
        ratio = driven / cfg["rotor_kg_m2"]
        rpm = n * cfg["output_rpm"]
        nm = (cfg["rotor_kg_m2"] + driven) * n * cfg["output_accel_rad_s2"]
        comparisons = (
            ("inertia", ratio, cfg["max_inertia_ratio"]),
            ("speed", rpm, cfg["max_motor_rpm"]),
            ("acceleration", nm, cfg["max_acceleration_nm"]),
        )
        # Admit equal limits despite sub-ULP differences in intermediate arithmetic.
        failed = tuple(name for name, v, limit in comparisons
                       if v > limit and not math.isclose(v, limit, rel_tol=1e-12, abs_tol=0))
        rows.append(Row(n, reflected, ratio, rpm, nm, failed))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", type=Path, help="input JSON file")
    args = parser.parse_args()
    try:
        rows = screen(json.loads(args.scenario.read_text(encoding="utf-8")))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Input error: {exc}\n")
    print("N  J_ref(kg m^2)  driven/rotor  motor(rpm)  accel(N m)  screen")
    for r in rows:
        result = ", ".join(r.failed) if r.failed else "pass"
        print(f"{r.ratio:g}  {r.reflected_load:.6g}  {r.inertia_ratio:.6g}  "
              f"{r.motor_rpm:.6g}  {r.acceleration_nm:.6g}  {result}")
    passed = [r for r in rows if not r.failed]
    if passed:
        best = min(passed, key=lambda r: (r.acceleration_nm, r.ratio))
        print(f"Lowest modeled acceleration torque among passing ratios: {best.ratio:g}:1")
    else:
        print("No ratio passed the modeled screen.")


if __name__ == "__main__":
    main()
