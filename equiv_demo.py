#!/usr/bin/env python3
"""equiv_demo.py -- the paper's recipe and the package's vignette, side by side.

Fire 374. Fire 373's census of 18 distinct scienceverse rules flagged two
"reachable fourth state" hits in `vignettes/sim.Rmd` -- rules where
corroboration and falsification can BOTH hold, which `R/study_eval.R` routes
to `inconclusive` in an unannotated else-branch. I reported that as a state
with no name in a three-verdict scheme and left it there.

It is sharper than that, and the sharpening is not a bug report.

The paper states the recipe twice on page 4, once on effects and once on
confidence intervals, and BOTH times corroboration carries a second conjunct:
the effect must be greater than zero AND not smaller than the SESOI. On a
single measure that second conjunct is exactly the negation of the
falsification criterion, so the paper's recipe is mutually exclusive by
construction -- and the paper's flagship 4- and 12-criterion kinship example
came back clean in fire 373's census.

`vignettes/sim.Rmd` drops the second conjunct. Its corroboration is
"significantly happier than cat owners", full stop. Its own English gloss says
exactly that, so this is not a coding slip -- it is a weaker recipe that reads
perfectly naturally. What it costs is the one result pattern a SESOI exists to
catch: an effect reliably above zero and reliably below the SESOI.

Run it and the two encodings disagree on exactly that pattern. The paper's
recipe calls it `falsify`. The vignette's calls it `inconclusive`.

Nothing here needs data. The last section computes a real pair of t-tests
anyway, because "logically possible" and "statistically ordinary" are
different claims and only one of them is interesting.
"""
from __future__ import annotations

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import reach as R                 # noqa: E402
import tsim                       # noqa: E402
from compare import compare, render   # noqa: E402

PAPER = """\
Lakens & DeBruine 2021, AMPPS 4(2), doi:10.1177/2515245920970949, p. 4,
section "What Does a Machine-Readable ... Prediction Look Like?" -- verbatim:

  "we might conclude that the study's prediction is corroborated when we can
   statistically conclude that the observed mean difference for at least one
   measure is both greater than 0 and not smaller than the smallest effect
   size of interest (SESOI). The prediction is falsified if both effects are
   smaller than the SESOI. Any other pattern of results, such as both effects
   being neither significantly larger than 0 nor smaller than the SESOI, is
   inconclusive."

and, made exact on one measure a few lines later:

  "we can conclude that we have corroborated our prediction if at least one of
   our 97.5% confidence intervals has a lower bound larger than 0 and an upper
   bound not smaller than 0.2. We can decide that our prediction is falsified
   if the upper bounds of both 97.5% confidence intervals are smaller than
   0.2, and our data are inconclusive in all other situations."
"""

VIGNETTE = """\
scienceverse@97d4054, vignettes/sim.Rmd lines 87-95 -- verbatim:

  add_criterion("happy_c", "p.value", "<", 0.05)      # t-test vs 0
  add_criterion("happy_f", "p.value", "<", 0.05)      # t-test vs mu = 0.2 (SESOI)
  add_eval("corroboration", "happy_c",
           "The hypothesis will be corroborated if dog owners are
            significantly happier than cat owners.")
  add_eval("falsification", "happy_f",
           "The hypothesis will be falsified if dog owners are significantly
            less than 0.2 units happier than cat owners.")
"""

# ---------------------------------------------------------------- encodings
# Shared vocabulary, stated so the verdict is checkable: `above0` is the
# "greater than 0" test and `belowS` is the "smaller than the SESOI" test.
# In the paper's CI form these are conf.int[1] > 0 and conf.int[2] < 0.2; in
# the vignette they are the two one-sided p values. The LOGICAL STRUCTURE is
# what differs, and it is the only thing compared here.

ABOVE0 = R.Criterion("above0", "t.conf.int[1]", ">", 0.0)
BELOWS = R.Criterion("belowS", "t.conf.int[2]", "<", 0.2)
# a confidence interval's lower bound cannot exceed its upper bound.
CI_ORDER = [("t.conf.int[1]", "<", "t.conf.int[2]")]

