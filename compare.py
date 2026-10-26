#!/usr/bin/env python3
"""compare.py -- do two encodings of the SAME stated prediction return the same verdict?

Fire 374. `reach.py` asks whether a single rule's verdicts can ever occur.
This asks a different question that came out of the same census: when a paper
states a prediction in prose and the code states it in criteria, do the two
agree on every result pattern that can actually happen?

A disagreement is reported ONLY with a verified numeric witness -- a vector of
result values that realises the truth assignment -- so every row of the output
is a concrete pattern of results on which the two encodings return different
verdicts. A propositionally-different cell with no witness is reported as
NO WITNESS and is NOT counted as a disagreement, the same rule reach.py uses:
when an instrument cannot reach a verdict it says so rather than guessing the
likelier one.

Not a claim about anybody's conduct. Two encodings of one sentence is the
normal state of a methods paper; the question is only whether they differ, and
where.
"""
from __future__ import annotations

import itertools
import sys
from dataclasses import dataclass

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from reach import (Criterion, Registration, eval_expr, numeric_witness,
                   parse_expr, verdict_of)


@dataclass
class Cell:
    assignment: dict[str, bool]
    verdict_a: str
    verdict_b: str
    witness: dict[str, float] | None   # None => NO WITNESS, not counted


@dataclass
class Diff:
    name_a: str
    name_b: str
    n_criteria: int
    n_assignments: int
    disagreements: list[Cell]          # feasible, witnessed
    no_witness: list[Cell]             # propositionally differ, no numbers found
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    def pairs(self) -> dict[tuple[str, str], int]:
        out: dict[tuple[str, str], int] = {}
        for c in self.disagreements:
            k = (c.verdict_a, c.verdict_b)
            out[k] = out.get(k, 0) + 1
        return out


def _merge(reg_a: Registration, reg_b: Registration):
    """Union the two criterion sets. Same id must mean the same comparison."""
    by_id: dict[str, Criterion] = {}
    for reg in (reg_a, reg_b):
        for c in reg.criteria:
            prev = by_id.get(c.id)
            if prev is None:
                by_id[c.id] = c
            elif (prev.var, prev.op, prev.value) != (c.var, c.op, c.value):
                raise ValueError(
                    f"criterion id {c.id!r} names different comparisons in the two "
                    f"encodings ({prev.var} {prev.op} {prev.value} vs "
                    f"{c.var} {c.op} {c.value}) -- they cannot be compared")
    domains = dict(reg_a.domains)
    domains.update(reg_b.domains)
    relations = list(dict.fromkeys(list(reg_a.relations) + list(reg_b.relations)))
    merged = Registration(
        name=f"{reg_a.name} vs {reg_b.name}",
        criteria=list(by_id.values()),
        corroboration="TRUE", falsification="TRUE",
        domains=domains, relations=relations,
    )
    return merged, by_id


def compare(reg_a: Registration, reg_b: Registration, max_criteria: int = 22) -> Diff:
    try:
        merged, by_id = _merge(reg_a, reg_b)
    except ValueError as e:
        return Diff(reg_a.name, reg_b.name, 0, 0, [], [], error=str(e))

    asts = {}
    for tag, reg in (("a", reg_a), ("b", reg_b)):
        try:
            asts[tag] = (parse_expr(reg.corroboration), parse_expr(reg.falsification))
        except ValueError as e:
            return Diff(reg_a.name, reg_b.name, len(by_id), 0, [], [],
                        error=f"unparseable evaluation in {tag}: {e}")

    ids = sorted(by_id)
    if len(ids) > max_criteria:
        return Diff(reg_a.name, reg_b.name, len(ids), 0, [], [],
                    error=f"{len(ids)} criteria is past the enumeration limit")

    diff = Diff(reg_a.name, reg_b.name, len(ids), 2 ** len(ids), [], [])
    for bits in itertools.product((False, True), repeat=len(ids)):
        env = dict(zip(ids, bits))
        va = verdict_of(eval_expr(asts["a"][0], env), eval_expr(asts["a"][1], env))
        vb = verdict_of(eval_expr(asts["b"][0], env), eval_expr(asts["b"][1], env))
        if va == vb:
            continue
        w = numeric_witness(merged, env)
        cell = Cell(dict(env), va, vb, w)
        (diff.disagreements if w is not None else diff.no_witness).append(cell)
    return diff


def render(diff: Diff, show: int = 8) -> str:
    L = [f"{diff.name_a}   VS   {diff.name_b}"]
    if not diff.ok:
        L.append(f"  ERROR: {diff.error}")
        return "\n".join(L)
    L.append(f"  {diff.n_criteria} criteria, {diff.n_assignments} truth assignments")
    if not diff.disagreements and not diff.no_witness:
        L.append("  AGREE on every result pattern.")
        return "\n".join(L)
    if diff.disagreements:
        L.append(f"  DISAGREE on {len(diff.disagreements)} feasible pattern(s):")
        for (a, b), n in sorted(diff.pairs().items()):
            L.append(f"    {a:<12} where the other says {b:<12}  x{n}")
        for cell in diff.disagreements[:show]:
            true = [k for k, v in sorted(cell.assignment.items()) if v] or ["(none)"]
            L.append(f"    - true: {', '.join(true)}")
            L.append(f"      A={cell.verdict_a}  B={cell.verdict_b}")
            L.append("      witness: " + ", ".join(
                f"{k}={v:g}" for k, v in sorted(cell.witness.items())))
        if len(diff.disagreements) > show:
            L.append(f"    ... {len(diff.disagreements) - show} more")
    if diff.no_witness:
        L.append(f"  NO WITNESS on {len(diff.no_witness)} pattern(s) -- these differ "
                 "propositionally but no numbers were found, so they are NOT counted.")
    return "\n".join(L)


