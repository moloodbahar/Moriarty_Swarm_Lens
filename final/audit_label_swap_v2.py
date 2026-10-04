#!/usr/bin/env python3
"""Read-only label-swap audit, pinned scores AND packets; Python 3.10+, stdlib.

Examples:
  py audit_label_swap_v2.py --snapshot artifacts/COMMIT --out results/audit.json
  py audit_label_swap_v2.py --repo research-2026-05 --rev COMMIT --out results/audit.json

No model calls. Exact equality describes artifacts, not the process that made them.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics as st
import subprocess

DIMS = ('correctness', 'completeness', 'clarity', 'creativity', 'constraint_adherence')
JUDGES = ('gpt-5.5', 'claude-opus-4.7', 'gemini-3.1-pro', 'kimi-k2.6')
BASE = 'experiments/replication-wave'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')

class Source:
    def __init__(self, snapshot=None, repo=None, rev='HEAD'):
        self.snapshot, self.repo, self.files = snapshot, repo, []
        if (snapshot is None) == (repo is None):
            raise ValueError('Choose exactly one of --snapshot or --repo.')
        if snapshot is not None:
            manifest = json.loads((Path(snapshot)/'snapshot_manifest.json').read_text(encoding='utf-8'))
            self.commit = manifest['commit']
            items = manifest['files']
            self.manifest = {x['path']: x for x in items}
            if len(self.manifest) != len(items):
                raise ValueError('Duplicate manifest paths.')
        else:
            self.commit = self.git('rev-parse', '--verify', '--end-of-options', rev+'^{commit}').decode().strip()
        if len(self.commit) != 40 or any(c not in '0123456789abcdef' for c in self.commit):
            raise ValueError('Expected a full Git commit SHA.')

    def git(self, *args):
        p = subprocess.run(['git', '-C', str(self.repo), *args], capture_output=True)
        if p.returncode:
            raise ValueError('Git lookup failed; verify repository, revision and file availability.')
        return p.stdout

    def read(self, path):
        if self.snapshot is not None:
            if path not in self.manifest:
                raise ValueError('File not declared in snapshot: '+path)
            raw = (Path(self.snapshot)/path).read_bytes()
            if sha(raw) != self.manifest[path]['sha256']:
                raise ValueError('Snapshot checksum mismatch: '+path)
        else:
            raw = self.git('show', self.commit+':'+path)
        self.files.append({'path': path, 'sha256': sha(raw), 'bytes': len(raw),
                           'commit': self.commit})
        return json.loads(raw.decode('utf-8-sig'))

def entries(obj):
    rows = obj['entries'] if isinstance(obj, dict) else obj
    if not isinstance(rows, list) or not rows:
        raise ValueError('Expected nonempty entry list.')
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError('Each entry must be an object.')
    return rows

def indexed(rows):
    result = {}
    for row in rows:
        bid = row.get('blind_id')
        if not isinstance(bid, str) or not bid or bid in result:
            raise ValueError('Missing or duplicate blind ID.')
        result[bid] = row
    return result

def parse_session(scored, packet, expected=40):
    scores, packets = indexed(entries(scored)), indexed(entries(packet))
    if scores.keys() != packets.keys():
        raise ValueError('Scored IDs do not exactly cover packet IDs; no rows may be silently dropped.')
    if len(scores) != expected:
        raise ValueError(f'Expected {expected} scored rows; found {len(scores)}.')
    pairs = {}
    for bid, p in packets.items():
        s = scores[bid]
        pid, text, label = p.get('prompt_id'), p.get('response_text'), p.get('displayed_label')
        if not all(isinstance(x, str) and x for x in (pid, text, label)):
            raise ValueError('Missing prompt, response text or displayed label.')
        if s.get('displayed_label') != label:
            raise ValueError('Score/packet displayed-label mismatch.')
        for name in ('prompt_id', 'response_text'):
            if name in s and s[name] != p[name]:
                raise ValueError('Score/packet identity mismatch: '+name)
        values = s.get('scores', s)
        row = tuple(values.get(d) for d in DIMS)
        if any(type(x) not in (int, float) or not math.isfinite(x) or not 1 <= x <= 10 for x in row):
            raise ValueError('Every dimension must be a finite numeric score in [1, 10].')
        # Never strip source text. Same text in different tasks is not one response.
        key = sha(canonical([pid, text]))
        if key in pairs:
            raise ValueError('Ambiguous duplicate response within a prompt/session.')
        pairs[key] = {'prompt_id': pid, 'response_sha256': sha(text.encode()),
                      'blind_id': bid, 'displayed_label': label, 'scores': list(row)}
    return pairs

def covariance(a, b):
    ma, mb = st.mean(a), st.mean(b)
    return st.mean([(x-ma)*(y-mb) for x, y in zip(a,b)])

def corr(a, b):
    va, vb = covariance(a,a), covariance(b,b)
    return None if va <= 1e-24 or vb <= 1e-24 else covariance(a,b)/math.sqrt(va*vb)

def ranks(a):
    order = sorted(range(len(a)), key=a.__getitem__)
    out, i = [0.0]*len(a), 0
    while i < len(a):
        j = i+1
        while j < len(a) and a[order[i]] == a[order[j]]:
            j += 1
        for k in range(i,j):
            out[order[k]] = (i+j-1)/2+1
        i = j
    return out

def coupling_diagnostic(pairs, judge):
    selected = []
    for p in pairs:
        a, b = p['session_1'], p['session_2']
        if (a['displayed_label'] == judge) != (b['displayed_label'] == judge):
            own, other = (a,b) if a['displayed_label'] == judge else (b,a)
            selected.append({'pair_key': p['pair_key'], 'prompt_id': a['prompt_id'],
                             'self_score': st.mean(own['scores']), 'baseline': st.mean(other['scores'])})
    if not selected:
        return {'n': 0}
    s = [p['self_score'] for p in selected]
    b = [p['baseline'] for p in selected]
    d = [x-y for x,y in zip(s,b)]
    cov_sb, var_b = covariance(s,b), covariance(b,b)
    return {'n': len(s), 'unique_prompts': len({p['prompt_id'] for p in selected}),
            'mean_delta': st.mean(d), 'pearson_delta_baseline': corr(d,b),
            'spearman_delta_baseline': corr(ranks(d),ranks(b)),
            'pearson_reverse_delta_self': corr([-x for x in d],s),
            'var_self': covariance(s,s), 'var_baseline': var_b,
            'cov_self_baseline': cov_sb, 'cov_delta_baseline': covariance(d,b),
            'identity_rhs_cov_self_baseline_minus_var_baseline': cov_sb-var_b,
            'interpretation': 'Delta = self - baseline shares baseline on both axes. '
                'Negative correlation alone does not identify a causal floor-raising mechanism. '
                'These diagnostics neither prove nor disprove such a mechanism.',
            'pairs': selected}

def audit_judge(source, judge, expected=40):
    sessions, methods = [], []
    for n in (1,2):
        scored = source.read(f'{BASE}/score_sheets/label_swap/{judge}/session_{n}_scored.json')
        packet = source.read(f'{BASE}/data/label_swap_packets/{judge}/session_{n}.json')
        methods.append(scored.get('scoring_method') if isinstance(scored,dict) else None)
        sessions.append(parse_session(scored,packet,expected))
    a,b = sessions
    if a.keys() != b.keys():
        raise ValueError('Sessions contain different response/task identities.')
    pairs = [{'pair_key':k, 'session_1':a[k], 'session_2':b[k]} for k in sorted(a)]
    same = sum(p['session_1']['displayed_label'] == p['session_2']['displayed_label'] for p in pairs)
    if same:
        raise ValueError('Found pairs without an actual label change.')
    cells = [abs(x-y) for p in pairs for x,y in zip(p['session_1']['scores'],p['session_2']['scores'])]
    return {'pairs':len(pairs), 'same_label_pairs':same,
            'identical_tuples':sum(p['session_1']['scores'] == p['session_2']['scores'] for p in pairs),
            'cells_differing':sum(x>0 for x in cells), 'cells':len(cells),
            'mean_abs_diff':st.mean(cells), 'reported_scoring_methods':methods,
            'method_limit':'Metadata is a report, not independent verification of the execution process.',
            'coupling':coupling_diagnostic(pairs,judge), 'pair_details':pairs}

def build_report(source, judges=JUDGES):
    result = {j:audit_judge(source,j) for j in judges}
    return {'version':'label-audit-0.2.0', 'commit':source.commit,
            'repository':'https://github.com/ai-village-agents/research-2026-05',
            'model_calls':0, 'judges':result, 'files':source.files,
            'conclusion_limit':'No gold process label. Exact score equality does not establish '
                'reuse, independent rescoring, joint-context consistency, or dishonesty.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--snapshot',type=Path); g.add_argument('--repo',type=Path)
    p.add_argument('--rev',default='HEAD')
    p.add_argument('--judges',nargs='+',choices=JUDGES,default=list(JUDGES))
    p.add_argument('--out',type=Path,required=True)
    a = p.parse_args()
    try:
        if a.out.exists():
            raise ValueError('Output exists; choose a new --out.')
        report = build_report(Source(a.snapshot,a.repo,a.rev),a.judges)
        write(a.out,report)
        for j,r in report['judges'].items():
            print(f"{j}: {r['identical_tuples']}/{r['pairs']} identical tuples; "
                  f"{r['cells_differing']}/{r['cells']} dimensions differ")
        print('No model calls. No ground-truth process inferred.')
    except (OSError,ValueError,KeyError,TypeError) as e:
        p.exit(1, 'ERROR: '+str(e)+'\n')

if __name__ == '__main__':
    main()
