# macOS development and offline validation

Use an approved Python 3.12 installation, Git and an approved package source. Production runs in Azure Functions; a Mac is not a production scheduler or host. Commands below start in the cloned repository root, independent of username or machine paths.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install --no-build-isolation --no-deps -e .
python scripts/validate.py
python -m build --no-isolation
```

The complete gate requires Azure SDKs, ReportLab, pypdf and jmespath. It checks all tests with no skips, host configuration, the research catalog and its packaged outline. Tests use fixtures/fake transports; they do not log in, obtain real tokens or connect to Azure. [Linux/macOS CI](https://github.com/csGIT34/auditevidencecollector/actions/workflows/offline.yml) runs the same gate and package builds. The [dispatch investigation](../infra/personal-lab/DISPATCH_INVESTIGATION.md) records the latest local gate and its limits. Check CI for the exact commit being cloned, and run the gate on the actual work Mac. The secure local FileStore uses POSIX no-follow opens, private files, directory-relative traversal and hard-link create-only publication. Validate on the Mac's intended filesystem; native Windows and network-share semantics are not claimed.

For a demonstration:

```sh
python -m azure_at_rest collect --fixture examples/demo-fixture.json --store evidence/archive
python -m azure_at_rest runs --store evidence/archive
# Use the exact newly printed run ID. The collection exits 1 intentionally.
python -m azure_at_rest pdf --store evidence/archive --run-id YOUR_EXACT_RUN_ID --export output/pdf/demo.pdf
```

A repeated export requires a new filename; nothing in the archive is replaced. No Azure authentication occurs for fixture runs. The fixture contains 34 resources with three failed rows and incomplete coverage. Optional Poppler rendering helps visual review; Poppler is not a production PDF-generation dependency.

## Functions development

The Functions Python SDK is included in the developer requirements. Its registration and handlers are tested offline. Azure Functions Core Tools v4 is a separate approved developer installation; it is not bundled or installed by the project. Before using `func start`, review the official [local development guide](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local). Core Tools and its extension loading may require downloads, and timer coordination needs runtime storage; do not assume a local host start is wholly offline.

Copy `local.settings.example.json` to ignored `local.settings.json`. Both operations are disabled by default and the collection schedule is empty. Do not fill in workplace settings or enable an operation until work-tenant access is authorized. Use `func start --port 7071` on localhost only; local Functions HTTP key checks are disabled. No public tunnel or exposed development port is part of this workflow.

After creating the Linux amd64 Python 3.12 deployment ZIP, you can test it in Microsoft's actual Functions container on a Mac with Docker Desktop or on Linux with Docker Engine:

```sh
python scripts/smoke_functions_runtime.py --package dist/functions-runtime.zip --output ../functions-runtime-check
```

Use a new output directory outside the checkout. The script pins the Microsoft image by digest, binds only a random loopback port, uses temporary local function keys, and supplies no Azure login, tenant settings or cloud credentials. Collection, reporting and the timer remain disabled. It checks function indexing, rejects missing/wrong keys and sends 20 consecutive authenticated validation requests over fresh connections. It records the package hash, host version and results, then removes its container. The container uses at most 2 GiB and one CPU. Initial image/extension downloads require internet access; this optional integration check is separate from the fixture-only offline gate. Linux CI runs it too. A local pass does not validate Flex ingress, managed identity, Azure networking or a different cloud host version.

For authorized local Azure adapter testing, `CG_AUTH_MODE=azure_cli` plus `CG_LOCAL_DEVELOPMENT=true` explicitly selects a tenant-bound developer credential. It is rejected when Azure host environment markers are present. `CG_MANAGED_IDENTITY_CLIENT_ID` may remain empty for this developer mode. The standard CLI still uses its current authorized CLI context, so inspect `az cloud show` and `az account show`, sign in to the intended tenant and pass an explicit subscription. No DefaultAzureCredential chain silently chooses another identity.

Use the workplace configuration guide for the separate runtime/evidence storage settings. An emulator is optional developer infrastructure requiring its own approval/setup; no emulator is required by the tests or automatically installed here. Do not place keys in tracked settings or shell scripts.

## Source transfer and build

The GitHub repository transfers source and reviewed configuration templates. `git status --short` and `git diff --cached` are the final staged-content checks before a separately authorized push. `.gitignore` excludes local settings, environments, credentials and standard output paths, but cannot protect an arbitrary forced export or a manual whole-directory upload.

Create the allowlisted source ZIP with `python scripts/package_functions.py --output dist/functions-source.zip`. Build dependencies for Linux in a clean approved build environment or with the selected Functions remote-build mechanism. Never deploy the Mac virtual environment. See [AZURE_FUNCTIONS.md](AZURE_FUNCTIONS.md) for hosted inputs, identity, triggers, limits and workplace acceptance.

## Additional local checks

Run `python scripts/demo_wiz.py --output ../wiz-demo` to exercise the complete synthetic [Wiz workflow](WIZ_INTEGRATION.md). Run `python scripts/benchmark_pipeline.py --output ../scale-results --sizes 100 1000 2000` to measure mixed-inventory/PDF scale without cloud calls. Both require new directories outside the checkout; outputs are private. See [scale results and limits](LOCAL_SCALE_VALIDATION.md).

The main validation gate includes `scripts/check_docs.py`, which checks relative Markdown file targets; external URLs and heading anchors are not checked. CI also benchmarks 100 resources on both operating systems and checks the packaged Linux Functions runtime.

To test home Terraform without live credentials/state, use the pinned Terraform version in `infra/personal-lab/versions.tf` and an isolated data directory:

```sh
export TF_DATA_DIR="$(mktemp -d)"
terraform -chdir=infra/personal-lab fmt -check -recursive
terraform -chdir=infra/personal-lab init -backend=false -input=false -lockfile=readonly
terraform -chdir=infra/personal-lab validate
terraform -chdir=infra/personal-lab test
unset TF_DATA_DIR
```

These tests use mocked providers and plan-only runs; they do not provision or read Azure resources. Initial provider/action/dependency downloads require internet access. Never point the test data directory at live Terraform state. CI runs these four mocked checks without Azure credentials.
