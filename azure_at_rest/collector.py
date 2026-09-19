"""GET-only public Azure ARM adapter and deterministic fixture adapter."""
import json
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, quote
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .catalog import RULES
from .controls import for_type, project as project_configuration, valid_value
from .safety import identity, label, now, project, subscription_id, resource_group_name

ARM = "https://management.azure.com"
INVENTORY_API = "2021-04-01"
SUBSCRIPTIONS_API = "2022-12-01"

class CollectionError(Exception):
    def __init__(self, code, status=None):
        self.code, self.status = code, status
        super().__init__(code)

def endpoint(path, api):
    return f'{ARM}{quote(path, safe="/()")}?api-version={api}'

def valid_url(url):
    if not isinstance(url, str):
        raise CollectionError("invalid_url")
    try:
        p = urlsplit(url)
        if (p.scheme != "https" or p.netloc.lower() != "management.azure.com" or p.fragment
                or not (p.path == "/subscriptions" or p.path.startswith("/subscriptions/")) or "\\" in url or any(c in url for c in "\r\n")):
            raise CollectionError("unsafe_url")
    except ValueError:
        raise CollectionError("invalid_url") from None
    return p

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CollectionError("redirect_rejected", code)

class AzureCliCredential:
    """Azure CLI credential for its current tenant/cloud. Token remains in memory."""
    def __init__(self):
        self.token, self.until = None, 0

    def get_token(self):
        if self.token and time.monotonic() < self.until:
            return self.token
        try:
            proc = subprocess.run(["az", "account", "get-access-token", "--resource", ARM + "/", "--output", "json"],
                                  capture_output=True, text=True, timeout=60, check=False)
            if proc.returncode:
                raise CollectionError("authentication_failed")
            data = json.loads(proc.stdout)
            token = data.get("accessToken")
            if not isinstance(token, str) or not token or any(c in token for c in "\r\n"):
                raise CollectionError("authentication_failed")
            remaining = float(data.get("expires_on", time.time() + 300)) - time.time() - 120
            self.token, self.until = token, time.monotonic() + max(0, min(remaining, 1800))
            return token
        except (OSError, subprocess.TimeoutExpired, ValueError, TypeError, AttributeError):
            raise CollectionError("authentication_failed") from None

class ArmTransport:
    validate_url = staticmethod(valid_url)
    def __init__(self, credential=None, retries=3, timeout=30, sleep=time.sleep, opener=None):
        self.credential = credential or AzureCliCredential()
        self.retries, self.timeout, self.sleep = retries, timeout, sleep
        self.opener = opener or build_opener(NoRedirect())

    def get(self, url):
        self.validate_url(url)  # Before obtaining or sending the bearer token.
        for attempt in range(self.retries + 1):
            req = Request(url, headers={"Authorization": "Bearer " + self.credential.get_token(),
                                       "Accept": "application/json"}, method="GET")
            try:
                with self.opener.open(req, timeout=self.timeout) as response:
                    payload = json.load(response)
                if not isinstance(payload, dict):
                    raise CollectionError("malformed_response")
                return payload
            except HTTPError as exc:
                status = exc.code
                retry_after = exc.headers.get("Retry-After", "") if exc.headers else ""
                exc.close()  # Never retain/log a provider's potentially sensitive error body.
                if status in (429, 500, 502, 503, 504) and attempt < self.retries:
                    wait = min(float(retry_after), 30) if retry_after.isdigit() else min(2 ** attempt, 30)
                    self.sleep(wait)
                    continue
                raise CollectionError("http_error", status) from None
            except (URLError, TimeoutError, OSError):
                if attempt < self.retries:
                    self.sleep(min(2 ** attempt, 30))
                    continue
                raise CollectionError("network_error") from None
            except (ValueError, UnicodeError):
                raise CollectionError("malformed_response") from None
        raise CollectionError("retry_exhausted")

