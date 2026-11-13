import numpy as np, pickle, sys, math, os
from scipy.io import wavfile
from pedalboard import Pedalboard, Reverb, Compressor, HighpassFilter, LowpassFilter, Limiter
sys.path.insert(0,'/home/user/work/gold3d')
import common as C
SR=48000; T=C.NF/C.FPS
EV=pickle.load(open('ev.pkl','rb')); rng=np.random.default_rng(7)
def load(n):
    sr,y=wavfile.read(n); assert sr==SR; return y.astype(np.float32)/32768
def rs(y,r):  # resample: r>1 = higher pitch
    n=int(len(y)/r); x=np.linspace(0,len(y)-1,n); i=np.arange(len(y))
    return np.stack([np.interp(x,i,y[:,c]) for c in range(2)],1).astype(np.float32)
fx=np.zeros((int(T*SR)+SR*3,2),np.float32)   # goes through reverb
dry=np.zeros_like(fx)
def add(buf,y,t,g=1.0,pan=0.0):
    i=int(t*SR)
    if i<0: y=y[-i:]; i=0
    n=min(len(y),len(buf)-i)
    if n<=0: return
    if y.ndim==1: y=np.stack([y,y],1)
    buf[i:i+n,0]+=y[:n,0]*g*(1-max(0,pan)*0.5); buf[i:i+n,1]+=y[:n,1]*g*(1+min(0,pan)*0.5)
def tick(f,d,dec,noise=0.3):
    t=np.arange(int(d*SR))/SR
    y=np.sin(2*np.pi*f*t)*np.exp(-t*dec)+0.4*np.sin(2*np.pi*f*2.76*t)*np.exp(-t*dec*1.6)
    y+=rng.normal(0,1,len(t))*np.exp(-t*900)*noise
    return (y*np.minimum(t/0.0006,1)).astype(np.float32)
# 1) ball / peg / wall ticks
last={}
for t,imp,kind,isg,x,y in EV:
    if t>=T: continue
    k=(kind,int(x//40),int(y//40))
    if t-last.get(k,-1)<0.04: continue
    last[k]=t
    v=min(1.0,imp/2200)**0.7; pan=(x-540)/540
    if kind=='peg': add(fx,tick(rng.uniform(2800,4300),0.10,85,0.3),t,0.16*v,pan)
    elif kind=='wall': add(fx,tick(rng.uniform(380,600),0.09,65,0.5),t,0.22*v,pan)
    elif kind=='ball': add(fx,tick(rng.uniform(1500,2200),0.045,170,0.6),t,0.11*v,pan)
# 2) real glass: hits on the cup, then the two shatters
gb=load('gb1.wav'); on=int(0.058*SR)
hit=gb[on:on+int(0.16*SR)].copy(); hit*=np.exp(-np.arange(len(hit))/SR*22)[:,None]
nh=len(C.HITS)
for n,(t,imp,dm) in enumerate(C.HITS[:-1]):
    p=1.9-0.5*n/nh+rng.uniform(-0.05,0.05)          # pitch drops as it weakens
    add(fx,rs(hit,p),t-0.002,0.30+0.35*n/nh)
    crk=gb[on+int(0.2*SR):on+int(0.2*SR)+int(0.07*SR)]*np.linspace(1,0,int(0.07*SR))[:,None]
    add(fx,rs(crk,1.5),t+0.03,1.2+1.5*n/nh)
add(fx,gb[on-200:],C.OUT-0.004,0.95); add(fx,rs(gb[on-200:],1.35),C.OUT+0.02,0.5)
add(fx,rs(gb[on-200:],0.72),C.TREL-0.004,1.0); add(fx,gb[on-200:],C.TREL+0.015,0.8); add(fx,rs(gb[on-200:],0.9),C.TREL+0.07,0.6)
# 3) gold landing thump + real wind chimes for the golden wave and the rise
t_=np.arange(int(0.35*SR))/SR; thump=(np.sin(2*np.pi*(95-60*t_)*t_)*np.exp(-t_*14)).astype(np.float32)
add(dry,thump,C.LT,0.55)
wc=load('wc.wav')
def seg(a,d,fi,fo):
    y=wc[int(a*SR):int((a+d)*SR)].copy(); n=len(y); e=np.ones(n,np.float32)
    k=int(fi*SR); e[:k]=np.linspace(0,1,k); k=int(fo*SR); e[-k:]*=np.linspace(1,0,k); return y*e[:,None]
add(fx,seg(0.6,T-C.LT+0.2,0.15,1.0),C.LT+0.05,0.38)
add(fx,rs(seg(5.9,T-C.TREL,0.05,1.0),1.26),C.TREL+0.1,0.36)
# 4) music bed: builds under the stuck phase, cut by the first shatter
mu=load('mus.wav'); n=len(mu); tt=np.arange(n)/SR
env=np.interp(tt,[0,0.4,C.OUT-0.05,C.OUT+0.9,T],[0,0.16,0.30,0.0,0.0]).astype(np.float32)
add(dry,mu*env[:,None],0,1.0)
board=Pedalboard([HighpassFilter(80),Reverb(room_size=0.3,damping=0.5,wet_level=0.16,dry_level=0.9,width=1.0)])
out=board(fx.T,SR).T+dry
out=out[:int(T*SR)]
out=Pedalboard([Compressor(threshold_db=-16,ratio=2.5),Limiter(threshold_db=-1.2)])(out.T,SR).T
out/=max(1e-6,np.abs(out).max())*1.04
k=int(0.35*SR); out[-k:]*=np.linspace(1,0,k)[:,None]
wavfile.write('a.wav',SR,(out*32767).astype(np.int16))
w=SR//2; print('rms per 0.5s:',' '.join(f'{np.sqrt((out[i:i+w]**2).mean()):.2f}' for i in range(0,len(out)-w,w)))
