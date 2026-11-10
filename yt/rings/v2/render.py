import numpy as np, math, pickle, sys, subprocess, colorsys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.ndimage import gaussian_filter
from sim import *
W_,H_=1080,1920; CX,CY=540,905
FD='/mnt/skills/examples/canvas-design/canvas-fonts/'
_fc={}
def F(n,s):
    if (n,s) not in _fc: _fc[(n,s)]=ImageFont.truetype(FD+n,s)
    return _fc[(n,s)]
S=pickle.load(open('sim.pkl','rb'))
frames=S['frames']; ev=S['ev']; ph=S['ph']; tend=S['tend']
NF=len(frames)
def col(i):
    h=(0.47+0.048*i)%1.0
    return np.array(colorsys.hsv_to_rgb(h,0.74,1.0),dtype=np.float32)
COL=[col(i) for i in range(N+3)]
breaks={e[2]:e[0] for e in ev if e[1]=='break'}
bts=sorted(breaks.values())
hits=[e for e in ev if e[1]=='hit']
hit_t=np.array([e[0] for e in hits])
rng=np.random.default_rng(7)
P=[]
for e in ev:
    t,k,i,x,y=e
    if k=='hit':
        n=np.array([x,y]); n=n/np.linalg.norm(n)
        for _ in range(16):
            a=rng.normal(0,0.9); c,s=math.cos(a),math.sin(a)
            d=-np.array([n[0]*c-n[1]*s,n[0]*s+n[1]*c]); sp=rng.uniform(120,560)
            P.append((t,x,y,d[0]*sp,d[1]*sp,rng.uniform(0.2,0.5),COL[i],1))
    else:
        R=RAD[i]; gc=ph[i]+omega(i)*t; m=int(2*math.pi*R/4.5)
        for a in np.linspace(0,2*math.pi,m,endpoint=False):
            d=(a-gc+math.pi)%(2*math.pi)-math.pi
            if abs(d)<GAPS[i]/2: continue
            c,s=math.cos(a),math.sin(a); sp=rng.uniform(40,460); tg=omega(i)*R*0.6
            P.append((t,R*c,R*s,c*sp-s*tg+rng.normal(0,40),s*sp+c*tg+rng.normal(0,40),rng.uniform(0.5,1.6),COL[i+int(rng.integers(0,3))],2))
        if i==N-1:
            for _ in range(1400):
                a=rng.uniform(0,2*math.pi); sp=rng.uniform(100,1400)
                P.append((t,x,y,math.cos(a)*sp,math.sin(a)*sp-250,rng.uniform(1.0,3.6),COL[rng.integers(0,N)],2))
for f in range(min(NF,int(tend*60)+40)):
    x,y,c=frames[f]
    for _ in range(2):
        P.append((f/60,x+rng.normal(0,4),y+rng.normal(0,4),rng.normal(0,45),rng.normal(0,45)-40,rng.uniform(0.3,0.8),COL[min(c,N-1)]*0.8,1))
PT=np.array([p[0] for p in P]); PX=np.array([p[1:6] for p in P]); PC=np.array([p[6] for p in P]); PS=np.array([p[7] for p in P])
yy,xx=np.mgrid[0:H_,0:W_].astype(np.float32)
RF=np.hypot(xx-CX,yy-CY); TF=np.arctan2(yy-CY,xx-CX)
neb=np.clip(1-RF/1000,0,1)**2
bg=np.zeros((H_,W_,3),np.float32); bg[...,0]=7;bg[...,1]=8;bg[...,2]=17; bg/=255
# faint dot grid
gm=((xx%60<2)&(yy%60<2)).astype(np.float32)*0.07
bg+=gm[...,None]*np.array([0.6,0.7,1.0],np.float32)
vig=np.clip((np.hypot((xx-540)/540,(yy-960)/960)-0.55)/0.6,0,1)**1.5
NS=260; SXY=np.stack([rng.integers(0,W_,NS),rng.integers(0,H_,NS)],1); SPH=rng.uniform(0,6.28,NS); SSP=rng.uniform(0.6,2.5,NS)
RING=[]
for i in range(N):
    R=RAD[i]; m=int(R+8); x0,y0=CX-m,CY-m
    r=RF[y0:y0+2*m,x0:x0+2*m]; cov=np.clip(W/2+0.5-np.abs(r-R),0,1)
    idx=np.nonzero(cov>0); RING.append((x0,y0,2*m,idx,cov[idx],TF[y0:y0+2*m,x0:x0+2*m][idx]))
