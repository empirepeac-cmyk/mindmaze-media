import bpy, bmesh, sys, math, time, os, random, mathutils
sys.path.insert(0,'/home/user/work/gold3d')
import common as C, sim
a=sys.argv[sys.argv.index('--')+1:]; RX,RY,SPP=int(a[0]),int(a[1]),int(a[2]); F0,F1,STEP=int(a[3]),int(a[4]),int(a[5]); OUT=a[6]
def bx(x): return (x-540)/100
def bz(y): return (960-y)/100
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene; s.render.engine='CYCLES'; s.cycles.device='CPU'; s.cycles.samples=SPP; s.cycles.use_denoising=True
s.cycles.max_bounces=6; s.cycles.glossy_bounces=4; s.cycles.diffuse_bounces=2; s.cycles.transparent_max_bounces=8; s.cycles.transmission_bounces=4
s.cycles.caustics_reflective=False; s.cycles.caustics_refractive=False
s.render.use_persistent_data=True; s.render.resolution_x=RX; s.render.resolution_y=RY; s.render.image_settings.file_format='PNG'
s.view_settings.view_transform='Standard'
w=bpy.data.worlds.new('w'); s.world=w; w.use_nodes=True
bg=w.node_tree.nodes['Background']; bg.inputs[0].default_value=(0.01,0.015,0.04,1); bg.inputs[1].default_value=1.0
def mat(name,col,rough=0.3,metal=0.0,emit=None,es=0.0,coat=0.0):
    m=bpy.data.materials.new(name); m.use_nodes=True; p=m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value=(*col,1); p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
    if coat and 'Coat Weight' in p.inputs: p.inputs['Coat Weight'].default_value=coat
    if emit:
        p.inputs['Emission Color'].default_value=(*emit,1); p.inputs['Emission Strength'].default_value=es
    return m
def box(x0,y0,x1,y1,d0,d1,m):
    bpy.ops.mesh.primitive_cube_add(size=1,location=((bx(x0)+bx(x1))/2,(d0+d1)/2,(bz(y0)+bz(y1))/2)); o=bpy.context.object
    o.scale=(abs(bx(x1)-bx(x0)),abs(d1-d0),abs(bz(y1)-bz(y0))); o.data.materials.append(m); return o
def seg(p,q,th,d0,d1,m,ext=0.0):
    L=math.hypot(q[0]-p[0],q[1]-p[1])/100+ext; ang=math.atan2(bz(q[1])-bz(p[1]),bx(q[0])-bx(p[0]))
    bpy.ops.mesh.primitive_cube_add(size=1,location=((bx(p[0])+bx(q[0]))/2,(d0+d1)/2,(bz(p[1])+bz(q[1]))/2)); o=bpy.context.object
    o.scale=(L,abs(d1-d0),th/100); o.rotation_euler=(0,-ang,0); o.data.materials.append(m); return o
def prism(pts,d0,d1,m):
    me=bpy.data.meshes.new('pr'); bm=bmesh.new()
    f=[bm.verts.new((bx(x),d0,bz(y))) for x,y in pts]; b=[bm.verts.new((bx(x),d1,bz(y))) for x,y in pts]
    n=len(pts); bm.faces.new(f); bm.faces.new(b[::-1])
    for i in range(n): bm.faces.new([f[(i+1)%n],f[i],b[i],b[(i+1)%n]])
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new('pr',me); s.collection.objects.link(o); me.materials.append(m); return o
# ---------- materials
BOARD=mat('board',(0.006,0.010,0.030),rough=0.6)
FRAME=mat('frame',(0.55,0.6,0.72),rough=0.22,metal=1.0,emit=(0.3,0.45,0.9),es=0.12)
PEG=mat('peg',(0.9,0.92,1.0),rough=0.2,metal=0.0,emit=(0.55,0.75,1.0),es=2.6)
def glassmat(name,es0=0.45):
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree; nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial'); tr=nt.nodes.new('ShaderNodeBsdfTransparent'); gl=nt.nodes.new('ShaderNodeBsdfGlossy')
    mx=nt.nodes.new('ShaderNodeMixShader'); fr=nt.nodes.new('ShaderNodeFresnel'); em=nt.nodes.new('ShaderNodeEmission'); ad=nt.nodes.new('ShaderNodeAddShader')
    at=nt.nodes.new('ShaderNodeAttribute'); at.attribute_type='OBJECT'; at.attribute_name='fl'
    ma=nt.nodes.new('ShaderNodeMath'); ma.operation='MULTIPLY_ADD'; ma.inputs[1].default_value=3.0; ma.inputs[2].default_value=es0
    tr.inputs[0].default_value=(0.72,0.9,1.0,1); gl.inputs[0].default_value=(0.9,0.97,1,1); gl.inputs[1].default_value=0.04; fr.inputs[0].default_value=1.9
    em.inputs[0].default_value=(0.45,0.8,1.0,1)
    nt.links.new(at.outputs['Fac'],ma.inputs[0]); nt.links.new(ma.outputs[0],em.inputs[1])
    nt.links.new(fr.outputs[0],mx.inputs[0]); nt.links.new(tr.outputs[0],mx.inputs[1]); nt.links.new(gl.outputs[0],mx.inputs[2])
    nt.links.new(mx.outputs[0],ad.inputs[0]); nt.links.new(em.outputs[0],ad.inputs[1]); nt.links.new(ad.outputs[0],out.inputs[0]); return m
