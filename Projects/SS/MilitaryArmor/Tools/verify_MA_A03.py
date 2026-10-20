"""Actual source/GLB checks and TEMP-only final review for MA-A03."""
import sys,json,math,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector
from weapon_batch_core import ROOT,write,Assembly
BID='MA-A03';PID='MA-A03-P01';folder=ROOT/'Blocks'/BID

def inspect():
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];tris=0;zero=[];positions=[];emission=[];scales=[];nonman=[]
 for o in meshes:
  if any(abs(s-1)>1e-6 for s in o.scale):scales.append(o.name)
  deps=bpy.context.evaluated_depsgraph_get();me=o.evaluated_get(deps).to_mesh();me.calc_loop_triangles();tris+=len(me.loop_triangles)
  for t in me.loop_triangles:
   if t.area<=1e-10:zero.append(o.name)
  positions.extend(o.matrix_world@v.co for v in me.vertices)
  bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);nonman.extend([e.index for e in bm.edges if not e.is_manifold]);bm.free()
  for m in me.materials:
   if m and m.use_nodes:
    p=m.node_tree.nodes.get('Principled BSDF')
    if p and p.inputs['Emission Strength'].default_value>0:emission.append(m.name)
  o.evaluated_get(deps).to_mesh_clear()
 finite=all(math.isfinite(n) for p in positions for n in p)
 # Footprint triangle: x>=-.5, y<=.5, y>=x; z in0..28.
 outside=[list(p) for p in positions if p.x<-.500001 or p.y>.500001 or p.y<p.x-1e-6 or p.z<-1e-6 or p.z>.280001]
 bounds={'min':[min(p[i] for p in positions) for i in range(3)],'max':[max(p[i] for p in positions) for i in range(3)]}
 result={'mesh_count':len(meshes),'evaluated_triangles':tris,'material_slots':sum(len(o.data.materials) for o in meshes),'zero_area_triangles':len(zero),'nonmanifold_edges':len(nonman),'nonunit_scales':scales,'emission':emission,'finite':finite,'boundary_overshoot':outside,'bounds':bounds}
 assert len(meshes)<=2 and tris<=240 and not zero and finite and not outside and not emission and not scales and not nonman,result
 return result

results={}
for label,path in [('part_source',ROOT/'Parts'/PID/(PID+'.blend')),('assembly_source',folder/(BID+'.blend'))]:
 bpy.ops.wm.open_mainfile(filepath=str(path));results[label]=inspect()
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(folder/'Exports'/(BID+'.glb')));results['glb_roundtrip']=inspect();assert results['glb_roundtrip']['evaluated_triangles']==results['assembly_source']['evaluated_triangles']
# Read exact join walls from re-opened source.
bpy.ops.wm.open_mainfile(filepath=str(folder/(BID+'.blend')))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
assert len(meshes)==1
coords=[tuple(v.co) for v in meshes[0].data.vertices]
for z in [0,.16]:
 for x,y in [(-.5,-.5),(.5,.5),(-.5,.5)]:assert any(Vector((x,y,z)).__sub__(Vector(p)).length<1e-6 for p in coords)
results['join_contract']={'exact_three_bottom_and_structural_corner_points':True,'structural_z':[0,.16],'top_z':.28,'nominal_polygon':[[-.5,-.5],[.5,.5],[-.5,.5]]}
# Render only final geometry. No visual helper objects in saved source/export.
a=Assembly.__new__(Assembly);a.bid=BID
review=Path(tempfile.gettempdir())/'MilitaryArmor-A03-review';review.mkdir(exist_ok=True)
a.review(review/'oblique.png',view=(2.6,-3,3),target=(0,0,.12),scale=1.6,resolution=600)
# Existing lighting reused for top.
cam=bpy.context.scene.camera;cam.location=(0,0,4);cam.rotation_euler=(0,0,0);cam.data.ortho_scale=1.4;cam.rotation_euler=Vector((0,0,-1)).to_track_quat('-Z','Y').to_euler();bpy.context.scene.render.filepath=str(review/'top.png');bpy.ops.render.render(write_still=True)
# Four paired wedges tessellate a clean 2x2 square; same final mesh rotated 180deg.
original=meshes[0];mesh=original.data
for o in list(bpy.context.scene.objects):
 if o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)

for x in [-.5,.5]:
 for y in [-.5,.5]:
  for rot in [0,math.pi]:
   o=bpy.data.objects.new('Final neighbour',mesh);bpy.context.scene.collection.objects.link(o);o.location=(x,y,0);o.rotation_euler.z=rot
cam.location=(3,-4,4.5);cam.rotation_euler=(Vector((0,0,.1))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=3.2;bpy.context.scene.render.filepath=str(review/'neighbours.png');bpy.ops.render.render(write_still=True)
check=json.loads((folder/'validation.json').read_text('utf8'));check.update(results);check['internal_final_review']={'paths':[str(review/name) for name in ['oblique.png','top.png','neighbours.png']],'human_visual_inspection':'pending root image review','display_props_exported':False};check['checks_passed']=True;write(folder/'validation.json',check);print(json.dumps(results,indent=2));print('REVIEWS',review)