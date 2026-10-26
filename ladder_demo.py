"""ladder_demo.py -- the rule that cost three days of quota, run through the
check that would have taken five minutes.

Fire 369's arm 5 pre-registered a six-way ladder over a replication of a
published identifier-rule result. Six cells, one per ladder rung j = 1..6, each
holding an above-threshold participation rate; two clauses decided the verdict:

  G12  the arm is VALID only if the j = 1 cell is at or below 0.25
  G11  the resolution depth D is the SMALLEST j whose cell is at or below 0.25

Both clauses were written the same evening, forty minutes apart, each one
correct read on its own. Put side by side they read the same cell in opposite
directions, and the consequence is below: on every arm G12 admits, G11 can only
ever return 1. The rule has ONE reachable output, so no data it would accept
could have falsified it.

Forty rows of data were collected to feed it, over three days of quota
(15 on 24 Oct, 19 on the 25th, 6 on the 26th -- counted off the UTC stamps
in answers35_q3_think_ladder.json, not remembered).

Run: python3 ladder_demo.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reach as R  # noqa: E402

# One criterion per rung: "the above-threshold rate in cell j is <= 0.25".
# scienceverse has no <= so the registered form was "< 0.2500001"; the exact
# operator does not matter to the argument and the check does not care.
RUNGS = [1, 2, 3, 4, 5, 6]
CRITERIA = [R.Criterion(f"c{j}", f"cell{j}.rate", "<", 0.2500001)
            for j in RUNGS]
DOMAINS = {f"cell{j}.rate": (0.0, 1.0) for j in RUNGS}

# every verdict the registration said it could return
DECLARED = ["invalid arm"] + [f"D = {j}" for j in RUNGS] + ["no ceiling"]


def registered_rule(env):
    """G12 then G11, exactly as registered."""
    if not env["c1"]:                       # G12: anchor must pass
        return "invalid arm"
    for j in RUNGS:                         # G11: smallest rung at or below .25
        if env[f"c{j}"]:
            return f"D = {j}"
    return "no ceiling"


def corrected_rule(env):
    """Amendment 9. Participation means the value is below the threshold, so a
    HIGH above-threshold rate at rung j means the model resolved AT MOST j
    digits: the ladder steps UP at j = K0, it does not step down. The repair
    has exactly one degree of freedom and the geometry fixes it."""
    if not env["c1"]:
        return "invalid arm"
    for j in RUNGS:
        if not env[f"c{j}"]:                # first rung that FAILS is the depth
            return f"D = {j - 1}" if j > 1 else "invalid arm"
    return "no ceiling"


def show(name, fn):
    counts, wit, missing = R.reachable_verdicts(
        CRITERIA, fn, domains=DOMAINS, declared=DECLARED)
    print(f"\n{name}")
    print(f"  {2 ** len(CRITERIA)} truth assignments over {len(CRITERIA)} criteria")
    print(f"  reachable verdicts: {len(counts)} of {len(DECLARED)} declared")
    for v, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        w = wit.get(v)
        tag = "" if w else "   (no numeric witness)"
        print(f"    {v:<12} {n:>3} assignments{tag}")
    if missing:
        print(f"  UNREACHABLE, though declared: {', '.join(missing)}")
    return counts, missing


if __name__ == "__main__":
    reg_counts, reg_missing = show("AS REGISTERED (fire 369)", registered_rule)
    cor_counts, cor_missing = show("AS CORRECTED (Amendment 9)", corrected_rule)
    print()
    depth_outs = [v for v in reg_counts if v.startswith("D = ")]
    print(f"As registered, the rule can name {len(depth_outs)} depth: "
          f"{', '.join(sorted(depth_outs))}.")
    print(f"As corrected, it can name {len([v for v in cor_counts if v.startswith('D = ')])}.")
    assert depth_outs == ["D = 1"], depth_outs
    print("\nThe check is five minutes of arithmetic over the clauses and needs "
          "no data at all.\nThe arm it was registered for took three days of a "
          "free-tier quota to collect.")
