#!/usr/bin/env python3
"""Recover the label pilot without replacing frozen observer source files.

prepare copies a verified contiguous prefix and archives the original failure.
resume adds schema maxItems=6 to remaining requests. No automatic retries.
Use this script, including its analyze command, for the recovered folder.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import zipfile
import moriarty as core
import followup
import transfer
import review_label_case as review

VERSION='label-recovery-0.1.0'
NOTE=('Exploratory recovery: a validated original prefix is reused; remaining requests '
      'add evidence.maxItems=6. Failed attempts are retained and excluded from history. '
      'This is not a wholly rerun experiment under one unchanged output schema.')

def digest_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def timestamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def verify_identity(record,job,payload):
    if record.get('job_id') != job['job_id'] or record.get('request_sha256') != core.digest(payload):
        raise ValueError('Saved response identity/request checksum mismatch; cannot reuse or retry automatically.')

def prepare(source,out):
    source,out=Path(source).resolve(),Path(out).resolve()
    if out.exists() or source==out or source in out.parents or out in source.parents:
        raise ValueError('Use a new sibling output folder, not the original or one of its subfolders.')
    if (source/'.running').exists():
        raise ValueError('Original run has a lock; confirm its process stopped before handling that lock.')
    plan=transfer.load_plan(source)
    if plan['cases'][0]['case_id'] != 'ai_village_gpt55_label_swap_exact_zero_v2':
        raise ValueError('This recovery is for the v2 label case.')
    if (source/'recovery_plan.json').exists():
        raise ValueError('Already a recovery run; use resume instead.')
    known={j['job_id'] for j in plan['jobs']}
    if any(p.stem not in known for p in (source/'responses').glob('*.json')):
        raise ValueError('Unknown saved response file.')
    valid={}; failed=[]; gap=False; copied=[]
    for job in plan['jobs']:
        path=source/'responses'/(job['job_id']+'.json')
        if not path.exists():gap=True;continue
        if gap:
            raise ValueError('Saved responses exist after a gap/failure; this recovery requires a contiguous prefix.')
        record=core.read(path)
        payload=followup.payload_for(plan,job,[valid[k] for k in job['parent_job_ids']])
        verify_identity(record,job,payload)
        if record.get('status')=='valid':
            transfer.record_check(record,job,payload)
            valid[job['job_id']]=record
            copied.append({'job_id':job['job_id'],'sha256':digest_file(path)})
        elif record.get('status')=='invalid':
            try:
                wire=core.extract_response(record['response'])
                parsed,_=core.resolve_citations(wire,job['public'])
                errors=core.validate_output(parsed,job['public']['visible_records'],job['order'])
            except (ValueError,KeyError,TypeError) as exc:errors=[str(exc)]
            if not errors:
                raise ValueError('Saved status is invalid but raw output validates. Inspect this inconsistency first.')
            failed.append({'job_id':job['job_id'],'sha256':digest_file(path),'errors':errors})
            gap=True
        else:
            raise ValueError('Unknown original response status.')
    if len(valid)==len(plan['jobs']):
        raise ValueError('Original run is already complete; no recovery needed.')
    policy={'version':VERSION,'created_utc':timestamp(),'base_plan_sha256':core.digest(plan),
       'runner_sha256':transfer.sha(__file__),'review_sha256':transfer.sha(review.__file__),
       'reused_responses':copied,'original_invalid':failed,
       'strict_job_ids':[j['job_id'] for j in plan['jobs'] if j['job_id'] not in valid],
       'schema_change':{'path':'text.format.schema.properties.evidence.maxItems','value':6},
       'interpretation_limit':NOTE}
    # Read and validate everything before creating the destination.
    out.mkdir(parents=True)
    shutil.copy2(source/'plan.json',out/'plan.json')
    (out/'responses').mkdir();(out/'source_archive').mkdir()
    for item in copied:
        shutil.copy2(source/'responses'/(item['job_id']+'.json'),out/'responses'/(item['job_id']+'.json'))
    for item in failed:
        shutil.copy2(source/'responses'/(item['job_id']+'.json'),out/'source_archive'/(item['job_id']+'.json'))
    if (source/'manifest.json').exists():shutil.copy2(source/'manifest.json',out/'source_archive'/'original_manifest.json')
    core.write(out/'recovery_plan.json',policy)
    print(f'PREPARED: {len(valid)} valid responses reused; {len(failed)} invalid response archived; '
          f'{len(policy["strict_job_ids"])} requests remain. Zero API calls.')
    for item in failed:print('Original failure: '+item['job_id']+'; '+'; '.join(item['errors']))
    return policy

def load(out):
    plan=transfer.load_plan(out);p=core.read(out/'recovery_plan.json')
    if p.get('version')!=VERSION or p.get('base_plan_sha256')!=core.digest(plan):
        raise ValueError('Recovery/base plan mismatch.')
    if p.get('runner_sha256')!=transfer.sha(__file__) or p.get('review_sha256')!=transfer.sha(review.__file__):
        raise ValueError('Recovery or review code changed after preparation.')
    reused=p['reused_responses'];ids=[r['job_id'] for r in reused]
    if ids != [j['job_id'] for j in plan['jobs'][:len(ids)]]:
        raise ValueError('Reused IDs are not a contiguous original prefix.')
    if p['strict_job_ids'] != [j['job_id'] for j in plan['jobs'][len(ids):]]:
        raise ValueError('Strict-schema job selection changed.')
    for item in reused:
        if digest_file(out/'responses'/(item['job_id']+'.json'))!=item['sha256']:
            raise ValueError('A reused response changed.')
    for item in p['original_invalid']:
        if digest_file(out/'source_archive'/(item['job_id']+'.json'))!=item['sha256']:
            raise ValueError('An archived failure changed.')
    return plan,p

def payload_for(plan,policy,job,valid):
    payload=followup.payload_for(plan,job,[valid[k] for k in job['parent_job_ids']])
    if job['job_id'] in policy['strict_job_ids']:
        payload['text']['format']['schema']['properties']['evidence']['maxItems']=6
    return payload

def collect(out,plan,policy):
    valid={};missing=[];invalid=[]
    expected={j['job_id'] for j in plan['jobs']}
    if any(p.stem not in expected for p in (out/'responses').glob('*.json')):
        raise ValueError('Unknown response file in recovered run.')
    for job in plan['jobs']:
        path=out/'responses'/(job['job_id']+'.json')
        if not path.exists():missing.append(job['job_id']);continue
        try:
            record=core.read(path);payload=payload_for(plan,policy,job,valid)
            transfer.record_check(record,job,payload)
            if job['job_id'] in policy['strict_job_ids']:
                attempts=[core.read(p) for p in sorted((out/'attempts'/job['job_id']).glob('*.json'))]
                matches=[a for a in attempts if a.get('status')=='valid' and a.get('record')==record]
                if len(matches)!=1:raise ValueError('Accepted response lacks exactly one matching valid attempt.')
            valid[job['job_id']]=record
        except (OSError,ValueError,KeyError,TypeError,AssertionError) as exc:
            invalid.append({'job_id':job['job_id'],'error':str(exc)})
    return valid,missing,invalid

def resume(out,execute=False,max_new_calls=10,retry_failed=False):
    out=Path(out);plan,policy=load(out)
    valid,missing,invalid=collect(out,plan,policy)
    if invalid:raise ValueError('Existing accepted responses failed validation: '+str(invalid))
    if len(missing)>max_new_calls:
        raise ValueError(f'{len(missing)} calls remain, exceeding --max-new-calls {max_new_calls}. No requests sent.')
    if not execute:
        print(f'DRY RUN: reuse {len(valid)} valid responses; {len(missing)} calls remain; zero sent.');return
    if not missing:
        print('Already complete; zero new API calls.');analyze(out);return
    if not os.getenv('OPENAI_API_KEY'):raise ValueError('OPENAI_API_KEY is missing.')
    lock=out/'.running'
    with lock.open('x') as f:f.write(str(os.getpid()))
    count=0
    state={'status':'running','recovery_plan_sha256':core.digest(policy),
           'new_requests_attempted':0,'completed_valid_outputs':len(valid)}
    core.write(out/'recovery_manifest.json',state)
    try:
        for n,job in enumerate(plan['jobs'],1):
            jid=job['job_id']
            if jid in valid:
                print(f'{n}/{len(plan["jobs"])} {job["arm"]} {job["checkpoint_id"]}: reused',flush=True);continue
            attempt_dir=out/'attempts'/jid;old=sorted(attempt_dir.glob('*.json'))
            if old:
                last=core.read(old[-1])
                if last['status']=='valid':raise ValueError('A valid attempt exists without its accepted response. Restore that response; do not re-call the model.')
                if not retry_failed:raise ValueError('Previous failed/uncertain attempt retained. Inspect it; use --retry-failed to authorize one further attempt at this checkpoint.')
            payload=payload_for(plan,policy,job,valid)
            attempt_path=attempt_dir/(f'{len(old)+1:04d}.json')
            attempt={'job_id':jid,'created_utc':timestamp(),'status':'request_started',
                     'request_sha256':core.digest(payload),'request':payload}
            core.write(attempt_path,attempt)
            count+=1;state['new_requests_attempted']=count;core.write(out/'recovery_manifest.json',state)
            try:raw=core.api_call(payload)
            except Exception as exc:
                attempt.update(status='request_error',error=str(exc));core.write(attempt_path,attempt);raise
            record={'job_id':jid,'checkpoint_id':job['checkpoint_id'],
                    'request_sha256':core.digest(payload),'response':raw,'status':'invalid','parsed':None}
            try:
                wire=core.extract_response(raw);record['raw_parsed']=wire
                record['parsed'],record['citation_resolution']=core.resolve_citations(wire,job['public'])
                errors=core.validate_output(record['parsed'],job['public']['visible_records'],job['order'])
                if errors:raise ValueError('; '.join(errors))
                record['status']='valid'
            except (ValueError,KeyError,TypeError) as exc:record['errors']=[str(exc)]
            attempt.update(status=record['status'],record=record);core.write(attempt_path,attempt)
            if record['status']!='valid':
                raise ValueError('New response invalid: '+'; '.join(record['errors'])+'. Saved in '+str(attempt_path)+'. No automatic retry.')
            transfer.record_check(record,job,payload)
            core.write(out/'responses'/(jid+'.json'),record);valid[jid]=record
            state['completed_valid_outputs']=len(valid);core.write(out/'recovery_manifest.json',state)
            print(f'{n}/{len(plan["jobs"])} {job["arm"]} {job["checkpoint_id"]}: new valid',flush=True)
        state['status']='completed';core.write(out/'recovery_manifest.json',state)
    except Exception as exc:
        state.update(status='stopped',reason=str(exc));core.write(out/'recovery_manifest.json',state);raise
    finally:lock.unlink(missing_ok=True)
    analyze(out)

def analyze(out,review_path=None):
    out=Path(out);plan,policy=load(out)
    valid,missing,invalid=collect(out,plan,policy)
    # Bind human reviews to the recovery policy as well as the original plan.
    review_plan={**plan,'recovery_plan_sha256':core.digest(policy)}
    saved=out/'label_reviewed_dataset.json';path=review_path or (saved if saved.exists() else None)
    reviews=review.validate_review(core.read(path),review_plan,valid) if path else {}
    if review_path:core.write(saved,core.read(review_path))
    report=review.summarize(review_plan,valid,missing,invalid,reviews)
    report.update(recovery=policy,original_base_plan_sha256=core.digest(plan))
    report['limitations'].append(NOTE)
    attempts=[core.read(p) for p in sorted((out/'attempts').glob('*/*.json'))]
    report['recovery_attempt_statuses']={s:sum(a['status']==s for a in attempts) for s in sorted({a['status'] for a in attempts})}
    report['original_invalid_attempts']=len(policy['original_invalid'])
    report['recovery_attempt_usage']={k:sum(((a.get('record',{}).get('response',{}).get('usage') or {}).get(k,0)) for a in attempts) for k in ['input_tokens','output_tokens']}
    core.write(out/'label_results.json',report);review.render(out,review_plan,valid,reviews)
    with zipfile.ZipFile(out/'label_share_bundle.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in ['plan.json','recovery_plan.json','recovery_manifest.json','label_results.json','label_review.html','label_reviewed_dataset.json']:
            p=out/name
            if p.exists():z.write(p,name)
        for folder in ['responses','attempts','source_archive']:
            for p in sorted((out/folder).rglob('*.json')):z.write(p,p.relative_to(out).as_posix())
    print(f'{len(valid)}/{len(plan["jobs"])} valid. Review: {out/"label_review.html"}. Share: {out/"label_share_bundle.zip"}.')
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('prepare');a.add_argument('--from-run',type=Path,required=True);a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('resume');a.add_argument('--out',type=Path,required=True);a.add_argument('--execute',action='store_true')
    a.add_argument('--max-new-calls',type=int,default=10);a.add_argument('--retry-failed',action='store_true')
    a=sub.add_parser('analyze');a.add_argument('--out',type=Path,required=True);a.add_argument('--review',type=Path)
    args=p.parse_args()
    try:
        if args.cmd=='prepare':prepare(args.from_run,args.out)
        elif args.cmd=='resume':resume(args.out,args.execute,args.max_new_calls,args.retry_failed)
        else:analyze(args.out,args.review)
    except (ValueError,OSError,RuntimeError,KeyError,TypeError,AssertionError) as exc:
        p.exit(1,'ERROR: '+str(exc)+'\n')

if __name__=='__main__':main()
