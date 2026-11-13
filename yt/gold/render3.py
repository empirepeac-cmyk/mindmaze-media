import sim3, sim, sys, subprocess, math, pickle
from PIL import Image, ImageDraw, ImageFont
seed=int(sys.argv[1]); depth=int(sys.argv[2]); out=sys.argv[3]
r=sim3.run(seed,depth,T=18.0)
FR=r['frames']; mat=r['mat']; st=r['st']; rel=r['rel']
pickle.dump(r,open(f'run3_{seed}.pkl','wb'))
rest=None
for f in range(len(FR)-30,0,-1):
    a=FR[f][1]; b=FR[f-1][1]
    if a and b and math.hypot(a[0]-b[0],a[1]-b[1])>0.35: rest=(f+1)/60; break
OUT=st['out']; print('in',st['in'],'out',OUT,'rest',rest,'bin',r['gold_bin'])
gb=r['gold_bin']
T_FX=rest+0.25; T_CUT=T_FX+1.2+1.0; END=T_CUT+0.7
Z0,Z1=OUT+0.25,OUT+1.6
ZMAX=1.4; PADB=500
gxf=FR[-1][1][0]; CXT=max(1080/ZMAX/2,min(1080-1080/ZMAX/2,gxf))
Y0T=sim.FLOOR-0.70*1920/ZMAX
FD='/mnt/skills/examples/canvas-design/canvas-fonts/'
f1=ImageFont.truetype(FD+'BigShoulders-Bold.ttf',44); f3=ImageFont.truetype(FD+'GeistMono-Bold.ttf',24)
COL=[(255,106,42),(150,215,255),(176,182,192)]
GOLD=(255,196,40); WH=(240,240,244); BG=(18,20,26); FRM=(90,96,110)
def mix(a,b,k): return tuple(int(a[i]+(b[i]-a[i])*k) for i in range(3))
def ease(x): x=max(0,min(1,x)); return x*x*(3-2*x)
p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','540x960','-r','30','-i','-',
  '-c:v','libx264','-crf','22','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
S=2
def P(v): return v*S
ff=ImageFont.truetype(FD+'BigShoulders-Bold.ttf',44*S)
for f in range(0,int(END*60),2):
    t=f/60; nxt=t>=T_CUT
    im=Image.new('RGB',(1080*S,(1920+PADB)*S),BG); d=ImageDraw.Draw(im)
    def circ(x,y,rad,**k): d.ellipse([P(x-rad),P(y-rad),P(x+rad),P(y+rad)],**k)
    for k in range(3):
        x0=sim.XL+k*sim.BW
        d.rectangle([P(x0),P(sim.FLOOR+8),P(x0+sim.BW),P(sim.FLOOR+30)],fill=COL[k])
        nm=['FIRE','ICE','CHROME'][k]; w=d.textlength(nm,font=ff)
        d.text((P(x0+sim.BW/2)-w/2,P(sim.FLOOR+44)),nm,font=ff,fill=COL[k])
    d.line([(P(sim.XL),P(400)),(P(sim.XL),P(sim.FLOOR)),(P(sim.XR),P(sim.FLOOR)),(P(sim.XR),P(400))],fill=FRM,width=10*S)
    for dx in sim.DIVX: d.line([(P(dx),P(sim.DIV_TOP)),(P(dx),P(sim.FLOOR))],fill=FRM,width=10*S)
    for (x,y) in r['pegs']: circ(x,y,9,fill=(200,205,215))
    for a,b in r['cup']: d.line([(P(a[0]),P(a[1])),(P(b[0]),P(b[1]))],fill=GOLD,width=8*S)
    d.rounded_rectangle([P(100),P(205),P(980),P(352)],12*S,outline=FRM,width=6*S)
    fr=FR[min(f,len(FR)-1)]
    for i,(x,y,row) in enumerate(sim.TRAY):
        c=WH
        if i in fr[0]:
            x,y=fr[0][i]
            if i in mat and t>=mat[i][1]: c=mix(WH,COL[mat[i][0]],min(1,(t-mat[i][1])/0.25))
        circ(x,y,16,fill=c,outline=BG,width=2*S)
        if i in mat and mat[i][0]==2 and t>=mat[i][1]: circ(x-5,y-6,4,fill=(235,238,244))
    g=fr[1] or (sim3.CX,400); R=sim.RG
    k=ease((t-T_FX)/1.2)
    if k>0:
        shell=[(255,150,60),(214,240,255),(225,228,235)][gb]
        circ(g[0],g[1],R+7*k,fill=mix(GOLD,shell,min(1,k*1.2)),outline=(255,255,255),width=3*S)
        circ(g[0],g[1],R-2-6*k,fill=GOLD); circ(g[0]-4,g[1]-5,4,fill=(255,236,170))
    else:
        circ(g[0],g[1],R,fill=GOLD,outline=BG,width=2*S); circ(g[0]-6,g[1]-7,5,fill=(255,236,170))
    z=1+(ZMAX-1)*ease((t-Z0)/(Z1-Z0))
    vw,vh=1080/z,1920/z
    cx=540+(CXT-540)*(z-1)/(ZMAX-1); y0=Y0T*(z-1)/(ZMAX-1)
    fr_=im.resize((540,960),Image.LANCZOS,box=(P(cx-vw/2),P(y0),P(cx+vw/2),P(y0+vh)))
    d2=ImageDraw.Draw(fr_)
    d2.rectangle([0,0,540,96],fill=BG)
    if nxt: parts=[('Next: the black one',WH)]
    elif t<OUT: parts=[('GOLD',GOLD),(' is stuck. Can they free it?',WH)]
    else: parts=[('GOLD',GOLD),(' is FREE!',WH)]
    w=sum(d2.textlength(a,font=f1) for a,_ in parts); x=270-w/2
    for a,c in parts: d2.text((x,6),a,font=f1,fill=c); x+=d2.textlength(a,font=f1)
    if not nxt:
        left=sum(1 for i in rel if rel[i]>t)
        if t>=OUT: left=sum(1 for i in rel if rel[i]>OUT)
        s=f'{left:02d} BALLS LEFT'; w=d2.textlength(s,font=f3)
        d2.text((270-w/2,62),s,font=f3,fill=(255,90,80) if left<=10 else (170,176,190))
    else:
        bx,by,br=270,170,44
        d2.ellipse([bx-br,by-br,bx+br,by+br],fill=(4,4,6),outline=(120,124,136),width=2)
        d2.arc([bx-br+9,by-br+9,bx+br-9,by+br-9],200,280,fill=(255,255,255),width=5)
    p.stdin.write(fr_.tobytes())
p.stdin.close(); p.wait(); print('END',END)
