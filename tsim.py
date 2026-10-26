#!/usr/bin/env python3
"""tsim.py -- two one-sided t-tests, simulated from SUFFICIENT STATISTICS.

Fire 374. The first version of `equiv_demo.py` simulated raw data: a
(reps x n) array per group, which at reps=4000 and n=10000 is ~1 GB transient
on a machine that was already 19 GB into swap with Ivy in the headset. It also
was not needed. Both one-sided tests of a two-sample t with equal variances
are functions of the same two numbers -- the difference of means and the
pooled standard error -- so simulating those directly is EXACT and costs two
floats per replicate instead of 2n.

  D   ~ Normal(d, 2 sigma^2 / n)
  Sp^2 ~ sigma^2 * chi2(2n-2) / (2n-2)
  se  = sqrt(Sp^2 * 2/n),   df = 2n-2
  p vs 0      = sf(D/se, df)            # alternative="greater"
  p vs SESOI  = cdf((D - S)/se, df)     # alternative="less"

`--selftest` checks it against raw-data scipy on matched settings before any
of it is believed.
"""
from __future__ import annotations

import sys

import numpy as np
from scipy import stats


def p_pair(n, true_d, sesoi, reps, rng, sigma=1.0):
    """-> (p_vs_zero, p_vs_sesoi), each an array of length `reps`."""
    df = 2 * n - 2
    D = rng.normal(true_d, sigma * np.sqrt(2.0 / n), reps)
    sp2 = sigma ** 2 * rng.chisquare(df, reps) / df
    se = np.sqrt(sp2 * 2.0 / n)
    return stats.t.sf(D / se, df), stats.t.cdf((D - sesoi) / se, df)


def _selftest() -> int:
    checks = []

    def chk(name, cond, extra=""):
        checks.append((name, bool(cond), extra))

    # 1. against raw-data scipy, same settings, big enough to compare
    #    DISTRIBUTIONS (the two cannot be matched replicate-by-replicate).
    for n, d, S in ((40, 0.1, 0.2), (200, 0.0, 0.2), (200, 0.3, 0.2)):
        reps = 20000
        rng = np.random.default_rng(900 + n)
        p0a, pSa = p_pair(n, d, S, reps, rng)
        rng2 = np.random.default_rng(1900 + n)
        dog = rng2.normal(d, 1.0, (reps, n))
        cat = rng2.normal(0.0, 1.0, (reps, n))
        p0b = stats.ttest_ind(dog, cat, axis=1, alternative="greater").pvalue
        pSb = stats.ttest_ind(dog - S, cat, axis=1, alternative="less").pvalue
        for tag, a, b in (("p vs 0", p0a, p0b), ("p vs SESOI", pSa, pSb)):
            ks = stats.ks_2samp(a, b).pvalue
            chk(f"n={n} d={d}: {tag} same distribution as raw data (KS p={ks:.3f})",
                ks > 0.01, f"KS p={ks:.4f}")
            ra, rb = float(np.mean(a < 0.05)), float(np.mean(b < 0.05))
            chk(f"n={n} d={d}: {tag} rejection rate matches ({ra:.4f} vs {rb:.4f})",
                abs(ra - rb) < 0.012, f"{ra:.4f} vs {rb:.4f}")

    # 2. known answer: under a true null the one-sided rejection rate is alpha.
    rng = np.random.default_rng(77)
    p0, _ = p_pair(500, 0.0, 0.2, 60000, rng)
    rate = float(np.mean(p0 < 0.05))
    chk(f"true null -> one-sided rate ~ 0.05 (got {rate:.4f})", abs(rate - 0.05) < 0.004)

    # 3. known answer: at true d exactly the SESOI, the "below SESOI" test is
    #    also at its nominal alpha.
    rng = np.random.default_rng(78)
    _, pS = p_pair(500, 0.2, 0.2, 60000, rng)
    rate = float(np.mean(pS < 0.05))
    chk(f"true d = SESOI -> below-SESOI rate ~ 0.05 (got {rate:.4f})",
        abs(rate - 0.05) < 0.004)

    # 4. memory: a big run must not allocate anything like raw data.
    import tracemalloc
    tracemalloc.start()
    rng = np.random.default_rng(5)
    p_pair(10000, 0.1, 0.2, 4000, rng)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    raw = 2 * 4000 * 10000 * 8
    chk(f"n=10000 reps=4000 peak {peak/1e6:.1f} MB, under 1% of raw's {raw/1e6:.0f} MB",
        peak < raw * 0.01, f"{peak/1e6:.2f} MB")

    bad = sum(1 for _, ok, _ in checks if not ok)
    for name, ok, extra in checks:
        print(("  FAIL  " if not ok else "  ok    ") + name)
    print(f"{len(checks) - bad}/{len(checks)} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(_selftest() if "--selftest" in sys.argv else (print(__doc__) or 0))
