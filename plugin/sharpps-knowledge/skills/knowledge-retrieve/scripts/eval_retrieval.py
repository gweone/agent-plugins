#!/usr/bin/env python3
"""Score retrieval quality from a golden set and recorded search results.

Stdlib only and offline: it does not call any search tool. An agent records ranked IDs per
golden query; this script computes hit rate, recall@k, precision@k and MRR. Version
suffixes ("id@3") are ignored so a new version of the same item still counts.
"""
import argparse
import json
import sys


def base_id(value):
    return str(value).split("@", 1)[0]


def load(path, key):
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or not isinstance(data.get(key), list):
        raise ValueError("%s: expected an object with a '%s' list" % (path, key))
    return data[key]


def rank_list(returned):
    seen, ordered = set(), []
    for item in returned:
        item = base_id(item)
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def evaluate(cases, results, k):
    by_id = {str(r.get("id")): r for r in results}
    rows, missing = [], []
    for case in cases:
        cid = str(case.get("id"))
        if cid not in by_id:
            missing.append(cid)
        top = rank_list(by_id.get(cid, {}).get("returned", []))[:k]
        expected = {base_id(e) for e in case.get("expected", [])}
        found = [i for i in top if i in expected]
        row = {"id": cid, "negative": not expected, "returned": top}
        if expected:
            first = next((n for n, i in enumerate(top, 1) if i in expected), None)
            row.update(hit=bool(found), recall=len(found) / len(expected),
                       precision=(len(found) / len(top)) if top else 0.0,
                       rr=(1.0 / first) if first else 0.0)
        else:
            row["false_positive"] = bool(top)
        rows.append(row)
    pos = [r for r in rows if not r["negative"]]
    neg = [r for r in rows if r["negative"]]

    def mean(name):
        return sum(r[name] for r in pos) / len(pos) if pos else None

    return {
        "k": k, "cases": len(rows), "positive_cases": len(pos), "negative_cases": len(neg),
        "hit_rate": mean("hit") if pos else None, "recall_at_k": mean("recall"),
        "precision_at_k": mean("precision"), "mrr": mean("rr"),
        "false_positive_rate": (sum(r["false_positive"] for r in neg) / len(neg)) if neg else None,
        "missing_results": missing, "rows": rows,
    }


def fmt(value):
    return "n/a" if value is None else "%.3f" % value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--golden", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--min-hit", type=float)
    parser.add_argument("--min-mrr", type=float)
    args = parser.parse_args(argv)
    try:
        report = evaluate(load(args.golden, "cases"), load(args.results, "results"), args.k)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=1))
    else:
        print("cases=%d (positive %d, negative %d) k=%d" % (
            report["cases"], report["positive_cases"], report["negative_cases"], args.k))
        for name in ("hit_rate", "recall_at_k", "precision_at_k", "mrr", "false_positive_rate"):
            print("%-20s %s" % (name, fmt(report[name])))
        if report["missing_results"]:
            print("missing results for:", ", ".join(report["missing_results"]))
        for row in report["rows"]:
            ok = (not row["false_positive"]) if row["negative"] else row["hit"]
            print("  [%s] %s" % ("ok" if ok else "MISS", row["id"]))
    failed = False
    if args.min_hit is not None and (report["hit_rate"] or 0.0) < args.min_hit:
        failed = True
    if args.min_mrr is not None and (report["mrr"] or 0.0) < args.min_mrr:
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
