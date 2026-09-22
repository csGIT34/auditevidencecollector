"""Azure Functions v2: scheduled collection and explicitly requested saved-run PDF."""
import json
import logging
import os
import azure.functions as func
from cloud_governance.archive import identity
from cloud_governance.hosting import ExecutionError, execute, schedule, enabled

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
# Our handlers emit fixed safe envelopes. Keep SDK response diagnostics out of host logs.
for _logger in ('azure', 'msal'):
    logging.getLogger(_logger).setLevel(logging.CRITICAL)


@app.function_name(name='GenerateEvidenceReport')
@app.route(route='evidence/reports', methods=['POST'], auth_level=func.AuthLevel.FUNCTION)
def generate_evidence_report(req: func.HttpRequest) -> func.HttpResponse:
    from cloud_governance.evidence_report import request_options
    from cloud_governance.wiz import decode
    try:
        raw = req.get_body()
        if len(raw) > 65536:
            raise ValueError()
        body = decode(raw)
        request_options(body)
        run_id = body.pop('run_id')
    except (ValueError, TypeError, KeyError, RecursionError):
        return func.HttpResponse('{"code":"invalid_evidence_report_request"}', status_code=400, mimetype='application/json')
    try:
        result = execute('evidence-report', run_id=run_id, selection=body)
        status = 201 if result['state'] == 'complete' else 503
    except ExecutionError as error:
        result = error.outcome
        status = 409 if result['code'] == 'operation_busy' else 500
    return func.HttpResponse(json.dumps(result), status_code=status, mimetype='application/json', headers={'Cache-Control': 'no-store'})


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
    except ExecutionError as error:
        result = error.outcome
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


if enabled(os.environ,'operational'):
    @app.function_name(name='ImportOperationalEvidence')
    @app.route(route='operational/import',methods=['POST'],auth_level=func.AuthLevel.FUNCTION)
    def import_operational_evidence(req: func.HttpRequest) -> func.HttpResponse:
        from cloud_governance.operational import MAX_BYTES
        from cloud_governance.archive import encode
        from cloud_governance.wiz import decode
        try:
            raw=req.get_body()
            if len(raw)>MAX_BYTES+4096:raise ValueError()
            body=decode(raw)
            if not isinstance(body,dict) or set(body)!={'run_id','document','as_of','max_age_hours'}:raise ValueError()
            run_id=identity(body['run_id'],'r')
            document=encode(body['document'])
            if len(document)>MAX_BYTES:raise ValueError()
        except (ValueError,TypeError,KeyError,RecursionError):
            return func.HttpResponse('{"code":"invalid_operational_request"}',status_code=400,mimetype='application/json')
        try:
            result=execute('operational-import',run_id=run_id,document=document,as_of=body['as_of'],max_age_hours=body['max_age_hours'])
            status=201 if result['state']=='complete' else 503
        except ExecutionError as error:
            result=error.outcome;status=409 if result['code']=='operation_busy' else 500
        return func.HttpResponse(json.dumps(result),status_code=status,mimetype='application/json',headers={'Cache-Control':'no-store'})

    @app.function_name(name='GenerateOperationalReport')
    @app.route(route='operational/reports',methods=['POST'],auth_level=func.AuthLevel.FUNCTION)
    def generate_operational_report(req: func.HttpRequest) -> func.HttpResponse:
        from cloud_governance.wiz import decode
        try:
            if len(req.get_body())>1024:raise ValueError()
            body=decode(req.get_body())
            if not isinstance(body,dict) or set(body)!={'evidence_id'}:raise ValueError()
            evidence_id=identity(body['evidence_id'],'o')
        except (ValueError,TypeError,KeyError):
            return func.HttpResponse('{"code":"exact_evidence_id_required"}',status_code=400,mimetype='application/json')
        try:
            result=execute('operational-report',evidence_id=evidence_id)
            status=201 if result['state']=='complete' else 503
        except ExecutionError as error:
            result=error.outcome;status=409 if result['code']=='operation_busy' else 500
        return func.HttpResponse(json.dumps(result),status_code=status,mimetype='application/json',headers={'Cache-Control':'no-store'})


