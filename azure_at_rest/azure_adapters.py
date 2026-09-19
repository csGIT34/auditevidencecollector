"""Optional Azure SDK boundary. Never provisions resources or changes policy."""
import hashlib
import re
import time
from uuid import uuid4
from .collector import ARM, ArmTransport, CollectionError, endpoint, SUBSCRIPTIONS_API
from .safety import subscription_id
from .storage import parts


def account_url(value):
    if not isinstance(value, str) or not re.fullmatch(r'https://[a-z0-9]{3,24}\.blob\.core\.windows\.net', value):
        raise ValueError('invalid_public_blob_endpoint')
    return value


def container_name(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,61}[a-z0-9]', value) or '--' in value:
        raise ValueError('invalid_container_name')
    return value


def token_credential(client_id, tenant_id, *, development=False):
    """Explicit UAMI in production; explicitly opted-in, tenant-bound CLI for dev."""
    if not subscription_id(tenant_id) or (not development and not subscription_id(client_id)):
        raise ValueError('invalid_identity_configuration')
    from azure.identity import AzureCliCredential, ManagedIdentityCredential
    if development:
        return AzureCliCredential(tenant_id=tenant_id, process_timeout=20)
    return ManagedIdentityCredential(client_id=client_id, connection_timeout=5, read_timeout=10, retry_total=2)


class ArmCredential:
    def __init__(self, credential):
        self.credential = credential

    def get_token(self):
        try:
            # SDK credentials own expiry/cache/refresh; never decode a JWT ourselves.
            token = self.credential.get_token(ARM + '/.default')
            if not isinstance(token.token, str) or not token.token or any(c in token.token for c in '\r\n') or token.expires_on <= time.time():
                raise ValueError('invalid_token')
            return token.token
        except Exception:
            raise CollectionError('authentication_failed') from None


class BudgetArmTransport(ArmTransport):
    def __init__(self, credential, deadline, retries=2):
        super().__init__(ArmCredential(credential), retries=retries, sleep=deadline.sleep)
        self.deadline = deadline

    def get(self, url):
        self.deadline.check()
        self.timeout = min(30, self.deadline.remaining())
        result = super().get(url)
        self.deadline.check()
        return result


def verify_tenant(transport, subscriptions, tenant_id):
    """ARM validates the bearer token; compare authoritative subscription metadata."""
    if not subscriptions or not subscription_id(tenant_id):
        raise ValueError('explicit_scope_required')
    for sid in subscriptions:
        if not subscription_id(sid):
            raise ValueError('invalid_subscription')
        data = transport.get(endpoint('/subscriptions/' + sid, SUBSCRIPTIONS_API))
        if (str(data.get('subscriptionId', '')).lower() != sid.lower()
                or str(data.get('tenantId', '')).lower() != tenant_id.lower() or data.get('state') != 'Enabled'):
            raise CollectionError('tenant_or_subscription_mismatch')


