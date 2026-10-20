import sys,bpy,json,math,shutil,os
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import Part,Assembly,ROOT,write,AXES
from redesign_compute_production import inspect,preview
B=ROOT/'Blocks'/'MA-S01'; ARCH=ROOT/'Versions'/'Auction-v2-rejected'/'Blocks'/'MA-S01'
class Model(Part):
 def __init__(self,pid,title):super().__init__(pid,title,'3.0')
 def finish(self,o,name,mat,bevel=0):return super().finish(o,name,mat,0)
def socket(i,p,tag,angle=0):return {'id':i,'role':tag.split('.')[-1],'parent':'part','position':list(p),'forward':[math.sin(angle),-math.cos(angle),0],'up':[0,0,1],'compatibility':[tag],'allowed_scale':[1,1,1]}
def finish(m,mounts):
 check=inspect();m.save(mounts=mounts,notes='Static closed protected trading infrastructure; v3.0. Blender authoring only. No textures/UV dependency; no animation. Unit scale only; physical BU unspecified. No GLB.')
 p=ROOT/'Parts'/m.pid;meta=json.loads((p/'part.json').read_text());meta['attachment_areas']=[{'id':s['id']+'-seat','role':s['role'],'parent':'part','shape':'logical-point-plane','dimensions':[.1,.1],'position':s['position'],'forward':s['forward'],'up':s['up'],'compatibility':s['compatibility'],'allowed_scale':[1,1,1],'allowed_rotations_degrees':[0]} for s in mounts];write(p/'part.json',meta);write(p/'geometry-validation.json',check)
 lo=meta['bounds_local']['min'];hi=meta['bounds_local']['max'];preview(p,[(a+b)/2 for a,b in zip(lo,hi)],max(b-a for a,b in zip(lo,hi))*1.6,420)
 write(p/'README.md',f'# {m.pid} v3.0\n\n{m.title}. Standalone editable Blender geometry. geometry-validation.json passed before assembly. Procedural PBR materials, full sockets and attachment areas: part.json. Static; no file textures or UV dependencies. Unit scale. BU unspecified. Previews top/perspective. No GLB.\n')
def plan():
 if not ARCH.exists():
  shutil.copytree(B,ARCH);am=json.loads((ARCH/'assembly.json').read_text())
  for i in am['instances']:i['source']=os.path.relpath(ROOT/'Parts'/i['part_id']/(i['part_id']+'.blend'),ARCH).replace('\\','/')
  write(ARCH/'assembly.json',am);write(ARCH/'archive-note.md','Rejected v2.0 saved before changes; Blender source copied unchanged. Part paths in assembly.json adjusted for archive location. Parts remain unchanged. Historical validations preserved.\n')
 write(B/'composition-plan.md','''# MA-S01 — аукцион базы, v3.0

Торговая инфраструктура 1×1 по auction-base; авторская геометрия не задаёт новые игровые условия рынка. Низкий трёхлучевой узел с тремя защищёнными интерфейсными гнёздами, направленными к центральному узкому коммутационному сердечнику. Сзади слева массивная сервисная спина. Нет большого монитора, огромной крышки, кассетного поля или наружных антенн. Небольшие утопленные диагностические индексы вторичны по отношению к конструкции.

Проверка reuse до моделирования: MA-S01-P01 v1.0 — единый фронтальный интерфейс 0.99×0.75 BU, не подходит для трёх радиальных малых гнёзд; MA-S01-P02 v1.0 — длинное бронеплечо, не интерфейс; MA-N01-P01 v1.0 — квадратное основание связи 1.74×1.65 BU, не подходит разомкнутому трёхлучевому силуэту. R2-P01/P02 — отвергнутые стойка и огромный дисплей, не использовать. Материалы/параметрические инструменты своего стиля повторно используются. Общие детали не меняются.

| Узел | Решение |
|---|---|
| Низкая трёхлучевая коммутационная рама | Новая MA-S01-R3-P01, v3.0 |
| Узкий центральный защищённый коммутатор | Новая MA-S01-R3-P02, v3.0 |
| Защищённое интерфейсное гнездо | Новая MA-S01-R3-P03 v3.0, три экземпляра |
| Асимметричная сервисная спина | Новая MA-S01-R3-P04 v3.0 |

Все детали сохраняются и проходят немедленный source/evaluated geometry gate до сборки. +Z вверх, -Y вперёд, BU условные, единичный масштаб; повороты экземпляров совмещают полные позы sockets. GLB не создавать. Архив v2: ../../Versions/Auction-v2-rejected/Blocks/MA-S01/.
''')
def parts():
 tag='MilitaryArmor.r3.auction'
 m=Model('MA-S01-R3-P01','Three-arm protected trade routing frame')
 m.slab('Triangular central chassis',[(-.62,-.43),(.62,-.43),(.76,-.16),(.35,.68),(-.35,.68),(-.76,-.16)],.04,.17,'Titanium')
 m.panel('Front inward routing keel',(0,-.50,.18),(.44,.72,.24),'Armor',.10)
 for x in [-.56,.56]:m.panel('Angled interface seat',(x,-.18,.19),(.55,.67,.24),'Armor',.10)
 m.panel('Rear interface seat',(0,.58,.19),(.60,.55,.24),'Armor',.09)
 m.panel('Service spine root',(-.62,.49,.16),(.42,.58,.20),'Titanium',.09)
 mounts=[socket('hull',(0,0,0),tag+'.hull'),socket('core',(0,-.18,.28),tag+'.core'),socket('left',(-.58,-.19,.29),tag+'.interface',math.pi/2),socket('right',(.58,-.19,.29),tag+'.interface',-math.pi/2),socket('rear',(0,.58,.29),tag+'.interface'),socket('service',(-.63,.48,.25),tag+'.service')];finish(m,mounts)
 m=Model('MA-S01-R3-P02','Longitudinal protected transaction-routing chamber')
 m.section('Narrow sealed central chamber',[(-.58,0,.12,.23,.21,.04),(-.39,0,.22,.43,.42,.07),(.15,0,.24,.43,.46,.07),(.34,0,.19,.28,.36,.06)],'Ceramic')
 m.section('Titanium center seam',[(-.38,0,.45,.13,.04,.015),(.14,0,.49,.13,.04,.015),(.25,0,.42,.10,.04,.015)],'Titanium')
 m.box('Inset diagnostic lip',(0,-.415,.285),(.26,.025,.07),'Dark')
 m.box('Diagnostic link index',(0,-.430,.287),(.10,.012,.019),'Optic')
 for x in [-.22,.22]:m.box('Closed routed neck',(x,-.05,.13),(.16,.20,.16),'Steel')
 finish(m,[socket('root',(0,0,0),tag+'.core')])
 m=Model('MA-S01-R3-P03','Inward facing protected infrastructure interface throat')
 m.section('Sloping port shield',[(-.23,0,.15,.44,.28,.06),(-.06,0,.24,.46,.44,.06),(.20,0,.22,.42,.40,.06)],'Ceramic')
 # A small dark inset on the inward sloping nose; no screen.
 m.box('Inset contact recess',(0,-.242,.15),(.30,.025,.16),'Dark')
 for x in [-.09,.09]:m.box('Protected data contacts',(x,-.259,.155),(.055,.018,.09),'Steel')
 m.box('Port diagnostic index',(0,-.270,.205),(.06,.010,.015),'Optic')
 m.panel('Upper protected interface cap',(0,.05,.455),(.32,.28,.035),'Armor',.055)
 m.box('Cap inset spine',(0,.06,.478),(.09,.19,.015),'Titanium')
 finish(m,[socket('root',(0,0,0),tag+'.interface')])
 m=Model('MA-S01-R3-P04','Offset enclosed service collector spine')
 m.section('Service collector rising shell',[(-.24,0,.19,.32,.37,.06),(.12,0,.32,.37,.62,.06),(.28,0,.32,.30,.62,.06)],'Armor')
 m.panel('Closed service crown',(0,.13,.66),(.31,.29,.10),'Ceramic',.06)
 m.box('Recessed service backbone',(0,.14,.719),(.10,.18,.018),'Titanium')
 m.box('Protected cross-routing neck',(.17,-.06,.15),(.25,.16,.18),'Steel')
 finish(m,[socket('root',(0,0,0),tag+'.service')])
