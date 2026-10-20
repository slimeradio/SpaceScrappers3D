"""MA-H02 open dual-comb radiator. Source-only Blender authoring."""
import sys,json,bpy,bmesh
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,write,Assembly,AXES
from redesign_compute_production import Model,socket,finish,preview,inspect
BID='MA-H02';folder=ROOT/'Blocks'/BID
write(folder/'composition-plan.md','''# MA-H02 — радиатор 2×3

Каталог radiator-2x3: визуальная заготовка без игрового XML; условные BU, +Z вверх, -Y вперёд. Физический масштаб, теплоотвод и рабочие температуры не заданы.

Изучены действующие MA-H01 v2.0 и детали MA-H01-R2-P01/P02: открытая гребёнка глубоких лопастей, не прежняя плиточная коробка. MA-H01-R2-P02 v2.0 подходит форме и интерфейсу: повторить 30 раз без изменения и растяжения. Две продольные банки по 15 поперечных лопастей, раздельные коллекторы, открытая центральная щель. Сверху зубчатый разреженный силуэт; нет единого тонкого поля, универсального поддона и батарейных кассет.

MA-H01-R2-P01 рассчитан на одну короткую гребёнку, unit-only запрещает растяжение. Создать новую MA-H02-P01 v2.0: два узких несущих коллектора и торцевые возвраты. Новая деталь проходит самостоятельный geometry gate с consistent normals до сборки, затем отдельные превью. Плоская широкая рама не нужна. Пересечения глубинных соединений намеренны; верхние крышки коллекторов толще возвратов, копланарных наружных поверхностей не создавать. Эмиссии, анимаций и GLB нет.
''')
xs=[-.98,.98];ys=[round(-2.38+j*.34,6) for j in range(15)];tag='MilitaryArmor.r2.radiator'
m=Model('MA-H02-P01','Dual narrow radiator collectors with recessed end return bridges')
for x in xs:
 m.panel('Collector keel',(x,0,.16),(.33,5.20,.32),'Titanium',.10)
 m.panel('Upper closed manifold',(x,0,.37),(.23,5.08,.16),'Ceramic',.07)
 for y in [-2.61,2.61]:
  m.panel('Protected terminal shoe',(x,y,.24),(.46,.34,.34),'Armor',.10)
for y in [-2.61,2.61]:
 m.panel('Recessed return bridge',(0,y,.20),(2.04,.19,.20),'Titanium',.06)
 m.panel('Return bridge shield',(0,y,.325),(1.35,.26,.13),'Armor',.065)
mounts=[socket('hull',(0,0,0),tag+'.hull')]
for bank,x in enumerate(xs):
 for j,y in enumerate(ys):mounts.append(socket(f'bank-{bank}-fin-{j}',(x,y,.27),tag+'.fin'))
# Immediate source normal consistency gate; finish also checks source/evaluated geometry.
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_contiguous for e in bm.edges),o.name;bm.free()
finish(m,mounts)
# Record the additional immediate normal check in the source gate.
p=ROOT/'Parts'/m.pid;gate=json.loads((p/'geometry-validation.json').read_text());gate['source_normals_consistent']=True;write(p/'geometry-validation.json',gate)
a=Assembly(BID,'radiator-2x3',[2,3],'Радиатор 2×3 — визуальная заготовка')
a.instance('DualCollector','MA-H02-P01');con=[]
for bank,x in enumerate(xs):
 for j,y in enumerate(ys):
  iid=f'RadiatingBlade-B{bank}-{j}';a.instance(iid,'MA-H01-R2-P02',loc=(x,y,.27));con.append({'parent_instance':'DualCollector','parent_socket':f'bank-{bank}-fin-{j}','child_instance':iid,'child_socket':'root'})
meta={'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'2.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'catalog_status':'visual-only; no game XML','axes':AXES,'instances':a.instances,'connections':con,'animations':[],'exports':[],'notes':'Open dual-comb radiator: thirty unchanged deep R2 blades on two narrow collectors. No emission, animation, temperatures, dissipation figures, physical metric scale or gameplay mechanics.'}
write(folder/'assembly.json',meta);bpy.context.scene.frame_end=1;bpy.context.view_layer.update();inspect();bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')));preview(folder,(0,0,.35),7.2,800,True)
write(folder/'README.md','''# MA-H02 — радиатор 2×3

Две открытые гребёнки глубоких поперечных лопастей на узких коллекторах. Сквозная щель между банками, открытые боковины и зубчатый контур сохраняют родство с действующим MA-H01 v2.0. Замкнутой наружной рамы, плиточного поля и универсального поддона нет.

Редактируемый источник MA-H02.blend; состав assembly.json; решение до моделирования composition-plan.md. Новая MA-H02-P01 v2.0 — двухканальный коллектор; повторно MA-H01-R2-P02 v2.0, 30 экземпляров без масштабирования или изменения. Всего 31 экземпляр, 2 исходные детали. Новая деталь прошла немедленную проверку до сборки. validation.json повторно открывает самостоятельные источники и сборку, проверяет геометрию и полные позы креплений.

Предпросмотры: Previews/top.png, perspective.png, top-grayscale.png. Процедурные PBR; без эмиссии, файловых текстур, UV-зависимости и анимации. Источники статичны. BU условные; радиатор — визуальная заготовка без игрового XML, теплоотвод/температуры/механика не задавались. GLB не создавался; игровая интеграция, коллайдеры и LOD не выполнялись. Соединения лопастей и коллекторов имеют намеренный заглублённый контакт.
''')
print('BUILT MA-H02',flush=True)
