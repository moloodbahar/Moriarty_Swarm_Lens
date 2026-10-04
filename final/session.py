#!/usr/bin/env python3
"""MORIARTY reusable session runner. Frozen observer prompts; evidence cap enforced."""
import argparse
import collections
import hashlib
import html
import json
import os
from pathlib import Path
import random
import sys
import zipfile
import moriarty as core
import followup as previous

ROOT=Path(__file__).resolve().parent
VERSION='session-1.0.0'
EXPECTED_CORE='6eadc0f304d2e69af1edd87bcaec51098738be49e008b029af9b169df631d70e'
EXPECTED_FOLLOWUP='eb824aa66910aa1d1310b9287b395c4ab67051834384897aab650f243ed631b4'
TARGET_LABELS=('unreviewed','on_target','off_target','mixed','unjudgeable')
SUPPORT_LABELS=('unreviewed','supported','unsupported','unclear')

def sha(path):
    # Git on Windows may convert LF to CRLF without changing the Python source.
    return hashlib.sha256(Path(path).read_bytes().replace(b'\r\n',b'\n')).hexdigest()

def make_plan(case,model,repeats=1,seed=261004,max_output_tokens=4096):
    if sha(core.__file__)!=EXPECTED_CORE or sha(previous.__file__)!=EXPECTED_FOLLOWUP:
        raise ValueError('The frozen observer files differ. Use the unchanged files in this release.')
    if len(case['checkpoints'])!=6:raise ValueError('Declare exactly six checkpoints for this protocol.')
    if len({c['id'] for c in case['checkpoints']})!=6:raise ValueError('Checkpoint IDs must be unique.')
    plan=previous.make_plan([case],model,list(previous.ARMS),['observed'],repeats,seed,max_output_tokens,'real')
    plan.update(version=VERSION,suite='generic_session',transfer_sha256=sha(__file__),
      followup_version=previous.VERSION,case_sha256=core.digest(case),
      limitations=[
        'One selected session; checkpoints and repeats are not independent episodes.',
        'Probabilities are model reports, not calibrated factual confidence.',
        'Exact quotes establish source existence, not whether an inference follows.',
        'History and recap add unequal input tokens. No demonstrated intervention gain.',
        'This release does not assign automatic factual accuracy, including for the illustrative fixture.'])
    plan['real_source_episode_count']=int(case['kind']=='real_observational')
    for job in plan['jobs']:payload_for(plan,job,[])  # preflight schema size before any paid call
    return plan

def payload_for(plan,job,parents):
    payload=previous.payload_for(plan,job,parents)
    payload['text']['format']['schema']['properties']['evidence']['maxItems']=6
    return payload

def load_plan(out):
    plan=core.read(out/'plan.json')
    if plan.get('version')!=VERSION:raise ValueError('Use session.py only for session-1.0.0 run folders.')
    expected=make_plan(plan['cases'][0],plan['model'],plan['repeats'],plan['seed'],plan['max_output_tokens'])
    if core.digest(plan)!=core.digest(expected):raise ValueError('Plan or code was changed after the run was frozen.')
    return plan

def record_check(record,job,payload):
    if record.get('job_id')!=job['job_id']:raise ValueError('Saved response belongs to a different job.')
    previous.check_record(record,job,payload)

