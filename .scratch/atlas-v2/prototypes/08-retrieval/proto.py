"""Disposable retrieval prototype for wayfinder ticket 08 (Atlas v2).

Reads the frozen Atlas v1 vault read-only. Keeps indexes in memory; caches
OpenRouter embeddings under ./cache so reruns cost nothing. Not production code.
"""

import glob
import json
import math
import os
import pathlib
import re
import sqlite3
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).parent
VAULT = pathlib.Path(
    "~/dev/atlas/vault/instances/atlas/summaries/sources/artifacts"
).expanduser()
API = "https://openrouter.ai/api/v1"
EMBED_MODEL = "nvidia/nemotron-3-embed-1b:free"
RERANK_MODEL = "nvidia/llama-nemotron-rerank-vl-1b-v2:free"

V2_SECTIONS = [
    "Key points",
    "Approaches / mechanics",
    "Evidence / examples",
    "Caveats / open questions",
]
STOP = set(
    """a an the and or of to in on for with without by from at as is are be been was were it its this that these those
    i me my we our you your he she they them their what which who whom how why when where can could should would do does
    did done have has had will shall may might must not no yes if then than so such into over under about via per any all
    some each more most other only own same very just also there here up down out off again further once both few many
    much get got use using used make made want need like one two""".split()
)


def api_key():
    for line in (
        pathlib.Path("~/.config/mise/.env").expanduser().read_text().splitlines()
    ):
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip().strip("\"'")
    raise RuntimeError("OPENROUTER_API_KEY missing from ~/.config/mise/.env")


def post(path, body, retries=6):
    key = api_key()
    for attempt in range(retries):
        req = urllib.request.Request(
            API + path,
            data=json.dumps(body).encode(),
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:300]
            if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(5 * 2**attempt)
                continue
            raise RuntimeError(f"{path} HTTP {e.code}: {msg}") from None
        except (urllib.error.URLError, TimeoutError):
            if attempt < retries - 1:
                time.sleep(5 * 2**attempt)
                continue
            raise


# ---------- corpus ----------


def _frontmatter(s):
    out = {}
    for line in s.splitlines():
        k, _, v = line.partition(":")
        v = v.strip()
        try:
            out[k.strip()] = json.loads(v) if v.startswith(("[", '"')) else v
        except json.JSONDecodeError:
            out[k.strip()] = v.strip('"')
    return out


def load_docs():
    docs = []
    for f in sorted(glob.glob(str(VAULT / "**/*.md"), recursive=True)):
        t = open(f).read()
        m = re.match(r"---\n(.*?)\n---\n(.*)", t, re.S)
        fm, body = _frontmatter(m.group(1)), m.group(2)
        secs = {}
        for h, c in re.findall(r"^## (.+?)\n(.*?)(?=^## |\Z)", body, re.S | re.M):
            secs[h.split(" (")[0].strip()] = c.strip()
        tl = re.search(r"\*\*TL;DR\*\*:\s*(.*)", body)
        d = dict(
            id=fm["source_id"],
            title=fm.get("title", ""),
            author=fm.get("author", ""),
            publisher=fm.get("publisher", ""),
            kind=fm.get("source_kind", ""),
            url=fm.get("canonical_url", ""),
            tldr=tl.group(1) if tl else "",
            secs=secs,
        )
        head = f"{d['title']}\n{d['author']} | {d['publisher']} | {d['kind']}"
        # v1: the whole stored note as written (metadata lines, TL;DR, assessment, labels, routing, cues).
        d["v1"] = f"{d['title']}\n{body}"
        # v2: claims-first record per ticket 02 (no TL;DR, ratings, labels, routing notes, cues).
        d["v2"] = head + "\n\n" + "\n\n".join(secs.get(s, "") for s in V2_SECTIONS)
        # v2c: v2 plus v1 "reuse cues" (the open question from ticket 02).
        d["v2c"] = d["v2"] + "\n\n" + secs.get("Reuse cues", "")
        docs.append(d)
    return docs


# ---------- BM25 (SQLite FTS5) ----------


