"""reach.py -- which verdicts can a machine-readable hypothesis test actually return?

A preregistered decision rule is a program, and a program can have a branch no
input reaches. In a decision rule that branch is not a style problem: if the
`falsify` verdict is unreachable, no possible data can falsify the hypothesis,
which is the formal shape of an unfalsifiable prediction.

THE OBJECT THIS READS is the scienceverse format (Lakens & DeBruine, 2021,
AMPPS 4(2), doi:10.1177/2515245920970949), whose semantics are taken from the
package source, `R/study_eval.R` at scienceverse/scienceverse@97d4054:

    criterion      -> one comparison, <result> <op> <comparator>, op in < > = !=
    corroboration  -> a boolean expression over criterion ids, with & | ! ( )
    falsification  -> another such expression
    conclusion     -> "corroborate"  if  C and not F
                      "falsify"      if  F and not C
                      "inconclusive" otherwise          <- note: INCLUDING C and F

That last line is why this script reports overlap separately. A registration
whose two rules can both fire at once is logically contradictory, and the
evaluator renders that contradiction as "inconclusive", which is also the
honest name for the in-between case. The contradiction is therefore invisible
in the output.

TWO LEVELS, and the difference matters:

  LEVEL 1, propositional (exact, and a PROOF).  Treat the criteria as free
  booleans. "falsify" is reachable iff (F and not C) is satisfiable. If it is
  not, no data anywhere can produce that verdict -- the result does not depend
  on effect sizes, sample size, or the data-generating process at all. This is
  the level that matters, and it is the level a power simulation cannot see,
  because a simulation samples DATA and this is a question about the space of
  logically possible RESULT PATTERNS.

  LEVEL 2, numeric.  A propositionally satisfiable branch can still be
  unreachable because criteria on the same variable contradict (`p < .05` and
  `p > .05`), or because of a structural relation between variables (a
  confidence interval's lower bound cannot exceed its upper bound). Level 2
  looks for an actual vector of numbers and then VERIFIES it by plain
  evaluation. A found witness is proof of reachability. A failure to find one
  is reported as "no witness found", never as unreachable.

WHAT IS NOT A DEFECT: an unreachable "inconclusive". A rule whose two
evaluations are exact complements (C = "x", F = "!x") partitions every possible
result into corroborate/falsify, and leaving no room for "inconclusive" is a
deliberate and good thing to do. Only an unreachable `corroborate` or an
unreachable `falsify` is flagged.

Iris, fire 373, Oct 26 2026.
"""
from __future__ import annotations

import itertools
import math
import re
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# expression parsing:  & | ! ( ) over identifiers
# --------------------------------------------------------------------------

_TOK = re.compile(r"\s*(&&|\|\||[&|!()]|[A-Za-z_][A-Za-z_0-9]*)")


def tokenize(src: str) -> list[str]:
    out, i = [], 0
    while i < len(src):
        m = _TOK.match(src, i)
        if not m:
            if src[i].isspace():
                i += 1
                continue
            raise ValueError(f"cannot tokenize at {i}: {src[i:i+20]!r}")
        tok = m.group(1)
        out.append("&" if tok == "&&" else "|" if tok == "||" else tok)
        i = m.end()
    return out


class Parser:
    """or -> and ('|' and)* ; and -> unary ('&' unary)* ; unary -> '!' unary | atom"""

    def __init__(self, toks: list[str]):
        self.t, self.i = toks, 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def take(self, what=None):
        tok = self.peek()
        if what is not None and tok != what:
            raise ValueError(f"expected {what!r}, got {tok!r}")
        self.i += 1
        return tok

    def parse(self):
        node = self.p_or()
        if self.peek() is not None:
            raise ValueError(f"trailing tokens from {self.peek()!r}")
        return node

    def p_or(self):
        node = self.p_and()
        while self.peek() == "|":
            self.take()
            node = ("or", node, self.p_and())
        return node

    def p_and(self):
        node = self.p_unary()
        while self.peek() == "&":
            self.take()
            node = ("and", node, self.p_unary())
        return node

    def p_unary(self):
        if self.peek() == "!":
            self.take()
            return ("not", self.p_unary())
        if self.peek() == "(":
            self.take()
            node = self.p_or()
            self.take(")")
            return node
        tok = self.peek()
        if tok is None or not tok[0].isalpha() and tok[0] != "_":
            raise ValueError(f"expected an identifier, got {tok!r}")
        self.take()
        return ("var", tok)


