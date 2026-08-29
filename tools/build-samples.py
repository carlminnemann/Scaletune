#!/usr/bin/env python3
"""Builds vendor/<instrument>-aac.js from Carl's own recordings.

Each recording is one continuous take: seventeen notes, from C2 upwards every
three semitones to C6, with four seconds of silence between them. The take is
cut at the silences, each note is trimmed, tapered, summed to mono and encoded,
and the seventeen come out as a MIDI.Soundfont file the sampler already knows
how to load.

Seventeen rather than eighty-eight. The library can shift a sample in cents at
playback, and every note in the scale is at most one semitone from one of these
— so the app picks the nearest and shifts it, instead of the file carrying five
times the bytes to say the same thing.

Nothing is retuned here. Each note's true pitch is measured and written out as
a correction in cents, which the app folds into the shift it is already making:
one resampling rather than two.

Needs afconvert, which is part of macOS. Run from the repo root:
    python3 tools/build-samples.py
"""
import base64,json,math,os,struct,subprocess,sys,wave

FONTE=os.path.expanduser('~/Desktop/scale tune')
SAIDA='vendor'
TMP='.sample-build'

# nome -> (ficheiro, segundos a guardar de cada nota, dBFS de destino)
INSTRUMENTOS={
    'strings':    ('strings/strings.wav',  6.5),
    'piano-real': ('piano-real/piano.wav', 6.5),
    'rhodes':     ('rhodes/rhodes.wav',    6.5),
    'hammond':    ('hammond/hammond.wav',  6.5),
}
BITRATE=80000
MIDI_BASE=36          # C2
PASSO=3               # de tres em tres semitons
N_NOTAS=17
NOMES=['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']

