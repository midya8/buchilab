# BuchiLab 0.3: the maximum that keeps returning

Inspect small finite games where the highest priority recurring forever decides the winner. The page shows recursive region solving, complete policies and each policy pair's eventual cycle. It implements established parity-game theory, not a new or scalable solver. The original repeated-goal API, v1 schema and action-lasso workflow remain separate.

## A winning region can contain a losing policy

The default has two states. Even owns `s0` with priority 1 and can `wait` at `s0` or `visit` `s1`. Odd owns `s1` with priority 2 and has the forced `return` to `s0`. Even wins from both states by repeatedly visiting 2. But the complete policy choosing wait loses from both roots: eventually only 1 recurs. A winning region does not make every region-preserving policy winning.

The second control changes ownership, not the graph: Odd owns the priority 1 choice and can remain there forever. The full maximal strongly connected component has even maximum 2, yet an odd self-loop remains available inside it. Looking only at the maxima of maximal SCCs would incorrectly certify Even. We inspect threshold-induced SCCs instead.

A separate control has a priority 7 finite prefix leading to a priority 0 self-loop. Even wins. The maximum of a finite prefix is not the maximum recurring infinitely often.

## Exact input and ordering

Input is exactly `{ "states": [...] }`, with one to six ordered records:

```json
{"name":"s0","owner":"even","priority":1,"moves":[
  {"action":"wait","to":"s0"},
  {"action":"visit","to":"s1"}
]}
```

The record is illustrative and needs its declared target `s1` in the full arena.

- Every state has exactly name, owner, priority and moves. Owner is `even` or `odd`.
- Priority is a strict integer 0..7; Python booleans are not integers here. Browser JSON parsing rejects decimal/exponent numeric syntax to match the strict native validator rather than silently converting `2.0` into an integer.
- Names and action labels are ASCII `[A-Za-z][A-Za-z0-9_]{0,15}`. State names are unique; actions are unique within each source state.
- Every state has one or two named moves to declared states. Parallel actions to the same destination remain distinct policy choices. Dead ends are rejected, not silently totalized.
- State order and move order are preserved. Sets are serialized in state order. Policies use lexicographic move-index product order over that player's owned states in state order. A player with no states has one empty policy.
- Joint policies are ordered Even policy first, then Odd policy. Every root is included in state order.
- The largest policy-pair atlas has 64 pairs, not 64 squared: the product of both players' choices equals the product over all at most six two-move states. There are at most 384 root lassos. A player's full catalog may have 64 complete policies.

Native generation input is capped at 65,536 bytes; verification input at 8MiB. Duplicate keys and nonfinite JSON are rejected. Browser input has the same 65,536-byte bound and duplicate-key checks. Parse, schema or verification failure never replaces an existing output file. Output is written atomically in the destination's directory. Changing browser input removes every previous result and disables export immediately; invalid input cannot leave stale evidence visible.

## Game semantics: MAX, not MIN

The graph is finite and total. A token starts at a chosen state. Its owner chooses a legal move and play continues forever. For an infinite play, consider precisely the priorities occurring infinitely often. This set is nonempty and finite. Even wins when its largest member is even; Odd wins otherwise. There are no draws.

`convention: "maximum_recurring_priority"` is part of every report. Sources use both conventions: Willemse's 2018 lecture minimizes the recurring priority; PGSolver, the 2018 BDD report and Oink maximize. We choose maximum throughout. To reflect a max game into the equivalent min game, choose an **even** upper bound M and replace priority p with M-p. An odd M flips priority parity. Merely relabeling distinct priorities consecutively can change the game unless both order and parity are preserved. We do not silently compress or reflect user input.

Finite parity games have positional determinacy: each state belongs to exactly one winning region, and each player has one memoryless strategy winning from every state in its region. This theorem justifies the complete positional-policy oracle below; finite-horizon testing would not.

## Region generator: classic Zielonka recursion

