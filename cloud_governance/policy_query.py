"""Read-only query transport for Azure Policy compliance.

Azure exposes compliance state only through a query API. `policyStates/latest/queryResults`
is registered for POST and rejects GET outright, because the query specification travels in
a request body. The call changes nothing — it returns records — but the verb is POST, so it
does not belong in the GET-only resource collector.

This module keeps that widening as narrow as it can be checked:

* one allowlisted path suffix, matched after the subscription scope is validated;
* one pinned API version;
* an empty request body, so nothing a caller supplies reaches the service;
* the same response bounding, duplicate-member rejection and depth limit as resource reads.

Anything else — another path, another method, another API version, a caller-supplied body —
is refused before a token is obtained.
"""
import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request

from .collector import MAX_RESPONSE_BYTES, CollectionError, NoRedirect, bounded_payload
from .safety import subscription_id

API_VERSION = '2019-10-01'
HOST = 'https://management.azure.com'
# The only query this transport may issue.
PATH = '/providers/Microsoft.PolicyInsights/policyStates/latest/queryResults'
MAX_RECORDS = 5000
# Policy Insights truncates to $top and returns no continuation link, so a full page is
# indistinguishable from a truncated one. Asking for one more than the limit makes the
# difference observable, the same way a bounded response read does.
QUERY_TOP = MAX_RECORDS + 1
# The assignment and its initiative are ordinary resource reads, so they stay GET.
ASSIGNMENT_API = '2023-04-01'
SET_DEFINITION_API = '2023-04-01'


# Each policy read is authorized at a different scope, so a denial is only actionable if
# the run says which one was refused.
ASSIGNMENT_READ = 'assignment'
INITIATIVE_READ = 'initiative'
STATES_READ = 'policy_states'


def denial(error, read):
    """Label a failure with the read that produced it."""
    error.read = read
    return error


def query_url(subscription, top):
    """Build the one permitted query URL, or refuse."""
    # A non-string subscription must fail here, not later during URL construction.
    if not isinstance(subscription, str) or subscription_id(subscription) != subscription:
        raise ValueError('Policy queries require an exact subscription UUID')
    if type(top) is not int or not 1 <= top <= QUERY_TOP:
        raise ValueError('Invalid policy record limit')
    return (HOST + '/subscriptions/' + subscription + PATH + '?api-version=' + API_VERSION
            + '&$top=' + str(top))


class PolicyQueryTransport:
    """POST to the single allowlisted query endpoint. No other request is possible."""

    def __init__(self, credential, timeout=30, opener=None, *, max_response_bytes=MAX_RESPONSE_BYTES):
        if type(max_response_bytes) is not int or not 1 <= max_response_bytes <= MAX_RESPONSE_BYTES:
            raise ValueError('Invalid response byte limit')
        from urllib.request import build_opener
        self.credential = credential
        self.timeout = timeout
        self.max_response_bytes = max_response_bytes
        self.opener = opener or build_opener(NoRedirect())
        self._allowed = set()

    def allow(self, *urls):
        """Record the exact metadata URLs this run may read, built by the helpers below."""
        self._allowed.update(urls)
        return self

    def _send(self, request, read):
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                raw = response.read(self.max_response_bytes + 1)
                if len(raw) > self.max_response_bytes:
                    raise CollectionError('response_size_limit')
                return bounded_payload(raw)
        except CollectionError:
            raise
        except HTTPError as exc:
            # HTTPError subclasses OSError, so a denial must be caught first or it reads
            # as a network fault and hides the status an operator needs.
            status = exc.code if isinstance(getattr(exc, 'code', None), int) else None
            raise denial(CollectionError('http_error', status), read) from None
        except (URLError, TimeoutError, OSError):
            raise denial(CollectionError('network_error'), read) from None
        except (ValueError, TypeError):
            raise denial(CollectionError('malformed_response'), read) from None

    def read(self, url, read=ASSIGNMENT_READ):
        """GET one of the two allowlisted policy metadata URLs."""
        if url not in self._allowed:
            raise ValueError('Policy reads are restricted to the assignment and its initiative')
        return self._send(Request(url, method='GET', headers={
            'Authorization': 'Bearer ' + self.credential.get_token(), 'Accept': 'application/json'}), read)

    def query(self, subscription, top=QUERY_TOP):
        url = query_url(subscription, top)
        # An empty body: the URL carries the whole query, so no caller input is transmitted.
        request = Request(url, data=b'', method='POST',
                          headers={'Authorization': 'Bearer ' + self.credential.get_token(),
                                   'Accept': 'application/json', 'Content-Type': 'application/json',
                                   'Content-Length': '0'})
        payload = self._send(request, STATES_READ)
        if not isinstance(payload, dict) or not isinstance(payload.get('value'), list):
            raise CollectionError('malformed_response')
        if len(payload['value']) > QUERY_TOP:
            raise CollectionError('response_size_limit')
        return payload['value']


