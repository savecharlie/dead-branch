"""harvest.py -- pull every machine-readable hypothesis test out of a
scienceverse tree (JSON study files, and the R/Rmd pipe chains in its own
tests, vignettes and README) and run reach.py over all of them.

Two source dialects:

  JSON   hypotheses[].criteria[] with id/analysis_id/result/operator/comparator,
         and hypotheses[].corroboration.evaluation / .falsification.evaluation.

  R      a `study() %>% add_criterion(...) %>% add_eval(...)` chain. A chain
         starts at each `study()`, so the criteria and evals between one
         `study()` and the next belong to the same registration. add_eval's
         type is matched on its first letter lowercased, which is what
         R/add_eval.R does.

Anything that cannot be parsed is COUNTED AND NAMED, never skipped silently --
a census with an unknown denominator is not a census.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reach as R  # noqa: E402

# a p value and a Shapiro-Wilk p value both live in [0, 1]; declaring it only
# ever SHRINKS the reachable set, so it can only make a verdict sharper.
P_LIKE = re.compile(r"(^|\.)(p|p\.value|pvalue|p_value)$|^(ts|to|rs|ro)$")


def _domains(criteria) -> dict[str, tuple[float, float]]:
    out = {}
    for c in criteria:
        tail = c.var.split(".", 1)[-1]
        if P_LIKE.search(tail) or P_LIKE.search(c.var):
            out[c.var] = (0.0, 1.0)
    return out


def _relations(criteria) -> list[tuple[str, str, str]]:
    """conf.int[1] <= conf.int[2] for every analysis that uses both."""
    rel = []
    seen = {c.var for c in criteria}
    for v in sorted(seen):
        if v.endswith("conf.int[1]"):
            hi = v[: -len("conf.int[1]")] + "conf.int[2]"
            if hi in seen:
                rel.append((v, "<=", hi))
    return rel


def from_json(path: Path):
    try:
        doc = json.loads(path.read_text())
    except Exception as e:  # noqa: BLE001
        return [], [f"{path}: unreadable JSON ({e})"]
    if not isinstance(doc, dict):
        return [], [f"{path}: top level is a {type(doc).__name__}, not a study object"]
    out, skipped = [], []
    hyps = doc.get("hypotheses") or []
    if not isinstance(hyps, list):
        return [], [f"{path}: hypotheses is not a list"]
    for i, h in enumerate(hyps):
        if not isinstance(h, dict):
            skipped.append(f"{path}#{i}: hypothesis is not an object")
            continue
        corrob = (h.get("corroboration") or {}).get("evaluation")
        falsif = (h.get("falsification") or {}).get("evaluation")
        crits = []
        bad = False
        for c in h.get("criteria") or []:
            cid, res, op = c.get("id"), c.get("result"), c.get("operator")
            comp = c.get("comparator")
            if not cid or res is None or op is None or comp is None:
                bad = True
                continue
            aid = c.get("analysis_id") or "?"
            var = f"{aid}.{res}"
            # a non-numeric comparator is the NAME of another result in the
            # same analysis -- study_eval.R resolves it with get_res_value
            val = float(comp) if isinstance(comp, (int, float)) else f"{aid}.{comp}"
            crits.append(R.Criterion(str(cid), var, str(op), val))
        if not corrob or not falsif or not crits:
            skipped.append(f"{path}#{h.get('id') or i}: "
                           f"{'no criteria' if not crits else ''}"
                           f"{' no corroboration' if not corrob else ''}"
                           f"{' no falsification' if not falsif else ''}".strip())
            continue
        if bad:
            skipped.append(f"{path}#{h.get('id') or i}: a criterion was malformed")
        out.append(R.Registration(
            f"{doc.get('name') or path.stem} / {h.get('id') or i}",
            crits, str(corrob), str(falsif),
            domains=_domains(crits), relations=_relations(crits),
            source=str(path)))
    return out, skipped


_CALL = re.compile(
    r"\b(study|add_hypothesis|add_analysis|add_criterion|add_eval)\s*\(", re.S)


def _args(text: str, start: int):
    """Split one call's arguments at depth 0. start is just past the '('."""
    depth, i, cur, args = 0, start, [], []
    instr = None
    while i < len(text):
        ch = text[i]
        if instr:
            cur.append(ch)
            if ch == "\\":
                if i + 1 < len(text):
                    cur.append(text[i + 1])
                    i += 2
                    continue
            elif ch == instr:
                instr = None
        elif ch in "\"'":
            instr = ch
            cur.append(ch)
        elif ch in "([{":
            depth += 1
            cur.append(ch)
        elif ch in ")]}":
            if depth == 0:
                args.append("".join(cur).strip())
                return [a for a in args if a != ""], i
            depth -= 1
            cur.append(ch)
        elif ch == "," and depth == 0:
            args.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    return None, i


def _unquote(a: str):
    a = (a or "").strip()
    if len(a) >= 2 and a[0] == a[-1] and a[0] in "\"'":
        return a[1:-1]
    return None


def _split_args(args):
    pos, named = [], {}
    for a in args:
        m = re.match(r"^([A-Za-z_][A-Za-z_0-9.]*)\s*=(?!=)\s*(.*)$", a, re.S)
        if m:
            named[m.group(1)] = m.group(2).strip()
        else:
            pos.append(a)
    return pos, named


def _take(pos, named, order):
    out, it = {}, iter(pos)
    for key in order:
        out[key] = named[key] if key in named else next(it, None)
    return out


def from_r(path: Path):
    """A tiny interpreter for the four calls that define a registration, with
    the package's OWN scoping rules:

      add_hypothesis(id)  starts a hypothesis; criteria and evaluations attach
                          to the LAST one added unless hypothesis_id is given.
      add_analysis(id)    starts an analysis; add_criterion attaches to the
                          LAST one added unless analysis_id is given -- so two
                          criteria both reading "p.value" off two different
                          analyses are two different numbers.
      a chain             must be connected by %>% back to a study(). A test
                          file that calls add_eval(s, ...) twenty times in
                          independent expectations is not a registration, and
                          the first draft of this function merged all twenty
                          into one and reported a dead branch in it.

    All three of those were false positives in the first harvest. Every flag
    it produced was checked by hand against the source; four of six were mine.
    """
    text = path.read_text(errors="replace")
    hyps: dict = {}          # (chain, hypothesis id) -> record
    order: list = []
    skipped = []
    chain = 0
    cur_h = None
    cur_a = None
    prev_end = None

    for m in _CALL.finditer(text):
        name = m.group(1)
        args, end = _args(text, m.end())
        if args is None:
            skipped.append(f"{path}: unbalanced {name}( near offset {m.start()}")
            continue
        # is this call piped onto the previous one?
        gap = text[prev_end:m.start()] if prev_end is not None else ""
        gap = re.sub(r"#[^\n]*", "", gap)
        piped = "%>%" in gap or "|>" in gap
        prev_end = end

        if name == "study" or not piped:
            chain += 1
            cur_h = cur_a = None
            if name == "study":
                continue
        pos, named = _split_args(args)
        if pos and _unquote(pos[0]) is None:
            pos = pos[1:]

        if name == "add_hypothesis":
            a = _take(pos, named, ["id"])
            cur_h = _unquote(a["id"]) or f"H{len(order)+1}"
            key = (chain, cur_h)
            if key not in hyps:
                hyps[key] = {"crits": [], "evals": {},
                             "line": text[: m.start()].count("\n") + 1}
                order.append(key)
        elif name == "add_analysis":
            a = _take(pos, named, ["id"])
            cur_a = _unquote(a["id"]) or "A"
        elif name == "add_criterion":
            a = _take(pos, named, ["id", "result", "operator", "comparator"])
            cid, res, op = _unquote(a["id"]), _unquote(a["result"]), _unquote(a["operator"])
            aid = _unquote(a.get("analysis_id") or named.get("analysis_id") or "") or cur_a or "A"
            if not cid or res is None or op is None:
                skipped.append(f"{path}: add_criterion with a computed argument")
                continue
            raw = a["comparator"]
            lit = _unquote(raw or "")
            if lit is not None:
                val = f"{aid}.{lit}"            # comparator names another result
            else:
                try:
                    val = float(raw)
                except (TypeError, ValueError):
                    skipped.append(f"{path}: comparator {raw!r} is an expression")
                    continue
            if cur_h is None:
                cur_h = "H1"
                key = (chain, cur_h)
                hyps.setdefault(key, {"crits": [], "evals": {},
                                      "line": text[: m.start()].count("\n") + 1})
                if key not in order:
                    order.append(key)
            hyps[(chain, cur_h)]["crits"].append(
                R.Criterion(cid, f"{aid}.{res}", op, val))
        elif name == "add_eval":
            a = _take(pos, named, ["type", "evaluation"])
            typ, ev = _unquote(a["type"] or ""), _unquote(a["evaluation"] or "")
            if not typ or ev is None:
                skipped.append(f"{path}: add_eval with a computed argument")
                continue
            key = (chain, cur_h)
            if key not in hyps:
                continue
            k = typ[:1].lower()
            if k in ("c", "f"):
                hyps[key]["evals"][k] = " ".join(ev.split())

    out = []
    for key in order:
        rec = hyps[key]
        if "c" not in rec["evals"] or "f" not in rec["evals"] or not rec["crits"]:
            continue
        crits = rec["crits"]
        out.append(R.Registration(
            f"{path.name}:{rec['line']} / {key[1]}", crits,
            rec["evals"]["c"], rec["evals"]["f"],
            domains=_domains(crits), relations=_relations(crits),
            source=f"{path}:{rec['line']}"))
    return out, skipped


def harvest(root: Path):
    regs, skipped = [], []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or ".git/" in str(p):
            continue
        if p.suffix == ".json":
            a, b = from_json(p)
        elif p.suffix in (".R", ".r", ".Rmd", ".rmd"):
            a, b = from_r(p)
        else:
            continue
        regs += a
        skipped += b
    return regs, skipped


if __name__ == "__main__":
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    verbose = "-v" in sys.argv
    regs, skipped = harvest(root)
    # DEDUPE. The repo ships the same prereg/postreg pair in four places
    # (docs/articles/files/, tests/testthat/input-data/, vignettes/files/,
    # vignettes/). Counting them four times would inflate both the clean count
    # and the denominator, so the census is over DISTINCT rules and every path
    # a rule appears at is printed beside it.
    seen: dict[tuple, list] = {}
    for rg in regs:
        key = (tuple(sorted((c.id, c.var, c.op, str(c.value)) for c in rg.criteria)),
               rg.corroboration, rg.falsification)
        seen.setdefault(key, []).append(rg)
    dup_total = len(regs)
    regs = [v[0] for v in seen.values()]
    copies = {id(v[0]): len(v) for v in seen.values()}
    where = {id(v[0]): [x.source for x in v] for v in seen.values()}
    KINDS = ["DEAD BRANCH", "NESTED RULES", "FOURTH STATE", "NO WITNESS",
             "ERROR", "UNDEFINED", "UNUSED"]
    buckets = {k: [] for k in KINDS}
    clean = 0
    for rg in regs:
        rep = R.analyse(rg)
        if verbose:
            print()
            print(rep)
        hit = False
        for k in KINDS:
            for f in rep.flags:
                if f.startswith(k):
                    buckets[k].append((rg.source, f))
                    hit = True
        if not hit:
            clean += 1
    print(f"== {dup_total} complete registrations under {root}, "
          f"{len(regs)} DISTINCT rules (the repo ships several of them "
          f"in more than one place)")
    print(f"   {clean} clean on every check")
    for k in KINDS:
        if buckets[k]:
            print(f"   {len(buckets[k])} {k}")
            for src, f in buckets[k]:
                print(f"      {src}")
                print(f"        {f}")
    if skipped:
        print(f"\n== {len(skipped)} things could not be parsed "
              f"(named, not hidden -- a census with an unknown denominator "
              f"is not a census):")
        from collections import Counter
        for why, n in Counter(s2.split(": ", 1)[-1] for s2 in skipped).most_common():
            print(f"   {n:3d}  {why}")
