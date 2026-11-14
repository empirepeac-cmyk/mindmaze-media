import numpy as np,os,subprocess
from scipy import signal
from scipy.io import wavfile
from pedalboard import Pedalboard,Reverb,Compressor,Limiter,HighpassFilter,LowpassFilter
SR=48000; DUR=34.6; N=int(SR*DUR); rng=np.random.default_rng(7)
L=np.zeros(N);R=np.zeros(N)
def add(x,t,g=1.0,pan=0.0):
    i=int(t*SR); x=x[:max(0,N-i)]
    L[i:i+len(x)]+=x*g*np.sqrt((1-pan)/2); R[i:i+len(x)]+=x*g*np.sqrt((1+pan)/2)
def bp(x,lo,hi,o=2): return signal.sosfilt(signal.butter(o,[lo,hi],btype='band',fs=SR,output='sos'),x)
def lp(x,f,o=2): return signal.sosfilt(signal.butter(o,f,btype='low',fs=SR,output='sos'),x)
def hp(x,f,o=2): return signal.sosfilt(signal.butter(o,f,btype='high',fs=SR,output='sos'),x)
def env_from_frames(v,smooth=2.0):
    """per-frame values (index = frame number, 24fps) -> audio-rate envelope"""
    v=np.asarray(v,float); v=signal.medfilt(v,3); k=np.hanning(int(smooth*2+3)); v=np.convolve(v,k/k.sum(),'same')
    t=np.arange(N)/SR*24+1; return np.interp(t,np.arange(len(v)),v)
def load(fn):
    tmp='/tmp/claude-0/-home-user/7503926b-fbab-5c1c-9fde-d9a76afa4905/scratchpad/_l.wav'
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',fn,'-ac','1','-ar',str(SR),tmp],check=True)
    sr,x=wavfile.read(tmp); return x.astype(np.float64)/32768
K='sfx/kenney/'
_c={}
def smp(name,rate=1.0):
    p={'x':K+'x/Audio/','r':K+'rpg-audio/Audio/','s':K+'sci-fi-sounds/Audio/'}[name[0]]+name[2:]+'.ogg'
    if p not in _c: _c[p]=load(p)
    x=_c[p]
    if rate!=1.0: x=signal.resample(x,int(len(x)/rate))
    return x
def modal(freqs,decs,amps,dur,noise=0.0):
    t=np.arange(int(dur*SR))/SR; y=np.zeros_like(t)
    for f,d,a in zip(freqs,decs,amps): y+=a*np.sin(2*np.pi*f*t+rng.uniform(0,6.28))*np.exp(-t/d)
    if noise: y+=noise*bp(rng.standard_normal(len(t)),1500,9000)*np.exp(-t/0.03)
    return y
def beep(notes,vib=0.0,gl=0.02):
    """notes: list of (f0,f1,dur,gap)"""
    out=[]
    for f0,f1,d,gap in notes:
        n=int(d*SR); t=np.arange(n)/SR; f=f0*(f1/f0)**(t/d)
        if vib: f=f*(1+vib*np.sin(2*np.pi*28*t))
        ph=2*np.pi*np.cumsum(f)/SR; y=np.sin(ph+0.9*np.sin(2*ph))*0.6+0.25*np.sin(2*ph)
        a=np.minimum(1,t/0.008)*np.minimum(1,(d-t)/gl); out+= [y*a,np.zeros(int(gap*SR))]
    return bp(np.concatenate(out),350,5200)
# ---------- signals from picture
M=np.load('motion.npy'); M=np.concatenate([[0],M,[0]])  # index = frame
B=np.load('brush.npy')
for c in (1,2,71,72,73,74,170,171,172,173,249,250,251,252,253,299,300,301,340,341,342,358,359,360,361,362,433,434,528,529,530,703,704): 
    if c<len(M): M[c]=0
