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
python3 ladder_demo.py                    # a real broken rule, mine
python3 staged_demo.py                    # a rule written in prose, encoded
python3 harvest.py <scienceverse-clone>   # census over a whole repo
```

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
lives. The first version of this tool called that a defect. It was wrong.

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
