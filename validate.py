"""validate.py -- reach.py is an instrument, so it gets validated on worlds
whose answer I worked out by hand BEFORE it is allowed to say anything about a
real registration.

That is Law 44, which exists because in fire 369 I pre-registered a decision
rule, never ran it on anything, and spent three days of a free-tier quota
collecting data for a rule that had exactly one reachable output. The whole
point of reach.py is that the defect is mechanically detectable; the whole
point of this file is that so is a broken reach.py.

Run:  python3 validate.py          (expects 14/14)
      python3 validate.py --force-red   (breaks the semantics on purpose and
                                         checks this suite goes red)
"""
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import reach as R  # noqa: E402

C = R.Criterion


def reg(name, crits, corrob, falsify, **kw):
    return R.Registration(name, crits, corrob, falsify, **kw)


CASES = []


def case(fn):
    CASES.append(fn)
    return fn


# --- the three verdicts, each made the truth on purpose -------------------

@case
def exact_complement():
    """C = x, F = !x partitions every possible result. 'inconclusive' is then
    unreachable, and that is DELIBERATE, not a defect -- so no flag."""
    r = R.analyse(reg("complement", [C("x", "p", "<", 0.05)], "x", "!x"))
    assert r.prop_reachable["corroborate"], r
    assert r.prop_reachable["falsify"], r
    assert not r.prop_reachable["inconclusive"], r
    assert not r.overlap_prop, r
    assert r.flags == [], r.flags
    assert r.witness["corroborate"] is not None and r.witness["falsify"] is not None, r


@case
def all_three_reachable():
    """C = a & b, F = !a & !b leaves a genuine middle."""
    r = R.analyse(reg("three", [C("a", "p", "<", 0.05), C("b", "d", ">", 0)],
                      "a & b", "!a & !b"))
    assert all(r.prop_reachable[v] for v in R.VERDICTS), r
    assert not r.overlap_prop and r.flags == [], r


# --- the defect this exists for -----------------------------------------

@case
def falsify_implied_by_corroborate():
    """F => C, so F can never be the verdict. Dead branch, and an overlap."""
    r = R.analyse(reg("implied", [C("a", "p", "<", 0.05), C("b", "d", ">", 0)],
                      "a | b", "a & b"))
    assert r.prop_reachable["corroborate"], r
    assert not r.prop_reachable["falsify"], r
    assert r.overlap_prop, r
    assert any("DEAD BRANCH" in f and "falsify" in f for f in r.flags), r.flags


@case
def corroborate_contradictory():
    """C = x & !x is never true, whatever the data."""
    r = R.analyse(reg("contra", [C("x", "p", "<", 0.05)], "x & !x", "!x"))
    assert not r.prop_reachable["corroborate"], r
    assert any("DEAD BRANCH" in f and "corroborate" in f for f in r.flags), r.flags


@case
def identical_rules_kill_both():
    """C and F identical: every result is 'inconclusive'. Both dead."""
    r = R.analyse(reg("same", [C("x", "p", "<", 0.05)], "x", "x"))
    assert not r.prop_reachable["corroborate"] and not r.prop_reachable["falsify"], r
    assert r.prop_reachable["inconclusive"] and r.overlap_prop, r
    assert len([f for f in r.flags if "DEAD BRANCH" in f]) == 2, r.flags


# --- level 2: propositionally fine, numerically impossible ---------------

@case
def same_variable_contradiction():
    """`p < .05` and `p > .05` are independent booleans to a propositional
    reader and mutually exclusive to a number."""
    r = R.analyse(reg("numeric", [C("lo", "p", "<", 0.05), C("hi", "p", ">", 0.05)],
                      "lo & hi", "!lo & !hi"))
    assert r.prop_reachable["corroborate"], r
    assert r.witness["corroborate"] is None, r.witness
    assert any("NO WITNESS" in f for f in r.flags), r.flags
    # and the other branch IS numerically fine: p == 0.05 exactly
    assert r.witness["falsify"] is not None, r


