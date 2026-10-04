#!/usr/bin/env python3
"""Convert an authorized, timestamped JSONL chat export into a six-checkpoint case."""
import argparse,datetime as dt,hashlib,json
from pathlib import Path
import moriarty as core

def build(input_path,spec,session=None,assume_utc=False):
    records=[];seen=set();sessions=set();assumed=0
    for line_number,line in enumerate(input_path.read_text(encoding='utf-8-sig').splitlines(),1):
        if not line.strip():continue
        envelope=json.loads(line);r=envelope.get('row',envelope)
        sid=r.get('session_id',r.get('room_id'))
        if session is not None and str(sid)!=session:continue
        if sid is not None:sessions.add(str(sid))
        rid=r.get('id');text=r.get('text',r.get('content'));time=r.get('time',r.get('created_at'))
        speaker=r.get('speaker') or r.get('agent_speaker_id') or r.get('user_speaker_id') or r.get('speaker_type')
        if not all(isinstance(v,str) and v.strip() for v in (rid,time,speaker)) or not isinstance(text,str):
            raise ValueError(f'Line {line_number}: require text id, time, speaker and text/content (null content is not supported).')
        if rid in seen:raise ValueError('Duplicate message ID: '+rid)
        seen.add(rid)
        stamp=dt.datetime.fromisoformat(time.replace('Z','+00:00'))
        if stamp.tzinfo is None:
            if not assume_utc:raise ValueError('Timezone missing. Declare --assume-utc only if appropriate for this export.')
            stamp=stamp.replace(tzinfo=dt.timezone.utc);assumed+=1
        if envelope.get('row_sha256'):
            checksum=hashlib.sha256(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            if checksum!=envelope['row_sha256']:raise ValueError('Source checksum mismatch: '+rid)
        records.append({'id':rid,'time':stamp.astimezone(dt.timezone.utc).isoformat(),
          'speaker':speaker,'text':text,'evidence_type':'recorded_statement',
          'original_time':time,'input_line':line_number})
    if len(sessions)>1 and session is None:raise ValueError('Multiple sessions present. Choose --session ROOM_ID.')
    records.sort(key=lambda r:(r['time'],r['id']))
    for i,r in enumerate(records,1):r['seq']=i
    cuts=spec['checkpoint_cutoffs']
    if len(cuts)!=6 or any(type(x)!=int for x in cuts) or cuts!=sorted(set(cuts)) or not records or cuts[0]<1 or cuts[-1]!=len(records):
        raise ValueError('Use six increasing integer checkpoint_cutoffs; the last must equal selected message count.')
    hs=spec['hypotheses']
    if len(hs)!=4 or len({h['id'] for h in hs})!=4 or any(not isinstance(h.get(k),str) or not h[k].strip() for h in hs for k in ('id','description')):
        raise ValueError('Supply four distinct hypothesis IDs with descriptions.')
    for key in ('case_id','question','target'):
        if not isinstance(spec.get(key),str) or not spec[key].strip():raise ValueError('Missing '+key)
    kind=spec.get('kind','real_observational')
    if kind not in ('real_observational','controlled_fixture'):raise ValueError('Invalid kind.')
    gold=spec.get('gold_hypothesis')
    if kind=='real_observational' and gold is not None:raise ValueError('No factual gold allowed for an unaudited observational case.')
    if kind=='controlled_fixture' and gold not in {h['id'] for h in hs}:raise ValueError('A fixture requires its scripted gold_hypothesis.')
    return {k:spec[k] for k in ('case_id','question','target')} | {
      'kind':kind,'hypotheses':hs,'records':records,'records_sha256':core.digest(records),
      'checkpoints':[{'id':f'c{i}','cutoff_seq':n} for i,n in enumerate(cuts,1)],
      'gold_hypothesis':gold,'diagnostic_checkpoint_id':None,
      'provenance':{'source_sha256':hashlib.sha256(input_path.read_bytes()).hexdigest(),
        'session':session,'assumed_utc_rows':assumed,'timestamp_meaning':'Message posting time; reported event times are not rewritten.',
        'selection':'User-supplied session and checkpoint cutoffs; not automatically an unseen case.'}}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--spec',type=Path,required=True)
    p.add_argument('--session');p.add_argument('--assume-utc',action='store_true');p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    try:
        if a.out.exists():raise ValueError('Output exists. Choose a new --out.')
        case=build(a.input,core.read(a.spec),a.session,a.assume_utc)
        core.write(a.out,case);core.load_case(a.out)
        print(f'{len(case["records"])} messages; six checkpoints; saved {a.out}. Zero API calls.')
    except (ValueError,KeyError,TypeError,OSError,AssertionError) as e:p.exit(1,'ERROR: '+str(e)+'\n')
if __name__=='__main__':main()