class BM25:
    def __init__(self, docs, field):
        self.db = sqlite3.connect(":memory:")
        self.db.execute(
            "create virtual table t using fts5(id unindexed, body, tokenize='porter unicode61')"
        )
        self.db.executemany(
            "insert into t values (?, ?)", [(d["id"], d[field]) for d in docs]
        )
        self.db.commit()

    @staticmethod
    def match_expr(q):
        toks = [
            w
            for w in re.findall(r"[a-z0-9]+", q.lower())
            if w not in STOP and len(w) > 1
        ]
        return " OR ".join(f'"{w}"' for w in dict.fromkeys(toks))

    def search(self, q, k=50):
        expr = self.match_expr(q)
        if not expr:
            return []
        rows = self.db.execute(
            "select id, -bm25(t) from t where t match ? order by bm25(t) limit ?",
            (expr, k),
        ).fetchall()
        return [(i, s) for i, s in rows]


# ---------- embeddings ----------


def _norm(v):
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def embed_texts(texts, prefix, batch=24):
    out = []
    for i in range(0, len(texts), batch):
        r = post(
            "/embeddings",
            {"model": EMBED_MODEL, "input": [prefix + t for t in texts[i : i + batch]]},
        )
        data = sorted(r["data"], key=lambda x: x["index"])
        out += [_norm(x["embedding"]) for x in data]
    return out


def doc_vectors(docs, field):
    path = HERE / "cache" / f"emb-{field}.json"
    cache = json.loads(path.read_text()) if path.exists() else {}
    todo = [d for d in docs if d["id"] not in cache]
    if todo:
        # Nemotron 3 Embed: "passage: " prefix for documents; ~4k-token serving cap, so clip long notes.
        vecs = embed_texts([d[field][:12000] for d in todo], "passage: ")
        for d, v in zip(todo, vecs):
            cache[d["id"]] = v
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(cache))
    return cache


def query_vectors(texts):
    path = HERE / "cache" / "emb-queries.json"
    cache = json.loads(path.read_text()) if path.exists() else {}
    todo = [t for t in dict.fromkeys(texts) if t not in cache]
    if todo:
        for t, v in zip(todo, embed_texts(todo, "query: ")):
            cache[t] = v
        path.write_text(json.dumps(cache))
    return [cache[t] for t in texts]


class Dense:
    def __init__(self, vecs):
        self.vecs = vecs

    def search(self, qv, k=50):
        scored = [(i, sum(a * b for a, b in zip(qv, v))) for i, v in self.vecs.items()]
        scored.sort(key=lambda x: -x[1])
        return scored[:k]


# ---------- fusion / rerank ----------


def rrf(*lists, k=60, top=50):
    s = {}
    for lst in lists:
        for rank, (i, _) in enumerate(lst):
            s[i] = s.get(i, 0) + 1 / (k + rank + 1)
    return sorted(s.items(), key=lambda x: -x[1])[:top]


def convex(a, b, alpha=0.5, top=50):
    """alpha*minmax(dense) + (1-alpha)*minmax(bm25); missing scores count as 0."""

    def mm(lst):
        if not lst:
            return {}
        hi, lo = max(s for _, s in lst), min(s for _, s in lst)
        return {i: (s - lo) / ((hi - lo) or 1) for i, s in lst}

    na, nb = mm(a), mm(b)
    s = {
        i: alpha * nb.get(i, 0) + (1 - alpha) * na.get(i, 0) for i in set(na) | set(nb)
    }
    return sorted(s.items(), key=lambda x: -x[1])[:top]


def nemotron_rerank(query, cands, texts, top_n=None):
    path = HERE / "cache" / "rerank.json"
    cache = json.loads(path.read_text()) if path.exists() else {}
    key = json.dumps([query, [i for i, _ in cands]])
    if key not in cache:
        r = post(
            "/rerank",
            {
                "model": RERANK_MODEL,
                "query": query,
                "documents": [texts[i][:6000] for i, _ in cands],
            },
        )
        cache[key] = [
            [cands[x["index"]][0], x["relevance_score"]] for x in r["results"]
        ]
        path.write_text(json.dumps(cache))
    out = sorted(((i, s) for i, s in cache[key]), key=lambda x: -x[1])
    return out[:top_n] if top_n else out


# ---------- metrics ----------


def ndcg(ranked, grades, k=10):
    dcg = sum(
        (2 ** grades.get(i, 0) - 1) / math.log2(r + 2) for r, i in enumerate(ranked[:k])
    )
    ideal = sorted(grades.values(), reverse=True)[:k]
    idcg = sum((2**g - 1) / math.log2(r + 2) for r, g in enumerate(ideal))
    return dcg / idcg if idcg else None


def recall(ranked, grades, k=10, min_grade=2):
    rel = {i for i, g in grades.items() if g >= min_grade}
    return len(rel & set(ranked[:k])) / len(rel) if rel else None
