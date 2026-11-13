import pymunk, random, math, sys
import sim
from sim import *
CX,CY=540,744   # cup bottom centre
def build3(depth, half=30):
    sp=pymunk.Space(); sp.gravity=(0,1900); sp.iterations=30
    sb=sp.static_body
    for a,b in [((XL,400),(XL,FLOOR)),((XR,400),(XR,FLOOR)),((XL,FLOOR),(XR,FLOOR))]:
        s=pymunk.Segment(sb,a,b,6); s.elasticity=0.35; s.friction=0.6; sp.add(s)
    for dx in DIVX:
        s=pymunk.Segment(sb,(dx,DIV_TOP),(dx,FLOOR),5); s.elasticity=0.35; s.friction=0.5; sp.add(s)
    pg=[p for p in PEGS if math.hypot(p[0]-CX,p[1]-CY)>75 and not (abs(p[0]-CX)<60 and p[1]<CY)]
    for (x,y) in pg:
        c=pymunk.Circle(sb,PEG_R,(x,y)); c.elasticity=0.3; c.friction=0.2; sp.add(c)
    cup=[((CX-half,CY-depth),(CX-10,CY)),((CX-10,CY),(CX+10,CY)),((CX+10,CY),(CX+half,CY-depth))]
    for a,b in cup:
        s=pymunk.Segment(sb,a,b,4); s.elasticity=0.2; s.friction=0.5; sp.add(s)
    return sp,pg,cup
def run(seed, depth=14, T=18.0, t0=0.9, t1=11.5, gt=0.35, record=True, half=30):
    rnd=random.Random(seed)
    sp,pg,cup=build3(depth,half)
    order=[]
    for row in range(4):
        idx=[i for i,t in enumerate(TRAY) if t[2]==row]; rnd.shuffle(idx); order+=idx
    n=len(order); rel={i:t0+(t1-t0)*k/(n-1) for k,i in enumerate(order)}
    pend=sorted(rel.items(), key=lambda kv:kv[1]); pi=0
    bodies={}; mat={}; frames=[]; ev=[]; gold=None
    st={'in':None,'out':None,'nrel':None,'ghits':0}
    data={'t':0}
    def post(arb,space,d):
        if arb.is_first_contact:
            a,b=arb.shapes
            imp=arb.total_impulse.length
            g=(a.collision_type==2 or b.collision_type==2)
            if g and st['in'] and not st['out'] and (a.collision_type==1 or b.collision_type==1): st['ghits']+=1
            if imp>80: ev.append((d['t'],imp,1 if g else 0))
    sp.on_collision(None,None,post_solve=post,data=data)
    for f in range(int(T*60)):
        t=f/60; data['t']=t
        while pi<len(pend) and pend[pi][1]<=t:
            i=pend[pi][0]; x,y,_=TRAY[i]
            b,c=ball(sp,x+rnd.uniform(-1,1),y,RB,1); c.bid=i; bodies[i]=b; pi+=1
        if gold is None and t>=gt: gold,gc=ball(sp,CX+rnd.uniform(-2,2),400,RG,2,el=0.25)
        for _ in range(SUB): sp.step(DT)
        if gold:
            gp=gold.position
            inside=abs(gp.x-CX)<half and CY-70<gp.y<CY
            if st['in'] is None and inside and gold.velocity.length<40: st['in']=t
            if st['in'] and st['out'] is None and (gp.y>CY+30 or abs(gp.x-CX)>half+25): st['out']=t; st['nrel']=pi
        for i,b in bodies.items():
            if i not in mat and (b.position.y>DIV_TOP+RB or (b.position.y>DIV_TOP-170 and b.velocity.length<60)):
                x=b.position.x; mat[i]=(0 if x<DIVX[0] else 1 if x<DIVX[1] else 2, t)
        if record:
            frames.append(({i:(b.position.x,b.position.y) for i,b in bodies.items()},(gold.position.x,gold.position.y) if gold else None))
    g=gold.position
    return dict(frames=frames,ev=ev,mat=mat,st=st,gold_bin=0 if g.x<DIVX[0] else 1 if g.x<DIVX[1] else 2,gold_pos=(g.x,g.y),
                gsp=gold.velocity.length,rel=rel,pegs=pg,cup=cup,gt=gt,seed=seed,depth=depth,t1=t1)
def job(a):
    seed,depth=a
    r=run(seed,depth,record=False)
    s=r['st']
    return seed,depth,s['in'],s['out'],s['nrel'],s['ghits'],r['gold_bin'],round(r['gold_pos'][1]),round(r['gsp'])
if __name__=='__main__':
    from multiprocessing import Pool
    ds=[int(x) for x in sys.argv[1].split(',')]; seeds=range(int(sys.argv[2]),int(sys.argv[3]))
    with Pool(4) as p:
        for r in p.imap(job,[(s,d) for d in ds for s in seeds]): print(r,flush=True)
