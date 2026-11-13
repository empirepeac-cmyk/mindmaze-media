import bpy, time, math
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene; s.render.engine='CYCLES'; s.cycles.device='CPU'; s.cycles.samples=48; s.cycles.use_denoising=True
s.render.resolution_x=540; s.render.resolution_y=960
w=bpy.data.worlds.new('w'); s.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0.02,0.02,0.04,1)
bpy.ops.mesh.primitive_plane_add(size=20); fl=bpy.context.object
m=bpy.data.materials.new('f'); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value=(0.05,0.05,0.07,1); b.inputs['Roughness'].default_value=0.15; fl.data.materials.append(m)
import random; random.seed(1)
for i in range(7):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5,location=(random.uniform(-1.5,1.5),random.uniform(-1.5,1.5),0.5),segments=48,ring_count=24); o=bpy.context.object; bpy.ops.object.shade_smooth()
    g=bpy.data.materials.new('g'); g.use_nodes=True; p=g.node_tree.nodes['Principled BSDF']
    import colorsys; c=colorsys.hsv_to_rgb(i/7,0.7,1); p.inputs['Base Color'].default_value=(*c,1); p.inputs['Roughness'].default_value=0.02
    try: p.inputs['Transmission Weight'].default_value=1.0
    except Exception: p.inputs['Transmission'].default_value=1.0
    o.data.materials.append(g)
bpy.ops.object.light_add(type='AREA',location=(2,-3,5)); L=bpy.context.object; L.data.energy=900; L.data.size=4
bpy.ops.object.camera_add(location=(0,-6.5,4.2),rotation=(math.radians(58),0,0)); s.camera=bpy.context.object
s.render.filepath='/home/user/work/b3d/t.png'; t=time.time(); bpy.ops.render.render(write_still=True); print('RENDER_SEC',round(time.time()-t,1))
