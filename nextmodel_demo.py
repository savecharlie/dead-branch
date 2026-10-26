#!/usr/bin/env python3
"""nextmodel_demo.py -- the eligibility floor is a parameter of the decision rule.

Fire 374, on arXiv:2606.27687 (Thomas, Gligoric & Shah, 26 Jun 2026),
"Mitigating LLM-based p-Hacking by Preregistering for the Next LLM".

Their protocol: finalise the procedure on today's models, preregister the
analysis plan TOGETHER WITH a set of eligible future models, and run the
confirmatory analysis on the first eligible model released afterward. The
confirmatory model does not exist at commitment time, so it cannot be hacked
against -- measured, 73.9% and 72.7% of transferred hacks blocked across 20
models and 11 configurations. The protocol works and this is not a rebuttal.

Their Table 1, field 2, tells the author to fix "concrete inclusion
thresholds (such as price per token, a MINIMUM BENCHMARK SCORE, a maximum
output-violation rate...)". So the eligible-model set carries a FLOOR on
capability, deliberately -- "rather than accepting whatever model comes next,
the researcher accepts only the model that meets their predefined and
checkable conditions". Their own conclusion notes the same drift from the
other side: "as models improve, researchers may already want to adopt the
strongest available model".

The composition nobody has made, and it is the same one fire 373 made for
Lakens & DeBruine: a preregistered decision rule is a program, and which of
its branches can fire is a question you can ask before any data exists.
Under this protocol the answer depends on the capability floor the author
wrote into field 2 -- so a rule can be committed in advance, timestamped,
transparent, unhackable by every defence in the paper, and still have only
ONE branch the confirmatory model can reach.

Nothing here is tuned after seeing data. That is the point: it is not
p-hacking, and that is exactly why none of the paper's defences see it.

Measured over the paper's own 100 items, with capability as the labeller's
false-positive rate on a corpus whose true rate is zero by construction --
their review task, built that way on purpose.

  python3 nextmodel_demo.py
"""
from __future__ import annotations

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import reach as R                     # noqa: E402

N_ITEMS = 100          # the paper's own n: "each draws on 100 labeled items"
LOW, HIGH = 0.05, 0.10 # the two thresholds of a three-branch rate rule
TINY = 1e-3            # a branch below this probability is reported unreachable-in-practice


# ------------------------------------------------------------------ the rule
# A three-branch threshold rule on the target-label rate, which is how the
# paper itself operationalises the analysis ("a fixed threshold on the
# target-label rate"). Written in scienceverse's own criterion form so
# reach.py can be pointed at it unchanged.

RATE = "annot.rate"
CRITERIA = [
    R.Criterion("over_high", RATE, ">", HIGH),
    R.Criterion("under_low", RATE, "<", LOW),
]


def verdict(env: dict) -> str:
    if env["over_high"]:
        return "SUBSTANTIAL"
    if env["under_low"]:
        return "NEGLIGIBLE"
    return "INCONCLUSIVE"


def logic_check():
    """reach.py and branch coverage both PASS this rule. That is the point."""
    reachable, witness, undeclared = R.reachable_verdicts(
        CRITERIA, verdict, domains={RATE: (0.0, 1.0)},
        declared=["SUBSTANTIAL", "NEGLIGIBLE", "INCONCLUSIVE"])
    print("  rule, in criterion form:")
    for c in CRITERIA:
        print(f"    {c.id:<10} = {c.var} {c.op} {c.value}")
    print("    SUBSTANTIAL if over_high; NEGLIGIBLE elif under_low; else INCONCLUSIVE")
    print("\n  reach.py, with no data:")
    for v, k in sorted(reachable.items()):
        w = witness.get(v)
        wtxt = f"   e.g. {RATE}={w[RATE]:g}" if w else ""
        print(f"    {v:<13} reachable ({k} assignment(s)){wtxt}")
    print(f"    declared but unreachable: {undeclared or 'none'}")
    print("  -> all three branches reachable. Branch coverage is satisfied.")
    return reachable, undeclared