# --------------------------------------------------------------------------
# known answers, hand-computed, BEFORE this says anything about real work
# --------------------------------------------------------------------------

def _p(var):
    return {var: (0.0, 1.0)}


def _selftest(force_red: bool = False) -> int:
    global verdict_of
    checks: list[tuple[str, bool]] = []

    def chk(name, cond):
        checks.append((name, bool(cond)))

    c1 = Criterion("c1", "t1.p.value", "<", 0.05)
    c2 = Criterion("c2", "t2.p.value", "<", 0.05)
    dom = {**_p("t1.p.value"), **_p("t2.p.value")}

    # 1. identical encodings agree everywhere.
    a = Registration("same-A", [c1, c2], "c1", "c2", domains=dom)
    b = Registration("same-B", [c1, c2], "c1", "c2", domains=dom)
    d = compare(a, b)
    chk("identical encodings: 0 disagreements", d.ok and not d.disagreements)
    chk("identical encodings: 4 assignments", d.n_assignments == 4)

    # 2. THE REAL SHAPE. Prose: corroborate = effect>0 AND not below SESOI.
    #    Code:  corroborate = effect>0 only.  They differ on exactly ONE
    #    assignment -- c1 and c2 both true -- where prose says falsify
    #    (C false because of the dropped conjunct, F true) and code says
    #    inconclusive (C and F both true).  Hand-computed: 1 of 4.
    prose = Registration("prose", [c1, c2], "c1 & !c2", "c2", domains=dom)
    code = Registration("code", [c1, c2], "c1", "c2", domains=dom)
    d = compare(prose, code)
    chk("dropped conjunct: exactly 1 disagreement", len(d.disagreements) == 1)
    cell = d.disagreements[0] if d.disagreements else None
    chk("dropped conjunct: on c1=T,c2=T",
        cell is not None and cell.assignment == {"c1": True, "c2": True})
    chk("dropped conjunct: prose=falsify, code=inconclusive",
        cell is not None and cell.verdict_a == "falsify"
        and cell.verdict_b == "inconclusive")
    chk("dropped conjunct: witness satisfies both criteria",
        cell is not None and cell.witness is not None
        and cell.witness["t1.p.value"] < 0.05 and cell.witness["t2.p.value"] < 0.05)
    chk("dropped conjunct: pair tally",
        d.pairs() == {("falsify", "inconclusive"): 1})

    # 3. the direction matters: swap the arguments and the pair flips.
    d2 = compare(code, prose)
    chk("argument order flips the pair",
        d2.pairs() == {("inconclusive", "falsify"): 1})

    # 4. a difference that lives only in an INFEASIBLE region is not a
    #    disagreement. c3 and c4 are p<.05 and p>.05 on the SAME variable, so
    #    both-true is numerically impossible; the encodings differ only there.
    c3 = Criterion("c3", "t1.p.value", "<", 0.05)
    c4 = Criterion("c4", "t1.p.value", ">", 0.05)
    one = Registration("one", [c3, c4], "c3 & c4", "c3 & !c3", domains=_p("t1.p.value"))
    two = Registration("two", [c3, c4], "c3 & !c3", "c3 & !c3", domains=_p("t1.p.value"))
    d = compare(one, two)
    chk("infeasible-only difference: 0 counted", len(d.disagreements) == 0)
    chk("infeasible-only difference: reported as NO WITNESS",
        len(d.no_witness) >= 1)

    # 5. same id, different comparison -> refuse rather than compare.
    bad = Registration("bad", [Criterion("c1", "t1.p.value", ">", 0.05)],
                       "c1", "c1 & !c1", domains=_p("t1.p.value"))
    d = compare(Registration("good", [c1], "c1", "c1 & !c1",
                             domains=_p("t1.p.value")), bad)
    chk("same id different comparison: refuses", not d.ok)

    # 6. an unparseable encoding is an error, not an agreement.
    d = compare(Registration("x", [c1], "c1 &", "c1 & !c1"),
                Registration("y", [c1], "c1", "c1 & !c1"))
    chk("unparseable: error not agreement", not d.ok)

    # 7. disjoint criteria sets still compare (union of ids).
    only_a = Registration("A", [c1], "c1", "c1 & !c1", domains=dom)
    only_b = Registration("B", [c2], "c2", "c2 & !c2", domains=dom)
    d = compare(only_a, only_b)
    chk("union of ids: 2 criteria, 4 assignments",
        d.ok and d.n_criteria == 2 and d.n_assignments == 4)
    chk("union of ids: disagrees where exactly one holds",
        len(d.disagreements) == 2)

    # 8. the render never prints a disagreement without a witness line.
    txt = render(compare(prose, code))
    chk("render shows witness for each printed disagreement",
        txt.count("witness:") == len(compare(prose, code).disagreements))

    if force_red:
        # break the comparison on purpose: make it only ever report agreement.
        # NB: patch THIS module's global. The first version did
        # `import compare as _self; _self.verdict_of = ...`, which under
        # `python3 compare.py` imports a SECOND module object (this one is
        # __main__), so the patch landed on a copy nothing called and the
        # force-red check passed happily. A check that cannot fail is not a
        # check -- the third time that exact defect has been mine.
        globals()["verdict_of"] = lambda c, f: "same"
        d = compare(prose, code)
        chk("FORCE-RED: a broken verdict_of must NOT still find the disagreement",
            len(d.disagreements) == 1)

    bad_n = sum(1 for _, ok in checks if not ok)
    for name, ok in checks:
        if not ok:
            print(f"  FAIL  {name}")
    print(f"{len(checks) - bad_n}/{len(checks)} passed")
    return 1 if bad_n else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest("--force-red" in sys.argv))
    print(__doc__)
