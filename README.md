# BuchiLab

**A winning state is not a winning policy.** A fully visible tiny adversarial repeated-goal game inspector. All nested fixed-point obligations, progress ranks, complete controller policies and reachable non-goal cycles. Independent Python/JavaScript and a separate joint-policy lasso oracle. No model or API.

[Interactive inspector](https://midya8.github.io/buchilab/) | [Exact semantics and seven-source ledger](METHOD.md) | [Generator](buchilab/core.py) | [Independent checker](buchilab/verify.py)

## The failure

Idle can wait forever or visit goal, which returns to idle. Both states are winning, but a controller policy that keeps choosing wait loses. A winning region alone is not a permissive policy. Rank-guided progress works; inspect the failing and working complete policies side by side through the selector.

Other original controls show a goal reached only once, environment starvation without fairness, the same graph with controller ownership, a six-state repeated return cycle, every-state goals and no goals.

## What is visible

- Every outer greatest-fixed-point iteration and inner least-fixed-point update, including unchanged final rounds.
- Every state's exists/all obligation, goal-dependent outer/inner scope and every move's membership test.
- Final inner ranks, every sufficient rank-permitted move and a complete canonical controller strategy.
- Every positional controller policy, all retained environment edges, all cyclic non-goal SCCs and every root's reachable bad-cycle vertices.
- Full JSON export and strict bounded atomic native CLI. Independent checker replays with sets/Floyd reachability and checks every joint positional-policy pair by its eventual lasso, without calling the generator.

## Run

Python 3.10+; no runtime dependency. Node 22+ and Chrome for optional browser tests.

```sh
python -m unittest discover -s tests -v
npm test
bash tools/check_wheel.sh
python -m buchilab arena.json --output report.json
python -m buchilab report.json --verify
python -m http.server 8000 --directory docs
```

Input: exactly `states`, one to six `{name, owner, goal, moves}` records. Each needs one to three `{action, to}` moves; action labels unique within state, declared targets only. Dead ends rejected. Explicit self-loops are a modeling choice. Goals are strict booleans. Complete schema, rank conventions and ordering in [METHOD.md](METHOD.md).

Nine native tests cover all 21,952 three-state graph/owner/goal combinations, 140 seeded larger games, maximum 729 policies and forged-certificate families. Three Node/actual-Chrome tests compare 331 complete reports and every control record at 320/390/1280. Installed wheels replay seven controls through module and console CLI outside checkout. These are tests, not formal proof.

## Limits

Finite total perfect-information turn-based recurrence, not safety or completion. No fairness assumption: an available environment action need never be taken. Not a deployed shield, learned abstraction, LLM guarantee, LTL compiler, stochastic/concurrent/generalized-Buchi solver, new algorithm or scalable benchmark. Original code/fixtures; standard game theory attributed.

## Action-level failure lassos

[Repeat the actual failure](https://midya8.github.io/buchilab/lassos.html) | [Witness contract, checks and source notes](LASSOS.md)

For every failing fixed controller policy and root, inspect the exact prefix once and non-goal cycle forever, with owner and action provenance. A separate report/API/CLI preserves the base v1 contract. Empty prefixes, nonempty self-loops, multiedge cycles, unreachable bad components and duplicate-target action choices are explicit. BFS generation is independently checked with bounded simple walks plus the joint-policy lasso oracle. These are per-policy counterexamples, not a uniform spoiling strategy for the whole game. Sixteen native and five Node/Chrome tests preserve all original tests.


## Max-parity games: the maximum that keeps returning

[Parity inspector](https://midya8.github.io/buchilab/parity.html) | [Exact contract, derivation and inspected sources](PARITY.md)

Separate six-state/two-move max-recurring-priority games, preserving every old goal and lasso workflow. Inspect classic Zielonka recursion, every synchronous attractor test, both players' complete policies, threshold-induced losing-cycle SCCs and every joint-policy/root lasso. A winning region does not certify a policy; a maximal SCC with an even maximum can still hide an odd self-loop. Prefix priorities do not decide a recurring winner.

Separate bitmask/Tarjan, set/Floyd/policy-pair and browser BFS implementations agree on660 complete reports. Actual pinned Oink runs three solver families with preprocessing disabled,1,980 solver runs and660 separately verified native canonical strategy certificates. Twelve original controls, strict atomic `buchilab-parity` / `python -m buchilab.parity_cli`, actual Chrome trusted-download tests and fresh-wheel origin checks. No new theory, scale, fairness or real-agent guarantee. Full counts and caveats in [PARITY.md](PARITY.md).