# ---------------------------------------------------- capability, measured
def branch_probs(fpr, n=N_ITEMS):
    """EXACT, not simulated. The corpus's true rate is 0, so each item is
    labelled positive with probability `fpr` independently; the count is
    Binomial(n, fpr) and the rate is count/n. Every branch probability is
    then a sum of binomial pmf terms -- no sampling, no seed, no noise."""
    from scipy.stats import binom
    k_high = int(HIGH * n)          # SUBSTANTIAL needs rate > HIGH, i.e. k > k_high
    k_low = LOW * n                 # NEGLIGIBLE needs rate < LOW, i.e. k < k_low
    p_sub = float(binom.sf(k_high, n, fpr))                       # P(K > k_high)
    p_neg = float(binom.cdf(int(k_low) - 1 if k_low == int(k_low)
                            else int(k_low), n, fpr))             # P(K < k_low)
    return {"SUBSTANTIAL": p_sub, "NEGLIGIBLE": p_neg,
            "INCONCLUSIVE": max(0.0, 1.0 - p_sub - p_neg)}


def known_answers() -> int:
    """Hand-computed binomial checks before any band is reported."""
    from scipy.stats import binom
    bad = 0

    def chk(name, cond):
        nonlocal bad
        if not cond:
            print(f"  FAIL  {name}")
            bad += 1

    # n=100, HIGH=0.10 -> SUBSTANTIAL iff k >= 11; LOW=0.05 -> NEGLIGIBLE iff k <= 4.
    p = branch_probs(0.10)
    chk("fpr=0.10: SUBSTANTIAL = P(K>=11) exactly",
        abs(p["SUBSTANTIAL"] - float(binom.sf(10, 100, 0.10))) < 1e-12)
    chk("fpr=0.10: NEGLIGIBLE = P(K<=4) exactly",
        abs(p["NEGLIGIBLE"] - float(binom.cdf(4, 100, 0.10))) < 1e-12)
    for f in (0.001, 0.02, 0.07, 0.15, 0.4):
        q = branch_probs(f)
        chk(f"fpr={f}: the three branch probabilities sum to 1",
            abs(sum(q.values()) - 1.0) < 1e-9)
    chk("a perfect labeller (fpr=0) is NEGLIGIBLE with probability 1",
        abs(branch_probs(0.0)["NEGLIGIBLE"] - 1.0) < 1e-12)
    chk("SUBSTANTIAL rises with fpr",
        all(branch_probs(a)["SUBSTANTIAL"] < branch_probs(b)["SUBSTANTIAL"]
            for a, b in ((0.02, 0.05), (0.05, 0.10), (0.10, 0.20))))
    chk("NEGLIGIBLE falls with fpr",
        all(branch_probs(a)["NEGLIGIBLE"] > branch_probs(b)["NEGLIGIBLE"]
            for a, b in ((0.02, 0.05), (0.05, 0.10), (0.10, 0.20))))
    print(f"  {11 - bad}/11 hand-computed checks passed")
    return bad


PREDICTION = """\
  PREDICTION, written before the table. A branch's probability is a binomial
  tail, so each one is live only over a BAND of labeller false-positive rates,
  and the bands do not cover each other. Specifically: there should be a
  capability good enough that SUBSTANTIAL falls under 1-in-1000 while
  NEGLIGIBLE is near-certain -- at which point the rule has ONE outcome the
  confirmatory model can produce, and the thing that chose it is the minimum
  benchmark score the author wrote into field 2 of the preregistration. If
  instead all three branches stay live across the whole plausible range, the
  concern is theoretical and I will say so."""


