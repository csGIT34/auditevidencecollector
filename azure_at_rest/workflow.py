"""Reusable deterministic operations; no host SDK or CLI process dependency."""
import time
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


def assess_snapshot(snapshot, *, reassessed=False, criteria=None):
    report = assess(snapshot, criteria)
    report['snapshot_sha256'] = snapshot_digest(snapshot)
    report['reassessed_from_snapshot'] = reassessed
    return report


def collect_run(store, transport, subscriptions=None, *, mode='offline_fixture', max_pages=1000, provenance=None, deadline=None, resource_group=None, criteria=None, graph_transport=None, tenant_id=None):
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
    report = assess_snapshot(snapshot, criteria=criteria)
    if deadline:
        deadline.check()
    manifest = save_run(store, snapshot, report, provenance=provenance)
    return {'run_id': manifest['run_id'], 'archive_state': 'complete',
            'assessment_conclusion': report['overall_summary']['conclusion'],
            'coverage_incomplete': report['overall_summary']['coverage_incomplete'],
            'resource_count': report['summary']['resource_count'], 'counts': report['summary']['counts'],
            'configuration_summary': report['configuration_assessment']['summary']}
