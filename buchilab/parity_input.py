"""Strict bounds for fully visible finite total max-parity games."""

import re


def validate(data):
    if type(data) is not dict or set(data) != {"states"}:
        raise ValueError("input must contain exactly states")
    rows = data["states"]
    if type(rows) is not list or not 1 <= len(rows) <= 6:
        raise ValueError("one to six states required")
    names = []
    for row in rows:
        if type(row) is not dict or set(row) != {"name", "owner", "priority", "moves"}:
            raise ValueError("state keys must be name, owner, priority, moves")
        name = row["name"]
        if (
            type(name) is not str
            or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,15}", name)
            or name in names
        ):
            raise ValueError("unique ASCII state identifiers required")
        names.append(name)
        if row["owner"] not in ("even", "odd") or type(row["owner"]) is not str:
            raise ValueError("owner must be even or odd")
        if type(row["priority"]) is not int or not 0 <= row["priority"] <= 7:
            raise ValueError("priority must be an integer from zero to seven")
        if type(row["moves"]) is not list or not 1 <= len(row["moves"]) <= 2:
            raise ValueError("one or two moves required; dead ends rejected")
        actions = []
        for move in row["moves"]:
            if type(move) is not dict or set(move) != {"action", "to"}:
                raise ValueError("move keys must be action and to")
            action = move["action"]
            if (
                type(action) is not str
                or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,15}", action)
                or action in actions
            ):
                raise ValueError("unique per-state ASCII action identifiers required")
            actions.append(action)
            if type(move["to"]) is not str:
                raise ValueError("move target must be a state identifier")
    if any(m["to"] not in names for s in rows for m in s["moves"]):
        raise ValueError("move target must be declared")
    return {
        "states": [
            {
                "name": s["name"],
                "owner": s["owner"],
                "priority": s["priority"],
                "moves": [dict(m) for m in s["moves"]],
            }
            for s in rows
        ]
    }
