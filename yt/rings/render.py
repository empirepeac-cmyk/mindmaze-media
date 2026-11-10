import numpy as np, math, pickle, sys, subprocess, colorsys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.ndimage import gaussian_filter
from sim import *
W_,H_=1080,1920; CX,CY=540,860
FD='/mnt/skills/examples/canvas-design/canvas-fonts/'
_fc={}
def F(n,s):
    if (n,s) not in _fc: _fc[(n,s)]=ImageFont.truetype(n,s)
    return _fc[(n,s)]
S=pickle.load(open('sim.pkl','rb'))
frames=S['frames']; ev=S['ev']; ph=S['ph']; tend=S['tend']
NF=len(frames)
def col(i):
    h=(0.50+0.052*i)%1.0
    return np.array(colorsys.hsv_to_rgb(h,0.72,1.0),dtype=np.float32)
COL=[col(i) for i in range(N)]
breaks={e[2]:e[0] for e in ev if e[1]=='break'}
hits=[e for e in ev if e[1]=='hit']
hit_t=np.array([e[0] for e in hits])
# particles
rng=np.random.default_rng(7)
P=[] # t0,x,y,vx,vy,life,color,size
for e in ev:
    t,k,i,x,y=e
    if k=='hit':
        n=np.array([x,y]); n=n/np.linalg.norm(n)
        for _ in range(12):
            a=rng.normal(0,0.9); c,s=math.cos(a),math.sin(a)
            d=-np.array([n[0]*c-n[1]*s,n[0]*s+n[1]*c]); sp=rng.uniform(120,520)
            P.append((t,x,y,d[0]*sp,d[1]*sp,rng.uniform(0.2,0.45),COL[i],1))
    else:
        R=RAD[i]; gc=ph[i]+omega(i)*t; m=int(2*math.pi*R/5)
        for a in np.linspace(0,2*math.pi,m,endpoint=False):
            d=(a-gc+math.pi)%(2*math.pi)-math.pi
            if abs(d)<GAP/2: continue
            c,s=math.cos(a),math.sin(a); sp=rng.uniform(40,420); tg=omega(i)*R*0.6
            P.append((t,R*c,R*s,c*sp-s*tg+rng.normal(0,40),s*sp+c*tg+rng.normal(0,40),rng.uniform(0.5,1.5),COL[i],2))
        if i==N-1:
            for _ in range(900):
                a=rng.uniform(0,2*math.pi); sp=rng.uniform(100,1300)
                P.append((t,x,y,math.cos(a)*sp,math.sin(a)*sp-200,rng.uniform(1.0,3.3),COL[rng.integers(0,N)],2))
PT=np.array([p[0] for p in P]); PX=np.array([p[1:6] for p in P]); PC=np.array([p[6] for p in P]); PS=np.array([p[7] for p in P])
# static fields
yy,xx=np.mgrid[0:H_,0:W_].astype(np.float32)
bg=np.zeros((H_,W_,3),np.float32)
d=np.hypot(xx-CX,yy-CY)/1100
bg[...,0]=10+16*np.clip(1-d,0,1)**2; bg[...,1]=11+14*np.clip(1-d,0,1)**2; bg[...,2]=22+34*np.clip(1-d,0,1)**2
bg/=255
RING=[]
for i in range(N):
    R=RAD[i]; m=R+8; x0,y0=CX-m,CY-m
    sx=xx[y0:y0+2*m,x0:x0+2*m]-CX; sy=yy[y0:y0+2*m,x0:x0+2*m]-CY
    r=np.hypot(sx,sy); cov=np.clip(W/2+0.5-np.abs(r-R),0,1)
    idx=np.nonzero(cov>0); RING.append((x0,y0,2*m,idx,cov[idx],np.arctan2(sy,sx)[idx]))
