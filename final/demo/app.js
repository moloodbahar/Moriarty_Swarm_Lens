(function(){
'use strict';
function viewMessages(c,checkpoint,mode,search){
 const n=Number(checkpoint),upper=c.checkpoints[n-1].cutoff_seq,lower=mode==='new'&&n>1?c.checkpoints[n-2].cutoff_seq:0;
 const q=String(search||'').toLowerCase();return c.records.filter(r=>r.seq>lower&&r.seq<=upper&&(!q||[r.text,r.speaker,r.id,r.time].join(' ').toLowerCase().includes(q)));
}
function messageCheckpoint(c,id){const r=c.records.find(x=>x.id===id);return r?c.checkpoints.findIndex(cp=>cp.cutoff_seq>=r.seq)+1:0;}
if(typeof module!=='undefined'&&module.exports)module.exports={viewMessages,messageCheckpoint};
if(typeof document==='undefined')return;
const replay=JSON.parse(document.getElementById('replay-data').textContent);
const cases=Object.fromEntries(replay.cases.map(c=>[c.id,c]));
const names={fresh_prefix:['Fresh reader','All current source messages; no earlier answers.'],persistent_history:['Answer history','Same messages, plus its own earlier answers.'],evidence_ledger:['Evidence ledger','History, plus instructions to check alternatives and contradictions.'],evidence_recap:['Source recap','Same messages, plus repeated earlier source records; no previous answers.']};
const short={independent_rescoring:'Separate rescoring',reused_per_response:'Reuse per response',joint_context_consistency:'Shared-context consistency',other_process:'Other process',native_judgment:'Native judgment',synthetic_script:'Synthetic script',delegated_judgment:'Delegated judgment'};
let current='original',arm='fresh_prefix',selected=null,highlight='';
const el=id=>document.getElementById(id),slider=el('checkpoint');
function node(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
function c(){return cases[current];}
function job(){return c().jobs.find(j=>j.arm===arm&&j.checkpoint==='c'+slider.value);}
function pct(p){return Math.round(p*100)+'%';}
function setCase(id,checkpoint){current=id;slider.value=checkpoint||1;arm='fresh_prefix';selected=null;highlight='';el('message-mode').value='new';el('message-search').value='';render();}
function render(){
 const data=c(),n=Number(slider.value),stage=data.checkpoint_notes[n-1];
 for(const id of Object.keys(cases))el('case-'+id).setAttribute('aria-pressed',String(id===current));
 el('fact-messages').textContent=data.records.length;el('fact-design').textContent=data.arms.length+' × 6';el('fact-citations').textContent=data.evidence_entries+' / '+data.evidence_entries;el('fact-review').textContent=data.review_summary;el('fact-review-caption').textContent=data.review_caption;
 el('case-kind').textContent=data.kind+' · no process gold label';el('case-title').textContent=data.title;el('case-description').textContent=data.description;el('case-question').textContent=data.question;el('case-target').textContent=data.target;el('case-limits').textContent=data.limits;el('case-takeaway').textContent=data.takeaway;el('source-run').href=data.original_run_url;
 el('slider-label').textContent='Checkpoint '+n+' of 6';el('prev').disabled=n===1;el('next').disabled=n===6;
 el('stage').replaceChildren(node('b','C'+n+' · '+stage.cutoff_seq+' messages visible'),node('p',stage.stage),node('p',stage.interpretation_limit,'note'));
 const cards=el('cards');cards.replaceChildren();cards.style.setProperty('--observer-count',data.arms.length);
 for(const a of data.arms){const j=data.jobs.find(x=>x.arm===a&&x.checkpoint==='c'+n),hids=data.hypotheses.map(h=>h.id),top=hids.reduce((x,y)=>j.probabilities[x]>=j.probabilities[y]?x:y);const card=node('article',undefined,'card');card.dataset.arm=a;card.setAttribute('aria-current',String(a===arm));card.append(node('h3',names[a][0]),node('p',names[a][1]),node('div',short[top]||top,'choice'),node('div',pct(j.probabilities[top]),'confidence'));
  for(const hid of hids){const row=node('div',undefined,'meter-row'),label=node('div',undefined,'meter-label'),track=node('div',undefined,'track'),fill=node('div',undefined,'fill');label.append(node('span',short[hid]||hid),node('span',pct(j.probabilities[hid])));fill.style.width=j.probabilities[hid]*100+'%';track.append(fill);row.append(label,track);card.append(row);}
  const button=node('button','Read this answer','read-answer secondary');button.addEventListener('click',()=>{arm=a;render();el('answer-title').scrollIntoView({behavior:'smooth',block:'start'});});card.append(button);cards.append(card);
 }
 const defs=el('hypothesis-definitions');defs.replaceChildren();for(const h of data.hypotheses){const p=node('p');p.append(node('b',(short[h.id]||h.id)+': '),document.createTextNode(h.description));defs.append(p);}
 const table=node('table'),head=node('thead'),row=node('tr');row.append(node('th','Setup'));for(const h of data.hypotheses)row.append(node('th',short[h.id]||h.id));head.append(row);table.append(head);const body=node('tbody');for(const a of data.arms){const j=data.jobs.find(x=>x.arm===a&&x.checkpoint==='c6'),tr=node('tr');tr.append(node('td',names[a][0]));for(const h of data.hypotheses)tr.append(node('td',pct(j.probabilities[h.id])));body.append(tr);}table.append(body);el('final-table').replaceChildren(table);
 renderMessages();renderAnswer();
}
function renderMessages(){
 const data=c(),n=Number(slider.value),prior=n>1?data.checkpoints[n-2].cutoff_seq:0,upper=data.checkpoints[n-1].cutoff_seq;
 const records=viewMessages(data,n,el('message-mode').value,el('message-search').value);el('message-count').textContent='Showing '+records.length+' messages · '+(upper-prior)+' newly available · '+upper+' available in total.';
 const list=el('conversation');list.replaceChildren();
 if(!records.length)list.append(node('p','No messages match this filter at this checkpoint.','empty'));
 for(const r of records){const article=node('article',undefined,'message'+(r.seq>prior?' is-new':'')+(r.id===selected?' is-selected':''));article.id='message-'+r.id;article.dataset.seq=r.seq;const header=node('div',undefined,'message-header');header.append(node('b','#'+r.seq+' · '+r.speaker),node('time',r.time));article.append(header);if(r.seq>prior)article.append(node('span','New at this checkpoint','new-tag'));const p=node('div',undefined,'message-text');const pos=r.id===selected&&highlight?r.text.indexOf(highlight):-1;if(pos>=0){p.append(document.createTextNode(r.text.slice(0,pos)),node('mark',highlight),document.createTextNode(r.text.slice(pos+highlight.length)));}else p.textContent=r.text;article.append(p,node('div','Source ID: '+r.id,'message-id'));list.append(article);}
}
function jump(id,quote){const r=c().records.find(x=>x.id===id);if(!r||r.seq>c().checkpoints[Number(slider.value)-1].cutoff_seq)return;selected=id;highlight=quote||'';el('message-mode').value='all';el('message-search').value='';renderMessages();const target=el('message-'+id);if(target)target.scrollIntoView({behavior:'smooth',block:'center'});}
function renderAnswer(){const j=job(),data=c(),box=el('answer');el('answer-title').textContent=names[arm][0]+' · '+j.checkpoint.toUpperCase();box.replaceChildren(node('p',j.answer.rationale,'answer-rationale'),node('p','Saved model answer. Wording may overstate what the messages establish.','answer-note'),node('h4','Quoted evidence'));
 for(const e of j.answer.evidence){const r=data.records.find(x=>x.id===e.source_id),part=node('div',undefined,'evidence'),button=node('button','Read #'+r.seq+' · '+r.speaker,'text-button');button.addEventListener('click',()=>jump(e.source_id,e.quote));part.append(node('div',e.relation+' → '+(short[e.hypothesis_id]||e.hypothesis_id),'evidence-label'),node('blockquote',e.quote),button);box.append(part);}
 if(!j.answer.evidence.length)box.append(node('p','No evidence entries in this answer.','note'));
 box.append(node('h4','What remains unresolved'));if(j.answer.unresolved.length){const ul=node('ul');for(const x of j.answer.unresolved)ul.append(node('li',x));box.append(ul);}else box.append(node('p','The observer listed none. This is not proof that nothing remains unknown.','answer-note'));
 box.append(node('h4','Observer’s proposed next observation'),node('p',j.answer.next_observation,'answer-rationale'));
}
function download(value,name){const u=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'})),a=node('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}
for(const id of Object.keys(cases))el('case-'+id).addEventListener('click',()=>setCase(id));
slider.addEventListener('input',()=>{selected=null;highlight='';render();});
el('prev').addEventListener('click',()=>{slider.value=Math.max(1,Number(slider.value)-1);selected=null;highlight='';render();});
el('next').addEventListener('click',()=>{slider.value=Math.min(6,Number(slider.value)+1);selected=null;highlight='';render();});
el('message-mode').addEventListener('change',renderMessages);el('message-search').addEventListener('input',renderMessages);
el('download-case').addEventListener('click',()=>download(c(),'moriarty_'+current+'_replay.json'));
el('download').addEventListener('click',()=>download(cases.label,'moriarty_label_replay.json'));
for(const b of document.querySelectorAll('[data-original-seq]'))b.addEventListener('click',()=>{const r=cases.original.records.find(x=>x.seq===Number(b.dataset.originalSeq));setCase('original',messageCheckpoint(cases.original,r.id));jump(r.id);});
render();
})();
