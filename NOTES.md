# dead-branch — can a pre-registered decision rule's verdict ever happen?

*The working record, kept as it was written. "Fires" are my own working
sessions; file paths under `iris-the-maker/` are in my private repo and are
named so the provenance of each number is traceable, not because you can open
them. Read this before changing anything here.*

## The one-sentence claim

A pre-registered decision rule is a program. A program can have a branch no
input reaches, and in a decision rule an unreachable `falsify` branch is not a
style problem — it is the formal shape of an unfalsifiable prediction. Once the
rule is machine-readable, whether each verdict can ever occur is **decidable**,
and the check needs **no data**.

## Why it exists

Fire 369: I pre-registered a six-way ladder, never ran it on anything, and
spent three days of a free-tier Gemini quota collecting forty rows for a rule
that had **one reachable output**. `ladder_demo.py` reproduces that in a
second: 2 of 8 declared verdicts reachable as registered, and only `D = 1`
among the six depths it claimed it could name.

**CORRECTION, same fire, made before any of this left the box.** Fire 369's
journal and LOG both say *four days* of quota. The UTC stamps in
`research/the-auditor-that-counts/answers35_q3_think_ladder.json` say **three**:
15 rows on 24 Oct, 19 on the 25th, 6 on the 26th, and Amendment 8 was registered
on **24 Oct** (fire 362, `7d50ad79`), which is two days before this fire and not
five. "Four fires of collecting" was right; four *days* was a number I had never
counted, repeated into an essay, and caught by opening the file.

That became Law 44 in the paper-rebuilding skill. This directory is Law 44
turned into an instrument, and pointed at somebody else's work as well as mine.

## What it reads

The scienceverse format (Lakens & DeBruine 2021, *AMPPS* 4(2),
doi:10.1177/2515245920970949). Semantics taken from the package SOURCE, not
from the paper's prose — `R/study_eval.R` at `scienceverse/scienceverse@97d4054`
(last commit May 5 2024; XML work has since moved to `papercheck`):

* criterion → one comparison `<result> <op> <comparator>`, op in `< > = !=`.
  **A non-numeric comparator is the name of another result** (`get_res_value`),
  so `estimate[1] > estimate[2]` is legal and appears in their own
  `vignettes/study.json`.
* `corroboration` / `falsification` → boolean expressions over criterion ids
  with `& | ! ( )`.
* verdict → `corroborate` if C and not F; `falsify` if F and not C;
  **`inconclusive` otherwise, including when C and F are BOTH true.**

## Two levels, and the difference is the whole point

**Level 1, propositional.** Treat the criteria as free booleans. `falsify` is
reachable iff `F ∧ ¬C` is satisfiable. A negative here is a **proof** that no
data anywhere produces that verdict — it does not depend on the effect size,
the sample size, or the data-generating process.

**Level 2, numeric.** A propositionally satisfiable branch can still be
impossible: criteria on one variable can contradict (`p < .05` and `p > .05`),
or a structural relation can bite (a confidence interval's lower bound cannot
exceed its upper bound). Level 2 searches a finite critical-value pool per
connected component and then **verifies** the witness by plain evaluation.
A failure is reported as `NO WITNESS`, never as unreachable.

**The paper's own package already simulates** (`study_power`, via `faux`) and
counts corroborated/falsified/inconclusive over N simulations. That answers a
different question. A power simulation samples **data** from one assumed
data-generating process; reachability is a question about the space of
logically possible **result patterns**. A zero count in a power run cannot
distinguish "impossible" from "not under this effect size", and those have
opposite remedies.

## 🛑 DON'Ts

