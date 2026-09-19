import copy
import json
import unittest
from azure_at_rest.backup_population import collect,valid_population
from azure_at_rest.collector import FixtureTransport,endpoint
from azure_at_rest.controls import CHECKS
from tests.helpers import resource

SOURCE=resource('Microsoft.Compute/disks','protected')['id']


def item(vault,kind):
    policy=vault+'/backupPolicies/approved'
    if kind=='dp_population':
        return {'id':vault+'/backupInstances/protected','properties':{'dataSourceInfo':{'resourceID':SOURCE},'policyInfo':{'policyId':policy},
                'currentProtectionState':'ProtectionConfigured','protectionStatus':{'status':'ProtectionConfigured'},'datasourceAuthCredentials':{'secret':'DO-NOT-SAVE-BACKUP-SECRET'}}}
    return {'id':vault+'/backupFabrics/Azure/protectionContainers/IaasVMContainer;rg;vm/protectedItems/VM;rg;vm',
            'properties':{'sourceResourceId':resource('Microsoft.Compute/virtualMachines','protected')['id'],'policyId':policy,'protectionState':'Protected','protectionStatus':'Healthy',
                          'friendlyName':'DO-NOT-SAVE-BACKUP-SECRET'}}


def normalized(raw,kind):
    p=raw['properties']
    if kind=='dp_population':return {'item_id':raw['id'].lower(),'source_id':p['dataSourceInfo']['resourceID'].lower(),
        'policy_id':p['policyInfo']['policyId'].lower(),'state':p['currentProtectionState'],'status':p['protectionStatus']['status']}
    return {'item_id':raw['id'].lower(),'source_id':p['sourceResourceId'].lower(),'policy_id':p['policyId'].lower(),'state':p['protectionState'],'status':p['protectionStatus']}

class BackupPopulationTests(unittest.TestCase):
    def cases(self):
        for cid in ('BV-backup-population','BV-recovery-population'):
            check=CHECKS[cid];vault=resource(check.resource_type,'vault')['id'];yield check,vault,item(vault,check.kind)

    def test_both_vault_families_keep_source_policy_and_status_without_secrets(self):
        for check,vault,raw in self.cases():
            result=collect(FixtureTransport({endpoint(vault+check.suffix,check.api):{'value':[raw]}}),vault,check,10)
            self.assertEqual('observed',result['state']);self.assertEqual([normalized(raw,check.kind)],result['value'])
            self.assertNotIn('DO-NOT-SAVE-BACKUP-SECRET',json.dumps(result))

    def test_denied_partial_duplicate_wrong_vault_and_missing_state_are_incomplete(self):
        for check,vault,raw in self.cases():
            url=endpoint(vault+check.suffix,check.api)
            wrong=copy.deepcopy(raw);wrong['id']=wrong['id'].replace('/vault/','/wrong/')
            missing=copy.deepcopy(raw);missing['properties'].pop('currentProtectionState' if check.kind=='dp_population' else 'protectionState')
            for response in ({'fixture_error':403},{'value':[raw,raw]},{'value':[wrong]},{'value':[missing]}, {'value':[raw],'nextLink':url+'&$skiptoken=missing'}):
                result=collect(FixtureTransport({url:response}),vault,check,10)
                self.assertEqual('partial',result['state'])

    def test_missing_or_unhealthy_protected_source_fails_expected_population(self):
        from tests.test_controls import fixture,collect as collect_arm
        from azure_at_rest.workflow import assess_snapshot
        responses,policy=fixture()
        for check,vault,raw in self.cases():
            target_url=next(url for url in responses if url.endswith(check.suffix+'?api-version='+check.api))
            responses[target_url]={'value':[]}
        snapshot=collect_arm(responses)
        results=assess_snapshot(snapshot,criteria=policy)['configuration_assessment']['results']
        self.assertTrue(all(row['result']=='FAIL' for row in results if row['check_id'] in ('BV-backup-population','BV-recovery-population')))
        responses,policy=fixture()
        url=next(url for url in responses if '/backupInstances?' in url)
        responses[url]['value'][0]['properties']['currentProtectionState']='ProtectionError'
        results=assess_snapshot(collect_arm(responses),criteria=policy)['configuration_assessment']['results']
        self.assertEqual('FAIL',next(row for row in results if row['check_id']=='BV-backup-population')['result'])
