import copy
import json
import unittest
from unittest.mock import Mock, patch
from azure_at_rest.graph import GraphCollector, FixtureGraphTransport, GraphTransport, valid_url, validate_identity_evidence
from azure_at_rest.collector import CollectionError
from azure_at_rest.snapshot import validate_snapshot
from azure_at_rest.workflow import assess_snapshot
from azure_at_rest.archive import save_run,load_run
from tests.test_archive import MemoryStore
from tests.test_controls import fixture as arm_fixture,collect

TENANT='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
APP='bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'
CLIENT='cccccccc-cccc-cccc-cccc-cccccccccccc'
SP='dddddddd-dddd-dddd-dddd-dddddddddddd'
OWNER='eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee'
ROLE='ffffffff-ffff-ffff-ffff-ffffffffffff'
BASE='https://graph.microsoft.com/v1.0/'


def fixture():
    return {
      BASE+'servicePrincipals/'+SP+'/oauth2PermissionGrants?$select=id,clientId,resourceId,consentType,principalId,scope':{'value':[]},
      BASE+'organization?$select=id':{'value':[{'id':TENANT}]},
      BASE+'applications?$select=id,appId,signInAudience,passwordCredentials,keyCredentials':{'value':[{'id':APP,'appId':CLIENT,'signInAudience':'AzureADMyOrg','passwordCredentials':[{'keyId':ROLE,'startDateTime':'2020-01-01T00:00:00Z','endDateTime':'2021-01-01T00:00:00Z','secretText':'DO-NOT-SAVE-GRAPH-SECRET','hint':'DO-NOT-SAVE-GRAPH-SECRET'}],'keyCredentials':[]}]},
      BASE+'servicePrincipals?$select=id,appId,accountEnabled':{'value':[{'id':SP,'appId':CLIENT,'accountEnabled':True,'displayName':'DO-NOT-SAVE-GRAPH-SECRET'}]},
      BASE+'applications/'+APP+'/federatedIdentityCredentials?$select=id,issuer,subject,audiences':{'value':[]},
      BASE+'applications/'+APP+'/owners?$select=id':{'value':[{'id':OWNER,'mail':'DO-NOT-SAVE-GRAPH-SECRET'}]},
      BASE+'servicePrincipals/'+SP+'/appRoleAssignments?$select=id,principalId,resourceId,appRoleId':{'value':[{'id':'opaque_assignment-ID','principalId':SP,'resourceId':OWNER,'appRoleId':ROLE}]}}


def evidence(responses=None):
    return GraphCollector(FixtureGraphTransport(fixture() if responses is None else responses),TENANT).collect()


