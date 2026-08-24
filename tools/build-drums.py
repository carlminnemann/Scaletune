#!/usr/bin/env python3
"""Builds vendor/drums/*.wav from the Muldjord Kit.

Five hits out of a kit that ships as 370 FLAC files: one velocity layer each,
trimmed, tapered so the cut cannot click, and normalised. The kick and the
side-stick are also shaped, because the kit is close-miked and generous at the
bottom — the kick puts 99% of its energy under 300Hz, which a phone speaker
cannot move at all. The shaping is a high-shelf, not a synthetic click: it lifts
what the drum already has up where a small speaker works.

Needs the source FLACs (fetched on demand) and afconvert, which is part of
macOS. Run from the repo root:  python3 tools/build-drums.py
"""
import math,os,struct,subprocess,sys,wave

BASE='https://raw.githubusercontent.com/freepats/muldjordkit/main/samples'
OUT='vendor/drums'
TMP='.drum-build'

# A cymbal has to be allowed to ring. Cut at 0.7s the ride died before the next
# beat at any slow tempo, which is what a ride must never do, so it runs 2.4s
# now with only a short taper at the end and the natural decay doing the work.
# It is the one sample kept at 32kHz: its tail is all shimmer, and 32k holds
# everything under 16kHz for two thirds of the bytes.
#
# The kick and the snare are Carl's own drums, recorded in his room; the cymbals
# are still the borrowed ones. A source beginning with "mine:" is a file from
# that session rather than one fetched from the kit, and it is a take rather
# than a one-shot — several strokes in one file — so it also says which stroke
# to take.
# name          source                              secs  shaping  taper  rate
SPEC=[
 ('kick',  'mine:bombo forte.wav#1',               0.50, 'kick',  0.30, 44100),
 ('snare', 'mine:snare forte.wav#1',               0.40, None,    0.30, 44100),
 ('hhc',   'HihatClosed/20-HihatClosed.flac',      0.22, None,    0.34, 44100),
 ('hho',   'HihatOpen/20-HihatOpen.flac',          1.00, None,    0.18, 44100),
 ('ride',  'RideR/9-RideR.flac',                   2.40, None,    0.15, 32000),
]
MINE=('/Users/carlminnemann/Library/CloudStorage/OneDrive-JOBRA/'
      'Carl Minnemann/Claude/bateria')

def biquad(d,b0,b1,b2,a1,a2):
    out=[];x1=x2=y1=y2=0.0
    for x in d:
        y=b0*x+b1*x1+b2*x2-a1*y1-a2*y2
        out.append(y);x2=x1;x1=x;y2=y1;y1=y
    return out

def hp(d,sr,f,q=0.707):
    w=2*math.pi*f/sr;a=math.sin(w)/(2*q);c=math.cos(w);a0=1+a
    return biquad(d,(1+c)/2/a0,-(1+c)/a0,(1+c)/2/a0,(-2*c)/a0,(1-a)/a0)

def shelf_high(d,sr,f,db,s=0.9):
    A=10**(db/40);w=2*math.pi*f/sr;c=math.cos(w)
    al=math.sin(w)/2*math.sqrt((A+1/A)*(1/s-1)+2);t=2*math.sqrt(A)*al
    a0=(A+1)-(A-1)*c+t
    return biquad(d,A*((A+1)+(A-1)*c+t)/a0,-2*A*((A-1)+(A+1)*c)/a0,A*((A+1)+(A-1)*c-t)/a0,
                    2*((A-1)-(A+1)*c)/a0,((A+1)-(A-1)*c-t)/a0)

def peaking(d,sr,f,db,q=1.0):
    A=10**(db/40);w=2*math.pi*f/sr;al=math.sin(w)/(2*q);c=math.cos(w);a0=1+al/A
    return biquad(d,(1+al*A)/a0,(-2*c)/a0,(1-al*A)/a0,(-2*c)/a0,(1-al/A)/a0)

SHAPE={
 # the beater end of the drum, brought up to where a phone can reproduce it
 'kick':  lambda d,sr: shelf_high(hp(d,sr,50),sr,1400,9),
}

