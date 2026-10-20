"""MA-H03 staggered triple-bank radiator. Source only."""
import sys,json,bpy,bmesh
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,write,Assembly,AXES
from redesign_compute_production import Model,socket,finish,preview,inspect
BID='MA-H03';folder=ROOT/'Blocks'/BID
tag='MilitaryArmor.r2.radiator'
banks=[]
for b,x in enumerate([-2.0,0,2.0]):
 count=8 if b==1 else 7;step=3.15 if b==1 else 2.8
 ys=[round(c+(j-(count-1)/2)*.34,6) for c in [-step,0,step] for j in range(count)]
 banks.append((x,ys))
write(folder/'composition-plan.md','''# MA-H03 — радиатор 3×5

Каталог radiator-3x5 — визуальная заготовка без игрового XML. BU условные; +Z вверх, -Y вперёд. Метры, температуры, теплоотвод, пар, эмиссия и анимация не задаются.

Изучены MA-H01 v2.0, MA-H02 и их part.json. Рабочий образ семейства — открытые глубокие поперечные лопасти с поднятыми рёбрами, узкие коллекторы и сквозные зазоры. MA-H01-R2-P02 v2.0 подходит без изменений: 66 экземпляров единичного масштаба. Три отдельные продольные банки, каждая разделена на три группы. Средняя банка длиннее; наружные торцы ступенчатые. Между банками и группами остаются сквозные щели. Это не сплошное поле солнечной панели и не батарейные кассеты.

MA-H02-P01 unit-only рассчитан на две короткие банки; растяжение запрещено, поэтому создаётся только новая MA-H03-P01 v2.0 — трёхканальный открытый коллектор. Узкие продольные силовые магистрали, локальные торцевые башмаки и две заглублённые поперечные связи; замкнутой наружной рамы и поддона нет. Ширина 5.8 BU, длина 9.32 BU — композиция сетки 3×5 без приравнивания клетки к метру. Готовые лопасти повторяются без пересборки. Новая деталь проверяется немедленно до сборки. Контакты связей с магистралями заглублены, наружные поверхности не копланарны. Только Blender, GLB не создавать.
''')
m=Model('MA-H03-P01','Triple open narrow collector with stepped terminal shoes')
for b,(x,ys) in enumerate(banks):
 length=9.0 if b==1 else 8.0
 m.panel('Longitudinal collector keel',(x,0,.16),(.32,length,.32),'Titanium',.09)
 m.panel('Protected upper manifold',(x,0,.39),(.23,length-.12,.14),'Ceramic',.065)
 for side in [-1,1]:
  y=side*(length/2+.04)
  m.panel('Individual terminal shoe',(x,y,.23),(.49,.24,.34),'Armor',.07)
  m.panel('Terminal inset',(x,y,.412),(.25,.13,.024),'Steel',.03)
for y in [-1.50,1.50]:
 m.panel('Recessed transverse return',(0,y,.13),(4.16,.20,.13),'Titanium',.055)
 for x in [-1.0,1.0]:m.panel('Local return shield',(x,y,.225),(.55,.29,.12),'Armor',.055)
mounts=[socket('hull',(0,0,0),tag+'.hull')]
for b,(x,ys) in enumerate(banks):
 for j,y in enumerate(ys):mounts.append(socket(f'bank-{b}-fin-{j}',(x,y,.27),tag+'.fin'))
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_contiguous for e in bm.edges),o.name;bm.free()
finish(m,mounts)
p=ROOT/'Parts'/m.pid;gate=json.loads((p/'geometry-validation.json').read_text());gate['source_normals_consistent']=True;write(p/'geometry-validation.json',gate)
a=Assembly(BID,'radiator-3x5',[3,5],'Радиатор 3×5 — визуальная заготовка')
a.instance('TripleCollector','MA-H03-P01');con=[]
for b,(x,ys) in enumerate(banks):
 for j,y in enumerate(ys):
  iid=f'RadiatingBlade-B{b}-{j}';a.instance(iid,'MA-H01-R2-P02',loc=(x,y,.27));con.append({'parent_instance':'TripleCollector','parent_socket':f'bank-{b}-fin-{j}','child_instance':iid,'child_socket':'root'})
meta={'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'2.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'catalog_status':'visual-only; no game XML','axes':AXES,'instances':a.instances,'connections':con,'animations':[],'exports':[],'notes':'Staggered triple open comb. 66 unchanged deep radiator blades in nine separated groups; narrow collector spines and recessed returns. No emission, animation, thermal figures or physical metric scale.'}
write(folder/'assembly.json',meta);bpy.context.scene.frame_end=1;bpy.context.view_layer.update();inspect();bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')));preview(folder,(0,0,.32),11.7,900,True)
write(folder/'README.md','''# MA-H03 — радиатор 3×5

Три открытые гребёнки глубоких лопастей. Средняя банка длиннее внешних, каждая разбита на три группы со сквозными разрывами; ступенчатые торцы и зубчатый контур. Узкие продольные коллекторы соединены двумя заглублёнными перемычками. Общей наружной рамы, плоского поддона и сплошного поля нет.

Исходник MA-H03.blend; состав assembly.json; план до моделирования composition-plan.md. Новая MA-H03-P01 v2.0 — трёхканальный коллектор; повторно MA-H01-R2-P02 v2.0, 66 лопастей без изменения источника или масштаба. Всего 67 экземпляров, два ID деталей. Новая деталь прошла немедленную проверку геометрии до сборки. validation.json — независимое открытие двух источников и сборки, геометрия и полные позы креплений.

Предпросмотры: Previews/top.png, perspective.png, top-grayscale.png. Статические редактируемые объекты с процедурными PBR. Нет файловых текстур, UV-зависимости, эмиссии или анимации. BU условные. Визуальная заготовка без игрового XML; теплоотвод и температуры не задавались. GLB не создавался. Игровая интеграция, коллайдеры и LOD не выполнялись. Контакты лопастей с коллекторами и заглублённых связей с магистралями намеренны; наружные поверхности связей и магистралей разнесены по высоте.
''')
print('BUILT MA-H03',flush=True)