The generator uses bitmasks. Each recursive call records its parent, entry branch, complete active subgame, maximum priority, corresponding player, first and second attractor evidence, child indices, opponent seed and returned regions. Empty recursive leaves are explicit.

For active subgame H:

1. If H is empty, return two empty regions.
2. Let m be the greatest active priority, a=m mod 2 and U the states with priority m.
3. Compute A=Attr_a^H(U), and recursively solve H minus A.
4. If that child's opponent region W_(1-a) is empty, player a wins all of H. Add A to its returned region.
5. Otherwise compute B=Attr_(1-a)^H(W_(1-a)) in the **original active H**, not only H minus A. Recursively solve H minus B; add B to the opponent's second-child region.

We implement the classic two-recursion form in the 2018 technical report, not Oink's optimized variant that can sometimes avoid a second recursion when no new state is attracted. The report calls this branch `opponent_dominion`, not a claim that all of A belongs to either player before the second call.

### Every synchronous attractor obligation

An attractor starts at its target. From current set X, a state owned by the attracting player qualifies when **some** active successor lies in X; a state owned by the other player qualifies when **every** active successor lies in X. All qualifications are evaluated against the previous X, and only then are they added together.

Every round includes before/after/added sets, every active state's exists/all test, every original named move, whether its target is active and whether it belongs to the previous X. Removed moves are visible but excluded from the quantifier. The seed is retained even if a seed state does not pass its predecessor test. The final unchanged round is included. Attractor complement subgames remain total; both native implementations and browser assert this rather than relying on empty universal quantifiers.

## Complete-policy certificates: threshold SCCs, not one SCC maximum

For each player, enumerate every complete positional policy. Fix its named action at every owned state and retain all opponent moves. This includes choices outside the player's winning region; no policy is silently truncated to one root.

For each priority t whose parity is the other player's, keep only states with priority at most t in the fixed-policy graph. Compute every SCC, including acyclic singletons. A component is a losing-cycle certificate exactly when it is cyclic and contains a state with priority t. Cyclic means at least two mutually reachable states or an actual self-loop, not reflexive reachability by itself.

Why this is exact: a cyclic strongly connected component containing a priority-t state admits a closed walk returning to that state, with maximum t. Conversely, a losing recurring cycle with maximum t is present in this threshold-induced graph. This detects smaller odd cycles inside even-maximal full components, and symmetrically smaller even cycles for an Odd policy.

A root loses under the fixed policy exactly when it reaches one of these losing-cycle states in the **full retained graph**, not the threshold-induced graph. A finite prefix may cross higher priorities before settling on a lower losing cycle. Each policy includes all retained action edges, every threshold's allowed states and SCC classification, and every root's reachable and bad-reachable sets.

The generator uses Tarjan SCCs and forward reachability. The checker reconstructs SCC classes with a separate positive-length Floyd relation; a diagonal is not introduced unless a real cycle exists. The browser uses per-state BFS and mutual-reachability classes. Shared schema and written semantics are disclosed; these implementations are not three independent theories.

### Canonical uniform policy

After computing regions, choose the first complete policy that wins from every state in that player's region. The independent oracle confirms one exists. This is bounded exhaustive strategy extraction, not a claim that the recursive region solver directly constructs its strategy. For an empty region the first complete policy is a vacuous uniform choice and is labeled accordingly by its empty winning region. A complete policy can win additional states only if those states are already in that player's true region.

## Independent joint-policy oracle and lasso atlas

Choose one complete positional policy for each player. Every source now has exactly one selected named move, so every root has a unique path. Follow until the first repeated state. The preceding states form the finite prefix; the suffix from that state's first occurrence is the nonempty recurring cycle. There is no extra repeated closing state in the cycle array. The last step returns to its first state. Every step retains from/action/to provenance.

