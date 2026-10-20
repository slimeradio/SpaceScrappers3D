"""Final Monitor assets; source parts before assembly, no rendering."""
from pathlib import Path
import importlib.util, math
STYLE=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('runtime',STYLE/'Tools/weapon_asset_runtime.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
P='cm-monitor-'
def ensure_part(pid,builder_fn,**metadata):
    complete=[STYLE/'Parts'/pid/(pid+'.blend'),STYLE/'Parts'/pid/'part.json',STYLE/'Exports'/'Parts'/(pid+'.glb')]
    if all(p.exists() for p in complete):
        print('REUSE_FINAL_PART '+pid,flush=True)
        return
    r.part(pid,builder_fn,**metadata)

def deck():
    r.box('naval foundation',(0,0,.24),(4.65,3.65,.48),'graphite',.14)
    r.box('orange upper flange',(0,0,.52),(4.06,3.12,.15),'orange',.09)
    for x in [-1.94,1.94]:
        for y in [-1.36,1.36]:
            r.box('massive corner buttress',(x,y,.31),(.79,.80,.61),'steel',.12)
            r.box('recessed corner armor',(x,y,.63),(.54,.54,.06),'graphite',.035)
    for x in [-1.20,0,1.20]:
        r.box('front impact guard',(x,-1.79,.36),(.86,.26,.46),'graphite',.06)

def casemate():
    r.profile('deep tapered casemate',[(-1.27,-.62),(-1.38,.32),(-.90,.70),(1.30,.65),(1.66,.30),(1.55,-.56)],3.66,'graphite',.12)
    for x in [-1.90,1.90]:
        r.profile('thick orange side cheek',[(-1.23,-.48),(-1.26,.27),(-.88,.59),(1.17,.55),(1.45,.24),(1.35,-.43)],.18,'orange',.065).location.x=x
        r.cyl('trunnion armor',(x,0,-.01),.44,.18,'steel','X')
        r.cyl('trunnion inset',(x+(.11 if x>0 else -.11),0,-.01),.29,.07,'graphite','X')
    r.box('lower frontal jaw',(0,-1.33,-.47),(3.42,.35,.27),'steel',.065)
    for x in [-1.04,0,1.04]:
        r.box('recoil opening backing',(x,-1.42,.02),(.91,.21,.90),'rubber',.065)

def gun():
    r.cyl('forged breech',(0,.12,0),.37,.90,'graphite','Y')
    r.ring('open long artillery tube',(0,-2.15,0),.245,.151,4.02,'steel','Y')
    for y in [-.40,-.76]:r.ring('heavy breech reinforcing collar',(0,y,0),.36,.235,.22,'steel','Y')
    r.ring('forward reinforced band',(0,-3.63,0),.29,.235,.18,'graphite','Y')
    r.ring('muzzle outer reinforcement',(0,-4.32,0),.345,.153,.42,'graphite','Y')
    r.ring('muzzle exposed steel lip',(0,-4.56,0),.35,.153,.09,'steel','Y')
    # Four longitudinal structural muzzle ribs leave open axial channels.
    for x in [-.285,.285]:
        r.box('muzzle side rib',(x,-4.3,0),(.10,.52,.40),'steel',.025)
    for z in [-.285,.285]:
        r.box('muzzle vertical rib',(0,-4.3,z),(.40,.52,.10),'steel',.025)
    for x in [-.25,.25]:
        r.box('barrel root recoil rail',(x,-.10,.30),(.10,.82,.14),'steel',.025)

def sleeve():
    r.ring('sliding recoil sleeve',(0,-.38,0),.46,.375,1.15,'steel','Y')
    r.ring('front sleeve armor',(0,-.97,0),.49,.37,.16,'graphite','Y')
    for x in [-.36,.36]:
        r.box('long recoil guide',(x,-.38,-.28),(.20,1.27,.24),'graphite',.04)
        r.cyl('buffer piston',(x,-.30,.33),.09,1.12,'steel','Y')
    r.box('top carriage armor',(0,-.24,.44),(.57,1.03,.16),'orange',.045)

def roof():
    r.box('roof armor main',(0,0,0),(3.28,2.05,.22),'orange',.09)
    r.box('roof spine',(0,.10,.16),(.48,2.11,.16),'steel',.05)
    for x in [-1.07,1.07]:
        r.box('large recessed roof panel',(x,.04,.14),(.92,1.41,.10),'graphite',.045)
        r.box('rear armored lip',(x,.84,.20),(.94,.14,.12),'steel',.025)

def counterweight():
    r.box('aft counterbalance',(0,0,0),(3.42,.83,.92),'graphite',.09)
    r.box('aft orange balance cap',(0,.46,.16),(3.15,.14,.52),'orange',.05)
    for x in [-1.20,-.80,-.40,0,.40,.80,1.20]:
        r.box('deep aft cooling well',(x,.55,-.13),(.21,.12,.32),'rubber',.02)
        r.box('cooling lower lip',(x,.62,-.31),(.25,.11,.08),'steel',.015)

ensure_part(P+'deck',deck,sockets=[r.socket('mount',(0,0,0)),r.socket('bearing',(0,0,.60))])
ensure_part(P+'casemate',casemate,sockets=[r.socket('mount',(0,0,0))])
ensure_part(P+'gun',gun,sockets=[r.socket('mount',(0,0,0))],points=[r.socket('muzzle',(0,-4.61,0),role='projectile-origin')],animations=[{'id':'recoil','node':'root','axis':[0,1,0],'range':[0,.30],'units':'design_unit'}])
ensure_part(P+'sleeve',sleeve,sockets=[r.socket('mount',(0,0,0)),r.socket('gun',(0,0,0))])
ensure_part(P+'roof',roof,sockets=[r.socket('mount',(0,0,0))])
ensure_part(P+'counterweight',counterweight,sockets=[r.socket('mount',(0,0,0))])
root=r.begin('fleet-artillery-monitor',expected_muzzles=3,title='Monitor triple heavy artillery')
r.add(P+'deck','foundation',root)
r.add('cm-bearing','bearing',root,loc=(0,0,.60),scale=1.35)
yaw=r.joint('yaw',root,loc=(0,0,1.34))
pitch=r.joint('elevation',yaw,loc=(0,0,.63))
r.add(P+'casemate','casemate',yaw,loc=(0,0,.63))
r.add(P+'roof','roof',yaw,loc=(0,.12,1.40))
r.add(P+'counterweight','aft_balance',yaw,loc=(0,1.77,.61))
for index,x in enumerate([-1.04,0,1.04]):
    r.add(P+'sleeve','carriage_%d'%index,pitch,loc=(x,-1.04,0))
    slide=r.joint('recoil_%d'%index,pitch,loc=(x,-1.04,0))
    r.add(P+'gun','gun_%d'%index,slide)
    r.muzzle('muzzle_%d'%index,slide,(0,-4.61,0),barrel_ref='fleet-artillery-monitor-barrel-%d'%index)
    shift=index*12
    r.key(slide,'location',1,[(1,-1.04),(20+shift,-1.04),(24+shift,-.74),(44+shift,-1.04),(121,-1.04)])
for x in [-1.50,1.50]:r.add('cm-lamp','status_'+str(x),yaw,loc=(x,-1.48,1.09),scale=.60)
r.key(yaw,'rotation_euler',2,[(1,0),(61,.40),(121,0)])
r.key(pitch,'rotation_euler',0,[(1,0),(61,-.25),(121,0)])
r.finish()