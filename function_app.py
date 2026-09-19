"""Azure Functions v2: scheduled collection and explicitly requested saved-run PDF."""
import json
import logging
import os
import azure.functions as func
from azure_at_rest.archive import identity
from azure_at_rest.hosting import execute, schedule

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
# Our handlers emit fixed safe envelopes. Keep SDK response diagnostics out of host logs.
for _logger in ('azure', 'msal'):
    logging.getLogger(_logger).setLevel(logging.CRITICAL)


@app.function_name(name='GenerateReport')
@app.route(route='reports', methods=['POST'], auth_level=func.AuthLevel.FUNCTION)
def generate_report(req: func.HttpRequest) -> func.HttpResponse:
    try:
        if len(req.get_body()) > 1024:
            raise ValueError()
        body = req.get_json()
        if not isinstance(body, dict) or set(body) != {'run_id'}:
            raise ValueError()
        run_id = identity(body['run_id'], 'r')
    except (ValueError, TypeError, KeyError):
        return func.HttpResponse('{"code":"exact_run_id_required"}', status_code=400, mimetype='application/json')
    try:
        result = execute('report', run_id=run_id)
        status = 201 if result['state'] == 'complete' else 503
    except RuntimeError as error:
        result = json.loads(str(error))  # execute emits only its fixed safe envelope.
        status = 409 if result['code'] == 'operation_busy' else 500
    return func.HttpResponse(json.dumps(result), status_code=status, mimetype='application/json',
                             headers={'Cache-Control': 'no-store'})


# No guessed default cadence. Unconfigured app indexes only the disabled report operation.
_schedule = schedule(os.environ)
if _schedule:
    @app.function_name(name='CollectEvidence')
    @app.timer_trigger(schedule=_schedule, arg_name='timer', run_on_startup=False, use_monitor=True)
    def collect_evidence(timer: func.TimerRequest) -> None:
        execute('collect')
