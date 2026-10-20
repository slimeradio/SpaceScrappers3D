"""Final Fleet fan weapon geometry; MilitaryArmor 1.3."""
import sys, math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import weapon_batch_core as c

def base():
    c.panel('Hex anchor keel',(0,0,.16),(5.7,2.8,.32),'Dark',.6)
    c.panel('Wide ceramic hardpoint',(0,0,.45),(6.1,3.0,.44),'Armor',.7)
    c.panel('Flush interface deck',(0,0,.69),(5.4,2.55,.12),'Titanium',.5)
    c.cyl('Azimuth motor',(0,0,.78),1.06,.32,'Dark',verts=48)
    c.ring('Azimuth indexed seat',(0,0,.92),1.18,.97,.15,'Z','Titanium')
    for s in [-1,1]:
        c.panel('Swept anchor shoulder',(s*2.30,0,.73),(.9,2.0,.19),'Ceramic',.32)
        for y in [-.65,0,.65]:
            c.box('Hardpoint diagnostic',(s*2.80,y,.52),(.025,.28,.026),'Signal',.004)
        c.panel('Inset anchor interface',(s*2.22,-.13,.845),(.38,.83,.026),'Dark',.10)

def body():
    c.section('Fan structural spine',[(-.95,0,.26,3.8,.4,.15),(.2,0,.40,4.7,.75,.25),(1.08,0,.46,3.8,.8,.25),(1.37,0,.42,2.7,.45,.15)],'Dark')
    for s in [-1,1]:
        c.section('Delta ceramic shoulder',[(-1.46,s*2.14,.46,.30,.40,.11),(-.4,s*2.19,.54,.82,.81,.22),(.68,s*1.94,.55,.80,.89,.25),(1.08,s*1.55,.50,.52,.66,.19)],'Ceramic')
        c.section('Floating armor liner',[(-1.23,s*2.20,.24,.37,.18,.05),(-.34,s*2.34,.28,.61,.25,.07),(.58,s*2.10,.29,.52,.25,.06)],'Titanium')
        c.panel('Top angular armor',(s*1.23,.54,.98),(1.1,1.2,.10),'Armor',.27)
        c.box('Swept power conduit',(s*1.67,.17,1.004),(.033,.80,.022),'Signal',.004)
        c.cyl('Enclosed trunnion',(s*1.72,-.65,.57),.34,.18,'Titanium',axis='X',verts=24)
        c.cyl('Trunnion ceramic lid',(s*1.83,-.65,.57),.27,.045,'Ceramic',axis='X',verts=12)
    c.panel('Aft control roof',(0,.79,1.00),(1.04,.98,.10),'Ceramic',.19)
    c.panel('Central sensor plinth',(0,-.10,.92),(.96,.72,.10),'Titanium',.15)

def gun():
    c.section('Single scatter chamber',[(-1.9,0,0,3.38,.40,.12),(-1.38,0,0,3.65,.63,.18),(-.33,0,0,3.06,.68,.18),(.28,0,0,2.45,.50,.15)],'Titanium')
    c.panel('Single dark muzzle aperture',(0,-1.963,0),(2.83,.04,.29),'Dark',.08)
    # Four faceted lips surround ONE broad aperture, not twelve barrels.
    for z in [-.225,.225]:
        c.section('Armored scatter lip',[(-2.03,0,z,3.06,.11,.035),(-1.73,0,z,3.56,.16,.04),(-1.02,0,z,3.40,.17,.045)],'Ceramic')
    for s in [-1,1]:
        c.section('Scatter aperture cheek',[(-2.0,s*1.56,0,.18,.34,.05),(-1.5,s*1.77,0,.30,.54,.08),(-.52,s*1.56,0,.24,.57,.07)],'Armor')
    for x in [-1.2,-.8,-.4,0,.4,.8,1.2]:
        c.box('Aperture field index',(x,-1.994,.145),(.15,.024,.019),'Signal',.003)
        c.panel('Upper field tile',(x,-1.14,.37),(.29,.58,.09),'Armor',.07)
        c.box('Field tile diagnostic',(x,-1.25,.419),(.021,.29,.012),'Signal',.002)
    for x in [-1.1,1.1]:
        c.panel('Recoil guide',(x,.13,-.23),(.21,.85,.20),'Dark',.06)
        c.box('Sealed recoil track',(x,.13,-.34),(.10,.60,.04),'Titanium',.006)

def cassette():
    c.section('Pulsed scatter feed',[(-.78,0,.12,.53,.24,.07),(-.44,0,.23,.76,.44,.12),(.59,0,.26,.76,.50,.14),(.82,0,.20,.51,.31,.09)],'Titanium')
    c.panel('Ceramic energy cassette',(0,.10,.52),(.63,1.08,.12),'Ceramic',.18)
    for y in [-.29,.10,.49]:
        c.panel('Capacitor separator',(0,y,.59),(.48,.09,.035),'Dark',.02)
        c.box('Capacitor state',(0,y,.614),(.21,.022,.012),'Signal',.002)