PAPER_REG = R.Registration(
    name="paper p.4 (CI form, one measure)",
    criteria=[ABOVE0, BELOWS],
    corroboration="above0 & !belowS",   # "lower bound > 0 AND upper bound NOT < SESOI"
    falsification="belowS",             # "upper bound smaller than SESOI"
    relations=CI_ORDER,
    source="Lakens & DeBruine 2021 p. 4",
)

VIGNETTE_REG = R.Registration(
    name="sim.Rmd (as written)",
    criteria=[ABOVE0, BELOWS],
    corroboration="above0",             # the second conjunct is not there
    falsification="belowS",
    relations=CI_ORDER,
    source="scienceverse@97d4054 vignettes/sim.Rmd",
)


def known_answers() -> int:
    """Hand-computed first, so nothing below is believed on the program's word."""
    bad = 0

    def chk(name, cond):
        nonlocal bad
        if not cond:
            print(f"  FAIL  {name}")
            bad += 1

    rp = R.analyse(PAPER_REG)
    rv = R.analyse(VIGNETTE_REG)
    # By hand, paper: (lo=T,hi=F)->corroborate  (hi=T)->falsify
    #                 (lo=F,hi=F)->inconclusive.  C and F cannot both hold.
    chk("paper: all three verdicts reachable",
        all(rp.prop_reachable[v] for v in R.VERDICTS))
    chk("paper: no C-and-F overlap", not rp.overlap_prop)
    chk("paper: every verdict has a verified numeric witness",
        all(rp.witness[v] is not None for v in R.VERDICTS))
    # By hand, vignette: (lo=T,hi=T) -> C and F both true -> inconclusive.
    chk("vignette: C and F can both hold", rv.overlap_prop)
    chk("vignette: the overlap has a verified witness", rv.overlap_witness is not None)
    chk("vignette: all three verdicts still reachable",
        all(rv.prop_reachable[v] for v in R.VERDICTS))
    # the witness must really satisfy both criteria.
    w = rv.overlap_witness or {}
    chk("vignette overlap witness: lower bound > 0 and upper bound < 0.2",
        bool(w) and w["t.conf.int[1]"] > 0 and w["t.conf.int[2]"] < 0.2)
    chk("vignette overlap witness: interval is ordered",
        bool(w) and w["t.conf.int[1]"] < w["t.conf.int[2]"])
    # and the diff, by hand: exactly one feasible pattern, falsify vs inconclusive.
    d = compare(PAPER_REG, VIGNETTE_REG)
    chk("diff: exactly one feasible disagreement", len(d.disagreements) == 1)
    chk("diff: paper=falsify where vignette=inconclusive",
        d.pairs() == {("falsify", "inconclusive"): 1})
    print(f"  {11 - bad}/11 hand-computed checks passed")
    return bad


def _cell_verdicts():
    """verdict per (above0, belowS) cell, for each encoding. Four cells only,
    so the simulations never evaluate a rule per replicate -- they count cells
    and look the verdict up. Same answer, and it is the whole of the speedup."""
    asts = {reg.name: (R.parse_expr(reg.corroboration), R.parse_expr(reg.falsification))
            for reg in (PAPER_REG, VIGNETTE_REG)}
    table = {}
    for a0 in (False, True):
        for bS in (False, True):
            env = {"above0": a0, "belowS": bS}
            table[(a0, bS)] = tuple(
                R.verdict_of(R.eval_expr(c, env), R.eval_expr(f, env))
                for c, f in (asts[PAPER_REG.name], asts[VIGNETTE_REG.name]))
    return table


CELLS = None   # filled on first use


