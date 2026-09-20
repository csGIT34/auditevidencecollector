"""Draft an approvable criteria file from a saved run.

A criterion says what an organization accepts. This program refuses to invent one, so
this drafter never writes an approved file: it produces a `draft` that leaves every
result UNKNOWN until a person reviews it and sets the status.

Two kinds of proposal are produced and they are labelled differently:

* `baseline` — a widely recognised hardening position for that exact property, proposed
  independently of what the tenant happens to do today.
* `observed` — no defensible baseline applies, so the value the tenant returned is
  offered as a starting point. Accepting one of these blesses the current state, which
  is exactly the decision a reviewer needs to make deliberately.

A proposal that the run already contradicts is kept, not softened; it will read FAIL and
that is the point.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cloud_governance import report_model  # noqa: E402
from cloud_governance.controls import CHECKS  # noqa: E402

# Hardening positions proposed independently of the tenant. Keyed by the predicate's
# exact property so a new service reusing the property inherits the same proposal.
BASELINE = {
    'httpsOnly': True,
    'supportsHttpsTrafficOnly': True,
    'allowBlobPublicAccess': False,
    'allowSharedKeyAccess': False,
    'disableLocalAuth': True,
    'features.disableLocalAuth': True,
    'DisableLocalAuth': True,
    'adminUserEnabled': False,
    'disableLocalAccounts': True,
    'enableRBAC': True,
    'aadProfile.enableAzureRBAC': True,
    'enableRbacAuthorization': True,
    'enablePurgeProtection': True,
    'enableSoftDelete': True,
    'configuration.ingress.allowInsecure': False,
    'remoteDebuggingEnabled': False,
    'allow': False,
    'platform.enabled': True,
    'globalValidation.requireAuthentication': True,
    'clientProtocol': 'Encrypted',
    'accessKeysAuthentication': 'Disabled',
    'highAvailability': 'Enabled',
    'apiServerAccessProfile.enablePrivateCluster': True,
    'securityProfile.uefiSettings.secureBootEnabled': True,
    'securityProfile.uefiSettings.vTpmEnabled': True,
    'osProfile.linuxConfiguration.disablePasswordAuthentication': True,
    'virtualMachineProfile.osProfile.linuxConfiguration.disablePasswordAuthentication': True,
}
# TLS minimums differ in spelling per provider; propose the strongest the enum offers.
TLS_PROPERTIES = ('minimumTlsVersion', 'minTlsVersion', 'scmMinTlsVersion', 'minimalTlsVersion')


# The accepted TLS floor, named explicitly. Ordering strings is not a security decision.
TLS_ACCEPTED = ('1.2', '1.3', 'TLS1_2', 'TLS1_3', 'Tls12', 'Tls13')


def proposal(check, observed):
    """Return (operator, value, origin) or None when nothing can be proposed."""
    if check.path in TLS_PROPERTIES and check.values:
        accepted = [value for value in check.values if value in TLS_ACCEPTED]
        if accepted:
            return 'one_of', accepted, 'baseline'
    if check.path in BASELINE:
        value = BASELINE[check.path]
        if not check.values or any(type(value) is type(v) and value == v for v in check.values):
            return 'equals', value, 'baseline'
    if observed is None:
        return None
    return 'equals', observed, 'observed'


def draft(report):
    checks, review = {}, []
    for row in report_model.configuration_results(report):
        check = CHECKS.get(row['check_id'])
        observation = row.get('observation') or {}
        observed = observation.get('value') if observation.get('state') in ('observed', 'partial') else None
        if check is None or row['check_id'] in checks:
            continue
        made = proposal(check, observed)
        if made is None:
            continue
        operator, value, origin = made
        checks[row['check_id']] = {'operator': operator, 'value': value}
        if origin == 'observed':
            review.append({'check': row['check_id'], 'property': check.path, 'proposed': value,
                           'why': 'No baseline position applies; this is the value the tenant returned. '
                                  'Approving it accepts the current configuration.'})
        elif observed is not None and (observed not in value if operator == 'one_of' else observed != value):
            review.append({'check': row['check_id'], 'property': check.path, 'proposed': value,
                           'observed': observed,
                           'why': 'The proposed baseline is stronger than the current configuration; '
                                  'this will read FAIL until the resource changes or the criterion does.'})
    return {'schema_version': '1.0', 'id': 'REPLACE-WITH-APPROVED-CRITERIA-ID', 'version': '1',
            'status': 'draft', 'checks': dict(sorted(checks.items()))}, review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Saved assessment JSON.')
    parser.add_argument('--output', type=Path, required=True, help='Draft criteria file to write; must not exist.')
    parser.add_argument('--review', type=Path, help='Optional review notes for the proposals needing a decision.')
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Refusing to overwrite an existing criteria file')
    report = json.loads(args.input.read_text(encoding='utf-8'))
    document, review = draft(report)
    args.output.write_text(json.dumps(document, indent=2, sort_keys=True) + '\n')
    if args.review:
        args.review.write_text(json.dumps(review, indent=2, sort_keys=True) + '\n')
    baseline = len(document['checks']) - sum(1 for r in review if 'observed' not in r)
    print('Drafted ' + str(len(document['checks'])) + ' criteria as status=draft; nothing passes until approved.')
    print('  proposals needing a decision: ' + str(len(review)))
    print('  of those, stronger than the current configuration: ' + str(sum(1 for r in review if 'observed' in r)))


if __name__ == '__main__':
    main()
