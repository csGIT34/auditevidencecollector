import copy
import json
import unittest
from azure_at_rest.authorization import API, SUFFIX, collect, valid_grants
from azure_at_rest.collector import FixtureTransport, endpoint
from azure_at_rest.controls import CHECKS, validate_policy
from azure_at_rest.workflow import assess_snapshot
from azure_at_rest.archive import save_run, load_run
from tests.test_archive import MemoryStore
from tests.helpers import SUB, resource

RID=resource('Microsoft.Storage/storageAccounts','store')['id']
SCOPE='/subscriptions/'+SUB
ASSIGNMENT='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
PRINCIPAL='bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'
ROLE='cccccccc-cccc-cccc-cccc-cccccccccccc'
ROLE_ID=SCOPE+'/providers/microsoft.authorization/roledefinitions/'+ROLE
LOOKUP=RID+'/providers/Microsoft.Authorization/roleDefinitions/'+ROLE
PERMISSIONS=[{'actions':['*'],'notActions':['microsoft.authorization/*/write'],'dataActions':[],'notDataActions':[]}]


def grant():
    return {'assignment_id':SCOPE+'/providers/microsoft.authorization/roleassignments/'+ASSIGNMENT,
            'principal_id':PRINCIPAL,'principal_type':'ServicePrincipal','scope':SCOPE,'role_id':ROLE_ID,
            'role_type':'CustomRole','permissions':copy.deepcopy(PERMISSIONS),'condition_sha256':None,
            'condition_version':None,'delegated_identity':None}


def responses():
    row=grant()
    return {endpoint(RID+SUFFIX,API)+'&$filter=atScope%28%29':{'value':[{
        'id':row['assignment_id'],'properties':{'principalId':PRINCIPAL,'principalType':'ServicePrincipal',
        'scope':SCOPE,'roleDefinitionId':ROLE_ID,'description':'DO-NOT-ARCHIVE-AUTH-SECRET'}}]},
        endpoint(LOOKUP,API):{'id':ROLE_ID,'properties':{'type':'CustomRole','roleName':'DO-NOT-ARCHIVE-AUTH-SECRET','permissions':copy.deepcopy(PERMISSIONS)}}}