def disc(L,x,y,r,c,a=1.0):
    x0=int(max(0,x-r-2)); x1=int(min(W_,x+r+3)); y0=int(max(0,y-r-2)); y1=int(min(H_,y+r+3))
    if x1<=x0 or y1<=y0: return
    dd=np.hypot(xx[y0:y1,x0:x1]-x,yy[y0:y1,x0:x1]-y)
    m=np.clip(r+0.5-dd,0,1)*a
    L[y0:y1,x0:x1]=np.maximum(L[y0:y1,x0:x1],m[...,None]*c)
_tc={}
def text(s,font,fill,glow=0):
    k=(s,font.path,font.size,fill,glow)
    if k in _tc: return _tc[k]
    b=font.getbbox(s); pad=30
    im=Image.new('RGBA',(b[2]-b[0]+2*pad,b[3]-b[1]+2*pad),(0,0,0,0))
    dr=ImageDraw.Draw(im); dr.text((pad-b[0],pad-b[1]),s,font=font,fill=fill)
    if glow:
        g=im.filter(ImageFilter.GaussianBlur(glow)); im=Image.alpha_composite(g,im)
    a=np.asarray(im).astype(np.float32)/255; _tc[k]=a; return a
def put(img,a,cx,y,alpha=1.0):
    h,w=a.shape[:2]; x0=int(cx-w/2); y0=int(y)
    xa,ya=max(0,x0),max(0,y0); xb,yb=min(W_,x0+w),min(H_,y0+h)
    if xb<=xa or yb<=ya: return
    s=a[ya-y0:yb-y0,xa-x0:xb-x0]; al=s[...,3:4]*alpha
    img[ya:yb,xa:xb]=img[ya:yb,xa:xb]*(1-al)+s[...,:3]*al
