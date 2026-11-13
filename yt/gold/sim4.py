import pymunk, random, math, sys
from sim import *
CX,CY=540,744; HALF=32; DEPTH=24
def run(seed, D=None, T=19.0, t0=0.9, t1=11.5, gt=0.35, record=True, IMIN=250):
    rnd=random.Random(seed)
    sp=pymunk.Space(); sp.gravity=(0,1900); sp.iterations=30
    sb=sp.static_body
    for a,b in [((XL,400),(XL,FLOOR)),((XR,400),(XR,FLOOR)),((XL,FLOOR),(XR,FLOOR))]:
        s=pymunk.Segment(sb,a,b,6); s.elasticity=0.35; s.friction=0.6; sp.add(s)
    for dx in DIVX:
        s=pymunk.Segment(sb,(dx,DIV_TOP),(dx,FLOOR),5); s.elasticity=0.35; s.friction=0.5; sp.add(s)
    pg=[p for p in PEGS if math.hypot(p[0]-CX,p[1]-CY)>75 and not (abs(p[0]-CX)<60 and p[1]<CY)]
    for (x,y) in pg:
        c=pymunk.Circle(sb,PEG_R,(x,y)); c.elasticity=0.3; c.friction=0.2; sp.add(c)
    cup=[((CX-HALF,CY-DEPTH),(CX-10,CY)),((CX-10,CY),(CX+10,CY)),((CX+10,CY),(CX+HALF,CY-DEPTH))]
    cs=[]
    for a,b in cup:
        s=pymunk.Segment(sb,a,b,4); s.elasticity=0.2; s.friction=0.5; s.collision_type=3; sp.add(s); cs.append(s)
    order=[]
    for row in range(4):
        idx=[i for i,t in enumerate(TRAY) if t[2]==row]; rnd.shuffle(idx); order+=idx
    n=len(order); rel={i:t0+(t1-t0)*k/(n-1) for k,i in enumerate(order)}
    pend=sorted(rel.items(), key=lambda kv:kv[1]); pi=0
    bodies={}; mat={}; frames=[]; ev=[]; gold=None
    st={'dmg':0.0,'hits':[],'brk':None,'pending':False}
    data={'t':0}
    def post(arb,space,d):
        if not arb.is_first_contact: return
        a,b=arb.shapes; ct={a.collision_type,b.collision_type}
        imp=arb.total_impulse.length
        if 1 in ct and (2 in ct or 3 in ct) and st['brk'] is None and gold is not None and imp>=IMIN:
            st['dmg']+=imp; st['hits'].append((d['t'],imp,st['dmg']))
            if D is not None and st['dmg']>=D: st['pending']=True
        if imp>80: ev.append((d['t'],imp,1 if 2 in ct else 0))
    sp.on_collision(None,None,post_solve=post,data=data)
    for f in range(int(T*60)):
        t=f/60; data['t']=t
        while pi<len(pend) and pend[pi][1]<=t:
            i=pend[pi][0]; x,y,_=TRAY[i]
            b,c=ball(sp,x+rnd.uniform(-1,1),y,RB,1); c.bid=i; bodies[i]=b; pi+=1
        if gold is None and t>=gt: gold,gc=ball(sp,CX+rnd.uniform(-2,2),400,RG,2,el=0.25)
        for _ in range(SUB):
            sp.step(DT)
            if st['pending'] and st['brk'] is None:
                for s in cs: sp.remove(s)
                st['brk']=t; st['nrel']=pi
        for i,b in bodies.items():
            if i not in mat and (b.position.y>DIV_TOP+RB or (b.position.y>DIV_TOP-170 and b.velocity.length<60)):
                x=b.position.x; mat[i]=(0 if x<DIVX[0] else 1 if x<DIVX[1] else 2, t)
        if record:
            frames.append(({i:(b.position.x,b.position.y) for i,b in bodies.items()},(gold.position.x,gold.position.y) if gold else None))
    g=gold.position
    return dict(frames=frames,ev=ev,mat=mat,st=st,gold_bin=0 if g.x<DIVX[0] else 1 if g.x<DIVX[1] else 2,gold_pos=(g.x,g.y),
                rel=rel,pegs=pg,cup=cup,gt=gt,seed=seed,t1=t1,D=D)
def job(seed):
    r=run(seed,record=False)
    h=r['st']['hits']
    # hits up to when last ball released and after
    return seed,len(h),round(r['st']['dmg']),[ (round(t,2),round(d)) for t,i,d in h if t>10.6], round(r['gold_pos'][1])
if __name__=='__main__':
    from multiprocessing import Pool
    with Pool(4) as p:
        for r in p.imap(job,range(int(sys.argv[1]),int(sys.argv[2]))): print(r,flush=True)