@case
def domain_makes_a_branch_impossible():
    """A p value lives in [0, 1]; `p > 2` cannot hold. Declaring the domain is
    what turns a reachable-looking branch into an honest NO WITNESS."""
    crits = [C("big", "p", ">", 2.0)]
    loose = R.analyse(reg("no domain", crits, "big", "!big"))
    assert loose.witness["corroborate"] is not None, loose
    tight = R.analyse(reg("domain", crits, "big", "!big",
                          domains={"p": (0.0, 1.0)}))
    assert tight.witness["corroborate"] is None, tight
    assert any("NO WITNESS" in f for f in tight.flags), tight.flags


@case
def ci_order_relation_bites():
    """A confidence interval's lower bound cannot exceed its upper bound. With
    that relation declared, 'lower > 0.5 and upper <= 0.2' is impossible."""
    crits = [C("lo", "ci_lo", ">", 0.5), C("hi", "ci_hi", ">", 0.2)]
    loose = R.analyse(reg("no relation", crits, "lo & !hi", "!lo"))
    assert loose.witness["corroborate"] is not None, loose
    tight = R.analyse(reg("relation", crits, "lo & !hi", "!lo",
                          relations=[("ci_lo", "<=", "ci_hi")]))
    assert tight.witness["corroborate"] is None, tight


@case
def relation_still_allows_the_possible():
    """The relation must not break branches that ARE possible."""
    crits = [C("lo", "ci_lo", ">", 0.0), C("hi", "ci_hi", ">", 0.2)]
    r = R.analyse(reg("ok with relation", crits, "lo & hi", "!hi",
                      relations=[("ci_lo", "<=", "ci_hi")]))
    w = r.witness["corroborate"]
    assert w is not None, r
    assert w["ci_lo"] > 0 and w["ci_hi"] > 0.2 and w["ci_lo"] <= w["ci_hi"], w


# --- bookkeeping defects -------------------------------------------------

@case
def undefined_criterion_is_an_error():
    r = R.analyse(reg("undef", [C("x", "p", "<", 0.05)], "x", "z"))
    assert r.error and r.referenced_but_undefined == ["z"], r
    assert any("UNDEFINED" in f for f in r.flags), r.flags


@case
def unused_criterion_is_flagged():
    r = R.analyse(reg("unused", [C("x", "p", "<", 0.05), C("y", "d", ">", 0)],
                      "x", "!x"))
    assert r.defined_but_unused == ["y"], r
    assert any("UNUSED" in f for f in r.flags), r.flags


@case
def unparseable_is_an_error_not_a_crash():
    r = R.analyse(reg("bad", [C("x", "p", "<", 0.05)], "x &", "!x"))
    assert r.error and "unparseable" in r.error, r


# --- the semantics must be scienceverse's, including its else-branch -----

@case
def verdict_table_matches_study_eval():
    """R/study_eval.R: corrob & !falsify -> corroborate; !corrob & falsify ->
    falsify; EVERYTHING ELSE -> inconclusive, including both-true."""
    assert R.verdict_of(True, False) == "corroborate"
    assert R.verdict_of(False, True) == "falsify"
    assert R.verdict_of(False, False) == "inconclusive"
    assert R.verdict_of(True, True) == "inconclusive"


@case
def witnesses_are_verified_not_asserted():
    """Every witness handed back must actually produce its verdict when the
    criteria are re-evaluated on it from scratch."""
    cases = [
        reg("a", [C("x", "p", "<", 0.05), C("y", "d", ">", 0)], "x & y", "!x & !y",
            domains={"p": (0.0, 1.0)}),
        reg("b", [C("lo", "ci_lo", ">", 0.0), C("hi", "ci_hi", ">", 0.2)],
            "lo & hi", "!hi", relations=[("ci_lo", "<=", "ci_hi")]),
    ]
    for rg in cases:
        rep = R.analyse(rg)
        crits = rg.by_id()
        for verdict, w in rep.witness.items():
            if w is None:
                continue
            env = {cid: c.holds(w) for cid, c in crits.items()}
            got = R.verdict_of(R.eval_expr(R.parse_expr(rg.corroboration), env),
                               R.eval_expr(R.parse_expr(rg.falsification), env))
            assert got == verdict, (rg.name, verdict, got, w)


