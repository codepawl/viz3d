"""Tests for fitout_check.py on examples/fitout-fixture.json, which plants one wrong conversion.

    uv run --no-project --with pillow python scripts/test_fitout_check.py
"""

import copy
import json
import pathlib
import sys
import tempfile
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import fitout_check  # noqa: E402

FIXTURE = SCRIPTS.parent / "examples" / "fitout-fixture.json"


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def by_id(rows):
    return {row["id"]: row for row in rows}


class ParseLength(unittest.TestCase):
    def test_written_forms(self):
        cases = {
            "6.10 m": 6.10, "6100 mm": 6.10, "610 cm": 6.10, "4.2m": 4.2,
            "20'-0\"": 6.096, "20' 0\"": 6.096, "20'": 6.096, "20 ft": 6.096,
            "13'-9 1/2\"": 4.2037, "165\"": 4.191, "165 in": 4.191, "5 ft 6 in": 1.6764,
            "39 3/8\"": 1.0001, "1,200 mm": 1.2, "20′-0″": 6.096,
        }
        for text, metres in cases.items():
            with self.subTest(text=text):
                self.assertAlmostEqual(fitout_check.parse_length(text), metres, places=3)

    def test_bare_number_uses_sheet_default(self):
        self.assertAlmostEqual(fitout_check.parse_length("6100", "mm"), 6.1)
        self.assertAlmostEqual(fitout_check.parse_length("48", "in"), 1.2192)
        with self.assertRaises(ValueError):
            fitout_check.parse_length("6100")

    def test_dual_annotation(self):
        primary, written = fitout_check.read_dimension_text("20'-0\" (6.40 m)", None)
        self.assertAlmostEqual(primary, 6.096, places=3)
        self.assertAlmostEqual(written, 6.40)
        primary, written = fitout_check.read_dimension_text("6.10 m [20'-0\"]", None)
        self.assertAlmostEqual(written, 6.096, places=3)

    def test_garbage_is_refused(self):
        for text in ("about six metres", "6.1 parsecs", ""):
            with self.subTest(text=text), self.assertRaises(ValueError):
                fitout_check.parse_length(text, "m")


class Units(unittest.TestCase):
    def test_planted_wrong_conversion_is_caught(self):
        rows = by_id(fitout_check.reconcile_units(load_fixture()))
        width = rows["room_width"]
        self.assertEqual(width["status"], "wrong conversion")
        self.assertIn("6.096 m, written as 6.400 m", width["faults"][0])
        self.assertAlmostEqual(width["resolved_m"], 6.098, places=3)

    def test_agreeing_sheets_pass(self):
        rows = by_id(fitout_check.reconcile_units(load_fixture()))
        for dimension_id in ("room_depth", "ceiling", "door"):
            with self.subTest(dimension_id=dimension_id):
                self.assertEqual(rows[dimension_id]["status"], "ok")

    def test_real_conflict_is_flagged_and_resolved_low(self):
        plan = load_fixture()
        plan["dimensions"].append({"id": "room_depth", "sheet": "M-201", "text": "27'"})
        depth = by_id(fitout_check.reconcile_units(plan))["room_depth"]
        self.assertEqual(depth["status"], "conflict")
        self.assertAlmostEqual(depth["resolved_m"], 8.0, places=3)

    def test_model_built_from_the_wrong_conversion_is_flagged(self):
        plan = load_fixture()
        plan["dimensions"][0]["b"] = [6.4, 4]
        width = by_id(fitout_check.reconcile_units(plan))["room_width"]
        self.assertEqual(width["status"], "model off")
        self.assertIn("+302 mm", width["faults"][-1])


class Fit(unittest.TestCase):
    def test_roaster_laid_out_for_the_wrong_width_clashes(self):
        rows = by_id(fitout_check.check_equipment(load_fixture()))
        roaster = rows["R1"]
        self.assertEqual(roaster["status"], "clash")
        self.assertEqual(roaster["binding"], "back service zone inside the room")
        self.assertAlmostEqual(roaster["margin_m"], -0.30, places=2)

    def test_same_layout_fits_in_the_room_it_was_drawn_for(self):
        plan = load_fixture()
        plan["rooms"][0]["poly"] = [[0, 0], [6.4, 0], [6.4, 8], [0, 8]]
        roaster = by_id(fitout_check.check_equipment(plan))["R1"]
        self.assertNotEqual(roaster["status"], "clash")

    def test_other_items(self):
        rows = by_id(fitout_check.check_equipment(load_fixture()))
        self.assertEqual(rows["C1"]["status"], "fits")
        self.assertEqual(rows["G1"]["status"], "fits")
        self.assertEqual(rows["P1"]["status"], "tight")
        self.assertAlmostEqual(rows["P1"]["margin_m"], 0.075, places=3)

    def test_ceiling_and_door(self):
        plan = load_fixture()
        plan["rooms"][0]["ceiling"] = 2.8
        roaster = by_id(fitout_check.check_equipment(plan))["R1"]
        names = [problem["check"] for problem in roaster["problems"]]
        self.assertIn("height with top clearance under the ceiling", names)
        plan = load_fixture()
        plan["equipment"][1]["at"] = [2.45, 0.9]
        tray = by_id(fitout_check.check_equipment(plan))["C1"]
        self.assertEqual(tray["status"], "clash")
        self.assertIn("door D1", tray["binding"])


class Outputs(unittest.TestCase):
    def test_all_writes_tables_card_and_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            plan_path = pathlib.Path(folder) / "plan.json"
            plan_path.write_text(json.dumps(load_fixture()), encoding="utf-8")
            sys.argv = ["fitout_check.py", "all", str(plan_path)]
            with self.assertRaises(SystemExit) as stopped:
                fitout_check.main()
            self.assertEqual(stopped.exception.code, 1)
            for name in ("fitout_units.md", "fitout_coordination.md", "fitout_report.json", "fitout_card.png"):
                self.assertTrue((pathlib.Path(folder) / name).exists(), name)
            table = (pathlib.Path(folder) / "fitout_coordination.md").read_text(encoding="utf-8")
            self.assertIn("✕ clash", table)
            self.assertIn("300 mm short", table)

    def test_clean_plan_passes(self):
        plan = copy.deepcopy(load_fixture())
        plan["dimensions"][1]["text"] = "20'-0\" (6.10 m)"
        plan["equipment"][0]["at"] = [4.775, 5.0]
        plan["equipment"][1]["at"] = [2.3, 5.2]
        with tempfile.TemporaryDirectory() as folder:
            plan_path = pathlib.Path(folder) / "plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            sys.argv = ["fitout_check.py", "all", str(plan_path)]
            with self.assertRaises(SystemExit) as stopped:
                fitout_check.main()
            self.assertEqual(stopped.exception.code, 0)


if __name__ == "__main__":
    unittest.main(verbosity=1)