class GraphTests(unittest.TestCase):
    def test_distinct_identity_owner_grants_expiry_and_no_values(self):
        result=evidence();validate_identity_evidence(result)
        self.assertTrue(result['complete']);self.assertTrue(result['verified_tenant'])
        self.assertEqual(2,len(result['resources']))
        app,sp=result['resources']
        self.assertEqual(APP,app['object_id']);self.assertEqual(CLIENT,app['app_id'])
        self.assertEqual(SP,sp['object_id']);self.assertEqual(CLIENT,sp['app_id'])
        self.assertEqual(1,app['configuration']['APPREG-expired-credentials']['value'])
        self.assertEqual(1,sp['configuration']['APPREG-role-grants']['value'])
        self.assertNotIn('DO-NOT-SAVE-GRAPH-SECRET',json.dumps(result))

    def test_wrong_or_denied_tenant_stops_before_identity_population(self):
        for org in ({'value':[{'id':OWNER}]},{'fixture_error':403},{'value':[{'id':42}]}):
            responses=fixture();responses[BASE+'organization?$select=id']=org
            transport=FixtureGraphTransport(responses);result=GraphCollector(transport,TENANT).collect()
            validate_identity_evidence(result)
            self.assertFalse(result['complete']);self.assertEqual([],result['resources'])
            self.assertEqual(1,len(transport.calls))

    def test_owners_partial_does_not_report_count_as_complete(self):
        responses=fixture();responses[BASE+'applications/'+APP+'/owners?$select=id']={'fixture_error':403}
        result=evidence(responses);validate_identity_evidence(result)
        self.assertFalse(result['complete'])
        self.assertEqual('partial',result['resources'][0]['configuration']['APPREG-owner-count']['state'])

    def test_pagination_traversal_and_scope_attack(self):
        url=BASE+'applications?$select=id,appId,signInAudience,passwordCredentials,keyCredentials'
        responses=fixture();original=responses[url]['value'];responses[url]={'value':[],'@odata.nextLink':BASE+'applications?$skiptoken=opaque'}
        responses[BASE+'applications?$skiptoken=opaque']={'value':original}
        result=evidence(responses);self.assertTrue(result['complete'])
        self.assertEqual(2,result['listings']['applications']['pages'])
        responses[url]['@odata.nextLink']='https://evil.example/v1.0/applications'
        transport=FixtureGraphTransport(responses);result=GraphCollector(transport,TENANT).collect()
        self.assertFalse(result['complete']);self.assertFalse(any('evil.example' in u for u in transport.calls))

    def test_hostile_origins_rejected_before_token(self):
        credential=Mock();transport=GraphTransport(credential=credential)
        for url in ['http://graph.microsoft.com/v1.0/applications','https://graph.microsoft.com.evil/v1.0/applications','https://graph.microsoft.com/beta/applications',BASE+'applications/../users',BASE+'users',BASE+'applications#token']:
            with self.assertRaises(CollectionError):transport.get(url)
        credential.get_token.assert_not_called()

    def test_invalid_and_duplicate_identities_mark_incomplete(self):
        responses=fixture();url=BASE+'applications?$select=id,appId,signInAudience,passwordCredentials,keyCredentials'
        responses[url]['value']*=2
        result=evidence(responses);validate_identity_evidence(result)
        self.assertFalse(result['complete']);self.assertEqual(2,len(result['resources']))
        responses=fixture();url=BASE+'servicePrincipals/'+SP+'/appRoleAssignments?$select=id,principalId,resourceId,appRoleId'
        responses[url]['value'][0]['principalId']=42
        result=evidence(responses);validate_identity_evidence(result);self.assertFalse(result['complete'])

    def test_bad_credential_metadata_is_partial_without_retaining_payload(self):
        responses=fixture();url=BASE+'applications?$select=id,appId,signInAudience,passwordCredentials,keyCredentials'
        responses[url]['value'][0]['passwordCredentials'][0]['endDateTime']='bad-secret'
        result=evidence(responses);validate_identity_evidence(result)
        self.assertEqual('partial',result['resources'][0]['configuration']['APPREG-expired-credentials']['state'])
        self.assertNotIn('bad-secret',json.dumps(result))

    def test_replay_rejects_extra_secret_and_wrong_identity(self):
        original=evidence()
        for mutation in (lambda r:r['resources'][0]['metadata'].update(secret='no'),lambda r:r['resources'][0].update(object_id=OWNER),lambda r:r.update(complete=False)):
            changed=copy.deepcopy(original);mutation(changed)
            with self.assertRaises(ValueError):validate_identity_evidence(changed)

    def test_unified_assessment_archive_and_historical_replay(self):
        responses,policy=arm_fixture();snapshot=collect(responses);snapshot['identity_evidence']=evidence()
        validate_snapshot(snapshot)
        policy['checks'].update({'APPREG-approved-owners':{'operator':'equals','value':[OWNER]},'APPREG-approved-role-grants':{'operator':'equals','value':[{'principalId':SP,'resourceId':OWNER,'appRoleId':ROLE}]},'APPREG-federation-trust':{'operator':'equals','value':[]},'APPREG-audience':{'operator':'equals','value':'AzureADMyOrg'},'APPREG-owner-count':{'operator':'at_least','value':1},'APPREG-expired-credentials':{'operator':'equals','value':0},'APPREG-sp-enabled':{'operator':'equals','value':True},'APPREG-role-grants':{'operator':'equals','value':1}})
        report=assess_snapshot(snapshot,criteria=policy)
        checks={r['check_id']:r for r in report['configuration_assessment']['results']}
        self.assertEqual('FAIL',checks['APPREG-expired-credentials']['result'])
        self.assertEqual('PASS',checks['APPREG-owner-count']['result'])
        self.assertEqual('FAILURES_FOUND',report['overall_summary']['conclusion'])
        store=MemoryStore();manifest=save_run(store,snapshot,report)
        with patch('azure_at_rest.controls.evaluate',side_effect=AssertionError('reassess')):
            self.assertEqual(report,load_run(store,manifest['run_id'])['assessment'])

    def test_exact_owners_and_role_tuples_are_checked_independently_of_count(self):
        responses,policy=arm_fixture();snapshot=collect(responses);snapshot['identity_evidence']=evidence()
        policy['checks'].update({'APPREG-approved-owners':{'operator':'equals','value':[ROLE]},'APPREG-approved-role-grants':{'operator':'equals','value':[{'principalId':SP,'resourceId':APP,'appRoleId':ROLE}]}})
        rows={r['check_id']:r for r in assess_snapshot(snapshot,criteria=policy)['configuration_assessment']['results']}
        self.assertEqual('FAIL',rows['APPREG-approved-owners']['result'])
        self.assertEqual('FAIL',rows['APPREG-approved-role-grants']['result'])

    def test_application_federation_incomplete_and_untrusted_subject(self):
        responses=fixture();url=BASE+'applications/'+APP+'/federatedIdentityCredentials?$select=id,issuer,subject,audiences'
        responses[url]={'value':[{'id':ROLE,'issuer':'https://issuer.example.invalid','subject':'repo:example/project:ref:refs/heads/main','audiences':['api://AzureADTokenExchange']}]}
        good=evidence(responses);validate_identity_evidence(good)
        self.assertEqual('observed',good['resources'][0]['configuration']['APPREG-federation-trust']['state'])
        responses[url]['value'][0]['issuer']='https://issuer.example.invalid?secret=NEVER'
        bad=evidence(responses);validate_identity_evidence(bad)
        self.assertFalse(bad['complete']);self.assertNotIn('NEVER',json.dumps(bad))

    def test_graph_sdk_audience_and_token_errors_are_sanitized(self):
        from azure_at_rest.graph import GraphCredential
        import time
        sdk=Mock();sdk.get_token.return_value=Mock(token='fixture-token',expires_on=time.time()+60)
        self.assertEqual('fixture-token',GraphCredential(sdk).get_token())
        sdk.get_token.assert_called_once_with('https://graph.microsoft.com/.default')
        sdk.get_token.side_effect=RuntimeError('SECRET SDK BODY')
        with self.assertRaises(CollectionError) as caught:GraphCredential(sdk).get_token()
        self.assertEqual('authentication_failed',str(caught.exception))


