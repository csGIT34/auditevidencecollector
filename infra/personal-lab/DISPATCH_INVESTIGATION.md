# Flex HTTP dispatch investigation — 2026-09-19

**Availability is still blocked. No runtime workaround is validated.** This follow-up isolates the failure from collector/PDF application code; it does not establish an Azure platform root cause or approve workplace deployment. Original live evidence remains unchanged.

## Controlled observations

The disposable personal app used East US Flex Consumption, Linux Python 3.12, Functions host `4.1054.250.26428`, extension bundle `4.39.1`, and `azure-functions==1.25.0`. Baseline: 2 GiB, maximum one on-demand instance per function group, HTTP concurrency one, zero always-ready instances. Collection/report/probe were disabled and no timer was configured. Networking, UAMI and storage permissions were unchanged.

| Control | Observed result |
| --- | --- |
| Original report route, prior session | First invalid request HTTP 400; next invalid request HTTP 503 in about 60 seconds. Reproduced with independent HTTP clients. |
| Minimal synchronous endpoint, fresh start | HTTP 200 in 0.185 seconds, returned counter 1; next request HTTP 503 in 60.090 seconds. |
| Same endpoint, HTTP concurrency temporarily two | First request HTTP 503 in 60.129 seconds. No successful workaround established. |
| Same endpoint, maximum instances temporarily two | First request HTTP 200 in 1.838 seconds; next request HTTP 503 in 60.099 seconds. |
| Minimal async endpoint | SCM reported deployment complete; after a fresh start, first request HTTP 503 in 60.119 seconds. No successful async invocation was observed, so this does not establish an async-worker mechanism. |

Each comparison was bounded, ended at the first unexpected response, restored the scale settings and stopped the app. The temporary endpoints did not import the audit application or call ARM, Blob, PDF rendering or collection. They retained the baseline dependency wheels and host configuration. This rules out an audit handler/import being necessary to reproduce the symptom; it does not rule out dependencies, hosting configuration or platform behavior.

Temporary `FunctionAppLogs` captured successful Python-worker initialization, route registration, and successful minimal handler executions in 13 ms and 29 ms. The retrieved logs contained no corresponding second handler invocation, while periodic host health responses remained HTTP 200. **Inference:** the evidence points toward dispatch before the handler, rather than a long-running audit operation. Telemetry arrived with delay; absent log entries are not proof of a specific internal failure. No worker crash or definitive causal error was captured.

## Minimal code used

This is diagnostic code for a disposable app, not a production health endpoint. Deployment replaces an app's code. The control used the original `host.json` and pinned Linux deployment dependencies. Invocation requires the existing function key and allowed operator address; never put a key in a URL or publish it with evidence.

```python
import json
import os
import threading
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
count = 0
lock = threading.Lock()

@app.function_name(name="DispatchControl")
@app.route(route="dispatch-control", methods=["POST"])
def dispatch_control(req: func.HttpRequest) -> func.HttpResponse:
    global count
    with lock:
        count += 1
        current = count
    return func.HttpResponse(
        json.dumps({"count": current, "pid": os.getpid()}),
        status_code=200, mimetype="application/json",
        headers={"Cache-Control": "no-store"})
```

The async comparison changed only the handler declaration to `async def` and its diagnostic response marker. Expected: consecutive HTTP 200 responses with advancing counters. Actual: responses above, including plain `Site Unavailable` HTTP 503, not an application JSON error. Exact private UTC request records, headers, bodies, deployment status and logs were saved locally. Personal resource identifiers, credentials, Terraform state and audit objects are excluded from this repository. No support case or public issue has been submitted.

## Separate packaging defect fixed

An initial temporary control ZIP accidentally used `zipfile.writestr` defaults, producing mode `0600` entries. Its unhealthy startup result was discarded as an invalid control, and the test was rebuilt with original mode `0644` entries. The original application package already had readable modes; this does **not** explain its 503.

That exposed a reproducible weakness in our normal builders: a private build directory with `umask 077` can produce unreadable deployment files. Both source and Linux runtime packaging now normalize file modes **inside the ZIP** to `0644`. Local source files and the output ZIP retain their private permissions. A regression using a `0600` dependency and restrictive umask failed before the fix and passed afterward. The full pinned offline gate passed **121 tests, zero skips**, plus catalog/export checks. This change affects packaging, not assessment criteria or HTTP handler behavior.

## Cost and preservation

Temporary diagnostics used one pay-as-you-go Log Analytics workspace and one FunctionAppLogs setting, with a verified 0.1 GB daily ingestion setting and 30-day included retention. No Application Insights resource, alert, Sentinel activation, commitment tier or always-ready instance was added. The daily ingestion setting can overshoot; it is not a spending cap.

The official East US Analytics ingestion meter was USD 2.30/GB above the shared free allowance. The estimate without free grants was USD 0.023 per 10 MB or USD 0.23 per 100 MB, communicated before enabling. One intermediate query measured 52,918 billed bytes across 107 records (about USD 0.00012 at that rate). This is a partial ingestion observation, not the complete Azure bill. Cost Management returned no posted month-to-date rows; billing delay prevents a zero-cost claim. [Azure Monitor pricing](https://azure.microsoft.com/en-us/pricing/details/monitor/), [daily cap limitations](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/daily-cap).

All nine original evidence objects were downloaded with the existing container-scoped Entra Data Reader and checked against their prior SHA-256 values. Every hash matched; no new audit evidence object was created. No additional collection or saved-run PDF was attempted while availability remained unresolved.

## Application restoration

The corrected application v0.3.2 / PDF renderer 1.2 package was deployed after the controls. The CLI reported successful deployment, and the indexed functions were `GenerateReport` and `LabProbe`, with no timer. Uploaded package: 16,190,157 bytes, SHA-256 `3315e44847a164e79788eadf3bfa80ae3af626000a5b93cb75f7f0ada6b66fc0`. Its application source matched published commit `242d9578ef756429548bae2f16490127613d7f34`; the later packaging fix changes build tooling, not those runtime bytes.

The restored report route still reproduced the failure: invalid `run_id=latest` returned HTTP 400 in 42.492 seconds, followed by HTTP 503 in 60.131 seconds. No report generation was requested. The app was then stopped. This deployment does not resolve the availability gate.

## Verified final state

The app is **Stopped**, all three operation flags are false, the schedule is empty, and no timer is indexed. HTTP concurrency and maximum instances are both restored to one, with zero always-ready instances. The original app settings, operator-only network restriction and disabled SCM basic authentication were verified. The temporary diagnostic setting and workspace were removed; the five original lab resources and two pre-existing resources remain. Available diagnostic records were exported privately before workspace removal.

The final ingestion query returned 171 records / 84,933 billed bytes (about USD 0.0002 at the stated rate before allowances), with latest received event time 19:54:57 UTC. This is received telemetry, not a complete invoice. The final Cost Management query was unavailable; storage and ordinary service costs remain until authorized lab teardown after workplace handoff. No monitoring automation or support message was created.

## Remaining acceptance gate

Use the minimal reproduction and private diagnostics for Azure-side dispatch investigation, or review a separately bounded deployment comparison. Do not weaken network/authentication or introduce always-ready/premium capacity to hide the symptom. Before workplace approval, prove repeated requests reliable, perform the second scoped collection, and regenerate the older run's PDF while retaining all original object hashes. Workplace identity, caller authentication, network and retention validation still apply.
