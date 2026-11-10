import numpy as np, pickle, math
from scipy.io import wavfile
from scipy.signal import fftconvolve
from sim import N
S=pickle.load(open('sim.pkl','rb')); SR=48000
T=len(S['frames'])/60; out=np.zeros((int(T*SR)+SR,2))
rng=np.random.default_rng(3)
def note(f,dur=1.1,vel=1.0):
    t=np.arange(int(dur*SR))/SR
    y=np.sin(2*np.pi*f*t)*np.exp(-t*5.5)
    y+=0.35*np.sin(2*np.pi*f*2.0*t)*np.exp(-t*9)
    y+=0.22*np.sin(2*np.pi*f*5.4*t+0.3)*np.exp(-t*38)
    y+=0.10*np.sin(2*np.pi*f*8.9*t)*np.exp(-t*60)
    k=rng.normal(0,1,len(t))*np.exp(-t*380)*0.25
    y=(y+k)*np.minimum(t/0.0015,1)
    return y*vel
def add(y,t,pan=0.0,g=1.0):
    i=int(t*SR); n=min(len(y),len(out)-i)
    out[i:i+n,0]+=y[:n]*g*(1-max(0,pan)*0.6); out[i:i+n,1]+=y[:n]*g*(1+min(0,pan)*0.6)
penta=[0,2,4,7,9]
def fr(k): return 261.63*2**((12*(k//5)+penta[k%5])/12)
nh=0
for e in S['ev']:
    t,kind,i,x,y=e
    if kind=='hit':
        k=i+[0,2,1,3][nh%4]; nh+=1
        add(note(fr(k),vel=0.55+0.1*rng.random()),t,pan=-x/600)
    else:
        last=(i==N-1)
        # shatter: bright chime cluster + filtered noise
        d=1.6 if not last else 3.2; tt=np.arange(int(d*SR))/SR
        y=np.zeros_like(tt)
        for j,sem in enumerate([0,7,12,16,19,24] if last else [12,19,24]):
            y+=np.sin(2*np.pi*fr(i)*2**(sem/12)*tt)*np.exp(-tt*(3.0 if last else 6))*0.25
        nz=rng.normal(0,1,len(tt)); nz=np.diff(nz,prepend=0)
        y+=nz*np.exp(-tt*(9 if last else 22))*0.10
        add(y,t,g=0.9 if last else 0.6)
        if last:
            for j,k in enumerate([10,12,14,15,17,19,20]): add(note(fr(k),1.6,0.6),t+0.09*j+0.05)
# reverb
ir_t=np.arange(int(1.4*SR))/SR; ir=rng.normal(0,1,(len(ir_t),2))*np.exp(-ir_t*4.5)[:,None]; ir[:int(0.012*SR)]=0
wet=np.stack([fftconvolve(out[:,c],ir[:,c])[:len(out)] for c in (0,1)],1)
out=out+wet*0.018
out=out[:int(T*SR)]; out/=np.abs(out).max()*1.05
out[-int(0.4*SR):]*=np.linspace(1,0,int(0.4*SR))[:,None]
wavfile.write('a.wav',SR,(out*32767).astype(np.int16))
