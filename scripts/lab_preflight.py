"""Read-only Azure preflight. Private JSON results only; never assumes empty costs mean $0."""
import argparse
import collections
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import subprocess
from uuid import UUID

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--subscription',required=True);p.add_argument('--tenant',required=True)
    p.add_argument('--private-output',type=Path,required=True)
    args=p.parse_args()
    sid,tenant=str(UUID(args.subscription)),str(UUID(args.tenant))
    output=args.private_output.expanduser().resolve()
    if output.is_relative_to(ROOT):
        raise ValueError('Save personal results OUTSIDE the source checkout')
    os.umask(0o077);output.mkdir(parents=True,exist_ok=False)
    def az(name,command):
        result=subprocess.run(['az',*command,'--only-show-errors','-o','json'],capture_output=True,text=True,timeout=120)
        if result.returncode:
            # May contain billing/account identifiers: private error file, never echo.
            (output/(name+'.error.txt')).write_text(result.stderr)
            return {'unavailable':True}
        try:data=json.loads(result.stdout)
        except ValueError:data={'unavailable':True}
        (output/(name+'.json')).write_text(json.dumps(data,indent=2));return data
    account=az('account',['account','show'])
    if account.get('id') != sid or account.get('tenantId') != tenant or account.get('environmentName') != 'AzureCloud' or account.get('state') != 'Enabled':
        raise ValueError('Active AzureCloud account does not match explicitly approved context; no further checks performed')
    scope='/subscriptions/'+sid
    def rest(name,path,body=None):
        command=['rest','--method','post' if body is not None else 'get','--url','https://management.azure.com'+path]
        if body is not None:
            f=output/(name+'.request.json');f.write_text(json.dumps(body));command+=['--body','@'+str(f)]
        return az(name,command)
    rest('subscription',scope+'?api-version=2022-12-01')
    rows=az('resource_metadata',['resource','list','--subscription',sid,'--query','[].{type:type,location:location}'])
    if isinstance(rows,list):
        (output/'resource_counts.json').write_text(json.dumps(dict(collections.Counter(r['type'] for r in rows)),indent=2))
    dataset={'granularity':'None','aggregation':{'totalCost':{'name':'Cost','function':'Sum'}}}
    for period in ('MonthToDate','BillingMonthToDate'):
        rest(period,scope+'/providers/Microsoft.CostManagement/query?api-version=2025-03-01',{'type':'ActualCost','timeframe':period,'dataset':dataset})
    now=datetime.now(timezone.utc);month_end=(now.replace(day=1)+timedelta(days=32)).replace(day=1)-timedelta(seconds=1)
    rest('forecast',scope+'/providers/Microsoft.CostManagement/forecast?api-version=2025-03-01',{
        'type':'Usage','timeframe':'Custom','dataset':{**dataset,'granularity':'Daily'},
        'timePeriod':{'from':now.strftime('%Y-%m-%dT00:00:00Z'),'to':month_end.strftime('%Y-%m-%dT23:59:59Z')},
        'includeActualCost':False,'includeFreshPartialCost':False})
    rest('policies',scope+'/providers/Microsoft.Authorization/policyAssignments?api-version=2023-04-01&$filter=atScope()')
    rest('defender',scope+'/providers/Microsoft.Security/pricings?api-version=2024-01-01')
    az('flex_locations',['functionapp','list-flexconsumption-locations'])
    az('providers',['provider','list','--subscription',sid,'--query',"[?namespace=='Microsoft.Web' || namespace=='Microsoft.Storage' || namespace=='Microsoft.ManagedIdentity' || namespace=='Microsoft.Authorization' || namespace=='Microsoft.App'].{namespace:namespace,state:registrationState}"])
    print('Read-only checks finished. Review private output and errors. Empty/missing costs, forecasts, quota or policies are unresolved; no financial approval is implied.')


if __name__=='__main__':main()
