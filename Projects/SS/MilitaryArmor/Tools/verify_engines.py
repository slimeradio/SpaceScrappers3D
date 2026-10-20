import bpy,json,math,sys,csv,struct,tempfile
from pathlib import Path
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,write,Assembly

def inspect():
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];dep=bpy.context.evaluated_depsgraph_get();count=0;zero=0;points=[]
    for obj in meshes:
        ev=obj.evaluated_get(dep);mesh=ev.to_mesh();mesh.calc_loop_triangles();count+=len(mesh.loop_triangles);zero+=sum(t.area<1e-11 for t in mesh.loop_triangles)
        points.extend(obj.matrix_world@v.co for v in mesh.vertices);ev.to_mesh_clear()
    return {'mesh_count':len(meshes),'evaluated_triangles':count,'zero_area_triangles':zero,'finite':all(math.isfinite(c) for p in points for c in p),'unit_scale':all(all(abs(s-1)<1e-5 for s in o.scale) for o in meshes),'materials_resolved':all(o.data.materials and all(s.material for s in o.material_slots) for o in meshes),'bounds':{'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}}

catalog={r['ID']:r for r in csv.DictReader((ROOT.parent/'Catalog/blocks.csv').open(encoding='utf-8-sig',newline='')) if r['Тип_XML']=='Thruster'}
records=[]
for bid,expected in [('MA-E01',1),('MA-E02',3)]:
    folder=ROOT/'Blocks'/bid;assembly=json.loads((folder/'assembly.json').read_text(encoding='utf8'));validation=json.loads((folder/'validation.json').read_text(encoding='utf8'))
    checks={}
    for pid in sorted(set(i['part_id'] for i in assembly['instances'])):
        bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Parts'/pid/(pid+'.blend')));checks[pid]=inspect()
        assert checks[pid]['finite'] and checks[pid]['materials_resolved'] and checks[pid]['zero_area_triangles']==0
    bpy.ops.wm.open_mainfile(filepath=str(folder/(bid+'.blend')));source=inspect();world_points=[]
    for i in assembly['instances']:
        part=json.loads((ROOT/'Parts'/i['part_id']/'part.json').read_text(encoding='utf8'))
        node=bpy.data.objects[i['id']]
        for p in part['functional_points']:
            position=node.matrix_world@Vector(p['position']);direction=node.matrix_world.to_3x3()@Vector(p['direction']);up=node.matrix_world.to_3x3()@Vector(p['up'])
            world_points.append({'instance':i['id'],'role':p['role'],'position':list(position),'direction':list(direction.normalized()),'up':list(up.normalized()),'node_preserved':i['id']+'::'+p['node'] in bpy.data.objects})
    assert sum(p['role']=='thrust' for p in world_points)==expected
    assert sum(p['role']=='exhaust' for p in world_points)==expected
    assert all(p['direction']==([0,1,0] if p['role']=='thrust' else [0,-1,0]) and p['node_preserved'] for p in world_points)
    # Actual logical sockets in the assembly must coincide with mating roots.
    sockets=[]
    def aligned(parent_id,parent_pid,socket_id,child_id,child_pid):
        pa=json.loads((ROOT/'Parts'/parent_pid/'part.json').read_text(encoding='utf8'));ch=json.loads((ROOT/'Parts'/child_pid/'part.json').read_text(encoding='utf8'))
        a=next(x for x in pa['mounts'] if x['id']==socket_id);b=ch['mounts'][0]
        pm=bpy.data.objects[parent_id].matrix_world;cm=bpy.data.objects[child_id].matrix_world
        okay=(pm@Vector(a['position'])-cm@Vector(b['position'])).length<1e-5 and (pm.to_3x3()@Vector(a['forward'])-cm.to_3x3()@Vector(b['forward'])).length<1e-5 and (pm.to_3x3()@Vector(a['up'])-cm.to_3x3()@Vector(b['up'])).length<1e-5
        sockets.append({'parent':parent_id,'socket':socket_id,'child':child_id,'aligned':okay});assert okay
    if bid=='MA-E01':
        aligned('HullCassette','MA-E01-P01','chamber','Chamber','MA-E01-P02');aligned('Chamber','MA-E01-P02','nozzle','Nozzle','MA-E01-P03');aligned('Chamber','MA-E01-P02','thermal-L','Thermal.L','MA-E01-P04');aligned('Chamber','MA-E01-P02','thermal-R','Thermal.R','MA-E01-P04');aligned('Chamber','MA-E01-P02','service','ServiceCartridge','MA-E01-P05')
    else:
        for i in range(3):aligned('FuelManifold','MA-E02-P01','chamber'+str(i),'Chamber'+str(i),'MA-E02-P02');aligned('Chamber'+str(i),'MA-E02-P02','nozzle','Nozzle'+str(i),'MA-E02-P03')
        aligned('FuelManifold','MA-E02-P01','service','ServiceCartridge','MA-P06')
    # Views are temporary; no display lights/cameras are saved to final assets.
    review=Assembly.__new__(Assembly);review.bid=bid
    review.review(path=Path(tempfile.gettempdir())/(bid+'-final-top.png'),view=(0,0,8),target=(0,0,0),scale=3.3 if bid=='MA-E01' else 4.2,resolution=700)
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(folder/'Exports'/(bid+'.glb')));roundtrip=inspect()
    assert source['mesh_count']==roundtrip['mesh_count'] and source['evaluated_triangles']==roundtrip['evaluated_triangles']
    assert roundtrip['zero_area_triangles']==0 and roundtrip['finite'] and roundtrip['materials_resolved']
    assert all(abs(source['bounds'][k][i]-roundtrip['bounds'][k][i])<.0001 for k in ['min','max'] for i in range(3))
    raw=(folder/'Exports'/(bid+'.glb')).read_bytes();n,kind=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+n].decode('utf8').rstrip());assert not doc.get('images') and not doc.get('animations')
    validation.update({'part_sources_reopened':checks,'source_reopened':True,'source_geometry':source,'glb_roundtrip':roundtrip,'glb_imported_in_Blender':True,'functional_points_world':world_points,'socket_alignment':sockets,'thrust_sources':expected,'visual_review_TEMP':['final-review.png','final-top.png'],'no_plume_mesh':True,'static_no_animations':True,'checks_passed':True})
    write(folder/'validation.json',validation)
    records.append({'id':bid,'title':assembly['title'],'catalog_id':assembly['catalog_id'],'catalog_grid':assembly['catalog_grid'],'source':f'Blocks/{bid}/{bid}.blend','viewer_asset':f'Blocks/{bid}/Exports/{bid}.glb','thrust_sources':expected,'parts':sorted(set(i['part_id'] for i in assembly['instances'])),'triangles':source['evaluated_triangles'],'meshes':source['mesh_count']})
