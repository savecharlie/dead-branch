"""staged_demo.py -- the check applied to a staged decision rule written in
PROSE, not in a format, because that is what preregistration templates actually
ask for.

The rule is quoted verbatim from Vaccaro, "Preregistration for Experiments with
AI Agents", arXiv:2606.11217v1, Sec. 4:

    "Researchers may preregister an initial design with explicit decision rules
     for subsequent stages: 'If pilot data indicate floor effects (accuracy <
     20%), we will increase context length by 500 tokens; if ceiling effects
     (accuracy > 90%), we will use more difficult items from the backup set.'
     The key constraint is that these decision rules must be specified in
     advance, not invented post hoc."

Encoding a prose rule is an act of interpretation, so the encoding is printed
beside the verdict. Without that, the verdict is worthless.

The point this makes is not that her example is broken -- it is clean, and the
run below says so. The point is that "specified in advance" is the only
constraint the passage names, and it is necessary rather than sufficient. The
rule in ladder_demo.py was specified in advance, time-stamped, and committed
before a single call was spent, and it still had one reachable output.

Run: python3 staged_demo.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reach as R  # noqa: E402

# the encoding, printed so a reader can disagree with it
ENCODING = """\
  variable   pilot.accuracy, a proportion, domain [0, 1]
  floor      pilot.accuracy < 0.20
  ceiling    pilot.accuracy > 0.90
  verdict    floor   -> "lengthen context by 500 tokens"
             ceiling -> "harder items from the backup set"
             neither -> "proceed as designed"   (not stated; the only
                        remaining option, and the passage implies it)
"""

CRITERIA = [R.Criterion("floor", "pilot.accuracy", "<", 0.20),
            R.Criterion("ceiling", "pilot.accuracy", ">", 0.90)]
DOMAINS = {"pilot.accuracy": (0.0, 1.0)}
DECLARED = ["lengthen context by 500 tokens",
            "harder items from the backup set",
            "proceed as designed"]


def staged_rule(env):
    if env["floor"]:
        return "lengthen context by 500 tokens"
    if env["ceiling"]:
        return "harder items from the backup set"
    return "proceed as designed"


if __name__ == "__main__":
    print(__doc__.split("Run:")[0].rstrip())
    print("\nENCODING\n" + ENCODING)
    counts, wit, missing = R.reachable_verdicts(
        CRITERIA, staged_rule, domains=DOMAINS, declared=DECLARED)
    print("RESULT")
    print(f"  {2 ** len(CRITERIA)} truth assignments over {len(CRITERIA)} criteria")
    for v in DECLARED:
        n = counts.get(v, 0)
        w = wit.get(v)
        if n == 0:
            print(f"  UNREACHABLE   {v}")
        elif w is None:
            print(f"  no witness    {v}   ({n} assignments, none realisable "
                  f"as a number)")
        else:
            x = ", ".join(f"{k}={val:g}" for k, val in sorted(w.items()))
            print(f"  reachable     {v}   ({n} assignments, e.g. {x})")
    print(f"\n  unreachable but declared: {missing or 'none'}")
    # floor and ceiling cannot both hold: one accuracy cannot be under .20 and
    # over .90, so the overlap is impossible rather than merely unlikely.
    both = R.numeric_witness(
        R.Registration("x", CRITERIA, "floor", "ceiling", domains=DOMAINS),
        {"floor": True, "ceiling": True})
    print(f"  floor and ceiling together: "
          f"{'POSSIBLE -- ' + str(both) if both else 'impossible, as it should be'}")
    assert not missing and both is None
    print("\nClean. Which is the result that makes the check worth running on "
          "something else.")