def _rates(n, true_d, sesoi, reps, rng):
    """-> dict of outcome frequencies for this (n, true_d)."""
    global CELLS
    if CELLS is None:
        CELLS = _cell_verdicts()
    import numpy as np
    p0, pS = tsim.p_pair(n, true_d, sesoi, reps, rng)
    a0, bS = p0 < 0.05, pS < 0.05
    out = {"both": 0.0, "paper_falsify": 0.0, "vign_inconcl": 0.0,
           "vign_falsify": 0.0, "disagree": 0.0}
    for (ca, cb), (va, vb) in CELLS.items():
        w = float(np.mean((a0 == ca) & (bS == cb)))
        if ca and cb:
            out["both"] += w
        if va == "falsify":
            out["paper_falsify"] += w
        if vb == "inconclusive":
            out["vign_inconcl"] += w
        if vb == "falsify":
            out["vign_falsify"] += w
        if va != vb:
            out["disagree"] += w
    return out


def real_numbers(n=500, true_d=0.1, sesoi=0.2, seed=374):
    """One ordinary sample, run through the vignette's OWN two tests."""
    import numpy as np
    from scipy import stats

    rng = np.random.default_rng(seed)
    dog = rng.normal(true_d, 1.0, n)
    cat = rng.normal(0.0, 1.0, n)
    # exactly sim.Rmd: t.test(dog, cat, mu=0, alternative="greater")
    #              and t.test(dog, cat, mu=0.2, alternative="less")
    p0 = stats.ttest_ind(dog, cat, alternative="greater").pvalue
    pS = stats.ttest_ind(dog - sesoi, cat, alternative="less").pvalue
    print(f"  n = {n} per group, true difference {true_d}, SESOI {sesoi}, seed {seed}")
    print(f"  observed mean difference  {dog.mean() - cat.mean():+.4f}")
    print(f"  p vs 0     = {p0:.5f}  ({'<' if p0 < .05 else '>='} .05)  -> above0 = {p0 < .05}")
    print(f"  p vs SESOI = {pS:.5f}  ({'<' if pS < .05 else '>='} .05)  -> belowS = {pS < .05}")
    env = {"above0": p0 < 0.05, "belowS": pS < 0.05}
    for reg in (PAPER_REG, VIGNETTE_REG):
        c = R.eval_expr(R.parse_expr(reg.corroboration), env)
        f = R.eval_expr(R.parse_expr(reg.falsification), env)
        print(f"  {reg.name:<34} -> {R.verdict_of(c, f)}")
    return env


PREDICTION_1 = """\
  PREDICTION, written before the numbers and kept whatever they say: if the
  true difference lies strictly between 0 and the SESOI, both one-sided tests
  are testing a true alternative, so each becomes significant with probability
  -> 1 as n grows. So the overlap is not a corner case -- it is the ASYMPTOTIC
  outcome over that whole interval, and the vignette's rule converges to
  `inconclusive` exactly where more data buys certainty. If instead the
  overlap frequency peaks and falls away, the prediction is dead and this is a
  small-sample curiosity."""

PREDICTION_2 = """\
  PREDICTION: the disagreement is confined to the OPEN interval (0, SESOI) --
  the region a SESOI exists to adjudicate -- and the two encodings AGREE at a
  true difference of 0 and at anything above the SESOI."""

PREDICTION_3 = """\
  PREDICTION: the vignette's `falsify` branch is propositionally reachable, so
  reach.py passes it and so does branch coverage. But inside (0, SESOI) it
  demands "significantly below the SESOI AND NOT significantly above 0" --
  power on one test and a lack of it on the other. Its probability should go
  to ZERO as n grows: a branch only an underpowered study can reach."""

NS = (50, 100, 250, 500, 1000, 2000, 5000, 10000)
DS = (0.0, 0.02, 0.05, 0.10, 0.15, 0.18, 0.20, 0.25, 0.40)


