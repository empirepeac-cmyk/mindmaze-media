import numpy as np,os,subprocess
from scipy import signal
from scipy.io import wavfile
from pedalboard import Pedalboard,Reverb,Compressor,Limiter,HighpassFilter
SR=48000; m=np.load('map.npy'); NFR=len(m); DUR=NFR/24; N=int(SR*DUR); rng=np.random.default_rng(11)
L=np.zeros(N);R=np.zeros(N)
def tn(t_old):
    """old film time -> time in Sepehr's cut (first frame showing that old frame or later)"""
    f=t_old*24+1; i=np.nonzero((m>=f)&(m<f+40))[0]
    if len(i)==0: return None
    i=i[0]; return (i+ (f-m[i] if m[i]>f else 0))/24.0
def add(x,t,g=1.0,pan=0.0):
    if t is None: return
    i=int(t*SR)
    if i>=N or i<0: return
    x=x[:N-i]; L[i:i+len(x)]+=x*g*np.sqrt((1-pan)/2); R[i:i+len(x)]+=x*g*np.sqrt((1+pan)/2)
def bp(x,lo,hi,o=2): return signal.sosfilt(signal.butter(o,[lo,hi],btype='band',fs=SR,output='sos'),x)
def lp(x,f,o=2): return signal.sosfilt(signal.butter(o,f,btype='low',fs=SR,output='sos'),x)
def hp(x,f,o=2): return signal.sosfilt(signal.butter(o,f,btype='high',fs=SR,output='sos'),x)
def remap(v): return np.asarray(v,float)[np.clip(m,0,len(v)-1)]          # per-new-frame values
def env(v,smooth=2.0):
    v=signal.medfilt(np.asarray(v,float),3); k=np.hanning(int(smooth*2+3)); v=np.convolve(v,k/k.sum(),'same')
    return np.interp(np.arange(N)/SR*24,np.arange(len(v)),v)
_c={}
def load(p):
    if p not in _c:
        tmp='/tmp/claude-0/-home-user/7503926b-fbab-5c1c-9fde-d9a76afa4905/scratchpad/_l.wav'
        subprocess.run(['ffmpeg','-y','-loglevel','error','-i',p,'-ac','1','-ar',str(SR),tmp],check=True)
        _c[p]=wavfile.read(tmp)[1].astype(np.float64)/32768
    return _c[p]
def rs(x,rate): return signal.resample(x,max(8,int(len(x)/rate))) if rate!=1 else x
def mk(i,rate=1.0,a=0,b=None):
    x=load(f'mk/{i}.wav'); x=x[int(a*SR):int(b*SR) if b else None]; x=x/np.abs(x).max(); return rs(x,rate)
K='../robot/sfx/kenney/'
def kn(p,rate=1.0): return rs(load(K+p+'.ogg'),rate)
def fade(x,fi=0.005,fo=0.05):
    x=x.copy(); a=int(fi*SR); b=int(fo*SR); x[:a]*=np.linspace(0,1,a); x[-b:]*=np.linspace(1,0,b); return x
def beep(notes,vib=0.0,gl=0.02):
    out=[]
    for f0,f1,d,gap in notes:
        n=int(d*SR); t=np.arange(n)/SR; f=f0*(f1/f0)**(t/d)
        if vib: f=f*(1+vib*np.sin(2*np.pi*28*t))
        ph=2*np.pi*np.cumsum(f)/SR; y=np.sin(ph+0.9*np.sin(2*ph))*0.6+0.25*np.sin(2*ph)
        a=np.minimum(1,t/0.008)*np.minimum(1,(d-t)/gl); out+=[y*a,np.zeros(int(gap*SR))]
    return bp(np.concatenate(out),350,5200)