Only the cycle's maximum priority determines its winner. Parallel actions remain distinct policy choices even if their paths coincide. Empty prefixes, single-state cycles and forced multi-state cycles are included.

For each fixed policy of player p, a root is winning exactly when **every** joint pair with that policy has lasso winner p. Union those roots over that player's policies to obtain its winning region. The independent checker confirms these regions agree with its set-based recursive solver, and that each policy's universal-opponent result agrees with its Floyd threshold certificate. The browser also cross-checks each displayed policy against every compatible joint-policy lasso. This exact oracle is small-bound exhaustive evidence, not a scale claim.

## Complete-report verification

`buchilab.parity_oracle.verify` reconstructs the entire canonical report with separate set recursion, positive-length Floyd threshold classes and functional-path policy pairs. It never calls the generator. It compares canonical JSON, preserving bool/int/null/string distinctions, ordering and exact keys. Mutating the input and recomputing a valid report is a different valid request, not a forgery claim.

Every noninput primitive leaf in the original default report is separately altered and rejected: 207 mutations. Structural/type/order/truncation forgeries are tested separately. Fresh installed wheels test 24 direct forgeries and 48 atomic CLI forgeries through two entrypoints, in addition to the retained old workflows.

## Run and reproduce

Python 3.10+ with no runtime package dependency. Node 22+ and actual Chrome for browser tests. CMake/C++/Git and network are needed only for optional external Oink reproduction.

```sh
python -m unittest discover -s tests -v
npm test
bash tools/check_wheel.sh
python -m buchilab.parity_cli arena.json --output report.json
python -m buchilab.parity_cli report.json --verify
buchilab-parity arena.json --output report.json
python -m http.server 8000 --directory docs
```

Open `parity.html`. The old `python -m buchilab`, `buchilab` console command, `buchilab.witness` and old pages/schemas remain supported. Reports use separate `buchilab-parity-v1`.

### Checked corpus and limits of the checks

- 660 complete native/oracle/browser reports: 576 exhaustive two-state arenas (four priorities, both owners, every nonempty simple successor subset), 72 seeded arenas with seed 73519 and twelve original controls.
- 1,907 recursive calls,1,672 attractor rounds,1,926 complete player policies,1,403 joint policies and 3,711 root lassos across that corpus.
- 31 Python tests, retaining sixteen original/lasso tests and adding fifteen parity tests. Nine Node/Chrome tests after adding three parity-engine tests and one actual-browser test to the old five.
- Actual Chrome: 36 control/width reports at 1280/390/320,117 recursive call selections,126 attractor rounds,333 displayed predecessor rows,114 policies,309 policy-root selections,273 threshold components,327 joint-root lassos and 696 action steps. Twelve downloads use actual trusted mouse events and completed file bytes, then the native checker, not a patched anchor or intercepted blob.
- Fresh installed wheels assert nine module origins under site-packages, twelve parity controls through module and console entrypoints,24 direct and 48 atomic CLI forgeries. The original seven goal controls and ten action-lasso controls are retained.

Counts describe this deterministic corpus, not all six-state games and not a formal proof. Input bounds make full policy enumeration feasible. No benchmark, scale, causal performance or production guarantee follows.

## Actual external reference: Oink, pinned and executed

Inspected and separately built Oink 1.1.0 source commit `db336a53e6a1b2dc12ab89b58d1871fe565d0147`, with Lace 2.6.0 commit `a091978dc4479fc3b9bc7af7dc77939ec8587c44`. Current Lace needs CMake 3.23 or newer; the optional script uses isolated CMake 3.31.10. The upstream README mentions Boost, but this pinned CMake build does not require it. The pinned bundled cxxopts header omits `<cstdint>` and failed on the newer hosted compiler. The build script explicitly preincludes this standard header with `-include cstdint`, without changing the pinned source trees or external checker. The original CI failure is retained; local and final CI results are reported separately.

