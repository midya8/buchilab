"""Classic max-priority Zielonka trace and bounded complete-policy certificates.

Region solver: synchronous attractor recursion. Policy certification: threshold
Tarjan SCCs and unrestricted reachability. Lasso atlas: functional joint policies.
No shared implementation with parity_oracle, apart from strict input validation.
"""

from itertools import product
from .parity_input import validate


def analyze(data):
    data = validate(data)
    ss = data["states"]
    ns = [s["name"] for s in ss]
    ids = {s: i for i, s in enumerate(ns)}
    n = len(ss)
    owners = [0 if s["owner"] == "even" else 1 for s in ss]
    priorities = [s["priority"] for s in ss]
    adj = [[ids[m["to"]] for m in s["moves"]] for s in ss]
    full = (1 << n) - 1
    ordered = lambda bits: [ns[i] for i in range(n) if bits >> i & 1]
    calls = []

    def attract(active, player, target):
        current = target
        rounds = []
        while True:
            after = current
            checks = []
            for i in range(n):
                if not active >> i & 1:
                    continue
                flags = [bool(current >> j & 1) for j in adj[i] if active >> j & 1]
                assert flags, "attractor complement must remain total"
                qualifies = any(flags) if owners[i] == player else all(flags)
                moves = [
                    {
                        "action": ss[i]["moves"][k]["action"],
                        "to": ns[j],
                        "active": bool(active >> j & 1),
                        "in_before": bool(current >> j & 1),
                    }
                    for k, j in enumerate(adj[i])
                ]
                checks.append(
                    {
                        "state": ns[i],
                        "operator": "exists" if owners[i] == player else "all",
                        "moves": moves,
                        "qualifies": qualifies,
                    }
                )
                if qualifies:
                    after |= 1 << i
            rounds.append(
                {
                    "index": len(rounds),
                    "before": ordered(current),
                    "after": ordered(after),
                    "added": ordered(after & ~current),
                    "checks": checks,
                }
            )
            if after == current:
                break
            current = after
        return current, {
            "player": player,
            "target": ordered(target),
            "rounds": rounds,
            "result": ordered(current),
        }

    def solve(active, parent=None, via="root"):
        index = len(calls)
        row = {
            "index": index,
            "parent": parent,
            "via": via,
            "active": ordered(active),
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
        calls.append(row)
        if not active:
            return [0, 0], index
        maximum = max(priorities[i] for i in range(n) if active >> i & 1)
        player = maximum % 2
        target = sum(
            1 << i for i in range(n) if active >> i & 1 and priorities[i] == maximum
        )
        first, evidence = attract(active, player, target)
        wins, child = solve(active & ~first, index, "without_first_attractor")
        row.update(
            maximum=maximum,
            player=player,
            target=ordered(target),
            first_attractor=evidence,
            first_child=child,
            opponent_seed=ordered(wins[1 - player]),
        )
        if not wins[1 - player]:
            wins[player] |= first
            row["branch"] = "opponent_empty"
        else:
            second, evidence = attract(active, 1 - player, wins[1 - player])
            wins, child = solve(active & ~second, index, "without_second_attractor")
            wins[1 - player] |= second
            row.update(
                second_attractor=evidence,
                second_child=child,
                branch="opponent_dominion",
            )
        assert not wins[0] & wins[1] and wins[0] | wins[1] == active
        row["winning"] = [ordered(w) for w in wins]
        return wins, index

    wins, _ = solve(full)
    catalogs = []
    choices_by_player = []
    for player in (0, 1):
        owned = [i for i in range(n) if owners[i] == player]
        choices = [
            dict(zip(owned, values))
            for values in product(*(range(len(adj[i])) for i in owned))
        ]
        choices_by_player.append(choices)
        policies = []
        for choice in choices:
            retained = [
                [j for k, j in enumerate(adj[i]) if i not in choice or k == choice[i]]
                for i in range(n)
            ]
            thresholds = []
            bad = set()
            for priority in sorted(set(priorities)):
                if priority % 2 == player:
                    continue
                allowed = {i for i in range(n) if priorities[i] <= priority}
                counter = 0
                indices, low, stack, on, components = {}, {}, [], set(), []

                def visit(v):
                    nonlocal counter
                    indices[v] = low[v] = counter
                    counter += 1
                    stack.append(v)
                    on.add(v)
                    for w in retained[v]:
                        if w not in allowed:
                            continue
                        if w not in indices:
                            visit(w)
                            low[v] = min(low[v], low[w])
                        elif w in on:
                            low[v] = min(low[v], indices[w])
                    if low[v] == indices[v]:
                        comp = []
                        while True:
                            w = stack.pop()
                            on.remove(w)
                            comp.append(w)
                            if w == v:
                                break
                        components.append(sorted(comp))

                for i in sorted(allowed):
                    if i not in indices:
                        visit(i)
                components.sort(key=lambda c: c[0])
                records = []
                for comp in components:
                    cyclic = len(comp) > 1 or comp[0] in retained[comp[0]]
                    at_maximum = any(priorities[i] == priority for i in comp)
                    losing = cyclic and at_maximum
                    if losing:
                        bad.update(comp)
                    records.append(
                        {
                            "states": [ns[i] for i in comp],
                            "cyclic": cyclic,
                            "contains_threshold": at_maximum,
                            "losing": losing,
                        }
                    )
                thresholds.append(
                    {
                        "priority": priority,
                        "allowed": [ns[i] for i in sorted(allowed)],
                        "components": records,
                    }
                )
            roots = []
            for root in range(n):
                reached = {root}
                todo = [root]
                for v in todo:
                    for w in retained[v]:
                        if w not in reached:
                            reached.add(w)
                            todo.append(w)
                roots.append(
                    {
                        "state": ns[root],
                        "reachable": [ns[i] for i in sorted(reached)],
                        "bad_reachable": [ns[i] for i in sorted(reached & bad)],
                        "winning": not bool(reached & bad),
                    }
                )
            policies.append(
                {
                    "index": len(policies),
                    "choices": [
                        {"state": ns[i], "action": ss[i]["moves"][choice[i]]["action"]}
                        for i in owned
                    ],
                    "edges": [
                        {"from": ns[i], **m}
                        for i, s in enumerate(ss)
                        for k, m in enumerate(s["moves"])
                        if i not in choice or k == choice[i]
                    ],
                    "thresholds": thresholds,
                    "roots": roots,
                    "winning": [r["state"] for r in roots if r["winning"]],
                }
            )
        canonical = next(
            p["index"]
            for p in policies
            if all(s in p["winning"] for s in ordered(wins[player]))
        )
        catalogs.append(
            {"player": player, "policies": policies, "canonical_policy": canonical}
        )
    pairs = []
    for even, ce in enumerate(choices_by_player[0]):
        for odd, co in enumerate(choices_by_player[1]):
            choice = {**ce, **co}
            roots = []
            for root in range(n):
                path, seen = [], {}
                v = root
                while v not in seen:
                    seen[v] = len(path)
                    path.append(v)
                    v = adj[v][choice[v]]
                cut = seen[v]
                cycle = path[cut:]
                maximum = max(priorities[i] for i in cycle)
                roots.append(
                    {
                        "state": ns[root],
                        "prefix": [ns[i] for i in path[:cut]],
                        "cycle": [ns[i] for i in cycle],
                        "steps": [
                            {"from": ns[i], **ss[i]["moves"][choice[i]]} for i in path
                        ],
                        "maximum": maximum,
                        "winner": maximum % 2,
                    }
                )
            pairs.append({"even_policy": even, "odd_policy": odd, "roots": roots})
    return {
        "schema": "buchilab-parity-v1",
        "convention": "maximum_recurring_priority",
        "input": data,
        "calls": calls,
        "winning": [ordered(w) for w in wins],
        "players": catalogs,
        "joint_policies": pairs,
    }
