import sim6 as sim4, sim, sys, random, subprocess, math, pickle
from PIL import Image, ImageDraw, ImageFont
seed=int(sys.argv[1]); D=float(sys.argv[2]); out=sys.argv[3]
r=sim4.run(seed,D=D,T=19.5)
FR=r['frames']; mat=r['mat']; st=r['st']; rel=r['rel']
pickle.dump(r,open(f'run5_{seed}.pkl','wb'))
HITS=st['hits']
rest=0
for f in range(len(FR)-30,0,-1):
    a=FR[f][1]; b=FR[f-1][1]
    if a and b and math.hypot(a[0]-b[0],a[1]-b[1])>0.35: rest=(f+1)/60; break
OUT=st['brk']; print('hits',len(HITS),'out',OUT,'rest',rest,'bin',r['gold_bin'])
LT,LP=st['land']; print('land',LT)
T_FX=LT; WSP=330.0
dmax=max(math.hypot(p[0]-LP[0],p[1]-LP[1]) for p in r['final'])
TREL=st['trel']; T_CUT=TREL+2.7; END=T_CUT+0.8; print('trel',TREL)
ZA=1.45; YA=sim4.CY-0.47*1920/ZA
ZMAX=1.3; PADB=500; CXT=540
Y0T=1560-0.58*1920/ZMAX
FD='/mnt/skills/examples/canvas-design/canvas-fonts/'
f1=ImageFont.truetype(FD+'BigShoulders-Bold.ttf',40); f3=ImageFont.truetype(FD+'GeistMono-Bold.ttf',24)
COL=[(255,106,42),(150,215,255),(176,182,192)]
GOLD=(255,196,40); WH=(240,240,244); BG=(18,20,26); FRM=(90,96,110)
def mix(a,b,k): return tuple(int(a[i]+(b[i]-a[i])*k) for i in range(3))
def ease(x): x=max(0,min(1,x)); return x*x*(3-2*x)
# camera progress follows gold's height after the break (smoothed)
NF=int(END*60); EP=[]; cur=0.0
for f in range(NF):
    g=FR[min(f,len(FR)-1)][1]; t=f/60
    tgt=0.0
    if g and t>OUT: tgt=max(0,min(1,(g[1]-sim4.CY-30)/(1380-sim4.CY)))
    tgt=max(tgt,cur) ; cur+= (tgt-cur)*0.09; EP.append(cur)
p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','540x960','-r','30','-i','-',
  '-c:v','libx264','-crf','22','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
