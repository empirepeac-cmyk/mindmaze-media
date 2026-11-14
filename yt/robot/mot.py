import numpy as np
from PIL import Image
def roi_motion(f0,f1,box):
    out=np.zeros(832); prev=None
    for f in range(f0,f1+1):
        a=np.asarray(Image.open(f'src/{f:04d}.png').convert('L').crop(box),dtype=np.float32)
        if prev is not None: out[f]=np.abs(a-prev).mean()
        prev=a
    return out
B=roi_motion(160,250,(240,820,520,1100))+roi_motion(300,341,(280,780,520,1080))+roi_motion(560,702,(0,800,330,1100))
np.save('brush.npy',B)
for a,b in [(160,250),(300,341),(560,702)]:
    print(a); print(' '.join(f'{B[f]:.0f}' for f in range(a,b+1)))
