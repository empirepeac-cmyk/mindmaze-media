import pymunk, random, math, pickle, sys
W,H=1080,1920
RB=16; RG=20
FLOOR=1740; DIVH=78; DIV_TOP=FLOOR-DIVH
XL,XR=60,1020
BW=(XR-XL)/3
DIVX=[XL+BW, XL+2*BW]
PEG_R=9
def pegs():
    P=[]
    y=560; r=0
    while y<=1390:
        if r%2: xs=[XL+k*96 for k in range(11)]
        else: xs=[XL+48+k*96 for k in range(1,9)]
        P+=[(x,y) for x in xs]
        y+=92; r+=1
    return P
PEGS=pegs()
# tray positions: 4 rows
def tray():
    T=[]
    for row in range(4):
        n=25 if row<3 else 24
        y=330-row*33
        x0=540-(n-1)*17
        for i in range(n): T.append((x0+i*34,y,row))
    return T
TRAY=tray()
def build():
    sp=pymunk.Space(); sp.gravity=(0,1900); sp.iterations=30
    sb=sp.static_body
    segs=[((XL,400),(XL,FLOOR)),((XR,400),(XR,FLOOR)),((XL,FLOOR),(XR,FLOOR))]
    for a,b in segs:
        s=pymunk.Segment(sb,a,b,6); s.elasticity=0.35; s.friction=0.6; sp.add(s)
    for dx in DIVX:
        s=pymunk.Segment(sb,(dx,DIV_TOP),(dx,FLOOR),5); s.elasticity=0.35; s.friction=0.5; sp.add(s)
    for (x,y) in PEGS:
        c=pymunk.Circle(sb,PEG_R,(x,y)); c.elasticity=0.3; c.friction=0.2; sp.add(c)
    return sp
def ball(sp,x,y,r,ct,el=0.42,vx=0):
    m=1.0*(r/RB)**2
    b=pymunk.Body(m,pymunk.moment_for_circle(m,0,r)); b.position=(x,y); b.velocity=(vx,0)
    c=pymunk.Circle(b,r); c.elasticity=el; c.friction=0.45; c.collision_type=ct
    sp.add(b,c); return b,c
DT=1/240; SUB=4  # 60fps
def whites(seed, t0=0.4, t1=6.0):
    rnd=random.Random(seed)
    sp=build()
    order=[]
    for row in range(4):
        idx=[i for i,t in enumerate(TRAY) if t[2]==row]; rnd.shuffle(idx); order+=idx
    n=len(order)
    rel={i: t0+(t1-t0)*k/(n-1) for k,i in enumerate(order)}
    return sp,rel,rnd
def run(seed, gx, gt=8.6, gvx=0.0, T=17.0, record=True):
    sp,rel,rnd=whites(seed)
    bodies={}; mat={}
    frames=[]; ev=[]
    gold=None; info={'first':None,'hits':[]}
    def post(arb,space,data):
        a,b=arb.shapes
        if arb.is_first_contact:
            imp=arb.total_impulse.length
            other=b if a.collision_type==2 else a
            if a.collision_type==2 or b.collision_type==2:
                kind='ball' if other.collision_type==1 else ('peg' if isinstance(other,pymunk.Circle) else 'wall')
                oid=getattr(other,'bid',None)
                info['hits'].append((data['t'],kind,oid,imp,tuple(gold.position)))
            elif imp>60:
                ev.append((data['t'],imp,0))
    data={'t':0}
    sp.on_collision(None,None,post_solve=post,data=data)
    nf=int(T*60)
    pend=sorted(rel.items(), key=lambda kv:kv[1])
    pi=0
    for f in range(nf):
        t=f/60; data['t']=t
        while pi<len(pend) and pend[pi][1]<=t:
            i=pend[pi][0]; x,y,_=TRAY[i]
            b,c=ball(sp,x+rnd.uniform(-1,1),y,RB,1); c.bid=i; bodies[i]=b; pi+=1
        if gold is None and t>=gt:
            gold,gc=ball(sp,gx,170,RG,2,el=0.4,vx=gvx)
        for _ in range(SUB): sp.step(DT)
        for i,b in bodies.items():
            if i not in mat and (b.position.y>DIV_TOP+RB or (b.position.y>DIV_TOP-170 and b.velocity.length<60)):
                x=b.position.x
                mat[i]=(0 if x<DIVX[0] else 1 if x<DIVX[1] else 2, t)
        if record:
            frames.append(({i:(b.position.x,b.position.y,b.angle) for i,b in bodies.items()},
                           (gold.position.x,gold.position.y,gold.angle) if gold else None))
    g=gold.position; gb=0 if g.x<DIVX[0] else 1 if g.x<DIVX[1] else 2
    final={i:(b.position.x,b.position.y) for i,b in bodies.items()}
    return dict(frames=frames,ev=ev,mat=mat,hits=info['hits'],gold_bin=gb,gold_pos=(g.x,g.y),
                gold_speed=gold.velocity.length,rel=rel,gt=gt,final=final,seed=seed,gx=gx)
if __name__=='__main__':
    seed=int(sys.argv[1])
    r=run(seed,700,record=False)
    cnt=[0,0,0]
    for i,(m,t) in r['mat'].items(): cnt[m]+=1
    ys=[min([p[1] for i,p in r['final'].items() if r['mat'].get(i,(9,))[0]==k] or [0]) for k in range(3)]
    print(seed,cnt,[round(y) for y in ys],'divtop',DIV_TOP,r['gold_bin'],r['gold_pos'])
