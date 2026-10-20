"""Battery authoring: new source parts validated before assembly; no GLB."""
import sys, json, math, bmesh
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import Part, Assembly, ROOT, AXES, write
import bpy
from mathutils import Vector
BID='MA-B01'
FOLDER=ROOT/'Blocks'/BID

def socket(i,p,role='battery-interface',rot=0):
    return {'id':i,'role':role,'position':list(p),'forward':[math.sin(rot),-math.cos(rot),0],'up':[0,0,1],'compatibility':(['MilitaryArmor.battery.'+role,'MilitaryArmor.service-cartridge.v1'] if role=='accessory' else ['MilitaryArmor.battery.'+role]),'restrictions':'unit scale; full pose alignment'}

def inspect():
    dep=bpy.context.evaluated_depsgraph_get();meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];tri=zero=nonmanifold=inward=0;pts=[]
    for o in meshes:
        ev=o.evaluated_get(dep);me=ev.to_mesh();me.calc_loop_triangles();tri+=len(me.loop_triangles);zero+=sum(t.area<1e-10 for t in me.loop_triangles)
        bad=sum(t.area<1e-10 for t in me.loop_triangles)
        if bad: print('DEGENERATE',o.name,bad,flush=True)
        bm=bmesh.new();bm.from_mesh(me);nonmanifold+=sum(not e.is_manifold for e in bm.edges);inward+=int(bm.calc_volume(signed=True)<0);bm.free();pts.extend(o.matrix_world@v.co for v in me.vertices);ev.to_mesh_clear()
    data={'mesh_count':len(meshes),'evaluated_triangles':tri,'zero_area_triangles':zero,'nonmanifold_edges':nonmanifold,'inward_components':inward,'finite':all(math.isfinite(c) for p in pts for c in p),'materials_resolved':all(o.data.materials and all(s.material for s in o.material_slots) for o in meshes),'bounds':{'min':[min(p[i] for p in pts) for i in range(3)],'max':[max(p[i] for p in pts) for i in range(3)]}}
    assert meshes and zero==0 and nonmanifold==0 and inward==0 and data['finite'] and data['materials_resolved'],data
    return data

def review(path,target,scale,res=512,view=None):
    r=Assembly.__new__(Assembly);r.bid=BID
    r.review(path=path,view=view or (5,-7,6),target=target,scale=scale,resolution=res)

def finish(m,mounts,notes):
    # Geometry gate immediately after the individual part, before assembly.
    check=inspect();check['validated_before_assembly']=True
    m.save(mounts=mounts,notes=notes)
    p=ROOT/'Parts'/m.pid
    d=json.loads((p/'part.json').read_text(encoding='utf8'))
    d['attachment_areas']=[{'id':'root-plane','shape':'logical-point-plane','position':mounts[0]['position'],'forward':mounts[0]['forward'],'up':[0,0,1],'allowed_rotations_degrees':[0],'restrictions':'unit scale only; no visible mounting geometry implied'}]
    if m.pid=='MA-B01-P01': d['attachment_areas'].append({'id':'service-cartridge-seat','shape':'logical-plane','dimensions':[.74,.60],'position':[0,0,.84],'forward':[0,-1,0],'up':[0,0,1],'allowed_rotations_degrees':[0],'compatibility':['MilitaryArmor.service-cartridge.v1'],'restrictions':'unit scale only; matches service bottom socket'})
    write(p/'part.json',d);write(p/'validation.json',check)
    z=(check['bounds']['min'][2]+check['bounds']['max'][2])/2
    extent=max(check['bounds']['max'][i]-check['bounds']['min'][i] for i in range(3))
    review(p/'Previews'/(m.pid+'.png'),(0,0,z),extent*1.55,384)

