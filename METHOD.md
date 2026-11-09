# Repeated-goal games with every fixed-point and policy obligation

## Exact model

Input is exactly `{states: [...]}`, with one to six records containing exactly `name`, `owner`, `goal`, `moves`. Names/action labels are ASCII identifiers of at most 16 characters. Owners are controller/environment; goal is a JSON boolean. Every state has one to three deterministic moves `{action, to}` with unique action labels locally and declared targets. Different actions may share a target. No dead ends: missing moves are rejected, never silently completed. Explicit self-loops are a modeling decision. Ownership need not alternate strictly.

Plays are infinite paths. The controller wins from a root if it has a strategy such that every environment response visits a goal state infinitely often. All states are analyzed as roots. There is no fairness restriction: an environment that always has a deliver edge can still wait forever. One goal visit, safe waiting, reward and task completion are different objectives. Empty goals lose everywhere; every-state goals win everywhere. Initial goal membership alone is not a winning certificate.

## Nested fixed points

Define Pre(X) as controller states with some successor in X, and environment states with all successors in X. Let F be goal states. Compute the greatest fixed point Z of the least fixed point Y of:

`(F intersect Pre(Z)) union ((V minus F) intersect Pre(Y))`.

Start outer Z = V; for each outer candidate restart inner Y = empty. Every update is synchronous. Each inner report includes previous/next sets, newly added states, every state quantifier, which set its goal flag selects, and every move's selected-set membership. After the inner loop stabilizes, replace Z with Y and record removed states. Both final unchanged inner and outer updates are included. Indices start at zero. Input order determines set serialization and move order.

The piecewise goal/non-goal form is the Boolean instance of the formula in Grädel, Lücking and Naaf, Section 5. This is not the distinct polynomial semiring/provenance computation in that paper. Standard finite monotone fixed-point theory supplies termination; testing is not a formal proof of the implementation.

## Rank strategy and a permissiveness failure

In the final outer iteration, a state's inner rank is the one-based update on which it first enters Y; losing states have null rank. Goal states that win enter at rank one. At a winning non-goal controller state, choose any move with a lower-rank winning target. At a winning goal state, choose any winning target. At winning environment states, every move satisfies the corresponding condition. A non-goal rank r guarantees a goal within at most r - 1 moves under this rank strategy. A move from a goal resets the rank, so that goal's rank one does not bound the time to the next goal. If R is the largest winning rank, gaps between goal visits under the rank strategy are at most R moves. No fastest-policy claim is made.

Every rank-permitted move is shown, but this is a sufficient policy family, not every winning policy. Canonical controller choice is the first rank-permitted input action at each winning controller state. To obtain a complete positional policy, losing controller states take their first action. `canonical_policy` is the first enumerated complete policy agreeing with those winning-state choices.

Staying inside the winning region does not by itself guarantee recurrence. In the first control, both idle and goal are winning, yet choosing idle's self-loop forever loses. Both targets are winning; only visit is rank-permitted. The UI deliberately defaults to the working rank policy but lets the reader inspect the failing complete policy as well.

## Every positional policy, independently audited

A complete positional controller policy fixes one action at every controller state, including unreachable or losing states. Policies are enumerated lexicographically by input state/action order, with last controller state changing fastest. No controller states means one empty controller policy. Duplicate-target action choices remain distinct policies. There can be up to 3^6 = 729 policies.

For each policy, retain its chosen controller edges and every environment edge. Compute SCCs of the **non-goal induced graph**. A component is cyclic if it has at least two vertices or a self-loop. Components and their vertices are ordered by original state index. For every root, show all reachable states in the full retained graph and all reachable cyclic non-goal vertices. The root wins under that policy exactly when none are reachable. Cycles need not be bottom SCCs in the full graph: an adversarial environment may ignore an exit. Prefix paths may visit goals before reaching a bad cycle; this is why full-graph reachability is used before testing non-goal recurrence.

The generator uses bitmask fixed points, Tarjan SCCs and BFS full reachability. JavaScript uses explicit sets and graph-search reachability/mutual reachability instead. The separate native checker independently replays fixed points with sets and reconstructs cyclic components through Floyd transitive closure. In addition it enumerates every joint controller/environment positional-policy pair, follows each root until the first repeated state and checks whether that exact eventual cycle contains a goal. This independent lasso oracle must agree for every controller policy. The union of controller-policy winning roots must equal the nested-fixed-point winning region, and the canonical rank policy must win from that entire region. Joint policies number at most 3^6 as ownership partitions the states, not 3^12. No claim to enumerate all history-dependent strategies is made. Memoryless determinacy for finite turn-based Buchi games is the reason positional policies suffice for the winning region.

The checker never calls the generator; it shares only input validation. It checks exact full report shape, order, values and primitive types, rejecting booleans substituted for integer indices/ranks. This is independent algorithmic evidence, not independent authorship or formal verification.