GLASS=glassmat('glass'); SHARD=glassmat('shard',1.2)
CRACK=mat('crack',(1,1,1),rough=0.5,emit=(1.0,1.0,1.0),es=5.0)
def ballmat():
    m=bpy.data.materials.new('ball'); m.use_nodes=True; nt=m.node_tree; p=nt.nodes['Principled BSDF']
    at=nt.nodes.new('ShaderNodeAttribute'); at.attribute_type='OBJECT'; at.attribute_name='g'
    at2=nt.nodes.new('ShaderNodeAttribute'); at2.attribute_type='OBJECT'; at2.attribute_name='e'
    def mixc(a,b):
        n=nt.nodes.new('ShaderNodeMix'); n.data_type='RGBA'; n.inputs[6].default_value=(*a,1); n.inputs[7].default_value=(*b,1); nt.links.new(at.outputs['Fac'],n.inputs[0]); return n.outputs[2]
    def mixf(a,b):
        n=nt.nodes.new('ShaderNodeMapRange'); n.inputs[3].default_value=a; n.inputs[4].default_value=b; nt.links.new(at.outputs['Fac'],n.inputs[0]); return n.outputs[0]
    nt.links.new(mixc((0.86,0.87,0.9),(1.0,0.5,0.06)),p.inputs['Base Color'])
    nt.links.new(mixf(0.0,1.0),p.inputs['Metallic']); nt.links.new(mixf(0.14,0.2),p.inputs['Roughness'])
    nt.links.new(mixf(1.0,0.0),p.inputs['Coat Weight'])
    p.inputs['Emission Color'].default_value=(1.0,0.55,0.12,1); nt.links.new(at2.outputs['Fac'],p.inputs['Emission Strength'])
    return m
BALL=ballmat()
# ---------- static geometry
box(-600,-600,1680,3000,0.30,0.40,BOARD)
XL,XR=sim.XL,sim.XR
seg((XL,392),(XL,1290),12,-0.22,0.3,FRAME); seg((XR,392),(XR,1290),12,-0.22,0.3,FRAME)
seg(C.POT[0],C.POT[1],12,-0.22,0.3,FRAME,0.06); seg(C.POT[-2],C.POT[-1],12,-0.22,0.3,FRAME,0.06)
# tray bracket (no floor)
seg((92,196),(988,196),10,-0.22,0.3,FRAME,0.1); seg((92,196),(92,360),10,-0.22,0.3,FRAME); seg((988,196),(988,360),10,-0.22,0.3,FRAME)
for x,y in C.PEGS:
    bpy.ops.mesh.primitive_cylinder_add(radius=sim.PEG_R/100,depth=0.5,vertices=24,location=(bx(x),0.05,bz(y)),rotation=(math.radians(90),0,0)); o=bpy.context.object; bpy.ops.object.shade_smooth(); o.data.materials.append(PEG)
# glass pot
pot=[seg(C.POT[i],C.POT[i+1],11,-0.24,0.3,GLASS,0.1) for i in range(1,len(C.POT)-2)]
# glass cup block: inverted trapezoid with V notch
CXp,CYp=C.CX,C.CY
rel=[(-42,-28),(-33,-28),(-10,2),(10,2),(33,-28),(42,-28),(15,88),(-15,88)]
cup=prism([(CXp+x,CYp+y+4) for x,y in rel],-0.24,0.28,GLASS)
FAR=(0,0,300)
# cracks: jagged emissive lines on the cup's front face, one per hit
rr=random.Random(4); cracks=[]
def inside(x,y):
    if y<5 or y>84: return False
    hw=15+(42-15)*(88-y)/116.0
    return abs(x)<hw-3
for n in range(len(C.HITS)):
    parts=[]
    x,y=rr.uniform(-12,12),5.0+rr.uniform(0,40)*(n/21.0); ang=rr.uniform(math.radians(40),math.radians(140))
    for k in range(rr.randint(2,4)):
        L=rr.uniform(8,15); nx,ny=x+math.cos(ang)*L,y+math.sin(ang)*L
        if not inside(nx,ny): ang=math.pi-ang+rr.uniform(-0.3,0.3); nx,ny=x+math.cos(ang)*L*0.6,y+abs(math.sin(ang))*L*0.6
        if not inside(nx,ny): break
        parts.append(seg((CXp+x,CYp+y+4),(CXp+nx,CYp+ny+4),1.15,-0.262,-0.245,CRACK,0.005)); x,y=nx,ny; ang+=rr.uniform(-0.9,0.9)
    cracks.append(parts)