for c in (249,250,338,339,340,341,701,702): B[c]=0
# ---------- 1 room tone + rain on the windows
room=lp(rng.standard_normal(N),140)*0.5+bp(rng.standard_normal(N),300,1200)*0.05
rain=hp(rng.standard_normal(N),2500)*0.06*(0.8+0.2*lp(rng.standard_normal(N),0.7)*40)
fade=np.clip((31.6-np.arange(N)/SR)/0.6,0,1)*np.clip(np.arange(N)/SR/0.6,0,1)
add((room*0.10+rain*0.07)*fade,0,1.0)
# ---------- 2 servo whirr following body motion
body=M.copy(); body[160:252]*=0.35; body[300:342]*=0.35; body[560:703]*=0.5
body[250:300]=0; body[341:360]=0; body[745:]=0
e=env_from_frames(body,2.5); e=np.clip((e-0.9)/7.0,0,1)**0.8
f=170+520*e; ph=2*np.pi*np.cumsum(f)/SR
serv=(signal.sawtooth(ph)*0.5+signal.sawtooth(ph*2.01)*0.25); serv=bp(serv,300,2600)+bp(rng.standard_normal(N),900,3000)*0.25
add(serv*e*0.055,0,1.0,-0.05)
# wheels while it drives to the charger (15.2-17.3) and when it turns round (22-23.4)
def wheels(t0,t1,g):
    n=int((t1-t0)*SR); t=np.arange(n)/SR; a=np.minimum(1,t/0.25)*np.minimum(1,(t1-t0-t)/0.2)
    y=lp(rng.standard_normal(n),220)*1.3+bp(rng.standard_normal(n),500,1400)*0.12*(0.6+0.4*np.sin(2*np.pi*9*t))
    add(y*a,t0,g)
wheels(15.15,17.3,0.08); wheels(21.9,23.3,0.07); wheels(0.25,0.55,0.07)
# ---------- 3 brush strokes exactly when the brush moves
Bn=np.zeros_like(B)
for a_,b_ in [(160,250),(300,341),(560,703)]:
    seg=signal.medfilt(B[a_:b_],3); p=np.percentile(seg,92); Bn[a_:b_]=np.clip((seg-2.5)/(p-2.5),0,1.25)
be=env_from_frames(Bn,1.2)**1.1
if os.path.exists('sfx/scrub.wav'):
    s_=load('sfx/scrub.wav'); s_=s_/np.abs(s_).max(); k=np.ones(2400)/2400
    lev=np.sqrt(np.convolve(s_**2,k,'same'))+0.02; s_=s_/lev*0.25
    br=hp(np.tile(s_,int(N/len(s_))+2)[:N],500)
else:
    br=np.zeros(N); grains=[('r/cloth1',1),('r/cloth2',1.6),('r/cloth3',1.8),('r/cloth4',2.5),('r/drawKnife3',1.5),('x/footstep_snow_001',0.8),('x/footstep_snow_003',0.8)]
    t=0.0
    while t<DUR-1:
        i=int(t*SR)
        if be[i]>0.03:
            nm,g=grains[rng.integers(len(grains))]; x=smp(nm,rng.uniform(1.15,1.7))*g
            x=x*np.hanning(len(x))**0.5; x=x[:N-i]; br[i:i+len(x)]+=x*rng.uniform(0.7,1.0)
            t+=rng.uniform(0.05,0.09)
        else: t+=0.01
    br=hp(br,900)*1.6+bp(br,3000,8000)*1.2
wet=np.where(np.arange(N)/SR>23,1,0)
br=br*(1-0.35*wet)+lp(br,1500)*0.9*wet
add(br*be*1.5,0,1.0,0.1)
# ---------- 4 lamp shots: mains hum + buzz, and it is otherwise quiet
def lamp(t0,t1):
    n=int((t1-t0)*SR); t=np.arange(n)/SR; a=np.minimum(1,t/0.05)*np.minimum(1,(t1-t0-t)/0.05)
    y=0.5*np.sin(2*np.pi*100*t)+0.25*np.sin(2*np.pi*200*t)+0.12*signal.sawtooth(2*np.pi*100*t)*1.0
    y=y+bp(signal.square(2*np.pi*100*t),2000,6000)*0.05
    add(y*a,t0,0.035)
