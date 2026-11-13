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
def frame(f,src):
    t=f/C.FPS
    im=Image.open(src).convert('RGB').resize((1080,1920),Image.LANCZOS).filter(ImageFilter.UnsharpMask(2,60,2))
    a=np.asarray(im).astype(np.float32)/255
    br=np.clip(a-0.62,0,1)*2.4
    sm=Image.fromarray((np.clip(br,0,1)*255).astype(np.uint8)).resize((270,480),Image.BILINEAR)
    b1=np.asarray(sm.filter(ImageFilter.GaussianBlur(5)).resize((1080,1920),Image.BILINEAR)).astype(np.float32)/255
    b2=np.asarray(sm.filter(ImageFilter.GaussianBlur(18)).resize((1080,1920),Image.BILINEAR)).astype(np.float32)/255
    a=np.clip(a*1.05+b1*0.45+b2*0.35,0,1)*VIG
    # white flash on the two shatters
    for T0,s_ in ((C.OUT,0.22),(C.TREL,0.30)):
        if 0<=t-T0<0.25: a=np.clip(a+s_*(1-(t-T0)/0.25)**2,0,1)
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
