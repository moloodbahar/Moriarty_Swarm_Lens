import argparse
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import followup as f

class FollowupTests(unittest.TestCase):
    def setUp(self):
        self.case=f.load_cases('real',f.ROOT/'data/ai_village_case_v2.json')[0]
        self.plan=f.make_plan([self.case],'MOCK',list(f.ARMS),list(f.VARIANTS),1,261004,4096,'real')

    def test_call_count_shared_stem_and_forks(self):
        self.assertEqual(self.plan['selected_calls'],36)
        self.assertEqual(sum(j['variant']=='stem' for j in self.plan['jobs']),20)
        jobs={j['job_id']:j for j in self.plan['jobs']}
        for arm in f.ARMS:
            branches=[j for j in jobs.values() if j['arm']==arm and j['variant']!='stem']
            self.assertEqual(len({tuple(j['parent_job_ids']) for j in branches}),1)
            for b in branches:
                self.assertEqual([jobs[x]['checkpoint_id'] for x in b['parent_job_ids']],['c1','c2','c3','c4','c5'])
                self.assertTrue(all(jobs[x]['arm']==arm and jobs[x]['variant']=='stem' for x in b['parent_job_ids']))

    def test_observed_payload_matches_frozen_runner(self):
        legacy=f.core.make_plan(self.case,'MOCK',1,0,261004,4096)
        history=[{'checkpoint_id':f'c{i}','parsed':{'probabilities':{'a':1}}} for i in range(1,6)]
        for arm in f.core.ARMS:
            j=next(j for j in self.plan['jobs'] if j['arm']==arm and j['variant']=='observed')
            old=next(j for j in legacy['jobs'] if j['arm']==arm and j['checkpoint_id']=='c6')
            self.assertEqual(f.payload_for(self.plan,j,history),f.core.request_payload(legacy,old,history))

    def test_ablation_retains_source_span_identity(self):
        observed=next(j['public'] for j in self.plan['jobs'] if j['variant']=='observed')
        bank={s['span_id']:s for s in observed['citation_spans']}
        for variant,removed in [('omit_replacement_updates',f.REMOVE_REPLACEMENT),('omit_context_updates',f.REMOVE_CONTEXT)]:
            public=next(j['public'] for j in self.plan['jobs'] if j['variant']==variant)
            self.assertEqual(len(public['visible_records']),17)
            self.assertTrue(all(r['seq'] not in removed for r in public['visible_records']))
            self.assertEqual(public['citation_spans'],[bank[s['span_id']] for s in public['citation_spans']])
            self.assertIn('e6_1',bank)
            self.assertIn('e6_1',{s['span_id'] for s in public['citation_spans']})

    def test_no_future_sources_or_private_labels_in_stem(self):
        for j in self.plan['jobs']:
            if j['variant']!='stem':continue
            cp=next(c for c in self.case['checkpoints'] if c['id']==j['checkpoint_id'])
            self.assertTrue(all(r['seq']<=cp['cutoff_seq'] for r in j['public']['visible_records']))
            self.assertNotIn('artifact_reference_guide',j['public'])
            self.assertNotIn('gold_hypothesis',json.dumps(j['public']))
        for c in f.controlled_cases():
            order=[h['id'] for h in c['hypotheses']]
            p=f.public_variant(c,c['checkpoints'][0],order,'stem')
            self.assertNotIn('control_mode',json.dumps(p));self.assertNotIn('gold_hypothesis',json.dumps(p))
            self.assertNotIn(c['records'][-1]['text'],json.dumps(p))

    def test_recap_has_source_statements_not_prior_opinions(self):
        j=next(j for j in self.plan['jobs'] if j['arm']=='evidence_recap' and j['variant']=='observed')
        parents=[{'checkpoint_id':f'c{i}','parsed':{'rationale':'PRIVATE_PRIOR_OPINION'}} for i in range(1,6)]
        payload=f.payload_for(self.plan,j,parents)
        self.assertNotIn('PRIVATE_PRIOR_OPINION',json.dumps(payload))
        recap=json.loads(payload['input'][0]['content'])['earlier_checkpoint_source_recap']
        self.assertEqual([r['seq'] for r in recap],[3,4,5,6,8])
        self.assertTrue(all(r in j['public']['visible_records'] for r in recap))

    def test_controls_require_staying_or_revising(self):
        cases=f.controlled_cases()
        self.assertEqual(len(cases),4)
        for initial in ('native_judgment','synthetic_script'):
            pair=[c for c in cases if c['initial_reported_hypothesis']==initial]
            self.assertEqual(pair[0]['records'][:5],pair[1]['records'][:5])
        for c in cases:
            same=c['gold_hypothesis']==c['initial_reported_hypothesis']
            self.assertEqual(same,c['control_mode']=='replacement')

    def test_annotations_do_not_mutate_source(self):
        before=f.core.digest(self.case)
        j=next(j for j in self.plan['jobs'] if j['variant']=='artifact_labels')
        self.assertEqual(j['public']['visible_records'],next(x['public']['visible_records'] for x in self.plan['jobs'] if x['variant']=='observed'))
        self.assertEqual(before,f.core.digest(self.case))

    def fake_api(self,payload):
        public=json.loads(payload['input'][-1]['content'])
        ids=[h['id'] for h in public['hypotheses']]
        answer={'probabilities':dict.fromkeys(ids,.25),'rationale':'Mock response for offline test only.',
          'evidence':[{'span_id':public['citation_spans'][0]['span_id'],'hypothesis_id':ids[0],'relation':'context'}],
          'unresolved':['Mock output'],'next_observation':'Audit original artifact.'}
        return {'status':'completed','usage':{'input_tokens':1,'output_tokens':1},
          'output':[{'content':[{'type':'output_text','text':json.dumps(answer)}]}]}

    def args(self,out):
        return argparse.Namespace(suite='real',case=f.ROOT/'data/ai_village_case_v2.json',model='MOCK',
          arms=','.join(f.ARMS),variants=','.join(f.VARIANTS),repeats=1,seed=261004,
          max_output_tokens=4096,max_calls=36,out=out,execute=True)

    def test_full_run_resume_review_and_unknown_denominator(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'run';args=self.args(out)
            with patch.dict(f.os.environ,{'OPENAI_API_KEY':'unit-test-placeholder'}),patch.object(f.core,'api_call',side_effect=self.fake_api) as api:
                f.run(args);self.assertEqual(api.call_count,36)
                f.run(args);self.assertEqual(api.call_count,36)
            result=f.core.read(out/'summary.json')
            self.assertEqual(result['valid_calls'],36);self.assertEqual(len(result['final_answers']),16)
            self.assertEqual(result['target_judgment_coverage'],0)
            review_html=(out/'review.html').read_text()
            self.assertNotIn('fresh_prefix',review_html);self.assertNotIn('evidence_ledger',review_html)
            final=result['final_answers'][0]
            review={'plan_sha256':f.core.digest(f.core.read(out/'plan.json')),
              'answers':[{'job_id':final['job_id'],'target':'unjudgeable','support':'unclear','notes':'Ambiguous.'}]}
            p=Path(tmp)/'review.json';f.core.write(p,review)
            result=f.analyze(out,p)
            self.assertEqual(result['target_judgment_coverage'],0)
            self.assertEqual(result['review_counts']['unjudgeable'],1)
            review['answers'][0]['target']='mixed';review['answers'][0]['notes']=''
            f.core.write(p,review)
            with self.assertRaises(ValueError):f.analyze(out,p)

    def test_budget_stops_before_any_api_or_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            args=self.args(Path(tmp)/'absent');args.max_calls=35
            with patch.object(f.core,'api_call') as api:
                with self.assertRaises(ValueError):f.run(args)
                self.assertEqual(api.call_count,0);self.assertFalse(args.out.exists())

    def test_network_failure_saves_completed_jobs(self):
        with tempfile.TemporaryDirectory() as tmp:
            args=self.args(Path(tmp)/'run');n=[0]
            def fail(payload):
                n[0]+=1
                if n[0]==2:raise RuntimeError('test network failure')
                return self.fake_api(payload)
            with patch.dict(f.os.environ,{'OPENAI_API_KEY':'unit-test-placeholder'}),patch.object(f.core,'api_call',side_effect=fail):
                with self.assertRaises(RuntimeError):f.run(args)
            self.assertEqual(len(list((args.out/'responses').glob('*.json'))),1)
            self.assertFalse((args.out/'.running').exists())
            self.assertEqual(f.core.read(args.out/'manifest.json')['status'],'stopped')

    def test_statistics_are_repeat_pairs_not_new_cases(self):
        result=f.paired_summary([-.5,-.25,0,.25,.5])
        self.assertEqual(result['paired_repeats'],5)
        self.assertEqual(result['mean_difference'],0)
        self.assertIsNotNone(result['within_case_bootstrap_95_interval'])
        self.assertIsNone(f.paired_summary([.1])['within_case_bootstrap_95_interval'])

    def test_review_rates_exclude_unknown_and_fixture_ties(self):
        rows=[{'review':{'target':label}} for label in ('on_target','off_target','mixed','unjudgeable','unreviewed')]
        result=f.condition_summary(rows,self.case)
        self.assertEqual(result['target_judgment_coverage'],3/5)
        self.assertEqual(result['target_drift_rate'],2/3)
        self.assertIsNone(result['fixture_gold_metrics'])
        self.assertIsNone(f.condition_summary([{'review':None}],self.case)['target_drift_rate'])
        c=f.controlled_cases()[0]
        p=dict.fromkeys([h['id'] for h in c['hypotheses']],.25)
        row={'review':None,'probabilities':p,'trajectory':{'steps':[{'brier':.75}]}}
        metrics=f.condition_summary([row],c)['fixture_gold_metrics']
        self.assertEqual(metrics['unique_top_accuracy'],0)
        self.assertEqual(metrics['mean_final_brier'],.75)

if __name__=='__main__':unittest.main()
