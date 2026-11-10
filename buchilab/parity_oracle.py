"""Independent set recursion, Floyd threshold classes and policy-pair lasso oracle.

Only the strict validator is shared with the generator. Complete-report comparison
uses canonical JSON so boolean/number type substitutions are not accepted.
"""

from itertools import product
import json
from .parity_input import validate


def replay(data):
    data = validate(data)
    states = data["states"]
    names = [s["name"] for s in states]
    rows = {s["name"]: s for s in states}
    owner = {s["name"]: 0 if s["owner"] == "even" else 1 for s in states}
    priorities = {s["name"]: s["priority"] for s in states}
    order = lambda values: [v for v in names if v in values]
    calls = []

    def attraction(universe, player, seed):
        before = frozenset(seed)
        history = []
        while True:
            qualifications = {}
            obligations = []
            for v in order(universe):
                outgoing = [m for m in rows[v]["moves"] if m["to"] in universe]
                if not outgoing:
                    raise ValueError("non-total recursive subgame")
                matches = {m["action"] for m in outgoing if m["to"] in before}
                q = (
                    bool(matches)
                    if owner[v] == player
                    else len(matches) == len(outgoing)
                )
                qualifications[v] = q
                obligations.append(
                    {
                        "state": v,
                        "operator": "exists" if owner[v] == player else "all",
                        "moves": [
                            {
                                "action": m["action"],
                                "to": m["to"],
                                "active": m["to"] in universe,
                                "in_before": m["to"] in before,
                            }
                            for m in rows[v]["moves"]
                        ],
                        "qualifies": q,
                    }
                )
            after = before | frozenset(v for v, q in qualifications.items() if q)
            history.append(
                {
                    "index": len(history),
                    "before": order(before),
                    "after": order(after),
                    "added": order(after - before),
                    "checks": obligations,
                }
            )
            if before == after:
                return before, {
                    "player": player,
                    "target": order(seed),
                    "rounds": history,
                    "result": order(before),
                }
            before = after

    def partition(universe, parent=None, via="root"):
        position = len(calls)
        call = {
            "index": position,
            "parent": parent,
            "via": via,
            "active": order(universe),
            "maximum": None,
            "player": None,
            "target": [],
            "first_attractor": None,
            "first_child": None,
            "opponent_seed": [],
            "second_attractor": None,
            "second_child": None,
            "branch": "empty",
            "winning": [[], []],
        }
        calls.append(call)
        if not universe:
            return (frozenset(), frozenset()), position
        maximum = max(priorities[v] for v in universe)
        player = maximum & 1
        seed = frozenset(v for v in universe if priorities[v] == maximum)
        removed, proof = attraction(universe, player, seed)
        regions, child = partition(
            universe - removed, position, "without_first_attractor"
        )
        enemy = regions[1 - player]
        call.update(
            maximum=maximum,
            player=player,
            target=order(seed),
            first_attractor=proof,
            first_child=child,
            opponent_seed=order(enemy),
        )
        if enemy:
            removed, proof = attraction(universe, 1 - player, enemy)
            regions, child = partition(
                universe - removed, position, "without_second_attractor"
            )
            result = list(regions)
            result[1 - player] = result[1 - player] | removed
            call.update(
                second_attractor=proof, second_child=child, branch="opponent_dominion"
            )
        else:
            result = list(regions)
            result[player] = result[player] | removed
            call["branch"] = "opponent_empty"
        call["winning"] = [order(x) for x in result]
        return tuple(result), position

    regions, _ = partition(frozenset(names))
    owned = [[v for v in names if owner[v] == p] for p in range(2)]
    choices = [
        [
            dict(zip(owned[p], values))
            for values in product(*(range(len(rows[v]["moves"])) for v in owned[p]))
        ]
        for p in range(2)
    ]
    pairs = []
    # Opponent universal quantification happens here, without SCCs or recursion.
    winning_by_policy = [[set(names) for _ in choices[p]] for p in range(2)]
    for e, even in enumerate(choices[0]):
        for o, odd in enumerate(choices[1]):
            decision = dict(even, **odd)
            roots = []
            for root in names:
                sequence = [root]
                while True:
                    current = sequence[-1]
                    target = rows[current]["moves"][decision[current]]["to"]
                    if target in sequence:
                        boundary = sequence.index(target)
                        break
                    sequence.append(target)
                loop = sequence[boundary:]
                highest = sorted(priorities[v] for v in loop)[-1]
                winner = highest & 1
                winning_by_policy[1 - winner][o if winner == 0 else e].discard(root)
                roots.append(
                    {
                        "state": root,
                        "prefix": sequence[:boundary],
                        "cycle": loop,
                        "steps": [
                            {"from": v, **rows[v]["moves"][decision[v]]}
                            for v in sequence
                        ],
                        "maximum": highest,
                        "winner": winner,
                    }
                )
            pairs.append({"even_policy": e, "odd_policy": o, "roots": roots})
    for player in range(2):
        if frozenset().union(*winning_by_policy[player]) != regions[player]:
            raise ValueError("positional oracle and recursive partition disagree")
    players = []
    for player in range(2):
        policies = []
        for index, decision in enumerate(choices[player]):
            edges = [
                {"from": v, **m}
                for v in names
                for k, m in enumerate(rows[v]["moves"])
                if v not in decision or decision[v] == k
            ]
            thresholds = []
            bad = set()
            for threshold in sorted(set(priorities.values())):
                if threshold % 2 == player:
                    continue
                allowed = {v for v in names if priorities[v] <= threshold}
                # Positive-length Floyd relation: diagonal only if a real cycle exists.
                reach = {
                    (e["from"], e["to"])
                    for e in edges
                    if e["from"] in allowed and e["to"] in allowed
                }
                for k in names:
                    if k in allowed:
                        reach |= {
                            (a, b)
                            for a in allowed
                            for b in allowed
                            if (a, k) in reach and (k, b) in reach
                        }
                pending = set(allowed)
                components = []
                for v in order(allowed):
                    if v not in pending:
                        continue
                    component = {
                        w
                        for w in allowed
                        if w == v or ((v, w) in reach and (w, v) in reach)
                    }
                    pending -= component
                    cyclic = (v, v) in reach
                    has_threshold = any(priorities[w] == threshold for w in component)
                    losing = cyclic and has_threshold
                    if losing:
                        bad |= component
                    components.append(
                        {
                            "states": order(component),
                            "cyclic": cyclic,
                            "contains_threshold": has_threshold,
                            "losing": losing,
                        }
                    )
                thresholds.append(
                    {
                        "priority": threshold,
                        "allowed": order(allowed),
                        "components": components,
                    }
                )
            reach = {(e["from"], e["to"]) for e in edges} | {(v, v) for v in names}
            for k in names:
                reach |= {
                    (a, b)
                    for a in names
                    for b in names
                    if (a, k) in reach and (k, b) in reach
                }
            roots = []
            for v in names:
                reachable = {w for w in names if (v, w) in reach}
                roots.append(
                    {
                        "state": v,
                        "reachable": order(reachable),
                        "bad_reachable": order(reachable & bad),
                        "winning": not bool(reachable & bad),
                    }
                )
            winners = [r["state"] for r in roots if r["winning"]]
            if set(winners) != winning_by_policy[player][index]:
                raise ValueError(
                    "Floyd threshold classes disagree with joint-policy lassos"
                )
            policies.append(
                {
                    "index": index,
                    "choices": [
                        {"state": v, "action": rows[v]["moves"][decision[v]]["action"]}
                        for v in owned[player]
                    ],
                    "edges": edges,
                    "thresholds": thresholds,
                    "roots": roots,
                    "winning": winners,
                }
            )
        canonical = next(
            p["index"] for p in policies if regions[player] <= set(p["winning"])
        )
        players.append(
            {"player": player, "policies": policies, "canonical_policy": canonical}
        )
    return {
        "schema": "buchilab-parity-v1",
        "convention": "maximum_recurring_priority",
        "input": data,
        "calls": calls,
        "winning": [order(x) for x in regions],
        "players": players,
        "joint_policies": pairs,
    }


def verify(report):
    try:
        if type(report) is not dict:
            return False
        actual = json.dumps(
            report, sort_keys=True, allow_nan=False, separators=(",", ":")
        )
        expected = json.dumps(
            replay(report["input"]),
            sort_keys=True,
            allow_nan=False,
            separators=(",", ":"),
        )
        return actual == expected
    except (ValueError, TypeError, KeyError, RecursionError, StopIteration):
        return False
