"""Reusable deterministic operations; no host SDK or CLI process dependency."""
import time
from . import report_model
from .archive import save_run, snapshot_digest
from .assessment import assess
from .collector import Collector


class DeadlineExceeded(TimeoutError):
    pass


class Deadline:
    """Cooperative budget between blocking operations; not a process watchdog."""
    def __init__(self, seconds, clock=time.monotonic):
        self.clock = clock
        self.end = clock() + seconds

    def check(self):
        if self.remaining() <= 0:
            raise DeadlineExceeded('execution_budget_exceeded')

    def remaining(self):
        return max(0, self.end - self.clock())

    def sleep(self, seconds):
        if seconds >= self.remaining():
            raise DeadlineExceeded('execution_budget_exceeded')
        time.sleep(seconds)


def assess_snapshot(snapshot, *, reassessed=False, criteria=None, policy=None):
    report = assess(snapshot, criteria, policy)
    report['snapshot_sha256'] = snapshot_digest(snapshot)
    report['reassessed_from_snapshot'] = reassessed
    return report


def collect_run(store, transport, subscriptions=None, *, mode='offline_fixture', max_pages=1000, provenance=None, deadline=None, resource_group=None, criteria=None, graph_transport=None, tenant_id=None, policy_transport=None, policy_assignment=None):
    if deadline:
        deadline.check()
    snapshot = Collector(transport, max_pages, mode).collect(subscriptions, resource_group=resource_group)
    if deadline:
        deadline.check()
    if graph_transport is not None:
        from .graph import GraphCollector
        from .safety import now
        snapshot['identity_evidence'] = GraphCollector(graph_transport,tenant_id,max_pages).collect()
        snapshot['completed_at'] = now()
    policy = None
    if policy_transport is not None and policy_assignment:
        from .policy_compliance import collect as collect_policy
        from .policy_query import fetch_mapping, assignment_id
        selected = sorted({s['id'] for s in snapshot['inventory']['subscriptions']})
        if len(selected) != 1:
            raise ValueError('Policy compliance requires exactly one selected subscription')
        policy_set = fetch_mapping(policy_transport, selected[0], policy_assignment)
        if deadline:
            deadline.check()
        policy = collect_policy(policy_transport.query(selected[0], assignment=policy_assignment,
                                resource_group=resource_group, max_pages=max_pages), policy_set,
                                assignment_id=assignment_id(selected[0], policy_assignment),
                                subscription=selected[0], resource_group=resource_group,
                                max_age_seconds=(criteria or {}).get('max_observation_age_seconds')
                                    if (criteria or {}).get('status') == 'approved' else None)
    report = assess_snapshot(snapshot, criteria=criteria, policy=policy)
    if deadline:
        deadline.check()
    manifest = save_run(store, snapshot, report, provenance=provenance)
    return {'run_id': manifest['run_id'], 'archive_state': 'complete',
            'assessment_conclusion': report_model.overall(report)['conclusion'],
            'coverage_incomplete': report_model.overall(report)['coverage_incomplete'],
            'resource_count': report_model.resource_summary(report)['resource_count'],
            'counts': report_model.resource_summary(report)['counts'],
            'configuration_summary': report_model.configuration_summary(report),
            'policy_summary': (report_model.policy_compliance(report) or {}).get('summary')}