def main():
    global c
    import weapon_batch_core as core
    import bpy, json, tempfile
    def socket(sid,pos,role='accessory'):
        return {'id':sid,'role':role,'position':list(pos),'forward':[0,-1,0],'up':[0,0,1],'compatible_role':role,'allowed_scale':[1,1,1]}
    spec=[('MA-W05-P01','Wide scatter hardpoint',base,[socket('bottom',(0,0,0),'anchor'),socket('yaw',(0,0,1),'yaw')]),('MA-W05-P02','Swept fan cradle',body,[socket('bottom',(0,0,0),'yaw'),socket('elevation',(0,-.65,.57),'elevation'),socket('service',(0,.79,1.05)),socket('optic',(0,-.10,.97)),socket('energy-left',(-2.75,.20,.20),'energy'),socket('energy-right',(2.75,.20,.20),'energy')]),('MA-W05-P03','Single scatter accelerator aperture',gun,[socket('root',(0,0,0),'elevation')]),('MA-W05-P04','Scatter pulse feed cassette',cassette,[socket('root',(0,0,0),'energy')])]
    for pid,title,fn,mounts in spec:
        c=core.Part(pid,title);fn();points=[{'id':'shoot','role':'muzzle','node':'socket.root','position':[0,-2.06,0],'forward':[0,-1,0],'up':[0,0,1]}] if pid.endswith('P03') else []
        c.save(mounts=mounts,points=points,notes='MilitaryArmor 1.3; purpose-built explicit unit-scale variant. Uniform PBR materials; independent editable objects.')
    a=core.Assembly('MA-W05','fleet-shotgun-fan',[2,1],'Fleet fan — wide scatter turret')
    a.instance('Hardpoint','MA-W05-P01')
    yaw=a.node('Yaw',a.root,(0,0,1));a.instance('FanCradle','MA-W05-P02',yaw)
    elev=a.node('Elevation',yaw,(0,-.65,.57));recoil=a.node('Recoil',elev);a.instance('ScatterAperture','MA-W05-P03',recoil)
    a.instance('LeftFeed','MA-W05-P04',yaw,(-2.75,.20,.20));a.instance('RightFeed','MA-W05-P04',yaw,(2.75,.20,.20))
    a.instance('Service','MA-P06',yaw,(0,.79,1.05));a.instance('Lidar','MA-P07',yaw,(0,-.10,.97))
    a.animate_rotation(yaw,'Z',[(1,0),(30,90),(60,180),(90,270),(120,360)])
    a.animate_rotation(elev,'X',[(1,0),(30,-12),(60,4),(90,-12),(120,0)])
    a.animate_location(recoil,'Y',[(1,0),(40,0),(43,.16),(53,0),(120,0)])
    path=a.save('Catalog 2x1 footprint class; one barrel, one muzzle, 12 projectiles per shot. BU scale not metres. Yaw360 per catalog; elevation/recoil are artistic demonstration, not gameplay values.')
    core.write(core.ROOT/'Blocks/MA-W05/README.md','# MA-W05 — Fleet fan\n\nWide fan-shaped scatter turret. One physical muzzle aperture, twelve projectiles per shot in catalog; the seven diagnostic field tiles are not barrels.\n\nEditable source: MA-W05.blend. Derived viewer export: Exports/MA-W05.glb. Four new independent source parts MA-W05-P01..P04; MA-P06/MA-P07 1.3 reused at unit scale. Details and attachment plan: composition-plan.md.\n\nAnimation: yaw 360 degrees, enclosed elevation and recoil. Elevation/recoil are visual demonstrations. BU physical scale, colliders, LOD and engine integration remain unspecified. Final Blender source and GLB are validated; no game installation performed.')
    a.review(view=(9,-10,8),target=(0,-.3,1.4),scale=8.5,resolution=700)
    a.review(path=Path(tempfile.gettempdir())/'MA-W05-final-top.png',view=(0,-.01,15),target=(0,0,0),scale=8.5,resolution=600)
    bpy.ops.wm.open_mainfile(filepath=str(core.ROOT/'Blocks/MA-W05/MA-W05.blend'))
    d=json.loads((core.ROOT/'Blocks/MA-W05/validation.json').read_text());d['source_reopened']=True
    for f in [1,30,43,60,90,120]:bpy.context.scene.frame_set(f)
    d['animation_frames_sampled']=[1,30,43,60,90,120]
    core.reset();bpy.ops.import_scene.gltf(filepath=str(path));d['glb_imported_in_Blender']=True;d['imported_mesh_objects']=sum(o.type=='MESH' for o in bpy.context.scene.objects);d['imported_actions']=len(bpy.data.actions)
    assert d['imported_mesh_objects']>0 and d['imported_actions']>0
    core.write(core.ROOT/'Blocks/MA-W05/validation.json',d)

if __name__=='__main__':main()
