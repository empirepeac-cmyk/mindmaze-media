import numpy as np,pickle
from PIL import Image
def hsv(a):
    f=a.astype(np.float32)/255; mx=f.max(2); mn=f.min(2); d=mx-mn
    r,g,b=f[...,0],f[...,1],f[...,2]
    h=np.zeros_like(mx); m=d>1e-6
    hr=((g-b)/np.where(m,d,1))%6; hg=(b-r)/np.where(m,d,1)+2; hb=(r-g)/np.where(m,d,1)+4
    h=np.where(mx==r,hr,np.where(mx==g,hg,hb))*60; h=np.where(m,h,0)
    return h,np.where(mx>0,d/np.maximum(mx,1e-6),0),mx
C={'cy':(168,200),'ye':(47,72),'gr':(110,166),'bl':(200,240),'pk':(318,348),'rd':(348,376)}
if __name__=='__main__':
    R=[]
    for k in range(1,831):
        a=np.asarray(Image.open(f'src/{k:04d}.png').convert('RGB')); h,s,v=hsv(a)
        st=(s>0.6)&(v>0.55); h2=np.where(h<16,h+360,h)
        R.append({n:int((st&(h2>=lo)&(h2<hi)).sum()) for n,(lo,hi) in C.items()})
    pickle.dump(R,open('cls.pkl','wb'))
    for k in range(0,830,3): print(k+1,round((k+1)/24,2),' '.join(f'{n}{c}' for n,c in R[k].items() if c>30))
