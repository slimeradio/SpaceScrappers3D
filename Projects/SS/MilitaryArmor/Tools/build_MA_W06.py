"""Final long-rail sniper geometry; MilitaryArmor 1.3."""
import sys, math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import weapon_batch_core as c

def base():
    c.panel('Longitudinal anchor keel',(0,0,.17),(2.55,5.7,.34),'Dark',.58)
    c.panel('Long ceramic hardpoint',(0,0,.43),(2.95,6.0,.40),'Armor',.64)
    c.panel('Machined narrow deck',(0,0,.67),(2.58,5.46,.09),'Titanium',.48)
    c.cyl('Limited arc motor',(0,-.05,.81),.99,.29,'Dark',verts=48)
    c.ring('Precision yaw seat',(0,-.05,.94),1.11,.90,.14,'Z','Titanium')
    for s in [-1,1]:
        for y in [-1.97,1.97]:
            c.panel('Diagonal anchor armor',(s*.83,y,.75),(.73,1.34,.14),'Ceramic',.27)
            c.box('Narrow interface diagnostic',(s*1.38,y,.49),(.018,.44,.025),'Signal',.003)
    for y in [-1.88,1.93]:
        c.panel('Deck technical insert',(0,y,.737),(.49,1.06,.05),'Dark',.13)
        for j in range(3):c.box('Inset pin',(0,y-.26+j*.26,.768),(.27,.045,.015),'Titanium',.003)

def body():
    c.section('Narrow recoil cradle',[(-1.52,0,.26,1.43,.44,.14),(-.56,0,.46,2.08,.85,.23),(.87,0,.56,1.82,.93,.26),(1.57,0,.45,1.03,.56,.17)],'Dark')
    for s in [-1,1]:
        c.section('Spearhead ceramic flank',[(-1.65,s*.74,.37,.24,.31,.08),(-.74,s*1.02,.54,.46,.81,.14),(.80,s*.91,.66,.45,.94,.16),(1.52,s*.53,.49,.31,.58,.10)],'Ceramic')
        c.section('Lower protected transmission',[(-1.24,s*.74,.15,.29,.19,.06),(.89,s*.75,.26,.37,.33,.10)],'Titanium')
        c.cyl('Sealed elevation joint',(s*.89,-.68,.72),.30,.18,'Titanium',axis='X',verts=24)
        c.cyl('Flush joint shield',(s*1.00,-.68,.72),.23,.04,'Armor',axis='X',verts=12)
        c.box('Cradle state index',(s*.82,.67,1.123),(.025,.46,.02),'Signal',.003)
    c.panel('Rear service deck',(0,1.02,1.13),(.89,.90,.10),'Ceramic',.18)
    c.panel('Lidar pedestal',(0,.15,1.08),(.91,.72,.09),'Titanium',.15)

def gun():
    c.section('Rail breech core',[(-1.02,0,0,.92,.53,.14),(.60,0,0,.98,.61,.17),(1.05,0,0,.65,.39,.11)],'Titanium')
    for s in [-1,1]:
        c.section('Continuous split accelerator rail',[(-5.45,s*.39,0,.20,.23,.055),(-5.1,s*.43,0,.28,.32,.075),(-1.0,s*.43,0,.33,.40,.09),(-.52,s*.35,0,.30,.39,.08)],'Titanium')
        # Recessed field strips face the central bore, not the external armor.
        c.box('Rail inner field trace',(s*.254,-3.09,.025),(.018,4.14,.045),'Signal',.003)
        for y in [-4.64,-3.51,-2.38,-1.25]:
            c.section('Isolated field-coil shell',[(y-.35,s*.47,0,.37,.38,.09),(y,s*.49,0,.43,.48,.11),(y+.32,s*.47,0,.38,.40,.09)],'Ceramic')
            c.box('Coil diagnostic',(s*.49,y,.254),(.11,.13,.019),'Signal',.003)
            c.panel('Coil spine',(s*.48,y,.272),(.15,.43,.045),'Dark',.04)
        c.section('Breech armor',[(-1.08,s*.41,.25,.30,.13,.04),(.44,s*.43,.33,.31,.15,.045),(.84,s*.26,.25,.23,.12,.035)],'Armor')
    # One central projectile channel remains open between rails.
    c.box('Muzzle lower bridge',(0,-5.37,-.19),(.95,.26,.10),'Titanium',.025)
    c.box('Muzzle upper bridge',(0,-5.37,.19),(.95,.26,.10),'Ceramic',.025)
    c.box('Bore shadow',(0,-.88,0),(.39,.035,.26),'Dark',.012)
    for s in [-1,1]:
        c.panel('Breech recoil slide',(s*.25,.53,-.32),(.15,.85,.19),'Dark',.045)
        c.box('Protected recoil rail',(s*.25,.53,-.429),(.07,.64,.03),'Titanium',.004)