if enabled(os.environ,'workload'):
    @app.function_name(name='ImportKubernetesEvidence')
    @app.route(route='workloads/kubernetes/import',methods=['POST'],auth_level=func.AuthLevel.FUNCTION)
    def import_kubernetes_evidence(req: func.HttpRequest) -> func.HttpResponse:
        from cloud_governance.kubernetes_evidence import MAX_BYTES
        from cloud_governance.archive import encode
        from cloud_governance.wiz import decode
        try:
            raw=req.get_body()
            if len(raw)>MAX_BYTES+4096:raise ValueError()
            body=decode(raw)
            if not isinstance(body,dict) or set(body)!={'run_id','document','criteria','as_of','max_age_seconds'}:raise ValueError()
            run_id=identity(body['run_id'],'r');document=encode(body['document'])
            if len(document)>MAX_BYTES:raise ValueError()
        except (ValueError,TypeError,KeyError,RecursionError):
            return func.HttpResponse('{"code":"invalid_kubernetes_request"}',status_code=400,mimetype='application/json')
        try:
            result=execute('workload-import',run_id=run_id,document=document,criteria=body['criteria'],as_of=body['as_of'],max_age_seconds=body['max_age_seconds'])
            status=201 if result['state']=='complete' else 503
        except ExecutionError as error:
            result=error.outcome;status=409 if result['code']=='operation_busy' else 500
        return func.HttpResponse(json.dumps(result),status_code=status,mimetype='application/json',headers={'Cache-Control':'no-store'})

    @app.function_name(name='GenerateKubernetesReport')
    @app.route(route='workloads/kubernetes/reports',methods=['POST'],auth_level=func.AuthLevel.FUNCTION)
    def generate_kubernetes_report(req: func.HttpRequest) -> func.HttpResponse:
        from cloud_governance.wiz import decode
        try:
            if len(req.get_body())>1024:raise ValueError()
            body=decode(req.get_body())
            if not isinstance(body,dict) or set(body)!={'evidence_id'}:raise ValueError()
            evidence_id=identity(body['evidence_id'],'k')
        except (ValueError,TypeError,KeyError):
            return func.HttpResponse('{"code":"exact_kubernetes_id_required"}',status_code=400,mimetype='application/json')
        try:
            result=execute('workload-report',evidence_id=evidence_id)
            status=201 if result['state']=='complete' else 503
        except ExecutionError as error:
            result=error.outcome;status=409 if result['code']=='operation_busy' else 500
        return func.HttpResponse(json.dumps(result),status_code=status,mimetype='application/json',headers={'Cache-Control':'no-store'})


if enabled(os.environ,'kubernetes_collection'):
    @app.function_name(name='CollectKubernetesEvidence')
    @app.route(route='workloads/kubernetes/collect',methods=['POST'],auth_level=func.AuthLevel.FUNCTION)
    def collect_kubernetes_evidence(req: func.HttpRequest) -> func.HttpResponse:
        from cloud_governance.wiz import decode
        try:
            if len(req.get_body())>1024:raise ValueError()
            body=decode(req.get_body())
            if not isinstance(body,dict) or set(body)!={'run_id'}:raise ValueError()
            run_id=identity(body['run_id'],'r')
        except (ValueError,TypeError,KeyError):
            return func.HttpResponse('{"code":"exact_run_id_required"}',status_code=400,mimetype='application/json')
        try:
            result=execute('workload-collect',run_id=run_id)
            status=201 if result['state']=='complete' else 503
        except ExecutionError as error:
            result=error.outcome;status=409 if result['code']=='operation_busy' else 500
        return func.HttpResponse(json.dumps(result),status_code=status,mimetype='application/json',headers={'Cache-Control':'no-store'})

if enabled(os.environ,'guest'):
    @app.function_name(name='ImportGuestEvidence')
    @app.route(route='guests/import',methods=['POST'],auth_level=func.AuthLevel.FUNCTION)
    def import_guest_evidence(req: func.HttpRequest) -> func.HttpResponse:
        from cloud_governance.guest_evidence import MAX_BYTES
        from cloud_governance.archive import encode
        from cloud_governance.wiz import decode
        try:
            raw=req.get_body()
            if len(raw)>MAX_BYTES+4096:raise ValueError()
            body=decode(raw)
            if not isinstance(body,dict) or set(body)!={'run_id','document','criteria','as_of','max_age_seconds'}:raise ValueError()
            run_id=identity(body['run_id'],'r');document=encode(body['document'])
            if len(document)>MAX_BYTES:raise ValueError()
        except (ValueError,TypeError,KeyError,RecursionError):
            return func.HttpResponse('{"code":"invalid_guest_request"}',status_code=400,mimetype='application/json')
        try:
            result=execute('guest-import',run_id=run_id,document=document,criteria=body['criteria'],as_of=body['as_of'],max_age_seconds=body['max_age_seconds'])
            status=201 if result['state']=='complete' else 503
        except ExecutionError as error:
            result=error.outcome;status=409 if result['code']=='operation_busy' else 500
        return func.HttpResponse(json.dumps(result),status_code=status,mimetype='application/json',headers={'Cache-Control':'no-store'})

    @app.function_name(name='GenerateGuestReport')
    @app.route(route='guests/reports',methods=['POST'],auth_level=func.AuthLevel.FUNCTION)
    def generate_guest_report(req: func.HttpRequest) -> func.HttpResponse:
        from cloud_governance.wiz import decode
        try:
            if len(req.get_body())>1024:raise ValueError()
            body=decode(req.get_body())
            if not isinstance(body,dict) or set(body)!={'evidence_id'}:raise ValueError()
            evidence_id=identity(body['evidence_id'],'g')
        except (ValueError,TypeError,KeyError):
            return func.HttpResponse('{"code":"exact_guest_id_required"}',status_code=400,mimetype='application/json')
        try:
            result=execute('guest-report',evidence_id=evidence_id)
            status=201 if result['state']=='complete' else 503
        except ExecutionError as error:
            result=error.outcome;status=409 if result['code']=='operation_busy' else 500
        return func.HttpResponse(json.dumps(result),status_code=status,mimetype='application/json',headers={'Cache-Control':'no-store'})