# timer arc
RT=512; covT=np.clip(3.5-np.abs(RF-RT),0,1); idxT=np.nonzero(covT>0); covT=covT[idxT]; thT=(TF[idxT]+np.pi/2)%(2*np.pi)
def disc(L,x,y,r,c,a=1.0):
    x0=int(max(0,x-r-2)); x1=int(min(W_,x+r+3)); y0=int(max(0,y-r-2)); y1=int(min(H_,y+r+3))
    if x1<=x0 or y1<=y0: return
    dd=np.hypot(xx[y0:y1,x0:x1]-x,yy[y0:y1,x0:x1]-y)
    m=np.clip(r+0.5-dd,0,1)*a
    L[y0:y1,x0:x1]=np.maximum(L[y0:y1,x0:x1],m[...,None]*c)
def wave(L,x,y,r,w,c,a):
    x0=int(max(0,x-r-w-2)); x1=int(min(W_,x+r+w+3)); y0=int(max(0,y-r-w-2)); y1=int(min(H_,y+r+w+3))
    if x1<=x0 or y1<=y0: return
    dd=np.hypot(xx[y0:y1,x0:x1]-x,yy[y0:y1,x0:x1]-y)
    m=np.clip(w/2+0.5-np.abs(dd-r),0,1)*a
    L[y0:y1,x0:x1]=np.maximum(L[y0:y1,x0:x1],m[...,None]*c)
_tc={}
def text(s,font,fill,glow=0):
    k=(s,font.path,font.size,fill,glow)
    if k in _tc: return _tc[k]
    b=font.getbbox(s); pad=34
    im=Image.new('RGBA',(b[2]-b[0]+2*pad,b[3]-b[1]+2*pad),(0,0,0,0))
    dr=ImageDraw.Draw(im); dr.text((pad-b[0],pad-b[1]),s,font=font,fill=fill)
    if glow:
        g=im.filter(ImageFilter.GaussianBlur(glow)); im=Image.alpha_composite(g,im)
    a=np.asarray(im).astype(np.float32)/255
    if len(_tc)>400: _tc.clear()
    _tc[k]=a; return a
def put(img,a,cx,y,alpha=1.0):
    if alpha<=0: return
    h,w=a.shape[:2]; x0=int(cx-w/2); y0=int(y)
    xa,ya=max(0,x0),max(0,y0); xb,yb=min(W_,x0+w),min(H_,y0+h)
    if xb<=xa or yb<=ya: return
    s=a[ya-y0:yb-y0,xa-x0:xb-x0]; al=s[...,3:4]*alpha
    img[ya:yb,xa:xb]=img[ya:yb,xa:xb]*(1-al)+s[...,:3]*al
