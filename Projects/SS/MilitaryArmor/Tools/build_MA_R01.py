"""MA-R01 authoring. Only new reactor parts and this assembly. No GLB."""
import sys, math, json, hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,bmesh
from mathutils import Vector
from weapon_batch_core import Part,Assembly,ROOT,AXES,write
BID='MA-R01'

def inspect():
    bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get();tri=0;zero=0;nonman=0;volumes=[];pts=[];bad=[]
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    for o in meshes:
        bm=bmesh.new();bm.from_mesh(o.data);nonman+=sum(not e.is_manifold for e in bm.edges);volumes.append(bm.calc_volume(signed=True));bm.free()
        ev=o.evaluated_get(dep);m=ev.to_mesh();m.calc_loop_triangles();tri+=len(m.loop_triangles);zero+=sum(t.area<1e-11 for t in m.loop_triangles)
        pts.extend(o.matrix_world@v.co for v in m.vertices)
        if not o.data.materials or any(not s.material for s in o.material_slots):bad.append(o.name)
        ev.to_mesh_clear()
    result={'mesh_count':len(meshes),'evaluated_triangles':tri,'zero_area_triangles':zero,'nonmanifold_source_edges':nonman,'positive_component_volumes':all(v>0 for v in volumes),'finite':all(math.isfinite(c) for p in pts for c in p),'materials_resolved':not bad,'unit_mesh_scale':all(all(abs(s-1)<1e-6 for s in o.scale) for o in meshes),'bounds':{'min':[min(p[i] for p in pts) for i in range(3)],'max':[max(p[i] for p in pts) for i in range(3)]}}
    result['checks_passed']=bool(meshes) and zero==0 and nonman==0 and result['finite'] and result['materials_resolved'] and result['positive_component_volumes'] and result['unit_mesh_scale']
    return result

def sock(i,p,role='reactor-module',forward=(0,-1,0),up=(0,0,1)):
    return {'id':i,'position':list(p),'role':role,'forward':list(forward),'up':list(up),'compatibility':['MilitaryArmor.reactor.'+role]+(['MilitaryArmor.service-cartridge.v1'] if role=='accessory' else []),'restrictions':'full-pose alignment; unit scale only','parent':None}

def preview(pid,path,scale,view,target,res=550):
    a=Assembly.__new__(Assembly);a.bid=pid;a.review(path=path,view=view,target=target,scale=scale,resolution=res)

def ready(m,mounts,notes):
    check=inspect();assert check['checks_passed'],check
    m.save(mounts=mounts,notes=notes)
    folder=ROOT/'Parts'/m.pid
    data=json.loads((folder/'part.json').read_text(encoding='utf8'))
    data['attachment_areas']=[{'id':'root-plane','role':mounts[0]['role'],'shape':'logical-plane','dimensions':[.12,.12],'position':mounts[0]['position'],'forward':mounts[0]['forward'],'up':mounts[0]['up'],'parent':None,'allowed_rotations_degrees':[0],'allowed_scale':[1,1,1],'compatibility':mounts[0]['compatibility']}]
    for s in data['mounts']:
        s['node']='socket.'+s['id'];o=bpy.data.objects[s['node']];o.rotation_euler=Vector(s['forward']).to_track_quat('-Y','Z').to_euler();o['forward']=s['forward'];o['up']=s['up']
    write(folder/'part.json',data)
    bpy.ops.wm.save_as_mainfile(filepath=str(folder/(m.pid+'.blend')))
    check['checked_before_assembly']=True;write(folder/'validation.json',check)
    bound=check['bounds'];center=Vector([(bound['min'][i]+bound['max'][i])/2 for i in range(3)]);extent=max(bound['max'][i]-bound['min'][i] for i in range(3))
    path=folder/'Previews'/(m.pid+'.png');path.parent.mkdir(exist_ok=True)
    preview(m.pid,path,extent*1.8,tuple(center+Vector((4,-6,5))),tuple(center))
    print('PART_READY',m.pid,flush=True)

