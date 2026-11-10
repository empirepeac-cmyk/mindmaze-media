import numpy as np, math, pickle, sys
N=12; R0=110; DR=34; W=8; RB=13
RAD=[R0+DR*i for i in range(N)]
GAP=math.radians(58)
FPS=60; SUB=20; DT=1/(FPS*SUB)
G=1500.0
def omega(i): return (1 if i%2==0 else -1)*(2.3-0.09*i)
def sim(seed, vmin=820.0, maxT=60):
    rng=np.random.default_rng(seed)
    ph=rng.uniform(0,2*math.pi,N)
    a=rng.uniform(0,2*math.pi)
    p=np.array([0.0,-20.0]); v=np.array([math.cos(a),math.sin(a)])*vmin
    cur=0; t=0.0; frames=[]; ev=[]; step=0
    while t<maxT:
        if step%SUB==0: frames.append((p[0],p[1],cur))
        v[1]+=G*DT; p=p+v*DT; t+=DT; step+=1
        if cur<N:
            R=RAD[cur]; r=math.hypot(*p)
            if r>=R-W/2-RB:
                n=p/r; vn=v@n
                th=math.atan2(p[1],p[0]); gc=ph[cur]+omega(cur)*t
                d=(th-gc+math.pi)%(2*math.pi)-math.pi
                if abs(d)<GAP/2-RB/R*0.85:
                    if r>=R:
                        ev.append((t,'break',cur,p[0],p[1])); cur+=1
                        if cur==N: tend=t
                elif vn>0:
                    v=v-2*vn*n
                    s=np.linalg.norm(v); s2=max(s,vmin)*1.004
                    v=v/s*min(s2,1150)
                    p=n*(R-W/2-RB-0.01)
                    ev.append((t,'hit',cur,p[0]+n[0]*RB,p[1]+n[1]*RB))
        else:
            if t>tend+4.0: break
    else: return None
    return dict(frames=frames,ev=ev,ph=ph,tend=tend,seed=seed)
if __name__=='__main__':
    best=[]
    for s in range(400):
        r=sim(s,maxT=40)
        if not r: continue
        bt=[0]+[e[0] for e in r['ev'] if e[1]=='break']
        dw=np.diff(bt); nb=sum(1 for e in r['ev'] if e[1]=='hit')
        if 21<r['tend']<29 and dw.max()<4.6 and dw[-1]>1.2 and dw[0]>0.8:
            best.append((dw.std(),s,r['tend'],nb,dw.round(1)))
    best.sort()
    for b in best[:8]: print(b[1],round(b[2],1),b[3],b[4])
