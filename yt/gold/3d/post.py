import numpy as np, sys, subprocess, math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0,'/home/user/work/gold3d')
import common as C
FD='/mnt/skills/examples/canvas-design/canvas-fonts/'
_f={}
def F(n,s):
    if (n,s) not in _f: _f[(n,s)]=ImageFont.truetype(FD+n,s)
    return _f[(n,s)]
HB='NationalPark-Bold.ttf'; MB='JetBrainsMono-Bold.ttf'
WH=(246,247,252); GOLD=(255,196,60); CY=(150,220,255); RED=(255,96,84); DIM=(170,180,205)
NH=len(C.HITS)
def ease(x): x=min(max(x,0),1); return 1-(1-x)**3
def line(d,cx,y,parts,font,a=255):
    w=sum(d.textlength(s,font=font) for s,_ in parts); x=cx-w/2
    for s,c in parts:
        d.text((x,y),s,font=font,fill=c+(int(max(0,min(255,a))),)); x+=d.textlength(s,font=font)
yy,xx=np.mgrid[0:1920,0:1080].astype(np.float32)
VIG=(1-0.42*np.clip(((xx-540)/760)**2+((yy-960)/1250)**2,0,1))[...,None]
BAND=np.clip((600-yy)/230,0,1)[...,None]**1.2*0.96
import random as _r
def w2s(t,wx,wy):
    cx,y0,vw,vh=C.cam(t); return (wx-(cx-vw/2))/vw*1080,(wy-y0)/vh*1920
# sparkle spawn list: one per ball when the gold wave reaches it
_P,_G=C.state(C.LT+0.5); SPK=[]; _rr=_r.Random(3)
for i,(x,y) in _P.items():
    t0=C.LT+math.hypot(x-C.LP[0],y-C.LP[1])/C.WSP
    for k in range(2): SPK.append((t0+_rr.uniform(0,0.15),x+_rr.uniform(-14,14),y+_rr.uniform(-14,14),_rr.uniform(-40,40),_rr.uniform(-190,-60),_rr.uniform(0.45,0.9),_rr.uniform(7,15)))
def shake(t):
    dx=dy=0.0
    for h in C.HITS:
        d=t-h[0]
        if 0<=d<0.14: a=(2.5+5*min(1,h[1]/1300))*(1-d/0.14); dx+=a*math.sin(d*95+h[0]*7); dy+=a*math.cos(d*83+h[0]*3)
    for T0,A in ((C.OUT,20),(C.TREL,26)):
        d=t-T0
        if 0<=d<0.45: a=A*(1-d/0.45)**2; dx+=a*math.sin(d*70); dy+=a*math.cos(d*61+1)
    return dx,dy
TR={'f':-9,'img':None}
def glow_at(a,sx,sy,rad,col,k):
    y0=int(max(0,sy-rad)); y1=int(min(1920,sy+rad)); x0=int(max(0,sx-rad)); x1=int(min(1080,sx+rad))
    if y1<=y0 or x1<=x0: return
    yy_,xx_=np.mgrid[y0:y1,x0:x1].astype(np.float32)
    g=np.clip(1-np.sqrt((xx_-sx)**2+(yy_-sy)**2)/rad,0,1)**2*k
    a[y0:y1,x0:x1]+=g[...,None]*np.array(col,np.float32)
