import argparse,contextlib,io,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import session as t
import prepare_session as prep

class SessionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.input=t.ROOT/'examples/earthquake_session.jsonl';self.spec=t.core.read(t.ROOT/'examples/earthquake_question.json')
  self.case=prep.build(self.input,self.spec);self.casepath=self.root/'case.json';t.core.write(self.casepath,self.case)
  self.plan=t.make_plan(self.case,'MOCK')
 def args(self,out):return argparse.Namespace(case=self.casepath,model='MOCK',repeats=1,seed=261004,max_output_tokens=4096,max_calls=24,out=out,execute=True)
 def fake(self,payload):
  public=json.loads(payload['input'][-1]['content']);ids=[h['id'] for h in public['hypotheses']]
  answer={'probabilities':dict.fromkeys(ids,.25),'rationale':'Offline mock, not an experimental answer.',
   'evidence':[{'span_id':public['citation_spans'][0]['span_id'],'hypothesis_id':ids[0],'relation':'context'}],
   'unresolved':['Mock answer'],'next_observation':'Inspect original alert source.'}
  return {'status':'completed','model':'MOCK','usage':{'input_tokens':2,'output_tokens':1},'output':[{'content':[{'type':'output_text','text':json.dumps(answer)}]}]}
 def test_no_future_gold_or_interpretation_leak_and_cap(self):
  for j in self.plan['jobs']:
   prior=[{'checkpoint_id':'c1','parsed':{'rationale':'PRIVATE_PRIOR_ANSWER'}} for _ in j['parent_job_ids']]
   payload=t.payload_for(self.plan,j,prior);serialized=json.dumps(payload)
   self.assertNotIn('gold_hypothesis',serialized);self.assertNotIn('provenance',serialized)
   self.assertEqual(payload['text']['format']['schema']['properties']['evidence']['maxItems'],6)
   self.assertEqual(len(j['public']['visible_records']),int(j['checkpoint_id'][1:]))
   if j['checkpoint_id']!='c6':self.assertNotIn(self.case['records'][-1]['text'],serialized)
   if j['arm'] in ('fresh_prefix','evidence_recap'):self.assertNotIn('PRIVATE_PRIOR_ANSWER',serialized)
  recap=next(j for j in self.plan['jobs'] if j['arm']=='evidence_recap' and j['checkpoint_id']=='c6')
  payload=t.payload_for(self.plan,recap,[])
  self.assertEqual([r['seq'] for r in json.loads(payload['input'][0]['content'])['earlier_checkpoint_source_recap']],[1,2,3,4,5])
 def test_full_mock_resume_review_and_no_fake_gold_metric(self):
  out=self.root/'run'
  with patch.dict(os.environ,{'OPENAI_API_KEY':'TEST_ONLY'}),patch.object(t.core,'api_call',side_effect=self.fake) as api,contextlib.redirect_stdout(io.StringIO()):
   t.run(self.args(out));t.run(self.args(out));self.assertEqual(api.call_count,24)
  report=t.core.read(out/'summary.json');self.assertEqual(report['valid_calls'],24);self.assertEqual(report['real_source_episodes'],0)
  self.assertFalse(report['gold_available']);self.assertEqual(len(t.core.read(out/'answers.json')),24)
  review={'plan_sha256':t.core.digest(t.core.read(out/'plan.json')),'answers':[{'job_id':report['final_answers'][0]['job_id'],'target':'on_target','support':'unclear','notes':'Mock review'}]}
  rp=self.root/'review.json';t.core.write(rp,review)
  with contextlib.redirect_stdout(io.StringIO()):t.analyze(out,rp)
  self.assertTrue((out/'reviewed_dataset.json').exists())
  review['plan_sha256']='tampered';t.core.write(rp,review)
  with self.assertRaises(ValueError):t.analyze(out,rp)
 def test_invalid_response_saved_stops_and_is_not_retried(self):
  def bad(payload):
   r=self.fake(payload);a=json.loads(r['output'][0]['content'][0]['text']);a['evidence']*=7;r['output'][0]['content'][0]['text']=json.dumps(a);return r
  out=self.root/'run'
  with patch.dict(os.environ,{'OPENAI_API_KEY':'TEST_ONLY'}),patch.object(t.core,'api_call',side_effect=bad) as api:
   with self.assertRaises(ValueError):t.run(self.args(out))
   with self.assertRaises(ValueError):t.run(self.args(out))
   self.assertEqual(api.call_count,1)
  self.assertEqual(len(list((out/'responses').glob('*.json'))),1)
 def test_tampered_request_and_budget_rejected(self):
  out=self.root/'run';args=self.args(out);args.max_calls=23
  with patch.object(t.core,'api_call') as api:
   with self.assertRaises(ValueError):t.run(args)
   self.assertEqual(api.call_count,0)
  args.max_calls=24
  with patch.dict(os.environ,{'OPENAI_API_KEY':'TEST_ONLY'}),patch.object(t.core,'api_call',side_effect=self.fake),contextlib.redirect_stdout(io.StringIO()):t.run(args)
  p=next((out/'responses').glob('*.json'));r=t.core.read(p);r['request_sha256']='tampered';t.core.write(p,r)
  with patch.dict(os.environ,{'OPENAI_API_KEY':'TEST_ONLY'}),patch.object(t.core,'api_call') as api,contextlib.redirect_stdout(io.StringIO()):
   with self.assertRaises(ValueError):t.run(args)
   self.assertEqual(api.call_count,0)
 def test_input_sorting_timezone_duplicates_and_mixed_rooms(self):
  rows=[json.loads(l) for l in self.input.read_text().splitlines()];p=self.root/'input.jsonl'
  def save():p.write_text('\n'.join(json.dumps(r) for r in rows))
  rows.reverse();save();self.assertEqual(prep.build(p,self.spec)['records'][0]['id'],'m1')
  rows[0]['time']=rows[0]['time'].removesuffix('Z');save()
  with self.assertRaises(ValueError):prep.build(p,self.spec)
  self.assertEqual(prep.build(p,self.spec,assume_utc=True)['provenance']['assumed_utc_rows'],1)
  rows[0]['time']+='Z';rows[0]['session_id']='other';save()
  with self.assertRaises(ValueError):prep.build(p,self.spec)
  rows[0]['session_id']='fictional-earthquake';rows[0]['id']=rows[1]['id'];save()
  with self.assertRaises(ValueError):prep.build(p,self.spec)
 def test_dry_run_zero_calls_and_changed_plan_rejected(self):
  out=self.root/'run';args=self.args(out);args.execute=False
  with patch.object(t.core,'api_call') as api,contextlib.redirect_stdout(io.StringIO()):t.run(args);self.assertEqual(api.call_count,0)
  bad=t.core.read(out/'plan.json');bad['cases'][0]['question']='Changed';t.core.write(out/'plan.json',bad)
  with self.assertRaises(ValueError):t.load_plan(out)
if __name__=='__main__':unittest.main()
