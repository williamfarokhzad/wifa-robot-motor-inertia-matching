import json
import math
from pathlib import Path
import subprocess
import sys
import unittest

from sweep import screen

ROOT = Path(__file__).resolve().parents[1]


def scenario(name="reference"):
    return json.loads((ROOT / "examples" / f"{name}.json").read_text())


class GearSweepTests(unittest.TestCase):
    def test_reference_against_hand_calculation(self):
        rows = screen(scenario())
        self.assertEqual([r.failed for r in rows],
                         [("inertia", "acceleration"), (), (), ("speed", "acceleration")])
        row = rows[1]
        self.assertAlmostEqual(row.reflected_load, .0004)
        self.assertAlmostEqual(row.inertia_ratio, 2.25)
        self.assertAlmostEqual(row.acceleration_nm, .195)
        self.assertEqual(row.motor_rpm, 1200)

    def test_kinetic_energy_invariant(self):
        cfg = scenario()
        w_load = cfg["output_rpm"] * math.tau / 60
        expected_load_energy = .5 * cfg["output_load_kg_m2"] * w_load**2
        for r in screen(cfg):
            w_motor = r.motor_rpm * math.tau / 60
            self.assertAlmostEqual(.5 * r.reflected_load * w_motor**2, expected_load_energy)

    def test_virtual_work_motor_and_load(self):
        cfg = scenario()
        base_j = cfg["rotor_kg_m2"] + cfg["gear_input_kg_m2"]
        a_load = cfg["output_accel_rad_s2"]
        load_work = cfg["output_load_kg_m2"] * a_load * .1
        for r in screen(cfg):
            motor_work = (r.acceleration_nm - base_j * a_load * r.ratio) * .1 * r.ratio
            self.assertAlmostEqual(motor_work, load_work)

    def test_exact_limits_are_inclusive(self):
        cfg = scenario() | dict(ratios=[10], max_inertia_ratio=2.25,
                                max_motor_rpm=1200, max_acceleration_nm=.195)
        self.assertEqual(screen(cfg)[0].failed, ())
        self.assertEqual(screen(cfg | dict(max_motor_rpm=1199))[0].failed, ("speed",))

    def test_no_ratio_passes_speed_conflict(self):
        self.assertTrue(all("speed" in r.failed for r in screen(scenario("speed-conflict"))))

    def test_heavy_load_discrete_minimum(self):
        rows = [r for r in screen(scenario("heavier-payload")) if not r.failed]
        self.assertEqual([r.ratio for r in rows], [15, 20, 25])
        self.assertEqual(min(rows, key=lambda r: r.acceleration_nm).ratio, 20)

    def test_zero_external_load_retains_input_inertia(self):
        row = screen(scenario() | dict(output_load_kg_m2=0, ratios=[1]))[0]
        self.assertEqual(row.reflected_load, 0)
        self.assertAlmostEqual(row.inertia_ratio, .25)
        self.assertAlmostEqual(row.acceleration_nm, .0075)

    def test_input_validation_and_order(self):
        cfg = scenario()
        self.assertEqual([r.ratio for r in screen(cfg | dict(ratios=[20, 1, 5]))], [1, 5, 20])
        for patch in (dict(ratios=[.1]), dict(ratios=[5, 5.0]), dict(rotor_kg_m2=0),
                      dict(max_inertia_ratio=True), dict(output_rpm=float("nan")), dict(extra=2)):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                screen(cfg | patch)

    def test_cli_expected_error(self):
        result = subprocess.run([sys.executable, "sweep.py", "examples/reversed-ratio.json"],
                                cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("motor speed / output speed", result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
