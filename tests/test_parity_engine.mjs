import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import { analyzeParity, validateParity } from "../docs/parity-engine.js";
const controls = JSON.parse(
  fs.readFileSync(
    new URL("../docs/parity-controls.json", import.meta.url),
    "utf8",
  ),
);
test("all660 complete native/oracle/browser reports", () => {
  const result = spawnSync(
    process.env.PYTHON || "python",
    [
      "-c",
      'import json;from tools.parity_cases import all_cases;from buchilab.parity import analyze;from buchilab.parity_oracle import verify\nfor c in all_cases():\n r=analyze(c);assert verify(r);print(json.dumps(r,separators=(",",":")))',
    ],
    { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 },
  );
  assert.equal(result.status, 0, result.stderr);
  const reports = result.stdout.trim().split("\n").map(JSON.parse);
  assert.equal(reports.length, 660);
  for (const r of reports) assert.deepEqual(analyzeParity(r.input), r);
});
test("max/min, hidden subcycle, policy closure and parallel action controls", () => {
  const r = analyzeParity(controls[0].input);
  assert.deepEqual(r.winning, [["s0", "s1"], []]);
  assert.deepEqual(
    r.players[0].policies.map((p) => p.winning),
    [[], ["s0", "s1"]],
  );
  assert.deepEqual(analyzeParity(controls[1].input).winning, [
    [],
    ["s0", "s1"],
  ]);
  assert.equal(
    analyzeParity(controls[2].input).joint_policies[0].roots[0].maximum,
    0,
  );
  assert.equal(analyzeParity(controls[8].input).joint_policies.length, 2);
  assert.equal(
    analyzeParity(controls[9].input).joint_policies[0].roots[0].maximum,
    6,
  );
  assert.equal(
    analyzeParity(controls[11].input).calls[0].branch,
    "opponent_dominion",
  );
});
test("strict bounded shape, integer and totality input and immutable data", () => {
  const input = structuredClone(controls[0].input),
    snapshot = structuredClone(input);
  analyzeParity(input);
  assert.deepEqual(input, snapshot);
  for (const value of [true, -1, 8, 2.1, "2", null]) {
    const c = structuredClone(input);
    c.states[0].priority = value;
    assert.throws(() => validateParity(c));
  }
  for (const mutate of [
    (c) => (c.states[0].moves = []),
    (c) => (c.states[0].moves[0].to = "absent"),
    (c) => (c.states[0].extra = 1),
    (c) => (c.extra = 1),
    (c) => (c.states[1].name = "s0"),
  ]) {
    const c = structuredClone(input);
    mutate(c);
    assert.throws(() => validateParity(c));
  }
});
