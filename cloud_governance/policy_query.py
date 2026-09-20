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
from urllib.request import Request

from .collector import MAX_RESPONSE_BYTES, CollectionError, NoRedirect, bounded_payload
from .safety import subscription_id

API_VERSION = '2019-10-01'
HOST = 'https://management.azure.com'
# The only query this transport may issue.
PATH = '/providers/Microsoft.PolicyInsights/policyStates/latest/queryResults'
MAX_RECORDS = 5000


def query_url(subscription, top):
    """Build the one permitted query URL, or refuse."""
    # A non-string subscription must fail here, not later during URL construction.
    if not isinstance(subscription, str) or subscription_id(subscription) != subscription:
        raise ValueError('Policy queries require an exact subscription UUID')
    if type(top) is not int or not 1 <= top <= MAX_RECORDS:
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

    def query(self, subscription, top=MAX_RECORDS):
        url = query_url(subscription, top)
        # An empty body: the URL carries the whole query, so no caller input is transmitted.
        request = Request(url, data=b'', method='POST',
                          headers={'Authorization': 'Bearer ' + self.credential.get_token(),
                                   'Accept': 'application/json', 'Content-Type': 'application/json',
                                   'Content-Length': '0'})
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                raw = response.read(self.max_response_bytes + 1)
                if len(raw) > self.max_response_bytes:
                    raise CollectionError('response_size_limit')
                payload = bounded_payload(raw)
        except CollectionError:
            raise
        except OSError:
            raise CollectionError('network_error') from None
        except (ValueError, TypeError):
            raise CollectionError('malformed_response') from None
        if not isinstance(payload, dict) or not isinstance(payload.get('value'), list):
            raise CollectionError('malformed_response')
        if len(payload['value']) > MAX_RECORDS:
            raise CollectionError('response_size_limit')
        return payload['value']


class FixturePolicyTransport:
    """Deterministic offline transport; the same projection path as a live query."""

    def __init__(self, records_by_subscription):
        self.records = records_by_subscription
        self.requested = []

    def query(self, subscription, top=MAX_RECORDS):
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
    if not isinstance(records, list) or len(records) > MAX_RECORDS:
        raise ValueError('Invalid policy export records')
    return records