```sh
# Builds both pinned sources and runs the real reference, no vendored copy:
bash tools/build_parity_reference.sh
# Or use an already built binary:
OINK_BIN=/path/to/oink python tools/check_parity_reference.py
```

All 660 corpus games are serialized in PGSolver format. Run three distinct Oink solver families, `--zlk`, `--spm` and `--tl`, with `--no` preprocessing and `-v` verification. 1,980 actual solver executions agree on 3,960 regions. Separately serialize our canonical uniform strategies and supplied region partition as a full solution; Oink's verifier accepts all 660 certificates without asking Oink to choose those policies. A known wrong wait policy in the default game is separately rejected by the actual verifier. External evidence is for winning regions and canonical strategies, not our JSON validator, attractor trace, naming/order contract or proof of parity-game theory. Shared standard theory remains shared.

## Inspected source ledger

All used claims came from fetched full text or actual pinned source, not search snippets. Sources use differing conventions; that conflict is preserved above.

| Source | Type/date | What was used | Limit |
| --- | --- | --- | --- |
| [Sanchez, Wesselink, Willemse: BDD-Based Parity Game Solving](https://pure.tue.nl/ws/files/92755535/CSR_18_01.pdf) | Primary technical report 18/01, March 2018 | Finite total max-parity model, positional determinacy, attractors, classic Algorithm 1 Zielonka | BDD performance results do not describe this toy explicit inspector |
| [Friedmann, Lange: PGSolver manual](https://timw.win.tue.nl/downloads/amc2014/pgsolver.pdf) | Solver technical manual, March 5 2014 | Max/min even reflection, uniform positional strategies, region closure and strategy verification | PGSolver itself was not installed or executed here |
| [Tim Willemse: AMC lecture 7](https://timw.win.tue.nl/downloads/amc2018/lecture%207.pdf) | University teaching, 2018 course | Attractor rounds, closed sets, dominions, recursive reasoning | MIN convention, deliberately not copied unchanged |
| [MERC Zielonka documentation](https://mercorg.github.io/merc-website/developer/symbolic/zielonka/) | Project technical docs, undated | Explicit max/min distinction and recursive overview | Rendered algorithm math incomplete; exact steps grounded in primary report |
| [Hartmut Klauck: Algorithms for Parity Games](https://www.labri.fr/perso/anca/Games/Stockholm17/ch7.pdf) | Textbook chapter, 2002 | Positional pair enumeration and eventual cycle oracle | Historical complexity discussion is not a current-best claim |
| [Certification for mu-calculus with winning strategies](https://spinroot.com/spin/Workshops/ws16/SPIN_2016_paper_21.pdf) | Primary SPIN 2016 paper | A good maximal SCC can hide bad subcycles; strategy certification via refined SCCs | This project implements bounded threshold classes, not that paper's full mu-calculus system |
| [Tom van Dijk: Oink paper](https://arxiv.org/html/1801.03859) | Primary TACAS 2018 paper/arXiv March 5 2018 | Max-parity semantics, actual solver families and optimized Zielonka variants | Our region recursion is the classic form, not those optimizations |
| [Oink maintainer repository](https://github.com/trolando/oink) | Actual inspected pinned source | CLI, CMake, algorithms, solution parser/verifier; real execution above | External dependency optional, not a runtime package or vendored source |

## Outside the contract

No dead-end finite-game convention, stochastic/concurrent/partial-observation game, fairness-added game, temporal-logic compiler, strategy learning, model-serving, real-world control guarantee, arbitrary-policy permissiveness theorem, novel solver, scalable symbolic backend or formal machine-checked proof. A full policy catalog is bounded enumeration. Original goal and action-lasso semantics are not silently generalized.

CI cancels superseded runs per workflow/ref. Push and pull-request refs remain distinct, so the final feature-push and PR checks each run and must each pass before merge. This avoids obsolete intermediate editor commits occupying the queue, not a replacement for exact final-head checks.
