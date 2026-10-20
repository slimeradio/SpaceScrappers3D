"""Parametric finished parts for Fleet Rocket Bastion. +Z up, -Y forward."""
import bpy, math, sys
from pathlib import Path
from mathutils import Vector
STYLE=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(STYLE/'Tools'))
import weapon_asset_runtime as r


def box(name,dims,loc,mat='graphite',bevel=.025,rot=None):
    return r.box(name,loc,dims,mat,bevel,rot)


def cyl(name,radius,depth,loc,mat='steel',axis='Z',vertices=96,bevel=.015):
    return r.cyl(name,loc,radius,depth,mat,axis,vertices,bevel)


def plinth():
    box('broad forged sole',(3.55,2.95,.26),(0,0,.13),'graphite',.055)
    box('stepped orange platform',(3.19,2.59,.27),(0,0,.38),'orange',.055)
    box('top steel deck',(2.86,2.3,.12),(0,0,.575),'steel',.035)
    for x in (-1,1):
        for y in (-1,1):
            box('corner impact block',(.48,.56,.5),(x*1.49,y*1.2,.32),'graphite',.045)
            box('exposed sole edge',(.51,.19,.08),(x*1.49,y*1.43,.15),'steel',.018)
    for x in (-1,1):
        box('side recessed seam',(.035,1.7,.085),(x*1.6,0,.39),'rubber',.008)
    box('front cable recess',(1.55,.05,.11),(0,-1.3,.39),'graphite',.012)


def cradle():
    box('central rotating saddle',(2.2,1.5,.28),(0,0,.14),'graphite',.045)
    for x in (-1,1):
        box('elevation bearing tower',(.26,1.15,.84),(x*1.15,0,.5),'graphite',.035)
        box('tower orange inset',(.07,.88,.42),(x*1.31,0,.66),'orange',.022)
        cyl('transverse axle',.235,.17,(x*1.3,0,.81),'steel',axis='X')
        cyl('armored axis cap',.29,.09,(x*1.41,0,.81),'graphite',axis='X',vertices=96)
    box('center buttress',(.45,.72,.33),(0,.32,.39),'steel',.03)


def pod():
    # Structural frame only; two independently authored cell instances fit inside it.
    for x in (-1,1):
        box('longitudinal pod armor',(.14,2.38,1.77),(x*.43,0,0),'orange',.032)
        box('inner supporting rail',(.065,2.2,1.55),(x*.33,0,0),'steel',.015)
    for z in (-1,1):
        box('pod end armor',(.9,2.38,.14),(0,0,z*.87),'orange',.035)
        box('outer graphite cap',(.79,1.85,.1),(0,.18,z*.96),'graphite',.025)
    box('rear pod cross member',(.86,.2,1.8),(0,1.12,0),'graphite',.025)
    box('cell separator',(.87,2.25,.095),(0,0,0),'steel',.018)
    for z in (-.88,.88):
        for y in (-.85,.8):
            box('transverse heat band',(.93,.16,.07),(0,y,z),'steel',.014)


def cell():
    # Four separate walls form a genuinely open square throat.
    for x in (-1,1):
        box('launch liner side',(.055,2.22,.64),(x*.3,-.08,0),'steel',.012)
        box('inner dark side',(.016,2.02,.51),(x*.264,-.02,0),'graphite',.004)
    for z in (-1,1):
        box('launch liner roof',(.65,2.22,.055),(0,-.08,z*.3),'steel',.012)
        box('inner dark roof',(.51,2.02,.016),(0,-.02,z*.264),'graphite',.004)
    box('sealed rear cell',(.64,.12,.64),(0,1.04,0),'graphite',.014)
    for x in (-1,1):
        box('heavy mouth jamb',(.095,.18,.74),(x*.345,-1.23,0),'graphite',.018)
    for z in (-1,1):
        box('heavy mouth lintel',(.74,.18,.095),(0,-1.23,z*.345),'graphite',.018)
    box('launch guide',(.075,1.84,.04),(0,-.02,-.25),'steel',.009)
    box('status amber lens',(.14,.027,.025),(0,-1.326,.352),'amber',.005)