FH='BricolageGrotesque-Bold.ttf'; FT='Tektur-Medium.ttf'; FR='Tektur-Regular.ttf'
WH=(246,245,255,255); DIM=(160,166,200,255); RED=(255,70,80,255)
WHf=np.array([1,1,1],np.float32); REDf=np.array([1,0.25,0.3],np.float32)
def rgb(c): return tuple(int(min(v,1)*255) for v in c)+(255,)
def ease(x): x=min(max(x,0),1); return 1-(1-x)**3
def frame(f):
    t=f/FPS; L=np.zeros((H_,W_,3),np.float32)
    px,py,cur=frames[f]; done=t>=tend
    tl=max(0.0,LIMIT-min(t,tend)); danger=(tl<5.0) and not done
    intro=ease(t/0.5)
    for i in range(N):
        if i in breaks and breaks[i]<=t: continue
        x0,y0,sz,idx,cov,th=RING[i]
        gc=ph[i]+omega(i)*t
        rel=(th-gc+np.pi)%(2*np.pi)-np.pi
        m=cov*np.clip((np.abs(rel)-GAPS[i]/2)*RAD[i]+0.5,0,1)
        u=(rel+np.pi)/(2*np.pi)
        if omega(i)<0: u=1-u
        grad=0.30+0.70*u**1.6
        b=1.0 if i==cur else 0.50
        hh=[e[0] for e in hits if e[2]==i and e[0]<=t]
        if hh: b+=1.4*math.exp(-(t-hh[-1])/0.13)
        if t<0.7: m=m*ease((t-0.035*i)/0.3)
        cc=COL[i][None,:]*(1-u[:,None])+COL[i+2][None,:]*u[:,None]
        v=L[y0:y0+sz,x0:x0+sz]; v[idx]=np.minimum((m*grad*b)[:,None]*cc+ (m*max(0,b-1)*0.5)[:,None],1.7)
    # timer arc
    if not done or t<tend+0.3:
        frac=tl/LIMIT; mk=(thT<frac*2*np.pi)
        tc=REDf if danger else WHf*0.55
        k=(0.6+0.4*abs(math.sin(t*2*math.pi*2))) if danger else 1.0
        L[idxT[0][mk],idxT[1][mk]]=np.maximum(L[idxT[0][mk],idxT[1][mk]],covT[mk][:,None]*tc*k*intro)
        ah=frac*2*np.pi-np.pi/2; disc(L,CX+RT*math.cos(ah),CY+RT*math.sin(ah),8,tc*1.3,intro)
    # shockwaves / ripples
    for i,b in breaks.items():
        ag=t-b
        if 0<=ag<0.55:
            a=(1-ag/0.55)**2; m=np.clip(3.5-np.abs(RF-(RAD[i]+ag*620)),0,1)*a
            L=np.maximum(L,m[...,None]*COL[i])
    for e in hits:
        ag=t-e[0]
        if 0<=ag<0.3: wave(L,CX+e[3],CY+e[4],6+ag*190,3,COL[e[2]],(1-ag/0.3)**1.5)
    c=COL[min(cur,N-1)]
    K=30
    for j in range(K,0,-1):
        g=f-j
        if g<0: continue
        for u in (0.0,0.5):
            ax=frames[g][0]*(1-u)+frames[g+1][0]*u; ay=frames[g][1]*(1-u)+frames[g+1][1]*u
            w=1-(j-u)/K
            disc(L,CX+ax,CY+ay,RB*(0.2+0.8*w),c*(0.5+0.5*w)+WHf*0.3*w**3,0.8*w**1.5)
    disc(L,CX+px,CY+py,RB,WHf,1.0)
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
    bt=[b for b in bts if b<=t]; fl=0
    if bt:
        ag=t-bt[-1]; amp=(26 if bt[-1]==tend else 10)*math.exp(-ag/0.14)
        if amp>0.5: L=np.roll(L,(int(amp*math.sin(f*2.1)),int(amp*math.cos(f*1.7))),axis=(0,1))
        fl=0.10*math.exp(-ag/0.10)*(3 if bt[-1]==tend else 1)
    small=L.reshape(H_//4,4,W_//4,4,3).mean((1,3))
    gl=gaussian_filter(small,(5,5,0))*1.1+gaussian_filter(small,(20,20,0))*1.5
    gl=np.stack([np.asarray(Image.fromarray(gl[...,k]).resize((W_,H_),Image.BILINEAR)) for k in range(3)],-1)
    # background
    tint=c
    if bt and t-bt[-1]<0.5 and cur>0:
        w=(t-bt[-1])/0.5; tint=COL[cur-1]*(1-w)+c*w
    img=bg+neb[...,None]*tint*0.13+L+gl+fl
    tw=0.25+0.25*np.sin(SPH+t*SSP); img[SXY[:,1],SXY[:,0]]+=tw[:,None]*np.array([0.8,0.85,1.0])
    if danger:
        img+=vig[...,None]*REDf*0.30*(0.5+0.5*math.sin(t*2*math.pi*2-1.5))
    # HUD
    left=N-len(bt)
    hud=1.0 if t<tend+0.3 else max(0,1-(t-tend-0.3)/0.3)
    if hud>0:
        put(img,text('15 RINGS. 30 SECONDS.',F(FH,84),WH,6),CX,58,hud*ease(t/0.4))
        pulse=0.6+0.4*abs(math.sin(t*3.0)) if t<4 else 0.9
        put(img,text('will it escape?  comment YES or NO',F(FR,46),DIM),CX,156,hud*ease((t-0.25)/0.4)*pulse)
        ts=f'{tl:04.1f}'
        jx=int(4*math.sin(f*1.9)) if danger else 0
        put(img,text(ts,F(FT,118),RED if danger else WH,8),CX+jx,222,hud*ease((t-0.3)/0.4))
        ag=t-bt[-1] if bt else 9
        s=text(f'{left}',F(FT,130),rgb(c),8)
        put(img,s,CX-175,1432-16*math.exp(-ag/0.09),hud)
        put(img,text('RINGS LEFT',F(FR,50),WH),CX+60,1470,hud)
    te=t-tend
    if te>0.3:
        a=ease((te-0.3)/0.35)
        put(img,text('ESCAPED!',F(FH,190),WH,10),CX,560-40*(1-a),a)
        put(img,text(f'with {LIMIT-tend:.1f}s left',F(FT,76),rgb(COL[1])),CX,810,ease((te-0.75)/0.35))
        put(img,text('LEVEL 2: 20 RINGS',F(FH,96),rgb(COL[11]),6),CX,1040,ease((te-1.6)/0.35))
        put(img,text('follow to watch it',F(FR,52),WH),CX,1180,ease((te-1.9)/0.35))
    return (np.clip(img,0,1)*255).astype(np.uint8)
if __name__=='__main__':
    if sys.argv[1]=='shot':
        for f in sys.argv[2:]: Image.fromarray(frame(int(f))).save(f'f{f}.png')
    else:
        k=int(sys.argv[1]); n=int(sys.argv[2]); a=NF*k//n; b=NF*(k+1)//n
        p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r','60','-i','-','-c:v','libx264','-preset','medium','-crf','15','-pix_fmt','yuv420p',f'part{k}.mp4'],stdin=subprocess.PIPE)
        for f in range(a,b): p.stdin.write(frame(f).tobytes())
        p.stdin.close(); p.wait()