plan='''# MA-B01 — батарея 4×4

Каталог battery-4x4: накопление и отдача энергии; размер в клетках 4×4. Числа XML не переинтерпретируются в геометрии. Единицы BU условные, физический масштаб не согласован.

План состава, сохранён до моделирования:

| Деталь | Проверенный источник | Решение | Причина |
|---|---|---|---|
| Несущая кассета 4×4 | MA-W01-P01 / MA-P01 | Новая MA-B01-P01 v1.0 | Оружейные основания и азимутальные кольца не подходят плоскому энергоблоку |
| Закрытый энергомодуль | MA-E01-P02, оружейные камеры | Новая MA-B01-P02 v1.0; 4 экземпляра | Камеры двигателей имеют сопловой интерфейс; батарее нужен закрытый модуль |
| Стреловидный защитный борт | MA-E01-P04 | Новая MA-B01-P03 v1.0; 2 экземпляра | Двигательная термопанель мала и ориентирована иначе; не масштабировать общий исходник |
| Утопленная торцевая шина | существующие Parts | Новая MA-B01-P04 v1.0; 2 экземпляра | Подходящего широкого закрытого интерфейса нет |
| Сервисный картридж | MA-P06 v1.3 | Повторное использование MA-R01-P05 v1.0; 1 экземпляр | MA-P06 v1.3 имеет 176 вырожденных треугольников; общий исправленный вариант MA-R01-P05 сохраняет габариты 0.74×0.60, нижний socket и единичный масштаб |

Все исходники деталей проверяются до сборки. Полные ориентации sockets, единичный масштаб. Правая система +Z вверх / -Y вперёд. Неподвижная конструкция, без выдуманных анимаций. Холодные светлые оболочки, графитовый каркас, ограниченная бирюзовая диагностика. Только Blender и PNG, GLB не создаётся.
'''
write(FOLDER/'composition-plan.md',plan)

if '--resume-bus' not in sys.argv and '--assembly-only' not in sys.argv:
    m=Part('MA-B01-P01','Battery — recessed structural cassette')
    m.panel('Graphite hull interface',(0,0,.10),(3.90,3.90,.20),'Dark',.40,.012)
    m.panel('Titanium load deck',(0,0,.26),(3.73,3.73,.12),'Titanium',.40,.012)
    # Central structural web separates the four cells; no exposed pipes or vehicle grille.
    m.panel('Longitudinal enclosed power spine',(0,0,.58),(.25,3.18,.52),'Armor',.08,.012)
    m.panel('Central service bridge',(0,0,.74),(1.06,.70,.20),'Armor',.16,.012)
    mounts=[socket('hull',[0,0,0],'hull')]
    for i,(x,y) in enumerate([(-.81,-.82),(.81,-.82),(-.81,.82),(.81,.82)]):mounts.append(socket('cell'+str(i),[x,y,.32],'cell'))
    mounts += [socket('sideR',[1.67,0,.32],'shoulder'),socket('sideL',[-1.67,0,.32],'shoulder',math.pi),socket('busF',[0,-1.65,.32],'bus'),socket('busB',[0,1.65,.32],'bus',math.pi),socket('service',[0,0,.84],'accessory')]
    finish(m,mounts,'Closed authoring cassette; sockets are logical interfaces. No new energy mechanics.')
    
    m=Part('MA-B01-P02','Battery — sealed storage module')
    m.panel('Energy module pressure body',(0,0,.30),(1.28,1.36,.60),'Titanium',.18,.018)
    m.section('Swept cold ceramic lid',[(-.66,0,.48,.91,.20,.05),(-.44,0,.65,1.25,.27,.07),(.38,0,.69,1.25,.24,.07),(.66,0,.48,.93,.17,.05)],'Ceramic',.012)
    m.panel('Dorsal graphite inset',(0,.015,.822),(.30,.77,.028),'Dark',.08,.004)
    m.panel('Flush diagnostic aperture',(0,-.16,.843),(.14,.24,.012),'Signal',.04,.002)
    for x in [-.645,.645]:
        m.box('Recessed cell connector',(x,.08,.30),(.018,.42,.17),'Dark',.007)
        m.box('Closed connector bridge',(x,.08,.31),(.026,.12,.10),'Armor',.005)
    finish(m,[socket('root',[0,0,0],'cell')],'Hermetically enclosed repeated storage cell. No fluid, heat or capacity gameplay contract. Emissive patch is static diagnostics.')
    
    m=Part('MA-B01-P03','Battery — swept armored shoulder')
    m.section('Graphite diagonal shoulder spine',[(-1.66,0,.13,.26,.22,.06),(-1.18,0,.27,.42,.46,.10),(.98,0,.31,.42,.53,.11),(1.65,0,.13,.25,.23,.05)],'Armor',.012)
    m.section('Swept ceramic shoulder blade',[(-1.60,0,.25,.20,.10,.025),(-1.09,0,.55,.36,.15,.035),(.94,0,.61,.36,.16,.04),(1.58,0,.26,.22,.11,.025)],'Ceramic',.008)
    m.box('Recessed lateral diagnostic',( .219,.15,.32),(.012,.64,.07),'Dark',.004)
    m.box('Diagnostic index',( .229,.15,.32),(.009,.29,.018),'Signal',.002)
    finish(m,[socket('root',[0,0,0],'shoulder')],'Left instance uses proper 180-degree Z rotation. No mirror or nonuniform scale. No automotive grille or handrail.')
    
    
