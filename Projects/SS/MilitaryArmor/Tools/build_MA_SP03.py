"""Solar 3x5 explicit-size source variant; no GLB."""
import sys,json,bpy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,write,Assembly,AXES
from redesign_compute_production import Model
from redesign_RHSS import finish,socket,gate,preview
BID='MA-SP03';folder=ROOT/'Blocks'/BID
tag='MilitaryArmor.r2.solar.field'
positions=[(x,y) for y in [-2.9,0,2.9] for x in [-1.5,1.5]]
write(folder/'composition-plan.md','''# MA-SP03 — солнечная панель 3×5

Каталог solar-3x5: визуальная заготовка без игрового XML, мощности и механики освещения. BU условны, +Z вверх, -Y вперёд.

ДО моделирования проверены MA-SP01-R2-P01/P02 v2.0, MA-SP02-P01 v2.0 и scripts их геометрии. Поля 1.8×3.6 и 3.6×5.4 имеют unit-only scale и не подходят размеру 3×5. Новая MA-SP03-P01 v2.0 — явный размерный вариант тонкого сплошного поля 5.4×9.0 BU с новой сеткой 12×30 пассивных ячеек. Ячейки сохраняют шаг и размеры семейства SP02; не растягиваются. Скошенные углы, цельный низкий контур, тонкие кромки. Никаких радиаторных лопастей, тяжёлой рамы, эмиссии или раскладывания.

Опора MA-SP01-R2-P01 v2.0 1.56×2.85×0.305 BU подходит без изменений: шесть unit-scale экземпляров, X=±1.5 и Y=-2.9/0/2.9, без вращения. Между соседними опорами по Y зазор 0.05 BU, по X 1.44 BU; наложений опор нет. Концы опор вписываются в подложку. Их sockets Photovoltaic-field совпадают с шестью полными sockets нового поля. Повторное использование сохраняет материалы и source. Одна новая деталь, один повторно используемый источник, семь экземпляров.

Новую деталь проверить standalone и сохранить превью ДО сборки. Статика, source-only Blender; GLB не создавать.
''')
m=Model('MA-SP03-P01','Large passive photovoltaic sail, explicit 3x5 size variant')
m.panel('Thin continuous substrate',(0,0,.026),(5.4,9.0,.052),'Titanium',.55)
m.panel('Single dielectric underlay',(0,0,.059),(5.26,8.86,.014),'Dark',.53)
m.mats['Optic'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=0
cells=0
for row in range(30):
 y=-4.06+row*.28
 for col in range(12):
  x=-2.255+col*.41
  if abs(y)>3.95 and abs(x)>2.15:continue
  m.panel('Passive photovoltaic cell',(x,y,.073),(.391,.262,.016),'Optic',.020);cells+=1
  for dx in [-.115,.115]:m.box('Fine passive collector trace',(x+dx,y,.082),(.006,.242,.003),'Steel')
for x in [-2.65,2.65]:m.box('Thin ceramic edge',(x,0,.062),(.036,7.78,.028),'Ceramic')
for y in [-4.45,4.45]:m.box('Thin terminal edge',(0,y,.062),(4.18,.036,.028),'Ceramic')
m.box('Longitudinal electrical collector',(0,0,.074),(.012,8.40,.018),'Steel')
mounts=[socket('root',(0,0,0),tag)]+[socket('support-'+str(j),(x,y,0),tag) for j,(x,y) in enumerate(positions)]
finish(m,mounts)
a=Assembly(BID,'solar-3x5',[3,5],'Солнечная панель 3×5 — визуальная заготовка')
a.instance('LargePVField','MA-SP03-P01',loc=(0,0,.30));con=[]
for j,(x,y) in enumerate(positions):
 iid='Support-'+str(j);a.instance(iid,'MA-SP01-R2-P01',loc=(x,y,0));con.append({'parent_instance':iid,'parent_socket':'Photovoltaic-field','child_instance':'LargePVField','child_socket':'support-'+str(j)})
meta={'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'2.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'catalog_status':'visual-only; no game XML','axes':AXES,'instances':a.instances,'connections':con,'animations':[],'exports':[],'photovoltaic_cell_count':cells,'notes':'One new thin continuous passive field; six unmodified support sources at unit scale. No emission, deployment or gameplay parameters.'}
write(folder/'assembly.json',meta);bpy.context.scene.frame_end=1;bpy.context.view_layer.update();gate();bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')));preview(folder,True)
write(folder/'README.md',f'''# MA-SP03 — солнечная панель 3×5

Тонкое цельное поле со скошенными углами, {cells} пассивных фотоэлементов и тонкими электрическими дорожками. Шесть лёгких скрытых нижних опор; глубокие радиаторные лопасти и тяжёлая рама отсутствуют. Семейство MA-SP01/MA-SP02 сохранено, ширина и длина поля созданы заново, ячейки не растянуты.

Редактируемый MA-SP03.blend. Новая деталь MA-SP03-P01 v2.0; повторно MA-SP01-R2-P01 v2.0 без изменения (6 экземпляров). Семь экземпляров / два источника. composition-plan.md — решение по reuse; assembly.json и part.json — ID/версии, полные позы и совместимость креплений.

Новая деталь проверена standalone ДО сборки. validation.json — независимое открытие обоих источников и сборки, проверки source/evaluated geometry, нормалей, материалов, версий, unit scale и full socket poses. Previews/top.png, perspective.png и top-grayscale.png. Процедурные PBR; без файловых текстур, UV-зависимости, эмиссии и анимаций.

BU условны; visual-only без игрового XML. Мощность, физические метры, коллайдеры и LOD не назначались. GLB не создавались. Дорожки входят в поверхность ячеек на 0.0005 BU; центральная шина касается диэлектрика и лежит в зазоре между колонками, без coplanar поверхностей. Опоры разделены зазорами; сопряжение опор с низом подложки намеренное.
''')
print('BUILT MA-SP03',cells,flush=True)