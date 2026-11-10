"""Full-report and independent positional oracle tests for max-parity games."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from buchilab.parity import analyze
from buchilab.parity_input import validate
from buchilab.parity_oracle import replay, verify
from tools.parity_cases import all_cases, controls, arena


class ParityTests(unittest.TestCase):
    def test_complete_reports_and_independent_oracle(self):
        metrics = dict(
            reports=0,
            calls=0,
            policies=0,
            joint_policies=0,
            lassos=0,
            attractor_rounds=0,
        )
        for case in all_cases():
            generated = analyze(case)
            self.assertEqual(generated, replay(case))
            self.assertTrue(verify(generated))
            metrics["reports"] += 1
            metrics["calls"] += len(generated["calls"])
            metrics["policies"] += sum(len(p["policies"]) for p in generated["players"])
            metrics["joint_policies"] += len(generated["joint_policies"])
            metrics["lassos"] += sum(
                len(p["roots"]) for p in generated["joint_policies"]
            )
            metrics["attractor_rounds"] += sum(
                len(c[k]["rounds"])
                for c in generated["calls"]
                for k in ("first_attractor", "second_attractor")
                if c[k] is not None
            )
        self.assertEqual(metrics["reports"], 660)
        print("PARITY_METRICS", json.dumps(metrics, sort_keys=True))

    def test_region_not_policy(self):
        report = analyze(controls()[0]["input"])
        self.assertEqual(report["winning"], [["s0", "s1"], []])
        self.assertEqual(
            [p["winning"] for p in report["players"][0]["policies"]], [[], ["s0", "s1"]]
        )
        self.assertEqual(report["players"][0]["canonical_policy"], 1)

    def test_hidden_subcycle(self):
        report = analyze(controls()[1]["input"])
        self.assertEqual(report["winning"], [[], ["s0", "s1"]])
        even = report["players"][0]["policies"][0]
        lower = even["thresholds"][0]
        self.assertEqual(lower["priority"], 1)
        self.assertTrue(lower["components"][0]["losing"])
        self.assertEqual(lower["components"][0]["states"], ["s0"])

    def test_transient_maximum_not_used(self):
        report = analyze(controls()[2]["input"])
        lasso = report["joint_policies"][0]["roots"][0]
        self.assertEqual(
            (lasso["prefix"], lasso["cycle"], lasso["maximum"], lasso["winner"]),
            (["s0"], ["s1"], 0, 0),
        )

    def test_maximum_not_minimum(self):
        report = analyze(controls()[9]["input"])
        lasso = report["joint_policies"][0]["roots"][0]
        self.assertEqual(lasso["maximum"], 6)
        self.assertEqual(lasso["winner"], 0)

    def test_parallel_actions_keep_policies(self):
        report = analyze(controls()[8]["input"])
        self.assertEqual(len(report["players"][0]["policies"]), 2)
        self.assertEqual(len(report["joint_policies"]), 2)
        self.assertNotEqual(
            report["players"][0]["policies"][0]["choices"],
            report["players"][0]["policies"][1]["choices"],
        )

    def test_second_attractor_uses_original_active(self):
        report = analyze(controls()[-1]["input"])
        root = report["calls"][0]
        self.assertEqual(root["branch"], "opponent_dominion")
        self.assertIsNotNone(root["second_child"])
        self.assertEqual(
            len(root["second_attractor"]["rounds"][0]["checks"]), len(root["active"])
        )

    def test_final_unchanged_attractor_rounds(self):
        for control in controls():
            for call in analyze(control["input"])["calls"]:
                for key in ("first_attractor", "second_attractor"):
                    if call[key]:
                        last = call[key]["rounds"][-1]
                        self.assertEqual(last["before"], last["after"])
                        self.assertEqual(last["added"], [])

    def test_oracle_does_not_call_generator(self):
        case = controls()[0]["input"]
        report = analyze(case)
        with patch(
            "buchilab.parity.analyze", side_effect=AssertionError("generator forbidden")
        ):
            self.assertTrue(verify(report))

    def test_every_noninput_primitive_mutation_rejected(self):
        report = analyze(controls()[0]["input"])
        paths = []

        def walk(value, path=()):
            if isinstance(value, dict):
                for key, child in value.items():
                    if path or key != "input":
                        walk(child, path + (key,))
            elif isinstance(value, list):
                for i, child in enumerate(value):
                    walk(child, path + (i,))
            else:
                paths.append(path)

        walk(report)
        for path in paths:
            forged = copy.deepcopy(report)
            node = forged
            for part in path[:-1]:
                node = node[part]
            old = node[path[-1]]
            node[path[-1]] = (
                (not old)
                if type(old) is bool
                else (
                    old + 1
                    if type(old) is int
                    else "changed" if old is None else old + "X"
                )
            )
            self.assertFalse(verify(forged), path)
        print("PARITY_PRIMITIVE_FORGERIES", len(paths))

    def test_shape_and_type_forgeries(self):
        report = analyze(controls()[0]["input"])
        forged = copy.deepcopy(report)
        forged["calls"][0]["index"] = False
        self.assertFalse(verify(forged))
        forged = copy.deepcopy(report)
        forged["extra"] = 0
        self.assertFalse(verify(forged))
        forged = copy.deepcopy(report)
        forged["joint_policies"].reverse()
        self.assertFalse(verify(forged))
        forged = copy.deepcopy(report)
        forged["calls"].pop()
        self.assertFalse(verify(forged))

    def test_strict_input(self):
        case = controls()[0]["input"]
        variants = []
        for value in [True, -1, 8, 2.0, "2", None]:
            bad = copy.deepcopy(case)
            bad["states"][0]["priority"] = value
            variants.append(bad)
        for value in [
            [],
            [{"action": "a0", "to": "s1"}] * 3,
            [{"action": "a0", "to": "absent"}],
            [{"action": "<script>", "to": "s0"}],
        ]:
            bad = copy.deepcopy(case)
            bad["states"][0]["moves"] = value
            variants.append(bad)
        bad = copy.deepcopy(case)
        bad["states"][1]["name"] = "s0"
        variants.append(bad)
        bad = copy.deepcopy(case)
        bad["states"][0]["owner"] = "controller"
        variants.append(bad)
        variants += [
            {"states": []},
            {"states": case["states"], "extra": 1},
            {"states": case["states"] * 4},
        ]
        for bad in variants:
            with self.assertRaises(ValueError):
                validate(bad)
        self.assertEqual(validate(case), case)
        self.assertIsNot(
            validate(case)["states"][0]["moves"], case["states"][0]["moves"]
        )

    def test_cli_roundtrip_and_atomic_preservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            source = tmp / "input.json"
            out = tmp / "report.json"
            for control in controls():
                source.write_text(json.dumps(control["input"]))
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "buchilab.parity_cli",
                        str(source),
                        "--output",
                        str(out),
                    ],
                    check=True,
                    capture_output=True,
                )
                report = json.loads(out.read_text())
                self.assertTrue(verify(report))
                done = subprocess.run(
                    [sys.executable, "-m", "buchilab.parity_cli", str(out), "--verify"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(
                    json.loads(done.stdout),
                    {"valid": True, "schema": "buchilab-parity-v1"},
                )
                report["convention"] = "minimum"
                source.write_text(json.dumps(report))
                out.write_text("preserve")
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "buchilab.parity_cli",
                        str(source),
                        "--verify",
                        "--output",
                        str(out),
                    ],
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 2)
                self.assertEqual(out.read_text(), "preserve")
                self.assertEqual(
                    sorted(p.name for p in tmp.iterdir()), ["input.json", "report.json"]
                )

    def test_cli_duplicate_nonfinite_oversized(self):
        for raw in ['{"states":[],"states":[]}', '{"states":NaN}', " " * 65537]:
            result = subprocess.run(
                [sys.executable, "-m", "buchilab.parity_cli", "-"],
                input=raw,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)

    def test_even_reflection_preserves_convention_conversion(self):
        case = controls()[9]["input"]
        reflected = copy.deepcopy(case)
        for s in reflected["states"]:
            s["priority"] = 8 - s["priority"]
        # Max parity in the reflected graph equals min parity in the original.
        self.assertEqual(analyze(reflected)["winning"], [[], ["s0", "s1"]])


if __name__ == "__main__":
    unittest.main()