def shield():
    box('thick external shield',(.18,1.75,1.46),(0,0,0),'orange',.04)
    box('rear graphite heel',(.23,.5,1.42),(0,.72,-.05),'graphite',.03)
    box('inset central strip',(.025,1.1,.14),(-.101,-.05,.12),'steel',.008)
    for z in (-1,1):
        box('raised armor rail',(.24,1.65,.17),(0,0,z*.7),'graphite',.028)
    for y in (-.58,.1,.78):
        box('panel break',(.025,.022,.92),(-.105,y,0),'rubber',.005)


def spine():
    box('central targeting spine',(.49,1.69,.9),(0,.1,0),'graphite',.035)
    box('orange top carapace',(.55,1.45,.18),(0,.1,.51),'orange',.032)
    box('steel front brow',(.48,.17,.37),(0,-.81,.27),'steel',.022)
    box('recessed targeting face',(.36,.06,.23),(0,-.91,.24),'rubber',.012)
    box('small optical aperture',(.13,.025,.09),(0,-.946,.24),'cyan',.012)
    for y in (.3,.53,.76):
        box('spine dorsal fins',(.44,.065,.16),(0,y,.62),'steel',.015)
    for x in (-1,1):
        box('central side channel',(.035,1.1,.13),(x*.255,.1,-.15),'rubber',.008)


def build():
    r.part('cm-bastion-plinth',plinth,sockets=[r.socket('bearing',(0,0,.64))],regions=[{'id':'deck','shape':'rectangle','size':[2.8,2.3],'position':[0,0,.64],'normal':[0,0,1],'parent':'root'}])
    r.part('cm-bastion-cradle',cradle,sockets=[r.socket('elevation',(0,0,.81))])
    r.part('cm-bastion-pod',pod,sockets=[r.socket('cell-low',(0,0,-.43)),r.socket('cell-high',(0,0,.43)),r.socket('shield',(0,0,0))])
    r.part('cm-bastion-cell',cell,sockets=[r.socket('mount',(0,0,0))],points=[r.socket('launch-mouth',(0,-1.34,0),role='muzzle')])
    r.part('cm-bastion-shield',shield,sockets=[r.socket('mount',(0,0,0))])
    r.part('cm-bastion-spine',spine,sockets=[r.socket('mount',(0,0,0))],points=[r.socket('aim',(0,-.95,.24),role='targeting')])
    root=r.begin('fleet-rocket-bastion',expected_muzzles=4,title='Fleet Bastion four-cell missile turret')
    r.add('cm-bastion-plinth','deck',root)
    yaw=r.joint('yaw',root,loc=(0,0,.64))
    r.add('cm-bearing','bearing',yaw,scale=.86)
    r.add('cm-bastion-cradle','cradle',yaw,loc=(0,0,.49))
    pitch=r.joint('pitch',yaw,loc=(0,0,1.3))
    r.add('cm-bastion-spine','central-spine',pitch,loc=(0,.03,.05))
    channel=0
    for x in (-1,1):
        px=x*.76
        r.add('cm-bastion-pod','pod-left' if x<0 else 'pod-right',pitch,loc=(px,0,0))
        r.add('cm-bastion-shield','shield-left' if x<0 else 'shield-right',pitch,loc=(x*1.31,.08,0),rot=(0,0,math.pi if x>0 else 0))
        for z in (-.43,.43):
            r.add('cm-bastion-cell','cell-'+str(channel),pitch,loc=(px,0,z))
            r.muzzle('muzzle-'+str(channel),pitch,(px,-1.34,z),barrel_ref='fleet-rocket-bastion-barrel-'+str(channel))
            channel+=1
    for x in (-1,1):
        r.add('cm-vent-cassette','rear-vent-left' if x<0 else 'rear-vent-right',pitch,loc=(x*.76,.73,1.005),scale=.7)
    r.add('cm-lamp','deck-status',yaw,loc=(0,-1.12,.13),scale=.7)
    r.key(yaw,'rotation_euler',2,[(1,0),(40,.85),(80,-.85),(120,0)])
    r.key(pitch,'rotation_euler',0,[(1,0),(40,math.radians(6)),(80,math.radians(-38)),(120,0)])
    r.finish()

if __name__=='__main__':
    build()