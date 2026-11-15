# B2A performance budgets and measured results

Synthetic-only protocol `b2a-performance-1`; machine-readable evidence: [results-b2a.json](../benchmarks/results-b2a.json). Reproduce with `npm run bench` (prints results and returns nonzero on budget failure); to write a new artifact use `node benchmarks/run.mjs --output /tmp/fieldmind-benchmark.json`.

Environment: v24.22.1, linux x64, AMD EPYC 9V74 80-Core Processor. No network, LLM generation, real authentication or production I/O measured.

One warmup then five sequential samples; nearest-rank p95 is the maximum of those five, not a statistically stable production SLO. Indexed lookups use 100 samples. Dataset construction is excluded; graph guards, validation, indexing and snapshot cloning are included in projection. Repository commit includes snapshot loading, validation, append, transactional SQL and audit, against a preseeded 1,000-prospect workspace.

| Operation | p95 ms | Budget ms | Result |
|---|---:|---:|---|
| validate_1000_prospects_8000_claims | 148.84 | 1000 | PASS |
| projection_1000_prospects_8000_claims | 485.52 | 1500 | PASS |
| indexed_finding_1000_prospects | 0.02 | 10 | PASS |
| validate_5000_prospects_40000_claims | 634.20 | 5000 | PASS |
| projection_5000_prospects_40000_claims | 1438.39 | 7000 | PASS |
| indexed_finding_5000_prospects | 0.01 | 10 | PASS |
| projection_2000_competing_values_one_subject | 67.95 | 1500 | PASS |
| legacy_preview_10000_records | 229.73 | 2000 | PASS |
| repository_commit_on_1000_prospect_snapshot | 494.80 | 3000 | PASS |

All nine timing budgets passed. Whole benchmark process peak RSS: **742.5 MiB**, within the proposed **1,024 MiB** batch-process smoke budget. This includes sequential datasets and repeat-run allocation/GC; it is not a measured per-request allocation or a mobile memory claim.

## Enforced input/graph bounds

- Legacy JSON preview: 16 MiB UTF-8, 10,000 account records, twenty shown candidates per item; full raw data retained.
- Domain projection/proof: 64 MiB snapshot, 100,000 total records, 40,000 claims, 200,000 dependency/conflict edges, dependency depth 64. Guard before recursive domain validation.
- Repository command: 16 MiB serialized additions envelope; scope and graph validation before commit. A future HTTP server must reject oversize requests before allocating/parsing whole payloads.
- Competing single-valued findings: twenty alternative IDs shown plus total count; source records are retained, not truncated. The skew benchmark tests 2,000 competing values for one subject to catch quadratic conflict-output growth.

## Consequences for implementation

Treat 1,000 prospects as an initial interactive server-workspace batch; 5,000/40,000 is a bounded batch-capacity test. Full snapshot reconstruction is too memory-heavy to assume it belongs on a phone or in a shared high-concurrency process. Before production: partition/paginate data, avoid compiling all team workspaces at once, profile retained heap and concurrency, set worker/process memory limits, and test representative low-end mobile rendering separately. No such infrastructure is selected or deployed in B2A.

Single finding lookup is indexed after one compilation; do not call the B1 full-snapshot resolver separately for every card. Do not render the entire 40,000-claim result at once. Resource budgets are initial guardrails, not proof of reliable production throughput.

Repository proof uses an in-memory database: the timing says nothing about disk durability, remote database latency, process-crash recovery or authentication-provider latency. Five synthetic timing samples cannot establish production tail-latency guarantees. End-to-end research speed and usefulness belong to the separately authorized real-world intelligence benchmark.
