import numpy as np,sys,os,colorsys
from PIL import Image
from scipy import ndimage as ndi
from cls import hsv,C
CY=(40,225,255);YE=(255,232,30);AM=(255,176,20);OR=(255,100,25);RD=(255,42,36)
lin=lambda c:(np.array(c)/255.)**2.2
def mix(a,b,t):
    t=min(1,max(0,t)); t=t*t*(3-2*t); return (lin(a)*(1-t)+lin(b)*t)**(1/2.2)
def hmix(t):
    t=min(1,max(0,t)); t=t*t*(3-2*t)
    h=(190+(363-190)*t)%360; return np.array(colorsys.hsv_to_rgb(h/360,0.86,1.0))
def plan(f):
    """source class, target rgb (0..1) or None to leave"""
    if 70<=f<=171 and True:
        if f<=140: return 'ye',mix(CY,YE,(f-70)/16.)
        return 'ye',mix(YE,AM,(f-140)/45.)   # reaches ~0.7 at 171
    if 172<=f<=260:
        if f<=215: return 'rd',mix(mix(YE,AM,31/45.),OR,(f-171)/44.)
        return 'rd',mix(OR,RD,(f-215)/70.)
    if 295<=f<=345: return 'pk',np.array(RD)/255.
    if 455<=f<=702: return 'bl',hmix((f-688)/26.)
    if 703<=f<=750: return 'rd',hmix((f-688)/26.)
    return None,None
SAT={'ye':0.92,'rd':0.9,'pk':0.85,'bl':0.95}
def proc(f):
    a=np.asarray(Image.open(f'src/{f:04d}.png').convert('RGB'))
    cl,T=plan(f)
    if cl is None: return a,None
    h,s,v=hsv(a); lo,hi=C[cl]
    if cl=='pk': lo,hi=312,372
    if cl=='rd': lo,hi=344,376
    h2=np.where(h<16,h+360,h)
    inh=(h2>=lo-6)&(h2<(hi if cl in ("rd","pk") else hi+4))
    core=inh&(s>0.6)&(v>0.55); core[:420]=False
    lab,n=ndi.label(core)
    if n:
        ar=ndi.sum(core,lab,range(1,n+1)); core=np.isin(lab,1+np.nonzero(ar>=30)[0])
    if not core.any(): return a,None
    reg=ndi.binary_dilation(core,iterations=14)&inh&(s>0.22)&(v>0.12)
    w=ndi.gaussian_filter(reg.astype(np.float32),0.7); w=np.where(core,1,w)
    th,ts,tv=colorsys.rgb_to_hsv(*T)
    ns=np.clip(s*ts/SAT[cl],0,1); nv=np.clip(v*(0.9+0.1*tv),0,1)
    # hsv->rgb with constant hue
    hh=th*6; i=int(hh)%6; fr=hh-int(hh)
    p=nv*(1-ns); q=nv*(1-ns*fr); t=nv*(1-ns*(1-fr))
    r,g,b=[(nv,t,p),(q,nv,p),(p,nv,t),(p,q,nv),(t,p,nv),(nv,p,q)][i]
    out=np.stack([r,g,b],2)*255
    res=a*(1-w[...,None])+out*w[...,None]
    return res.round().clip(0,255).astype(np.uint8),reg
if __name__=='__main__':
    if sys.argv[1]=='all':
        os.makedirs('out',exist_ok=True)
        for f in range(1,831):
            o,_=proc(f); Image.fromarray(o).save(f'out/{f:04d}.png')
    else:
        fs=[int(x) for x in sys.argv[1:]]; W=Image.new('RGB',(300*len(fs),300*2))
        for i,f in enumerate(fs):
            o,reg=proc(f); a=Image.open(f'src/{f:04d}.png')
            if reg is not None and reg.any():
                ys,xs=np.nonzero(reg[:, :]); 
                # biggest cluster centre = median
                cx,cy=int(np.median(xs)),int(np.median(ys)); print(f,reg.sum(),cx,cy,xs.min(),xs.max(),ys.min(),ys.max())
            else: cx,cy=360,640; print(f,'none')
            bx=(max(0,min(420,cx-150)),cy-150,max(0,min(420,cx-150))+300,cy+150)
            W.paste(a.crop(bx),(300*i,0)); W.paste(Image.fromarray(o).crop(bx),(300*i,300))
        W.save('rc.jpg',quality=90)
