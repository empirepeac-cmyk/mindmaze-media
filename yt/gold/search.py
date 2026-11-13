import sim, sys, time
from multiprocessing import Pool
def job(a):
    seed,gx=a
    r=sim.run(seed,gx,record=False,T=15.0)
    bh=[h for h in r['hits'] if h[1]=='ball']
    if not bh: return None
    t,_,oid,imp,pos=bh[0]
    m=r['mat'].get(oid,(None,))[0]
    oy=r['final'][oid][1]
    if pos[1]<sim.DIV_TOP-200: return None
    cnt=[0,0,0]
    for i,(mm,tt) in r['mat'].items(): cnt[mm]+=1
    npeg=len([h for h in r['hits'] if h[1]=='peg'])
    return dict(seed=seed,gx=gx,t=round(t,2),m=m,oy=round(oy),px=round(pos[0]),imp=round(imp),bin=r['gold_bin'],
                gp=(round(r['gold_pos'][0]),round(r['gold_pos'][1])),sp=round(r['gold_speed'],1),cnt=cnt,npeg=npeg,
                nb=len(bh))
if __name__=='__main__':
    seeds=[int(s) for s in sys.argv[1:]]
    jobs=[(s,gx) for s in seeds for gx in range(600,861,13)]
    t=time.time()
    with Pool(4) as p: R=p.map(job,jobs)
    for r in R:
        if r and r['m']==2 and r['bin']==1 and r['px']>sim.DIVX[1]-5 and sum(r['cnt'])==99: print('***',r,flush=True)
        elif r and r['m']==2 and r['bin']==1: print('  *',r)
    print(len(jobs),time.time()-t)
