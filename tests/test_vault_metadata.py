import copy
import json
import unittest
from unittest.mock import Mock,patch
from cloud_governance.vault_metadata import API,collect,assess,valid_url,valid_objects,Credential,VaultTransport
from cloud_governance.collector import CollectionError
from cloud_governance.controls import CHECKS
from cloud_governance.archive import save_run,load_run,publish_pdf
from cloud_governance.workflow import assess_snapshot,Deadline
from tests.test_controls import fixture,collect as run_collection
from tests.test_archive import MemoryStore

BASE='https://example.vault.azure.net'
RID='/subscriptions/11111111-1111-1111-1111-111111111111/resourcegroups/example/providers/microsoft.keyvault/vaults/example'
AS_OF='2026-09-20T02:00:00+00:00'
CRITERION={'enabled_only':True,'require_expiration':True,'min_remaining_seconds':3600}

def item(kind='secrets',name='example'):
    return {'kid' if kind=='keys' else 'id':BASE+'/'+kind+'/'+name,'attributes':{'enabled':True,'created':1700000000,'updated':1700000000,'exp':2000000000},'value':'SECRET-CANARY','tags':{'owner':'SECRET-CANARY'},'cer':'SECRET-CANARY'}

class VaultMetadataTests(unittest.TestCase):
    def collect(self,pages,kind='secrets',max_pages=10,parent=None):
        transport=Mock();transport.get.side_effect=pages;arm=Mock();arm.vault_transport_factory=Mock(return_value=transport)
        result=collect(arm,RID,CHECKS['KV-'+kind+'-lifecycle'],max_pages,parent or {'properties':{'vaultUri':BASE+'/'}})
        return result,transport

    def test_all_families_exclude_values_tags_and_certificate_material(self):
        for kind in ('keys','secrets','certificates'):
            result,transport=self.collect([{'value':[item(kind)]}],kind)
            self.assertEqual('observed',result['state']);self.assertTrue(valid_objects(result['value'],kind))
            self.assertNotIn('SECRET-CANARY',json.dumps(result));self.assertEqual(1,transport.get.call_count)
            self.assertEqual('PASS',assess(result['value'],CRITERION,AS_OF)[0])

    def test_only_same_vault_base_list_paths_allowed(self):
        for url in (BASE+'/secrets/example?api-version='+API,BASE+'/keys/example/versions?api-version='+API,'https://other.vault.azure.net/secrets?api-version='+API,BASE+'/secrets?api-version=7.2',BASE+'/secrets?api-version='+API+'&api-version='+API,BASE+'/secrets?api-version='+API+'#fragment'):
            with self.assertRaises(CollectionError):valid_url(url,BASE,'secrets')
        valid_url(BASE+':443/secrets?api-version='+API+'&$skiptoken=opaque%2Btoken',BASE,'secrets')

    def test_pagination_denial_cycles_and_changed_scope_remain_incomplete(self):
        url=BASE+'/secrets?api-version='+API+'&maxresults=25'
        for pages,state in [([{'value':[item()],'nextLink':url}],'pagination_cycle'),
            ([{'value':[item()],'nextLink':BASE+'/keys?api-version='+API}],'unsafe_url'),
            ([CollectionError('http_error',403)],'http_error')]:
            result,_=self.collect(pages);self.assertEqual('partial',result['state']);self.assertEqual(state,result['collection']['errors'][0]['code'])
        result,_=self.collect([{'value':[item()],'nextLink':url+'&$skiptoken=next'}],max_pages=1)
        self.assertEqual('pagination_limit',result['collection']['errors'][0]['code'])

    def test_duplicate_malformed_and_wrong_vault_objects_cannot_pass(self):
        for obj in ({**item(),'id':BASE+'/secrets/example/version'}, {**item(),'id':'https://other.vault.azure.net/secrets/example'}, {**item(),'attributes':{'enabled':'true'}}, {**item(),'attributes':{'exp':True}}):
            result,_=self.collect([{'value':[obj]}]);self.assertEqual('partial',result['state']);self.assertTrue(result['collection']['malformed'])
        result,_=self.collect([{'value':[item(),item()]}]);self.assertEqual('partial',result['state'])

    def test_expiration_missing_disabled_unknown_and_future_are_distinct(self):
        result,_=self.collect([{'value':[item()]}]);value=result['value'][0]
        for changes,expected in [({'exp':None},'FAIL'),({'exp':1700000000},'FAIL'),({'enabled':False},'UNKNOWN'),({'enabled':None},'UNKNOWN'),({'updated':2000000000},'UNKNOWN')]:
            self.assertEqual(expected,assess([{**value,**changes}],CRITERION,AS_OF)[0])
        self.assertEqual('UNKNOWN',assess([],CRITERION,AS_OF)[0])
        mixed=[{**value,'exp':None},{**value,'object_id':BASE+'/secrets/other','enabled':None}]
        decision,_,details=assess(mixed,CRITERION,AS_OF);self.assertEqual('FAIL',decision);self.assertTrue(details['coverage_incomplete'])

    def test_opt_in_and_arm_endpoint_binding(self):
        self.assertEqual({'state':'missing'},collect(object(),RID,CHECKS['KV-secrets-lifecycle'],10,{}))
        result,transport=self.collect([],parent={'properties':{'vaultUri':'https://other.vault.azure.net/'}})
        self.assertEqual('invalid',result['state']);transport.get.assert_not_called()
        result,transport=self.collect([],parent={'properties':{'vaultUri':BASE,'provisioningState':'Failed'}})
        self.assertEqual('missing',result['state']);transport.get.assert_not_called()

    def test_frozen_lifecycle_results_preserve_failure_and_unknown_in_pdf_archive(self):
        responses,policy=fixture()
        url=next(k for k in responses if '.vault.azure.net/secrets?' in k)
        first=responses[url]['value'][0];first['attributes']['exp']=None
        second=copy.deepcopy(first);second['id']+='-other';second['attributes']['enabled']=None
        responses[url]['value'].append(second)
        policy['checks']['KV-secrets-lifecycle']={'operator':'lifecycle','value':CRITERION}
        snapshot=run_collection(responses);report=assess_snapshot(snapshot,criteria=policy)
        self.assertTrue(report['overall_summary']['coverage_incomplete'])
        row=next(r for r in report['configuration_assessment']['results'] if r['check_id']=='KV-secrets-lifecycle')
        self.assertEqual('FAIL',row['result']);self.assertTrue(row['lifecycle_evaluation']['coverage_incomplete'])
        store=MemoryStore();run=save_run(store,snapshot,report)['run_id'];before=dict(store.objects)
        with patch('cloud_governance.vault_metadata.assess',side_effect=AssertionError('No reassessment')):
            self.assertEqual(report,load_run(store,run)['assessment']);publish_pdf(store,run)
        for key,data in before.items():self.assertEqual(data,store.objects[key])

    def test_transport_validates_before_token_and_uses_vault_audience(self):
        import time
        credential=Mock();credential.get_token.return_value=Mock(token='TOKEN',expires_on=time.time()+100)
        self.assertEqual('TOKEN',Credential(credential).get_token());credential.get_token.assert_called_once_with('https://vault.azure.net/.default')
        credential.reset_mock();transport=VaultTransport(BASE,credential,Deadline(30))
        with self.assertRaises(CollectionError):transport.get(BASE+'/secrets/example?api-version='+API)
        credential.get_token.assert_not_called()

    def test_host_factory_creates_only_opted_in_vault_transport_and_closes_identity(self):
        from cloud_governance.hosting import Settings,resources,ConfigurationError
        from tests.test_hosting import environment
        for flag in ('false','true'):
            settings=Settings.parse({**environment(),'CG_VAULT_METADATA_ENABLED':flag});credential=Mock();store=Mock()
            with patch('cloud_governance.hosting.token_credential',return_value=credential),patch('cloud_governance.hosting.BlobStore',return_value=store):
                with resources(settings,Deadline(30),'collect') as (_,arm):
                    self.assertEqual(flag=='true',hasattr(arm,'vault_transport_factory'))
                    if flag=='true':self.assertIsInstance(arm.vault_transport_factory(BASE),VaultTransport)
            credential.close.assert_called_once();store.close.assert_called_once()
        with self.assertRaises(ConfigurationError):Settings.parse({**environment(),'CG_VAULT_METADATA_ENABLED':'yes'})