class FixturePolicyTransport:
    """Deterministic offline transport; the same projection path as a live query."""

    def __init__(self, records_by_subscription, metadata=None):
        self.records = records_by_subscription
        self.metadata = metadata or {}
        self.requested = []

    def allow(self, *urls):
        return self

    def read(self, url, read=ASSIGNMENT_READ):
        document = self.metadata.get(url)
        if document is None:
            raise denial(CollectionError('fixture_response_missing'), read)
        return document

    def query(self, subscription, top=QUERY_TOP):
        query_url(subscription, top)  # Enforce the same argument contract offline.
        self.requested.append(subscription)
        value = self.records.get(subscription)
        if value is None:
            raise CollectionError('fixture_response_missing')
        if isinstance(value, dict) and 'fixture_error' in value:
            raise CollectionError('http_error')
        return list(value)[:top]


def decode_records(text):
    """Accept an operator-supplied export for tenants that cannot query directly."""
    if not isinstance(text, str) or len(text.encode()) > 8 * 1024 * 1024:
        raise ValueError('Invalid policy export')
    document = json.loads(text)
    if not isinstance(document, dict) or document.get('schema_version') != '1.0':
        raise ValueError('Expected policy export schema_version 1.0')
    records = document.get('records')
    if not isinstance(records, list) or len(records) > QUERY_TOP:
        raise ValueError('Invalid policy export records')
    return records


def assignment_url(subscription, name):
    """GET URL for one policy assignment at subscription scope."""
    if not isinstance(subscription, str) or subscription_id(subscription) != subscription:
        raise ValueError('Policy reads require an exact subscription UUID')
    if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_.\-]{1,128}', name):
        raise ValueError('Invalid policy assignment name')
    return (HOST + '/subscriptions/' + subscription + '/providers/Microsoft.Authorization/policyAssignments/'
            + name + '?api-version=' + ASSIGNMENT_API)


def set_definition_url(definition_id):
    """GET URL for the built-in or custom initiative an assignment names."""
    if not isinstance(definition_id, str) or not re.fullmatch(
            r'(/subscriptions/[0-9a-f-]{36})?/providers/Microsoft\.Authorization/policySetDefinitions/[A-Za-z0-9_.\-]{1,128}',
            definition_id, re.IGNORECASE):
        raise ValueError('Invalid policy set definition reference')
    return HOST + definition_id + '?api-version=' + SET_DEFINITION_API


def fetch_mapping(transport, subscription, assignment_name):
    """Read the assignment and its initiative so control mapping is frozen with the run."""
    url = assignment_url(subscription, assignment_name)
    transport.allow(url)
    assignment = transport.read(url, ASSIGNMENT_READ)
    if not isinstance(assignment, dict) or not isinstance(assignment.get('properties'), dict):
        raise CollectionError('malformed_response')
    definition_id = assignment['properties'].get('policyDefinitionId')
    definition_url = set_definition_url(definition_id)
    transport.allow(definition_url)
    policy_set = transport.read(definition_url, INITIATIVE_READ)
    if not isinstance(policy_set, dict) or not isinstance(policy_set.get('properties'), dict):
        raise CollectionError('malformed_response')
    return policy_set['properties']
