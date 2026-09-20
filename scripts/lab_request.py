"""One explicitly selected live lab HTTP request; no retries, keys only in memory."""
import argparse
import getpass
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.request import Request, build_opener
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cloud_governance.collector import NoRedirect
from cloud_governance.archive import identity


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',required=True,help='Exact https://APP.azurewebsites.net base URL')
    parser.add_argument('--operation',choices=['probe','report','collect','no-key'],required=True)
    parser.add_argument('--run-id')
    parser.add_argument('--private-output',type=Path,required=True)
    args=parser.parse_args()
    if not re.fullmatch(r'https://[a-z0-9-]+\.azurewebsites\.net',args.url):
        raise ValueError('Expected exact Azure public-cloud Function App base URL')
    output=args.private_output.expanduser().resolve()
    if output.is_relative_to(ROOT) or output.exists():
        raise ValueError('Use a new private output file outside the checkout')
    if args.operation=='report':
        body={'run_id':identity(args.run_id,'r')};path='/api/reports'
    elif args.operation=='collect':
        body={'input':''};path='/admin/functions/CollectEvidence'
    else:body={};path='/api/lab-probe'
    headers={'Content-Type':'application/json'}
    if args.operation!='no-key':
        key=getpass.getpass('Lab master key (collect only): ' if args.operation=='collect' else 'Lab function key: ')
        if not key or '\n' in key or '\r' in key:raise ValueError('Invalid key')
        headers['x-functions-key']=key
    request=Request(args.url+path,data=json.dumps(body).encode(),headers=headers,method='POST')
    try:
        with build_opener(NoRedirect()).open(request,timeout=150) as response:status=response.status;data=response.read()
    except HTTPError as error:status=error.code;data=error.read()
    os.umask(0o077);output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('xb') as stream:stream.write(data)
    print('HTTP',status,'; response saved privately. No retry performed; inspect archive before retrying an uncertain request.')
    return 0 if 200<=status<300 else 1


if __name__=='__main__':raise SystemExit(main())