if __name__=='__main__':
    if '--assembly-only' not in sys.argv:
        m=Part('MA-R01-P01','Реактор — диагональное силовое основание')
        m.panel('Graphite lower interface',(0,0,.12),(3.58,3.58,.24),'Dark',.52,bevel=.025)
        m.panel('Octagonal load carrier',(0,0,.31),(3.45,3.45,.18),'Titanium',.60,bevel=.018)
        m.panel('Central foundation',(0,0,.45),(1.82,1.82,.20),'Armor',.42)
        for i in range(4):
            a=i*math.pi/2
            # Distinct diagonal corner folds, not decorative physical fasteners.
            o=m.slab('Swept corner structural shoulder',[(-1.63,-1.10),(-1.10,-1.63),(-.73,-1.63),(-1.35,-1.00),(-1.35,-.71),(-1.63,-.71)],.40,.19,'Ceramic',.014);o.rotation_euler.z=a
            o=m.box('Inset edge coupling',(0,-1.74,.28),(.61,.04,.105),'Dark',.01);o.rotation_euler.z=a;o.location=Vector((0,-1.74,.28));o.location.rotate(__import__('mathutils').Matrix.Rotation(a,4,'Z'))
        mounts=[sock('hull',(0,0,0),'hull'),sock('core',(0,0,.51),'core')]
        for i in range(4):
            a=i*math.pi/2;c=math.cos(a);s=math.sin(a)
            mounts.append(sock('screen'+str(i),(1.05*s,-1.05*c,.42),'screen',forward=(s,-c,0)))
            mounts.append(sock('thermal'+str(i),(1.20*s,-1.20*c,.37),'thermal',forward=(s,-c,0)))
        ready(m,mounts,'Four rotated modular sectors. Foundation is not a physical metre/cell conversion.')

        m=Part('MA-R01-P02','Реактор — герметичный центральный корпус')
        m.cyl('Sealed lower pressure vessel',(0,0,.45),.85,.9,'Titanium','Z',8)
        m.ring('Lower structural collar',(0,0,.10),.91,.78,.15,'Z','Dark',8)
        m.cyl('Upper shield drum',(0,0,.96),.76,.44,'Armor','Z',8)
        m.cyl('Ceramic crown',(0,0,1.225),.72,.12,'Ceramic','Z',8)
        m.cyl('Inset central service field',(0,0,1.292),.57,.028,'Dark','Z',8)
        for i in range(4):
            a=i*math.pi/2
            o=m.panel('Crown radial conductor',(0,-.49,1.311),(.24,.12,.020),'Titanium',.04,bevel=.003);o.rotation_euler.z=a;o.location.rotate(__import__('mathutils').Matrix.Rotation(a,4,'Z'))
            o=m.box('Crown diagnostic aperture',(0,-.50,1.325),(.12,.018,.007),'Signal',.002);o.rotation_euler.z=a;o.location.rotate(__import__('mathutils').Matrix.Rotation(a,4,'Z'))
            o=m.panel('Vertical shield segment',(0,-.78,.54),(.49,.15,.58),'Armor',.08);o.rotation_euler.z=a;o.location.rotate(__import__('mathutils').Matrix.Rotation(a,4,'Z'))
        ready(m,[sock('root',(0,0,0),'core'),sock('service',(0,0,1.308),'accessory')],'Static sealed vessel; small diagnostic emission only. No fuel feature or inferred gameplay functionality.')

        m=Part('MA-R01-P03','Реактор — стреловидный броневой экран')
        m.section('Graphite screened spine',[(-.64,0,.30,1.02,.30,.09),(-.13,0,.64,1.30,.68,.16),(.28,0,.83,.93,.57,.14)],'Dark',.018)
        m.section('Swept ceramic shield',[(-.62,0,.43,1.20,.24,.07),(-.11,0,.91,1.48,.24,.065),(.29,0,1.02,.98,.20,.06)],'Ceramic',.018)
        m.section('Inset armor center',[(-.48,0,.52,.46,.09,.025),(-.08,0,.93,.60,.09,.025),(.19,0,1.055,.40,.07,.02)],'Armor',.009)
        for side in [-1,1]:
            m.stripe('Diagonal load rib',(side*.50,-.54,.26),(side*.57,-.17,.78),.09,'Titanium')
        m.box('Recessed shield diagnostic field',(0,-.646,.34),(.48,.018,.065),'Titanium',.006)
        m.box('Shield diagnostic index',(0,-.659,.34),(.22,.009,.016),'Signal',.002)
        ready(m,[sock('root',(0,0,0),'screen')],'Four identical sectors; proper 90 degree rotations only. Broad planar ceramic skin, no ladders or vehicle grilles.')

        m=Part('MA-R01-P04','Реактор — закрытая термокассета')
        m.section('Sealed angular thermal manifold',[(-.48,0,.14,1.15,.22,.06),(-.28,0,.23,1.33,.30,.08),(.21,0,.17,1.12,.24,.07)],'Titanium',.012)
        for x in [-.43,-.14,.14,.43]:
            m.panel('Closed ceramic heat rejection tile',(x,-.24,.405),(.23,.43,.047),'Armor',.045,bevel=.005)
        m.panel('Rear thermal cover',(0,.08,.325),(.94,.20,.05),'Ceramic',.055,bevel=.007)
        ready(m,[sock('root',(0,0,0),'thermal')],'Closed panels, not open radiator vents; no emission, no moving elements.')


    if not (ROOT/'Parts/MA-R01-P05/MA-R01-P05.blend').exists():
        m=Part('MA-R01-P05','Реактор — сервисный картридж, исправленные фаски')
        with bpy.data.libraries.load(str(ROOT/'Parts/MA-P06/MA-P06.blend'),link=False) as (src,dst):dst.collections=['MA-P06']
        for original in dst.collections[0].objects:
            if original.type!='MESH':continue
            obj=original.copy();obj.data=original.data.copy();m.coll.objects.link(obj)
            for mod in obj.modifiers:
                if mod.type=='BEVEL':mod.width=min(mod.width,.001)
        ready(m,[sock('bottom',(0,0,0),'accessory')],'Explicit MA-P06 v1.3 variant: identical geometry/material layout, bevel widths capped at 0.001 BU to eliminate degenerate inset and lock triangles. Original part untouched.')
        data=json.loads((ROOT/'Parts/MA-R01-P05/part.json').read_text(encoding='utf8'));data['variant_of']={'id':'MA-P06','version':'1.3'};write(ROOT/'Parts/MA-R01-P05/part.json',data)

    a=Assembly(BID,'reactor-4x4-aaaa',[4,4],'Реактор')
    a.instance('Foundation','MA-R01-P01')
    a.instance('Core','MA-R01-P02',loc=(0,0,.51))
    for i in range(4):
        angle=i*math.pi/2;c=math.cos(angle);s=math.sin(angle)
        a.instance('Shield'+str(i),'MA-R01-P03',loc=(1.05*s,-1.05*c,.42),rot=(0,0,angle))
        a.instance('Thermal'+str(i),'MA-R01-P04',loc=(1.20*s,-1.20*c,.37),rot=(0,0,angle))
    a.instance('Service','MA-R01-P05',loc=(0,0,1.818))
    bpy.context.scene.frame_end=1;bpy.context.view_layer.update()
    folder=ROOT/'Blocks'/BID
    doc={'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'1.0','title':'Реактор','catalog_id':a.catalog_id,'catalog_grid':[4,4],'axes':AXES,'instances':a.instances,'nodes':[{'id':o.name,'parent':o.parent.name if o.parent else None,'translation':list(o.location),'rotation_euler_xyz':list(o.rotation_euler),'scale':list(o.scale)} for o in a.nodes],'animations':[],'exports':[],'notes':'Static Blender source, no gameplay contract. Catalog supplies no uranium consumption; no fuel mechanism invented. BU authoring only.'}
    doc['connections']=[{'parent':'Foundation','socket':'core','child':'Core','child_socket':'root'}]+[{'parent':'Foundation','socket':k+str(i),'child':v+str(i),'child_socket':'root'} for i in range(4) for k,v in [('screen','Shield'),('thermal','Thermal')]]+[{'parent':'Core','socket':'service','child':'Service','child_socket':'bottom'}]
    write(folder/'assembly.json',doc)
    bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')))
    result=inspect();assert result['checks_passed'],result
    write(folder/'validation-build.json',result)
    (folder/'Previews').mkdir(exist_ok=True)
    preview(BID,folder/'Previews'/(BID+'-perspective.png'),5.55,(6,-8,7),(0,0,.75),900)
    bpy.ops.wm.open_mainfile(filepath=str(folder/(BID+'.blend')))
    preview(BID,folder/'Previews'/(BID+'-top.png'),4.45,(0,0,9),(0,0,0),850)
    write(folder/'README.md','''# MA-R01 — реактор\n\nКаталог reactor-4x4-aaaa, сетка 4×4. Герметичный центральный корпус, четыре стреловидных экрана, четыре закрытые термокассеты на диагональном основании. Бирюзовая эмиссия только в диагностике.\n\nИсходник: MA-R01.blend. Предпросмотры: Previews/MA-R01-perspective.png и Previews/MA-R01-top.png. Состав и логические соединения — assembly.json; независимая проверка — validation.json.\n\nПять новых самостоятельных деталей MA-R01-P01…P05, включая явный вариант MA-P06 v1.3: тот же картридж с исправленными радиусами фасок. Прежняя деталь не изменялась. Всего 11 экземпляров. У каждой новой детали исходник, метаданные, предпросмотр и геометрическая проверка до включения в сборку.\n\nПроцедурные PBR Blender, файловых текстур/UV нет. Статичная конструкция без анимаций. Все экземпляры единичного масштаба; BU условные, +Z вверх, -Y вперёд. GLB не создавался. Исходник не устанавливался и не проверялся в игре, игровой контракт, LOD, коллайдеры и физический масштаб не задаются этой моделью.\n''')
    print('REACTOR_BUILT',flush=True)