def assembly():
 a=Assembly('MA-S01','auction-base',[1,1],'Блок аукциона базы');con=[]
 a.instance('TradeRoutingFrame','MA-S01-R3-P01')
 for iid,pid,loc,angle,sid in [('TransactionCore','MA-S01-R3-P02',(0,-.18,.28),0,'core'),('PortLeft','MA-S01-R3-P03',(-.58,-.19,.29),math.pi/2,'left'),('PortRight','MA-S01-R3-P03',(.58,-.19,.29),-math.pi/2,'right'),('PortRear','MA-S01-R3-P03',(0,.58,.29),0,'rear'),('ServiceCollector','MA-S01-R3-P04',(-.63,.48,.25),0,'service')]:
  a.instance(iid,pid,loc=loc,rot=(0,0,angle));con.append({'parent_instance':'TradeRoutingFrame','parent_socket':sid,'child_instance':iid,'child_socket':'root'})
 meta={'schema':'MilitaryArmor.BlenderAuthoring/1','id':'MA-S01','version':'3.0','title':a.title,'catalog_id':'auction-base','catalog_grid':[1,1],'axes':AXES,'instances':a.instances,'connections':con,'animations':[],'exports':[],'notes':'Protected low trading-infrastructure routing hub, inward interface throats and offset service collector. Authoring interpretation only; no market rules or functionality invented.'}
 write(B/'assembly.json',meta);bpy.context.scene.frame_end=1;bpy.ops.wm.save_as_mainfile(filepath=str(B/'MA-S01.blend'));preview(B,(0,0,.40),2.85,850,True)
 write(B/'README.md','# MA-S01 — аукцион базы, v3.0\n\nНизкий трёхлучевой коммуникационный узел торговой инфраструктуры. Три защищённых интерфейсных гнезда направлены к узкой центральной камере; асимметричная сервисная спина и утопленные малые индексы. Большой экран исключён. Назначение и ограничения: auction-base, 1×1; модель не меняет игровые условия рынка.\n\nРедактируемый исходник MA-S01.blend, состав assembly.json, выбор деталей composition-plan.md. Четыре новые самостоятельные детали MA-S01-R3-P01…P04 v3.0, шесть экземпляров. Геометрические gates до сборки; независимая повторная проверка в validation.json. Top/perspective/top-grayscale в Previews. Все sockets совмещены по позиции и ориентации, unit scale. Материалы процедурные PBR, без файловых текстур, анимаций и UV-зависимости. BU условные. GLB не создавались.\n\nОтвергнутая v2 сохранена в ../../Versions/Auction-v2-rejected/Blocks/MA-S01/; v1 в ../../Versions/FunctionalIdentity-before/Blocks/MA-S01/. Старые Parts не изменены. Игровая интеграция/LOD/коллайдеры не выполнялись.\n')
if __name__=='__main__':
 if '--assembly-only' not in sys.argv:plan();parts()
 assembly()