S=2
def P(v): return v*S
ff=ImageFont.truetype(FD+'BigShoulders-Bold.ttf',44*S)
for f in range(0,int(END*60),2):
    t=f/60; nxt=t>=T_CUT
    im=Image.new('RGB',(1080*S,(1920+PADB)*S),BG); d=ImageDraw.Draw(im)
    def circ(x,y,rad,**k): d.ellipse([P(x-rad),P(y-rad),P(x+rad),P(y+rad)],**k)
    d.line([(P(sim.XL),P(400)),(P(sim.XL),P(1290))],fill=FRM,width=10*S)
    d.line([(P(sim.XR),P(400)),(P(sim.XR),P(1290))],fill=FRM,width=10*S)
    d.line([(P(x),P(y)) for x,y in r['pot'][:2]],fill=FRM,width=10*S); d.line([(P(x),P(y)) for x,y in r['pot'][-2:]],fill=FRM,width=10*S)
    if t<TREL: d.line([(P(x),P(y)) for x,y in r['pot'][1:-1]],fill=(170,225,255),width=9*S,joint='curve')
    else:
        rr=random.Random(21); dt=t-TREL; pp=r['pot'][1:-1]
        for n in range(40):
            k=rr.randrange(len(pp)-1); u=rr.random()
            x0=pp[k][0]+(pp[k+1][0]-pp[k][0])*u; y0_=pp[k][1]+(pp[k+1][1]-pp[k][1])*u
            vx=(x0-540)*rr.uniform(0.8,2.2); vy=rr.uniform(-250,150)
            x=x0+vx*dt; y=y0_+vy*dt+900*dt*dt; a=rr.uniform(0,6.28)+dt*rr.uniform(-9,9); L=rr.uniform(8,18)
            d.line([(P(x-math.cos(a)*L),P(y-math.sin(a)*L)),(P(x+math.cos(a)*L),P(y+math.sin(a)*L))],fill=(190,232,255),width=6*S)
    for (x,y) in r['pegs']: circ(x,y,9,fill=(200,205,215))
    nh=sum(1 for h in HITS if h[0]<=t); dm=max([h[2] for h in HITS if h[0]<=t] or [0])
    if t<OUT:
        for a,b in r['cup']: d.line([(P(a[0]),P(a[1])),(P(b[0]),P(b[1]))],fill=(170,225,255),width=9*S)
        rr=random.Random(3)
        for n in range(nh):
            sg=r['cup'][rr.randrange(3)]; u=rr.random()
            x=sg[0][0]+(sg[1][0]-sg[0][0])*u; y=sg[0][1]+(sg[1][1]-sg[0][1])*u
            pts=[(x,y)]
            for q in range(3): pts.append((pts[-1][0]+rr.uniform(-9,9),pts[-1][1]+rr.uniform(-9,9)))
            d.line([(P(a),P(b)) for a,b in pts],fill=BG,width=2*S)
        fl=max([h[0] for h in HITS if h[0]<=t] or [-9])
        if t-fl<0.12: 
            for a,b in r['cup']: d.line([(P(a[0]),P(a[1])),(P(b[0]),P(b[1]))],fill=(255,255,255),width=11*S)
    else:
        rr=random.Random(8); dt=t-OUT
        for n in range(14):
            vx=rr.uniform(-380,380); vy=rr.uniform(-420,60); x0=sim4.CX+rr.uniform(-30,30); y0_=sim4.CY-rr.uniform(0,20)
            x=x0+vx*dt; y=y0_+vy*dt+950*dt*dt; a=rr.uniform(0,6.28)+dt*rr.uniform(-9,9); L=rr.uniform(6,13)
            d.line([(P(x-math.cos(a)*L),P(y-math.sin(a)*L)),(P(x+math.cos(a)*L),P(y+math.sin(a)*L))],fill=(190,232,255),width=6*S)
    d.rounded_rectangle([P(100),P(205),P(980),P(352)],12*S,outline=FRM,width=6*S)
    fr=FR[min(f,len(FR)-1)]
    for i,(x,y,row) in enumerate(sim.TRAY):
        c=WH
        if i in fr[0]:
            x,y=fr[0][i]
            if t>T_FX:
                k=((t-T_FX)*WSP-math.hypot(x-LP[0],y-LP[1]))/60
                if t>=TREL-0.3: k=9
                if k>0: c=mix(WH,GOLD,min(1,k))
                if 0<k<0.5: circ(x,y,20,fill=(255,244,200))
        circ(x,y,16,fill=c,outline=BG,width=2*S)
        if c!=WH: circ(x-5,y-6,4,fill=(255,236,170))
    g=fr[1] or (sim4.CX,400); R=sim.RG
    circ(g[0],g[1],R,fill=GOLD,outline=BG,width=2*S); circ(g[0]-6,g[1]-7,5,fill=(255,236,170))
    e=ease(EP[min(f,NF-1)])*(1-ease((t-TREL-0.1)/1.3))
    zb=1.0+(ZA-1.0)*(1-ease((t-TREL-0.1)/1.3)) if t>TREL else ZA
    z=zb+(ZMAX-zb)*e; vw,vh=1080/z,1920/z
    cx=540+(CXT-540)*e; cx=max(vw/2,min(1080-vw/2,cx)); ya=YA*(1-ease((t-TREL-0.1)/1.3)) if t>TREL else YA
    y0=ya+(Y0T-ya)*e
    fr_=im.resize((540,960),Image.LANCZOS,box=(P(cx-vw/2),P(y0),P(cx+vw/2),P(y0+vh)))
    d2=ImageDraw.Draw(fr_)
    d2.rectangle([0,0,540,96],fill=BG)
    if nxt: parts=[('Next: the black one',WH)]
    elif t>=TREL: parts=[('GOLD',GOLD),(' set them all free',WH)]
    elif t<OUT: parts=[('How many hits can the ',WH),('glass',(170,225,255)),(' take?',WH)]
    else: parts=[('It broke on hit ',WH),(str(len(HITS)),GOLD)]
    w=sum(d2.textlength(a,font=f1) for a,_ in parts); x=270-w/2
    for a,c in parts: d2.text((x,6),a,font=f1,fill=c); x+=d2.textlength(a,font=f1)
    if not nxt:
        left=sum(1 for i in rel if rel[i]>t)
        if t>=OUT: left=sum(1 for i in rel if rel[i]>OUT)
        s=f'HITS {nh:02d}   BALLS LEFT {left:02d}'; w=d2.textlength(s,font=f3)
        d2.text((270-w/2,62),s,font=f3,fill=(255,90,80) if left<=10 else (170,176,190))
    else:
        bx,by,br=270,170,44
        d2.ellipse([bx-br,by-br,bx+br,by+br],fill=(4,4,6),outline=(120,124,136),width=2)
        d2.arc([bx-br+9,by-br+9,bx+br-9,by+br-9],200,280,fill=(255,255,255),width=5)
    p.stdin.write(fr_.tobytes())
p.stdin.close(); p.wait(); print('END',END)
