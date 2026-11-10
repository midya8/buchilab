"""Actual pinned Oink cross-check with three algorithm families and built-in verifier.

Set OINK_BIN to a separately built Oink1.1.0 binary. No output/result substitution.
This checks winning regions, not the JSON parser or complete trace semantics.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from buchilab.parity import analyze
from tools.parity_cases import all_cases


def main():
    binary = os.environ["OINK_BIN"]
    counts = {
        "requests": 0,
        "actual_solver_runs": 0,
        "regions_checked": 0,
        "canonical_certificates": 0,
    }
    with tempfile.TemporaryDirectory() as tmp:
        source, solution = Path(tmp) / "arena.pg", Path(tmp) / "answer.sol"
        source.write_text("parity 1;\n0 1 0 0,1;\n1 2 1 0;\n")
        solution.write_text("paritysol 2;\n0 0 1;\n1 0;\n")
        good = subprocess.run(
            [binary, "--no", "--sol", str(solution), "-v", str(source)],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        if "solution verified" not in good.stdout:
            raise ValueError(
                "external verifier calibration did not accept the known good policy"
            )
        solution.write_text("paritysol 2;\n0 0 0;\n1 0;\n")
        bad = subprocess.run(
            [binary, "--no", "--sol", str(solution), "-v", str(source)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if (
            bad.returncode == 0
            or "verification error: loser can win" not in bad.stdout + bad.stderr
        ):
            raise ValueError(
                "external verifier calibration did not reject the known losing wait policy"
            )
        counts["known_good_calibration"] = 1
        counts["known_bad_calibration"] = 1
        for case in all_cases():
            states = case["states"]
            ids = {s["name"]: i for i, s in enumerate(states)}
            source.write_text(
                "parity "
                + str(len(states) - 1)
                + ";\n"
                + "".join(
                    str(i)
                    + " "
                    + str(s["priority"])
                    + " "
                    + str(0 if s["owner"] == "even" else 1)
                    + " "
                    + ",".join(str(ids[m["to"]]) for m in s["moves"])
                    + ";\n"
                    for i, s in enumerate(states)
                )
            )
            report = analyze(case)
            expected = report["winning"]
            for algorithm in ("zlk", "spm", "tl"):
                solution.unlink(missing_ok=True)
                result = subprocess.run(
                    [
                        binary,
                        "--no",
                        "--" + algorithm,
                        "-v",
                        str(source),
                        str(solution),
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=10,
                )
                if "solution verified" not in result.stdout:
                    raise ValueError("Oink did not confirm its solution verifier")
                actual = [[], []]
                assignments = {}
                for line in solution.read_text().splitlines()[1:]:
                    vertex, winner, *_ = line.rstrip(";").split()
                    vertex, winner = int(vertex), int(winner)
                    if (
                        vertex in assignments
                        or not 0 <= vertex < len(states)
                        or winner not in (0, 1)
                    ):
                        raise ValueError("invalid Oink solution partition")
                    assignments[vertex] = winner
                if set(assignments) != set(range(len(states))):
                    raise ValueError("incomplete Oink partition")
                for i in range(len(states)):
                    actual[assignments[i]].append(states[i]["name"])
                if actual != expected:
                    raise ValueError(
                        "Oink " + algorithm + " disagrees: " + json.dumps(case)
                    )
                counts["actual_solver_runs"] += 1
                counts["regions_checked"] += 2
            # Submit our own uniform canonical strategies, rather than reusing
            # Oink's different strategy choices. All vertices have supplied winners.
            certificate = ["paritysol " + str(len(states)) + ";"]
            for i, state in enumerate(states):
                winner = 0 if state["name"] in expected[0] else 1
                suffix = ""
                if state["owner"] == ("even" if winner == 0 else "odd"):
                    catalog = report["players"][winner]
                    policy = catalog["policies"][catalog["canonical_policy"]]
                    action = next(
                        c["action"]
                        for c in policy["choices"]
                        if c["state"] == state["name"]
                    )
                    target = next(
                        m["to"] for m in state["moves"] if m["action"] == action
                    )
                    suffix = " " + str(ids[target])
                certificate.append(str(i) + " " + str(winner) + suffix + ";")
            solution.write_text("\n".join(certificate) + "\n")
            checked = subprocess.run(
                [binary, "--no", "--sol", str(solution), "-v", str(source)],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            if "solution verified" not in checked.stdout:
                raise ValueError(
                    "Oink did not verify the submitted native canonical strategies"
                )
            counts["canonical_certificates"] += 1
            counts["requests"] += 1
    print(json.dumps(counts, sort_keys=True))


if __name__ == "__main__":
    main()