def parse_expr(src: str):
    return Parser(tokenize(src)).parse()


def expr_vars(node) -> set[str]:
    k = node[0]
    if k == "var":
        return {node[1]}
    if k == "not":
        return expr_vars(node[1])
    return expr_vars(node[1]) | expr_vars(node[2])


def eval_expr(node, env: dict[str, bool]) -> bool:
    k = node[0]
    if k == "var":
        return env[node[1]]
    if k == "not":
        return not eval_expr(node[1], env)
    if k == "and":
        return eval_expr(node[1], env) and eval_expr(node[2], env)
    if k == "or":
        return eval_expr(node[1], env) or eval_expr(node[2], env)
    raise AssertionError(k)


# --------------------------------------------------------------------------
# the registration object
# --------------------------------------------------------------------------

@dataclass
class Criterion:
    """One comparison. `value` is a number, OR the name of another variable --
    scienceverse resolves a non-numeric comparator out of the results list
    (`get_res_value(criterion$comparator, results)` in R/study_eval.R), so
    `estimate[1] > estimate[2]` is a legal criterion and appears in the
    package's own vignettes/study.json. The first draft of this file required a
    number and silently DROPPED those criteria, after which the checker
    reported the evaluation as referencing an undefined criterion -- a false
    positive of mine, found by hand-checking all six flags of the first
    harvest. Four of the six were mine."""

    id: str
    var: str                 # "<analysis_id>.<result>"
    op: str                  # one of  <  >  =  !=
    value: float | str       # a constant, or another var name

    @property
    def is_pairwise(self) -> bool:
        return isinstance(self.value, str)

    def holds(self, env: dict) -> bool:
        x = env[self.var]
        y = env[self.value] if self.is_pairwise else self.value
        if self.op == "<":
            return x < y
        if self.op == ">":
            return x > y
        if self.op == "=":
            return x == y
        if self.op == "!=":
            return x != y
        raise ValueError(f"unknown operator {self.op!r}")


@dataclass
class Registration:
    name: str
    criteria: list[Criterion]
    corroboration: str
    falsification: str
    # optional sharpening. domains: var -> (lo, hi) inclusive, e.g. a p value in [0, 1].
    domains: dict[str, tuple[float, float]] = field(default_factory=dict)
    # structural relations between two variables that hold by construction,
    # e.g. ("trust.conf.int[1]", "<=", "trust.conf.int[2]") -- a confidence
    # interval's lower bound cannot exceed its upper bound.
    relations: list[tuple[str, str, str]] = field(default_factory=list)
    source: str = ""

    def by_id(self) -> dict[str, Criterion]:
        return {c.id: c for c in self.criteria}


VERDICTS = ("corroborate", "falsify", "inconclusive")


def verdict_of(corrob: bool, falsify: bool) -> str:
    """Exactly R/study_eval.R's three-way, including its else-branch."""
    if corrob and not falsify:
        return "corroborate"
    if falsify and not corrob:
        return "falsify"
    return "inconclusive"


# --------------------------------------------------------------------------
# LEVEL 2: is a given truth assignment over the criteria numerically possible?
# --------------------------------------------------------------------------

_INF = math.inf