class BlobStore:
    """Create-only block blobs with bounded retries and same-attempt reconciliation."""
    def __init__(self, url, container, credential, prefix='', *, retries=2, deadline=None, client=None, sleep=time.sleep):
        self.url, self.container = account_url(url), container_name(container)
        self.prefix = '/'.join(parts(prefix)) + '/' if prefix else ''
        if type(retries) is not int or not 0 <= retries <= 3:
            raise ValueError('invalid_retry_count')
        self.retries, self.deadline, self.sleep = retries, deadline, sleep
        if client is None:
            from azure.storage.blob import ContainerClient
            client = ContainerClient(url, container, credential=credential, retry_total=0,
                                     connection_timeout=5, read_timeout=20, logging_enable=False)
        self.client = client

    def _name(self, key):
        name = self.prefix + '/'.join(parts(key))
        if len(name) > 1024:
            raise ValueError('blob_name_too_long')
        return name

    def _check(self):
        if self.deadline:
            self.deadline.check()

    @staticmethod
    def _transient(error):
        from azure.core.exceptions import ServiceRequestError, ServiceResponseError
        return isinstance(error, (ServiceRequestError, ServiceResponseError)) or getattr(error, 'status_code', None) in (408, 429, 500, 502, 503, 504)

    @staticmethod
    def _raise(error):
        status = getattr(error, 'status_code', None)
        from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError, ClientAuthenticationError
        if isinstance(error, ResourceNotFoundError) or status == 404:
            raise FileNotFoundError('blob_not_found') from None
        if isinstance(error, ResourceExistsError) or status in (409, 412):
            raise FileExistsError('blob_exists') from None
        if isinstance(error, ClientAuthenticationError) or status in (401, 403):
            raise PermissionError('blob_access_denied') from None
        raise OSError('blob_operation_failed') from None

    def _wait(self, attempt):
        delay = min(2 ** attempt, 4)
        if self.deadline:
            self.deadline.sleep(delay)
        else:
            self.sleep(delay)

    def _call(self, operation):
        from azure.core.exceptions import AzureError
        for attempt in range(self.retries + 1):
            self._check()
            try:
                result = operation()
                self._check()
                return result
            except AzureError as error:
                if self._transient(error) and attempt < self.retries:
                    self._wait(attempt)
                else:
                    self._raise(error)

    def read(self, key):
        blob = self.client.get_blob_client(self._name(key))
        return self._call(lambda: blob.download_blob(max_concurrency=1, timeout=30, logging_enable=False,
                                                     progress_hook=lambda *_: self._check()).readall())

    def put_new(self, key, data):
        if not isinstance(data, bytes):
            raise TypeError('Object payload must be bytes')
        from azure.core import MatchConditions
        from azure.core.exceptions import AzureError, ResourceNotFoundError
        blob = self.client.get_blob_client(self._name(key))
        marker = uuid4().hex
        checksum = hashlib.sha256(data).hexdigest()
        for attempt in range(self.retries + 1):
            self._check()
            try:
                blob.upload_blob(data, blob_type='BlockBlob', overwrite=False, match_condition=MatchConditions.IfMissing,
                                 metadata={'cg_write_id': marker, 'cg_sha256': checksum}, max_concurrency=1,
                                 timeout=30, logging_enable=False, progress_hook=lambda *_: self._check())
                self._check()
                return
            except AzureError as error:
                # A server commit can outlive a lost response. Only adopt this exact
                # in-flight write, never an unrelated existing object with equal bytes.
                ambiguous = self._transient(error) or getattr(error, 'status_code', None) in (409, 412)
                if ambiguous:
                    self._check()
                    try:
                        properties = blob.get_blob_properties(timeout=30, logging_enable=False)
                        metadata = properties.metadata or {}
                        if metadata.get('cg_write_id') == marker:
                            actual = blob.download_blob(max_concurrency=1, timeout=30, logging_enable=False).readall()
                            if metadata.get('cg_sha256') != checksum or actual != data:
                                raise OSError('blob_reconciliation_mismatch')
                            self._check()
                            return
                    except ResourceNotFoundError:
                        pass
                    except AzureError:
                        # Original transient error may still be retried, condition intact.
                        pass
                if self._transient(error) and attempt < self.retries:
                    self._wait(attempt)
                else:
                    self._raise(error)

    def keys(self, prefix):
        logical = '/'.join(parts(prefix.rstrip('/'))) + '/'
        physical = self.prefix + logical
        def listing():
            found = []
            for page in self.client.list_blobs(name_starts_with=physical, timeout=30, logging_enable=False).by_page():
                self._check()
                for blob in page:
                    name = blob.name
                    if not name.startswith(physical):
                        raise ValueError('blob_listing_outside_prefix')
                    key = name[len(self.prefix):]
                    parts(key)
                    found.append(key)
            return sorted(set(found))
        return self._call(listing)

    def close(self):
        self.client.close()
