# dead-branch

**Can your preregistered decision rule ever return the verdict it promises?**

A preregistered analysis plan is a program. A program can contain a branch no
input reaches. In a decision rule, an unreachable `falsify` branch is not a
style problem — it means **no possible data falsifies the hypothesis**, which is
the formal shape of an unfalsifiable prediction.

Once the rule is machine-readable, that question is **decidable**, and answering
it needs **no data at all**.

```
python3 validate.py                       # 17 known answers. run this first
python3 compare.py --selftest             # 15 more, for the two-encoding diff
python3 ladder_demo.py                    # a real broken rule, mine
python3 staged_demo.py                    # a rule written in prose, encoded
python3 harvest.py <scienceverse-clone>   # census over a whole repo

python3 colling_demo.py                   # a real preregistration. needs scipy
python3 equiv_demo.py                     # needs numpy + scipy
python3 nextmodel_demo.py                 # needs scipy
```

`reach.py`, `validate.py`, `harvest.py`, `compare.py`, `ladder_demo.py` and
`staged_demo.py` need **nothing but the standard library**. The last two demos
measure frequencies and want numpy/scipy; their committed output is in
`EQUIV_REPORT.txt` and `NEXTMODEL_REPORT.txt` if you would rather read than
run.

## What it reads

The [`scienceverse`](https://github.com/scienceverse/scienceverse) format from
Lakens & DeBruine (2021), *Improving Transparency, Falsifiability, and Rigor by
Making Hypothesis Tests Machine-Readable*, **AMPPS** 4(2),
[doi:10.1177/2515245920970949](https://doi.org/10.1177/2515245920970949).

Semantics were taken off the package **source** — `R/study_eval.R` at
`scienceverse/scienceverse@97d4054` — not off the paper's prose:

```
criterion       one comparison,  <result> <op> <comparator>,  op in  <  >  =  !=
                a non-numeric comparator NAMES another result, so
                estimate[1] > estimate[2] is legal
corroboration   a boolean expression over criterion ids, with  &  |  !  ( )
falsification   another such expression
verdict         "corroborate"   if C and not F
                "falsify"       if F and not C
                "inconclusive"  otherwise — INCLUDING when C and F are both true
```

`reachable_verdicts()` takes any verdict function of any arity, so a rule that
is not a corroborate/falsify pair can be checked without being deformed into one.

## Two levels

**Propositional.** Treat the criteria as free booleans. `falsify` is reachable
iff `F ∧ ¬C` is satisfiable. A negative is a **proof**: no data anywhere
produces that verdict, independent of effect size, sample size, or the
data-generating process.

**Numeric.** A propositionally satisfiable branch can still be impossible —
criteria on one variable can contradict (`p < .05` and `p > .05`), or a
structural relation can bite (a confidence interval's lower bound cannot exceed
its upper bound). The numeric level searches a finite critical-value pool per
connected component and then **verifies** the witness by plain evaluation. A
failure prints `NO WITNESS`, never "unreachable".

### Why a power simulation does not answer this

`scienceverse` can already simulate datasets and count how many come back
corroborated, falsified or inconclusive. That answers a different question. A
simulation samples **data** from one assumed data-generating process;
reachability is about the space of logically possible **result patterns**. A
zero count in a power run cannot tell "impossible" from "not at this effect
size", and those have opposite remedies: rewrite the rule, or go collect the
data. Four criteria is sixteen table lookups; the simulation is a thousand model
fits.

## What it flags, and what it deliberately does not

| flag | meaning |
|---|---|
| `DEAD BRANCH` | `corroborate` or `falsify` can never be the verdict |
| `NESTED RULES` | both rules can hold *and* a branch is dead — the rule is broken |
| `FOURTH STATE` | both rules can hold with all three verdicts also reachable — **not** a bug |
| `NO WITNESS` | propositionally reachable, no numbers found |
| `UNDEFINED` / `UNUSED` | bookkeeping |

An **unreachable `inconclusive` is not flagged.** `C = "x"`, `F = "!x"`
partitions every possible result on purpose, and leaving no middle is a good
thing to do.

The `FOURTH STATE` distinction was forced by a real case. `scienceverse`'s own
`vignettes/sim.Rmd` sets corroboration to "significantly greater than 0" and
falsification to "significantly smaller than the smallest effect of interest".
Both can hold at once, and in equivalence testing that is the most informative
result on the board — a real effect, too small to matter. It is not a
contradiction. The three-verdict scheme simply has no name for it, so
`study_eval.R` sends it to `inconclusive`, where "we learned nothing" also
lives. The first version of this tool called that a defect. It was wrong, and it
is still wrong: **the overlap is not a bug.** What turned out to be there
instead is in the next section, and it is a different kind of thing.

## Census over the `scienceverse` repository

37 complete registrations, **18 distinct rules** (the repo ships several of them
in four directories, so counting files would inflate both halves):

| | |
|---|---|
| clean on every check | **15** |
| dead `falsify` branch | **1** |
| reachable fourth state | **2** (by design, above) |

**The paper's flagship example is clean** — the kinship/trust registration in
both its 4-criterion and 12-criterion forms, the latter 4,096 truth
assignments. A checker that fires on good work is worth nothing, so that result
matters more than the one below.

The one dead branch is `tests/testthat/test-study_analyse.R`, the test named
*"criterion name overlap"*:

```r
add_criterion("a",   "p.value",  ">",  0.001)
add_criterion("aa",  "estimate", "<",  10)
add_criterion("aa2", "estimate", ">", -10)
add_eval("corroboration", "a | (aa | aa2)")
add_eval("falsification", "aa2 | (aa & a)")
```

Every way of satisfying `F` satisfies `C`, so the verdict can never be
`falsify`, and the test asserts the resulting `"inconclusive"` as expected
output — which, given the rules, it is.

**It is a fixture for string substitution, not a scientific registration, and
should never be described as one.** That is the point rather than the gotcha:
four lines, written by the two authors of the paper on machine-readable
falsifiability, inside their own repository, in which falsification was
impossible — and every tool in the chain stayed quiet. If it can happen there it
is not a discipline problem. It is a missing check.

## A real preregistration — the one the paper holds up

Every rule above comes out of a package's own files, which is a fair complaint
to make of the claim. `colling_demo.py` runs the check on a published
Registered Replication Report's analysis plan: Colling, Szűcs, De Marco, Cipora,
Ulrich, Nuerk … & McShane (2020), *Registered Replication Report on Fischer et
al. (2003)*, **AMPPS**, plan at [osf.io/6a2ny](https://osf.io/6a2ny/).
Seventeen labs. Filed before the data.

**It is the example Lakens & DeBruine choose**, on their page 3:

> in the analysis plan of the Registered Replication Report on Fischer et al.
> (2003) by Colling et al. (2020), available at https://osf.io/6a2ny/, **a clear
> decision rule for corroboration is specified**

Their Model 1 rule, verbatim from the plan:

> If the congruency effect is positive and statistically significantly different
> from zero in the 500 ms and 750 ms delay conditions but not statistically
> significantly different from zero in the 250 ms and 1000 ms delay conditions,
> we will consider the findings of Fischer et al. (2003) to be replicated within
> the limits they propose. If it is positive and statistically significantly
> different from zero in conditions beyond the 500 ms and 750 ms delay
> conditions, we can consider the findings of Fischer et al. (2003) to be
> replicated but for the effect to be more general than they originally proposed.

Four delays, so sixteen possible patterns of "significant and positive". One
clause is ambiguous — does *"beyond the 500 ms and 750 ms delay conditions"*
presuppose those two, or name only the extras? Both readings are encoded and
printed, because that choice is interpretation and you should be able to
disagree with it:

| | reading A (presupposes) | reading B (extras only) |
|---|---|---|
| replicated within their limits | 1 of 16 | 1 of 16 |
| replicated, more general | 3 of 16 | 12 of 16 |
| **no declared verdict** | **12 of 16** | **3 of 16** |

### The plan names two grades of success and no failure

Every pattern in that last row is one where the replication did **not** find the
effect. The plan says what counts as replicated within the original's limits and
what counts as replicated more generally. It does not say what counts as not
replicated.

That is the complaint Lakens & DeBruine open with — *researchers often do not
explicitly state what would corroborate or falsify their prediction* — sitting
inside the example they picked to show a rule done well. The corroboration half
was specified carefully enough to quote. The other half was not specified at
all, and nothing in the chain asks.

Scoped, because this is a claim about someone's document: the file is the only
thing that GUID resolves to, the Stage 1 proposed analysis. Measured over its
text, the stem "replicat" occurs **three times, all inside that one sentence**,
and *not replicat*, *fail to replicat*, *unsuccessful*, *no evidence*, *null
result* and *falsif* occur **zero** times.

### And "within their limits" is a vanishing branch

To earn the primary verdict the replication must find significance at 500 and
750 **and fail to find it** at 250 and 1000. Two of its four conditions are
demands for a non-significant result, so power helps one pair and hurts the
other. Exact normal-theory arithmetic, true effect 0.20 at 500 and 750:

| N | true offset 0 | 0.02 | 0.05 | 0.10 |
|---|---|---|---|---|
| 200 | 0.588 | 0.577 | 0.518 | 0.326 |
| 500 | 0.892 | 0.849 | 0.631 | 0.151 |
| 2,000 | 0.903 | 0.730 | 0.153 | 0.000 |
| 20,000 | 0.903 | 0.037 | 0.000 | 0.000 |
| 100,000 | 0.903 | 0.000 | 0.000 | 0.000 |

If the effect at 250 and 1000 is **exactly** zero the verdict settles at
0.95² = 0.903 and stays. For **any** nonzero value, however small, it peaks and
then falls to zero: a bigger replication becomes less able to confirm the
original's limits. The branch survives only on the knife edge of an exact point
null, which is the thing a smallest-effect-of-interest exists because nobody
believes.

Assumptions are stated in the script and they do work: standard error
1/√N in effect units, two-sided α = 0.05, and the four delays treated as
independent where the plan's model is multivariate. Correlation moves the
numbers, not the direction — the non-significance demand is unaffected by it.

**None of this is an error in the replication.** The team ran it, reported it,
and specified the rule in public and in advance, which is more than most. It is
that two properties of that rule are invisible to every check it passed: no
written failure verdict, and a primary success verdict a larger study is less
likely to be able to reach.

## Two encodings of one sentence

`compare.py` asks a second question that came out of that fourth-state case: a
paper states its decision rule in prose and its code states it in criteria —
**do the two return the same verdict on every result pattern that can happen?**

A disagreement is reported only with a **verified numeric witness**, a vector of
result values that realises it. A cell that differs propositionally but has no
numbers prints `NO WITNESS` and is not counted, which is the same rule the
checker uses everywhere: when an instrument cannot reach a verdict it says so
rather than guessing the likelier one.

### The instance: `equiv_demo.py`

Lakens & DeBruine state the recipe twice on page 4. Both times corroboration
carries a **second conjunct**:

> "corroborated when we can statistically conclude that the observed mean
> difference for at least one measure is **both greater than 0 and not smaller
> than** the smallest effect size of interest (SESOI)"

> "corroborated if at least one of our 97.5% confidence intervals has a lower
> bound larger than 0 **and an upper bound not smaller than 0.2**"

On a single measure that second conjunct is exactly the negation of the
falsification criterion, so **their recipe is mutually exclusive by
construction** — which is why the flagship kinship example comes back clean.

`vignettes/sim.Rmd` drops it. Its corroboration is one criterion, and its own
English gloss says so: *"corroborated if dog owners are significantly happier
than cat owners."* No second clause. **This is not a coding slip — it is a
weaker recipe that reads perfectly naturally in English.** What it costs is the
one result pattern a SESOI exists to catch.

```
paper p.4 (CI form, one measure)   VS   sim.Rmd (as written)
  2 criteria, 4 truth assignments
  DISAGREE on 1 feasible pattern(s):
    falsify      where the other says inconclusive  x1
    - true: above0, belowS
      witness: t.conf.int[1]=0.0666667, t.conf.int[2]=0.133333
```

An effect reliably above zero and reliably below the SESOI. The paper's recipe
calls that `falsify`, correctly: the prediction was that the effect is big
enough to matter, and it is not. The vignette's calls it `inconclusive`.

### How often, measured

Five predictions, in order, **two of them dead and kept verbatim** in the
output. With a true effect at half the SESOI, per group:

| n | both criteria significant | paper = falsify | vignette = inconclusive | disagree |
|---|---|---|---|---|
| 500 | 0.000 | 0.473 | 0.053 | 0.000 |
| 1000 | 0.447 | 0.722 | 0.447 | **0.447** |
| 2000 | 0.868 | 0.931 | 0.868 | **0.868** |
| 10000 | 1.000 | 1.000 | 1.000 | **1.000** |

The disagreement rate **goes to one**. For any true effect strictly inside
(0, SESOI) both one-sided tests are testing a true alternative, so both become
significant, so the vignette's rule converges to `inconclusive` exactly where
more data should buy certainty.

### A vanishing branch

The sharper half. The vignette's `falsify` branch **is** propositionally
reachable, so this checker passes it and so does branch coverage. But inside
(0, SESOI) it demands *significantly below the SESOI and NOT significantly above
zero* — power on one test and a lack of it on the other:

| n per group | P(vignette = falsify) | P(paper = falsify) |
|---|---|---|
| 500 | 0.4758 | 0.4763 |
| 1000 | 0.2791 | 0.7235 |
| 2000 | 0.0613 | 0.9336 |
| 10000 | **0.0000** | **1.0000** |

The same rule at low power; opposite rules at high power. Its falsification is
reachable **only by a study too small to see the effect it has.** Call it a
vanishing branch: every static check is satisfied, and the asymptotics are not.

And the whole thing is governed by two numbers and nothing else —
`(z0, zS) = (d, S−d)·√(n/2)`. Hold both fixed and vary n by a factor of 100 and
every rate matches to 0.006. So whether that branch can fire is set by the
study's **power** against 0 and against the SESOI: not by the hypothesis, not by
the prose, and not by anything a reviewer sees.

## When the rule is run on a model that does not exist yet

`nextmodel_demo.py`, on Thomas, Gligorić & Shah, *Mitigating LLM-based p-Hacking
by Preregistering for the Next LLM*,
[arXiv:2606.27687](https://arxiv.org/abs/2606.27687).

Their protocol: finalise the procedure on today's models, preregister the plan
**together with a set of eligible future models**, and run the confirmatory
analysis on the first eligible model released afterward. It cannot be hacked
against because it does not exist. Measured, it blocks 73.9% and 72.7% of
transferred hacks across 20 models. **The protocol works and this is not a
rebuttal.**

Their Table 1 field 2 tells the author to fix inclusion thresholds "such as
price per token, a minimum benchmark score, a maximum output-violation rate", so
the eligible set carries a **floor on capability by design**. Their own
conclusion agrees from the other side: "as models improve, researchers may
already want to adopt the strongest available model".

Now put that beside the analysis, which they operationalise as a threshold on
the target-label rate. A threshold rule has branches; a branch's probability is
a binomial tail; so each branch is live only over a **band** of labeller
behaviour. On their review task — 100 items, true rate zero by construction,
exact binomial, no simulation:

| labeller false-positive rate | live branches |
|---|---|
| 0.00 | 1 — negligible only |
| 0.02 | 2 |
| **0.036 – 0.140** | **3 — all of them** |
| 0.15 | 2 |
| 0.25 | 1 — substantial only |

All three outcomes are available only inside a window spanning **a factor of
about four** in labeller error. Outside it, one of the two decisive verdicts
drops under one in a thousand.

So the cuts and the floor can be chosen together, before the confirmatory model
exists, such that one outcome is the only one it can produce. **Nothing is tuned
after seeing data.** The commitment is real, the timestamp is real, the model
genuinely did not exist — every defence in their paper is satisfied and none of
them is aimed at this, because it is not p-hacking. The thing that decided the
result is the minimum benchmark score in field 2.

The ask is one line, between their fields 2 and 5: for each outcome the rule can
declare, state the range of model behaviour over which that outcome is
reachable, and check it against the floor you just wrote down. It is exact
arithmetic, and unlike the confirmatory run it can be done the day the
preregistration is filed.

**Honest limit:** that instance is constructed. It was not found in their data,
and they are the ones holding the data that could settle whether the band is
real across model generations.

## The rule that started it

Mine. `ladder_demo.py` runs it:

```
AS REGISTERED
  reachable verdicts: 2 of 8 declared
    invalid arm   32 assignments
    D = 1         32 assignments
  UNREACHABLE, though declared: D = 2, D = 3, D = 4, D = 5, D = 6, no ceiling
```

Two clauses, written forty minutes apart, each correct read alone. One said a run
was valid only if the first rung came in at or below a quarter; the other said
the answer was the *smallest* rung at or below a quarter. Side by side, the first
rung does both jobs in opposite directions, so on every run the first clause
admits, the second can only ever answer **one**. I collected forty rows over
three days of a rationed quota before noticing.

Nobody was protecting anything. It was a typo, and the rule had never been run —
not once, on nothing — because there was no data yet, and running an analysis
plan on no data feels like a category error. It is the only moment when the plan
is the only thing you can be wrong about.

Running the corrected rule through the same check then found something I did not
know: it can never say `D = 6` either. Six rungs name five finite depths plus
"deeper than we looked". The rule is right; my list of declared verdicts was one
item too long.

## A rule written in prose

Templates ask for the decision rule in words, not in a format, so
`staged_demo.py` takes one verbatim — the staged example in Vaccaro,
*Preregistration for Experiments with AI Agents*,
[arXiv:2606.11217](https://arxiv.org/abs/2606.11217), §4:

> "If pilot data indicate floor effects (accuracy < 20%), we will increase
> context length by 500 tokens; if ceiling effects (accuracy > 90%), we will use
> more difficult items from the backup set." The key constraint is that these
> decision rules must be specified in advance, not invented post hoc.

It comes back **clean**: all three outcomes reachable, and floor-and-ceiling
together is impossible rather than merely unlikely. That is the result worth
having first — a check that fires on a careful author's example is not a check.

Encoding a prose rule is an act of interpretation, so `staged_demo.py` prints
its encoding beside its verdict. Without that the verdict is worthless, and you
should disagree with the encoding rather than with the number.

The point the demo makes is about the quoted constraint rather than the quoted
rule: **specified in advance is necessary and not sufficient.** The rule in
`ladder_demo.py` was specified in advance, time-stamped, and committed before a
single API call was spent. It still had one reachable output. A dead branch is
not a forking path; it is a path that does not fork, and time-stamping cannot
see it.

## Honesty about this tool

`validate.py` holds 17 hand-computed known answers and `--force-red` breaks the
verdict semantics on purpose to check the suite notices. It caught two real bugs
before the checker said anything about anybody: a non-strict bound silently
relaxing a strict one (`p < .05` became `p <= .05`, witness `p = 0.05`), and an
`UNDEFINED` flag swallowed by an early return.

Three more of this repository's own instruments were wrong, and are recorded
because a wrong instrument produces confident wrong accusations:

* `compare.py`'s `--force-red` **passed when it should have failed.** It did
  `import compare as _self` while running as `python3 compare.py`, which makes a
  second module object — `__main__` is the one being called — so the patch
  landed on a copy nothing used. A check that cannot fail is not a check.
* `reach.py` placed **one** point strictly inside each gap between breakpoints,
  so two variables tied by a strict relation that must both land in one gap had
  a single candidate to share. `0 < conf.int[1] < conf.int[2] < 0.2` is ordinary
  and the old pool reported it `NO WITNESS`. Fixed; `interior=1` is
  bit-identical to the old pool over 2000 random cases, and enlarging a pool can
  only turn a `NO WITNESS` into a witness, so **no number published here moves**
  — the census re-ran at the same 37/18/15/1/2.
* The first version of `equiv_demo.py` allocated about a gigabyte of raw samples
  it did not need. Both one-sided tests are functions of the difference of means
  and the pooled standard error, so `tsim.py` simulates those **sufficient
  statistics** instead: peak 0.3 MB against 640 MB, validated against raw-data
  scipy on three settings by KS test and rejection rate before it was used.

**The first census produced six flags and four were mine**, each caught by
hand-checking it against the source: named R arguments dropping a criterion; no
`add_hypothesis` scoping; no `add_analysis` scoping (two criteria both reading
`p.value` off different analyses are two different numbers); and non-piped
`add_eval(s, ...)` calls in a test file merged into one phantom registration. All
four are fixed and all four are regression cases. `harvest.py` names and counts
every parse failure, because a census with an unknown denominator is not a census.

`NOTES.md` has the full working record, including the don'ts.

## Licence

MIT.

— Iris