class FixtureTransport:
    def __init__(self, responses):
        self.responses, self.calls = responses, []

    def get(self, url):
        valid_url(url)
        self.calls.append(url)
        if url not in self.responses:
            raise CollectionError("fixture_response_missing")
        value = self.responses[url]
        if isinstance(value, dict) and "fixture_error" in value:
            raise CollectionError("http_error", value["fixture_error"])
        return value

class Collector:
    def __init__(self, transport, max_pages=1000, mode="azure"):
        if max_pages < 1:
            raise ValueError("max_pages must be positive")
        self.transport, self.max_pages, self.mode = transport, max_pages, mode
        self.errors, self.resources = [], {}
        self.resource_group = None
        self.authorization_roles = {}

    def error(self, scope, operation, exc):
        error = {"scope": scope, "operation": operation, "code": exc.code,
                 "http_status": exc.status, "observed_at": now()}
        self.errors.append(error)
        return error

    def paged(self, url, scope, operation):
        items, seen, pages, complete = [], set(), 0, False
        initial_path = valid_url(url).path.lower()
        while url:
            try:
                if valid_url(url).path.lower() != initial_path:
                    raise CollectionError("pagination_scope_changed")
                if url in seen:
                    raise CollectionError("pagination_cycle")
                if pages >= self.max_pages:
                    raise CollectionError("pagination_limit")
                seen.add(url)
                page = self.transport.get(url)
                if not isinstance(page, dict) or not isinstance(page.get("value"), list):
                    raise CollectionError("malformed_page")
                items.extend(page["value"])
                pages += 1
                url = page.get("nextLink")
                if url is not None and (not isinstance(url, str) or not url):
                    raise CollectionError("invalid_next_link")
                if url is None:
                    complete = True
            except CollectionError as exc:
                self.error(scope, operation, exc)
                break
        return items, {"complete": complete, "pages": pages, "items_received": len(items)}

    def add_resource(self, raw, sid, parent=None, expected_type=None):
        meta = identity(raw)
        if (not meta or meta["subscription_id"] != sid.lower()
                or (self.resource_group and meta["resource_group"].lower() != self.resource_group.lower())
                or (expected_type and meta["type"].lower() != expected_type.lower())
                or (parent and meta["id"].lower().rsplit("/", 2)[0] != parent.lower())):
            self.error(parent or f"/subscriptions/{sid}", "inventory_identity", CollectionError("invalid_resource_identity"))
            return None
        key = meta["id"].lower()
        if key not in self.resources:
            self.resources[key] = {**meta, "location": label(raw.get("location", "global")),
                                   "kind": label(raw.get("kind", "unspecified")),
                                   "sku": label(raw.get("sku", {}).get("name", "unspecified")) if isinstance(raw.get("sku", {}), dict) else "[invalid]",
                                   "collected_at": now(), "collection_status": "inventory_only", "evidence": {},
                                   "children": {}, "errors": []}
        return self.resources[key]

    def hydrate(self, record):
        rule = RULES.get(record["type"].lower())
        checks = for_type(record["type"])
        if (not rule or rule.mode == "na") and not checks:
            return
        api = rule.api if rule and rule.api else checks[0].api
        rid = record["id"]
        record["api_version"] = api
        record["request_path"] = rid  # No URLs with opaque continuation tokens.
        try:
            raw = self.transport.get(endpoint(rid, api))
            verified = identity(raw)
            if (not verified or verified["id"].lower() != rid.lower()
                    or not isinstance(raw.get("properties"), dict)):
                raise CollectionError("invalid_detail_identity_or_properties")
            record["evidence"] = project(raw, rule) if rule else {}
            if checks:
                record["configuration"] = project_configuration(raw, record["type"])
            if isinstance(raw.get("sku"), dict) and "name" in raw["sku"]:
                record["sku"] = label(raw["sku"]["name"])
            record["collection_status"] = "ok"
        except CollectionError as exc:
            record["collection_status"] = "error"
            record["errors"].append(self.error(rid, "resource_get", exc))
        for suffix, supplemental_api in sorted({(c.suffix,c.api) for c in checks if c.suffix and c.operation == 'get'}):
            path = rid + suffix
            try:
                raw = self.transport.get(endpoint(path, supplemental_api))
                if (not isinstance(raw, dict) or not isinstance(raw.get('id'), str)
                        or raw['id'].lower() != path.lower() or not isinstance(raw.get('properties'), dict)):
                    raise CollectionError('invalid_detail_identity_or_properties')
                observations = project_configuration(raw, record['type'], suffix)
            except CollectionError as exc:
                observations = {c.id:{'state':'error','code':exc.code,'http_status':exc.status} for c in checks if c.suffix == suffix}
            record.setdefault('configuration', {}).update(observations)
        for check in (c for c in checks if c.operation == 'federation'):
            reader = Collector(self.transport,self.max_pages,self.mode)
            path = rid + check.suffix
            rows, listing = reader.paged(endpoint(path,check.api),rid,'configuration_federation')
            trusts = []; seen_trusts=set();malformed=False
            for row in rows:
                if not isinstance(row,dict) or not isinstance(row.get('id'),str) or row['id'].lower().rsplit('/',1)[0]!=path.lower() or row['id'].lower() in seen_trusts or not isinstance(row.get('properties'),dict):
                    malformed=True;continue
                seen_trusts.add(row['id'].lower())
                props=row['properties']
                trust={k:props.get(k) for k in ('issuer','subject','audiences')}
                if isinstance(trust['audiences'],list) and all(isinstance(a,str) for a in trust['audiences']):trust['audiences']=sorted(set(trust['audiences']))
                if not valid_value(check,[trust]):malformed=True;continue
                trusts.append(trust)
            trusts.sort(key=lambda r:json.dumps(r,sort_keys=True))
            record.setdefault('configuration',{})[check.id] = {'state':'observed' if listing['complete'] and not malformed else 'partial','value':trusts} if valid_value(check,trusts) else {'state':'invalid'}
            record['configuration'][check.id]['collection']={**listing,'malformed':malformed,'errors':[{k:e[k] for k in ('code','http_status')} for e in reader.errors]}
        for check in (c for c in checks if c.operation == 'diagnostics'):
            reader = Collector(self.transport, self.max_pages, self.mode)
            path = rid + check.suffix
            settings, listing = reader.paged(endpoint(path,check.api),rid,'configuration_diagnostics')
            categories = set()
            malformed = False
            seen_settings = set()
            for setting in settings:
                if (not isinstance(setting,dict) or not isinstance(setting.get('id'),str)
                        or setting['id'].lower().rsplit('/',1)[0] != path.lower()
                        or setting['id'].lower() in seen_settings or not isinstance(setting.get('properties'),dict)):
                    malformed = True
                    continue
                seen_settings.add(setting['id'].lower())
                logs = setting['properties'].get('logs')
                if not isinstance(logs,list):
                    malformed = True
                    continue
                for log in logs:
                    if not isinstance(log,dict) or type(log.get('enabled')) is not bool:
                        malformed = True
                        continue
                    if not log['enabled']:
                        continue
                    if bool(log.get('category')) == bool(log.get('categoryGroup')):
                        malformed = True
                        continue
                    name = ('category:'+str(log['category'])) if log.get('category') else ('group:'+str(log['categoryGroup']))
                    if not valid_value(check,[name]):
                        malformed = True
                    else:
                        categories.add(name)
            values = sorted(categories)
            if not valid_value(check,values):
                observation = {'state':'invalid'}
            else:
                observation = {'state':'observed' if listing['complete'] and not malformed else 'partial','value':values}
            observation['collection']={**listing,'malformed':malformed,'errors':[{k:e[k] for k in ('code','http_status')} for e in reader.errors]}
            record.setdefault('configuration',{})[check.id] = observation
        for check in (c for c in checks if c.operation == 'authorization'):
            from .authorization import collect as collect_authorization
            record.setdefault('configuration',{})[check.id] = collect_authorization(self.transport,rid,self.max_pages,self.authorization_roles)
        record["collected_at"] = now()
        # Enumerate known children even if the parent GET was denied.
        for suffix, child_type in (rule.children if rule else ()):
            rows, listing = self.paged(endpoint(rid + "/" + suffix, rule.api), rid, "list_" + suffix)
            children = []
            for row in rows:
                child = self.add_resource(row, record["subscription_id"], rid, child_type)
                if child:
                    children.append(child["id"])
                else:
                    listing["complete"] = False
            record["children"][suffix] = {**listing, "ids": sorted(set(children), key=str.lower)}
        if rule and rule.mode == "tde" and not (rule.key == "sql-tde" and record["name"].lower() == "master"):
            suffix = "/transparentDataEncryption/current"
            try:
                tde = self.transport.get(endpoint(rid + suffix, rule.api))
                if (not isinstance(tde, dict) or not isinstance(tde.get("id"), str)
                        or tde["id"].lower() != (rid + suffix).lower()
                        or not isinstance(tde.get("properties"), dict)):
                    raise CollectionError("invalid_tde_response")
                state = tde["properties"].get("state", tde["properties"].get("status"))
                record["evidence"]["tde.state"] = state if state in ("Enabled", "Disabled") else "[missing-or-unrecognized]"
                record["evidence"]["tde.observed_at"] = now()
            except CollectionError as exc:
                record["errors"].append(self.error(rid, "tde_get", exc))

    def collect(self, subscriptions=None, *, resource_group=None):
        if resource_group is not None and (not resource_group_name(resource_group) or not subscriptions or len(set(subscriptions)) != 1):
            raise ValueError("Resource-group scope requires one explicit subscription and a valid group")
        self.errors, self.resources = [], {}
        self.resource_group = resource_group
        started = now()
        inventory = {"subscription_discovery": {"complete": True, "mode": "explicit"}, "subscriptions": []}
        if subscriptions is None:
            rows, discovery = self.paged(endpoint("/subscriptions", SUBSCRIPTIONS_API), "/subscriptions", "list_subscriptions")
            inventory["subscription_discovery"] = {**discovery, "mode": "accessible_in_current_tenant"}
            subscriptions = []
            for row in rows:
                sid = subscription_id(row.get("subscriptionId")) if isinstance(row, dict) else None
                if sid:
                    subscriptions.append(sid)
                else:
                    inventory["subscription_discovery"]["complete"] = False
                    self.error("/subscriptions", "list_subscriptions", CollectionError("invalid_subscription_identity"))
        for sid in sorted(set(subscriptions)):
            if not subscription_id(sid):
                raise ValueError("subscription must be a UUID")
            scope = f"/subscriptions/{sid}"
            if resource_group:
                scope += "/resourceGroups/" + resource_group
            rows, listing = self.paged(endpoint(scope + "/resources", INVENTORY_API), scope, "list_resources")
            for row in rows:
                if not self.add_resource(row, sid):
                    listing["complete"] = False
            inventory["subscriptions"].append({"id": sid, **listing, **({"resource_group": resource_group} if resource_group else {})})
        processed = set()
        while pending := sorted(set(self.resources) - processed):
            for key in pending:
                processed.add(key)
                self.hydrate(self.resources[key])
        inventory["complete"] = (inventory["subscription_discovery"]["complete"]
                                 and bool(inventory["subscriptions"])
                                 and all(s["complete"] for s in inventory["subscriptions"]))
        return {"schema_version": "1.1", "mode": self.mode, "started_at": started, "completed_at": now(),
                "inventory": inventory, "resources": sorted(self.resources.values(), key=lambda r: r["id"].lower()),
                "errors": self.errors}