M=np.load('../robot/motion.npy'); M=np.concatenate([[0],M,[0]]); B=np.load('../robot/brush.npy').copy()
for c in (1,2,71,72,73,74,170,171,172,173,249,250,251,252,253,299,300,301,340,341,342,358,359,360,361,362,433,434,528,529,530,703,704): M[c]=0
for c in (249,250,338,339,340,341,701,702): B[c]=0
cut=np.concatenate([[False],np.abs(np.diff(m)-1)>1])                       # his edit points
# ---- room + rain bed
endt=tn(31.2) or DUR-3
room=lp(rng.standard_normal(N),140)*0.5+bp(rng.standard_normal(N),300,1200)*0.05
rain=load('mk/2393.wav'); rain=np.tile(rain,int(N/len(rain))+2)[:N]
fd=np.clip((endt-np.arange(N)/SR)/0.6,0,1)*np.clip(np.arange(N)/SR/0.5,0,1)
add((room*0.08+hp(rain,800)*0.10)*fd,0)
# ---- servo follows body motion
body=M.copy(); body[160:252]*=0.35; body[300:342]*=0.35; body[560:703]*=0.5; body[250:300]=0; body[341:360]=0; body[745:]=0
bn=remap(body); bn[cut]=0
e=env(bn,2.5); e=np.clip((e-0.9)/7.0,0,1)**0.8
ph=2*np.pi*np.cumsum(170+520*e)/SR
serv=bp(signal.sawtooth(ph)*0.5+signal.sawtooth(ph*2.01)*0.25,300,2600)+bp(rng.standard_normal(N),900,3000)*0.25
add(serv*e*0.045,0,1.0,-0.05)
def wheels(o0,o1,g):
    t0,t1=tn(o0),tn(o1)
    if t0 is None or t1 is None or t1<=t0: return
    n=int((t1-t0)*SR); t=np.arange(n)/SR; a=np.minimum(1,t/0.25)*np.minimum(1,(t1-t0-t)/0.2)
    add((lp(rng.standard_normal(n),220)*1.3+bp(rng.standard_normal(n),500,1400)*0.12*(0.6+0.4*np.sin(2*np.pi*9*t)))*a,t0,g)
wheels(15.15,17.3,0.07); wheels(21.9,23.3,0.06); wheels(0.55,0.8,0.05)
# ---- BRUSH: one real recorded stroke per visible stroke
def strokes(src,thr=0.12,mind=0.12):
    x=load(src); x=x/np.abs(x).max(); n=int(0.01*SR); ev=np.sqrt(np.convolve(x**2,np.ones(n)/n,'same')); on=ev>thr*ev.max()
    on=np.convolve(on,np.ones(int(0.04*SR)),'same')>0; out=[]; d=np.diff(on.astype(int)); st=np.nonzero(d==1)[0]; en=np.nonzero(d==-1)[0]
    for s in st:
        e_=en[en>s]
        if len(e_) and (e_[0]-s)/SR>=mind: out.append(fade(x[s:e_[0]],0.01,0.03))
    return out
G=strokes('mk/165.wav')+strokes('mk/162.wav')+strokes('mk/3086.wav')
G=[g/np.sqrt((g**2).mean()) *0.1 for g in G if 0.12<len(g)/SR<0.9]
print('real strokes available',len(G),'median len',np.median([len(g)/SR for g in G]))
Bs=np.zeros_like(B)
for a_,b_ in [(160,250),(300,341),(560,703)]:
    seg=np.convolve(signal.medfilt(B[a_:b_],3),[.25,.5,.25],'same'); p=np.percentile(seg,92); Bs[a_:b_]=np.clip((seg-2.0)/(p-2.0),0,1.3)
bnew=remap(Bs); bnew[cut]=0
sm=np.convolve(bnew,np.hanning(7)/np.hanning(7).sum(),'same'); act=sm>0.14
nst=0; i=0
while i<NFR:
    if not act[i]: i+=1; continue
    j=i+int(np.argmax(bnew[i:i+3]))                    # snap to the local motion peak
    h=max(bnew[j],sm[j]); dur=rng.uniform(0.2,0.3)
    g=G[rng.integers(len(G))]; rate=np.clip(len(g)/SR/dur,1.0,2.4); x=rs(g,rate)
    wet=(j/24)>(tn(23.5) or 99)
    x=hp(x,500) if not wet else hp(x,350)*0.75+lp(x,1800)*0.6
    add(fade(x,0.008,0.04),max(0,j/24-0.04),0.5*min(1.15,h)**0.7,0.12+rng.uniform(-.05,.05)); nst+=1
    i=j+int(rng.integers(5,7))
