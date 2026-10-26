#!/usr/bin/env python3
"""colling_demo.py -- a REAL preregistration, and the one the paper holds up.

Fire 374. Every rule checked in this repository so far has come out of a
package's own files, which is a fair complaint to make of the claim. This one
is a published Registered Replication Report's analysis plan, written in prose,
filed on OSF before the data: Colling, Szucs, De Marco, Cipora, Ulrich, Nuerk,
... & McShane (2020), *Registered Replication Report on Fischer et al. (2003)*,
AMPPS; plan at https://osf.io/6a2ny/ (the OSF GUID resolves to
`Colling+Szucs16_RegRep_ProposedAnalysis.docx`, downloaded and extracted to
`reading/colling-rrr/`).

**It is the example Lakens & DeBruine choose.** Verbatim from their p. 3:

  "In Registered Replication Reports published in this journal, authors are
   asked to explicitly specify when a replication corroborates the original
   finding. For example, in the analysis plan of the Registered Replication
   Report on Fischer et al. (2003) by Colling et al. (2020), available at
   https://osf.io/6a2ny/, a clear decision rule for corroboration is
   specified: ..."

So this is not a rule nobody vetted. It is a seventeen-lab replication's
pre-registered rule, quoted approvingly in the paper that proposed making such
rules machine-readable. Two things come out of running the check on it, and
neither is a criticism of the authors' conduct.

ENCODING A PROSE RULE IS INTERPRETATION, so both readings of the one ambiguous
clause are printed with their verdicts, and you should disagree with an
encoding rather than with a number.
"""
from __future__ import annotations

import itertools
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import reach as R                      # noqa: E402

# ------------------------------------------------------------------ the rule
RULE = """\
Model 1, verbatim from the plan (reading/colling-rrr/plan.txt):

  "The primary model will be a multivariate meta-analytic model that does not
   account for any of the moderators. If the congruency effect is positive and
   statistically significantly different from zero in the 500 ms and 750 ms
   delay conditions but not statistically significantly different from zero in
   the 250 ms and 1000 ms delay conditions, we will consider the findings of
   Fischer et al. (2003) to be replicated within the limits they propose. If it
   is positive and statistically significantly different from zero in
   conditions beyond the 500 ms and 750 ms delay conditions, we can consider
   the findings of Fischer et al. (2003) to be replicated but for the effect to
   be more general than they originally proposed."
"""

DELAYS = (250, 500, 750, 1000)
IDS = {d: f"sig{d}" for d in DELAYS}   # "positive AND significantly != 0" at that delay


def verdict_strict(env):
    """Reading A: 'beyond the 500 and 750 conditions' presupposes those two."""
    core = env["sig500"] and env["sig750"]
    extra = env["sig250"] or env["sig1000"]
    if core and not extra:
        return "replicated within their limits"
    if core and extra:
        return "replicated, more general"
    return "NO DECLARED VERDICT"


def verdict_loose(env):
    """Reading B: 'in conditions beyond' names only the extra conditions, so
    significance at 250 or 1000 alone triggers the more-general verdict."""
    core = env["sig500"] and env["sig750"]
    extra = env["sig250"] or env["sig1000"]
    if core and not extra:
        return "replicated within their limits"
    if extra:
        return "replicated, more general"
    return "NO DECLARED VERDICT"


def logic(verdict_fn, name):
    crit = [R.Criterion(IDS[d], f"z{d}", ">", 1.96) for d in DELAYS]
    reachable, witness, undeclared = R.reachable_verdicts(
        crit, lambda e: verdict_fn(e),
        declared=["replicated within their limits", "replicated, more general"])
    total = 2 ** len(DELAYS)
    print(f"\n  {name}")
    for v, k in sorted(reachable.items(), key=lambda kv: -kv[1]):
        print(f"    {v:<30} {k:>3} of {total} patterns")
    print(f"    declared but unreachable: {undeclared or 'none'}")
    unnamed = reachable.get("NO DECLARED VERDICT", 0)
    print(f"    -> {unnamed}/{total} result patterns have NO verdict the plan names")
    return reachable


FINDING_1 = """\
  FINDING 1 -- the plan names two grades of success and no failure.

  Both readings leave a block of result patterns with no declared verdict, and
  every one of them is a result in which the replication did NOT find the
  effect. The plan says what counts as "replicated within their limits" and
  what counts as "replicated, more general". It does not say, anywhere in Model
  1, what counts as not replicated.

  That is exactly the complaint Lakens & DeBruine open with -- "researchers
  often do not explicitly state what would corroborate or falsify their
  prediction" -- and it is sitting inside the example they chose to illustrate a
  rule done well. Which is the point: the corroboration half was specified
  carefully enough to quote, and the falsification half was not specified at
  all, and nobody noticed, because no tool asks.

  It is also why the two readings matter so differently. Under reading A the
  unnamed block is most of the space; under reading B it is a corner. The
  prose does not decide between them.

  SCOPED, because this is a claim about somebody's document. The file is the
  one the paper links to and the only thing the OSF GUID resolves to:
  `Colling+Szucs16_RegRep_ProposedAnalysis.docx`, the Stage 1 proposed
  analysis. Measured over its extracted text: the word stem "replicat" appears
  3 times, all three inside the Model 1 sentence above, and there are ZERO
  occurrences of "not replicat", "fail to replicat", "does not replicat",
  "unsuccessful", "no evidence", "null result" or "falsif". The published
  Registered Report may frame the inference somewhere this document does not,
  and that would not change the finding, which is about the rule a reader
  following the citation actually gets."""


