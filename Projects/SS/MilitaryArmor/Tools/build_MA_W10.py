"""Pulse laser; editable parts and assembly only, no exports."""
import bpy,sys,math,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import weapon_batch_core as core
from build_MA_W09 import geometry,previews,socket
ROOT=core.ROOT;write=core.write;BID='MA-W10'
REUSE=['MA-W02-P01','MA-W02-P04','MA-P06']
def energy(c):
 c.section('Pulsed scatter feed',[(-.78,0,.12,.53,.24,.07),(-.44,0,.23,.76,.44,.12),(.59,0,.26,.76,.50,.14),(.82,0,.20,.51,.31,.09)],'Titanium')
 c.panel('Ceramic energy cassette',(0,.10,.52),(.63,1.08,.12),'Ceramic',.18)
 for y in [-.29,.10,.49]:
  c.panel('Capacitor separator',(0,y,.59),(.48,.09,.035),'Dark',.02,.002)
  c.box('Capacitor state',(0,y,.614),(.21,.022,.012),'Signal',.002)
def cradle(c):
 c.cyl('Sealed pulse azimuth',(0,0,.21),.72,.42,'Dark',verts=32)
 c.ring('Azimuth datum',(0,0,.39),.76,.63,.07,'Z','Titanium',32)
 c.panel('Narrow optical fork sill',(0,0,.49),(1.84,1.37,.24),'Titanium',.24)
 for s in [-1,1]:
  c.section('Swept pulse trunnion',[(-.72,s*.82,.71,.26,.46,.08),(-.28,s*.88,.85,.32,.72,.10),(.54,s*.77,.71,.32,.50,.09)],'Ceramic')
  c.cyl('Gimbal bearing',(s*.87,-.28,.92),.24,.22,'Titanium',axis='X',verts=24)
  c.cyl('Gimbal dielectric lid',(s*1.0,-.28,.92),.19,.04,'Armor',axis='X',verts=12)
 c.panel('Pulse cassette shoe',(1.22,.49,.53),(.82,1.76,.12),'Dark',.14)
 c.panel('Protected power bridge',(.81,.24,.52),(.65,.65,.17),'Titanium',.12)
def bench(c):
 for s in [-1,1]:
  c.section('Open optical bench rail',[(-1.22,s*.51,-.20,.23,.19,.055),(-.64,s*.55,-.17,.30,.24,.065),(.77,s*.48,-.14,.30,.29,.07),(1.18,s*.32,-.11,.22,.22,.06)],'Titanium')
  c.section('Floating ceramic rail cover',[(-1.05,s*.59,.10,.23,.20,.05),(-.23,s*.64,.19,.27,.25,.06),(.73,s*.48,.20,.30,.29,.07)],'Ceramic')
  for y in [-.67,-.12,.43]:c.panel('Cooling vane',(s*.67,y,.03),(.25,.12,.40),'Armor',.04)
  c.box('Bench alignment index',(s*.51,.14,.365),(.035,.40,.015),'Signal',.003)
 c.section('Aft pulse resonator',[(.54,0,0,.77,.50,.14),(.95,0,.03,.94,.64,.17),(1.35,0,0,.60,.45,.13)],'Armor')
 c.panel('Resonator ceramic lid',(0,1.03,.36),(.63,.62,.10),'Ceramic',.13)
 c.panel('Recessed optical path',(0,-.30,-.24),(.52,1.84,.08),'Dark',.07)
 c.panel('Rear optical window',(0,.47,0),(.41,.045,.28),'Optic',.008,.002)
 for y in [-.66,.05]:c.panel('Optical bench crossmember',(0,y,-.16),(1.09,.12,.15),'Titanium',.035)
 c.panel('Aperture coupling',(0,-1.24,-.12),(1.06,.27,.29),'Titanium',.09)
