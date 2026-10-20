"""Explicit 4x6 passive photovoltaic source, no exports."""
import sys,json,bpy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,write,Assembly,AXES,outline
from redesign_compute_production import Model
from redesign_RHSS import finish,socket,gate,preview
BID='MA-SP04';folder=ROOT/'Blocks'/BID
tag='MilitaryArmor.r2.solar.field'
positions=[(x,y) for y in [-3.9,0,3.9] for x in [-2.1,2.1]]
write(folder/'composition-plan.md','''# MA-SP04 — солнечная панель 4×6

Каталог solar-4x6: visual-only без игрового XML, мощности или механики освещения. BU условны, +Z вверх, -Y вперёд.

ДО моделирования проверены MA-SP01-R2-P01 v2.0, MA-SP03-P01 v2.0 и геометрические scripts семейства. Поле SP03 5.4×9.0 BU unit-only не подходит новому размеру. Создать явный вариант MA-SP04-P01 7.2×10.8 BU; сетка 16×36=576 ячеек. Шаг .41/.28 и размеры .391/.262 BU сохранены, ячейки не растягиваются. Скошенное цельное тонкое поле; нижние опоры скрыты. Без тяжёлой рамы, радиаторных лопастей, эмиссии и раскладывания.

Опора MA-SP01-R2-P01 v2.0 1.56×2.85×.305 BU подходит без изменений: шесть экземпляров при X=±2.1 и Y=-3.9/0/3.9. Unit scale, без вращений; минимальный зазор между опорами 1.05 BU, по X 2.64 BU. Все опоры вписываются в поле. Их sockets Photovoltaic-field совмещаются с полными sockets нового поля. Сохранить один новый источник и один повторно используемый источник, семь экземпляров.

Ячейки и дорожки параметрически собраны по рядам с раздельными замкнутыми элементами и vertex groups Cell-00..15 / Trace-00..31. Каждый ряд редактируется отдельно; source geometry сохраняется. Проверить геометрию standalone немедленно, сохранить самостоятельные превью, затем собрать блок. GLB не создавать.
''')
m=Model('MA-SP04-P01','Large passive photovoltaic sail, explicit 4x6 size variant')
m.panel('Thin continuous substrate',(0,0,.026),(7.2,10.8,.052),'Titanium',.55)
m.panel('Single dielectric underlay',(0,0,.059),(7.06,10.66,.014),'Dark',.53)
m.mats['Optic'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=0

def batch(name,items,mat):
 verts=[];faces=[];groups=[]
 for label,(x,y,z),(w,d,h),cut in items:
  pts=outline(w,d,cut) if cut else [(-w/2,-d/2),(w/2,-d/2),(w/2,d/2),(-w/2,d/2)];n=len(pts);off=len(verts)
  verts.extend((x+a,y+b,z-h/2) for a,b in pts);verts.extend((x+a,y+b,z+h/2) for a,b in pts)
  fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
  faces.extend(tuple(off+k for k in f) for f in fs);groups.append((label,list(range(off,off+2*n))))
 o=m.mesh(name,verts,faces,mat,0)
 for label,indices in groups:o.vertex_groups.new(name=label).add(indices,1.0,'REPLACE')
 o['element_count']=len(items)
 return o
cells=0
for row in range(36):
 y=-4.90+row*.28;ci=[];ti=[]
 for col in range(16):
  x=-3.075+col*.41
  ci.append((f'Cell-{col:02d}',(x,y,.073),(.391,.262,.016),.020));cells+=1
  for j,dx in enumerate([-.115,.115]):ti.append((f'Trace-{col*2+j:02d}',(x+dx,y,.082),(.006,.242,.003),0))
 batch(f'PV-row-{row:02d}',ci,'Optic');batch(f'Trace-row-{row:02d}',ti,'Steel')
for x in [-3.55,3.55]:m.box('Thin ceramic edge',(x,0,.062),(.036,9.58,.028),'Ceramic')
for y in [-5.35,5.35]:m.box('Thin terminal edge',(0,y,.062),(5.98,.036,.028),'Ceramic')
m.box('Longitudinal electrical collector',(0,0,.074),(.012,10.24,.018),'Steel')
mounts=[socket('root',(0,0,0),tag)]+[socket('support-'+str(j),(x,y,0),tag) for j,(x,y) in enumerate(positions)]
finish(m,mounts)
a=Assembly(BID,'solar-4x6',[4,6],'Солнечная панель 4×6 — визуальная заготовка')
a.instance('LargePVField','MA-SP04-P01',loc=(0,0,.30));con=[]
for j,(x,y) in enumerate(positions):
 iid='Support-'+str(j);a.instance(iid,'MA-SP01-R2-P01',loc=(x,y,0));con.append({'parent_instance':iid,'parent_socket':'Photovoltaic-field','child_instance':'LargePVField','child_socket':'support-'+str(j)})
meta={'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'2.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'catalog_status':'visual-only; no game XML','axes':AXES,'instances':a.instances,'connections':con,'animations':[],'exports':[],'photovoltaic_cell_count':cells,'notes':'One new thin continuous passive field; six unmodified support sources at unit scale. No emission, deployment or gameplay parameters.'}
write(folder/'assembly.json',meta);bpy.context.scene.frame_end=1;bpy.context.view_layer.update();gate();bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')));preview(folder,True)
write(folder/'README.md',f'''# MA-SP04 — солнечная панель 4×6

Тонкое цельное поле со скошенными углами, {cells} пассивных фотоэлементов и тонкими электрическими дорожками. Шесть лёгких скрытых нижних опор; глубокие радиаторные лопасти и тяжёлая рама отсутствуют. Семейство MA-SP01/MA-SP02/MA-SP03 сохранено, ширина и длина поля созданы заново, ячейки не растянуты.

Редактируемый MA-SP04.blend. Новая деталь MA-SP04-P01 v2.0; повторно MA-SP01-R2-P01 v2.0 без изменения (6 экземпляров). Семь экземпляров / два источника. composition-plan.md — решение по reuse; assembly.json и part.json — ID/версии, полные позы и совместимость креплений. Ячейки и дорожки сгруппированы по 36 редактируемым рядам с vertex groups отдельных элементов.

Новая деталь проверена standalone ДО сборки. validation.json — независимое открытие обоих источников и сборки, проверки source/evaluated geometry, нормалей, материалов, версий, unit scale и full socket poses. Previews/top.png, perspective.png и top-grayscale.png. Процедурные PBR; без файловых текстур, UV-зависимости, эмиссии и анимаций.

BU условны; visual-only без игрового XML. Мощность, физические метры, коллайдеры и LOD не назначались. GLB не создавались. Дорожки входят в поверхность ячеек на 0.0005 BU; центральная шина касается диэлектрика и лежит в зазоре между колонками, без coplanar поверхностей. Опоры разделены зазорами минимум 1.05 BU; сопряжение опор с низом подложки намеренное.
''')
print('BUILT MA-SP04',cells,flush=True)
