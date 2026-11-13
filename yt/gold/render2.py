import sim, sys, pickle, subprocess, math
from PIL import Image, ImageDraw, ImageFont
seed=int(sys.argv[1]); gx=float(sys.argv[2]); GT=float(sys.argv[3]); out=sys.argv[4]
r=sim.run(seed,gx,gt=GT,T=16.0)
FR=r['frames']; mat=r['mat']; gt=r['gt']
rest=None
for f in range(len(FR)-30,0,-1):
    a=FR[f][1]; b=FR[f-1][1]
    if a and b and math.hypot(a[0]-b[0],a[1]-b[1])>0.35: rest=(f+1)/60; break
hit=[h for h in r['hits'] if h[1]=='ball'][0][0]
print('hit',hit,'rest',rest)
T_FROST=rest+0.25; T_CUT=T_FROST+1.3+1.1; END=T_CUT+0.7
Z0,Z1=GT+1.3,GT+2.9   # zoom window
ZMAX=1.4; CXT=650; PADB=500
Y0T=sim.FLOOR-0.70*1920/ZMAX
FD='/mnt/skills/examples/canvas-design/canvas-fonts/'
f1=ImageFont.truetype(FD+'BigShoulders-Bold.ttf',46); f2=ImageFont.truetype(FD+'BigShoulders-Bold.ttf',44)
COL=[(255,106,42),(150,215,255),(176,182,192)]
GOLD=(255,196,40); WH=(240,240,244); BG=(18,20,26)
def mix(a,b,k): return tuple(int(a[i]+(b[i]-a[i])*k) for i in range(3))
def ease(x): x=max(0,min(1,x)); return x*x*(3-2*x)
p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','540x960','-r','30','-i','-',
  '-c:v','libx264','-crf','22','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
S=2  # supersample of world
def P(v): return v*S
for f in range(0,int(END*60),2):
    t=f/60; wide=False; nxt=t>=T_CUT
    im=Image.new('RGB',(1080*S,(1920+PADB)*S),BG); d=ImageDraw.Draw(im)
    def circ(x,y,rad,**k): d.ellipse([P(x-rad),P(y-rad),P(x+rad),P(y+rad)],**k)
    for k in range(3):
        x0=sim.XL+k*sim.BW
        d.rectangle([P(x0),P(sim.FLOOR+8),P(x0+sim.BW),P(sim.FLOOR+30)],fill=COL[k])
        nm=['FIRE','ICE','CHROME'][k]; ff=ImageFont.truetype(FD+'BigShoulders-Bold.ttf',44*S); w=d.textlength(nm,font=ff)
        d.text((P(x0+sim.BW/2)-w/2,P(sim.FLOOR+44)),nm,font=ff,fill=COL[k])
    d.line([(P(sim.XL),P(400)),(P(sim.XL),P(sim.FLOOR)),(P(sim.XR),P(sim.FLOOR)),(P(sim.XR),P(400))],fill=(90,96,110),width=10*S)
    for dx in sim.DIVX: d.line([(P(dx),P(sim.DIV_TOP)),(P(dx),P(sim.FLOOR))],fill=(90,96,110),width=10*S)
    for (x,y) in sim.PEGS: circ(x,y,9,fill=(200,205,215))
    d.rounded_rectangle([P(100),P(205),P(980),P(352)],12*S,outline=(90,96,110),width=6*S)
    d.rounded_rectangle([P(gx-34),P(134),P(gx+34),P(200)],10*S,outline=GOLD if t<gt else (90,96,110),width=6*S)
    fr=FR[min(f,len(FR)-1)]
    for i,(x,y,row) in enumerate(sim.TRAY):
        c=WH
        if i in fr[0]:
            x,y,_=fr[0][i]
            if i in mat and t>=mat[i][1]: c=mix(WH,COL[mat[i][0]],min(1,(t-mat[i][1])/0.25))
        circ(x,y,16,fill=c,outline=BG,width=2*S)
        if i in mat and mat[i][0]==2 and t>=mat[i][1]: circ(x-5,y-6,4,fill=(235,238,244))
    g=fr[1] or (gx,170,0); R=sim.RG
    k=ease((t-T_FROST)/1.3)
    if k>0:
        # frost creeping over neighbours + shell growing around gold
        circ(g[0],g[1],R+7*k,fill=mix(GOLD,(214,240,255),min(1,k*1.2)),outline=(255,255,255),width=int(3*S))
        circ(g[0],g[1],R-2-6*k,fill=GOLD)
        circ(g[0]-4,g[1]-5,4,fill=(255,236,170))
        import random
        rr=random.Random(5)
        for n in range(10):
            a=rr.uniform(0,6.283); L=(R+10+rr.uniform(4,22))*k
            d.line([(P(g[0]+math.cos(a)*(R+6*k)),P(g[1]+math.sin(a)*(R+6*k))),(P(g[0]+math.cos(a)*L*1.0+math.cos(a)*R),P(g[1]+math.sin(a)*L+math.sin(a)*R))],fill=(235,248,255),width=2*S)
    else:
        circ(g[0],g[1],R,fill=GOLD,outline=BG,width=2*S)
        circ(g[0]-6,g[1]-7,5,fill=(255,236,170))
    if wide:
        circ(gx,168,R,fill=(6,6,8),outline=(70,72,80),width=2*S)
        d.arc([P(gx-R+5),P(168-R+5),P(gx+R-5),P(168+R-5)],195,285,fill=(255,255,255),width=4*S)
        d.rounded_rectangle([P(gx-34),P(134),P(gx+34),P(200)],10*S,outline=(230,230,236),width=6*S)
    z=1.0 if wide else 1+(ZMAX-1)*ease((t-Z0)/(Z1-Z0))
    vw,vh=1080/z,1920/z
    cx=540+(CXT-540)*(z-1)/(ZMAX-1); cx=max(vw/2,min(1080-vw/2,cx))
    y0=Y0T*(z-1)/(ZMAX-1); y1=y0+vh
    fr_=im.resize((540,960),Image.LANCZOS,box=(P(cx-vw/2),P(y0),P(cx+vw/2),P(y1)))
    d2=ImageDraw.Draw(fr_)
    if not nxt:
        parts=[('Where will ',WH),('GOLD',GOLD),(' land?',WH)]
    else:
        parts=[('Next: the black one',WH)]
    w=sum(d2.textlength(a,font=f1) for a,_ in parts); x=270-w/2
    d2.rectangle([0,0,540,66],fill=BG)
    for a,c in parts: d2.text((x,10),a,font=f1,fill=c); x+=d2.textlength(a,font=f1)
    if nxt:
        bx,by,br=270,150,44
        d2.ellipse([bx-br,by-br,bx+br,by+br],fill=(4,4,6),outline=(120,124,136),width=2)
        d2.arc([bx-br+9,by-br+9,bx+br-9,by+br-9],200,280,fill=(255,255,255),width=5)
        d2.ellipse([bx+12,by+18,bx+20,by+24],fill=(90,94,104))
    p.stdin.write(fr_.tobytes())
p.stdin.close(); p.wait()
print('END',END)
