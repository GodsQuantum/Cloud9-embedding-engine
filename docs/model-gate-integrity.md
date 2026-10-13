# Embedding model comparison — index and vector integrity

This change is a **source-only safety improvement** for the Cloud9 Embedding Engine bilingual retrieval benchmark, not a change in the live embedding server or its index format.

## Why it matters

The original `scripts/model_gate.py` read `/v1/embeddings` results in response-arrival order, assuming this was the input order. The OpenAI-compatible response has a numerical `index` field. Concurrent/batched model servers may return items out of order; computing recall directly from arrival order could cause misleading retrieval quality comparisons and the promotion/rejection of the wrong model.

The corrected gate:
- validates the exact number of returned embeddings and **distinct, contiguous integer response indices** from 0 to N-1;
- reorders vectors by their declared `index`, not by network response order;
- rejects zero, NaN/infinite, nonnumeric and mismatched-dimension vectors;
- rejects query/document embeddings with different dimensions before cosine;
- preserves the existing **six bilingual French/English reference pairs**, `--url`, `--model`, `recall_at_1`, `dimension` and timing keys;
- fails explicitly on an invalid comparison instead of silently emitting a normal retrieval score.

A server with no proper index field fails the benchmark rather than being assumed correct. This is intentional for **model comparisons**, not a global runtime requirement.

## Validation, 13 October 2026

Eight isolated Python contracts (`tests/model_gate_contract_test.py`) pass: scrambled response order restored; bad indices, malformed vectors, NaN/infinity, zero vectors, inconsistent dimensions rejected; retrieval `recall@1=1` on synthetic one-hot data; preservation of the six bilingual test pairs.

These tests **do not** query the live `192.168.1.219:8091` GPU endpoint. The production model remains `Qwen3-Embedding-0.6B Q8_0`, 1024 dimensions, with its previous multi-request throughput measurements retained. The AMD Radeon 780M is currently unsafe for new GPU A/B because Cloud9 Proxmox has two longstanding kernel D-state tasks. **Do not claim that any new embedding model is faster or more accurate without matched hardware measurements.**

To run the source-only gate:

```bash
bash tests/catalog.sh
python3 -B tests/model_gate_contract_test.py
```

Once the GPU is healthy and an explicit benchmark window is available, compare the production Qwen3 baseline with shortlisted open/commercial-license-compatible candidates on the same French+English corpus, real documents, retrieval relevance judgments, batch sizes, latency, VRAM/GTT and CPU energy. Model dimension/pooling changes **require explicit re-indexing**; do not switch the live endpoint's embeddings invisibly.
