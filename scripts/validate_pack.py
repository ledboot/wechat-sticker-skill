#!/usr/bin/env python3
"""Strict local quality gate. Does not certify WeChat acceptance."""
import argparse, json, re
from collections import Counter
from pathlib import Path
from PIL import Image, ImageChops

ROOT=Path(__file__).resolve().parents[1]
def validate(root,profile,selection=None):
    root=Path(root);spec=json.loads(Path(profile).read_text(encoding='utf-8'))
    issues=[];checked=[]
    def check_file(p,dims,max_kb,fmt,alpha=False,animated=False):
        if not p.is_file(): issues.append(f'MISSING {p}');return
        size=p.stat().st_size
        if size>max_kb*1024:issues.append(f'OVERSIZE {p} ({size/1024:.1f}KB > {max_kb}KB)')
        try:
            with Image.open(p) as im:
                if im.size!=tuple(dims):issues.append(f'DIMENSIONS {p} {im.size} != {tuple(dims)}')
                if im.format not in fmt:issues.append(f'FORMAT {p}: {im.format} not {fmt}')
                if animated:
                    if im.n_frames<3:issues.append(f'STATIC GIF {p}: only {im.n_frames} frames')
                    if im.info.get('loop')!=0:issues.append(f'NOT INFINITE LOOP {p}')
                    frames=[]
                    for i in range(im.n_frames):
                        im.seek(i);frames.append(im.convert('RGB').resize((24,24)).tobytes())
                        dur=im.info.get('duration',0)
                        if dur<30 or dur>2000:issues.append(f'ODD DURATION {p} frame {i}: {dur}ms')
                    if len(set(frames))<3:issues.append(f'INSUFFICIENT MOTION {p}')
                if alpha:
                    # Verify actual transparent pixels (not just RGBA mode).
                    if animated:
                        im.seek(0)
                        if im.info.get('transparency') is None and 'transparency' not in im.info:
                            issues.append(f'NO GIF TRANSPARENCY {p}')
                    elif im.mode not in ('RGBA','LA','P') or ('A' not in im.getbands() and 'transparency' not in im.info):
                        issues.append(f'NO TRANSPARENCY CHANNEL {p}')
                checked.append(str(p))
        except Exception as e:issues.append(f'INVALID {p}: {e}')
    stickers=root/'stickers';thumbs=root/'thumbs'
    gifs=sorted(stickers.glob('*.gif')) if stickers.exists() else []
    if not 8<=len(gifs)<=24:issues.append(f'STICKER COUNT {len(gifs)} not in 8–24')
    expected=[f'{i:02}' for i in range(1,len(gifs)+1)]
    if [p.stem for p in gifs]!=expected:issues.append('STICKER NAMES must be consecutive 01.gif, 02.gif, ...')
    for p in gifs:
        check_file(p,spec['sticker_size'],spec['sticker_max_kb'],['GIF'],spec.get('require_transparent_sticker',True),True)
        check_file(thumbs/(p.stem+'.png'),spec['thumb_size'],spec['thumb_max_kb'],['PNG'],True)
    # Auxiliary filenames are dimension-suffixed, computed from the active profile.
    # The banner may be JPEG or PNG; tip images may be PNG or animated GIF.
    for key,base,extensions,formats,alpha in [
        ('banner','banner',['jpg','png'],['JPEG','PNG'],False),
        ('cover','cover',['png'],['PNG'],True),
        ('icon','icon',['png'],['PNG'],True),
        ('tip_guide','tip_guide',['png','gif'],['PNG','GIF'],False),
        ('tip_thanks','tip_thanks',['png','gif'],['PNG','GIF'],False)]:
        dims=spec[key+'_size']
        stem=f'{base}_{dims[0]}x{dims[1]}'
        found=[root/f'{stem}.{ext}' for ext in extensions if (root/f'{stem}.{ext}').is_file()]
        if not found:
            issues.append(f'MISSING {root / (stem + "." + extensions[0])} (allowed: {", ".join(extensions)})')
            continue
        if len(found)>1: issues.append(f'DUPLICATE VARIANTS {stem}: {found}')
        for asset in found:
            check_file(asset,dims,spec[key+'_max_kb'],formats,alpha,animated=(asset.suffix.lower()=='.gif'))
    distribution={}
    if selection:
        rows=json.loads(Path(selection).read_text(encoding='utf-8'))
        distribution=dict(Counter(x['category'] for x in rows))
        if len(rows)!=len(gifs):issues.append('SELECTION COUNT mismatch')
        if distribution and max(distribution.values())-min(distribution.values())>1:issues.append('CATEGORY IMBALANCE (>1)')
        for item in rows:
            if len(item['text'])>5:issues.append(f'TEXT TOO LONG {item["text"]}')
    return {'passed':not issues,'checked_files':len(checked),'gif_count':len(gifs),
            'category_distribution':distribution,'issues':issues,'profile':spec['name'],
            'note':'Technical checks only; content, rights, typography and current WeChat rules require human review.'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True)
    p.add_argument('--profile',default=str(ROOT/'references/profile_conservative.json'))
    p.add_argument('--selection');p.add_argument('--report');a=p.parse_args()
    result=validate(a.root,a.profile,a.selection)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if a.report:Path(a.report).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    raise SystemExit(0 if result['passed'] else 1)