def capacitor():
    c.section('Aft pulse capacitor keel',[(-.18,0,.14,.69,.27,.08),(.20,0,.27,.93,.52,.15),(1.38,0,.35,.81,.68,.20),(1.94,0,.21,.42,.36,.11)],'Titanium')
    for y in [.25,.68,1.11,1.54]:
        c.panel('Capacitor ceramic lamella',(0,y,.69),(.73,.29,.16),'Ceramic',.09)
        c.box('Capacitor insulated separator',(0,y+.17,.67),(.56,.06,.08),'Dark',.015)
        for s in [-1,1]:c.box('Capacitor status rail',(s*.32,y,.78),(.023,.18,.012),'Signal',.002)
    c.panel('Aft armor tail',(0,1.75,.49),(.42,.46,.09),'Armor',.10)

def main():
    global c
    import weapon_batch_core as core
    import bpy, json, tempfile
    def socket(sid,pos,role='accessory'):
        return {'id':sid,'role':role,'position':list(pos),'forward':[0,-1,0],'up':[0,0,1],'compatible_role':role,'allowed_scale':[1,1,1]}
    spec=[('MA-W06-P01','Long sniper hardpoint',base,[socket('bottom',(0,0,0),'anchor'),socket('yaw',(0,0,1),'yaw')]),('MA-W06-P02','Spearhead sniper cradle',body,[socket('bottom',(0,0,0),'yaw'),socket('elevation',(0,-.68,.72),'elevation'),socket('service',(0,1.02,1.18)),socket('optic',(0,.15,1.125)),socket('capacitor',(0,1.30,.30),'energy')]),('MA-W06-P03','Long split-rail accelerator',gun,[socket('root',(0,0,0),'elevation')]),('MA-W06-P04','Aft capacitor keel',capacitor,[socket('root',(0,0,0),'energy')])]
    for pid,title,fn,mounts in spec:
        c=core.Part(pid,title);fn();points=[{'id':'shoot','role':'muzzle','node':'socket.root','position':[0,-5.52,0],'forward':[0,-1,0],'up':[0,0,1]}] if pid.endswith('P03') else []
        c.save(mounts=mounts,points=points,notes='MilitaryArmor 1.3; purpose-built explicit unit-scale variant. Uniform PBR materials; independent editable objects.')
    a=core.Assembly('MA-W06','sniper-turret',[1,2],'Long-rail sniper turret')
    a.instance('Hardpoint','MA-W06-P01');yaw=a.node('Yaw',a.root,(0,0,1));a.instance('SpearCradle','MA-W06-P02',yaw)
    elev=a.node('Elevation',yaw,(0,-.68,.72));recoil=a.node('Recoil',elev);a.instance('SplitRail','MA-W06-P03',recoil)
    a.instance('AftCapacitor','MA-W06-P04',yaw,(0,1.30,.30));a.instance('Service','MA-P06',yaw,(0,1.02,1.18));a.instance('Lidar','MA-P07',yaw,(0,.15,1.125))
    a.animate_rotation(yaw,'Z',[(1,0),(30,-45),(60,0),(90,45),(120,0)])
    a.animate_rotation(elev,'X',[(1,0),(30,-12),(60,4),(90,-12),(120,0)])
    a.animate_location(recoil,'Y',[(1,0),(40,0),(43,.22),(53,0),(120,0)])
    path=a.save('Catalog 1x2 footprint class; one barrel and one muzzle. BU scale not metres. Catalog yaw ±45deg; elevation/recoil are artistic demonstrations. Split rails share one central projectile channel.')
    core.write(core.ROOT/'Blocks/MA-W06/README.md','# MA-W06 — Rail sniper\n\nNarrow long split-rail accelerator, four segmented field-coil pairs, aft capacitor keel and precise open muzzle bridge. One central projectile channel.\n\nEditable source: MA-W06.blend. Derived viewer export: Exports/MA-W06.glb. Four new independent source parts MA-W06-P01..P04; MA-P06/MA-P07 1.3 reused at unit scale. Details and attachment plan: composition-plan.md.\n\nCatalog 1x2 grid and 90-degree yaw arc. Elevation/recoil are visual demonstrations. BU physical scale, colliders, LOD and engine integration remain unspecified. Final Blender source and GLB are validated; no game installation performed.')
    a.review(view=(10,-13,10),target=(0,-1.4,1.3),scale=11.8,resolution=700)
    a.review(path=Path(tempfile.gettempdir())/'MA-W06-final-top.png',view=(0,-1.4,17),target=(0,-1.4,0),scale=11.8,resolution=600)
    bpy.ops.wm.open_mainfile(filepath=str(core.ROOT/'Blocks/MA-W06/MA-W06.blend'))
    d=json.loads((core.ROOT/'Blocks/MA-W06/validation.json').read_text());d['source_reopened']=True
    for f in [1,30,43,60,90,120]:bpy.context.scene.frame_set(f)
    d['animation_frames_sampled']=[1,30,43,60,90,120]
    core.reset();bpy.ops.import_scene.gltf(filepath=str(path));d['glb_imported_in_Blender']=True;d['imported_mesh_objects']=sum(o.type=='MESH' for o in bpy.context.scene.objects);d['imported_actions']=len(bpy.data.actions)
    assert d['imported_mesh_objects']>0 and d['imported_actions']>0
    core.write(core.ROOT/'Blocks/MA-W06/validation.json',d)

if __name__=='__main__':main()