def run(args):
    case=core.load_case(args.case)
    plan=make_plan(case,args.model,args.repeats,args.seed,args.max_output_tokens)
    if plan['selected_calls']>args.max_calls:
        raise ValueError(f'{plan["selected_calls"]} calls required, exceeding --max-calls {args.max_calls}. No requests sent.')
    if args.execute and not os.getenv('OPENAI_API_KEY'):raise ValueError('OPENAI_API_KEY is missing. No requests sent.')
    out=args.out
    if (out/'plan.json').exists():
        if core.digest(core.read(out/'plan.json'))!=core.digest(plan):raise ValueError('Configuration differs. Use a new --out.')
    elif out.exists() and any(out.iterdir()):raise ValueError('Choose an empty output folder or a matching run.')
    out.mkdir(parents=True,exist_ok=True)
    lock=out/'.running'
    if lock.exists():raise ValueError('Run lock exists. Remove it only after confirming no earlier process is running.')
    core.write(out/'plan.json',plan)
    if not args.execute:
        print(f'DRY RUN: {len(plan["jobs"])} calls planned, zero sent. See {out/"plan.json"}')
        return
    with lock.open('x') as handle:handle.write(str(os.getpid()))
    valid={}
    state={'status':'running','plan_sha256':core.digest(plan),'new_requests_attempted':0,'completed_valid_outputs':0}
    core.write(out/'manifest.json',state)
    try:
        for n,job in enumerate(plan['jobs'],1):
            parents=[valid[x] for x in job['parent_job_ids']]
            payload=payload_for(plan,job,parents)
            path=out/'responses'/(job['job_id']+'.json')
            if path.exists():
                record=core.read(path);record_check(record,job,payload)
            else:
                core.write(out/'requests'/(job['job_id']+'.json'),payload)
                state['new_requests_attempted']+=1;core.write(out/'manifest.json',state)
                raw=core.api_call(payload)
                record={'job_id':job['job_id'],'checkpoint_id':job['checkpoint_id'],
                  'request_sha256':core.digest(payload),'response':raw,'status':'invalid','parsed':None}
                try:
                    wire=core.extract_response(raw)
                    record['raw_parsed']=wire
                    record['parsed'],record['citation_resolution']=core.resolve_citations(wire,job['public'])
                    errors=core.validate_output(record['parsed'],job['public']['visible_records'],job['order'])
                    if errors:raise ValueError('; '.join(errors))
                    record['status']='valid'
                except (ValueError,KeyError,TypeError) as exc:record['errors']=[str(exc)]
                core.write(path,record);record_check(record,job,payload)
            valid[job['job_id']]=record
            state['completed_valid_outputs']=len(valid);core.write(out/'manifest.json',state)
            print(f'{n}/{len(plan["jobs"])} {job["arm"]} {job["checkpoint_id"]}: valid',flush=True)
        state['status']='completed';core.write(out/'manifest.json',state)
    except Exception as exc:
        state['status']='stopped';state['reason']=str(exc);core.write(out/'manifest.json',state);raise
    finally:lock.unlink(missing_ok=True)
    analyze(out)

def read_reviews(path,plan,valid):
    if path is None:return {}
    review=core.read(path)
    previous.validate_reviews(review,plan,valid)
    return {r['job_id']:r for r in review['answers']}

