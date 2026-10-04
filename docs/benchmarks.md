# Benchmark protocol

Two tests are intentionally separate.

## Throughput

`scripts/bench_client.py` measures the served API on the actual machine. Record:

- model and quantization;
- hardware and backend;
- batch size;
- request concurrency;
- input size;
- vector dimension;
- wall time and p95 latency.

Do not compare results from different input lengths as if they were equivalent.

## Retrieval smoke gate

`scripts/model_gate.py` runs a tiny bilingual FR/EN recall@1 check. It catches broken pooling, wrong endpoint configuration and obviously bad conversions.

It is **not** a replacement for MTEB, MIRACL, BEIR or a domain-specific evaluation.

## Cloud9 reference

Reference hardware: Ryzen 7 8845HS / Radeon 780M, RADV Vulkan.

Qwen3-Embedding-0.6B Q8_0 produced about 54.9 req/s on the short sequential micro-benchmark and about 73.4 embeddings/s at batch 32. Five cross-engine samples had cosine 0.99959–0.99976 versus the TEI/ONNX representation.

Large knowledge-base chunks around ~900 tokens take materially longer. Production configuration should therefore be chosen from real corpus tests, not the short benchmark alone.


## Cloud9 profile gate — 2026-10-03

Same model and backend for every arm: Qwen3-Embedding-0.6B Q8_0, Radeon 780M / Vulkan, batch size 2048. Raw artifacts are retained locally under `bench/results/2026-10-03-profile-ab/`.

| Profile | Context | Parallel | UBatch | Recall@1 | Small req/s | Batch32 emb/s | Long8 emb/s |
|---|---:|---:|---:|---:|---:|---:|---:|
| previous production | 8192 | 1 | 512 | 1.00 | 20.245 | 20.529 | 3.369 |
| selected | 8192 | 4 | 2048 | 1.00 | 19.238 | 26.436 | 3.432 |
| np8 | 8192 | 8 | 2048 | 1.00 | 19.731 | 26.831 | 3.311 |
| bulk np8 | 16384 | 8 | 2048 | 1.00 | 19.495 | 27.096 | 3.338 |

Decision:
- retain Qwen3-Embedding-0.6B Q8_0 and its 1024-dimensional index compatibility;
- production profile becomes **8K / np4 / ub2048**;
- versus the previous profile it improves batch32 throughput by ~28.8% and the long-input test by ~1.9%, with ~5% lower single-request microbenchmark throughput;
- np8 and 16K add too little to justify extra parallel/context capacity;
- BitNet official GGUFs remain runtime-blocked on the current llama.cpp tensor type, and Harrier remains a research candidate; no re-index is justified.

A later confirmation request against the live production endpoint was deliberately excluded from profile selection because concurrent Cloud9 workloads (Next.js build, n8n, MCPProxy, HAOS) reduced batch32 throughput to 1.844 emb/s. The controlled exclusive A/B above is the comparable selection dataset.

## Idle polling optimization — 2026-10-04

The production llama-server was observed with no TCP clients and no recent requests while consuming about 143% host CPU at idle. The cause was llama.cpp's default `--poll 50` worker polling.

The wrapper now defaults to:
- `C9EE_POLL=0`;
- `C9EE_POLL_BATCH=0`.

Live validation on the same Qwen3-Embedding-0.6B Q8_0 / 8K / np4 / ub2048 profile:
- `GET /health`: OK;
- one French embedding request: 0.2469 s, 1 vector, 1024 dimensions;
- three consecutive 1-second idle CPU samples after the request: **0.00% / 0.00% / 0.00%**;
- previous idle process CPU before the change: about **143%**.

This is retained because it removes continuous idle CPU burn without changing the model, index dimension, batching profile or API contract. Throughput selection remains based on the controlled profile A/B above; the 0.2469 s smoke is a functional/idle-power validation, not a new throughput benchmark.