def frequency_over_n(sesoi=0.2, true_d=0.1, reps=40000, seed=3740):
    import numpy as np
    print(PREDICTION_1)
    print(f"\n  true difference {true_d} (half the SESOI {sesoi}), {reps} reps per n\n")
    print(f"  {'n/group':>8} {'both sig':>9} {'paper=falsify':>14} {'vign=inconcl':>13} {'disagree':>9}")
    rows = []
    for n in NS:
        r = _rates(n, true_d, sesoi, reps, np.random.default_rng(seed + n))
        rows.append((n, r))
        print(f"  {n:>8} {r['both']:>9.3f} {r['paper_falsify']:>14.3f} "
              f"{r['vign_inconcl']:>13.3f} {r['disagree']:>9.3f}")
    held = (rows[-1][1]["both"] > 0.98
            and all(rows[i][1]["both"] <= rows[i + 1][1]["both"] + 0.01
                    for i in range(len(rows) - 1)))
    print(f"\n  monotone and -> 1 : {held}")
    print("  PREDICTION HELD." if held
          else "  PREDICTION FAILED -- say so, do not rescue it.")
    return rows, held


def vanishing_branch(sesoi=0.2, reps=40000, n=10000, seed=5550):
    import numpy as np
    print(PREDICTION_2)
    print(f"\n  (1) sweep, n = {n} per group, SESOI {sesoi}, {reps} reps")
    print(f"  {'true d':>8} {'region':<15} {'disagree':>9} {'paper=fals':>11} {'vign=fals':>10}")
    sweep = []
    for d in DS:
        r = _rates(n, d, sesoi, reps, np.random.default_rng(seed + int(d * 1000)))
        region = ("= 0" if d == 0 else "inside (0,S)" if 0 < d < sesoi
                  else "= SESOI" if d == sesoi else "above SESOI")
        sweep.append((d, region, r))
        print(f"  {d:>8.2f} {region:<15} {r['disagree']:>9.3f} "
              f"{r['paper_falsify']:>11.3f} {r['vign_falsify']:>10.3f}")
    inside = [r for _d, reg, r in sweep if reg == "inside (0,S)"]
    outside = [r for _d, reg, r in sweep if reg in ("= 0", "above SESOI")]
    conf = (all(r["disagree"] > 0.90 for r in inside)
            and all(r["disagree"] < 0.05 for r in outside))
    print(f"\n  confined to the open interval : {conf}")

    print("\n" + PREDICTION_3)
    print(f"\n  (2) the vignette's `falsify` branch as n grows, true d = 0.10")
    print(f"  {'n/group':>8} {'P(vignette=falsify)':>20} {'P(paper=falsify)':>18}")
    series = []
    for nn in NS:
        r = _rates(nn, 0.10, sesoi, reps, np.random.default_rng(seed + 7 + nn))
        series.append((nn, r["vign_falsify"], r["paper_falsify"]))
        print(f"  {nn:>8} {r['vign_falsify']:>20.4f} {r['paper_falsify']:>18.4f}")
    vanish = series[-1][1] < 0.01 and series[-1][1] < series[0][1]
    print(f"\n  goes to zero as the study improves : {vanish}")
    print(f"  PREDICTION 3 {'HELD' if vanish else 'FAILED'}.")
    if vanish:
        print("  A branch branch-coverage passes, that only an underpowered study")
        print("  can reach: reachable in logic, vanishing in practice.")
    if not conf:
        print("\n  🛑 PREDICTION 2 FAILED, AND THE FAILURE IS THE USEFUL PART.")
        print("  It is kept exactly as written. At a FIXED n the disagreement is NOT")
        print("  uniform over the open interval: there is a boundary layer at each")
        print("  end where one of the two tests is only partly powered -- at")
        print("  n = 10000, d = 0.02 and d = 0.18 both sit at ~0.41, not >0.90.")
        print("  'Confined to the open interval' is a statement about the LIMIT and")
        print("  I wrote it as a statement about a table. See prediction 4.")
    return sweep, series, conf and vanish