class GraphCompletenessTests(unittest.TestCase):
    def test_missing_population_and_false_complete_children_rejected(self):
        valid = evidence()
        for name in ('applications','servicePrincipals','applications/'+APP+'/owners'):
            altered = copy.deepcopy(valid)
            del altered['listings'][name]
            with self.assertRaises(ValueError):
                validate_identity_evidence(altered)
        altered = copy.deepcopy(valid)
        altered['listings']['applications/'+APP+'/owners']['complete'] = False
        altered['complete'] = False
        with self.assertRaises(ValueError):
            validate_identity_evidence(altered)
        altered = copy.deepcopy(valid)
        altered['resources'].pop()
        with self.assertRaises(ValueError):
            validate_identity_evidence(altered)


class DelegatedConsentTests(unittest.TestCase):
    def test_scope_claims_tenant_wide_and_per_user_consent(self):
        responses=fixture();url=BASE+'servicePrincipals/'+SP+'/oauth2PermissionGrants?$select=id,clientId,resourceId,consentType,principalId,scope'
        responses[url]={'value':[{'id':'grant-one','clientId':SP,'resourceId':APP,'consentType':'AllPrincipals','principalId':None,'scope':'User.Read Mail.Read User.Read','description':'DO-NOT-SAVE-CONSENT'},
                                 {'id':'grant-two','clientId':SP,'resourceId':APP,'consentType':'Principal','principalId':OWNER,'scope':'User.Read'}]}
        result=evidence(responses);validate_identity_evidence(result)
        observed=result['resources'][1]['configuration']['APPREG-delegated-grants']
        self.assertEqual('observed',observed['state'])
        self.assertEqual(2,len(observed['value']))
        self.assertNotIn('DO-NOT-SAVE-CONSENT',json.dumps(result))
        self.assertTrue(any(row['scopes']==['Mail.Read','User.Read'] for row in observed['value']))

    def test_denied_wrong_client_and_partial_consent_cannot_pass(self):
        url=BASE+'servicePrincipals/'+SP+'/oauth2PermissionGrants?$select=id,clientId,resourceId,consentType,principalId,scope'
        for response in ({'fixture_error':403},{'value':[{'id':'bad','clientId':APP,'resourceId':APP,'consentType':'AllPrincipals','principalId':None,'scope':'User.Read'}]},
                         {'value':[],'@odata.nextLink':url+'&$skiptoken=missing'}):
            responses=fixture();responses[url]=response
            result=evidence(responses);validate_identity_evidence(result)
            self.assertEqual('partial',result['resources'][1]['configuration']['APPREG-delegated-grants']['state'])
            self.assertFalse(result['complete'])