lamp(10.42,12.42); lamp(14.21,14.96)
# ---------- 5 the bin
metal=None
if os.path.exists('sfx/clang.wav'): metal=load('sfx/clang.wav'); metal/=np.abs(metal).max()
def clang(scale=1.0,dur=1.6,bright=1.0):
    fr=np.array([212,389,517,731,968,1340,1790,2410,3150,4200])*scale; de=np.array([.9,.7,.6,.45,.4,.3,.25,.18,.12,.08])*dur/1.6
    am=np.array([1,.8,.9,.6,.7,.5,.45,.35,.3,.2])*np.linspace(1,bright,10)
    return modal(fr,de,am,dur,noise=1.2)
add(smp('x/impactMetal_medium_000',0.8),17.36,0.16,0.35)       # robot's back bumps the bin
add(smp('r/creak2',0.9),17.5,0.05,0.4)                          # it tips
add(smp('r/metalPot1',0.55),17.98,0.55,0.45)                    # bin hits the floor
add(smp('x/impactPlate_heavy_002',0.6),17.98,0.45,0.4)
add(smp('s/impactMetal_003',0.9),17.98,0.5,0.3)
add(clang(1.0,1.2,1.0),17.99,0.07,0.45)
add(smp('x/impactPlate_heavy_004',0.75),18.16,0.22,0.35)       # lid lands and spins down
tt=18.34; gap=0.17; j=0
while gap>0.04 and tt<19.0:
    add(smp('x/impactPlate_light_00%d'%(j%5),rng.uniform(.95,1.15)),tt,0.13*min(1,gap/0.11+0.25),0.3); tt+=gap; gap*=0.85; j+=1
for t,r,g in [(18.22,1.5,.20),(18.4,1.9,.16),(18.62,1.3,.18),(18.88,2.1,.11),(19.2,1.7,.08),(19.62,2.3,.05)]:   # tins
    add(smp('x/impactTin_medium_00%d'%rng.integers(5),r),t,g,rng.uniform(-.1,.5))
for t,nm,g in [(18.08,'r/bookFlip1',.18),(18.3,'r/cloth1',.2),(18.5,'r/bookFlip2',.3),(18.75,'r/bookFlip3',.15),(19.0,'r/cloth3',.2)]:  # paper, rubbish
    add(smp(nm,0.8),t,g,0.3)
add(smp('x/impactWood_light_000',1.0),15.0,0.12,0.0)            # brush put down
add(smp('x/impactWood_light_002',1.3),23.75,0.06,-0.3)          # brush picked up
# ---------- 6 robot voice (few, only on a change of mood)
V=[(0.95,[(620,900,.09,.05),(900,1250,.13,0)],.07),          # spots the stain
   (3.05,[(700,1050,.16,0)],.06),                             # hm?
   (6.55,[(520,500,.07,.05),(520,500,.07,0)],.06),            # right, brush
   (10.15,[(480,300,.28,0)],.07),                             # annoyed
   (15.05,[(660,990,.10,.04),(990,1320,.16,0)],.07),          # oh! it was the lamp
   (18.45,[(1500,1700,.06,.04),(1500,1700,.06,0)],.07),       # startled
   (20.3,[(700,380,.45,0)],.06),                              # oh no
   (29.35,[(420,250,.5,0)],.06)]                              # tired
for t,n,g in V: add(beep(n,vib=0.012 if n[0][2]>.25 else 0),t,g)
add(modal([220,440,660],[1.6,1.2,.8],[1,.4,.2],2.2),31.55,0.02)  # title
# ---------- master
st=np.stack([L,R]).astype(np.float32)
pb=Pedalboard([HighpassFilter(35),Reverb(room_size=0.32,wet_level=0.13,dry_level=0.9,damping=0.6),Compressor(threshold_db=-16,ratio=2.5),Limiter(threshold_db=-1.5)])
st=pb(st,SR); st=st/np.abs(st).max()*0.89
wavfile.write('newa.wav',SR,(st.T*32767).astype(np.int16)); print('ok',st.shape, 'scrub sample' if os.path.exists('sfx/scrub.wav') else 'scrub synth','clang sample' if metal is not None else 'clang synth')