def nome(m): return NOMES[m%12]+str(m//12-1)
def freq(m): return 440.0*2**((m-69)/12.0)

# ---------- ler ----------
def ler_mono(p):
    """A gravacao inteira, somada a mono, em floats."""
    w=wave.open(p,'rb'); sw=w.getsampwidth(); ch=w.getnchannels(); sr=w.getframerate()
    n=w.getnframes(); esc=float(1<<(8*sw-1))
    x=[]
    while True:
        raw=w.readframes(sr)
        if not raw: break
        fr=sw*ch
        for i in range(0,len(raw)-fr+1,fr):
            s=0
            for c in range(ch):
                s+=int.from_bytes(raw[i+c*sw:i+(c+1)*sw],'little',signed=True)
            x.append(s/esc/ch)
    w.close()
    return x,sr

# ---------- cortar ----------
def cortar(x,sr):
    """Os inicios e fins das notas, pelo silencio entre elas."""
    passo=max(1,sr//1000)
    env=[max(abs(v) for v in x[i:i+passo]) for i in range(0,len(x)-passo,passo)]
    pico=max(env); lim=max(pico*0.02,0.0025)
    notas=[];dentro=False;i0=0
    for i,v in enumerate(env):
        if not dentro and v>lim: dentro=True;i0=i
        elif dentro and v<lim*0.6 and all(env[j]<lim*0.6 for j in range(i,min(i+300,len(env)))):
            if i-i0>200: notas.append([i0/1000.0,i/1000.0])
            dentro=False
    if dentro: notas.append([i0/1000.0,len(env)/1000.0])
    return notas

# ---------- medir ----------
def goertzel(x,sr,f):
    """Magnitude a uma frequencia so, com janela de Hann."""
    n=len(x);k=2*math.cos(2*math.pi*f/sr);s1=s2=0.0
    for i,v in enumerate(x):
        w=0.5-0.5*math.cos(2*math.pi*i/(n-1))
        s0=v*w+k*s1-s2;s2=s1;s1=s0
    return math.sqrt(max(s1*s1+s2*s2-k*s1*s2,0))/n

def parcial(x,sr,fc,span=90):
    """A frequencia e o nivel do pico mais proximo de fc."""
    bm=-1;bk=0;c={}
    for k in range(-span,span+1,2):
        m=goertzel(x,sr,fc*2**(k/1200.0));c[k]=m
        if m>bm: bm=m;bk=k
    a=c.get(bk-2,bm);b=bm;d=c.get(bk+2,bm);den=a-2*b+d
    return fc*2**((bk+(2*0.5*(a-d)/den if den else 0))/1200.0),bm

def altura(x,sr,f0):
    """A fundamental, tirada da serie inteira de parciais.

    Nao basta medir a primeira. Num piano ela e a mais fraca de todas — no C2
    deste esta 16 dB abaixo da segunda — e uma leitura feita so nela anda dez
    centimos ao lado. As parciais de um piano tambem nao sao harmonicas: estao
    esticadas, tanto mais quanto mais altas, e usa-las como se fossem da uma
    leitura alta. Entao ajusta-se o modelo que descreve as duas coisas,
    f(n) = n*f0*sqrt(1+B*n^2), a todas as parciais que se ouvem, com peso pelo
    nivel de cada uma: sai o f0 e sai a esticadela."""
    med=[]
    for n in range(1,7):
        f,m=parcial(x,sr,f0*n)
        if m>0: med.append((n,f,m))
    if not med: return f0
    forte=max(m for _,_,m in med)
    med=[(n,f,m) for n,f,m in med if m>forte*0.02]      # -34 dB da mais forte
    if len(med)<2:
        return med[0][1]/med[0][0] if med else f0
    melhor=None
    for B in [i*2e-5 for i in range(0,61)]:             # 0 a 1,2e-3
        num=den=0.0
        for n,f,m in med:
            prev=f/(n*math.sqrt(1+B*n*n))
            num+=m*math.log2(prev);den+=m
        cand=2**(num/den)
        err=sum(m*(1200*math.log2(f/(cand*n*math.sqrt(1+B*n*n))))**2 for n,f,m in med)
        if melhor is None or err<melhor[0]: melhor=(err,cand)
    return melhor[1]

def cents_de(x,sr,ini,fim,f0):
    """A mediana de varias leituras, todas dentro da nota e nenhuma no ataque.

    A janela cresce nos graves. A 0,35 s o lobo principal em C2 vale 145
    centimos e a leitura passa a depender de qualquer coisa que ande por perto;
    quarenta periodos poem o lobo a valer o mesmo em toda a extensao."""
    leituras=[];n=max(int(sr*0.35),int(40*sr/f0))
    for t in (0.25,0.45,0.7,1.0,1.4,1.9):
        k=int((ini+t)*sr)
        if k+n<=int(fim*sr) and k+n<len(x):
            leituras.append(altura(x[k:k+n],sr,f0))
    if not leituras:                              # nota curta: uma leitura so
        k=int((ini+0.12)*sr);n=min(n,int((fim-ini-0.15)*sr))
        if n>sr//20: leituras=[altura(x[k:k+n],sr,f0)]
    if not leituras: return 0.0
    leituras.sort()
    f=leituras[len(leituras)//2]
    return 1200*math.log2(f/f0)

# ---------- escrever ----------
def wav16(p,x,sr):
    w=wave.open(p,'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes(b''.join(struct.pack('<h',max(-32768,min(32767,int(v*32767)))) for v in x))
    w.close()

def aac(entrada,saida):
    subprocess.run(['afconvert','-f','m4af','-d','aac ','-b',str(BITRATE),
                    '--mix','-c','1',entrada,saida],check=True,
                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def main():
    quais=sys.argv[1:] or list(INSTRUMENTOS)
    os.makedirs(TMP,exist_ok=True)
    for inst in quais:
        rel,guardar=INSTRUMENTOS[inst]
        p=os.path.join(FONTE,rel)
        print('==',inst,'—',p)
        x,sr=ler_mono(p)
        notas=cortar(x,sr)
        if len(notas)!=N_NOTAS:
            print('   PAROU: %d notas, esperava %d'%(len(notas),N_NOTAS)); continue
        # o mesmo ganho para as dezassete: as diferencas entre notas sao a gravacao
        pico=max(max(abs(v) for v in x[int(a*sr):int(b*sr)]) for a,b in notas)
        ganho=0.89/pico                                  # -1 dBFS de tecto
        afinacao={}; pedacos=[]
        for k,(a,b) in enumerate(notas):
            m=MIDI_BASE+k*PASSO
            f0=freq(m)
            afinacao[m]=round(cents_de(x,sr,a,b,f0),1)
            i0=max(0,int((a-0.008)*sr))                  # 8 ms antes do ataque
            i1=min(len(x),i0+int(guardar*sr),int(b*sr)+int(0.05*sr))
            d=[v*ganho for v in x[i0:i1]]
            ent=int(sr*0.002)                            # 2 ms a entrar
            sai=int(sr*0.060)                            # 60 ms a sair
            for i in range(min(ent,len(d))): d[i]*=i/ent
            for i in range(min(sai,len(d))): d[len(d)-1-i]*=i/sai
            pedacos.append((m,d))
            print('   %-4s %5.2f s  %+5.1f cent'%(nome(m),len(d)/sr,afinacao[m]))
        objecto={}
        for m,d in pedacos:
            w=os.path.join(TMP,'%s-%d.wav'%(inst,m)); a4=w[:-4]+'.m4a'
            wav16(w,d,sr); aac(w,a4)
            objecto[nome(m)]='data:audio/mp4;base64,'+base64.b64encode(open(a4,'rb').read()).decode()
        fora=os.path.join(SAIDA,inst+'-aac.js')
        with open(fora,'w') as f:
            f.write("if (typeof(MIDI) === 'undefined') var MIDI = {};\n")
            f.write("if (typeof(MIDI.Soundfont) === 'undefined') MIDI.Soundfont = {};\n")
            f.write('MIDI.Soundfont.%s = {\n'%inst.replace('-','_'))
            for m,_ in pedacos:
                f.write('%s: "%s",\n'%(json.dumps(nome(m)),objecto[nome(m)]))
            f.write('}\n')
        print('   -> %s  %.2f MB'%(fora,os.path.getsize(fora)/1e6))
        print('   afinação:',json.dumps(afinacao))

if __name__=='__main__': main()
