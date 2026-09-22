"""Allowlisted evidence projection. Never serialize whole ARM responses."""
from datetime import date, datetime, timezone
import re
from urllib.parse import urlsplit
from uuid import UUID

MISSING = object()
INVALID = "[invalid-or-unrecognized]"

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def get(obj, path, default=None):
    for part in path.split("."):
        if not isinstance(obj, dict) or part not in obj:
            return default
        obj = obj[part]
    return obj

def subscription_id(value):
    try:
        return str(UUID(value)) if isinstance(value, str) else None
    except (ValueError, AttributeError):
        return None

def resource_group_name(value):
    """Portable explicit scope; reject URL delimiters and ambiguous names."""
    return value if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_().-]{1,90}", value) and not value.endswith('.') else None


def resource_group_id(value):
    if not isinstance(value, str):
        return None
    bits = value.split('/')
    return value if len(bits) == 5 and bits[1].lower() == 'subscriptions' and subscription_id(bits[2]) and bits[3].lower() == 'resourcegroups' and resource_group_name(bits[4]) else None


def identity(raw):
    """Verify type against the last ARM provider segment; extension resources allowed."""
    if not isinstance(raw, dict):
        return None
    rid, rt = raw.get("id"), raw.get("type")
    if not isinstance(rid, str) or not isinstance(rt, str) or len(rid) > 2048:
        return None
    if not re.fullmatch(r"/[A-Za-z0-9_.() -]+(?:/[A-Za-z0-9_.() -]+)+", rid):
        return None
    parts = rid.strip("/").split("/")
    if any(x in (".", "..", "") for x in parts):
        return None
    if len(parts) < 6 or parts[0].lower() != "subscriptions" or not subscription_id(parts[1]):
        return None
    grouped = parts[2].lower() == "resourcegroups"
    providers = [i for i, p in enumerate(parts) if p.lower() == "providers"]
    if not providers or providers[0] != (4 if grouped else 2):
        return None
    p = providers[-1]
    rest = parts[p + 2:]
    if len(rest) < 2 or len(rest) % 2:
        return None
    derived = parts[p + 1] + "/" + "/".join(rest[::2])
    if derived.lower() != rt.lower():
        return None
    return {"id": rid, "type": derived, "name": rest[-1], "subscription_id": parts[1].lower(), "resource_group": parts[3] if grouped else ""}

def resource_id(value):
    if not isinstance(value, str):
        return None
    p = value.strip("/").split("/")
    try:
        i = max(i for i, part in enumerate(p) if part.lower() == "providers")
        rt = p[i + 1] + "/" + "/".join(p[i + 2::2])
    except (ValueError, IndexError):
        return None
    return value if identity({"id": value, "type": rt}) else None

def label(value):
    return value if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_. ,()-]{1,128}", value) else INVALID

def storage_name(url):
    if not isinstance(url, str):
        return None
    try:
        host = urlsplit(url).hostname or ""
    except ValueError:
        return None
    match = re.fullmatch(r"([a-z0-9]{3,24})\.(?:blob|dfs|file)\.core\.windows\.net", host)
    return match.group(1) if match else None

ENUMS = {
    "encryption.keySource": {"Microsoft.Storage", "Microsoft.Keyvault", "Microsoft.KeyVault"},
    "encryption.type": {"EncryptionAtRestWithPlatformKey", "EncryptionAtRestWithCustomerKey", "EncryptionAtRestWithPlatformAndCustomerKeys"},
    "dataEncryption.type": {"SystemManaged", "AzureKeyVault"},
    "encryption.status": {"enabled", "disabled", "Enabled", "Disabled"},
    "encryption.infrastructureEncryption": {"Enabled", "Disabled"},
    "osDiskType": {"Managed", "Ephemeral"},
    "captureDescription.destination.name": {"EventHubArchive.AzureBlockBlob", "EventHubArchive.AzureDataLake"},
    "sku.name": {"Basic", "Standard", "Premium"},
    "sku.family": {"C", "P"},
}

def project(raw, rule):
    props = raw.get("properties", {})
    evidence = {}
    for path in rule.paths:
        value = get(props, path, MISSING)
        if value is MISSING:
            continue
        if path in ENUMS:
            value = value if isinstance(value, str) and value in ENUMS[path] else INVALID
        elif path.lower().endswith("id"):
            value = resource_id(value) or INVALID
        elif path == "defaultDataLakeStorage.accountUrl":
            value = storage_name(value) or INVALID
        elif path == "nodeResourceGroup":
            value = label(value)
        elif path.startswith("redisConfiguration."):
            value = value if isinstance(value, str) and value in {"true", "false"} else INVALID
        elif path == "osDiskSizeGB":
            value = value if type(value) is int and 0 <= value <= 65536 else INVALID
        elif path == "sku.capacity":
            value = value if type(value) is int and 0 <= value <= 64 else INVALID
        else:
            value = value if type(value) is bool else INVALID
        evidence[path] = value
    state = props.get("provisioningState")
    if state is not None:
        evidence["provisioningState"] = state if isinstance(state, str) and state.lower() in {
            "succeeded", "failed", "canceled", "cancelled", "creating", "updating", "deleting", "accepted", "running"
        } else INVALID
    # Only IDs and disk metadata, never VHD URLs (which may include SAS) or app settings.
    refs = []
    for prefix in ("storageProfile", "virtualMachineProfile.storageProfile"):
        profile = get(props, prefix, {})
        if not isinstance(profile, dict):
            continue
        disks = [profile.get("osDisk", {})] + (profile.get("dataDisks", []) if isinstance(profile.get("dataDisks", []), list) else [])
        for disk in disks:
            if not isinstance(disk, dict):
                continue
            rid = get(disk, "managedDisk.id")
            if rid is not None:
                refs.append({"relation": "managed_disk", "id": resource_id(rid) or INVALID})
            if get(disk, "vhd.uri") is not None:
                evidence["unmanaged_disk_present"] = True
    if refs:
        evidence["references"] = refs
    volumes = get(props, "template.volumes")
    if isinstance(volumes, list):
        evidence["volumes"] = [{k: label(v[k]) for k in ("name", "storageName", "storageType") if k in v}
                               for v in volumes if isinstance(v, dict)]
    pools = props.get("agentPoolProfiles")
    if isinstance(pools, list):
        evidence["agent_pools"] = [{k: (v[k] if type(v[k]) is bool else label(v[k]))
                                    for k in ("name", "osDiskType", "enableEncryptionAtHost") if k in v}
                                   for v in pools if isinstance(v, dict)]
    return evidence


def valid_api_version(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}(?:-preview)?", value):
        return False
    try:
        date.fromisoformat(value[:10])
        return True
    except ValueError:
        return False