def analyze(out,review_path=None):
    plan=load_plan(out);case=plan['cases'][0]
    valid={};missing=[];invalid=[]
    for job in plan['jobs']:
        path=out/'responses'/(job['job_id']+'.json')
        if not path.exists():missing.append(job['job_id']);continue
        try:
            record=core.read(path)
            payload=payload_for(plan,job,[valid[x] for x in job['parent_job_ids']])
            record_check(record,job,payload);valid[job['job_id']]=record
        except (ValueError,KeyError,TypeError) as exc:invalid.append({'job_id':job['job_id'],'error':str(exc)})
    saved=out/'reviewed_dataset.json'
    path=review_path or (saved if saved.exists() else None)
    reviews=read_reviews(path,plan,valid)
    if review_path:core.write(saved,core.read(review_path))
    outputs=[];finals=[];usage=collections.defaultdict(collections.Counter)
    for job in plan['jobs']:
        if job['job_id'] not in valid:continue
        record=valid[job['job_id']]
        entry={'job_id':job['job_id'],'case_id':job['case_id'],'repeat':job['repeat'],'arm':job['arm'],
          'checkpoint_id':job['checkpoint_id'],'visible_record_count':len(job['public']['visible_records']),
          'answer':record['parsed']}
        outputs.append(entry)
        u=record['response'].get('usage',{}) or {}
        for key in ('input_tokens','output_tokens'):usage[job['arm']][key]+=u.get(key,0)
        if job['variant']!='stem':
            chain=[valid[x]['parsed'] for x in job['parent_job_ids']]+[record['parsed']]
            finals.append({**entry,'probabilities':record['parsed']['probabilities'],
              'trajectory':core.trajectory_metrics(chain,None,None,.8),'review':reviews.get(job['job_id'])})
    counts=collections.Counter((x['review'] or {}).get('target','unreviewed') for x in finals)
    judged=sum(counts[k] for k in ('on_target','off_target','mixed'))
    contrasts=[]
    lookup={(x['repeat'],x['arm']):x for x in finals}
    for arm in plan['arms']:
        if arm=='fresh_prefix':continue
        deltas={h['id']:[] for h in case['hypotheses']}
        for repeat in range(plan['repeats']):
            a=lookup.get((repeat,'fresh_prefix'));b=lookup.get((repeat,arm))
            if a and b:
                for hid in deltas:deltas[hid].append(b['probabilities'][hid]-a['probabilities'][hid])
        contrasts.append({'arm_minus_fresh':arm,'probability_differences':{k:previous.paired_summary(v) for k,v in deltas.items()}})
    report={'version':VERSION,'status':'complete' if not missing and not invalid else 'incomplete',
      'plan_sha256':core.digest(plan),'case_id':case['case_id'],'model':plan['model'],
      'question':case['question'],'target':case['target'],'hypotheses':case['hypotheses'],
      'planned_calls':len(plan['jobs']),'valid_calls':len(valid),'missing':missing,'invalid':invalid,
      'source_records':len(case['records']),'real_source_episodes':1 if case['kind']=='real_observational' else 0,'case_kind':case['kind'],'gold_available':False,
      'final_answers':finals,'arm_contrasts':contrasts,'review_counts':dict(counts),
      'target_judgment_coverage':judged/len(finals) if finals else None,
      'reviewed_target_drift_rate':(counts['off_target']+counts['mixed'])/judged if judged else None,
      'usage_by_arm':{k:dict(v) for k,v in usage.items()},'limitations':plan['limitations'],
      'interpretation':'No automatic accuracy or gain score. Evaluate explanations against sources. Outcome changes may be warranted; no-overlap source messages do not establish independence of the agent population.'}
    core.write(out/'summary.json',report);core.write(out/'answers.json',outputs)
    render_review(out,plan,valid,reviews)
    ids=[h['id'] for h in case['hypotheses']]
    lines=['# Session observer results','',case['question'],'',
      f'Valid calls: {len(valid)}/{len(plan["jobs"])}. Source messages: {len(case["records"])}. One selected session. No automatic factual accuracy.','',
      '| Repeat | Arm | '+' | '.join(ids)+' | Target review |',
      '|---:|---|'+'---:|'*len(ids)+'---|']
    for row in finals:
        probs=' | '.join(f'{row["probabilities"][hid]:.3f}' for hid in ids)
        lines.append(f'| {row["repeat"]} | {row["arm"]} | {probs} | {(row["review"] or {}).get("target","unreviewed")} |')
    lines+=['',report['interpretation'],'','Full final rationales and quotes are in summary.json. Every checkpoint answer is in answers.json.','The archive share_bundle.zip contains these files, the plan, review page, and saved API responses.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    bundle(out)
    print(f'{len(valid)}/{len(plan["jobs"])} valid calls. Open {out/"review.html"}; share {out/"share_bundle.zip"}.')
    return report

def render_review(out,plan,valid,reviews):
    jobs=[j for j in plan['jobs'] if j['variant']!='stem' and j['job_id'] in valid]
    random.Random(plan['seed']+403).shuffle(jobs)
    e=html.escape
    parts=['<!doctype html><html lang="en"><meta charset="utf-8"><title>Session target review</title><style>body{font:16px system-ui;max-width:1050px;margin:30px auto;padding:20px;background:#f5f7fa}section{background:white;border:1px solid #ccd3dd;padding:20px;margin:20px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}select,button,textarea{font:inherit;padding:8px}textarea{width:95%}</style><h1>Review the observer’s answer</h1><p>Judge its answer to the fixed question, not whether the agents eventually succeeded. Condition labels are hidden; source wording can still reveal context. Review is optional and makes no model calls.</p><ul><li>On target: distinguishes the fixed target named in the question, even if uncertain.</li><li>Off target: substitutes another artifact, actor, task or later event for the fixed target.</li><li>Mixed: conflates those targets. Uncertainty about multiple contributing causes is not, by itself, mixed.</li><li>Unjudgeable: the explanation does not allow a reliable target judgment.</li></ul><p>Support concerns whether the visible sources justify the answer’s inference, not whether a source merely exists. Agent reports of verification remain reports. Explain off-target/mixed labels in notes.</p><button onclick="save()">Download target_review.json</button>']
    for n,j in enumerate(jobs,1):
        r=reviews.get(j['job_id'],{})
        parts+=['<section data-job="'+j['job_id']+'"><h2>Item '+str(n)+'</h2>',
          '<p><b>Question:</b> '+e(j['public']['question'])+'</p><p><b>Target:</b> '+e(j['public']['target'])+'</p>',
          '<pre>'+e(json.dumps(valid[j['job_id']]['parsed'],indent=2,ensure_ascii=False))+'</pre>']
        for key,options in [('target',TARGET_LABELS),('support',SUPPORT_LABELS)]:
            parts.append('<label>'+key+': <select class="'+key+'">')
            for opt in options:parts.append('<option value="'+opt+'"'+(' selected' if r.get(key,'unreviewed')==opt else '')+'>'+opt.replace('_',' ')+'</option>')
            parts.append('</select></label> ')
        parts+=['<p><textarea class="notes" placeholder="Explanation and source IDs">'+e(r.get('notes',''))+'</textarea></p>',
          '<details><summary>Visible source evidence and hypotheses</summary><pre>'+e(json.dumps(j['public'],indent=2,ensure_ascii=False))+'</pre></details></section>']
    parts.append('<script>function save(){const answers=[...document.querySelectorAll("section")].map(s=>({job_id:s.dataset.job,target:s.querySelector(".target").value,support:s.querySelector(".support").value,notes:s.querySelector(".notes").value}));if(answers.some(a=>["off_target","mixed"].includes(a.target)&&!a.notes.trim())){alert("Please explain every off-target/mixed label in notes.");return;}const blob=new Blob([JSON.stringify({plan_sha256:'+json.dumps(core.digest(plan))+',answers},null,2)],{type:"application/json"});const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="target_review.json";a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}</script></html>')
    (out/'review.html').write_text(''.join(parts),encoding='utf-8')

def bundle(out):
    names=['plan.json','manifest.json','summary.json','RESULTS.md','answers.json','review.html','reviewed_dataset.json']
    paths=[out/n for n in names if (out/n).exists()]+sorted((out/'responses').glob('*.json'))
    with zipfile.ZipFile(out/'share_bundle.zip','w',zipfile.ZIP_DEFLATED) as z:
        for path in paths:z.write(path,path.relative_to(out).as_posix())

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
    r=sub.add_parser('run');r.add_argument('--case',type=Path,required=True)
    r.add_argument('--model',required=True);r.add_argument('--repeats',type=int,default=1)
    r.add_argument('--seed',type=int,default=261004);r.add_argument('--max-output-tokens',type=int,default=4096)
    r.add_argument('--max-calls',type=int,default=24);r.add_argument('--out',type=Path,required=True)
    r.add_argument('--execute',action='store_true')
    a=sub.add_parser('analyze');a.add_argument('--out',type=Path,required=True);a.add_argument('--review',type=Path)
    args=p.parse_args()
    try:
        if args.cmd=='run':run(args)
        else:analyze(args.out,args.review)
    except (ValueError,KeyError,TypeError,RuntimeError,OSError,AssertionError) as exc:
        print('ERROR: '+str(exc),file=sys.stderr);return 1
    return 0

if __name__=='__main__':sys.exit(main())