def _var_witness(cons, domain):
    """cons: list of (op, value, truth) on ONE variable. -> (ok, witness)."""
    lo, lo_strict = -_INF, False
    hi, hi_strict = _INF, False
    eqs, neqs = set(), set()
    for op, v, truth in cons:
        # Tighten only. A NON-strict bound at the same value as an existing
        # strict one is WEAKER, so it must not be applied -- the first draft
        # applied it and turned `p < .05` into `p <= .05`, which made
        # (`p < .05` true, `p > .05` false) report the witness p = 0.05.
        # Caught by a hand-computed known answer before the script said
        # anything about anybody's registration.
        if op == "<":
            if truth:                                   # x < v
                if v < hi or (v == hi and not hi_strict):
                    hi, hi_strict = v, True
            else:                                       # x >= v
                if v > lo:
                    lo, lo_strict = v, False
        elif op == ">":
            if truth:                                   # x > v
                if v > lo or (v == lo and not lo_strict):
                    lo, lo_strict = v, True
            else:                                       # x <= v
                if v < hi:
                    hi, hi_strict = v, False
        elif op == "=":
            (eqs if truth else neqs).add(v)
        elif op == "!=":
            (neqs if truth else eqs).add(v)
        else:
            raise ValueError(op)
    if domain is not None:
        dlo, dhi = domain
        if dlo > lo or (dlo == lo and lo_strict):
            lo, lo_strict = dlo, False
        if dhi < hi or (dhi == hi and hi_strict):
            hi, hi_strict = dhi, False

    def inside(x):
        if lo != -_INF and (x < lo or (x == lo and lo_strict)):
            return False
        if hi != _INF and (x > hi or (x == hi and hi_strict)):
            return False
        return x not in neqs

    if eqs:
        if len(eqs) > 1:
            return False, None
        e = next(iter(eqs))
        return (inside(e), e if inside(e) else None)

    # candidates, cheapest first; the neqs are a finite set so an open interval
    # always has a usable point, we just have to walk off the forbidden ones.
    cands = []
    if lo == -_INF and hi == _INF:
        cands = [0.0, 1.0, -1.0]
    elif lo == -_INF:
        cands = [hi - 1.0, hi - 0.5, hi] if hi_strict else [hi, hi - 1.0]
    elif hi == _INF:
        cands = [lo + 1.0, lo + 0.5, lo] if lo_strict else [lo, lo + 1.0]
    else:
        mid = (lo + hi) / 2.0
        cands = [mid, (lo + mid) / 2.0, (mid + hi) / 2.0]
        if not lo_strict:
            cands.append(lo)
        if not hi_strict:
            cands.append(hi)
    for c in cands:
        if inside(c):
            return True, c
    # last resort: jitter inside the interval
    if lo != -_INF and hi != _INF and hi > lo:
        for k in range(3, 40):
            c = lo + (hi - lo) * k / 41.0
            if inside(c):
                return True, c
    return False, None


def _critical_pool(reg: Registration, interior: int = 1) -> list[float]:
    """For predicates built only from comparisons against a finite set of
    breakpoints, a witness exists iff one exists among the breakpoints, points
    just either side of them, and one point beyond each extreme. That finite
    pool is what the search below is over, which is why a search failure here
    is close to a proof -- but it is still reported as "no witness found", not
    as unreachable, because the pool argument is mine and the proof of
    unreachability I am willing to publish is the propositional one.

    `interior` is the number of points placed strictly inside each gap between
    adjacent breakpoints. ONE IS NOT ENOUGH when two variables are tied by a
    STRICT relation and both must land inside the same gap: with a single
    midpoint the only candidate is shared, so `lo < hi` cannot be satisfied and
    a feasible pattern is reported NO WITNESS. Found fire 374 on
    `equiv_demo.py`: `0 < conf.int[1] < conf.int[2] < 0.2` is ordinary and the
    old pool could not express it. `interior=1` reproduces the old pool
    exactly, so every number published before this change is unaffected --
    and enlarging the pool can only turn a NO WITNESS into a witness, never
    the reverse, so no propositional verdict can move either."""
    vals = sorted({float(c.value) for c in reg.criteria if not c.is_pairwise})
    for lo, hi in reg.domains.values():
        vals += [lo, hi]
    vals = sorted(set(vals))
    if not vals:
        return [-1.0, 0.0, 1.0]
    d = 0.5
    pool = [vals[0] - 1.0, vals[-1] + 1.0]
    for i, v in enumerate(vals):
        pool += [v - d, v, v + d]
        if i + 1 < len(vals):
            nxt = vals[i + 1]
            if interior == 1:
                # the original expression, kept EXACTLY so the pool is
                # bit-identical to every pool used before fire 374 --
                # v + (nxt - v) * 1/2 is the same number in arithmetic and a
                # different one in floating point, and a pool value sitting a
                # last-bit away from a breakpoint is exactly where a strict
                # comparison could flip.
                pool.append((v + nxt) / 2.0)
            else:
                for j in range(1, interior + 1):
                    pool.append(v + (nxt - v) * j / (interior + 1))
    return sorted(set(pool))


