# Local pipeline scale validation

The benchmark exercises actual fixture collection, assessment, create-only local archive publication, exact-run PDF generation and source-preservation verification. It creates no cloud resources and makes no Azure/Wiz calls.

```sh
python scripts/benchmark_pipeline.py --output ../scale-results --sizes 100 1000 2000
```

Use a new directory outside the checkout. Each size uses a fresh Python child process, mixed Storage/Kusto/Functions/network/unsupported resources, paginated inventory and injected denied detail reads. PASS, FAIL, UNKNOWN, ERROR, UNSUPPORTED and NOT_APPLICABLE are all represented. Each result preserves the source count, archive hashes, PDF size/pages/hash, durations, tool/platform/Python version and peak process RSS. No resources are dropped to meet a threshold.

The default local headroom targets are PDF publication <=120 seconds and peak RSS <=1,536 MiB. They are benchmark thresholds, not organization policy or process memory caps. `--worker-timeout` (default 300 seconds) bounds each benchmark child; a timeout/crash is recorded as failure, never a smaller successful inventory. `--max-report-seconds` and `--max-rss-mib` customize acceptance. Results are private JSON and synthetic archives, not uploaded CI artifacts.

## Measured development baseline, 2026-09-19

| Resources | PDF publication | Peak RSS | Pages | PDF bytes |
| ---: | ---: | ---: | ---: | ---: |
| 100 | 0.680 s | 65.78 MiB | 157 | 397,718 |
| 1,000 | 6.705 s | 217.64 MiB | 1,480 | 3,141,679 |
| 2,000 | 14.505 s | 389.77 MiB | 2,949 | 6,194,053 |

Measured on this Linux x86_64 Python 3.12 development machine with collector 0.4.0. All source hashes remained unchanged. The renderer and assessment rules were unchanged; full results stay outside the public repository. This is a narrow synthetic fixture benchmark, not a production capacity promise.

PDFs deliberately include full per-resource evidence and verification instructions, so page counts can be large. Real work data can have deeper dependencies, long fields, more child resources or denials. This benchmark includes fixture construction and rendering in peak RSS but excludes PDF inspection; it does not measure network latency, managed identity, Blob transfer/retries, Flex cold starts, cloud CPU allocation or simultaneous workloads. Validate the real approved work population before enabling a cadence.

Linux and macOS CI run the 100-resource case as a regression check. Run larger sizes locally when changing collection/archive/rendering behavior; do not turn all large PDFs into a per-test artifact upload.