PREDICTION_4 = """\
  PREDICTION 4, the repaired version of 2, and it is sharper because it says
  what the boundary layer DOES. Both tests see the true difference only
  through a standardised distance: d*sqrt(n/2) for the test against 0, and
  (S-d)*sqrt(n/2) for the test against the SESOI. So (a) for any FIXED d
  strictly inside (0, S) the disagreement rate -> 1 as n grows, boundary layer
  and all; and (b) the layer's width in d shrinks like 1/sqrt(n), so plotting
  disagreement against d*sqrt(n/2) should collapse different n onto ONE curve.
  (b) is the real test -- (a) alone is implied by prediction 1."""


def boundary_layer(sesoi=0.2, reps=40000, seed=8800):
    """The failed prediction, repaired and re-tested on new numbers."""
    import numpy as np
    print(PREDICTION_4)

    print("\n  (a) a fixed d near the edge, as n grows: d = 0.02")
    print(f"  {'n/group':>9} {'disagree':>9}")
    rows = []
    for n in (10_000, 40_000, 160_000, 640_000):
        r = _rates(n, 0.02, sesoi, reps, np.random.default_rng(seed + n))
        rows.append((n, r["disagree"]))
        print(f"  {n:>9} {r['disagree']:>9.3f}")
    a_ok = rows[-1][1] > 0.98 and all(rows[i][1] <= rows[i + 1][1] + 0.01
                                      for i in range(len(rows) - 1))
    print(f"  fixed d inside -> 1 : {a_ok}")

    print("\n  (b) collapse: disagreement against the standardised distance")
    print("      z = d*sqrt(n/2). Same z, different n, should give the same rate.")
    zs = (1.0, 1.5, 2.0, 3.0, 4.0)
    print("      " + "z".rjust(5) + "".join(f"{'n='+str(n):>12}" for n in (2000, 10000, 50000)))
    grid = {}
    for z in zs:
        line = f"      {z:>5.1f}"
        for n in (2000, 10000, 50000):
            d = z * np.sqrt(2.0 / n)
            r = _rates(n, d, sesoi, reps,
                       np.random.default_rng(seed + n + int(z * 97)))
            grid[(z, n)] = r["disagree"]
            line += f"{r['disagree']:>12.3f}"
        print(line)
    spreads = [max(grid[(z, n)] for n in (2000, 10000, 50000))
               - min(grid[(z, n)] for n in (2000, 10000, 50000)) for z in zs]
    worst = max(spreads)
    b_ok = worst < 0.05
    print(f"\n      widest spread across n at fixed z : {worst:.3f}   collapse: {b_ok}")
    print(f"  PREDICTION 4 {'HELD' if (a_ok and b_ok) else 'FAILED'}.")
    print(f"  4(a) {'held' if a_ok else 'failed'}; 4(b) {'held' if b_ok else 'failed'}.")
    if not b_ok:
        print("\n  🛑 4(b) FAILED, and the shape of the failure names my mistake.")
        print("  The collapse is near-exact at z = 1.0, 1.5, 2.0 (spread <= 0.01)")
        print("  and breaks at z = 4, where n=2000 reads 0.748 against 0.991.")
        print("  Because there are TWO standardised distances, not one:")
        print("    z0 = d*sqrt(n/2)      the test against 0")
        print("    zS = (S-d)*sqrt(n/2)  the test against the SESOI")
        print("  and holding z0 fixed while n varies lets zS roam -- at z0=4 it is")
        print("  2.3 at n=2000 and 27.6 at n=50000. I collapsed a two-parameter")
        print("  function on one parameter. Prediction 5 holds both.")
    return rows, grid, a_ok and b_ok


PREDICTION_5 = """\
  PREDICTION 5, the repaired 4(b). The two tests are functions of the data
  only through (z0, zS) = (d, S-d) * sqrt(n/2), so the whole outcome
  distribution -- every cell, every verdict, both encodings -- should depend on
  n, d and S ONLY through that pair. Hold BOTH fixed and vary n by a factor of
  100 and every rate should be the same to simulation noise. That cannot be
  done with S fixed, because z0 + zS = S*sqrt(n/2); the SESOI has to be scaled
  too, which is the content of the claim rather than a dodge. The one thing
  left over is the degrees of freedom (2n-2), which only shrinks the t toward
  a normal as n grows, so any residual should be small and one-signed."""


