# Import the standalone audit evidence collector

Follow this document as the task instructions. Download only the clean project files listed below into the work environment. No repository clone, ZIP, Git history or source remote is needed.

## What to download

The standalone project is under `workplace/`. The exact allowlist and SHA-256 hashes are in [docs/workplace-files.json](../workplace-files.json). Download **only** those listed paths from `workplace/`, preserving their relative paths and removing the `workplace/` prefix in the destination. The list includes:

- `cloud_governance/`, `function_app.py` and `host.json`: application code and packaged data.
- `tests/` and synthetic JSON under `examples/`: regression tests and offline fixtures.
- Dependency files, `.gitignore`, `.funcignore`, settings templates and selected `scripts/`: setup, validation and packaging.
- `README.md` and selected `docs/`: operational instructions, the implementation prompt, and required catalog/schema data.

Do not copy other repository files. The file list, this import instruction and the downloader are transfer tools only; keep them outside the work project. The resulting project contains no source-repository links, origin manifest, development-history documents, personal infrastructure or Git metadata. Keep technical evidence provenance, vendor citations and catalog data inside the application intact.

## Download without cloning

Inspect the work repository's instructions and existing files first. Choose a **new** staging/project directory whose parent already exists. Resolve the current `main` commit once, then use that exact commit for every download. The script below downloads the small transfer helper into a temporary directory; that helper retrieves only allowlisted project files, verifies every hash and publishes the directory only after all downloads succeed.

Run with Python 3, replacing `DESTINATION` with an appropriate new directory. This downloads source only; it does not install dependencies, create Git metadata, log in to Azure or deploy anything.

```python
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.request import Request, urlopen

DESTINATION = Path("./audit-evidence-collector")  # Must not already exist.
REPOSITORY = "csGIT34/auditevidencecollector"

def read(url):
    request = Request(url, headers={"User-Agent": "workplace-source-import"})
    with urlopen(request, timeout=60) as response:
        return response.read()

revision = json.loads(read(
    f"https://api.github.com/repos/{REPOSITORY}/commits/main"
))["sha"]
with tempfile.TemporaryDirectory() as temporary:
    helper = Path(temporary) / "download.py"
    helper.write_bytes(read(
        f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/scripts/download_workplace_source.py"
    ))
    subprocess.run([
        sys.executable, str(helper), "--ref", revision,
        "--output", str(DESTINATION.resolve()),
    ], check=True)
```

If a project directory already exists, download to a new staging directory first. Compare files, then merge only the intended project content, preserving unrelated work. Include `.gitignore` and `.funcignore` when copying. Do not overwrite existing files indiscriminately. Do not add an origin remote or retain the transfer script/file list in the work repo. If GitHub access is restricted, report the exact access blocker rather than cloning or importing the entire repository as a fallback.

## Set up and validate

Read the downloaded `README.md` and `docs/START_WORK.md`. Read other operational contracts only for the task at hand. Machine-readable catalog data under `docs/audit` is required by tests and package checks; it is not exploratory reading.

From the downloaded project root, use approved Python 3.12 with pip/venv support and the approved package source:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/validate.py
python scripts/demo_audit_evidence.py --output ../audit-rehearsal
```

The rehearsal output must be a new private directory outside the checkout. Keep `constraints.txt` unchanged. Report actual results; do not accept skipped tests, weaken checks or infer live readiness from offline tests. Full dependency-based validation must run in this environment; source availability is not evidence of acceptance.

Use existing workplace CI and infrastructure conventions. Establish local readiness, then identify the actual tenant/scope, identity/storage/network, criteria and integration inputs for the next task. Deployment and live access require actual authorization. Native Wiz mapping remains unfinished; use real schema and sanitized examples rather than invented contracts.

Finish with the project location, files imported, exact validation results, outstanding inputs and the next concrete step. Update the project's `docs/STATUS.md` with current acceptance results, without adding transfer history or source-repository details to the project.