if '--assembly-only' not in sys.argv:
    m=Part('MA-B01-P04','Battery — enclosed power bus')
    m.panel('Closed transverse manifold',(0,0,.22),(3.03,.36,.44),'Armor',.10,.012)
    m.panel('Cold ceramic manifold bridge',(0,0,.48),(2.84,.29,.08),'Ceramic',.07,.008)
    m.box('Protected connector well',(0,-.187,.25),(1.12,.02,.20),'Dark',.003)
    for x in [-.31,.31]:
        m.panel('Recessed terminal cover',(x,-.202,.25),(.32,.035,.12),'Titanium',.003,0)
        m.box('Terminal diagnostic index',(x,-.224,.25),(.10,.008,.018),'Signal',.002)
    finish(m,[socket('root',[0,0,0],'bus')],'Sealed paired terminals; no exposed cabling. Visual authoring interfaces only.')
    
    
# Existing MA-P06 source is loaded without modifying or rebuilding it.
a=Assembly(BID,'battery-4x4',[4,4],'Батарея 4×4')
a.instance('Cassette','MA-B01-P01')
for i,(x,y) in enumerate([(-.81,-.82),(.81,-.82),(-.81,.82),(.81,.82)]):a.instance('Cell'+str(i),'MA-B01-P02',loc=(x,y,.32))
a.instance('ShoulderR','MA-B01-P03',loc=(1.67,0,.32));a.instance('ShoulderL','MA-B01-P03',loc=(-1.67,0,.32),rot=(0,0,math.pi))
a.instance('BusF','MA-B01-P04',loc=(0,-1.65,.32));a.instance('BusB','MA-B01-P04',loc=(0,1.65,.32),rot=(0,0,math.pi))
a.instance('Service','MA-R01-P05',loc=(0,0,.84))
bpy.context.scene.frame_end=1;bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
assembly={'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'1.0','title':'Батарея 4×4','catalog_id':'battery-4x4','catalog_grid':[4,4],'axes':AXES,'instances':a.instances,'animations':[],'exports':[],'connections':[{'parent':'Cassette','socket':('cell'+str(i)),'child':'Cell'+str(i),'child_socket':'root'} for i in range(4)]+[{'parent':'Cassette','socket':s,'child':c,'child_socket':cs} for s,c,cs in [('sideR','ShoulderR','root'),('sideL','ShoulderL','root'),('busF','BusF','root'),('busB','BusB','root'),('service','Service','bottom')]],'notes':'Editable source, static authoring asset. Catalog cells are not metres. No GLB, no game installation.'}
write(FOLDER/'assembly.json',assembly)
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/(BID+'.blend')))
review(FOLDER/'Previews'/'perspective.png',(0,0,.55),5.7,900,view=(6,-8,7))
bpy.ops.wm.open_mainfile(filepath=str(FOLDER/(BID+'.blend')))
review(FOLDER/'Previews'/'top.png',(0,0,0),4.55,800,view=(0,0,8))
write(FOLDER/'README.md',plan+'\nИсходник: MA-B01.blend. Состав: assembly.json. Превью: Previews/perspective.png и Previews/top.png. Четыре новые самостоятельные детали, один общий исправленный вариант MA-R01-P05 v1.0; 10 экземпляров. Материалы процедурные PBR, без файловых текстур и UV; эмиссия только диагностика. Проверка отдельных исходников и готовой сборки: validation.json. Игровая интеграция, физический масштаб, LOD и коллайдер не входят в эту задачу.\n')
print('MA_B01_BUILT',flush=True)