## Reproduction evidence

Nine native tests pass Python 3.10-3.13. They include all 21,952 three-state total distinct-target directed graphs with every ownership and goal subset, 140 seeded one-to-six-state games, the maximum 729-policy/duplicate-target case, original owner-flip/once-versus-recurrence controls, every report-family forgery, strict types, checker with solver disabled, input immutability, ordering, dead-end/schema rejection and strict atomic CLI failure cases.

Three Node/actual-Chrome tests pass. Python and JavaScript match 331 complete reports: 564 outer iterations, 1,084 inner updates, 3,482 state obligations, 1,048 complete controller policies, 4,132 policy-root verdicts, 5,339 retained edges and 765 cyclic components. Browser checks all seven controls, every displayed record and JSON/export/invalid-input clearing/overflow at 320/390/1280. Controls contain 12 outer iterations, 26 inner updates, 83 obligations, 95 round moves, 18 state verdicts, 22 state moves, nine policies, 15 choices, 24 retained edges, five components and 22 policy-root verdicts. Installed-wheel replay checks seven controls through both CLI entry points outside checkout and four installed module origins.

Report schema is `buchilab-v1`. Native input limit 64 KiB; verification-report limit 8 MiB. Duplicate keys and nonfinite constants are rejected. Invalid input does not replace an existing output; writes use atomic replacement. Browser JSON.parse uses normal last-key-wins parsing before bounded validation, unlike the native duplicate-key rejection. Editable inputs stay local; static page assets and controls are loaded, but no user-entered graph is sent to a service.

## Inspected source ledger

Inspected November 9, 2026. Original implementation, UI and controls. Established mathematical ideas are attributed rather than claimed as new.

| Source | Type | What it supports and what is not implemented |
| --- | --- | --- |
| [Chatterjee, Henzinger and Piterman, Algorithms for Büchi Games](https://arxiv.org/html/0805.2620), 2008 | Primary research paper | Finite turn-based objective and classical memoryless determinacy, Section 2; classical attractor-removal context. No paper-specific optimized algorithm or complexity improvement. |
| [Grädel, Lücking and Naaf, Semiring Provenance for Büchi Games](https://lmcs.episciences.org/13205/pdf), LMCS 20(1), published March 8, 2024 | Primary research paper | Section 5's greatest/least fixed-point formula in its Boolean instance, positional-strategy versus richer-strategy distinctions. No absorptive polynomial semiring, sum-of-strategies, absorption-minimality or repair synthesis. |
| [Defining Winning Strategies in Fixed-Point Logic](https://logic.rwth-aachen.de/pub/graedel/CGLP15.pdf) | Primary research paper | Section IV's Buchi/coBuchi duality and nested attractor/rank strategy distinction. No general parity-game or LFP compiler. |
| [Barbara Jobstmann, Reachability and Büchi Games](https://richmodels.epfl.ch/_media/w2_wed_3.pdf), Bucharest, May 2010 | Academic lecture notes | Existential/universal predecessors, attractors, ranks, recurrence versus one-time reachability. Different presentation of recurrence candidates, not copied fixtures. |
| [Languages, logics and automata: graph games](https://www.labri.fr/perso/anca/Games/graphgames.pdf) | Academic lecture notes | Positional Buchi strategies, largest recurrence fixed point and progress attractor. Not the later generalized Muller/parity constructions. |
| [mCRL2, A dash of infinity](https://www.mcrl2.org/mcrl2/web/user_manual/fundamentals/a_dash_of_infinity.html), 202607.0 documentation | Official tool documentation | Least/greatest fixed-point semantics and repeated behavior/fairness vocabulary. No mCRL2 integration or modal-mu-calculus parser; no fairness is assumed here. |
| [Spot reactive synthesis notebook](https://spot.lre.epita.fr/ipynb/synthesis.html) | Official tool documentation | Boundary to full LTL-to-game, parity synthesis, strategy simplification, Mealy/circuit production. None of that pipeline is implemented. The input is the hand-written tiny game. |

A searched community Buchi-game page could not be fetched and is not used as evidence. Papers, academic notes and official tool documentation cover three source types. A quantitative concurrent-game paper found during search was not used: memoryless claims do not transfer indiscriminately to concurrent or stochastic objectives.

## Limits

No learned/validated abstraction, LLM guarantee, execution shield, safety objective, generalized multiple-goal fairness, stochastic or simultaneous moves, timing, partial observation, reward, runtime enforcement, temporal-logic parsing, source-code verification, novel algorithm, scalability benchmark or formal proof. A supplied graph can omit real behavior or label goals incorrectly. Results about it do not validate a real agent protocol. All policies here are deterministic positional policies, not every strategy with history.
