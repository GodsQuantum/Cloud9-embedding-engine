<p align="center">
  <img src="docs/assets/logo.svg" width="132" alt="Cloud9 Embedding Engine logo">
</p>

<h1 align="center">Cloud9 Embedding Engine</h1>

<p align="center"><strong>RDNA-first, OpenAI-compatible embeddings. Benchmark first. Index second.</strong></p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.fr.md">Français</a> · <a href="README.zh-CN.md">简体中文</a>
</p>

Cloud9 Embedding Engine is a small, model-aware runtime for local semantic embeddings. It serves dedicated embedding models through llama.cpp's OpenAI-compatible API, keeps GPU occupancy small enough for shared AI workstations, and makes model changes explicit so vector indexes are never silently mixed.

The reference platform is an AMD Ryzen 7 8845HS / Radeon 780M (RADV/Vulkan), but the wrapper stays close to upstream llama.cpp and works on any backend supported by your llama.cpp build.

## Why a dedicated engine?

- **OpenAI-compatible** — `/v1/embeddings` works with Open WebUI and other OpenAI-compatible clients.
- **Small resident model** — embedding stays separate from the large chat model and can coexist with agent/inference workloads.
- **RDNA-first Vulkan** — validated on Radeon 780M, without ROCm-only assumptions.
- **Model gate** — benchmark a candidate before promoting it.
- **Index safety** — switching model or vector dimension is treated as a re-index event, never an invisible runtime tweak.
- **Bulk vs production profiles** — production defaults to one low-contention slot; initial corpus ingestion can temporarily use more slots.
- **No model lock-in** — the catalog documents quality, licensing, dimensions, context, pooling and trusted quantized variants.
- **Multi-node ready** — replicate the same model on several machines and health-check them with `scripts/cluster-doctor.sh`; route complete embedding requests instead of introducing tensor-sharding overhead. See [docs/distributed.md](docs/distributed.md).

## Current model shortlist

| Model | Why it is here | License | Context | Dimensions | Recommended efficient variant |
|---|---|---|---:|---:|---|
| **Qwen3-Embedding-0.6B** | Proven fast baseline on the reference 780M; strong multilingual retrieval | Apache-2.0 | 32K | 1024 | official GGUF Q8_0 |
| **Jina Embeddings v5 Text Small Retrieval** | 2026 quality-focused multilingual model, 119+ languages | CC BY-NC 4.0 | 32K | 1024 / Matryoshka | Q6_K or Q8_0 |
| **IBM Granite Embedding 311M Multilingual R2** | 2026 compact, commercial-friendly multilingual model; French explicitly enhanced | Apache-2.0 | 32K | 768 / Matryoshka | official ONNX/OpenVINO; GGUF after local verification |

See [docs/models.md](docs/models.md) for exact sources, caveats and alternatives.

## Reference hardware result

Qwen3-Embedding-0.6B Q8_0, llama.cpp Vulkan, Ryzen 7 8845HS / Radeon 780M:

| Test | Result |
|---|---:|
| single request, short benchmark | ~54.9 req/s |
| batch 8 | ~67.4 embeddings/s |
| batch 16 | ~68.9 embeddings/s |
| batch 32 | ~73.4 embeddings/s |
| cosine vs TEI/ONNX reference | 0.99959–0.99976 |

These are hardware-specific measurements, not universal claims. Large real-world chunks are slower; use the benchmark tool on your own corpus.


September 20, 2026 bulk-profile tuning on the reference 8845HS / Radeon 780M, Qwen3-Embedding-0.6B Q8_0, 32 synthetic ~556-token inputs:

| llama-server profile | Throughput |
|---|---:|
| `np=4, ubatch=512` | 4.59 embeddings/s |
| `np=4, ubatch=2048` | 5.66 embeddings/s |
| `np=8, ubatch=2048` | **10.85 embeddings/s** |
| `np=16, ubatch=2048` | 6.09 embeddings/s |

The result is deliberately profile-specific: current llama.cpp embedding mode requires the batch to fit one ubatch, and Vulkan multi-slot scaling is hardware/build dependent.

## Quick start

```bash
git clone https://github.com/GodsQuantum/cloud9-embedding-engine.git
cd cloud9-embedding-engine
./scripts/install.sh

cloud9-embedding-engine doctor
cloud9-embedding-server
```

Default endpoint: `http://127.0.0.1:8091/v1/embeddings`.

Use a specific model:

```bash
C9EE_MODEL_ID=qwen3-0.6b-q8 cloud9-embedding-server
C9EE_MODEL_ID=jina-v5-small-q6 cloud9-embedding-server
```

## Profiles

```text
production  1 slot   lowest GPU contention; recommended for normal RAG/query traffic
balanced    2 slots  moderate concurrency
bulk        8 slots  initial corpus ingestion on the validated 8845HS/780M profile; revert after the bulk run
```

All profiles default to `C9EE_CACHE_RAM=0`: embedding workloads rarely repeat identical prompts, so llama.cpp host prompt cache adds memory pressure without useful reuse. Override it only after workload-specific measurement.

The engine does **not** claim zero interference with a large LLM sharing the same iGPU. Production mode minimizes the collision window; benchmark concurrent inference on your hardware before increasing slots.

## Repository layout

- `bin/` — stable CLI and server entry points.
- `config/` — runtime examples.
- `models/catalog.json` — vetted model metadata.
- `scripts/` — install, benchmark and model gate.
- `docs/` — architecture, models, installation and benchmark protocol.
- `systemd/` — production service template.
- `tests/` — smoke tests and config checks.

## License

Cloud9 Embedding Engine code is MIT licensed. **Model licenses are separate** and are recorded in the model catalog. In particular, Jina v5 Small is non-commercial under CC BY-NC 4.0.
