"""Final Cyclone assets; no rendering. Run with Blender background."""
from pathlib import Path
import importlib.util, math
STYLE=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('runtime',STYLE/'Tools/weapon_asset_runtime.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
P='cm-cyclone-'
def ensure_part(pid,builder_fn,**metadata):
    complete=[STYLE/'Parts'/pid/(pid+'.blend'),STYLE/'Parts'/pid/'part.json',STYLE/'Exports'/'Parts'/(pid+'.glb')]
    if all(p.exists() for p in complete):
        print('REUSE_FINAL_PART '+pid,flush=True)
        return
    r.part(pid,builder_fn,**metadata)

def deck():
    r.box('low broad armored deck',(0,0,.19),(3.35,2.7,.38),'graphite',.13)
    r.box('orange deck inset',(0,0,.40),(2.8,2.2,.13),'orange',.08)
    for x in [-1.39,1.39]:
        for y in [-.99,.99]:
            r.box('thick corner pedestal',(x,y,.22),(.62,.66,.43),'steel',.10)
            r.box('corner inset',(x,y,.45),(.34,.38,.04),'graphite',.025)
    for x in [-.85,.85]:
        r.box('forward impact block',(x,-1.33,.26),(.68,.15,.28),'orange',.045)

def receiver():
    r.box('forged twin receiver',(0,.14,0),(2.24,1.72,.93),'graphite',.14)
    r.box('roof shell',(0,.26,.53),(2.0,1.4,.19),'orange',.085)
    r.box('center spine',(0,-.05,.66),(.32,1.73,.15),'steel',.045)
    r.box('rear electrical compartment',(0,1.05,-.05),(1.72,.4,.74),'steel',.07)
    for x in [-.78,.78]:
        r.ring('front breech collar',(x,-.76,0),.5,.33,.24,'steel','Y')
        r.box('breech shoulder',(x,-.46,.33),(.48,.77,.15),'orange',.04)
    for x in [-.60,-.3,0,.3,.6]:
        r.box('rear cooling fin',(x,1.29,-.02),(.09,.24,.50),'graphite',.025)

def rotor():
    # A real annular muzzle per tube rather than capped cylinders.
    r.cyl('rotor rear spindle',(0,.05,0),.38,.36,'graphite','Y')
    r.cyl('central shaft',(0,-1.02,0),.095,2.30,'steel','Y')
    for k in range(6):
        a=2*math.pi*k/6; x=.30*math.cos(a); z=.30*math.sin(a)
        r.ring('continuous open bore tube %d'%k,(x,-1.05,z),.118,.072,2.25,'steel','Y')
        r.ring('blackened muzzle %d'%k,(x,-2.22,z),.142,.073,.19,'graphite','Y')
        r.ring('tube root seal %d'%k,(x,-.05,z),.14,.115,.16,'graphite','Y')
    for y in [-.35,-1.32,-1.98]:
        r.ring('cluster tension cage',(0,y,0),.49,.405,.16,'graphite','Y')
        for k in range(6):
            a=math.tau*k/6
            r.box('radial collar bridge',(0.37*math.cos(a),y,.37*math.sin(a)),(.19,.19,.14),'steel',.025,rot=(0,-a,0))
    r.ring('orange rotor rim',(0,-.35,0),.506,.478,.10,'orange','Y')

def motor():
    r.cyl('rotary motor casing',(0,0,0),.46,.76,'graphite','Y')
    for y in [-.31,.31]:r.ring('motor forged ring',(0,y,0),.49,.35,.10,'steel','Y')
    for k in range(8):
        a=math.tau*k/8
        r.box('longitudinal motor rib',(.435*math.cos(a),0,.435*math.sin(a)),(.09,.54,.10),'steel',.02,rot=(0,-a,0))
    r.cyl('motor rear hub',(0,.44,0),.21,.16,'steel','Y')

def drum():
    r.cyl('ammo drum',(0,0,0),.63,.62,'graphite','X')
    for x in [-.28,.28]:r.ring('rolled drum rim',(x,0,0),.67,.53,.09,'steel','X')
    r.cyl('drum armor face',(.34,0,0),.56,.12,'orange','X')
    r.cyl('drum center axle',(.43,0,0),.22,.12,'steel','X')
    for k in range(12):
        a=math.tau*k/12
        r.box('drum protective rib',(0,.61*math.cos(a),.61*math.sin(a)),(.48,.10,.10),'steel',.02,rot=(a,0,0))

def cheek():
    r.profile('angular side armor',[(-.78,-.30),(-.55,.38),(.65,.48),(.94,.10),(.82,-.42),(-.46,-.48)],.19,'orange',.065)
    r.box('lower steel jaw',(0,.13,-.44),(.25,1.15,.15),'steel',.045)
    r.box('inset cooling recess',(.115,.28,.02),(.035,.61,.24),'graphite',.018)
    for y in [.05,.23,.41]:r.box('cooling separator',(.145,y,.02),(.045,.055,.25),'steel',.012)

ensure_part(P+'deck',deck,sockets=[r.socket('mount',(0,0,0)),r.socket('bearing',(0,0,.46))])
ensure_part(P+'receiver',receiver,sockets=[r.socket('mount',(0,0,0)),r.socket('rotor-left',(-.78,-.86,0)),r.socket('rotor-right',(.78,-.86,0))])
ensure_part(P+'rotor',rotor,sockets=[r.socket('mount',(0,0,0))],points=[r.socket('muzzle',(0,-2.32,0),role='firing-group-center')],animations=[{'id':'spin','axis':[0,-1,0],'node':'root','range_degrees':[0,360],'cyclic':True}])
ensure_part(P+'motor',motor,sockets=[r.socket('mount',(0,0,0))])
ensure_part(P+'drum',drum,sockets=[r.socket('mount',(0,0,0))])
ensure_part(P+'cheek',cheek,sockets=[r.socket('mount',(0,0,0))])
root=r.begin('fleet-minigun-cyclone',expected_muzzles=2,title='Cyclone twin rotary battery')
r.add(P+'deck','foundation',root)
r.add('cm-bearing','bearing',root,loc=(0,0,.46),scale=.92)
yaw=r.joint('yaw',root,loc=(0,0,.99))
pitch=r.joint('elevation',yaw,loc=(0,0,.47))
r.add(P+'receiver','receiver',yaw,loc=(0,0,.47))
for side,x in [('left',-.78),('right',.78)]:
    spin=r.joint('rotor_'+side,pitch,loc=(x,-.86,0))
    r.add(P+'rotor','rotating_cluster_'+side,spin)
    r.add(P+'motor','motor_'+side,pitch,loc=(x,.94,0))
    r.add(P+'drum','drum_'+side,yaw,loc=(-1.45 if x<0 else 1.45,.35,.37),rot=(0,0,math.pi if x<0 else 0))
    r.add(P+'cheek','cheek_'+side,yaw,loc=(-1.13 if x<0 else 1.13,0,.52),rot=(0,0,math.pi if x<0 else 0))
    r.muzzle('muzzle_'+side,spin,(0,-2.32,0),barrel_ref='fleet-minigun-cyclone-barrel-'+('0' if x<0 else '1'))
    r.key(spin,'rotation_euler',1,[(1,0),(121,-math.tau*4)])
r.add('cm-lamp','status',yaw,loc=(0,-.91,.84),scale=.7)
r.key(yaw,'rotation_euler',2,[(1,0),(61,.55),(121,0)])
r.key(pitch,'rotation_euler',0,[(1,0),(61,-.28),(121,0)])
r.finish()