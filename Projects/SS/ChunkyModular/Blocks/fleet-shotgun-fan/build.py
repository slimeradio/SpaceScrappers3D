"""Fleet Fan: one short wide single bore, 12 pellets per shot, no typography."""
import bpy, math, sys
from pathlib import Path
STYLE=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(STYLE/'Tools'))
import weapon_asset_runtime as r


def box(name,dims,loc,mat='graphite',bevel=.025,rot=None):
    return r.box(name,loc,dims,mat,bevel,rot)


def cyl(name,radius,depth,loc,mat='steel',axis='Z',vertices=96,bevel=.015):
    return r.cyl(name,loc,radius,depth,mat,axis,vertices,bevel)


def plinth():
    box('wide low deck',(2.64,1.54,.23),(0,0,.115),'graphite',.045)
    box('orange low saddle',(2.36,1.32,.21),(0,0,.32),'orange',.035)
    box('steel exposed deck',(2.09,1.13,.09),(0,0,.46),'steel',.02)
    for x in (-1,1):
        box('side armor block',(.35,1.5,.32),(x*1.18,0,.28),'graphite',.035)
        box('exposed foot edge',(.36,.32,.055),(x*1.18,-.59,.11),'steel',.012)
    for y in (-1,1):
        box('deck seam',(1.46,.025,.055),(0,y*.665,.33),'rubber',.006)


def breech():
    box('heavy low breech',(1.63,1.45,.61),(0,.14,.03),'graphite',.045)
    box('orange receiver spine',(1.43,.87,.29),(0,.37,.39),'orange',.04)
    box('rear steel buffer',(1.53,.28,.52),(0,.95,.02),'steel',.025)
    box('dark rear service seam',(1.35,.025,.1),(0,1.105,.03),'rubber',.006)
    for x in (-1,1):
        box('breech flank plate',(.17,1.3,.46),(x*.84,.17,.06),'orange',.03)
        cyl('elevation trunnion',.22,.18,(x*.96,.19,0),'steel',axis='X')
        box('upper barrel guide',(.14,1.42,.13),(x*.54,-.1,.38),'steel',.018)
    box('bottom loading recess',(.94,.4,.07),(0,.59,-.305),'rubber',.01)


def muzzle():
    # One connected rectangular opening, never a row of independent barrels.
    for x in (-1,1):
        box('wide bore side wall',(.12,1.15,.5),(x*.65,-.38,0),'steel',.02)
        box('dark inner side wall',(.018,1.01,.31),(x*.58,-.35,0),'graphite',.004)
    for z in (-1,1):
        box('wide bore roof',(1.42,1.15,.11),(0,-.38,z*.25),'steel',.025)
        box('dark inner roof',(1.16,.99,.018),(0,-.33,z*.186),'graphite',.004)
    # Stepped muzzle lip maintains a genuinely open central passage.
    for x in (-1,1):
        box('muzzle cheek',(.18,.3,.67),(x*.72,-.95,0),'graphite',.028)
    for z in (-1,1):
        box('muzzle lintel',(1.61,.3,.15),(0,-.95,z*.3),'graphite',.028)
        box('bright muzzle lip',(1.55,.04,.055),(0,-1.119,z*.255),'steel',.009)
        for y in (-.6,-.26,.08):
            box('shroud cooling rib',(1.4,.075,.07),(0,y,z*.325),'graphite',.014)
    box('rear barrel shoe',(1.45,.27,.64),(0,.37,0),'graphite',.028)


def slide():
    for x in (-1,1):
        box('long recoil shoe',(.19,1.32,.18),(x*.52,-.1,0),'graphite',.025)
        box('exposed slide runner',(.11,1.12,.05),(x*.52,-.16,.115),'steel',.012)
        box('buffer stop',(.27,.21,.27),(x*.52,.56,.035),'steel',.022)
    box('slide bridge',(1.23,.32,.16),(0,.35,-.07),'graphite',.022)
    box('protective central trough',(.57,.8,.13),(0,-.15,-.11),'rubber',.014)


