// Separate browser implementation: set attractors, BFS mutual-reachability classes,
// and functional-policy paths. No network, model or runtime package dependency.
export function validateParity(input) {
  const object = (x, keys) =>
    x !== null &&
    typeof x === "object" &&
    !Array.isArray(x) &&
    Object.keys(x).sort().join("|") === [...keys].sort().join("|");
  const identifier = (x) =>
    typeof x === "string" && /^[A-Za-z][A-Za-z0-9_]{0,15}$/.test(x);
  if (
    !object(input, ["states"]) ||
    !Array.isArray(input.states) ||
    input.states.length < 1 ||
    input.states.length > 6
  )
    throw Error("Exactly one to six states required");
  const names = new Set();
  for (const s of input.states) {
    if (
      !object(s, ["name", "owner", "priority", "moves"]) ||
      !identifier(s.name) ||
      names.has(s.name)
    )
      throw Error("Unique ASCII state identifiers required");
    names.add(s.name);
    if (
      !["even", "odd"].includes(s.owner) ||
      !Number.isInteger(s.priority) ||
      s.priority < 0 ||
      s.priority > 7
    )
      throw Error("Owner even/odd and integer priority0..7 required");
    if (!Array.isArray(s.moves) || s.moves.length < 1 || s.moves.length > 2)
      throw Error("One or two moves per state; dead ends rejected");
    const actions = new Set();
    for (const m of s.moves) {
      if (
        !object(m, ["action", "to"]) ||
        !identifier(m.action) ||
        actions.has(m.action) ||
        typeof m.to !== "string"
      )
        throw Error("Unique per-state ASCII action identifiers required");
      actions.add(m.action);
    }
  }
  for (const s of input.states)
    for (const m of s.moves)
      if (!names.has(m.to)) throw Error("Every target must be declared");
  return JSON.parse(JSON.stringify(input));
}

