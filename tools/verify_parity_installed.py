"""Fresh-wheel origin/entrypoint/atomic-forgery checks outside the checkout."""

import copy
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from buchilab.parity import analyze
from buchilab.parity_oracle import verify

modules = [
    "buchilab",
    "buchilab.core",
    "buchilab.verify",
    "buchilab.__main__",
    "buchilab.witness",
    "buchilab.parity_input",
    "buchilab.parity",
    "buchilab.parity_oracle",
    "buchilab.parity_cli",
]
origins = [
    str(Path(importlib.import_module(name).__file__).resolve()) for name in modules
]
assert all("site-packages" in origin for origin in origins), origins
controls = json.loads(Path(sys.argv[1]).read_text())
commands = [
    [sys.executable, "-m", "buchilab.parity_cli"],
    [str(Path(sys.executable).parent / "buchilab-parity")],
]
env = dict(os.environ)
env.pop("PYTHONPATH", None)
counts = dict(
    controls=0,
    entrypoints=2,
    direct_forgeries=0,
    atomic_cli_forgeries=0,
    installed_origins=origins,
)
with tempfile.TemporaryDirectory() as outside:
    destination = Path(outside) / "certificate.json"
    for control in controls:
        expected = analyze(control["input"])
        assert verify(expected)
        for command in commands:
            built = subprocess.run(
                command + ["-", "--output", str(destination)],
                input=json.dumps(control["input"]),
                text=True,
                capture_output=True,
                check=True,
                cwd=outside,
                env=env,
            )
            assert not built.stdout
            assert json.loads(destination.read_text()) == expected
            checked = subprocess.run(
                command + [str(destination), "--verify"],
                capture_output=True,
                text=True,
                check=True,
                cwd=outside,
                env=env,
            )
            assert json.loads(checked.stdout) == {
                "valid": True,
                "schema": "buchilab-parity-v1",
            }
        forged = [copy.deepcopy(expected), copy.deepcopy(expected)]
        forged[0]["joint_policies"][0]["roots"][0]["winner"] ^= 1
        forged[1]["calls"][0]["index"] = False
        for bad in forged:
            assert not verify(bad)
            counts["direct_forgeries"] += 1
            for command in commands:
                destination.write_bytes(b"unchanged output\n")
                checked = subprocess.run(
                    command + ["-", "--verify", "--output", str(destination)],
                    input=json.dumps(bad),
                    capture_output=True,
                    text=True,
                    cwd=outside,
                    env=env,
                )
                assert checked.returncode == 2 and not checked.stdout
                assert destination.read_bytes() == b"unchanged output\n"
                assert [p.name for p in Path(outside).iterdir()] == ["certificate.json"]
                counts["atomic_cli_forgeries"] += 1
        counts["controls"] += 1
print(json.dumps(counts, sort_keys=True))