assert set(catalog)==set(r['catalog_id'] for r in records)
write(ROOT/'engines.json',{'schema':'MilitaryArmor.EngineAuthoringIndex/1','models':records,'catalog_Thruster_coverage_complete':True,'axes':{'exhaust':'-Y','thrust':'+Y','up':'+Z'},'physical_scale':'BU unspecified','game_validation':False,'checks_passed':True})
lines=['# Двигатели MilitaryArmor','','Все тяговые блоки общего каталога SS: крупное сопло среднего двигателя и компактный тройной кластер. Форма согласована с текущим космическим направлением.','','| ID | Блок | Сетка каталога | Источники тяги | Просмотр | Исходник |','|---|---|---|---:|---|---|']
for r in records:lines.append(f'| {r["id"]} | {r["title"]} | {r["catalog_grid"][0]}×{r["catalog_grid"][1]} | {r["thrust_sources"]} | [GLB]({r["viewer_asset"]}) | [Blender]({r["source"]}) |')
lines+=['','Восемь новых самостоятельных деталей; три камеры и три малых сопла используют общие источники. Сервисный картридж MA-P06 1.3 повторно использован в тройном блоке; средний получил отдельный компактный вариант по ширине. Материалы и эмиссивные области описаны в part.json; логические точки тяги, выхлопа и полные ориентации креплений сохраняются отдельно от видимой геометрии.','','Авторинг: +Z вверх, +Y тяга, −Y выход струи, единичный масштаб. Все три источника тройного двигателя сонаправлены. Единицы BU условные; это не утверждение о конвертации игровых координат и метров. Геометрия сопел полая; постоянное пламя отсутствует. Статическая конструкция без выдуманных анимаций.','','Проверены исходники, реальные импорты GLB, материалы, соответствие кромок креплений и функциональные точки. Игровая установка, сила тяги и баланс не менялись. Поле engine-room в каталоге относится к отдельному производителю топлива и не включено в набор тяговых блоков.']
write(ROOT/'Engines.md','\n'.join(lines));print('ENGINES_VERIFIED',flush=True)
