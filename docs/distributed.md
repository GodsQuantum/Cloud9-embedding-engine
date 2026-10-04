# Multi-node embeddings

Cloud9 Embedding Engine scales across machines by **replicating the model and routing complete embedding requests**.
It does not shard one embedding request across hosts. For this workload, request-level replication avoids network
synchronization overhead and gives useful throughput/failover immediately.

## Cloud9 + Celestra over USB4

1. Install the same Cloud9 Embedding Engine release and model/dimension on both nodes.
2. Use the Linux USB4/Thunderbolt network interface as a private point-to-point path when desired.
3. Verify every node with:
   `C9EE_CLUSTER_NODES=http://NODE1:8091,http://NODE2:8091 ./scripts/cluster-doctor.sh`
4. Put a health-aware least-connections/round-robin proxy in front only after both nodes report the same model
   identity and embedding dimension.

Never mix different embedding models or dimensions behind one logical endpoint: that silently corrupts vector
index semantics. A model change is a re-index event.

## Routing policy

- Interactive RAG/query traffic: least-connections or round-robin.
- Bulk indexing: shard batches across healthy nodes.
- No session affinity is required for normal embeddings.
- Keep per-node production concurrency independently benchmarked; a second machine is not a reason to increase
  `np` on each iGPU.
- On worker loss, retry the whole request on a healthy node; do not merge partial vectors.

The coordinator/load balancer is intentionally outside the inference process so a node remains usable standalone.
