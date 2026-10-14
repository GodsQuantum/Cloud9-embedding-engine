#!/usr/bin/env python3
"""Small bilingual retrieval correctness gate, never an MTEB replacement.

OpenAI-compatible embedding response indexes must be validated and re-ordered
before recall calculations. Incorrect ordering can quietly corrupt the A/B.
"""
import argparse
import json
import math
import sys
import time
import urllib.request

PAIRS = [
    ("serveur de sauvegarde pour machines virtuelles", "Proxmox Backup Server stores versioned VM and container backups."),
    ("spectacle humoristique et écriture de blagues", "A stand-up comedian writes jokes, punchlines and comic premises for a live comedy show."),
    ("recherche sémantique de documents", "Semantic search retrieves passages by meaning rather than exact keywords."),
    ("température des disques durs", "Hard drive temperature should be monitored under sustained storage load."),
    ("réseau USB4 entre deux ordinateurs", "USB4 host-to-host networking can expose a high-speed point-to-point link."),
    ("transcription audio en français", "French speech transcription converts recorded audio into searchable text."),
]


def ordered_embeddings(data, expected_count):
    """Reject malformed, duplicated, misdimensioned or non-finite embeddings."""
    if not isinstance(data, list) or len(data) != expected_count or not data:
        raise ValueError("Unexpected embedding row count")
    if not all(isinstance(row, dict) for row in data):
        raise ValueError("Malformed embedding row")
    indexes = [row.get("index") for row in data]
    if any(type(i) is not int for i in indexes) or sorted(indexes) != list(range(expected_count)):
        raise ValueError("Embedding indices missing, duplicated or out of range")
    rows = sorted(data, key=lambda row: row["index"])
    vectors = []
    width = None
    for row in rows:
        raw = row.get("embedding")
        if not isinstance(raw, list) or not raw or any(type(x) not in (int, float) for x in raw):
            raise ValueError("Embedding is not a nonempty numeric list")
        values = [float(x) for x in raw]
        if not all(math.isfinite(x) for x in values):
            raise ValueError("NaN or infinity in embeddings")
        if not any(x != 0.0 for x in values):
            raise ValueError("Zero embedding cannot be cosine-normalized")
        if width is None:
            width = len(values)
        if len(values) != width:
            raise ValueError("Mixed embedding dimensions in one response")
        vectors.append(values)
    return vectors


def embed(url, model, items):
    request = urllib.request.Request(
        url,
        data=json.dumps({"model": model, "input": items}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError("Malformed embedding response")
    return ordered_embeddings(payload.get("data"), len(items))


def cos(a, b):
    if not a or len(a) != len(b):
        raise ValueError("Mismatched or empty vector dimensions")
    numerator = sum(x * y for x, y in zip(a, b, strict=True))
    anorm = math.sqrt(sum(x * x for x in a))
    bnorm = math.sqrt(sum(y * y for y in b))
    if anorm == 0 or bnorm == 0 or not all(math.isfinite(z) for z in (numerator, anorm, bnorm)):
        raise ValueError("Invalid cosine norm")
    score = numerator / (anorm * bnorm)
    if not math.isfinite(score):
        raise ValueError("Non-finite cosine similarity")
    return score


def evaluate(url, model, pairs=PAIRS):
    queries = [q for q, _ in pairs]
    docs = [d for _, d in pairs]
    start = time.perf_counter()
    qv = embed(url, model, queries)
    dv = embed(url, model, docs)
    if len(qv[0]) != len(dv[0]):
        raise ValueError("Query/document embedding dimensions differ")
    correct = 0
    hit_at_3 = 0
    reciprocal_rank = 0.0
    ndcg_at_3 = 0.0
    for i, query in enumerate(qv):
        scores = [cos(query, document) for document in dv]
        # Stable, deterministic tie-breaking prevents backend-order noise.
        ranked = sorted(range(len(scores)), key=lambda j: (-scores[j], j))
        rank = ranked.index(i) + 1
        correct += rank == 1
        hit_at_3 += rank <= 3
        reciprocal_rank += 1.0 / rank
        if rank <= 3:
            ndcg_at_3 += 1.0 / math.log2(rank + 1)
    return {
        "pairs": len(pairs),
        "recall_at_1": correct / len(pairs),
        "recall_at_3": hit_at_3 / len(pairs),
        "mrr": reciprocal_rank / len(pairs),
        "ndcg_at_3": ndcg_at_3 / len(pairs),
        "elapsed_s": round(time.perf_counter() - start, 4),
        "dimension": len(qv[0]),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8091/v1/embeddings")
    parser.add_argument("--model", default="local")
    args = parser.parse_args()
    try:
        result = evaluate(args.url, args.model)
    except (ValueError, KeyError, TypeError, ArithmeticError) as exc:
        print(json.dumps({"status": "invalid-embedding-result", "reason": str(exc)}), file=sys.stderr)
        return 3
    print(json.dumps(result, indent=2))
    return 0 if result["recall_at_1"] == 1.0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