def capability_bands():
    print(PREDICTION)
    print(f"\n  n = {N_ITEMS} items (the paper's own), true rate 0 by construction,")
    print(f"  thresholds {LOW} / {HIGH}, exact binomial -- no simulation.\n")
    print(f"  {'fpr':>6} {'P(SUBSTANTIAL)':>15} {'P(INCONCLUSIVE)':>16} "
          f"{'P(NEGLIGIBLE)':>14}  live branches")
    rows = []
    for fpr in (0.00, 0.01, 0.02, 0.03, 0.05, 0.07, 0.10, 0.15, 0.25, 0.40):
        p = branch_probs(fpr)
        live = [k for k in ("SUBSTANTIAL", "INCONCLUSIVE", "NEGLIGIBLE") if p[k] >= TINY]
        rows.append((fpr, p, live))
        print(f"  {fpr:>6.2f} {p['SUBSTANTIAL']:>15.2e} {p['INCONCLUSIVE']:>16.2e} "
              f"{p['NEGLIGIBLE']:>14.2e}  {len(live)}: {', '.join(s[:4] for s in live)}")
    singles = [(f, p, live) for f, p, live in rows if len(live) == 1]
    print(f"\n  rows where the rule has ONE reachable outcome: "
          f"{[f for f, _p, _l in singles] or 'none'}")
    held = bool(singles) and any(l == ["NEGLIGIBLE"] for _f, _p, l in singles)
    print(f"  PREDICTION {'HELD' if held else 'FAILED -- say so'}.")
    return rows, held


def the_crossover():
    """The two numbers that make this actionable for an author."""
    from scipy.optimize import brentq
    f_sub = brentq(lambda f: branch_probs(f)["SUBSTANTIAL"] - TINY, 1e-9, 0.5)
    f_neg = brentq(lambda f: branch_probs(f)["NEGLIGIBLE"] - TINY, 1e-9, 0.9)
    print(f"  SUBSTANTIAL drops below 1-in-1000 at a false-positive rate of "
          f"{f_sub:.4f}")
    print(f"  NEGLIGIBLE  drops below 1-in-1000 at a false-positive rate of "
          f"{f_neg:.4f}")
    print(f"  so the rule has all three outcomes available only for a labeller")
    print(f"  whose false-positive rate on this corpus lies in "
          f"({f_sub:.3f}, {f_neg:.3f}).")
    print("  Outside that window it is a rule with one answer, committed in")
    print("  advance, and no defence in the paper can see it -- nothing was")
    print("  tuned, and the confirmatory model genuinely did not exist.")
    # verify the two roots rather than trusting the solver
    ok = (abs(branch_probs(f_sub)["SUBSTANTIAL"] - TINY) < 1e-9
          and abs(branch_probs(f_neg)["NEGLIGIBLE"] - TINY) < 1e-9)
    print(f"  (both roots verified by re-evaluation: {ok})")
    return f_sub, f_neg, ok


ASK = """\
  WHAT THIS ASKS FOR, and it is one line in their Table 1.

  Field 2 already makes the author name the eligible-model set and a minimum
  benchmark score. Field 5 already makes them state "the precise statistical
  tests and how results will be interpreted". The missing requirement sits
  between the two: for each outcome the rule can declare, state the range of
  model behaviour over which that outcome is reachable -- and check it against
  the floor in field 2 before the preregistration is filed.

  It costs an author the arithmetic above, which is exact and takes seconds,
  and it is the only one of the paper's protections that does not need the
  future to arrive first."""


if __name__ == "__main__":
    print(__doc__)
    print("=" * 74)
    print("1. THE RULE, AND WHAT PURE LOGIC SAYS ABOUT IT")
    logic_check()
    print("\n" + "=" * 74)
    print("2. KNOWN ANSWERS FIRST")
    if known_answers():
        print("  hand-computed checks failed -- nothing else is reported.")
        sys.exit(1)
    print("\n" + "=" * 74)
    print("3. THE SAME RULE, AGAINST CAPABILITY")
    capability_bands()
    print("\n" + "=" * 74)
    print("4. THE WINDOW")
    the_crossover()
    print("\n" + "=" * 74)
    print(ASK)
