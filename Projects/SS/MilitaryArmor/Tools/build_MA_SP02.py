"""Wide passive photovoltaic sail; source only."""
import sys,json,bpy,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_batch_core import ROOT,write,Assembly,AXES
from redesign_compute_production import Model
from redesign_RHSS import finish,socket,gate,preview
BID='MA-SP02';folder=ROOT/'Blocks'/BID
tag='MilitaryArmor.r2.solar.field'
positions=[(0,-1.55),(0,1.55)]
write(folder/'composition-plan.md','''# MA-SP02 — солнечная панель 2×3

Каталог solar-2x3: visual-only, игрового XML нет. BU условны, +Z вверх, -Y вперёд. Мощность и метрический масштаб не задаются.

Изучены MA-SP01 v2.0, метаданные обеих MA-SP01-R2 деталей и их параметрическая геометрия в Tools/redesign_RHSS.py. Опора MA-SP01-R2-P01 v2.0 (1.56×2.85×0.305 BU) подходит для повторения: два unit-scale экземпляра Y±1.55 с поворотом Z=90° поддерживают поле четырьмя поперечинами. Существующий исходник не изменяется. Полные sockets нового поля совпадают с опорами.

MA-SP01-R2-P02 v2.0: поле 1.8×3.6, unit-only. Не растягивать: создать явный размерный вариант MA-SP02-P01 v2.0 — единое поле 3.6×5.4, новая равномерная сетка 8×18 ячеек с четырьмя пропусками на скошенных углах, тонкие пассивные дорожки. Родство с MA-SP01 сохранено. Открытая радиаторная гребёнка и тяжёлая силовая рама отсутствуют. Других подходящих деталей не требуется.

Одна новая деталь/один повторно используемый источник, три экземпляра. До сборки проверить новую деталь и сохранить самостоятельные превью. Статика, без эмиссии, анимаций и GLB.
''')
m=Model('MA-SP02-P01','Wide passive photovoltaic field, explicit 2x3 size variant')
m.panel('Thin continuous substrate',(0,0,.026),(3.6,5.4,.052),'Titanium',.44)
m.panel('Single dielectric underlay',(0,0,.059),(3.46,5.26,.014),'Dark',.42)
m.mats['Optic'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=0
for row in range(18):
 y=-2.38+row*.28
 for col in range(8):
  x=-1.435+col*.41
  if abs(y)>2.25 and abs(x)>1.25:continue
  m.panel('Passive photovoltaic cell',(x,y,.073),(.391,.262,.016),'Optic',.020)
  for dx in [-.115,.115]:m.box('Fine passive collector trace',(x+dx,y,.082),(.006,.242,.003),'Steel')
for x in [-1.75,1.75]:m.box('Thin ceramic edge',(x,0,.062),(.036,4.48,.028),'Ceramic')
for y in [-2.65,2.65]:m.box('Thin terminal edge',(0,y,.062),(2.68,.036,.028),'Ceramic')
m.box('Longitudinal electrical collector',(0,0,.074),(.012,5.04,.018),'Steel')
mounts=[socket('root',(0,0,0),tag)]
for j,(x,y) in enumerate(positions):
 s=socket('support-'+str(j),(x,y,0),tag);s['forward']=[1,0,0];mounts.append(s)
finish(m,mounts)
a=Assembly(BID,'solar-2x3',[2,3],'Солнечная панель 2×3 — визуальная заготовка')
a.instance('WidePVField','MA-SP02-P01',loc=(0,0,.30));con=[]
for j,(x,y) in enumerate(positions):
 iid='SupportQuadrant-'+str(j);a.instance(iid,'MA-SP01-R2-P01',loc=(x,y,0),rot=(0,0,math.pi/2));con.append({'parent_instance':iid,'parent_socket':'Photovoltaic-field','child_instance':'WidePVField','child_socket':'support-'+str(j)})
meta={'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'2.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'catalog_status':'visual-only; no game XML','axes':AXES,'instances':a.instances,'connections':con,'animations':[],'exports':[],'notes':'One new wide passive field; two unmodified support sources at unit scale. No emission, deployment mechanism or gameplay parameters.'}
write(folder/'assembly.json',meta);bpy.context.scene.frame_end=1;bpy.context.view_layer.update();gate();bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')));preview(folder,True)
write(folder/'README.md','''# MA-SP02 — солнечная панель 2×3

Тонкое сплошное поле со скошенными углами, сеткой 140 пассивных ячеек и электрическими дорожками. Две поперечные опоры, без тяжёлого поддона и силовой рамы. Семейство MA-SP01 v2.0; новое поле создано размерным вариантом, ячейки не растягивались. В отличие от радиатора поверхность цельная и низкая.

Редактируемый MA-SP02.blend. Новая MA-SP02-P01 v2.0; повторно MA-SP01-R2-P01 v2.0 без изменения (2 экземпляра). Всего три экземпляра/два источника. Состав, версии, позы и совместимость: assembly.json / part.json. Решение по повторному использованию: composition-plan.md.

Новая деталь проверена ДО сборки. validation.json — независимый повторный процесс открывает оба источника и сборку; проверяет геометрию, нормали, положительный объём, source/evaluated degeneracy, материалы, ссылки и полные позы sockets. Виды Previews/top.png, perspective.png и top-grayscale.png. Процедурные PBR; без файловых текстур, UV-зависимости, эмиссии и анимаций.

BU условны; visual-only без игрового XML. Мощность, коллайдеры, LOD и игровой экспорт не задавались. GLB не создавались. Прилегания опор и подложки намеренные; тонкие слои разведены по высоте, coplanar поверхностей нет.
''')
print('BUILT MA-SP02',flush=True)