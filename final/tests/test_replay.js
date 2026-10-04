'use strict';
const assert=require('node:assert/strict');const fs=require('node:fs');const path=require('node:path');
const {viewMessages,messageCheckpoint}=require('../demo/app.js');
const data=JSON.parse(fs.readFileSync(path.join(__dirname,'../demo/replay_data.json'),'utf8'));
let checked=0;
for(const c of data.cases){
 const seen=[];
 for(let n=1;n<=6;n++){
  const prefix=viewMessages(c,n,'all',''),newly=viewMessages(c,n,'new','');
  assert.equal(prefix.length,c.checkpoints[n-1].cutoff_seq);seen.push(...newly.map(r=>r.id));
  assert.deepEqual(seen,prefix.map(r=>r.id));
  for(const j of c.jobs.filter(j=>j.checkpoint==='c'+n)){
   assert(c.arms.includes(j.arm));assert.equal(Object.keys(j.probabilities).length,4);
   for(const e of j.answer.evidence){const r=prefix.find(r=>r.id===e.source_id);assert(r);assert(r.text.includes(e.quote));assert(messageCheckpoint(c,r.id)<=n);checked++;}
  }
 }
 assert.equal(new Set(seen).size,c.records.length);
 assert.equal(viewMessages(c,1,'all','no-such-term-975421').length,0);
 assert.deepEqual(viewMessages(c,1,'all',c.records[0].id).map(r=>r.id),[c.records[0].id]);
}
const original=data.cases.find(c=>c.id==='original'),label=data.cases.find(c=>c.id==='label');
assert.equal(original.arms.length,3);assert.equal(original.jobs.length,18);assert.equal(label.arms.length,4);assert.equal(label.jobs.length,24);
assert.equal(original.jobs.find(j=>j.arm==='fresh_prefix'&&j.checkpoint==='c5').probabilities.synthetic_script,.85);
assert.equal(original.jobs.find(j=>j.arm==='fresh_prefix'&&j.checkpoint==='c6').probabilities.native_judgment,.85);
assert.equal(checked,252);
console.log('PASS: both case prefixes; new-message partition; filters; 252 quote links; 18/24 answers; original/recap distinction.');