def numeric_witness(reg: Registration, assignment: dict[str, bool]):
    """A vector of numbers realising `assignment`, VERIFIED, or None.

    Variables with only scalar criteria are solved independently and exactly.
    Variables tied together -- by a result-vs-result criterion, or by a
    declared structural relation like a confidence interval's ordering -- are
    solved jointly by searching the critical-value pool within their connected
    component only, which keeps the product small. Whatever comes out is then
    checked by plain evaluation before it is returned."""
    scalar: dict[str, list] = {}
    all_vars: set[str] = set()
    for c in reg.criteria:
        all_vars.add(c.var)
        if c.is_pairwise:
            all_vars.add(c.value)
        elif c.id in assignment:
            scalar.setdefault(c.var, []).append((c.op, float(c.value), assignment[c.id]))
    for a, _, b in reg.relations:
        all_vars.update((a, b))
    for v in all_vars:
        scalar.setdefault(v, [])

    # pairwise constraints live in this assignment: (a, op, b, truth)
    pairs = [(c.var, c.op, c.value, assignment[c.id])
             for c in reg.criteria if c.is_pairwise and c.id in assignment]
    pairs += [(a, op, b, True) for a, op, b in reg.relations]

    # connected components over the pairwise graph
    parent = {v: v for v in all_vars}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, _op, b, _t in pairs:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    comps: dict[str, list[str]] = {}
    for v in all_vars:
        comps.setdefault(find(v), []).append(v)

    def rel_ok(x, op, y, truth):
        if op == "<":
            got = x < y
        elif op == ">":
            got = x > y
        elif op == "=":
            got = x == y
        elif op == "!=":
            got = x != y
        elif op == "<=":
            got = x <= y
        elif op == ">=":
            got = x >= y
        else:
            raise ValueError(op)
        return got == truth

    # how many points strictly inside each gap: enough for the longest strict
    # chain that could be forced into one gap, which is the largest component.
    _maxcomp = max((len(m) for m in comps.values()), default=1)
    pool = _critical_pool(reg, interior=_maxcomp if _maxcomp <= 4 else 1)
    pick: dict[str, float] = {}
    for _root, members in comps.items():
        local = [p for p in pairs if p[0] in members or p[2] in members]
        if not local:
            v = members[0]
            ok, w = _var_witness(scalar[v], reg.domains.get(v))
            if not ok:
                return None
            pick[v] = w
            continue
        # feasible pool per member, from its own scalar criteria
        feas = []
        for v in members:
            ok, _w = _var_witness(scalar[v], reg.domains.get(v))
            if not ok:
                return None
            cand = [x for x in pool
                    if all(_sat_one(op, val, truth, x) for op, val, truth in scalar[v])
                    and (reg.domains.get(v) is None
                         or reg.domains[v][0] <= x <= reg.domains[v][1])]
            if not cand:
                return None
            feas.append(cand)
        if len(members) > 4:
            return None            # refuse to pretend; reported as "no witness"
        combos = 1
        for f in feas:
            combos *= len(f)
        if combos > 2_000_000:
            return None            # same refusal, on cost rather than size
        found = None
        for combo in itertools.product(*feas):
            env = dict(zip(members, combo))
            if all(rel_ok(env[a] if a in env else pick.get(a),
                          op,
                          env[b] if b in env else pick.get(b), t)
                   for a, op, b, t in local
                   if (a in env or a in pick) and (b in env or b in pick)):
                found = env
                break
        if found is None:
            return None
        pick.update(found)

    # VERIFY. Never return a witness that has not been checked by plain
    # evaluation against every criterion, domain and relation.
    for c in reg.criteria:
        if c.id in assignment and c.holds(pick) != assignment[c.id]:
            return None
    for v, (dlo, dhi) in reg.domains.items():
        if v in pick and not (dlo <= pick[v] <= dhi):
            return None
    for a, op, b in reg.relations:
        if a in pick and b in pick and not rel_ok(pick[a], op, pick[b], True):
            return None
    return pick


