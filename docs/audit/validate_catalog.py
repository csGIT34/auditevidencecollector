"""Offline reference/coverage validation for the research catalog (not tenant tests)."""
from pathlib import Path
import json
import re


def main():
    root = Path(__file__).resolve().parent
    data = json.loads((root / 'catalog.json').read_text())
    index = json.loads((root / 'nist-control-index.json').read_text())
    expected = ['Event Hubs', 'AKS', 'App registrations', 'Event Grid',
                'Storage Accounts', 'Cosmos DB', 'Managed Redis', 'Function Apps',
                'Key Vaults', 'PostgreSQL Flexible Servers', 'Azure Container Apps',
                'user-assigned managed identities', 'private endpoints',
                'Azure Container Registries', 'backup vaults', 'App Configuration',
                'Application Insights', 'Managed Grafana', 'Managed Prometheus',
                'Log Analytics Workspaces', 'Virtual Machines',
                'Virtual Machine Scale Sets', 'Automation accounts']
    assert [s['name'] for s in data['services']] == expected
    assert set(data['domains']) == set('INRTKLCVBODG')
    assert len(data['families']) == 20
    assert len({f['id'] for f in data['families']}) == 20
    assert data['nist_source'] == index['source']
    checks = {c['id']: c for c in data['checks']}
    assert len(checks) == len(data['checks'])
    assert all(c in checks for c in data['shared_checks'])
    service_ids = {s['id'] for s in data['services']}
    for c in checks.values():
        assert c['service_id'] in service_ids | {'shared'}
        assert c['domain'] in data['domains']
        assert c['organization_parameters'] in data['organization_parameters']
        for field in ['title', 'evidence', 'acceptance_candidate', 'owner',
                      'automation', 'maturity', 'gap', 'nist', 'sources']:
            assert c[field], (c['id'], field)
        assert c['maturity'].startswith(('DISCOVERY_ONLY', 'Existing encryption only:'))
        assert all(p in data['permission_profiles'] for p in c['permission_profiles'])
        assert all(s in data['sources'] for s in c['sources'])
        for m in c['nist']:
            control = index['controls'][m['control']]
            assert m['title'] == control['title']
            assert m['rationale'] and m['claim_limit']
            objective_ids = {o['id'] for o in control['assessment_objectives']}
            method_ids = {o['id'] for o in control['assessment_methods']}
            assert m['assessment_objectives'] and set(m['assessment_objectives']) <= objective_ids
            assert m['assessment_methods'] and set(m['assessment_methods']) <= method_ids
            assert c['id'] in control['mapped_checks']
    cells = 0
    for s in data['services']:
        assert set(s['domain_coverage']) == set(data['domains'])
        assert all(c in checks and checks[c]['service_id'] == s['id'] for c in s['checks'])
        assert all(r in data['sources'] for r in s['sources'])
        for domain, cov in s['domain_coverage'].items():
            cells += 1
            assert cov['status'] in {'direct', 'shared', 'inherited', 'not_resource_local'}
            assert cov['rationale'] and cov['check_refs']
            assert all(c in checks for c in cov['check_refs'])
            if cov['status'] != 'not_resource_local':
                assert any(checks[c]['domain'] == domain for c in cov['check_refs'])
    assert cells == 276
    for f in data['families']:
        assert f['review'] and f['responsibility'] and f['decision']
        for cid in f['candidate_controls'] + [f['policy_procedure_control']]:
            assert cid in index['controls']
        assert all(c in checks for c in f['shared_check_refs'])
    for source in data['sources'].values():
        assert source['url'].startswith('https://') and source['reviewed_on']
    for path in root.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            if not target.startswith(('https://', '#')):
                assert (path.parent / target.split('#')[0]).exists(), (path, target)
    matrix = (root / 'SERVICE_MATRIX.md').read_text()
    assert all(f'**{c}**' in matrix for s in data['services'] for c in s['checks'])
    assert all(f'. {s["name"]} (' in matrix for s in data['services'])
    print(f'Validated {len(data["services"])} services, {cells} domain cells, '
          f'{len(data["families"])} families, {len(checks)} proposed checks, '
          f'{len(index["controls"])} NIST references and {len(data["sources"])} sources.')
    print('This validates research structure and references, not tenant control effectiveness.')


if __name__ == '__main__':
    main()
