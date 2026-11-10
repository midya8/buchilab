"""Bounded deterministic parity evidence cases, not performance benchmarks."""

from itertools import product
import json
from pathlib import Path
import random


def arena(priorities, owners, successors):
    return {
        "states": [
            {
                "name": "s" + str(i),
                "owner": ["even", "odd"][owners[i]],
                "priority": p,
                "moves": [
                    {"action": "a" + str(k), "to": "s" + str(j)}
                    for k, j in enumerate(successors[i])
                ],
            }
            for i, p in enumerate(priorities)
        ]
    }


def controls():
    return json.loads(
        (Path(__file__).resolve().parents[1] / "docs/parity-controls.json").read_text()
    )


def all_cases():
    for priorities in product(range(4), repeat=2):
        for owners in product(range(2), repeat=2):
            for successors in product([[0], [1], [0, 1]], repeat=2):
                yield arena(priorities, owners, successors)
    rng = random.Random(73519)
    for _ in range(72):
        n = rng.randrange(1, 7)
        yield arena(
            [rng.randrange(8) for _ in range(n)],
            [rng.randrange(2) for _ in range(n)],
            [rng.sample(range(n), rng.randrange(1, min(n, 2) + 1)) for _ in range(n)],
        )
    for control in controls():
        yield control["input"]