def _sat_one(op, val, truth, x):
    if op == "<":
        got = x < val
    elif op == ">":
        got = x > val
    elif op == "=":
        got = x == val
    elif op == "!=":
        got = x != val
    else:
        raise ValueError(op)
    return got == truth


# --------------------------------------------------------------------------
# the analysis
# --------------------------------------------------------------------------

@dataclass
class Report:
    name: str
    source: str
    n_criteria: int
    referenced_but_undefined: list[str]
    defined_but_unused: list[str]
    # level 1, propositional: can this verdict EVER be returned, treating the
    # criteria as free booleans? False here is a proof of unreachability.
    prop_reachable: dict[str, bool] = field(default_factory=dict)
    # level 2: a verified vector of numbers producing that verdict.
    witness: dict[str, dict | None] = field(default_factory=dict)
    # both rules firing at once. Logically contradictory; R/study_eval.R renders
    # it as "inconclusive" with no warning.
    overlap_prop: bool = False
    overlap_witness: dict | None = None
    n_assignments: int = 0
    error: str = ""

    @property
    def flags(self) -> list[str]:
        out = []
        if self.referenced_but_undefined:
            out.append("UNDEFINED CRITERIA: " + ", ".join(self.referenced_but_undefined))
        if self.error:
            out.append("ERROR: " + self.error)
            return out
        for v in ("corroborate", "falsify"):
            if not self.prop_reachable.get(v, False):
                out.append(f"DEAD BRANCH: '{v}' is unreachable for any possible results")
            elif self.witness.get(v) is None:
                out.append(f"NO WITNESS for '{v}' (propositionally reachable; no numbers found)")
        if self.overlap_prop:
            # Two very different things wear the same shape, and which one it is
            # depends on whether a branch died. Found by hand-checking the three
            # flags the harvest left after its own bugs were fixed: the package's
            # sim.Rmd overlaps on PURPOSE -- "significantly greater than 0" and
            # "significantly smaller than the smallest effect of interest" can
            # both be true, and in equivalence testing that is the single most
            # informative result. It is not a contradiction. It is a fourth
            # state with no name in a three-verdict scheme.
            if any(not self.prop_reachable.get(v, False) for v in ("corroborate", "falsify")):
                out.append("NESTED RULES: corroboration and falsification can both hold, "
                           "and one of them can therefore never be the verdict")
            else:
                out.append("FOURTH STATE: corroboration and falsification can both hold at "
                           "once, with all three verdicts also reachable; study_eval.R files "
                           "that under 'inconclusive', which is also the name for the "
                           "no-information case")
        if self.defined_but_unused:
            out.append("UNUSED CRITERIA: " + ", ".join(self.defined_but_unused))
        return out

    def __str__(self):
        head = f"{self.name}" + (f"   [{self.source}]" if self.source else "")
        lines = [head, f"  {self.n_criteria} criteria, {self.n_assignments} truth assignments"]
        for v in VERDICTS:
            mark = "reachable    " if self.prop_reachable.get(v) else "UNREACHABLE  "
            w = self.witness.get(v)
            wt = ""
            if w:
                wt = "  witness " + ", ".join(
                    f"{k}={v2:g}" for k, v2 in sorted(w.items()))
            elif self.prop_reachable.get(v):
                wt = "  (no numeric witness found)"
            lines.append(f"  {v:<13} {mark}{wt}")
        if not self.flags:
            lines.append("  . clean")
        for f_ in self.flags:
            lines.append("  !! " + f_)
        return "\n".join(lines)