def two_parameter_collapse(reps=40000, seed=9100):
    import numpy as np
    print(PREDICTION_5)
    print(f"\n  {'z0':>5} {'zS':>5}" + "".join(f"{'n='+str(n):>11}" for n in (500, 5000, 50000))
          + f"{'spread':>9}")
    worst = 0.0
    for z0, zS in ((1.0, 1.0), (2.0, 2.0), (4.0, 2.0), (2.0, 4.0), (3.0, 1.0), (1.0, 3.0)):
        vals = []
        line = f"  {z0:>5.1f} {zS:>5.1f}"
        for n in (500, 5000, 50000):
            k = np.sqrt(2.0 / n)
            d, S = z0 * k, (z0 + zS) * k
            r = _rates(n, d, S, reps,
                       np.random.default_rng(seed + n + int(z0 * 31 + zS * 7)))
            vals.append(r["disagree"])
            line += f"{r['disagree']:>11.3f}"
        spread = max(vals) - min(vals)
        worst = max(worst, spread)
        print(line + f"{spread:>9.3f}")
    ok = worst < 0.02
    print(f"\n  widest spread across a 100x range of n : {worst:.3f}")
    print(f"  PREDICTION 5 {'HELD' if ok else 'FAILED'}.")
    if ok:
        print("  So the disagreement is governed by two standardised distances and")
        print("  nothing else. Read it back into the registration: whether the")
        print("  vignette's `falsify` branch can fire is set by the study's POWER")
        print("  against 0 and against the SESOI -- not by the hypothesis, not by")
        print("  the prose, and not by anything a reviewer sees.")
    return worst, ok


if __name__ == "__main__":
    print(__doc__)
    print("=" * 74)
    print(PAPER)
    print(VIGNETTE)
    print("=" * 74)
    print("ENCODINGS, printed because a verdict on prose is worthless without them:")
    for reg in (PAPER_REG, VIGNETTE_REG):
        print(f"\n  {reg.name}   [{reg.source}]")
        for c in reg.criteria:
            print(f"    {c.id:<8} = {c.var} {c.op} {c.value}")
        print(f"    corroboration = {reg.corroboration}")
        print(f"    falsification = {reg.falsification}")
        print(f"    relations     = {reg.relations}")
    print("\n" + "=" * 74)
    print("KNOWN ANSWERS FIRST")
    bad = known_answers()
    if bad:
        print("\nhand-computed checks failed -- not reporting anything else.")
        sys.exit(1)
    print("\n" + "=" * 74)
    print("REACHABILITY, each rule on its own")
    for reg in (PAPER_REG, VIGNETTE_REG):
        rep = R.analyse(reg)
        reach = ", ".join(v for v in R.VERDICTS if rep.prop_reachable[v])
        print(f"\n  {reg.name}")
        print(f"    reachable verdicts : {reach}")
        print(f"    C and F both true  : {rep.overlap_prop}"
              + ("  witness " + str({k: round(v, 4) for k, v in rep.overlap_witness.items()})
                 if rep.overlap_witness else ""))
    print("\n" + "=" * 74)
    print("THE DIFF")
    print(render(compare(PAPER_REG, VIGNETTE_REG)))
    print("\n" + "=" * 74)
    print("IS THE DISAGREEING PATTERN ORDINARY?")
    real_numbers()
    print("\n" + "=" * 74)
    print("HOW OFTEN?")
    frequency_over_n()
    print("\n" + "=" * 74)
    print("WHERE DOES IT LIVE, AND WHAT HAPPENS TO `falsify`?")
    vanishing_branch()
    print("\n" + "=" * 74)
    print("THE FAILED PREDICTION, REPAIRED")
    boundary_layer()
    print("\n" + "=" * 74)
    print("AND THE REPAIR, REPAIRED")
    two_parameter_collapse()