export function analyzeParity(input) {
  const data = validateParity(input),
    states = data.states,
    names = states.map((s) => s.name),
    rows = new Map(states.map((s) => [s.name, s])),
    owner = (v) => (rows.get(v).owner === "even" ? 0 : 1),
    priority = (v) => rows.get(v).priority,
    order = (set) => names.filter((v) => set.has(v));
  const calls = [];
  function attract(active, player, seed) {
    let current = new Set(seed);
    const rounds = [];
    for (;;) {
      const next = new Set(current),
        checks = [];
      for (const v of order(active)) {
        const s = rows.get(v),
          activeMoves = s.moves.filter((m) => active.has(m.to));
        if (!activeMoves.length) throw Error("Recursive subgame not total");
        const qualifies =
          owner(v) === player
            ? activeMoves.some((m) => current.has(m.to))
            : activeMoves.every((m) => current.has(m.to));
        if (qualifies) next.add(v);
        checks.push({
          state: v,
          operator: owner(v) === player ? "exists" : "all",
          moves: s.moves.map((m) => ({
            ...m,
            active: active.has(m.to),
            in_before: current.has(m.to),
          })),
          qualifies,
        });
      }
      rounds.push({
        index: rounds.length,
        before: order(current),
        after: order(next),
        added: order(new Set([...next].filter((v) => !current.has(v)))),
        checks,
      });
      if (next.size === current.size)
        return {
          result: current,
          evidence: {
            player,
            target: order(seed),
            rounds,
            result: order(current),
          },
        };
      current = next;
    }
  }
  function solve(active, parent = null, via = "root") {
    const index = calls.length,
      call = {
        index,
        parent,
        via,
        active: order(active),
        maximum: null,
        player: null,
        target: [],
        first_attractor: null,
        first_child: null,
        opponent_seed: [],
        second_attractor: null,
        second_child: null,
        branch: "empty",
        winning: [[], []],
      };
    calls.push(call);
    if (!active.size) return { regions: [new Set(), new Set()], index };
    const maximum = Math.max(...[...active].map(priority)),
      player = maximum % 2,
      target = new Set([...active].filter((v) => priority(v) === maximum)),
      first = attract(active, player, target),
      rest = new Set([...active].filter((v) => !first.result.has(v)));
    let sub = solve(rest, index, "without_first_attractor"),
      regions = sub.regions;
    Object.assign(call, {
      maximum,
      player,
      target: order(target),
      first_attractor: first.evidence,
      first_child: sub.index,
      opponent_seed: order(regions[1 - player]),
    });
    if (regions[1 - player].size) {
      const second = attract(active, 1 - player, regions[1 - player]);
      sub = solve(
        new Set([...active].filter((v) => !second.result.has(v))),
        index,
        "without_second_attractor",
      );
      regions = sub.regions;
      for (const v of second.result) regions[1 - player].add(v);
      Object.assign(call, {
        second_attractor: second.evidence,
        second_child: sub.index,
        branch: "opponent_dominion",
      });
    } else {
      for (const v of first.result) regions[player].add(v);
      call.branch = "opponent_empty";
    }
    call.winning = regions.map(order);
    return { regions, index };
  }
  const winning = solve(new Set(names)).regions.map(order);
  const owned = [0, 1].map((p) => names.filter((v) => owner(v) === p));
  const choices = owned.map((vertices) => {
    let list = [new Map()];
    for (const v of vertices)
      list = list.flatMap((d) =>
        rows.get(v).moves.map((_, k) => new Map([...d, [v, k]])),
      );
    return list;
  });
  const reachable = (root, edges, allowed) => {
    const visited = new Set([root]),
      queue = [root];
    for (let i = 0; i < queue.length; i++)
      for (const e of edges)
        if (e.from === queue[i] && allowed.has(e.to) && !visited.has(e.to)) {
          visited.add(e.to);
          queue.push(e.to);
        }
    return visited;
  };
  const players = [0, 1].map((player) => {
    const policies = choices[player].map((decision, index) => {
      const edges = states.flatMap((s) =>
          s.moves
            .filter(
              (_, k) => !decision.has(s.name) || decision.get(s.name) === k,
            )
            .map((m) => ({ from: s.name, ...m })),
        ),
        bad = new Set(),
        thresholds = [];
      for (const t of [...new Set(states.map((s) => s.priority))].sort(
        (a, b) => a - b,
      )) {
        if (t % 2 === player) continue;
        const allowed = new Set(names.filter((v) => priority(v) <= t)),
          reach = new Map(
            [...allowed].map((v) => [v, reachable(v, edges, allowed)]),
          ),
          done = new Set(),
          components = [];
        for (const v of order(allowed)) {
          if (done.has(v)) continue;
          const group = order(allowed).filter(
            (w) => reach.get(v).has(w) && reach.get(w).has(v),
          );
          for (const w of group) done.add(w);
          const cyclic =
              group.length > 1 || edges.some((e) => e.from === v && e.to === v),
            contains_threshold = group.some((w) => priority(w) === t),
            losing = cyclic && contains_threshold;
          if (losing) for (const w of group) bad.add(w);
          components.push({
            states: group,
            cyclic,
            contains_threshold,
            losing,
          });
        }
        thresholds.push({ priority: t, allowed: order(allowed), components });
      }
      const roots = names.map((v) => {
        const reached = reachable(v, edges, new Set(names)),
          bad_reachable = order(
            new Set([...reached].filter((w) => bad.has(w))),
          );
        return {
          state: v,
          reachable: order(reached),
          bad_reachable,
          winning: !bad_reachable.length,
        };
      });
      return {
        index,
        choices: owned[player].map((v) => ({
          state: v,
          action: rows.get(v).moves[decision.get(v)].action,
        })),
        edges,
        thresholds,
        roots,
        winning: roots.filter((r) => r.winning).map((r) => r.state),
      };
    });
    const canonical_policy = policies.findIndex((p) =>
      winning[player].every((v) => p.winning.includes(v)),
    );
    if (canonical_policy < 0) throw Error("No uniform positional winner");
    return { player, policies, canonical_policy };
  });
  const joint_policies = [];
  choices[0].forEach((even, ei) =>
    choices[1].forEach((odd, oi) => {
      const decision = new Map([...even, ...odd]),
        roots = names.map((root) => {
          const path = [],
            seen = new Map();
          let v = root;
          while (!seen.has(v)) {
            seen.set(v, path.length);
            path.push(v);
            v = rows.get(v).moves[decision.get(v)].to;
          }
          const boundary = seen.get(v),
            cycle = path.slice(boundary),
            maximum = Math.max(...cycle.map(priority));
          return {
            state: root,
            prefix: path.slice(0, boundary),
            cycle,
            steps: path.map((w) => ({
              from: w,
              ...rows.get(w).moves[decision.get(w)],
            })),
            maximum,
            winner: maximum % 2,
          };
        });
      joint_policies.push({ even_policy: ei, odd_policy: oi, roots });
    }),
  );
  // A separate bounded universal-opponent check catches policy/certificate drift.
  for (const player of players)
    for (const policy of player.policies) {
      const pairs = joint_policies.filter(
        (j) =>
          (player.player === 0 ? j.even_policy : j.odd_policy) === policy.index,
      );
      const expected = names.filter((v) =>
        pairs.every(
          (j) => j.roots.find((r) => r.state === v).winner === player.player,
        ),
      );
      if (JSON.stringify(expected) !== JSON.stringify(policy.winning))
        throw Error("Policy SCC certificate disagrees with lasso atlas");
    }
  return {
    schema: "buchilab-parity-v1",
    convention: "maximum_recurring_priority",
    input: data,
    calls,
    winning,
    players,
    joint_policies,
  };
}