print('strokes placed',nst)
# ---- lamp hum only while the lamp is on screen
lam=((m>=252)&(m<=299))|((m>=343)&(m<=358)); d=np.diff(np.concatenate([[0],lam.astype(int),[0]]))
for s,e_ in zip(np.nonzero(d==1)[0],np.nonzero(d==-1)[0]):
    if e_-s<8: continue
    n=int((e_-s)/24*SR); t=np.arange(n)/SR; a=np.minimum(1,t/0.05)*np.minimum(1,(n/SR-t)/0.05)
    y=0.5*np.sin(2*np.pi*100*t)+0.25*np.sin(2*np.pi*200*t)+0.12*signal.sawtooth(2*np.pi*100*t)+bp(signal.square(2*np.pi*100*t),2000,6000)*0.05
    add(y*a,s/24,0.03)
# ---- BIN: real recordings
add(mk(833,0.62),tn(17.34),0.22,0.35)                      # robot's back knocks the bin
add(kn('rpg-audio/Audio/creak2',0.85),tn(17.5),0.07,0.4)   # it tips
tc=tn(17.96)
add(mk(2980,0.78),tc,0.85,0.4)                              # bin slams on the floor
add(mk(835,0.7),tc+0.02,0.55,0.45)
add(fade(mk(398,1.0,0.1,2.6),0.01,1.2),tc+0.05,0.5,0.35)    # rubbish pours out
add(mk(3158,0.9),tc+0.2,0.45,0.3)                           # lid lands and rattles
add(mk(389,1.0),tc+0.42,0.4,0.45)                           # tins bounce
add(mk(389,1.35),tc+0.95,0.22,0.2)
add(mk(820,1.3),tc+0.7,0.2,0.5)
add(kn('x/Audio/impactWood_light_000',1.0),tn(15.0),0.14,0.0)   # brush put down
add(kn('x/Audio/impactWood_light_002',1.3),tn(23.75),0.07,-0.3) # brush picked up
# ---- robot voice
V=[(0.95,[(620,900,.09,.05),(900,1250,.13,0)],.06),(3.05,[(700,1050,.16,0)],.05),(6.55,[(520,500,.07,.05),(520,500,.07,0)],.05),
   (10.15,[(480,300,.28,0)],.06),(15.05,[(660,990,.10,.04),(990,1320,.16,0)],.06),(18.45,[(1500,1700,.06,.04),(1500,1700,.06,0)],.06),
   (20.0,[(700,380,.45,0)],.05),(29.35,[(420,250,.5,0)],.05)]
for t,n,g in V: add(beep(n,vib=0.012 if n[0][2]>.25 else 0),tn(t),g)
tt=np.nonzero(m>=762)[0]
if len(tt):
    t=np.arange(int(2.2*SR))/SR; add(sum(a*np.sin(2*np.pi*f*t)*np.exp(-t/d) for f,d,a in [(220,1.6,1),(440,1.2,.4),(660,.8,.2)]),tt[0]/24,0.02)
st=np.stack([L,R]).astype(np.float32)
st=Pedalboard([HighpassFilter(35),Reverb(room_size=0.3,wet_level=0.12,dry_level=0.9,damping=0.6),Compressor(threshold_db=-14,ratio=2.5),Limiter(threshold_db=-1.5)])(st,SR)
st=st/np.abs(st).max()*0.89; wavfile.write('newa.wav',SR,(st.T*32767).astype(np.int16))
x=st.mean(0); n=SR//4; r=[20*np.log10(np.sqrt((x[i:i+n]**2).mean())+1e-9) for i in range(0,len(x)-n,n)]
for i in range(0,len(r),8): print(f'{i/4:5.1f}',' '.join(f'{v:4.0f}' for v in r[i:i+8]))
print('crash at',tc,'lamp',[(s/24,e_/24) for s,e_ in zip(np.nonzero(d==1)[0],np.nonzero(d==-1)[0])])