def analyse(reg: Registration, max_criteria: int = 22) -> Report:
    crits = reg.by_id()
    rep = Report(reg.name, reg.source, len(reg.criteria), [], [])
    try:
        c_ast = parse_expr(reg.corroboration)
        f_ast = parse_expr(reg.falsification)
    except ValueError as e:
        rep.error = f"unparseable evaluation: {e}"
        return rep

    used = expr_vars(c_ast) | expr_vars(f_ast)
    rep.referenced_but_undefined = sorted(used - set(crits))
    rep.defined_but_unused = sorted(set(crits) - used)
    if rep.referenced_but_undefined:
        rep.error = "references criteria that are not defined"
        return rep
    if len(reg.criteria) > max_criteria:
        rep.error = f"{len(reg.criteria)} criteria is past the enumeration limit"
        return rep

    ids = [c.id for c in reg.criteria]
    rep.prop_reachable = {v: False for v in VERDICTS}
    rep.witness = {v: None for v in VERDICTS}
    rep.n_assignments = 2 ** len(ids)

    for bits in itertools.product((False, True), repeat=len(ids)):
        env = dict(zip(ids, bits))
        corrob = eval_expr(c_ast, env)
        falsify = eval_expr(f_ast, env)
        v = verdict_of(corrob, falsify)
        both = corrob and falsify
        if both:
            rep.overlap_prop = True
        # a propositional witness exists; now look for numbers, but only while
        # we still need one for this verdict (the search is the expensive half).
        need = rep.witness[v] is None
        rep.prop_reachable[v] = True
        if need or (both and rep.overlap_witness is None):
            w = numeric_witness(reg, env)
            if w is not None:
                if need:
                    rep.witness[v] = w
                if both and rep.overlap_witness is None:
                    rep.overlap_witness = w
    return rep


# --------------------------------------------------------------------------
# the general case: ANY verdict function, not just corroborate/falsify
# --------------------------------------------------------------------------

def reachable_verdicts(criteria: list[Criterion], verdict_fn,
                       domains=None, relations=None, declared=None):
    """Which verdicts can a decision rule of ANY arity actually return?

    `verdict_fn` takes {criterion_id: bool} and returns a hashable verdict.
    Returns (reachable, witness, unreachable_declared) where `reachable` maps
    each verdict to the number of truth assignments producing it, `witness`
    maps it to a verified vector of numbers, and `unreachable_declared` lists
    any verdict in `declared` that nothing can produce.

    This exists because the rule that cost me three days of a free-tier quota
    in fire 369 was not a corroborate/falsify pair -- it was a six-way ladder
    that named a resolution depth, and the defect was the same defect: five of
    its six outcomes could not occur. Forcing such a rule into someone else's
    two-rule schema to check it would be its own kind of lie.
    """
    reg = Registration("general", criteria, "x", "x",
                       domains=domains or {}, relations=relations or [])
    ids = [c.id for c in criteria]
    counts: dict = {}
    wit: dict = {}
    for bits in itertools.product((False, True), repeat=len(ids)):
        env = dict(zip(ids, bits))
        v = verdict_fn(env)
        counts[v] = counts.get(v, 0) + 1
        if v not in wit:
            w = numeric_witness(reg, env)
            if w is not None:
                wit[v] = w
    missing = [d for d in (declared or []) if d not in counts]
    return counts, wit, missing