def frame(f,src):
    t=f/C.FPS
    im=Image.open(src).convert('RGB').resize((1080,1920),Image.LANCZOS).filter(ImageFilter.UnsharpMask(2,60,2))
    a=np.asarray(im).astype(np.float32)/255
    br=np.clip(a-0.62,0,1)*2.4
    sm=Image.fromarray((np.clip(br,0,1)*255).astype(np.uint8)).resize((270,480),Image.BILINEAR)
    b1=np.asarray(sm.filter(ImageFilter.GaussianBlur(5)).resize((1080,1920),Image.BILINEAR)).astype(np.float32)/255
    b2=np.asarray(sm.filter(ImageFilter.GaussianBlur(18)).resize((1080,1920),Image.BILINEAR)).astype(np.float32)/255
    # light trails: decayed bright parts of the previous frames
    brt=np.clip(a-0.55,0,1)*1.6
    if TR['f']==f-1 and TR['img'] is not None: tr=np.maximum(brt,TR['img']*0.62)
    else: tr=brt
    TR['f']=f; TR['img']=tr
    a=np.maximum(a,np.minimum(tr*0.75+0.25*a,1.0)*(tr>0.02))
    a=np.clip(a*1.05+b1*0.45+b2*0.35,0,1)
    # grade: contrast + saturation
    a=np.clip((a-0.5)*1.12+0.5,0,1); lum=a.mean(2,keepdims=True); a=np.clip(lum+(a-lum)*1.22,0,1)
    # local light bursts at the two shatters and the gold landing
    for T0,(wx,wy),rad,col,dur in ((C.OUT,(C.CX,C.CY+20),520,(0.75,0.92,1.0),0.3),(C.TREL,(540,1580),900,(0.8,0.95,1.0),0.35),(C.LT,C.LP,420,(1.0,0.78,0.3),0.4)):
        d_=t-T0
        if 0<=d_<dur:
            sx,sy=w2s(t,wx,wy); glow_at(a,sx,sy,rad,col,0.9*(1-d_/dur)**2)
    # golden sparkles
    for t0,x,y,vx,vy,life,sz in SPK:
        d_=t-t0
        if 0<=d_<life:
            sx,sy=w2s(t,x+vx*d_,y+vy*d_); k=math.sin(math.pi*d_/life)
            glow_at(a,sx,sy,sz*2.2,(1.0,0.85,0.45),0.9*k); glow_at(a,sx,sy,sz*0.7,(1,1,1),1.0*k)
    a=np.clip(a,0,1)
    dx,dy=shake(t)
    if abs(dx)+abs(dy)>0.3:
        a=np.asarray(Image.fromarray((a*255).astype(np.uint8)).resize((1140,2026),Image.BILINEAR).crop((int(30+dx),int(53+dy),int(30+dx)+1080,int(53+dy)+1920))).astype(np.float32)/255
    a=a*VIG
    # white flash on the two shatters
    for T0,s_ in ((C.OUT,0.10),(C.TREL,0.14)):
        if 0<=t-T0<0.2: a=np.clip(a+s_*(1-(t-T0)/0.2)**2,0,1)
    a=a*(1-BAND)+np.array([0.02,0.03,0.07],np.float32)*BAND
    im=Image.fromarray((a*255).astype(np.uint8)).convert('RGBA')
    ov=Image.new('RGBA',(1080,1920),(0,0,0,0)); d=ImageDraw.Draw(ov)
    nh=C.nhits(t); lf=C.left(t)
    if t<C.OUT:
        k=ease(t/0.3)
        line(d,540,150,[('How many hits',WH)],F(HB,76),255*k)
        line(d,540,236,[('can the ',WH),('glass',CY),(' take?',WH)],F(HB,76),255*k)
        lh=max([h[0] for h in C.HITS if h[0]<=t] or [-9]); p=max(0,1-(t-lh)/0.25)
        sz=int(92+26*p); line(d,540,350-13*p,[(f'{nh:02d}',mix(WH,CY,p))],F(MB,sz),255*k)
        line(d,540,466,[('HITS',DIM)],F(MB,36),255*k)
        col=RED if lf<=10 else DIM
        line(d,540,522,[(f'{lf:02d} balls left',col)],F(MB,42),255*ease((t-0.8)/0.4))
    elif t<C.TREL:
        k=ease((t-C.OUT)/0.3)
        line(d,540,170-20*(1-k),[('It broke on hit ',WH),(str(NH),GOLD)],F(HB,84),255*k)
    elif t<C.T_CUT:
        k=ease((t-C.TREL)/0.35)
        line(d,540,170-20*(1-k),[('GOLD',GOLD),(' set them all free',WH)],F(HB,80),255*k)
    else:
        k=ease((t-C.T_CUT)/0.25)
        line(d,540,170,[('Next: the ',WH),('black',(120,126,140)),(' one',WH)],F(HB,84),255*k)
        bx_,by_,br_=540,420,84
        d.ellipse([bx_-br_,by_-br_,bx_+br_,by_+br_],fill=(5,5,8,int(255*k)),outline=(120,126,140,int(255*k)),width=3)
        d.arc([bx_-br_+16,by_-br_+16,bx_+br_-16,by_+br_-16],200,275,fill=(255,255,255,int(255*k)),width=9)
        d.ellipse([bx_+26,by_+36,bx_+40,by_+46],fill=(110,116,130,int(200*k)))
    g=ov.filter(ImageFilter.GaussianBlur(9)); ga=g.split()[3].point(lambda v:int(v*0.45)); g.putalpha(ga)
    return Image.alpha_composite(Image.alpha_composite(im,g),ov).convert('RGB')
def mix(a,b,k): return tuple(int(a[i]+(b[i]-a[i])*k) for i in range(3))
if __name__=='__main__':
    if sys.argv[1]=='shot': frame(int(sys.argv[2]),sys.argv[3]).save(sys.argv[4])
    else:
        p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r','30','-i','-','-c:v','libx264','-preset','slow','-crf','17','-pix_fmt','yuv420p','v.mp4'],stdin=subprocess.PIPE)
        for f in range(C.NF): p.stdin.write(frame(f,f'fr/f{f:04d}.png').tobytes())
        p.stdin.close(); p.wait()