def power_table():
    """FINDING 2, and it needs no simulation: exact normal-theory arithmetic."""
    from scipy.stats import norm

    print("""\
  FINDING 2 -- the "within their limits" verdict is a VANISHING BRANCH, and it
  is the cleanest instance I have found.

  To earn it, the replication must find significance at 500 and 750 and must
  FAIL to find it at 250 and 1000. Two of its four conditions are demands for
  a non-significant result. Power helps the first pair and hurts the second,
  so the verdict's probability depends on an exact point null being exactly
  true at the other two delays.

  PREDICTION, before the table: if the true effect at 250 and 1000 is exactly
  zero the verdict's probability rises to about 0.95^2 = 0.903 and stays there;
  if it is ANY nonzero value, however small, the probability rises, turns over,
  and goes to zero. A bigger replication becomes LESS able to confirm the
  original's limits. If instead the curves all flatten out high, the prediction
  is dead and this is not a real asymmetry.

  Stated assumptions, because they are doing work: each delay's congruency
  effect is estimated with standard error 1/sqrt(N) in units of the effect;
  "significantly different from zero" is two-sided alpha = 0.05 so the cut is
  |z| > 1.96, and "positive and significant" is z > +1.96; the four delays are
  treated as independent, where the plan's actual model is multivariate with
  correlated delays -- correlation would change the numbers and not the
  direction, since the non-significance demand is unaffected by it.
  True effect at 500 and 750 fixed at 0.20.""")
    d_core = 0.20
    print(f"\n  {'N':>7}" + "".join(f"{'d=' + format(x, '.2f'):>11}"
                                    for x in (0.0, 0.02, 0.05, 0.10)))
    print("         " + "  true effect at 250 ms and 1000 ms ->")
    rows = {}
    for N in (50, 100, 200, 500, 1000, 2000, 5000, 20000, 100000):
        line = f"  {N:>7}"
        for d_off in (0.0, 0.02, 0.05, 0.10):
            r = N ** 0.5
            p_pos_sig = float(norm.sf(1.96 - d_core * r))          # z > 1.96
            p_ns = float(norm.cdf(1.96 - d_off * r)
                         - norm.cdf(-1.96 - d_off * r))            # |z| < 1.96
            p = p_pos_sig ** 2 * p_ns ** 2
            rows.setdefault(d_off, []).append((N, p))
            line += f"{p:>11.4f}"
        print(line)
    null_ok = abs(rows[0.0][-1][1] - 0.95 ** 2) < 0.002
    vanish_ok = all(rows[d][-1][1] < 1e-3 and max(p for _n, p in rows[d]) > 0.1
                    for d in (0.02, 0.05, 0.10))
    print(f"\n  exact-zero column settles at 0.95^2 = {0.95**2:.4f} : {null_ok}")
    print(f"  every nonzero column peaks and then goes to zero : {vanish_ok}")
    print(f"  PREDICTION {'HELD' if (null_ok and vanish_ok) else 'FAILED -- say so'}.")
    for d in (0.02, 0.05, 0.10):
        peak = max(rows[d], key=lambda t: t[1])
        print(f"    true offset {d:.2f}: best chance {peak[1]:.4f} at N = {peak[0]}, "
              f"then down to {rows[d][-1][1]:.2e} at N = {rows[d][-1][0]}")
    return rows, null_ok and vanish_ok


CLOSING = """\
  WHAT THIS IS AND IS NOT.

  It is not an error in the replication. The team ran it, reported it, and the
  paper is in the literature; the rule was specified in advance, in public, and
  in enough detail to quote, which is more than most.

  It is that two properties of that rule are invisible to every check in the
  chain it passed through. Its failure verdict is not written down anywhere, and
  its primary success verdict is one that a larger study is less likely to be
  able to reach. Neither is a matter of conduct and neither is caught by a
  time stamp, a reviewer, or a reading of the prose. Both are arithmetic over
  the clauses, and the second one needs a sentence about power that no template
  asks for."""


if __name__ == "__main__":
    print(__doc__)
    print("=" * 74)
    print(RULE)
    print("=" * 74)
    print("ENCODINGS -- the one ambiguous clause, read both ways")
    print("  criteria: sig250, sig500, sig750, sig1000")
    print("            = 'positive and statistically significantly different from zero'")
    print("              at that delay, i.e. z > +1.96")
    print("  reading A: 'beyond the 500 and 750 conditions' PRESUPPOSES those two")
    print("  reading B: 'in conditions beyond' names only the extra conditions")
    a = logic(verdict_strict, "reading A (strict)")
    b = logic(verdict_loose, "reading B (loose)")
    print("\n" + "=" * 74)
    print(FINDING_1)
    print("\n  the two readings, side by side:")
    for k in sorted(set(a) | set(b)):
        print(f"    {k:<30} A: {a.get(k,0):>3}   B: {b.get(k,0):>3}")
    print("\n" + "=" * 74)
    power_table()
    print("\n" + "=" * 74)
    print(CLOSING)