class AuthorizationTests(unittest.TestCase):
    def test_inherited_grants_and_exact_permissions_are_preserved_without_names(self):
        transport=FixtureTransport(responses())
        result=collect(transport,RID,10,{})
        self.assertEqual(result['state'],'observed')
        self.assertEqual(result['value'],[grant()])
        self.assertNotIn('DO-NOT-ARCHIVE-AUTH-SECRET',json.dumps(result))
        self.assertTrue(valid_grants(result['value']))

    def test_denied_definition_and_partial_pages_never_look_complete(self):
        fixture=responses();fixture[endpoint(LOOKUP,API)]={'fixture_error':403}
        result=collect(FixtureTransport(fixture),RID,10,{})
        self.assertEqual(result['state'],'partial')
        self.assertEqual(result['collection']['errors'][0]['http_status'],403)
        fixture=responses();url=endpoint(RID+SUFFIX,API)+'&$filter=atScope%28%29'
        fixture[url]['nextLink']=endpoint(RID+SUFFIX,API)+'&$skipToken=next'
        result=collect(FixtureTransport(fixture),RID,10,{})
        self.assertEqual(result['state'],'partial')
        self.assertEqual(result['value'],[grant()])

    def test_pagination_scope_filter_and_host_attacks_rejected(self):
        url=endpoint(RID+SUFFIX,API)+'&$filter=atScope%28%29'
        for following in ('https://evil.example/steal',endpoint(RID+SUFFIX,API)+'&$filter=principalId%20eq%20'+PRINCIPAL,
                          endpoint('/subscriptions/'+PRINCIPAL+'/providers/Microsoft.Authorization/roleAssignments',API)):
            fixture=responses();fixture[url]['nextLink']=following
            transport=FixtureTransport(fixture);result=collect(transport,RID,10,{})
            self.assertEqual(result['state'],'partial')
            self.assertNotIn(following,transport.calls)

    def test_unrelated_scope_duplicate_wrong_definition_are_incomplete(self):
        url=endpoint(RID+SUFFIX,API)+'&$filter=atScope%28%29'
        for mutation in ('scope','duplicate','definition'):
            fixture=responses()
            if mutation=='scope':fixture[url]['value'][0]['properties']['scope']='/subscriptions/'+PRINCIPAL
            elif mutation=='duplicate':fixture[url]['value']*=2
            else:fixture[endpoint(LOOKUP,API)]['id']=ROLE_ID.replace(ROLE,PRINCIPAL)
            result=collect(FixtureTransport(fixture),RID,10,{})
            self.assertEqual(result['state'],'partial')

    def test_conditions_hashed_and_role_lookup_cached(self):
        fixture=responses();url=endpoint(RID+SUFFIX,API)+'&$filter=atScope%28%29'
        fixture[url]['value'][0]['properties'].update(condition='DO-NOT-ARCHIVE-CONDITION',conditionVersion='2.0')
        transport=FixtureTransport(fixture);cache={}
        result=collect(transport,RID,10,cache);collect(transport,RID,10,cache)
        self.assertEqual(1,transport.calls.count(endpoint(LOOKUP,API)))
        self.assertEqual(64,len(result['value'][0]['condition_sha256']))
        self.assertNotIn('DO-NOT-ARCHIVE-CONDITION',json.dumps(result))

    def test_malformed_permission_and_principal_rejected(self):
        value=grant();value['principal_id']=None
        self.assertFalse(valid_grants([value]))
        fixture=responses();fixture[endpoint(LOOKUP,API)]['properties']['permissions'][0]['actions']=['secret://bad?token=secret']
        self.assertEqual('partial',collect(FixtureTransport(fixture),RID,10,{})['state'])

    def test_actual_collection_assessment_archive_and_markdown(self):
        from tests.test_controls import fixture,collect as collect_arm
        from azure_at_rest.report import markdown
        arm,policy=fixture()
        snapshot=collect_arm(arm)
        row=next(row for row in snapshot['resources'] if row['type']=='microsoft.storage/storageaccounts')
        observation=collect(FixtureTransport(responses()),RID,10,{})
        row['configuration']['ST-approved-arm-grants']=observation
        policy['checks']['ST-approved-arm-grants']={'operator':'equals','value':[grant()]}
        report=assess_snapshot(snapshot,criteria=policy)
        result=next(r for r in report['configuration_assessment']['results'] if r['check_id']=='ST-approved-arm-grants')
        self.assertEqual('PASS',result['result'])
        self.assertIn('notActions',markdown(report))
        store=MemoryStore();run=save_run(store,snapshot,report)
        self.assertEqual(report,load_run(store,run['run_id'])['assessment'])
        policy['checks']['ST-approved-arm-grants']['value']=[]
        report=assess_snapshot(snapshot,criteria=policy)
        self.assertEqual('FAIL',next(r for r in report['configuration_assessment']['results'] if r['check_id']=='ST-approved-arm-grants')['result'])

    def test_changed_custom_role_permissions_fail_approved_grant_set(self):
        from tests.test_controls import fixture,collect as collect_arm
        arm,policy=fixture();snapshot=collect_arm(arm)
        target=next(row for row in snapshot['resources'] if row['type']=='microsoft.storage/storageaccounts')
        changed=responses()
        changed[endpoint(LOOKUP,API)]['properties']['permissions'][0]['notActions']=[]
        target['configuration']['ST-approved-arm-grants']=collect(FixtureTransport(changed),RID,10,{})
        policy['checks']['ST-approved-arm-grants']={'operator':'equals','value':[grant()]}
        report=assess_snapshot(snapshot,criteria=policy)
        self.assertEqual('FAIL',next(row for row in report['configuration_assessment']['results'] if row['check_id']=='ST-approved-arm-grants')['result'])

    def test_role_definition_reads_stay_under_selected_resource(self):
        transport=FixtureTransport(responses())
        result=collect(transport,RID,10,{})
        self.assertEqual('observed',result['state'])
        self.assertTrue(all(url.startswith('https://management.azure.com'+RID+'/') for url in transport.calls))
