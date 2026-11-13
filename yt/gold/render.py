import sim, sys, pickle, subprocess, math
from PIL import Image, ImageDraw, ImageFont
seed=int(sys.argv[1]); gx=float(sys.argv[2]); out=sys.argv[3]
r=sim.run(seed,gx,T=17.0)
FR=r['frames']; mat=r['mat']; gt=r['gt']
# rest time
rest=None
for f in range(len(FR)-30,0,-1):
    a=FR[f][1]; b=FR[f-1][1]
    if a and b and math.hypot(a[0]-b[0],a[1]-b[1])>0.35: rest=(f+1)/60; break
print('rest',rest,'bin',r['gold_bin'],[h for h in r['hits'] if h[1]=='ball'][:3])
END=rest+3.4
FD='/mnt/skills/examples/canvas-design/canvas-fonts/'
f1=ImageFont.truetype(FD+'BigShoulders-Bold.ttf',92); f2=ImageFont.truetype(FD+'BigShoulders-Bold.ttf',44)
COL=[(255,106,42),(150,215,255),(176,182,192)]
GOLD=(255,200,50)
def mix(a,b,k): return tuple(int(a[i]+(b[i]-a[i])*k) for i in range(3))
p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','540x960','-r','30','-i','-',
  '-c:v','libx264','-crf','23','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
for f in range(0,int(END*60),2):
    t=f/60
    im=Image.new('RGB',(1080,1920),(18,20,26)); d=ImageDraw.Draw(im)
    # bins tint
    for k in range(3):
        x0=sim.XL+k*sim.BW
        d.rectangle([x0,sim.FLOOR+8,x0+sim.BW,sim.FLOOR+30],fill=COL[k])
        nm=['FIRE','ICE','CHROME'][k]; w=d.textlength(nm,font=f2)
        d.text((x0+sim.BW/2-w/2,sim.FLOOR+44),nm,font=f2,fill=COL[k])
    d.line([(sim.XL,400),(sim.XL,sim.FLOOR),(sim.XR,sim.FLOOR),(sim.XR,400)],fill=(90,96,110),width=10)
    for dx in sim.DIVX: d.line([(dx,sim.DIV_TOP),(dx,sim.FLOOR)],fill=(90,96,110),width=10)
    for (x,y) in sim.PEGS: d.ellipse([x-9,y-9,x+9,y+9],fill=(200,205,215))
    # tray + hatch
    d.rounded_rectangle([100,205,980,352],12,outline=(90,96,110),width=6)
    d.rounded_rectangle([gx-34,134,gx+34,200],10,outline=GOLD if t<gt else (90,96,110),width=6)
    fr=FR[min(f,len(FR)-1)]
    for i,(x,y,row) in enumerate(sim.TRAY):
        if i in fr[0]:
            x,y,_=fr[0][i]
            c=(240,240,244)
            if i in mat and t>=mat[i][1]: c=mix((240,240,244),COL[mat[i][0]],min(1,(t-mat[i][1])/0.25))
        else: c=(240,240,244)
        d.ellipse([x-16,y-16,x+16,y+16],fill=c,outline=(18,20,26),width=2)
    g=fr[1] or (gx,170,0)
    k=0 if t<rest+0.3 else min(1,(t-rest-0.3)/1.4)
    R=sim.RG
    d.ellipse([g[0]-R,g[1]-R,g[0]+R,g[1]+R],fill=mix(GOLD,(210,238,255),k),outline=(18,20,26),width=2)
    if k>0: d.ellipse([g[0]-9,g[1]-9,g[0]+9,g[1]+9],fill=GOLD)
    if t<END-0.6:
        parts=[('Where will ',(240,240,244)),('GOLD',GOLD),(' land?',(240,240,244))]
        w=sum(d.textlength(a,font=f1) for a,_ in parts); x=540-w/2
        for a,c in parts: d.text((x,22),a,font=f1,fill=c); x+=d.textlength(a,font=f1)
    else:
        s='Next: the black one'; w=d.textlength(s,font=f1); d.text((540-w/2,22),s,font=f1,fill=(240,240,244))
        d.ellipse([gx-R,170-R,gx+R,170+R],fill=(8,8,10),outline=(150,150,160),width=3)
    p.stdin.write(im.resize((540,960),Image.LANCZOS).tobytes())
p.stdin.close(); p.wait()
pickle.dump(r,open('run.pkl','wb'))