def decode(src,dst,rate=44100):
    subprocess.run(['afconvert','-f','WAVE','-d','LEI16@%d'%rate,'-c','1',src,dst],check=True)

def read(p):
    w=wave.open(p);sr=w.getframerate();n=w.getnframes()
    d=struct.unpack('<%dh'%n,w.readframes(n));w.close()
    return [x/32768 for x in d],sr

def read_any(p):
    """Carl's files are 24-bit and some are stereo; folded to mono floats."""
    w=wave.open(p)
    n,sr,ch,sw=w.getnframes(),w.getframerate(),w.getnchannels(),w.getsampwidth()
    raw=w.readframes(n);w.close()
    out=[0.0]*n;step=sw*ch
    for i in range(n):
        b=i*step;acc=0.0
        for c in range(ch):
            o=b+c*sw
            if sw==3:
                v=raw[o]|(raw[o+1]<<8)|(raw[o+2]<<16)
                if v&0x800000: v-=0x1000000
                acc+=v/8388608.0
            else:
                v=raw[o]|(raw[o+1]<<8)
                if v&0x8000: v-=0x10000
                acc+=v/32768.0
        out[i]=acc/ch
    return out,sr

def nth_stroke(d,sr,which):
    """Where stroke number `which` begins, in a file holding several."""
    blk=256
    env=[max(abs(v) for v in d[i:i+blk]) or 0.0 for i in range(0,len(d)-blk,blk)]
    pk=max(env);starts=[];armed=True
    for i,v in enumerate(env):
        if armed and v>pk*0.35: starts.append(i);armed=False
        elif not armed and v<pk*0.08: armed=True
    if not starts: return 0
    return starts[min(which,len(starts))-1]*blk

def phone_peak(d,sr):
    """Roughly what a phone speaker lets out: two poles at 400Hz."""
    f=hp(hp(d,sr,400),sr,400)
    return max(abs(x) for x in f)

def main():
    os.makedirs(OUT,exist_ok=True);os.makedirs(TMP,exist_ok=True)
    for name,src,dur,shape,taper,rate in SPEC:
        if src.startswith('mine:'):
            fn,_,which=src[5:].partition('#')
            d,sr=read_any(os.path.join(MINE,fn))
            at=nth_stroke(d,sr,int(which or 1))
            pk=max(abs(x) for x in d)
            back=at
            while back>0 and abs(d[back])>pk*0.02: back-=1
            start=max(0,back-int(0.002*sr))
        else:
            flac=os.path.join(TMP,name+'.flac');wav=os.path.join(TMP,name+'.wav')
            if not os.path.exists(flac):
                subprocess.run(['curl','-sL','-o',flac,BASE+'/'+src],check=True)
            decode(flac,wav,rate)
            d,sr=read(wav)
            pk=max(abs(x) for x in d)
            start=next(i for i,x in enumerate(d) if abs(x)>pk*0.02)
            start=max(0,start-int(0.002*sr))
        cut=list(d[start:start+int(dur*sr)])
        tail=int(len(cut)*taper)         # a cosine taper over the end
        for i in range(tail):
            cut[len(cut)-tail+i]*=0.5*(1+math.cos(math.pi*(i/tail)))
        if sr!=rate:
            n=int(len(cut)*rate/sr);rs=[0.0]*n
            for i in range(n):
                x=i*sr/rate;j=int(x);f=x-j
                a=cut[j] if j<len(cut) else 0.0
                b=cut[j+1] if j+1<len(cut) else 0.0
                rs[i]=a+(b-a)*f
            cut=rs;sr=rate
        if shape:cut=SHAPE[shape](cut,sr)
        g=0.95/(max(abs(x) for x in cut) or 1)
        frames=[max(-32768,min(32767,int(x*g*32767))) for x in cut]
        p=os.path.join(OUT,name+'.wav')
        f=wave.open(p,'w');f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr)
        f.writeframes(struct.pack('<%dh'%len(frames),*frames));f.close()
        print('%-6s %5.3fs %6d bytes   through a phone speaker %.0f%% of its peak survives'%(
            name,len(cut)/sr,os.path.getsize(p),100*phone_peak([x*g for x in cut],sr)/0.95))

if __name__=='__main__':
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main()