FB=FD+'BigShoulders-Bold.ttf'; FM=FD+'GeistMono-Bold.ttf'; FMr=FD+'GeistMono-Regular.ttf'
WH=(245,244,255,255); DIM=(150,156,190,255)
def rgb(c): return tuple(int(v*255) for v in c)+(255,)
def ease(x): x=min(max(x,0),1); return 1-(1-x)**3
def frame(f):
    t=f/FPS; L=np.zeros((H_,W_,3),np.float32)
    px,py,cur=frames[f]
    # rings
    for i in range(N):
        if i in breaks and breaks[i]<=t: continue
        x0,y0,sz,idx,cov,th=RING[i]
        gc=ph[i]+omega(i)*t
        dd=np.abs((th-gc+np.pi)%(2*np.pi)-np.pi)
        m=cov*np.clip((dd-GAP/2)*RAD[i]+0.5,0,1)
        b=1.0 if i==cur else 0.42
        hh=[e[0] for e in hits if e[2]==i and e[0]<=t]
        if hh: b+=1.3*math.exp(-(t-hh[-1])/0.13)
        if t<0.6: m=m*ease((t-0.03*i)/0.35)
        v=L[y0:y0+sz,x0:x0+sz]; v[idx]=m[:,None]*np.minimum(COL[i]*b+max(0,b-1)*0.5,1.6)
    # trail + ball
    c=COL[min(cur,N-1)]
    K=26
    for j in range(K,0,-1):
        g=f-j
        if g<0: continue
        for u in (0.0,0.5):
            ax=frames[g][0]*(1-u)+frames[g+1][0]*u; ay=frames[g][1]*(1-u)+frames[g+1][1]*u
            w=1-(j-u)/K
            disc(L,CX+ax,CY+ay,RB*(0.25+0.75*w),c,0.75*w**1.6)
    disc(L,CX+px,CY+py,RB,np.array([1,1,1],np.float32),1.0)
    # particles
    age=t-PT; ok=(age>=0)&(age<PX[:,4])
    if ok.any():
        a=age[ok]; q=PX[ok]; x=CX+q[:,0]+q[:,2]*a; y=CY+q[:,1]+q[:,3]*a+0.5*700*a*a
        al=(1-a/q[:,4])**1.5; cc=PC[ok]*al[:,None]; sz=PS[ok]
        xi=x.astype(int); yi=y.astype(int)
        for dx in (0,1,2):
            for dy in (0,1,2):
                big=(sz==2)|((dx<2)&(dy<2))
                X=xi+dx-1; Y=yi+dy-1; g=big&(X>=0)&(X<W_)&(Y>=0)&(Y<H_)
                np.maximum.at(L,(Y[g],X[g]),cc[g])
    # shake
    bt=[b for b in breaks.values() if b<=t]
    fl=0
    if bt:
        ag=t-max(bt); amp=(22 if max(bt)==tend else 9)*math.exp(-ag/0.14)
        if amp>0.5:
            L=np.roll(L,(int(amp*math.sin(f*2.1)),int(amp*math.cos(f*1.7))),axis=(0,1))
        fl=0.10*math.exp(-ag/0.10)*(3 if max(bt)==tend else 1)
    small=L.reshape(H_//4,4,W_//4,4,3).mean((1,3))
    g1=gaussian_filter(small,(5,5,0)); g2=gaussian_filter(small,(18,18,0))
    gl=g1*1.1+g2*1.4
    gl=np.stack([np.asarray(Image.fromarray(gl[...,k]).resize((W_,H_),Image.BILINEAR)) for k in range(3)],-1)
    img=bg+L+gl+fl
    # HUD
    nb=int((hit_t<=t).sum()); left=N-len(bt)
    hud=1.0 if t<tend+0.25 else max(0,1-(t-tend-0.25)/0.3)
    if hud>0:
        pulse=0.55+0.45*abs(math.sin(t*3.2)) if t<3.2 else 1.0
        put(img,text('HOW MANY BOUNCES',F(FB,92),WH,6),CX,78,hud*ease(t/0.4)*pulse)
        put(img,text('until it escapes?',F(FMr,46),DIM),CX,170,hud*ease((t-0.2)/0.4))
        ag=t-max(bt) if bt else 9
        s=text(f'{left}',F(FB,150),rgb(COL[min(cur,N-1)]),8)
        put(img,s,CX-150,1385-14*math.exp(-ag/0.09),hud)
        put(img,text('RINGS',F(FM,44),WH),CX+60,1425,hud); put(img,text('LEFT',F(FM,44),DIM),CX+45,1480,hud)
        ah=t-hit_t[hit_t<=t].max() if nb else 9
        put(img,text(f'bounces: {nb}',F(FM,52),WH if ah>0.12 else rgb(c)),CX,1262+0*ah,hud*0) 
    else: nb=len(hits)
    if t<tend+0.25 and nb>=0:
        ah=t-hit_t[hit_t<=t].max() if nb else 9
        a=text(f'{nb}',F(FB,96),WH,5)
        put(img,a,CX,254-8*math.exp(-ah/0.07),ease((t-0.4)/0.4)*0.95)
    te=t-tend
    if te>0.25:
        a=ease((te-0.25)/0.35)
        put(img,text('ESCAPED!',F(FB,230),WH,10),CX,560-40*(1-a),a)
        a2=ease((te-0.7)/0.35)
        put(img,text(f'in {len(hits)} bounces',F(FM,70),rgb(COL[0])),CX,860,a2)
        a3=ease((te-1.5)/0.35)
        put(img,text('LEVEL 2: 20 RINGS',F(FB,110),rgb(COL[9]),6),CX,1060,a3)
        put(img,text('follow to watch it',F(FMr,50),WH),CX,1215,ease((te-1.8)/0.35))
    return (np.clip(img,0,1)*255).astype(np.uint8)
if __name__=='__main__':
    if sys.argv[1]=='shot':
        for f in sys.argv[2:]: Image.fromarray(frame(int(f))).save(f'f{f}.png')
    else:
        k=int(sys.argv[1]); n=int(sys.argv[2]); a=NF*k//n; b=NF*(k+1)//n
        p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r','60','-i','-','-c:v','libx264','-preset','medium','-crf','15','-pix_fmt','yuv420p',f'part{k}.mp4'],stdin=subprocess.PIPE)
        for f in range(a,b): p.stdin.write(frame(f).tobytes())
        p.stdin.close(); p.wait()
