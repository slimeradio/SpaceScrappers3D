"""MA-HS02 dual-bank thermal store; source-only authoring."""
import sys,json,bpy,bmesh
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,write,Assembly,AXES
from redesign_compute_production import Model,socket,finish,preview,inspect
BID='MA-HS02';folder=ROOT/'Blocks'/BID
write(folder/'composition-plan.md','''# MA-HS02 — накопитель тепла 2×2

Каталог heat-store-2x2: визуальная заготовка без игрового XML. Геометрия BU условная, +Z вверх, -Y вперёд. Не задаёт теплоёмкость и механику.

Изучены актуальные MA-HS01 v2.0 и MA-HS01-R2-P01/P02/P03, их исходные параметры и метаданные. Семейная индивидуальность: массивный сердечник с кольцами изоляции и глубокими промежутками, защищённый тепловой коллектор. Не использовать старые коробочные кассеты v1.

Повторно использовать MA-HS01-R2-P02 v2.0 без изменения, десять единичных экземпляров: две независимые продольные банки по пять колец. Это развитие объёма 2×2, не растяжение маленького блока. Кольцевые оболочки, разрыв между банками и общий задний коллектор отличают накопитель от батареи/топливного бака/реактора.

Создать MA-HS02-P01 v2.0 — двухканальное изолированное ложе с двумя сердечниками; старое ложе 1×1 не поддерживает две банки и длину пяти колец, unit-only запрещает растягивание. Создать MA-HS02-P02 v2.0 — центральный защищённый коллектор с обратной задней перемычкой, старый П-коллектор 1×1 не охватывает обе банки без недопустимого масштаба. Небольшие универсальные служебные крышки и бронеплечи не требуются.

Новые детали отдельно сохранить и проверить до сборки. Статика без эмиссии, без GLB. Старые детали не изменять.
''')
tag='MilitaryArmor.r2.thermal';ys=[-1.14,-.57,0,.57,1.14]
m=Model('MA-HS02-P01','Dual-bank insulated thermal bed with continuous protected cores')
for x in [-.91,.91]:
 m.panel('Independent thermal bed',(x,0,.22),(1.38,3.22,.32),'Titanium',.18)
 m.cyl('Continuous insulated core',(x,0,.83),.49,2.98,'Dark',axis='Y',verts=24)
 for dx in [-.63,.63]:
  m.section('Isolated longitudinal runner',[(-1.64,x+dx,.19,.22,.26,.05),(-1.4,x+dx,.18,.28,.30,.06),(1.4,x+dx,.18,.28,.30,.06),(1.64,x+dx,.19,.22,.26,.05)],'Armor')
 for y in [-1.48,1.48]:
  m.cyl('Inset insulated endcap',(x,y,.83),.44,.10,'Titanium',axis='Y',verts=24)
  m.ring('End insulation lip',(x,y,.83),.51,.41,.12,axis='Y',mat='Ceramic',verts=24)
mounts=[socket('hull',(0,0,0),tag+'.hull'),socket('collector',(0,0,0),tag+'.dual-collector')]
for bank,x in enumerate([-.91,.91]):
 for j,y in enumerate(ys):mounts.append(socket(f'bank-{bank}-section-{j}',(x,y,.21),tag+'.section'))
finish(m,mounts)
m=Model('MA-HS02-P02','Central protected collector joining two insulated thermal banks')
m.panel('Central return spine',(0,0,.49),(.15,3.0,.28),'Steel',.045)
m.panel('Recessed collector protective ridge',(0,0,.67),(.22,2.76,.12),'Armor',.045)
for y in ys:
 for x in [-.10,.10]:
  m.cyl('Protected thermal branch',(x,y,.49),.075,.20,'Titanium',axis='X',verts=16)
m.panel('Rear return bridge',(0,1.67,.51),(3.37,.23,.26),'Titanium',.08)
for x in [-.91,.91]:
 m.panel('Insulated rear collector shoe',(x,1.62,.54),(.46,.38,.35),'Armor',.075)
 m.cyl('Core return neck',(x,1.5,.70),.12,.22,'Steel',axis='Y',verts=16)
finish(m,[socket('root',(0,0,0),tag+'.dual-collector')])
a=Assembly(BID,'heat-store-2x2',[2,2],'Накопитель тепла 2×2 — визуальная заготовка')
a.instance('DualThermalBed','MA-HS02-P01');con=[]
for bank,x in enumerate([-.91,.91]):
 for j,y in enumerate(ys):
  iid=f'ThermalRing-B{bank}-{j}';a.instance(iid,'MA-HS01-R2-P02',loc=(x,y,.21));con.append({'parent_instance':'DualThermalBed','parent_socket':f'bank-{bank}-section-{j}','child_instance':iid,'child_socket':'root'})
a.instance('DualCollector','MA-HS02-P02');con.append({'parent_instance':'DualThermalBed','parent_socket':'collector','child_instance':'DualCollector','child_socket':'root'})
meta={'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'2.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'catalog_status':'visual-only; no game XML','axes':AXES,'instances':a.instances,'connections':con,'animations':[],'exports':[],'notes':'Two thermal banks, ten unchanged v2 insulation rings. New bed and collector. No gameplay parameters, emission or physical metric scale.'}
write(folder/'assembly.json',meta);bpy.context.scene.frame_end=1;bpy.context.view_layer.update();inspect();bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')));preview(folder,(0,.04,.83),5.45,800,True)
write(folder/'README.md','''# MA-HS02 — накопитель тепла 2×2

Две продольные тепловые банки с глубокими пазами между массивными кольцами изоляции, отдельными сердечниками и единым задним возвратным коллектором. Родство с MA-HS01 v2 сохранено; геометрия кольца используется без масштабирования.

Исходник MA-HS02.blend, состав assembly.json, решение по повторному использованию composition-plan.md. Новые MA-HS02-P01/P02 v2.0, повторно MA-HS01-R2-P02 v2.0 (10 экземпляров). Всего 12 экземпляров/3 исходных детали. Каждый новый исходник проходит немедленный gate до сборки; проверка validation.json повторно открывает детали и сборку.

Предпросмотры Previews/top.png, perspective.png, top-grayscale.png. Процедурные PBR материалы, без файловых текстур, эмиссии и анимации. Габариты BU условные. Каталог visual-only без XML; теплоёмкость и рабочие температуры не определяются. GLB не создавался, игровой установки и проверки нет. Коллайдеры/LOD не входят в модель. Пересечения в стыках оболочек, ложа и тепловых подключений конструктивно намеренны.
''')
print('BUILT MA-HS02',flush=True)