# shards
def mkshards(n,seed,src,spread):
    r_=random.Random(seed); L=[]
    for i in range(n):
        x0,y0=src(r_); sz=r_.uniform(7,17)
        pts=[(sz*math.cos(a),sz*math.sin(a)*r_.uniform(0.4,0.9)) for a in (0.2,2.2+r_.uniform(-.4,.4),4.3+r_.uniform(-.4,.4))]
        o=prism([(540+px,960+py) for px,py in pts],-0.03,0.03,SHARD); o['fl']=0.0
        vx,vy=spread(r_,x0,y0); L.append((o,x0,y0,vx,vy,r_.uniform(0,6.28),r_.uniform(-9,9),r_.uniform(-6,6),r_.uniform(-0.2,0.12)))
    return L
cupsh=mkshards(18,8,lambda r_:(CXp+r_.uniform(-34,34),CYp+r_.uniform(-20,88)),lambda r_,x,y:(r_.uniform(-380,380),r_.uniform(-420,60)))
pp=C.POT[1:-1]
def potsrc(r_):
    k=r_.randrange(len(pp)-1); u=r_.random(); return (pp[k][0]+(pp[k+1][0]-pp[k][0])*u, pp[k][1]+(pp[k+1][1]-pp[k][1])*u)
potsh=mkshards(46,21,potsrc,lambda r_,x,y:((x-540)*r_.uniform(0.8,2.2),r_.uniform(-250,150)))
def place(L,dt):
    for o,x0,y0,vx,vy,a0,w,w2,dy in L:
        if dt<0: o.location=FAR; continue
        x=x0+vx*dt; y=y0+vy*dt+900*dt*dt
        o.location=(bx(x),dy-0.1,bz(y)); o.rotation_euler=(w2*dt,a0+w*dt,w2*dt*0.6)
# balls
bpy.ops.mesh.primitive_uv_sphere_add(radius=1,segments=40,ring_count=20,location=(0,0,300)); base=bpy.context.object; bpy.ops.object.shade_smooth()
base.data.materials.append(BALL)
balls=[]
for i in range(len(C.TRAY)):
    o=base.copy(); s.collection.objects.link(o); o.scale=(sim.RB/100,)*3; o['g']=0.0; o['e']=0.0; balls.append(o)
gold=base.copy(); s.collection.objects.link(gold); gold.scale=(sim.RG/100,)*3; gold['g']=1.0; gold['e']=1.3
cup['fl']=0.0
for o in pot: o['fl']=0.0
def light(loc,e,size,col=(1,1,1),tgt=(0,0,0)):
    bpy.ops.object.light_add(type='AREA',location=loc); L=bpy.context.object; L.data.energy=e; L.data.size=size; L.data.color=col
    d=mathutils.Vector(tgt)-mathutils.Vector(loc); L.rotation_euler=d.to_track_quat('-Z','Y').to_euler(); return L
light((-5,-7,9),2100,4); light((7,-6,-6),500,10,(0.4,0.6,1.0)); light((0,-12,0),70,18); light((5,-8,6),380,5,(1.0,0.85,0.65))
bpy.ops.object.camera_add(location=(0,-12,0),rotation=(math.radians(90),0,0)); cam=bpy.context.object; cam.data.type='ORTHO'; s.camera=cam
os.makedirs(OUT,exist_ok=True)
for f in range(F0,F1,STEP):
    fp=f'{OUT}/f{f:04d}.png'
    if os.path.exists(fp): continue
    t=f/C.FPS; P,G=C.state(t)
    for i,o in enumerate(balls):
        x,y=P[i] if i in P else C.TRAY[i][:2]
        o.location=(bx(x),0,bz(y)); k=C.goldk(t,x,y); o['g']=k; o['e']=3.0*4*k*(1-k)+(0.45 if k>=1 else 0); o.update_tag()
    gx,gy=G if G else (C.CX,400); gold.location=(bx(gx),0,bz(gy))
    # cup
    if t<C.OUT:
        cup.location=(0,0,0); nh=C.nhits(t); lh=max([h[0] for h in C.HITS if h[0]<=t] or [-9])
        cup['fl']=max(0.0,1-(t-lh)/0.16); cup.update_tag()
        for n,parts in enumerate(cracks):
            for o in parts: o.hide_render=not (n<nh)
    else:
        cup.location=FAR
        for parts in cracks:
            for o in parts: o.hide_render=True
    place(cupsh,t-C.OUT)
    for o in pot: o.hide_render=t>=C.TREL
    place(potsh,t-C.TREL)
    cx,y0,vw,vh=C.cam(t); cam.data.ortho_scale=vh/100; cam.location=(bx(cx),-12,bz(y0+vh/2))
    s.render.filepath=fp; t0=time.time(); bpy.ops.render.render(write_still=True); print('FRAME',f,round(time.time()-t0,1),flush=True)
