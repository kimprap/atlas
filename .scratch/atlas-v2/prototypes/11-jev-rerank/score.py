"""Recompute ticket 11's scores from the saved files. Read-only; no API calls.

Run: python3 score.py
"""

import json
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).parent
T08 = HERE.parent / "08-retrieval"
sys.path.insert(0, str(T08))
import proto  # noqa: E402

Q = json.loads((T08 / "queries.json").read_text())
QID = {q["qid"]: q for q in Q}
G = json.loads((T08 / "grades.json").read_text())
RUNS08 = json.loads((T08 / "runs-top10.json").read_text())
NEW = json.loads((HERE / "runs.json").read_text())
EXTRA = {}
for k, g in json.loads((HERE / "grades-new.json").read_text())["new"].items():
    qid, i = k.split("|")
    EXTRA.setdefault(qid, {})[i] = g

METHODS = {
    "bm25_v2_rw (no rerank)": {q: RUNS08[q]["bm25_v2_rw"] for q in RUNS08},
    "opus_high (ticket 08)": {q: RUNS08[q]["bm25_v2_rw+llm"] for q in RUNS08},
    "opus_medium": NEW["opus_medium"],
    "jev_short": NEW["jev_short"],
    "jev_full": NEW["jev_full"],
    "nemotron (ticket 08)": {q: RUNS08[q]["bm25_v2_rw+nemo"] for q in RUNS08},
}


def grades(qid):
    g = dict(G[qid])
    g.update(EXTRA.get(qid, {}))
    if qid == "R1":  # the user's six trading sources override the grader
        for i in QID["R1"]["gold_user"]:
            g[i] = 2
    return g


def rr(run, q):
    top = run[q["qid"]][:10]
    return 1 / (top.index(q["seed"]) + 1) if q["seed"] in top else 0


def mean(a):
    return sum(a) / len(a)


def boot(d, n=10000, seed=7):
    rnd = random.Random(seed)
    ms = sorted(mean([d[rnd.randrange(len(d))] for _ in d]) for _ in range(n))
    return mean(d), ms[int(0.025 * n)], ms[int(0.975 * n)]


SQ = [q for q in Q if "seed" in q]
print("| Method | nDCG@10 all | Recall@10 all | nDCG@10 real (R) | Seed MRR | Seed at rank 1 | R1 six in top 10 |")
print("| - | - | - | - | - | - | - |")
for m, run in METHODS.items():
    nd = [proto.ndcg(run[q["qid"]][:10], grades(q["qid"])) for q in Q]
    rc = [x for q in Q if (x := proto.recall(run[q["qid"]][:10], grades(q["qid"]))) is not None]
    ndr = [n for q, n in zip(Q, nd) if q["qid"].startswith("R")]
    first = sum(run[q["qid"]][0] == q["seed"] for q in SQ)
    r1 = sum(i in run["R1"][:10] for i in QID["R1"]["gold_user"])
    print(f"| {m} | {mean(nd):.3f} | {mean(rc):.3f} | {mean(ndr):.3f} | {mean([rr(run, q) for q in SQ]):.3f} | {first}/{len(SQ)} | {r1}/6 |")

print()
print("| Comparison | Metric | Difference | 95% CI |")
print("| - | - | - | - |")
for a, b in [
    ("jev_full", "opus_high (ticket 08)"),
    ("jev_short", "opus_high (ticket 08)"),
    ("jev_full", "opus_medium"),
    ("jev_short", "opus_medium"),
    ("opus_medium", "opus_high (ticket 08)"),
    ("jev_full", "jev_short"),
    ("jev_full", "nemotron (ticket 08)"),
]:
    A, B = METHODS[a], METHODS[b]
    d = [proto.ndcg(A[q["qid"]][:10], grades(q["qid"])) - proto.ndcg(B[q["qid"]][:10], grades(q["qid"])) for q in Q]
    print("| %s vs %s | nDCG@10 | %+.3f | %+.3f to %+.3f |" % (a, b, *boot(d)))
    d = [rr(A, q) - rr(B, q) for q in SQ]
    print("| %s vs %s | Seed MRR | %+.3f | %+.3f to %+.3f |" % (a, b, *boot(d)))