def drum():
    cyl('ammo drum body',.43,.45,(0,0,0),'graphite',axis='X')
    cyl('orange outer drum sleeve',.45,.21,(.04,0,0),'orange',axis='X')
    cyl('machined rim outer',.46,.065,(.235,0,0),'steel',axis='X')
    cyl('machined rim inner',.46,.065,(-.235,0,0),'steel',axis='X')
    cyl('inset armored outer lid',.36,.08,(.28,0,0),'graphite',axis='X')
    cyl('central hub',.14,.105,(.34,0,0),'steel',axis='X')
    for k in range(8):
        a=2*math.pi*k/8
        ob=box('raised drum reinforcement',(.3,.11,.065),(0,math.sin(a)*.425,math.cos(a)*.425),'graphite',.012)
        ob.rotation_euler.x=-a
    box('feed throat',(.3,.35,.39),(-.15,.36,0),'steel',.025)


def carapace():
    r.profile('sloping top armor',[(-.65,0),(-.37,.18),(.57,.18),(.81,.03),(.72,-.05),(-.65,-.05)],1.55,'orange',.025)
    box('raised center panel',(.67,.62,.06),(0,.12,.215),'graphite',.018)
    for x in (-1,1):
        box('carapace exposed side edge',(.045,1.01,.045),(x*.77,.07,.08),'steel',.008)
    for y in (-.31,.55):
        box('top panel seam',(1.16,.022,.012),(0,y,.192),'rubber',.004)


def build():
    r.part('cm-fan-plinth',plinth,sockets=[r.socket('bearing',(0,0,.5))],regions=[{'id':'deck','shape':'rectangle','size':[2.4,1.3],'position':[0,0,.5],'normal':[0,0,1],'parent':'root'}])
    r.part('cm-fan-breech',breech,sockets=[r.socket('muzzle',(0,-.6,0)),r.socket('carapace',(0,.14,.46)),r.socket('drum-left',(-1.0,.38,0)),r.socket('drum-right',(1.0,.38,0))])
    r.part('cm-fan-muzzle',muzzle,sockets=[r.socket('mount',(0,0,0))],points=[r.socket('single-bore',(0,-1.12,0),role='muzzle')])
    r.part('cm-fan-slide',slide,sockets=[r.socket('receiver',(0,0,.19))])
    r.part('cm-fan-drum',drum,sockets=[r.socket('feed',(-.3,.36,0))])
    r.part('cm-fan-carapace',carapace,sockets=[r.socket('mount',(0,0,0))])
    root=r.begin('fleet-shotgun-fan',expected_muzzles=1,title='Fleet Fan single-bore wide shotgun')
    r.add('cm-fan-plinth','deck',root)
    yaw=r.joint('yaw',root,loc=(0,0,.5))
    r.add('cm-bearing','bearing',yaw,scale=.52)
    support=r.joint('support',yaw,loc=(0,0,.3))
    for x in (-1,1):
        # Existing side bearing is used without changing the v2 source.
        r.add('cm-trunnion-armored','trunnion-left' if x<0 else 'trunnion-right',support,loc=(x*1.01,.15,.29),rot=(0,0,math.pi if x<0 else 0),scale=.42)
    pitch=r.joint('pitch',support,loc=(0,.15,.34))
    r.add('cm-fan-slide','recoil-guide',pitch,loc=(0,-.1,-.33))
    recoil=r.joint('recoil',pitch)
    r.add('cm-fan-breech','receiver',recoil)
    r.add('cm-fan-muzzle','single-barrel',recoil,loc=(0,-.68,.02))
    r.add('cm-fan-carapace','top-armor',recoil,loc=(0,.14,.46))
    for x in (-1,1):
        r.add('cm-fan-drum','drum-left' if x<0 else 'drum-right',pitch,loc=(x*1.12,.48,0),rot=(0,0,math.pi if x<0 else 0))
    r.add('cm-lamp','diagnostic',pitch,loc=(0,-.58,.43),scale=.45)
    r.add('cm-vent-cassette','rear-cooling',pitch,loc=(0,.55,.64),scale=.55)
    r.muzzle('muzzle-0',recoil,(0,-1.8,.02),barrel_ref='fleet-shotgun-fan-barrel-0')
    r.key(yaw,'rotation_euler',2,[(1,0),(40,.8),(80,-.8),(120,0)])
    r.key(pitch,'rotation_euler',0,[(1,0),(40,math.radians(10)),(80,math.radians(-22)),(120,0)])
    r.key(recoil,'location',1,[(1,0),(11,0),(14,.13),(23,0),(120,0)])
    r.finish()


if __name__=='__main__':
    build()