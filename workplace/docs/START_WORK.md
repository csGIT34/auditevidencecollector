# Implementation prompt

Work in this repository, preserving existing changes. Read README.md, then only the operational contracts relevant to the immediate task.

Set up approved Python 3.12, install requirements-dev.txt with constraints.txt unchanged, run `python scripts/validate.py`, then run `python scripts/demo_audit_evidence.py --output <new-private-directory-outside-checkout>`. Replace the placeholder before execution. Record actual results; do not weaken checks or accept skipped tests.

The product collects audit evidence, including positive, adverse, incomplete and unassessed states. Keep exact-run archives immutable. Reports must not reassess historical facts or claim control satisfaction. Keep collection deterministic without runtime AI.

After establishing the baseline, identify the available workplace inputs: authorized tenant/subscription/Policy scope, identity/storage/network/callers, approved criteria/tailoring and actual Wiz schema/sanitized examples. Implement a concrete supported integration slice with tests. Native Wiz mapping is unfinished; never invent endpoints, fields or status meanings. Preserve source timestamps and identity, pagination, denials and partial errors. A resolved issue is not automatically positive evidence.

Use existing workplace infrastructure patterns. Keep deployment and live collection within actual authorization. Finish with changed files, exact validation results, outstanding inputs and the next concrete step. Update docs/STATUS.md with current acceptance evidence.
