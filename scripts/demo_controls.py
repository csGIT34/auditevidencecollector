"""Run all registered configuration predicates with synthetic ARM/Graph evidence."""
from cloud_governance import report_model
import argparse
import json
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    target=args.output.resolve()
    if target.exists() or target==ROOT or ROOT in target.parents:parser.error('Use a new directory outside the checkout')
    os.umask(0o077)
    from cloud_governance.archive import load_run,publish_pdf,encode,digest
    from cloud_governance.collector import FixtureTransport
    from cloud_governance.graph import FixtureGraphTransport
    from cloud_governance.controls import decode_policy
    from cloud_governance.report import markdown
    from cloud_governance.storage import FileStore
    from cloud_governance.workflow import collect_run
    source=ROOT/'examples/control-suite'
    arm=json.loads((source/'arm-fixture.json').read_text())['responses']
    graph=json.loads((source/'graph-fixture.json').read_text())['responses']
    criteria=decode_policy((source/'criteria.json').read_text())
    store=FileStore(target/'archive');exports=FileStore(target)
    run=collect_run(store,FixtureTransport(arm),['11111111-1111-1111-1111-111111111111'],
                    graph_transport=FixtureGraphTransport(graph),tenant_id='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',criteria=criteria)
    saved=load_run(store,run['run_id'])
    before={k:digest(store.read(k)) for k in store.keys('runs/')}
    pdf=publish_pdf(store,run['run_id'])
    assert before=={k:digest(store.read(k)) for k in before}
    exports.put_new('report.pdf',store.read(pdf['pdf']['key']))
    exports.put_new('assessment.json',encode(saved['assessment']))
    exports.put_new('report.md',markdown(saved['assessment']).encode())
    cfg=report_model.configuration(saved['assessment'])
    result={'synthetic':True,'azure_calls':0,'graph_calls':0,'run_id':run['run_id'],
            'service_entries':len({r['catalog_ref'].split('-')[0] for r in cfg['results']}),
            'configuration_summary':cfg['summary'],'archive_originals_preserved':True,
            'pdf_sha256':pdf['pdf']['sha256'], 'pdf':str(target/'report.pdf')}
    exports.put_new('result.json',encode(result));print(json.dumps(result,indent=2))

if __name__=='__main__':main()
