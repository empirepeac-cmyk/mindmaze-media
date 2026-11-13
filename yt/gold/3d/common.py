import pickle, math, random, sys, os
sys.path.insert(0,'/home/user/work/gold3d')
import sim, sim6
PK='/home/user/work/gold3d/run.pkl'
if not os.path.exists(PK):
    r=sim6.run(1,D=21000,T=19.5); pickle.dump(r,open(PK,'wb'))
R=pickle.load(open(PK,'rb'))
FR=R['frames']; st=R['st']; HITS=st['hits']; OUT=st['brk']; LT,LP=st['land']; TREL=st['trel']; REL=R['rel']
WSP=sim6.WSP; CX,CY=sim6.CX,sim6.CY; POT=R['pot']; CUP=R['cup']; PEGS=R['pegs']; TRAY=sim.TRAY; GT=R['gt']
T_CUT=TREL+2.7; END=T_CUT+0.8; FPS=30; NF=int(END*FPS)
ZA=1.6; YA=CY-0.45*1920/ZA; ZMAX=1.3; Y0T=1560-0.58*1920/ZMAX
def ease(x): x=max(0,min(1,x)); return x*x*(3-2*x)
EP=[]; cur=0.0
for f in range(int(END*60)+2):
    g=FR[min(f,len(FR)-1)][1]; t=f/60; tgt=0.0
    if g and t>OUT: tgt=max(0,min(1,(g[1]-CY-30)/(1380-CY)))
    tgt=max(tgt,cur); cur+=(tgt-cur)*0.09; EP.append(cur)
def cam(t):
    """returns cx, y0, vw, vh in world px"""
    f=min(int(round(t*60)),len(EP)-1)
    back=ease((t-TREL-0.1)/1.3) if t>TREL else 0.0
    e=ease(EP[f])*(1-back); zb=1.0+(ZA-1.0)*(1-back); ya=YA*(1-back)
    z=zb+(ZMAX-zb)*e; vw,vh=1080/z,1920/z
    return 540.0, ya+(Y0T-ya)*e, vw, vh
def state(t):
    f=min(int(round(t*60)),len(FR)-1); return FR[f]
def goldk(t,x,y):
    if t>=TREL-0.3: return 1.0
    if t<=LT: return 0.0
    return max(0.0,min(1.0,((t-LT)*WSP-math.hypot(x-LP[0],y-LP[1]))/60))
def nhits(t): return sum(1 for h in HITS if h[0]<=t)
def left(t): return sum(1 for i in REL if REL[i]>t)
if __name__=='__main__': print(NF,END,OUT,LT,TREL,len(HITS),[round(h[0],2) for h in HITS])
