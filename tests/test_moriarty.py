import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import argparse
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import moriarty as m

def output(ids, source=None):
    return {'probabilities':{i:.25 for i in ids}, 'rationale':'Insufficient evidence.',
      'evidence':[] if source is None else [{'source_id':source['id'],'quote':source['text'],
        'hypothesis_id':ids[0],'relation':'context'}], 'unresolved':['Process unverified.'],
      'next_observation':'Audit the score script.'}

class Tests(unittest.TestCase):
    def setUp(self):
        self.case=m.load_case(m.ROOT/'data/ai_village_case.json')
        self.ids=[h['id'] for h in self.case['hypotheses']]
        self.cp=self.case['checkpoints'][0]
        self.visible=m.public_prefix(self.case,self.cp,self.ids)['visible_records']

    def test_real_case_no_gold(self):
        self.assertIsNone(self.case['gold_hypothesis'])
        r=m.trajectory_metrics([output(self.ids)],None,None,.8)
        self.assertNotIn('q',r['steps'][0]);self.assertIsNone(r['longest_committed_wrong_run'])

    def test_future_and_gold_never_in_prompt(self):
        fixture=m.load_case(m.ROOT/'data/fixtures/deadline_appearance.json')
        public=m.public_prefix(fixture,fixture['checkpoints'][0],[h['id'] for h in fixture['hypotheses']])
        s=json.dumps(public)
        self.assertNotIn('gold_hypothesis',s)
        self.assertNotIn(fixture['records'][-1]['text'],s)
        self.assertEqual(len(public['visible_records']),1)

    def test_future_evidence_rejected(self):
        o=output(self.ids,self.case['records'][-1])
        self.assertIn('Unknown or future source ID',m.validate_output(o,self.visible,self.ids))

    def test_fabricated_quote_rejected(self):
        o=output(self.ids,self.visible[0]);o['evidence'][0]['quote']='fabricated quote'
        self.assertTrue(m.validate_output(o,self.visible,self.ids))

    def test_probability_nan_bool_sum_and_keys(self):
        for bad in [float('nan'), True, 1.1]:
            o=output(self.ids);o['probabilities'][self.ids[0]]=bad
            self.assertTrue(m.validate_output(o,self.visible,self.ids))
        o=output(self.ids);o['probabilities'][self.ids[0]]=.26
        self.assertTrue(m.validate_output(o,self.visible,self.ids))
        o=output(self.ids);o['probabilities']['invented']=o['probabilities'].pop(self.ids[0])
        self.assertTrue(m.validate_output(o,self.visible,self.ids))

    def test_exact_quote_passes_but_semantics_not_automated(self):
        o=output(self.ids,self.visible[0])
        o['evidence'][0]['relation']='supports' # Existence is not semantic entailment.
        self.assertEqual(m.validate_output(o,self.visible,self.ids),[])

    def test_same_prefix_and_order_all_arms(self):
        plan=m.make_plan(self.case,'TEST',2,2,7,4096)
        for repeat in range(2):
            for cp in ('c1','c2'):
                jobs=[j for j in plan['jobs'] if j['repeat']==repeat and j['checkpoint_id']==cp]
                self.assertEqual(len({j['evidence_sha256'] for j in jobs}),1)
                self.assertEqual(len({tuple(j['order']) for j in jobs}),1)
                self.assertEqual({j['arm'] for j in jobs},set(m.ARMS))

    def test_persistent_has_only_prior_judgments(self):
        plan=m.make_plan(self.case,'TEST',1,2,7,4096)
        old={'checkpoint_id':'c1','parsed':output(self.ids)}
        for job in plan['jobs']:
            payload=m.request_payload(plan,job,[old])
            self.assertEqual(len(payload['input']),1 if job['arm']=='fresh_prefix' else 3)
            self.assertFalse(payload['store']);self.assertEqual(payload['truncation'],'disabled')

    def test_capture_and_recovery_known_fixture(self):
        def p(values):return {'probabilities':dict(zip('abcd',values))}
        r=m.trajectory_metrics([p([.05,.85,.05,.05]),p([.1,.8,.05,.05]),p([.9,.04,.03,.03])],'a',2,.8)
        self.assertEqual(r['longest_committed_wrong_run'],2)
        self.assertEqual(r['recovery_lag'],0)
        self.assertAlmostEqual(r['steps'][-1]['brier'],.0134)

    def test_refusal_incomplete_invalid_json(self):
        for raw in [{'status':'incomplete'}, {'status':'completed','output':[{'content':[{'type':'refusal'}]}]},
                    {'status':'completed','output':[{'content':[{'type':'output_text','text':'not json'}]}]}]:
            with self.assertRaises(ValueError):m.extract_response(raw)

    def test_failure_preserves_earlier_calls_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            args=argparse.Namespace(case=m.ROOT/'data/ai_village_case.json',model='MOCK',repeats=1,
              checkpoints=2,seed=7,max_output_tokens=4096,out=Path(tmp)/'run',execute=True,threshold=.8)
            raw={'status':'completed','output':[{'content':[{'type':'output_text','text':json.dumps(output(self.ids))}]}]}
            with patch.dict(m.os.environ,{'OPENAI_API_KEY':'test-not-real'}), patch.object(m,'api_call',side_effect=[raw,RuntimeError('test failure')]):
                with self.assertRaises(RuntimeError):m.run(args)
            self.assertEqual(len(list((args.out/'responses').glob('*.json'))),1)
            with patch.dict(m.os.environ,{'OPENAI_API_KEY':'test-not-real'}),patch.object(m,'api_call',return_value=raw) as call:
                m.run(args);self.assertEqual(call.call_count,5)
            self.assertEqual(m.read(args.out/'manifest.json')['status'],'completed')

    def test_tampered_case_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            c=json.loads(json.dumps(self.case));c['records'][0]['text']+='tamper'
            p=Path(tmp)/'case.json';m.write(p,c)
            with self.assertRaises(AssertionError):m.load_case(p)

    def test_html_escapes_transcript_instructions(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);plan=m.make_plan(self.case,'MOCK',1,1,7,4096)
            m.write(folder/'plan.json',plan)
            j=plan['jobs'][0];j['public']['visible_records'][0]['text']='<script>alert(1)</script>'
            r={'parsed':output(self.ids)}
            m.make_dashboard(folder,self.case,[(j,r)],{})
            text=(folder/'dashboard.html').read_text()
            self.assertNotIn('<script>alert(1)</script>',text);self.assertIn('&lt;script&gt;',text)

if __name__=='__main__':unittest.main()
