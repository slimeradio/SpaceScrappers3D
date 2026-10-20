"""Final continuous optical beam turret; no raster previews."""
import sys, math
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent.parent/'Tools'))
import weapon_asset_runtime as r

def bed():
    r.box('long laser station keel',(0,0,.16),(1.80,4.35,.32),'graphite',.065)
    r.box('main orange armor',(0,0,.35),(1.64,4.12,.17),'orange',.045)
    for y in [-1.78,1.78]:
        r.box('cross frame',(0,y,.18),(2.02,.45,.36),'steel',.04)
        for x in [-.78,.78]: r.box('corner impact shoe',(x,y,.28),(.53,.63,.52),'graphite',.055)
    for y in [-1.32,1.32]:
        r.box('armored coolant cover',(0,y,.49),(1.18,.54,.17),'graphite',.03)
        for x in [-.4,-.2,0,.2,.4]: r.box('coolant cover rib',(x,y,.595),(.09,.41,.045),'steel',.009)

def chamber():
    r.box('optical resonator chamber',(0,.10,0),(1.10,1.63,.87),'graphite',.08)
    r.box('top orange bridge',(0,.12,.51),(1.02,1.37,.22),'orange',.055)
    r.box('service channel',(0,.12,.65),(.31,1.12,.08),'steel',.014)
    for x in [-.60,.60]:
        r.box('shoulder shell',(x,.25,.03),(.23,1.54,.78),'orange',.05)
        r.cyl('pitch shaft',(x,0,0),.34,.29,'steel','X')
        r.ring('pitch seal',(x*1.2,0,0),.37,.27,.10,'graphite','X')
    r.box('back pulse isolator',(0,.99,.02),(.89,.38,.67),'steel',.05)
    for x in [-.28,0,.28]: r.box('back black vent',(x,1.195,.02),(.12,.055,.43),'rubber',.012)

def emitter():
    r.cyl('optical cavity',(0,-.49,0),.56,.95,'graphite','Y')
    r.ring('rear cavity ring',(0,-.11,0),.63,.43,.17,'steel','Y')
    r.ring('focus bezel',(0,-.98,0),.68,.44,.25,'steel','Y')
    r.ring('heat isolation ring',(0,-.82,0),.62,.48,.10,'orange','Y')
    r.cyl('deep optical glass',(0,-.925,0),.425,.055,'cyan','Y',bevel=.008)
    r.ring('inner optical retainer',(0,-.975,0),.44,.37,.06,'graphite','Y')
    for a in [math.pi/4,3*math.pi/4,5*math.pi/4,7*math.pi/4]:
        x=.53*math.cos(a); z=.53*math.sin(a)
        r.box('long focus cage',(x,-.53,z),(.17,.79,.17),'steel',.022)
    r.box('brow impact hood',(0,-.65,.66),(1.24,.86,.16),'orange',.045)
    r.box('chin radiator shoe',(0,-.66,-.65),(1.0,.75,.14),'graphite',.032)

def cooler():
    r.box('coolant manifold',(0,0,0),(.54,1.66,.74),'graphite',.045)
    for y in [-.69,.69]: r.box('orange end tank',(0,y,0),(.64,.27,.87),'orange',.04)
    for y in [-.51,-.34,-.17,0,.17,.34,.51]:
        r.box('steel cooling fin',(0,y,.02),(.77,.075,.77),'steel',.013)
    for z in [-.25,.25]:
        r.cyl('coolant hardline',(.42,0,z),.065,1.53,'steel','Y',bevel=.012)
        for y in [-.57,.57]: r.ring('hardline collar',(.42,y,z),.09,.06,.13,'graphite','Y')

def power():
    r.box('laser power supply',(0,0,0),(1.04,.85,.72),'graphite',.06)
    r.box('orange armored power top',(0,0,.43),(1.15,.90,.16),'orange',.04)
    for x in [-.36,0,.36]:
        r.box('electrical transformer ridge',(x,0,.54),(.16,.68,.08),'steel',.014)
    for x in [-.29,.29]:
        r.cyl('energy coupling',(x,-.48,0),.15,.20,'steel','Y')
        r.ring('energy coupling isolator',(x,-.54,0),.17,.10,.07,'graphite','Y')
        r.cyl('energy contact',(x,-.59,0),.08,.035,'cyan','Y',bevel=.005)
    r.box('rear inset',(0,.445,0),(.76,.04,.36),'rubber',.01)
    for x in [-.27,-.09,.09,.27]: r.box('rear fins',(x,.48,0),(.07,.10,.33),'steel',.01)

def build(block_id):
    r.part('cm-beam-bed',bed,sockets=[r.socket('mount',(0,0,0)),r.socket('bearing',(0,0,.45))])
    r.part('cm-beam-chamber',chamber,sockets=[r.socket('mount',(0,0,0)),r.socket('emitter',(0,-.72,0)),r.socket('power',(0,1.2,0))],regions=[{'id':'side_cooling','shape':'box','dimensions':[2.7,1.8,1.0],'position':[0,.20,0],'parent':'root','compatibility':['cm-beam-cooler']}])
    r.part('cm-beam-emitter',emitter,sockets=[r.socket('mount',(0,0,0))],points=[r.socket('beam_origin',(0,-1.15,0),role='continuous_beam')])
    r.part('cm-beam-cooler',cooler,sockets=[r.socket('mount',(0,0,0))])
    r.part('cm-beam-power',power,sockets=[r.socket('mount',(0,0,0))])
    root=r.begin(block_id,expected_muzzles=1,title='Турель непрерывного лазера')
    r.add('cm-beam-bed','bed',parent=root)
    r.add('cm-bearing','bearing',parent=root,loc=(0,0,.45),scale=.62)
    yaw=r.joint('yaw',parent=root,loc=(0,0,.80))
    pitch=r.joint('pitch',parent=yaw,loc=(0,0,.67))
    r.add('cm-beam-chamber','resonator',parent=pitch)
    r.add('cm-beam-emitter','optical_emitter',parent=pitch,loc=(0,-.72,0))
    r.add('cm-beam-cooler','cooler_right',parent=pitch,loc=(1.01,.20,0))
    r.add('cm-beam-cooler','cooler_left',parent=pitch,loc=(-1.01,.20,0),rot=(0,0,math.pi))
    r.add('cm-beam-power','power_supply',parent=pitch,loc=(0,1.60,0))
    r.add('cm-lamp','status',parent=pitch,loc=(0,2.08,.25),rot=(0,0,math.pi),scale=.55)
    r.muzzle('continuous_beam_exit',pitch,(0,-1.87,0),barrel_ref='continuous-emitter')
    r.key(yaw,'rotation_euler',2,[(1,0),(35,-math.pi/2),(70,math.pi/2),(105,0)])
    r.key(pitch,'rotation_euler',0,[(1,0),(35,math.radians(9)),(70,math.radians(-14)),(105,0)])
    root['catalog_grid']='1x3'; yaw['range_degrees']='-180..180'; yaw['rotate_speed_degrees_per_second']=90
    root['weapon_kind']='ContinuousBeam; one emitter; no ballistic recoil'
    r.finish()

def main(): build('continuous-laser-turret')

if __name__=='__main__': main()
