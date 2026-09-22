# Audit evidence collector

Read-only Azure evidence collection with immutable run archives and full or selected JSON, Markdown and PDF reports. Azure Policy, direct configuration reads, normalized Wiz imports and operational records retain positive, adverse and incomplete evidence. Reports do not certify control satisfaction. Collection and reporting require no runtime AI.

## Setup

Use Python 3.12 with pip/venv support on Linux, WSL's Linux filesystem, or macOS. Use an approved package source and keep dependency constraints unchanged.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/validate.py
python scripts/demo_audit_evidence.py --output ../audit-rehearsal
```

The rehearsal directory must be new and outside the checkout. It uses synthetic fixtures and makes no cloud calls. The validation gate requires all dependencies and rejects skipped tests. JSON catalog data under `docs/audit` supports tests and generated package data; it is not required reading.

## Operate and extend

- [Runtime and deployment](docs/WORKPLACE_RUNTIME_CONTRACT.md)
- [Functions settings](docs/AZURE_FUNCTIONS.md)
- [Report selections](docs/EVIDENCE_REPORTS.md)
- [Wiz integration](docs/WIZ_INTEGRATION.md)
- [Implementation prompt](docs/START_WORK.md)

Collection and reporting default disabled. Supply approved tenant/scope, managed identity, storage, network, criteria and caller authorization before enablement. Settings templates contain placeholders only.

## Current limitations

Direct collection runs before Policy. Policy collection currently handles one subscription/assignment with a 5,000-row retention bound. Overflow remains incomplete; Policy denial currently prevents publication. Definition/parameter/exemption snapshots and estate-wide orchestration remain unfinished. Native Wiz authentication and schema mapping require actual source contracts. Guest/Kubernetes have separate supplements; combined selected-report rows remain unfinished. Evidence availability does not establish whole-objective effectiveness.
