from cloud_governance import report_model
import copy
import json
import unittest
from unittest.mock import patch
from cloud_governance.backup_jobs import collect,assess,valid_criterion
from cloud_governance.collector import FixtureTransport,endpoint
from cloud_governance.controls import CHECKS,validate_policy
from tests.helpers import resource

SOURCE=resource('Microsoft.Compute/disks','protected')['id'].lower()
AS_OF='2026-09-20T01:00:00+00:00'


def job(rid,check):
    return {'id':rid+'/backupJobs/job-1','properties':{'dataSourceId':SOURCE,'operationCategory':'Backup','operation':'Backup','status':'Completed',
        'startTime':'2026-09-20T00:00:00Z','endTime':'2026-09-20T00:30:00Z',
        'errorDetails':[{'message':'SECRET-CANARY'}],'extendedInfo':{'propertyBag':{'password':'SECRET-CANARY'}}}}


def normalized(raw,check):
    p=raw['properties'];dp=check.resource_type=='microsoft.dataprotection/backupvaults'
    return {'job_id':raw['id'].lower(),'source_id':p['dataSourceId'].lower() if dp else None,'operation':p['operationCategory'] if dp else p['operation'],
            'status':p['status'],'start_time':p['startTime'],'end_time':p.get('endTime')}


def criterion(scope='sources'):
    return {'scope':scope,'source_ids':[SOURCE] if scope=='sources' else [],'operation':'Backup','max_age_seconds':3600}

class BackupJobTests(unittest.TestCase):
    def cases(self):
        for cid in ('BV-backup-jobs','BV-recovery-jobs'):
            c=CHECKS[cid];rid=resource(c.resource_type,'vault')['id'];yield c,rid,job(rid,c)

    def test_both_vaults_exclude_job_error_bags_and_preserve_times(self):
        for c,rid,raw in self.cases():
            result=collect(FixtureTransport({endpoint(rid+c.suffix,c.api):{'value':[raw]}}),rid,c,10)
            self.assertEqual('observed',result['state']);self.assertEqual([normalized(raw,c)],result['value'])
            self.assertNotIn('SECRET-CANARY',json.dumps(result))

    def test_bad_dates_wrong_vault_duplicates_denial_and_truncation_are_partial(self):
        for c,rid,raw in self.cases():
            wrong=copy.deepcopy(raw);wrong['id']=rid+'-wrong/backupJobs/job-1'
            missing=copy.deepcopy(raw);missing['properties'].pop('endTime')
            reversed_time=copy.deepcopy(raw);reversed_time['properties']['endTime']='2026-09-19T00:00:00Z'
            url=endpoint(rid+c.suffix,c.api)
            for response in ({'value':[wrong]},{'value':[missing]},{'value':[reversed_time]},{'value':[raw,raw]},
                             {'fixture_error':403},{'value':[raw],'nextLink':url+'&$skiptoken=missing'}):
                self.assertEqual('partial',collect(FixtureTransport({url:response}),rid,c,10)['state'])

    def test_recency_handles_latest_failures_staleness_future_and_missing_population(self):
        c,rid,raw=next(self.cases());row=normalized(raw,c);expected=criterion()
        self.assertEqual('PASS',assess([row],expected,AS_OF)[0])
        self.assertEqual('FAIL',assess([],expected,AS_OF)[0])
        self.assertEqual('FAIL',assess([row],{**expected,'source_ids':[SOURCE+'-other']},AS_OF)[0])
        self.assertEqual('FAIL',assess([row],expected,'2026-09-20T02:00:00Z')[0])
        self.assertEqual('UNKNOWN',assess([row],expected,'2026-09-19T23:00:00Z')[0])
        for status,result in [('Failed','FAIL'),('CompletedWithWarnings','FAIL'),('InProgress','UNKNOWN')]:
            latest={**row,'job_id':row['job_id']+'-new','start_time':'2026-09-20T00:45:00Z','end_time':None,'status':status}
            self.assertEqual(result,assess([row,latest],expected,AS_OF)[0])
        conflict={**row,'job_id':row['job_id']+'-conflict','status':'Failed'}
        self.assertEqual('FAIL',assess([row,conflict],expected,AS_OF)[0])

    def test_operator_requires_explicit_scope_valid_window_and_supported_association(self):
        dp=CHECKS['BV-backup-jobs'];rs=CHECKS['BV-recovery-jobs']
        self.assertTrue(valid_criterion(dp,criterion()));self.assertFalse(valid_criterion(rs,criterion()))
        self.assertTrue(valid_criterion(rs,criterion('vault')))
        for changes in ({'max_age_seconds':True},{'max_age_seconds':0},{'source_ids':[]},{'operation':'Anything'},{'scope':'implicit'}):
            self.assertFalse(valid_criterion(dp,{**criterion(),**changes}))

    def test_full_pipeline_uses_frozen_assessment_time_and_policy(self):
        from tests.test_controls import fixture,collect as collect_arm
        from cloud_governance.workflow import assess_snapshot
        from cloud_governance.archive import save_run,load_run
        from tests.test_archive import MemoryStore
        responses,policy=fixture();policy['checks']['BV-backup-jobs']={'operator':'recent_jobs','value':criterion()}
        policy['checks']['BV-recovery-jobs']={'operator':'recent_jobs','value':criterion('vault')}
        validate_policy(policy)
        snapshot=collect_arm(responses)
        with patch('cloud_governance.controls.now',return_value=AS_OF):report=assess_snapshot(snapshot,criteria=policy)
        self.assertTrue(all(r['result']=='PASS' for r in report_model.configuration_results(report)))
        store=MemoryStore();manifest=save_run(store,snapshot,report)
        # Replay does not reinterpret old observations using today's age.
        with patch('cloud_governance.backup_jobs.assess',side_effect=AssertionError('must not reassess')):
            load_run(store,manifest['run_id'])


    def test_backup_success_cannot_substitute_for_required_restore(self):
        c,rid,raw=next(self.cases());backup=normalized(raw,c)
        expected={**criterion(),'operation':'BackupAndRestore'}
        self.assertEqual('FAIL',assess([backup],expected,AS_OF)[0])
        restore={**backup,'job_id':backup['job_id']+'-restore','operation':'Restore'}
        self.assertEqual('PASS',assess([backup,restore],expected,AS_OF)[0])
        restore['status']='Failed'
        self.assertEqual('FAIL',assess([backup,restore],expected,AS_OF)[0])


    def test_known_failure_does_not_hide_unfinished_required_restore(self):
        from cloud_governance.controls import overall_summary
        c,rid,raw=next(self.cases());backup=normalized(raw,c);backup['status']='Failed'
        restore={**backup,'job_id':backup['job_id']+'-restore','operation':'Restore','status':'InProgress','end_time':None}
        result,reason,details=assess([backup,restore],{**criterion(),'operation':'BackupAndRestore'},AS_OF)
        self.assertEqual('FAIL',result);self.assertTrue(details['coverage_incomplete'])
        report={'summary':{'counts':{'FAIL':0},'coverage_incomplete':False},'configuration_assessment':{
            'summary':{'conclusion':'FAILURES_FOUND','counts':{'FAIL':1,'UNKNOWN':0,'ERROR':0}},'results':[{'job_evaluation':details}]}}
        self.assertEqual({'conclusion':'FAILURES_FOUND','coverage_incomplete':True,'failed_check_count':1},overall_summary(report))