# --- result-vs-result criteria (a legal scienceverse comparator) ----------

@case
def pairwise_criterion_reachable():
    """`estimate[1] > estimate[2]` -- the comparator is another result, which
    appears in the package's own vignettes/study.json."""
    crits = [C("p", "A.p.value", "<", 0.05),
             C("dir", "A.estimate[1]", ">", "A.estimate[2]")]
    r = R.analyse(reg("pairwise", crits, "p & dir", "p & !dir",
                      domains={"A.p.value": (0.0, 1.0)}))
    assert all(r.prop_reachable[v] for v in R.VERDICTS), r
    assert not r.overlap_prop, r
    assert r.flags == [], r.flags
    w = r.witness["corroborate"]
    assert w["A.p.value"] < 0.05 and w["A.estimate[1]"] > w["A.estimate[2]"], w
    w = r.witness["falsify"]
    assert w["A.p.value"] < 0.05 and w["A.estimate[1]"] <= w["A.estimate[2]"], w


@case
def pairwise_criterion_can_be_impossible():
    """x > y and y > x cannot both hold."""
    crits = [C("f", "A.x", ">", "A.y"), C("b", "A.y", ">", "A.x")]
    r = R.analyse(reg("cycle", crits, "f & b", "!f & !b"))
    assert r.prop_reachable["corroborate"], r
    assert r.witness["corroborate"] is None, r.witness
    assert any("NO WITNESS" in x for x in r.flags), r.flags
    assert r.witness["falsify"] is not None, r      # x == y


@case
def two_analyses_are_two_variables():
    """Two criteria both named p.value but on DIFFERENT analyses are different
    numbers. Collapsing them into one variable was a real bug in the first
    harvester and it invented a defect in the package's sim.Rmd."""
    crits = [C("a", "first.p.value", "<", 0.05),
             C("b", "second.p.value", ">", 0.05)]
    r = R.analyse(reg("two analyses", crits, "a & b", "!a & !b",
                      domains={"first.p.value": (0.0, 1.0),
                               "second.p.value": (0.0, 1.0)}))
    assert r.witness["corroborate"] is not None, r   # possible: .01 and .9
    same = [C("a", "one.p.value", "<", 0.05), C("b", "one.p.value", ">", 0.05)]
    r2 = R.analyse(reg("one analysis", same, "a & b", "!a & !b",
                       domains={"one.p.value": (0.0, 1.0)}))
    assert r2.witness["corroborate"] is None, r2     # impossible on one number


def main():
    force_red = "--force-red" in sys.argv
    if force_red:
        # break the one line everything else depends on
        R.verdict_of = lambda c, f: "corroborate" if c else "falsify" if f else "inconclusive"
        print("-- semantics broken on purpose (both-true now reads 'corroborate')")
    passed, failed = 0, []
    for fn in CASES:
        try:
            fn()
            passed += 1
        except AssertionError as e:
            failed.append((fn.__name__, str(e)[:200]))
        except Exception as e:  # noqa: BLE001
            failed.append((fn.__name__, f"{type(e).__name__}: {e}"))
    for name, why in failed:
        print(f"  FAIL  {name}: {why}")
    print(f"{passed}/{len(CASES)} passed")
    if force_red:
        print("force-red expected at least one FAIL above:",
              "yes" if failed else "NO -- the suite is not load-bearing")
        return 0 if failed else 1
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
