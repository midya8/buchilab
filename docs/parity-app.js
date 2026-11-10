import { analyzeParity } from "./parity-engine.js";
import { parseJSON } from "./parity-json.js";
const $ = (id) => document.getElementById(id),
  playerName = (p) => (p === 0 ? "Even /0" : "Odd /1"),
  list = (a) => (a.length ? a.join(", ") : "∅");
let report = null,
  controls = [];
function clear(id) {
  $(id).replaceChildren();
}
function text(tag, value, className) {
  const n = document.createElement(tag);
  n.textContent = String(value);
  if (className) n.className = className;
  return n;
}
function options(id, items) {
  clear(id);
  for (const [value, label] of items) {
    const o = text("option", label);
    o.value = String(value);
    $(id).append(o);
  }
}
function card(id, title, body) {
  const c = document.createElement("div");
  c.className = "card";
  c.append(text("strong", title), text("p", body));
  $(id).append(c);
}
function row(id, values) {
  const tr = document.createElement("tr");
  for (const value of values) tr.append(text("td", value));
  $(id).append(tr);
}
const outputIds = [
  "metrics",
  "region-summary",
  "states",
  "call",
  "call-summary",
  "phase",
  "round",
  "attractor-summary",
  "obligations",
  "policy",
  "policy-summary",
  "policy-choices",
  "policy-root",
  "policy-verdict",
  "policy-edges",
  "thresholds",
  "even-policy",
  "odd-policy",
  "joint-root",
  "lasso-verdict",
  "prefix",
  "cycle",
  "joint-steps",
  "json",
];
function invalidate() {
  report = null;
  window.parityReport = null;
  $("results").hidden = true;
  $("download").disabled = true;
  for (const id of outputIds) clear(id);
  $("status").textContent =
    "Input changed. Inspect again to replace all evidence.";
  $("status").className = "";
}
function selectRound() {
  clear("attractor-summary");
  clear("obligations");
  if (!report) return;
  const c = report.calls[Number($("call").value)],
    a = c[$("phase").value];
  if (!a) {
    card(
      "attractor-summary",
      "Empty recursive leaf",
      "Both winning regions are empty. No attractor is computed.",
    );
    return;
  }
  const r = a.rounds[Number($("round").value)];
  card(
    "attractor-summary",
    `${playerName(a.player)} attracts to ${list(a.target)}`,
    `Round ${r.index}: ${list(r.before)} → ${list(r.after)}. Added: ${list(r.added)}. ${r.added.length ? "Continue." : "Unchanged fixed point included."}`,
  );
  for (const q of r.checks)
    row("obligations", [
      q.state,
      q.operator,
      q.moves
        .map(
          (m) =>
            `${m.action} → ${m.to}: ${m.active ? "active" : "removed"} / ${m.in_before ? "in set" : "outside set"}`,
        )
        .join("\n"),
      q.qualifies ? "yes" : "no",
    ]);
}
function selectPhase() {
  clear("round");
  const c = report.calls[Number($("call").value)],
    a = c[$("phase").value];
  if (a)
    options(
      "round",
      a.rounds.map((r) => [
        r.index,
        `${r.index} · before{${list(r.before)}} · +{${list(r.added)}}${r.added.length ? "" : " · fixed point"}`,
      ]),
    );
  selectRound();
}
function selectCall() {
  const c = report.calls[Number($("call").value)];
  clear("call-summary");
  card(
    "call-summary",
    `Call ${c.index} · ${c.branch}`,
    `Parent: ${c.parent === null ? "root" : c.parent}. Entry: ${c.via}. Active: ${list(c.active)}. Maximum: ${c.maximum === null ? "none" : c.maximum}. Player: ${c.player === null ? "none" : playerName(c.player)}.`,
  );
  card(
    "call-summary",
    `Returned Even{${list(c.winning[0])}} / Odd{${list(c.winning[1])}}`,
    `First child: ${c.first_child ?? "none"}. Opponent seed after first recursion: ${list(c.opponent_seed)}. Second child: ${c.second_child ?? "none"}.`,
  );
  options("phase", [
    ["first_attractor", "First: attract to current maximum"],
    ...(c.second_attractor
      ? [
          [
            "second_attractor",
            "Second: opponent attracts to its first-child region",
          ],
        ]
      : []),
  ]);
  $("phase").disabled = !c.first_attractor;
  $("round").disabled = !c.first_attractor;
  selectPhase();
}
function policyRoot() {
  clear("policy-verdict");
  const p =
      report.players[Number($("player").value)].policies[
        Number($("policy").value)
      ],
    r = p.roots[Number($("policy-root").value)];
  card(
    "policy-verdict",
    `${r.state} · ${r.winning ? "wins" : "loses"} under this fixed policy`,
    `Reachable: ${list(r.reachable)}. Reachable losing-cycle states: ${list(r.bad_reachable)}.`,
  );
}
function selectPolicy() {
  for (const id of [
    "policy-summary",
    "policy-choices",
    "policy-edges",
    "thresholds",
  ])
    clear(id);
  const player = Number($("player").value),
    catalog = report.players[player],
    p = catalog.policies[Number($("policy").value)];
  card(
    "policy-summary",
    `${playerName(player)} · policy ${p.index}${p.index === catalog.canonical_policy ? " · canonical uniform winner" : ""}`,
    `Wins from: ${list(p.winning)}. The opponent retains every legal move. A complete policy includes choices even outside its winning region.`,
  );
  if (!p.choices.length)
    card(
      "policy-choices",
      "The sole empty policy",
      "This player owns no states. Every other-player action remains.",
    );
  for (const c of p.choices)
    card("policy-choices", c.state, `Choose ${c.action}.`);
  for (const e of p.edges) row("policy-edges", [e.from, e.action, e.to]);
  if (!p.thresholds.length)
    card(
      "thresholds",
      "No opposite-parity priority exists",
      "Every cycle maximum has this player's parity.",
    );
  for (const t of p.thresholds) {
    const box = document.createElement("div");
    box.className = "card";
    box.append(
      text("strong", `Threshold ${t.priority} · allowed{${list(t.allowed)}}`),
    );
    for (const c of t.components)
      box.append(
        text(
          "p",
          `{${list(c.states)}} · ${c.cyclic ? "cyclic" : "acyclic"} · ${c.contains_threshold ? "contains threshold" : "below threshold"} · ${c.losing ? "LOSING CYCLE" : "not a losing-cycle certificate"}`,
          c.losing ? "no" : "muted",
        ),
      );
    $("thresholds").append(box);
  }
  policyRoot();
}
function selectPlayer() {
  const p = report.players[Number($("player").value)];
  options(
    "policy",
    p.policies.map((q) => [
      q.index,
      `${q.index} · wins{${list(q.winning)}}${q.index === p.canonical_policy ? " · canonical" : ""}`,
    ]),
  );
  selectPolicy();
}
function selectJoint() {
  for (const id of ["lasso-verdict", "prefix", "cycle", "joint-steps"])
    clear(id);
  const e = Number($("even-policy").value),
    o = Number($("odd-policy").value),
    pair = report.joint_policies.find(
      (p) => p.even_policy === e && p.odd_policy === o,
    ),
    r = pair.roots[Number($("joint-root").value)];
  card(
    "lasso-verdict",
    `${r.state} · ${playerName(r.winner)} wins this exact play`,
    `Even policy ${e}, Odd policy ${o}. Recurring maximum ${r.maximum}. Prefix ${r.prefix.length} states; cycle ${r.cycle.length} states.`,
  );
  if (!r.prefix.length)
    card(
      "prefix",
      "Empty prefix",
      "This root is already on the repeated cycle.",
    );
  r.prefix.forEach((v, i) =>
    card(
      "prefix",
      `${i + 1}. ${v}`,
      `Priority ${report.input.states.find((s) => s.name === v).priority}; follow once.`,
    ),
  );
  r.cycle.forEach((v, i) =>
    card(
      "cycle",
      `${i + 1}. ${v}`,
      `Priority ${report.input.states.find((s) => s.name === v).priority}; repeat forever.`,
    ),
  );
  r.steps.forEach((s, i) =>
    row("joint-steps", [
      i + 1,
      s.from,
      s.action,
      s.to,
      i < r.prefix.length ? "prefix" : "cycle",
      report.input.states.find((q) => q.name === s.from).priority,
    ]),
  );
}
function render() {
  const r = report;
  window.parityReport = r;
  $("results").hidden = false;
  $("download").disabled = false;
  $("json").textContent = JSON.stringify(r, null, 2);
  clear("metrics");
  for (const [value, label] of [
    [r.input.states.length, "states"],
    [r.calls.length, "recursive calls"],
    [r.joint_policies.length, "joint policy pairs"],
    [r.players[0].policies.length, "Even policies"],
    [r.players[1].policies.length, "Odd policies"],
    [r.joint_policies.length * r.input.states.length, "exact root lassos"],
  ]) {
    const c = document.createElement("div");
    c.className = "metric";
    c.append(text("strong", value), text("span", label));
    $("metrics").append(c);
  }
  clear("region-summary");
  for (const p of [0, 1])
    card(
      "region-summary",
      playerName(p),
      `Winning region: ${list(r.winning[p])}.`,
    );
  clear("states");
  for (const s of r.input.states) {
    const p = r.winning[0].includes(s.name) ? 0 : 1,
      policy = r.players[p].policies[r.players[p].canonical_policy],
      choice = policy.choices.find((c) => c.state === s.name);
    row("states", [
      s.name,
      s.owner,
      s.priority,
      playerName(p),
      s.moves.map((m) => `${m.action} → ${m.to}`).join("\n"),
      choice ? choice.action : "opponent-owned: all retained",
    ]);
  }
  options(
    "call",
    r.calls.map((c) => [
      c.index,
      `${c.index} · ${c.via} · active{${list(c.active)}} · ${c.branch}`,
    ]),
  );
  selectCall();
  for (const id of ["policy-root", "joint-root"])
    options(
      id,
      r.input.states.map((s, i) => [i, s.name]),
    );
  $("player").value = "0";
  selectPlayer();
  for (const p of [0, 1])
    options(
      p === 0 ? "even-policy" : "odd-policy",
      r.players[p].policies.map((q) => [
        q.index,
        `${q.index} · ${q.choices.map((c) => c.state + ":" + c.action).join(" / ") || "empty policy"}`,
      ]),
    );
  selectJoint();
  $("status").className = "";
  $("status").textContent =
    `Checked ${r.joint_policies.length} complete policy pairs and every root against threshold-cycle certificates. All displayed evidence is current.`;
}
function run() {
  invalidate();
  try {
    report = analyzeParity(parseJSON($("input").value));
    render();
  } catch (e) {
    invalidate();
    $("status").className = "error";
    $("status").textContent = "Invalid input: " + e.message;
  }
}
$("input").addEventListener("input", invalidate);
$("run").addEventListener("click", run);
$("call").addEventListener("change", selectCall);
$("phase").addEventListener("change", selectPhase);
$("round").addEventListener("change", selectRound);
$("player").addEventListener("change", selectPlayer);
$("policy").addEventListener("change", selectPolicy);
$("policy-root").addEventListener("change", policyRoot);
for (const id of ["even-policy", "odd-policy", "joint-root"])
  $(id).addEventListener("change", selectJoint);
$("download").addEventListener("click", () => {
  if (!report) return;
  const url = URL.createObjectURL(
      new Blob([JSON.stringify(report, null, 2) + "\n"], {
        type: "application/json",
      }),
    ),
    a = document.createElement("a");
  a.href = url;
  a.download = "buchilab-parity.json";
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
$("control").addEventListener("change", () => {
  const c = controls[Number($("control").value)];
  $("input").value = JSON.stringify(c.input, null, 2);
  $("control-note").textContent = c.description;
  run();
});
try {
  const response = await fetch("parity-controls.json");
  if (!response.ok) throw Error("Controls unavailable");
  controls = await response.json();
  options(
    "control",
    controls.map((c, i) => [i, c.title]),
  );
  $("control").dispatchEvent(new Event("change"));
} catch (e) {
  $("status").className = "error";
  $("status").textContent = "Controls unavailable: " + e.message;
}
