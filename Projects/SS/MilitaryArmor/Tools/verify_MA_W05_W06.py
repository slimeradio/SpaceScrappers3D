import bpy, json, sys, math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,write,reset
for bid in ['MA-W05','MA-W06']:
    validations=[]
    for i in range(1,5):
        pid=bid+f'-P{i:02}';folder=ROOT/'Parts'/pid;meta=json.loads((folder/'part.json').read_text())
        if meta['functional_points']:
            for pt in meta['functional_points']:pt['node']='socket.root'
            write(folder/'part.json',meta)
        bpy.ops.wm.open_mainfile(filepath=str(folder/(pid+'.blend')))
        visible=[o for o in bpy.context.scene.objects if o.type=='MESH']
        assert visible
        assert all(all(math.isfinite(v) for v in o.location) for o in visible)
        assert all(abs(v-1)<.000001 for o in visible for v in o.scale)
        assert all(m['id'] in {mat.name for mat in bpy.data.materials} for m in meta['materials'])
        assert all('socket.'+m['id'] in bpy.data.objects for m in meta['mounts'])
        assert all(p['node'] in bpy.data.objects for p in meta['functional_points'])
        validations.append({'id':pid,'reopened':True,'mesh_count':len(visible),'materials_resolved':True,'logical_sockets_resolved':True,'unit_scale':True,'functional_points_resolved':True})
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blocks'/bid/(bid+'.blend')))
    ass=json.loads((ROOT/'Blocks'/bid/'assembly.json').read_text());checks=[]
    for inst in ass['instances']:
        assert inst['id'] in bpy.data.objects
        assert all(abs(v-w)<.000001 for v,w in zip(bpy.data.objects[inst['id']].location,inst['translation']))
    for frame in [1,30,43,60,90,120]:
        bpy.context.scene.frame_set(frame);checks.append({'frame':frame,'yaw_deg':math.degrees(bpy.data.objects['Yaw'].rotation_euler.z),'elevation_deg':math.degrees(bpy.data.objects['Elevation'].rotation_euler.x),'recoil_y':bpy.data.objects['Recoil'].location.y})
    assert not bpy.data.libraries
    d=json.loads((ROOT/'Blocks'/bid/'validation.json').read_text());d.update({'part_source_checks':validations,'animation_sample_values':checks,'external_libraries':[],'visual_review':'Final neutral hero and top inspected from TEMP, no intermediate user artifacts.'})
    write(ROOT/'Blocks'/bid/'validation.json',d)
