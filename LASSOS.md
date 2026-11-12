# BuchiLab: replay a failing policy

A lasso gives a finite prefix to follow once and a nonempty cycle to repeat
forever. This mode shows a concrete failure for each losing fixed-policy/root
pair. It does not replace the original repeated-goal report.

[Live inspector](https://midya8.github.io/buchilab/lassos.html) | [Base fixed-point method and seven-source ledger](METHOD.md)

## Separate contract, unchanged v1

`buchilab.witness.lassos(data)` returns exactly `schema`, `input`, `policies`, with schema `buchilab-lassos-v1`. Input and complete positional-controller policy order are identical to the base game. Each policy contains `index`, `choices` and every input-ordered root. Each root contains `state`, strict boolean `winning` and `lasso`. Winning roots have null lasso. Losing roots have exactly `anchor`, `prefix`, `cycle`; each step is exactly `{from, action, to}` from the retained graph. Choice records preserve exact controller-action labels, even when targets are identical. With no controller states, there is one empty policy.

The base `buchilab-v1` report/API, original nine native tests, original three Node/Chrome tests and seven base fixtures remain unchanged. The native CLI helper gains optional generator/checker/schema injection, with its old defaults preserved. The witness module exposes a separate CLI, not a new default report schema:

```sh
python -m buchilab.witness arena.json --output lassos.json
python -m buchilab.witness lassos.json --verify
```

Existing duplicate-key/nonfinite/64 KiB arena/8 MiB report limits, strict UTF-8, atomic file replacement and failed-write preservation apply. Browser JSON.parse keeps normal last-key-wins semantics. All graph data stays local to the page.

## Canonical witness, not a globally shortest lasso

For a fixed controller policy retain its chosen edges and all environment edges. Select the first input-ordered vertex that is reachable from the root and belongs to a cyclic SCC of the non-goal induced graph. This is the anchor. Return a shortest full-graph prefix from root to anchor, and a shortest **nonempty** non-goal cycle from anchor back to itself. Retained input-action order breaks equal-length ties. The prefix is empty when root equals anchor, even if a self-loop exists. A one-edge self-loop is a valid cycle. Shortest prefix length is at most n - 1 and shortest cycle length at most n. No global minimal total length is claimed: input-order anchor selection can deliberately choose a longer cycle than a later anchor's self-loop.

Follow the prefix once and the cycle forever. The finite prefix may include goals. All cycle vertices must be non-goals; otherwise infinitely repeating it would not demonstrate failure of the repeated-goal objective. Controller actions always obey the selected policy. The environment behavior described can depend on whether it is on the prefix or repeating cycle. It is not presented as a positional environment policy, nor as a single environment strategy defeating all controller policies. Prefix and cycle may overlap at vertices other than the anchor. No fairness condition requires taking an enabled exit.

## Generator and independent checks

Native generation reuses the original bitmask/Tarjan/BFS game report for the selected policy's bad/reachable vertices, then builds action paths with a BFS predecessor-edge map. The checker never calls this generator or the fixed-point solver. It independently enumerates complete controller policies, retains exact action edges, and uses the existing exhaustive joint positional-policy lasso oracle for per-policy winning classification. For each losing root it tries candidate anchors in input order and enumerates simple paths breadth-first, permitting only the final return to close a non-goal cycle. Enumeration is bounded by n - 1 prefix edges or n cycle edges. This independent bounded-walk construction checks existence, canonical anchor, shortest lengths, tie order and exact action provenance. Full recursive strict-type/shape comparison rejects omitted or extra fields, bool-as-index, forged winning/null decisions, changed anchor, missing cycle, reordered prefix and fake action labels.

JavaScript independently builds the base game report with its set/graph-closure engine and constructs canonical witnesses with bounded simple walks rather than predecessor maps. The browser and native checker share the simple-walk idea, not code; independence is algorithmic between generation and checking, not independent authorship or formal proof.

## Controls and checks

Ten browser controls preserve all seven base controls and add: input-order anchor with a two-edge cycle and action ties versus a shorter later self-loop; an unreachable bad cycle beside a winning all-goal root; and duplicate-target controller actions that remain distinct policies/witnesses.

At the lasso release, seven added native tests preserved the original nine, for 16 total tests passing Python 3.10-3.13. All remain in the current 31-test suite. New coverage includes all 21,952 three-state graph/owner/goal combinations, 120 seeded larger cases, the 729-policy duplicate-target maximum, nonempty self-loop cycles, empty prefixes, goals on the finite prefix, null winning witnesses, owner/action tie order, a multiedge cycle, unreachable bad components, independent checker with solver patched out, every report-family forgery, exact primitive types, immutability and strict atomic CLI rejection.

The lasso release added two Node/actual-Chrome tests to the original three, for five total. All remain in the current nine-test suite. Witness Python/JavaScript comparison covers 314 complete reports, 1,023 policies, 4,189 roots, 1,713 failing-policy witnesses, 1,449 prefix edges and 2,114 cycle edges. All two-state distinct-target games plus ownership and goals are included, alongside ten controls and 160 seeded cases. Counts are descriptive test coverage, not speed or superiority claims.

At 320/390/1280 the new actual-Chrome test visits every record in all ten controls: 13 policies, 17 controller choices, 32 roots, 19 witnesses, ten prefix edges and 22 cycle edges. It checks exact owners/actions/endpoints and text, null/empty states, full JSON/export, invalid-input clearing and horizontal overflow. Installed-wheel reproduction preserves seven base reports/two CLI entry points and adds ten witness reports through the witness module CLI, generation and verification outside checkout; five installed module origins are checked.

## Sources and boundaries

Inspected November 9, 2026. These extend the base's seven sources across primary research papers, academic notes and official tool documentation, not a replacement theory claim.

- [NetworkX, Shortest Paths](https://networkx.org/documentation/stable/reference/algorithms/shortest_paths.html), official documentation, undated: BFS shortest-hop paths in unweighted graphs and predecessor reconstruction. This implementation is handwritten, not NetworkX integration. Its tiny edge-scanning BFS implementation is not claimed to meet the library table's optimized adjacency-list complexity.
- [Spot twa_run reference](https://spot.lre.epita.fr/doxygen/structspot_1_1twa__run.html), official documentation, undated: explicit prefix/cycle run representation, nonempty-cycle requirement and the difference between printing and actual replay. We check edge provenance, not only formatted states. No Spot run object or acceptance-mark machinery is implemented.
- [Spot lasso_enumerator reference](https://spot.lre.epita.fr/doxygen/classspot_1_1lasso__enumerator.html), official documentation, undated: finite stem/nonempty repeated-cycle vocabulary and bounded enumeration. Spot enumerates accepted automaton runs by total length; this inspector deliberately does not claim that ordering or enumerate all lassos.
- [Spot word notebook](https://spot.lre.epita.fr/ipynb/word.html), official documentation, undated: prefix/cycle access, labels, cycle simplification/rotation and accepted-word projection. No formula parser, word simplifier, BDD projection or LTL-to-automaton pipeline is implemented. Our edge labels are game actions, not Boolean valuations.

The original seven-source method establishes finite adversarial recurrence and positional determinacy. The new witness is a counterexample for a particular controller policy, not the entire game's universal controller quantifier. Graph completeness and goal labels remain the author's modeling responsibility. No learned abstraction, runtime shield, stochastic/concurrent game, fairness, formal verification, novel algorithm, scalability benchmark or real-agent guarantee.
