import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import moriarty as m

class SpanTests(unittest.TestCase):
    def setUp(self):
        self.case=m.load_case(m.ROOT/'data/ai_village_case_v2.json')
        self.ids=[h['id'] for h in self.case['hypotheses']]
        self.public=m.public_prefix(self.case,self.case['checkpoints'][0],self.ids)

    def wire(self,span_id):
        return {'probabilities':dict.fromkeys(self.ids,.25),'rationale':'Uncertain.',
          'evidence':[{'span_id':span_id,'hypothesis_id':self.ids[0],'relation':'context'}],
          'unresolved':[],'next_observation':'Audit the original script.'}

    def test_exact_unicode_offsets_and_long_lines(self):
        source="  I’ll use `a.py`.\r\n"+'word '*240+'\n\nآخر متن 🙂'
        records=[{'seq':1,'id':'x','text':source}]
        spans=m.citation_spans(records)
        self.assertGreater(len(spans),3)
        for s in spans:
            self.assertEqual(s['text'],source[s['start']:s['end']])
            self.assertLessEqual(len(s['text']),500)
        self.assertIn('آخر متن 🙂',[s['text'] for s in spans])

    def test_reconstruction_and_strict_validation(self):
        span=self.public['citation_spans'][0]
        result,audit=m.resolve_citations(self.wire(span['span_id']),self.public)
        self.assertEqual(result['evidence'][0]['quote'],span['text'])
        self.assertEqual(audit[0]['source_id'],span['source_id'])
        self.assertEqual(m.validate_output(result,self.public['visible_records'],self.ids),[])

    def test_future_unknown_and_free_text_fail(self):
        for sid in ['invented','e6_1']:
            with self.assertRaises(ValueError):m.resolve_citations(self.wire(sid),self.public)
        wire=self.wire(self.public['citation_spans'][0]['span_id'])
        wire['evidence'][0]['quote']='shortened ... text'
        with self.assertRaises(ValueError):m.resolve_citations(wire,self.public)

    def test_catalog_stability_prefix_safety_and_enum(self):
        later=m.public_prefix(self.case,self.case['checkpoints'][3],self.ids)
        self.assertEqual(self.public['citation_spans'],later['citation_spans'][:len(self.public['citation_spans'])])
        schema=m.schema(self.ids,[s['span_id'] for s in self.public['citation_spans']])
        evidence=schema['properties']['evidence']['items']['properties']
        self.assertNotIn('quote',evidence)
        self.assertNotIn('e6_1',evidence['span_id']['enum'])

if __name__=='__main__':unittest.main()
