#!/usr/bin/env python3
"""Select evenly distributed themes (8–24) from six supplied categories."""
import argparse, json, random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def select(count=16, seed=42, include=None, exclude=None):
    if not 8 <= count <= 24:
        raise ValueError('count must be 8–24')
    data = json.loads((ROOT/'references/topics.json').read_text(encoding='utf-8'))
    rng = random.Random(seed)
    categories = [x['category'] for x in data]
    items = {x['category']: [{'category':x['category'],'text':t,'action':a} for t,a in x['items']] for x in data}
    exclude = set(exclude or [])
    selected = []
    for name in include or []:
        matches = [v for group in items.values() for v in group if v['text']==name]
        if not matches: raise ValueError('unknown requested topic: '+name)
        if name in exclude: raise ValueError('topic included and excluded: '+name)
        if name not in [v['text'] for v in selected]: selected.append(matches[0])
    if len(selected)>count: raise ValueError('included topics exceed count')
    # Minimize max-min discrepancy after compulsory inclusions.
    while len(selected)<count:
        counts = {c: sum(v['category']==c for v in selected) for c in categories}
        available = [c for c in categories if any(v['text'] not in exclude and v['text'] not in [s['text'] for s in selected] for v in items[c])]
        if not available: raise ValueError('not enough available topics')
        low = min(counts[c] for c in available)
        choices = [c for c in available if counts[c]==low]
        c = rng.choice(choices)
        candidates = [v for v in items[c] if v['text'] not in exclude and v['text'] not in [s['text'] for s in selected]]
        # Bias toward user-supplied order as common-frequency ranking.
        selected.append(candidates[0] if rng.random()<0.7 else rng.choice(candidates[:min(4,len(candidates))]))
    rng.shuffle(selected)
    return [dict(index=i+1, filename=f'{i+1:02}.gif', **v) for i,v in enumerate(selected)]

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--count',type=int,default=16);p.add_argument('--seed',type=int,default=42)
    p.add_argument('--include',nargs='*',default=[]);p.add_argument('--exclude',nargs='*',default=[])
    p.add_argument('--out',default='selection.json');a=p.parse_args()
    result=select(a.count,a.seed,a.include,a.exclude)
    Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    from collections import Counter
    print('Selected',len(result),'themes:',dict(Counter(x['category'] for x in result)),'->',a.out)
