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

# name          source file                        seconds  shaping
SPEC=[
 ('kick',  'KdrumL/20-KdrumL.flac',                0.55, 'kick'),
 ('snare', 'Snare1/40-Snare.flac',                 0.45, None),
 ('hhc',   'HihatClosed/20-HihatClosed.flac',      0.22, None),
 ('hho',   'HihatOpen/20-HihatOpen.flac',          0.55, None),
 ('ride',  'RideR/9-RideR.flac',                  0.70, None),
]

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

def decode(src,dst):
    subprocess.run(['afconvert','-f','WAVE','-d','LEI16@44100','-c','1',src,dst],check=True)

def read(p):
    w=wave.open(p);sr=w.getframerate();n=w.getnframes()
    d=struct.unpack('<%dh'%n,w.readframes(n));w.close()
    return [x/32768 for x in d],sr

def phone_peak(d,sr):
    """Roughly what a phone speaker lets out: two poles at 400Hz."""
    f=hp(hp(d,sr,400),sr,400)
    return max(abs(x) for x in f)

def main():
    os.makedirs(OUT,exist_ok=True);os.makedirs(TMP,exist_ok=True)
    for name,src,dur,shape in SPEC:
        flac=os.path.join(TMP,name+'.flac');wav=os.path.join(TMP,name+'.wav')
        if not os.path.exists(flac):
            subprocess.run(['curl','-sL','-o',flac,BASE+'/'+src],check=True)
        decode(flac,wav)
        d,sr=read(wav)
        pk=max(abs(x) for x in d)
        start=next(i for i,x in enumerate(d) if abs(x)>pk*0.02)
        start=max(0,start-int(0.002*sr))
        cut=list(d[start:start+int(dur*sr)])
        tail=int(len(cut)*0.34)          # a cosine taper over the last third
        for i in range(tail):
            cut[len(cut)-tail+i]*=0.5*(1+math.cos(math.pi*(i/tail)))
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