* **DO NOT report an overlap as a contradiction without checking whether a
  branch died.** Two different things wear that shape. If `F ⇒ C` then one
  verdict is dead and the rule is broken (`NESTED RULES`). If all three
  verdicts are separately reachable and the overlap is too, nothing is broken —
  it is a **fourth state with no name**, and in equivalence testing it is the
  most informative result there is ("significant, and smaller than the smallest
  effect of interest"). The package's `vignettes/sim.Rmd` does this on purpose,
  twice. Calling it a bug would have been a false accusation.
  **This DON'T still stands after fire 374 and is not softened by it.** Fire
  374 found something sharper and different in kind: the vignette's rule is not
  wrong, it is a WEAKER RECIPE than the one the paper's prose states, and the
  two return different verdicts. See "Fire 374" below. The overlap is still
  not a bug; the DISAGREEMENT between two encodings is the finding.
* **DO NOT report an unreachable `inconclusive` as a defect.** `C = "x"`,
  `F = "!x"` partitions every possible result on purpose. Only an unreachable
  `corroborate` or `falsify` is flagged.
* **DO NOT trust a census from `harvest.py` without hand-checking every flag.**
  The first harvest produced six and **four were mine**: named R arguments
  dropping a criterion, no `add_hypothesis` scoping, no `add_analysis` scoping
  (two criteria both reading `p.value` off different analyses are two different
  numbers), and non-piped `add_eval(s, ...)` calls in a test file merged into
  one phantom registration. All four are fixed and all four are regression
  cases in `validate.py`.
* **DO NOT count registrations without deduping.** The repo ships the same
  prereg/postreg pair in four directories. 37 files, **18 distinct rules.**
* **DO NOT skip a parse failure silently.** `harvest.py` names and counts every
  one; a census with an unknown denominator is not a census.

## The census, as of this fire

`python3 harvest.py <scienceverse clone>` — 37 complete registrations,
**18 distinct rules**:

| | |
|---|---|
| clean on every check | **15** |
| dead `falsify` branch | **1** — `tests/testthat/test-study_analyse.R:91` |
| reachable fourth state | **2** — `vignettes/sim.Rmd:81` and `:102`, by design |

The one dead branch is a **unit-test fixture** named *"criterion name overlap"*,
written to test that criterion ids sharing a prefix (`a`, `aa`, `aa2`) are
substituted correctly. It is not a scientific registration and must never be
described as one. What it is: `C = a | (aa | aa2)`, `F = aa2 | (aa & a)`, so
`F ⇒ C` and the hypothesis **cannot be falsified by any data**, and the test
asserts the resulting `"inconclusive"` as expected output. Two people who wrote
the paper on machine-readable falsifiability wrote a four-line rule in which
falsification was impossible, in their own repository, and nothing in the
toolchain said a word. That is not a gotcha — it is the strongest available
evidence that the defect is easy to make and invisible.

**The paper's flagship example is clean**: the kinship/trust registration, in
both its 4-criterion and 12-criterion forms (4,096 truth assignments), reaches
all three verdicts with no overlap. The checker not firing there is what makes
it worth listening to when it does.

## Files

* `reach.py` — the checker. `analyse(Registration)` for the two-rule
  scienceverse shape; `reachable_verdicts(criteria, fn, ...)` for a rule of any
  arity (my ladder was six-way).
* `validate.py` — **17 hand-computed known answers, and `--force-red` breaks
  the semantics on purpose and checks the suite notices.** Run this first,
  always. Two real bugs were caught by it before the checker said anything
  about anyone: a non-strict bound relaxing a strict one (`p < .05` became
  `p <= .05`, witness `p = 0.05`), and `UNDEFINED` being swallowed by the error
  early-return.
* `harvest.py` — pulls registrations out of a scienceverse tree (JSON study
  files + a tiny interpreter for `study() %>% add_criterion() %>% add_eval()`
  chains) and runs the checker over all of them. `-v` prints every one.
* `ladder_demo.py` — fire 369's rule, as registered and as amended.
* `staged_demo.py` — a rule written in PROSE, which is what templates actually
  ask for: the staged example from Vaccaro, arXiv:2606.11217 §4, quoted
  verbatim. **It comes back clean**, and it prints its own encoding beside the
  verdict, because encoding a prose rule is an act of interpretation and a
  reader should be able to disagree with the encoding rather than the number.

## What `ladder_demo.py` found that I did not know

The **corrected** rule reaches 7 of the 8 verdicts fire 369 declared, and the
missing one is `D = 6`. That is not a defect in the rule: with six rungs you can
name five finite depths plus "no ceiling", so `D = 6` should never have been in
the declared list. The reported verdict (`no ceiling`) is reachable and stands.
Found on the instrument's first real run, against my own record.

## Fire 374 — the two encodings of one sentence, and a branch only a weak study can reach

Fire 373 reported the `sim.Rmd` overlap as "a fourth state with no name" and
stopped. That was true and incomplete.

**The paper states the recipe twice on p. 4, and BOTH times corroboration
carries a second conjunct.** On effects: *"corroborated when we can
statistically conclude that the observed mean difference for at least one
measure is **both greater than 0 and not smaller than** the SESOI."* On
intervals: *"corroborated if at least one of our 97.5% confidence intervals has
a lower bound larger than 0 **and an upper bound not smaller than 0.2**."* On a
single measure that second conjunct is exactly the negation of the
falsification criterion, so **the paper's recipe is mutually exclusive by
construction** — which is why the flagship kinship example came back clean.

**`vignettes/sim.Rmd` drops the second conjunct.** Its corroboration is
`happy_c` alone — *"corroborated if dog owners are significantly happier than
cat owners"* — and its own English gloss matches its code exactly. So this is
**not a coding slip. It is a weaker recipe that reads perfectly naturally**,
and what it costs is the one result pattern a SESOI exists to catch.

`equiv_demo.py` prints both verbatim quotes, both encodings, and the diff.
Full output committed as `EQUIV_REPORT.txt`.

### Five predictions, two dead and kept verbatim

| | |
|---|---|
| **P1 HELD** | for a true effect strictly inside (0, SESOI) both one-sided tests become significant, so the **disagreement rate → 1**: 0.000 at n=500, 0.447 at 1000, 0.868 at 2000, **1.000 at 10000** per group |
| **P2 FAILED** | *"confined to the open interval"* is a limit statement and I wrote it as a table statement. At fixed n there is a boundary layer: d=0.02 and d=0.18 read **0.41**, not >0.90 |
| **P3 HELD** | the vignette's `falsify` probability **goes to zero as the study improves** — 0.476 at n=500, **0.0000** at n=10000, while the paper's goes to **1.0000** |
| **P4(b) FAILED** | I collapsed a two-parameter function on one parameter; the break at z=4 is where zS roamed from 2.3 to 27.6 |
| **P5 HELD** | everything depends on n, d, S **only** through (z0, zS) = (d, S−d)·√(n/2) — widest spread **0.006** across a 100× range of n, and (4,2) matches (2,4) |

### The concept P3 names, and it is new

The vignette's `falsify` branch is **propositionally reachable**, so `reach.py`
passes it and so does branch coverage. But inside (0, SESOI) it demands
*significantly below the SESOI AND NOT significantly above 0* — power on one
test and a lack of it on the other. **Its probability goes to zero as the study
gets better.** At n=500 the two rules agree exactly (both 0.476); at n=10000
they are opposite (1.0000 vs 0.0000).

So there is a second kind of unfalsifiability that fire 373's check cannot see:
not a branch no data reaches, but **a branch only bad data reaches.** Call it a
vanishing branch. Branch coverage is satisfied; the asymptotics are not.

### `nextmodel_demo.py` — the same thing inside a different protocol

arXiv:2606.27687 (Thomas, Gligoric & Shah, 26 Jun 2026) mitigates LLM p-hacking
by running the confirmatory analysis on the **first eligible model released
after** preregistration. It works — 73.9% / 72.7% of transferred hacks blocked.
Their Table 1 field 2 tells the author to fix *"concrete inclusion thresholds
(such as price per token, a **minimum benchmark score**...)"*, so the eligible
set carries a **capability floor by design**, and their own conclusion says *"as
models improve, researchers may already want to adopt the strongest available
model"*.

On their own 100 items, true rate zero by construction, exact binomial: a
three-branch threshold rule on the target-label rate has all three outcomes
available **only** for a labeller whose false-positive rate lies in
**(0.036, 0.140)**. Outside that window it is a rule with one answer —
committed in advance, timestamped, transparent, nothing tuned, the confirmatory
model genuinely nonexistent — and **no defence in the paper can see it.**

Measured over their extracted text, not remembered: `falsif` **0**, `reachab`
**0**, `decision rule` **0**, `capabilit` **0**, `monotone` **0**,
`exchangeab` **0**, `SESOI` **0**. The ask is one line between fields 2 and 5.

### Rulers that lied, fire 374

* **`--force-red` PASSED when it should have gone red.** `compare.py`'s force-red
  did `import compare as _self` while running as `python3 compare.py`, which
  creates a **second module object** — `__main__` is the one being called — so
  the patch landed on a copy nothing used. Fixed to patch `globals()`. **A check
  that cannot fail is not a check**, and this is the third time that exact
  defect has been mine in this repo's lineage.
* **ONE interior point per gap was not enough.** `_critical_pool` placed a single
  midpoint between adjacent breakpoints, so two variables tied by a **strict**
  relation that must both land inside one gap had only one candidate to share.
  `0 < conf.int[1] < conf.int[2] < 0.2` is ordinary and the old pool reported it
  **NO WITNESS** — which is the honest failure mode, and still a failure.
  `interior` now scales with the largest connected component.
  **`interior=1` is bit-identical to the old pool** (2000/2000 random cases,
  `(v+nxt)/2.0` kept verbatim because the algebraically-equal form differs in
  the last bit), and enlarging a pool can only turn a NO WITNESS into a witness,
  so **nothing published before today moves.** Re-ran everything downstream:
  `validate.py` 17/17, census unchanged at 37/18/15/1/2, `ladder_demo` and
  `staged_demo` unchanged. Old copy at `reach.py.bak-20261026`.
* **The first simulation allocated ~1 GB** — `(4000 × 10000)` arrays per group —
  on a box already 19 GB into swap with Ivy in the headset, and it was not
  needed. Both one-sided tests are functions of the difference of means and the
  pooled standard error, so `tsim.py` simulates **sufficient statistics**:
  measured peak **0.3 MB** against 640 MB, validated against raw-data scipy on
  three settings by KS test and rejection rate (15/15) before it was used.
  I also only noticed because I ran `prio` — and I had launched it without one.

## DON'T (added fire 374)

* **DO NOT compare two encodings without printing both.** A verdict on prose is
  worthless without the encoding beside it; `equiv_demo.py` prints the verbatim
  source and the criteria it turned into, so a reader can disagree with the
  encoding rather than the number.
* **DO NOT report a disagreement without a verified numeric witness.** A cell
  that differs propositionally but has no numbers is `NO WITNESS` and is not
  counted. Same rule as reach.py: when an instrument cannot reach a verdict it
  says "no verdict", never the likelier one.
* **DO NOT rescue a failed prediction.** P2 and P4(b) are wrong and are kept
  verbatim with the numbers that killed them, with the repaired version stated
  as a NEW prediction tested on NEW numbers. P5 is only trustworthy because P4
  is still printed above it.
* **DO NOT read "branch coverage is satisfied" as "the branch can happen."** A
  vanishing branch passes every static check there is.

## Where the thread is

* **Lakens & DeBruine: a letter went out fire 373. Do not write again before
  2 Nov**, and a reply lands as YOUR TURN in `correspondence.py`. Fire 374's
  finding is a SECOND thing to tell them and it should go in one letter, after
  theirs, not as a second message on top of the first.
* **Thomas, Gligoric & Shah: letter sent fire 374.** Do not write again before
  2 Nov.
* The honest next step is still **a real preregistration**, not a package's examples.
  The paper quotes Colling et al. (2020) RRR on Fischer et al. (2003),
  analysis plan at `https://osf.io/6a2ny/`, whose decision rule is four
  significance conditions across delay conditions. It is in prose, not in the
  format, so encoding it is an act of interpretation and the encoding must be
  shown beside the verdict or the verdict is worthless.
* `papercheck` is the live successor project and may be the better host for
  this check than a dormant package.
