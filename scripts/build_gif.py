#!/usr/bin/env python3
"""Assemble independent RGBA frame PNGs into real animated transparent looping GIFs."""
import argparse, os
from pathlib import Path
from PIL import Image, ImageChops, ImageSequence

def encode(frame, colors=64):
    frame=frame.convert('RGBA').resize((240,240),Image.Resampling.LANCZOS)
    # Reserve palette 0 for transparency, map RGB colors to indices 1..N.
    alpha=frame.getchannel('A')
    bg=Image.new('RGB',frame.size,(255,255,255));bg.paste(frame,mask=alpha)
    p=bg.quantize(colors=min(colors,254),method=Image.Quantize.MEDIANCUT)
    palette=p.getpalette()[:colors*3]
    trans=Image.new('P',frame.size,0)
    full=[0,0,0]+palette+[0]*(768-3-len(palette))
    trans.putpalette(full)
    # Palette shift +1 for opaque pixels, reserve index 0 for transparent.
    raw=p.tobytes();mask=alpha.point(lambda a:255 if a>=128 else 0).tobytes()
    out=bytes((idx+1 if mask[i] else 0) for i,idx in enumerate(raw))
    trans.frombytes(out)
    trans.info['transparency']=0
    return trans

def build(frames, dest, duration=160, max_kb=100):
    paths=sorted(Path(frames).glob('*.png'))
    if len(paths)<3: raise ValueError('at least 3 frame PNGs required')
    src=[Image.open(p).convert('RGBA') for p in paths]
    if any(im.getextrema()[3][0]==255 for im in src):
        print('WARNING: at least one frame has no transparent pixels; inspect visual background')
    if len(set(im.tobytes() for im in src))<3: raise ValueError('frames are not visually distinct')
    dest=Path(dest);dest.parent.mkdir(parents=True,exist_ok=True)
    best=None
    for n in (len(src), max(7,len(src)-2), 6):
        if n>len(src):continue
        ids=[round(i*(len(src)-1)/(n-1)) for i in range(n)]
        for colors in (96,64,48,32,24,16):
            seq=[encode(src[i],colors) for i in ids]
            seq[0].save(dest,save_all=True,append_images=seq[1:],duration=duration,loop=0,disposal=2,
                        optimize=True,transparency=0)
            size=dest.stat().st_size
            if best is None or size<best[0]: best=(size,n,colors)
            if size<=max_kb*1024:
                with Image.open(dest) as im:
                    if im.n_frames<3 or im.info.get('loop')!=0: raise ValueError('invalid animated GIF')
                print(f'{dest} {size/1024:.1f}KB frames={n} colors={colors} loop=forever')
                return
    raise ValueError(f'Cannot compress below {max_kb}KB. Best {best}. Simplify source art or background.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--frames',required=True);p.add_argument('--out',required=True)
    p.add_argument('--duration',type=int,default=160);p.add_argument('--max-kb',type=int,default=100)
    p.add_argument('--thumb',default=None,help='write 120x120 PNG of a representative frame')
    a=p.parse_args();build(a.frames,a.out,a.duration,a.max_kb)
    if a.thumb:
        with Image.open(a.out) as gif:
            gif.seek(min(4,gif.n_frames-1))
            thumb=gif.convert('RGBA').resize((120,120),Image.Resampling.LANCZOS)
            Path(a.thumb).parent.mkdir(parents=True,exist_ok=True);thumb.save(a.thumb,optimize=True)
            print('thumb:',a.thumb)
