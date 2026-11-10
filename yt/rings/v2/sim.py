import numpy as np, math, pickle, sys
N=15; R0=96; DR=27.5; W=7; RB=11
RAD=[R0+DR*i for i in range(N)]
GAPS=[math.radians(g) for g in np.linspace(68,38,N)]
FPS=60; SUB=20; DT=1/(FPS*SUB)
G=1500.0; LIMIT=30.0
def omega(i): return (1 if i%2==0 else -1)*(2.5-0.085*i)
def sim(seed, vmin=900.0, maxT=60):
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
                if abs(d)<GAPS[cur]/2-RB/R*0.85:
                    if r>=R:
                        ev.append((t,'break',cur,p[0],p[1])); cur+=1
                        if cur==N: tend=t
                elif vn>0:
                    v=v-2*vn*n
                    s=np.linalg.norm(v); s2=max(s,vmin)*1.004
                    v=v/s*min(s2,1200)
                    p=n*(R-W/2-RB-0.01)
                    ev.append((t,'hit',cur,p[0]+n[0]*RB,p[1]+n[1]*RB))
        else:
            if t>tend+4.2: break
    else: return None
    return dict(frames=frames,ev=ev,ph=ph,tend=tend,seed=seed)
def f(s):
    r=sim(s,maxT=33.8)
    if not r: return None
    bt=[0]+[e[0] for e in r['ev'] if e[1]=='break']
    return (s,round(r['tend'],2),sum(1 for e in r['ev'] if e[1]=='hit'),np.diff(bt).round(1))
if __name__=='__main__':
    from multiprocessing import Pool
    with Pool(4) as p: res=[x for x in p.map(f,range(int(sys.argv[1]),int(sys.argv[2]))) if x]
    print(len(res))
    for x in res:
        if 27.6<x[1]<29.5: print(s:=x[0],x[1],x[2],list(x[3]))
