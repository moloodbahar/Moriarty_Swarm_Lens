#!/usr/bin/env python3
"""Revalidate the historical label run and supplied review without model calls."""
import argparse,collections
from pathlib import Path
import moriarty as core
import transfer,review_label_case as review

def export(run,review_path):
    plan=transfer.load_plan(run);case=plan['cases'][0]
    valid,missing,invalid=review.validated_outputs(run,plan)
    if missing or invalid:raise ValueError(f'Run incomplete: {len(missing)} missing, {len(invalid)} invalid.')
    labels=review.validate_review(core.read(review_path),plan,valid)
    jobs=[];counts=collections.defaultdict(collections.Counter);quotes=0;usage=collections.Counter();models=set()
    for job in plan['jobs']:
        record=valid[job['job_id']];answer=record['parsed'];row=labels.get(job['job_id'],{})
        quotes+=len(answer['evidence']);models.add(record['response'].get('model'))
        for k in ('input_tokens','output_tokens'):usage[k]+=record['response'].get('usage',{}).get(k,0)
        for k in review.LABELS:counts[job['arm']][k+':'+row.get(k,'unreviewed')]+=1
        # Public export contains numeric results and source IDs, not transcript text.
        jobs.append({'job_id':job['job_id'],'arm':job['arm'],'checkpoint':job['checkpoint_id'],
          'probabilities':answer['probabilities'],'review':{k:row.get(k,'unreviewed') for k in review.LABELS},
          'citation_source_ids':[e['source_id'] for e in answer['evidence']]})
    return {'schema':'moriarty-public-results-v1','plan_sha256':core.digest(plan),
      'case_id':case['case_id'],'records_sha256':case['records_sha256'],
      'model_requested':plan['model'],'models_reported':sorted(models),
      'source_messages':len(case['records']),'checkpoints':case['checkpoints'],
      'checkpoint_notes':case['checkpoint_review_notes'],'hypotheses':case['hypotheses'],
      'question':case['question'],'target':case['target'],'valid_calls':len(valid),
      'exact_visible_evidence_entries':quotes,'reviewed_outputs':len(labels),
      'review_counts':{k:dict(v) for k,v in counts.items()},'usage':dict(usage),
      'jobs':jobs,'gold_available':False,'independent_episodes_in_this_run':1,
      'limits':['One submitted review pass; no second-rater adjudication.',
        'The ledger c4 no-overclaim note explains consistency, not inference support; retain the label but do not infer a ledger benefit.',
        'Valid quotes do not establish valid inferences. Hypotheses partially overlap.',
        'Public export omits raw transcripts. Full verification requires the original authorized run bundle.',
        'Original requests used the historical schema. New session runner caps evidence at six from its first call.',
        'The supplied bundle does not establish how many failed or discarded attempts occurred.']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True)
    p.add_argument('--review',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    try:
        result=export(a.run,a.review);core.write(a.out,result)
        print(f'{result["valid_calls"]}/24 valid outputs; {result["exact_visible_evidence_entries"]} exact visible evidence entries; {result["reviewed_outputs"]} reviews. Zero model calls.')
    except (ValueError,OSError,TypeError,KeyError,AssertionError) as e:p.exit(1,'ERROR: '+str(e)+'\n')
if __name__=='__main__':main()