def main():
 folder=ROOT/'Blocks'/BID
 write(folder/'composition-plan.md','# MA-W10 — composition before modeling\n\nCatalog laser-blaster-small-turret: 1x3, one beam-emitter, Beam, 360deg yaw at90deg/s. BU not metres.\n\nReuse MA-W02-P01v1.0 laser foundation: correct power spine and azimuth socket; MA-W02-P04v1.0 short focusing aperture: optical function and unit dimensions fit; MA-W05-P04v1.0 pulse energy cassette: ready energy interface; MA-P06v1.3 flush service. All unit-scale, unchanged.\n\nNew MA-W10-P01: low asymmetric fork with energy shoe. MA-W02-P02 is too tall and wide for this lighter open bench. New MA-W10-P02: open dual optical rails and aft resonator. The closed continuous-laser chamber MA-W02-P03 would hide the pulsed optical path. Validate both standalone sources before assembly. No recoil, GLB or game integration.')
 hashes={p:hashlib.sha256((ROOT/'Parts'/p/(p+'.blend')).read_bytes()).hexdigest() for p in REUSE}
 specs=[('MA-W10-P01','Light asymmetric pulse-laser fork',cradle,[socket('bottom',(0,0,0),'structural'),socket('elevation',(0,-.28,.92),'elevation'),socket('pulse-feed',(1.22,.49,.59),'energy')]),('MA-W10-P02','Open pulse optical bench',bench,[socket('root',(0,0,0),'elevation'),socket('focus',(0,-1.24,0),'structural')])]
 specs.append(('MA-W10-P03','Pulse feed cassette - reduced bevel variant of MA-W05-P04',energy,[socket('root',(0,0,0),'energy')]))
 write(folder/'composition-plan.md',(folder/'composition-plan.md').read_text()+'\n\nValidation update before assembly: MA-W05-P04 has14 zero-area evaluated triangles on separator bevels. Do not modify old source. Create explicit MA-W10-P03 variant with .002BU separator bevel; preserve dimensions and energy socket. Validate standalone before assembly.')
 for pid,title,fn,mounts in specs:
  if not (ROOT/'Parts'/pid/'geometry-validation.json').exists():
   c=core.Part(pid,title);fn(c);checks=geometry();c.save(mounts,notes='Independent static editable part; unit scale; uniform procedural PBR. No file textures, UV dependency or local moving mechanism.')
   write(ROOT/'Parts'/pid/'geometry-validation.json',{'checks_passed':True,'validated_before_assembly':True,'meshes':checks});previews(ROOT/'Parts'/pid/'Previews')
 variant_path=ROOT/'Parts/MA-W10-P03/part.json';variant=json.loads(variant_path.read_text())
 variant['variant_of']={'id':'MA-W05-P04','version':'1.0','source_sha256':hashlib.sha256((ROOT/'Parts/MA-W05-P04/MA-W05-P04.blend').read_bytes()).hexdigest(),'change':'Separator bevel .002 BU replaces .015 BU to remove evaluated degenerate triangles; dimensions and root socket unchanged.'}
 write(variant_path,variant)
 a=core.Assembly(BID,'laser-blaster-small-turret',[1,3],'Малая импульсная лазерная турель')
 a.instance('LaserFoundation','MA-W02-P01');a.instance('ServiceCartridge','MA-P06',a.root,(0,1.22,.90))
 yaw=a.node('Azimuth',a.root,(0,-.42,.68));a.instance('PulseFork','MA-W10-P01',yaw)
 elev=a.node('Elevation',yaw,(0,-.28,.92));a.instance('OpticalBench','MA-W10-P02',elev)
 a.instance('FocusAperture','MA-W02-P04',elev,(0,-1.24,0));a.instance('PulseFeed','MA-W10-P03',yaw,(1.22,.49,.59))
 a.animate_rotation(yaw,'Z',[(1,0),(25,90),(49,180),(73,270),(97,360)])
 a.animate_rotation(elev,'X',[(1,0),(25,-12),(49,5),(73,-12),(97,0)])
 scene=bpy.context.scene;scene.render.fps=24;scene.frame_end=97;scene.frame_set(1);bpy.context.view_layer.update();geometry()
 connections=[dict(parent_instance='LaserFoundation',parent_socket='azimuth',child_instance='PulseFork',child_socket='bottom'),dict(parent_instance='LaserFoundation',parent_socket='service',child_instance='ServiceCartridge',child_socket='bottom'),dict(parent_instance='PulseFork',parent_socket='elevation',child_instance='OpticalBench',child_socket='root'),dict(parent_instance='OpticalBench',parent_socket='focus',child_instance='FocusAperture',child_socket='optical-input'),dict(parent_instance='PulseFork',parent_socket='pulse-feed',child_instance='PulseFeed',child_socket='root')]
 data=dict(schema='MilitaryArmor.BlenderAuthoring/1',id=BID,version='1.0',title=a.title,catalog_id='laser-blaster-small-turret',catalog_grid=[1,3],axes=core.AXES,instances=a.instances,nodes=[dict(id=o.name,parent=o.parent.name if o.parent else None,translation=list(o.location),rotation_euler_xyz=list(o.rotation_euler),scale=list(o.scale)) for o in a.nodes],connections=connections,animations=dict(fps=24,frame_range=[1,97],channels=a.clips,demonstration_only=True,interpolation='LINEAR yaw; Bezier elevation'),functional_points=[dict(id='shoot',part_instance='FocusAperture',part_point='continuous-emitter',semantic_role='single pulse beam output; optical hardware reused')],catalog_contract=dict(barrel_count=1,projectiles_per_shot=1,firing_arc_degrees=360,rotate_speed_degrees_per_second=90,pivot_grid=[.5,.5],projectile_kind='Beam'),exports=[],reused_source_sha256=hashes,notes='BU not metres; grid1x3. Single instantaneous beam. 90deg/s full turn demo; elevation artistic. No recoil. No engine integration, colliders/LOD or GLB.')
 for layer in yaw.animation_data.action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 write(folder/'assembly.json',data);bpy.ops.wm.save_as_mainfile(filepath=str(folder/(BID+'.blend')));previews(folder/'Previews')
 write(folder/'README.md','# MA-W10 — малая импульсная лазерная турель\n\nОткрытый оптический стенд с разнесёнными керамическими направляющими, короткая фокусирующая апертура, задний резонатор и одна боковая импульсная кассета. Одна линза и один импульсный луч по каталогу, сетка 1×3.\n\nНовые детали MA-W10-P01/P02 и вариант кассеты MA-W10-P03; база MA-W02-P01, линза MA-W02-P04 и сервис MA-P06 повторно использованы без изменения и масштаба. Исходник MA-W10.blend; состав/sockets/позы assembly.json, план composition-plan.md. Превью perspective.png, top.png, top-grayscale.png в Previews.\n\nПолный оборот360° за4секунды (90°/с), демонстрационное склонение без отдачи. BU условные, коллайдеры и LOD не заданы. Только авторинг, игровой запуск не проверялся; GLB не создавался.')
 print('BUILT MA-W10',flush=True)
if __name__=='__main__':main()
