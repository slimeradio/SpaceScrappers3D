"""Final rail sniper asset; run with Blender background. No preview generation."""
import sys, math
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent.parent/'Tools'))
import weapon_asset_runtime as r

def bed():
    r.box('forged keel',(0,0,.16),(1.68,3.55,.32),'graphite',.065)
    r.box('orange armored deck',(0,0,.35),(1.48,3.28,.18),'orange',.045)
    for x in [-.67,.67]:
        r.box('longitudinal steel skid',(x,0,.11),(.24,3.9,.22),'steel',.04)
        for y in [-1.55,1.55]:
            r.box('armored end shoe',(x,y,.29),(.42,.57,.48),'graphite',.055)
            r.box('end shoe ridge',(x,y,.55),(.27,.42,.07),'steel',.015)
    r.box('rear service inset',(0,1.33,.46),(.72,.4,.08),'rubber',.018)
    for x in [-.27,0,.27]: r.box('deck service channel',(x,1.33,.515),(.11,.32,.035),'steel',.007)

def breech():
    r.box('central forging',(0,.2,0),(1.17,1.7,.86),'graphite',.07)
    r.box('rear armor wedge',(0,.87,.06),(1.34,.56,.97),'orange',.09)
    r.box('upper structural rib',(0,.15,.49),(.77,1.37,.16),'steel',.03)
    r.box('loading cassette',(0,.73,.62),(.69,.65,.23),'graphite',.04)
    for x in [-.64,.64]:
        r.box('breech cheek',(x,.16,0),(.19,1.24,.71),'orange',.045)
        r.cyl('pitch spindle',(x,0,0),.31,.25,'steel','X')
        r.ring('pitch spindle shoulder',(x*1.14,0,0),.34,.22,.10,'graphite','X')
    r.box('front magnetic guide',(0,-.69,0),(1.02,.30,.68),'steel',.045)
    r.box('guide dark center',(0,-.857,0),(.48,.045,.24),'rubber',.009)

def rails():
    # One firing channel between two separate electromagnetic rails.
    for x in [-.31,.31]:
        r.box('rail carrier',(x,-1.66,0),(.34,3.72,.42),'graphite',.045)
        r.box('exposed acceleration conductor',(x,-1.67,.235),(.22,3.50,.075),'steel',.014)
        r.box('orange rail armor',(x*1.17,-1.34,-.06),(.19,2.70,.50),'orange',.035)
        for y in [-.32,-.92,-1.52,-2.12,-2.72]:
            r.box('induction segment',(x,y,.32),(.30,.32,.14),'steel',.018)
            r.box('magnetic slot',(x,y,.397),(.18,.12,.018),'cyan',.004)
    for y in [0,-.7,-1.4,-2.1,-2.95]:
        r.box('lower rail bridge',(0,y,-.27),(.94,.18,.19),'steel',.025)
    r.box('muzzle left fang',(-.38,-3.59,.015),(.23,.49,.57),'steel',.025)
    r.box('muzzle right fang',(.38,-3.59,.015),(.23,.49,.57),'steel',.025)
    r.box('muzzle lower jaw',(0,-3.54,-.33),(.92,.43,.15),'graphite',.025)

def capacitor():
    r.box('armored power bank',(0,0,0),(.44,1.46,.56),'graphite',.045)
    r.box('removable armor lid',(0,0,.31),(.48,1.53,.12),'orange',.025)
    for y in [-.48,0,.48]:
        r.cyl('capacitor body',(0,y,0),.20,.40,'steel','X')
        r.ring('capacitor clamp',(0,y,0),.227,.194,.10,'graphite','X')
    for y in [-.61,.61]: r.box('contact strip',(0,y,.395),(.26,.10,.04),'cyan',.006)

def sight():
    r.box('optical instrument body',(0,0,0),(.31,1.06,.28),'graphite',.034)
    r.box('sight armored hood',(0,-.18,.17),(.39,.70,.11),'orange',.025)
    r.cyl('scope forward lens',(0,-.575,0),.105,.04,'cyan','Y',bevel=.008)
    r.ring('scope protective bezel',(0,-.60,0),.15,.11,.12,'steel','Y')
    r.box('rear adjustment housing',(0,.39,.17),(.23,.25,.15),'steel',.02)

def build(block_id):
    r.part('cm-sniper-bed',bed,sockets=[r.socket('mount',(0,0,0)),r.socket('bearing',(0,0,.45))])
    r.part('cm-sniper-breech',breech,sockets=[r.socket('mount',(0,0,0)),r.socket('rails',(0,-.83,0)),r.socket('sight',(0,.1,.8))],regions=[{'id':'power_banks','shape':'box','dimensions':[1.7,1.6,.8],'position':[0,.20,0],'parent':'root','compatibility':['cm-sniper-capacitor']}])
    r.part('cm-sniper-rails',rails,sockets=[r.socket('mount',(0,0,0))],points=[r.socket('projectile_exit',(0,-3.85,0),role='muzzle')])
    r.part('cm-sniper-capacitor',capacitor,sockets=[r.socket('mount',(0,0,0))])
    r.part('cm-sniper-sight',sight,sockets=[r.socket('mount',(0,0,0))],points=[r.socket('optical_axis',(0,-.65,0),role='aim')])
    root=r.begin(block_id,expected_muzzles=1,title='Снайперская рельсовая турель')
    r.add('cm-sniper-bed','bed',parent=root)
    r.add('cm-bearing','bearing',parent=root,loc=(0,0,.45),scale=.55)
    yaw=r.joint('yaw',parent=root,loc=(0,0,.76))
    pitch=r.joint('pitch',parent=yaw,loc=(0,0,.62))
    r.add('cm-sniper-breech','breech',parent=pitch)
    recoil=r.joint('recoil',parent=pitch,loc=(0,-.83,0))
    r.add('cm-sniper-rails','rail_accelerator',parent=recoil)
    r.add('cm-sniper-capacitor','capacitor_left',parent=pitch,loc=(-.94,.30,0))
    r.add('cm-sniper-capacitor','capacitor_right',parent=pitch,loc=(.94,.30,0))
    r.add('cm-sniper-sight','precision_sight',parent=pitch,loc=(0,.12,.82))
    r.add('cm-lamp','status',parent=pitch,loc=(0,1.20,.27),rot=(0,0,math.pi),scale=.5)
    r.muzzle('sniper_exit',recoil,(0,-3.85,0),barrel_ref='sniper-barrel')
    r.key(yaw,'rotation_euler',2,[(1,0),(35,-math.pi/4),(70,math.pi/4),(105,0)])
    r.key(pitch,'rotation_euler',0,[(1,0),(35,math.radians(8)),(70,math.radians(-12)),(105,0)])
    r.key(recoil,'location',1,[(1,-.83),(42,-.83),(45,-.66),(56,-.83),(105,-.83)])
    root['catalog_grid']='1x2'; yaw['range_degrees']='-45..45'; yaw['rotate_speed_degrees_per_second']=45
    r.finish()

def main(): build('sniper-turret')

if __name__=='__main__': main()
