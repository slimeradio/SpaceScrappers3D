"""Final catalog wedge armor; no intermediate asset variants."""
import sys, json, math, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from mathutils import Vector
from weapon_batch_core import Part,Assembly,write,ROOT
BID='MA-A03'; PID='MA-A03-P01'
outline=[(-.5,-.5),(.5,.5),(-.5,.5)]
p=Part(PID,'Faceted spacecraft wedge armor 1x1')
v=[(x,y,0) for x,y in outline]+[(x,y,.16) for x,y in outline]
f=[(2,1,0)]; material=[0]
for i in range(3):
 j=(i+1)%3;f.append((i,j,3+j,3+i));material.append(0)
# Clipped top ring: unequal shoulders follow the diagonal hull edge.
ring=[]
for i,a in enumerate(outline):
 prev=outline[(i-1)%3];nxt=outline[(i+1)%3]
 for b in [prev,nxt]:
  delta=Vector(b)-Vector(a);q=Vector(a)+delta.normalized()*.095;ring.append(q)
for q in ring:v.append((q.x,q.y,.235))
for i in range(3):
 j=(i+1)%3
 f.append((3+i,6+2*i,6+2*i+1));material.append(0)
 f.append((3+i,6+2*i+1,6+2*j,3+j));material.append(0)
# Upper shell shifted from the diagonal: a broad diagonal shoulder and narrow rear return.
center=Vector((-1/6,1/6))
for q in ring:
 q=center+(q-center)*.79+Vector((-.018,.018));v.append((q.x,q.y,.28))
for i in range(6):
 j=(i+1)%6;f.append((6+i,6+j,12+j,12+i));material.append(0)
# One shallow inset, no separate floating plate or tiny grooves.
for q in v[12:18]:
 xy=center+(Vector(q[:2])-center)*.90;v.append((xy.x,xy.y,.255))
for i in range(6):
 j=(i+1)%6;f.append((12+i,12+j,18+j,18+i));material.append(1)
f.append(tuple(range(18,24)));material.append(0)
o=p.mesh('MA-A03.faceted-shell',v,f,'Armor',0);o.data.materials.append(p.mats['Ceramic'])
for poly,index in zip(o.data.polygons,material):poly.material_index=index
mounts=[{'id':'root','role':'structural-bottom','parent':o.name,'position':[0,0,0],'forward':[0,-1,0],'up':[0,0,1],'compatibility':['MilitaryArmor.armor'],'constraints':'unit scale; bottom at z0'}]
for i,(a,b) in enumerate(zip(outline,outline[1:]+outline[:1])):
 d=Vector(b)-Vector(a);n=Vector((d.y,-d.x,0)).normalized();mounts.append({'id':'edge-'+str(i),'role':'coplanar-armor-join','parent':o.name,'position':[(a[0]+b[0])/2,(a[1]+b[1])/2,.08],'forward':list(n),'up':[0,0,1],'compatibility':['MilitaryArmor.armor'],'constraints':{'edge_length_BU':d.length,'wall_height_BU':.16}})
p.save(mounts=mounts,notes='Armor wedge catalog 1x1; 1 BU visual pitch only. Exact triangular structural skirt. Quiet inset cap. No emission, textures, hardware, animation or functional points.')
partfile=ROOT/'Parts'/PID/'part.json';data=json.loads(partfile.read_text('utf8'));data['attachment_areas']=[{'id':'bottom-footprint','role':'structural-mount','parent':o.name,'shape':'polygon','vertices_local':[[x,y,0] for x,y in outline],'position':[0,0,0],'normal':[0,0,-1],'up':[0,1,0],'allowed_rotation_degrees':[0,90,180,270],'compatibility':['MilitaryArmor.armor'],'constraints':'nominal triangular footprint; authoring only, not engine socket contract'}];write(partfile,data)
a=Assembly(BID,'armor-wedge',[1,1],'Faceted spacecraft wedge armor')
a.instance('shell',PID);a.save(notes='Single standalone faceted shell. Catalog footprint 1x1; physical scale unspecified. Static armor; no animation.',frame_end=1)
assemblyfile=ROOT/'Blocks'/BID/'assembly.json';data=json.loads(assemblyfile.read_text('utf8'));data['animations']=[];write(assemblyfile,data)
write(ROOT/'Blocks'/BID/'README.md','''# MA-A03 — клиновидная броня 1×1

Каталог: armor-wedge. Точный треугольный торец основания; широкое диагональное плечо, срезанные верхние вершины и утопленная спокойная лицевая плоскость. Подходит для частого повторения без мелкого шума.

Деталь: MA-A03-P01 v1.0, один экземпляр shell с единичным масштабом. Один меш, два материала Armor/Ceramic без эмиссии и файловых текстур. Крепления только логические; анимаций и функциональных точек нет.

Редактируемый источник MA-A03.blend; готовый GLB Exports/MA-A03.glb. Единица BU условная, pivot в центре каталожной клетки z=0, +Z вверх и -Y вперёд; высота .28, ровная стенка стыка .16. Каталожная клетка не считается метром. Игровая установка и физический масштаб не проверялись.

Результаты фактической проверки исходников, импорта GLB и бюджета записаны в validation.json. Финальный внутренний обзор — в TEMP, без промежуточных пользовательских вариантов.
''')
print('FINAL_ARMOR',BID)