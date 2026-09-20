import copy
import json
import unittest
from cloud_governance.collector import Collector, FixtureTransport, endpoint
from cloud_governance.controls import CHECKS
from cloud_governance.diagnostic_routes import project, valid_routes
from cloud_governance.workflow import assess_snapshot
from tests.helpers import resource, SUB
from tests.test_controls import fixture

PATH=resource('Microsoft.KeyVault/vaults','vault')['id']+'/providers/Microsoft.Insights/diagnosticSettings'
WORKSPACE=resource('Microsoft.OperationalInsights/workspaces','logs')['id']
OTHER=resource('Microsoft.OperationalInsights/workspaces','other')['id']
LISTING={'complete':True,'pages':1,'items_received':1}

def setting(name='audit',workspace=WORKSPACE,category='AuditEvent'):
    return {'id':PATH+'/'+name,'properties':{'logs':[{'category':category,'enabled':True}],
                'workspaceId':workspace,'secretCanary':'DO-NOT-SAVE-ROUTE-SECRET'}}

class DiagnosticRouteTests(unittest.TestCase):
    def test_destination_is_bound_to_its_own_enabled_categories(self):
        result=project([setting(),setting('other',OTHER,'Different')],PATH,{**LISTING,'items_received':2},[])
        self.assertEqual('observed',result['state']);self.assertTrue(valid_routes(result['value']))
        self.assertEqual(['category:AuditEvent'],result['value'][0]['logs'])
        self.assertEqual(WORKSPACE.lower(),result['value'][0]['workspace_id'])
        self.assertEqual(OTHER.lower(),result['value'][1]['workspace_id'])
        self.assertNotIn('DO-NOT-SAVE-ROUTE-SECRET',json.dumps(result))

    def test_invalid_missing_destination_and_partial_listing_cannot_pass(self):
        for workspace in (None,False,{},'https://evil.example?secret=bad',resource('Microsoft.Storage/storageAccounts','wrong-type')['id']):
            result=project([setting(workspace=workspace)],PATH,LISTING,[])
            self.assertEqual('partial',result['state'])
            self.assertEqual([],result['value'])
        result=project([setting()],PATH,{**LISTING,'complete':False},[])
        self.assertEqual('partial',result['state']);self.assertEqual(1,len(result['value']))

    def test_empty_disabled_duplicate_and_wrong_setting_identity(self):
        disabled=setting();disabled['properties']['logs'][0]['enabled']=False
        self.assertEqual([],project([disabled],PATH,LISTING,[])['value'])
        self.assertEqual('observed',project([],PATH,{**LISTING,'items_received':0},[])['state'])
        self.assertEqual('partial',project([setting(),setting()],PATH,LISTING,[])['state'])
        wrong=setting();wrong['id']=WORKSPACE+'/providers/Microsoft.Insights/diagnosticSettings/other'
        self.assertEqual('partial',project([wrong],PATH,LISTING,[])['state'])

    def test_eventhub_storage_partner_ids_preserved_without_keys(self):
        value=setting();props=value['properties'];props['workspaceId']=''
        props.update(eventHubAuthorizationRuleId=resource('Microsoft.EventHub/namespaces/authorizationRules','events/send')['id'],
                     eventHubName='audit',storageAccountId=resource('Microsoft.Storage/storageAccounts','logs')['id'],
                     marketplacePartnerId=resource('Microsoft.Datadog/monitors','partner')['id'])
        result=project([value],PATH,LISTING,[])
        self.assertEqual('observed',result['state'])
        self.assertEqual('audit',result['value'][0]['eventhub_name'])

    def test_real_collector_reuses_list_and_rejects_wrong_destination(self):
        responses,policy=fixture();transport=FixtureTransport(responses)
        snapshot=Collector(transport,mode='offline_fixture').collect([SUB])
        row=next(r for r in snapshot['resources'] if r['type']=='microsoft.keyvault/vaults')
        check=CHECKS['KV-diagnostic-routes'];url=endpoint(row['id']+check.suffix,check.api)
        self.assertEqual(1,transport.calls.count(url))
        result=next(r for r in assess_snapshot(snapshot,criteria=policy)['configuration_assessment']['results'] if r['check_id']==check.id)
        self.assertEqual('PASS',result['result'])
        responses[url]['value'][0]['properties']['workspaceId']=OTHER
        changed=Collector(FixtureTransport(responses),mode='offline_fixture').collect([SUB])
        result=next(r for r in assess_snapshot(changed,criteria=policy)['configuration_assessment']['results'] if r['check_id']==check.id)
        self.assertEqual('FAIL',result['result'])
