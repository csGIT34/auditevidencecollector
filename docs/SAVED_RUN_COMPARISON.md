# Compare exact saved runs

Both runs must already be in the same local archive. No Azure calls or reassessment occur.

```sh
cloud-governance compare-runs --store /private/archive --before r_EXACT_BEFORE --after r_EXACT_AFTER
cloud-governance comparison-show --store /private/archive --comparison-id d_EXACT_COMPARISON
```

Replace placeholders with actual `r-` / `d-` identifiers. The first command writes immutable JSON and Markdown under `run-comparisons/`, with a completion manifest written last. The second verifies both source archives and every saved comparison object before showing the original Markdown. The source runs are unchanged. An intent without a manifest is an incomplete publication.

The JSON includes before/after observations, timestamps, saved criteria, rule definitions, results, manifest hashes and declared scope. Changes distinguish new/missing observations, changed facts, changed criteria/rules, changed outcomes and loss of previously assessable evidence. Timestamp-only changes do not count as configuration drift. ARM encryption and configuration rows and Graph configuration rows are included; legacy encryption-only archives can be compared with newer runs.

Missing resources are **no longer observed**, not proven deleted. Scope, permissions, pagination, collector versions and timing can explain differences. Changed results with changed criteria do not prove a resource changed. A draft/approved policy transition is recorded separately from the observation. Comparison is not a compliance conclusion. Inspect full JSON for saved values; the Markdown provides the changed-row index.
