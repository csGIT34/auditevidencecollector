# Copyable workplace source import prompt

Attach `workplace-source-ready-20260922.zip` to the work session, then copy the text below. If generating a fresh bundle, run `python3 scripts/export_workplace_source.py --output /tmp/workplace-source.zip` from the prepared lab checkout and substitute that filename in the prompt.

---

Import the attached workplace-source-ready-20260922.zip into this work repository.

1. Extract into a temporary staging directory. Verify every payload hash in WORKPLACE_SOURCE_MANIFEST.json before editing. Record the source revision and working-tree provenance. This bundle includes handover changes beyond the last committed lab revision; do not replace it with an older remote clone.

2. Inspect this repo’s instructions and existing files. Import the bundle into an appropriate project directory, preserving unrelated work and resolving path conflicts carefully. Do not download the whole lab repository or its exploratory documentation.

3. Read the bundled README.md, docs/WORKPLACE_AZURE_HANDOFF.md, and docs/prompts/AZURE_ADAPTER_IMPLEMENTATION.md. Read other guides only as needed.

4. Set up approved Python 3.12 with a virtual environment. Install requirements-dev.txt without relaxing constraints.txt. Run:

   ```sh
   python scripts/validate.py --workplace
   python scripts/demo_audit_evidence.py --output <new-private-directory-outside-checkout>
   ```

   Replace the angle-bracket placeholder with a real, new private directory outside the checkout before running the rehearsal. The workplace gate retains all tests and rejects skips. Only lab research-prose checks are omitted. Keep the machine-readable catalog/test data even though it lives under docs/audit.

5. Adapt CI to workplace conventions. Do not deploy personal Terraform or build with --with-lab-probe. Establish local readiness before cloud integration, using actual workplace inputs and authorization.

Report imported files, exact validation results, missing inputs, and the next concrete integration step. Do not claim live readiness from offline tests.
