from pathlib import Path
r=Path(__file__).resolve().parents[1]
def w(p,t): p.write_bytes(t.replace('\r\n','\n').replace('\n','\r\n').encode('utf8'))
s=(r/'Tools/build_MA_I01.py').read_text(encoding='utf8')
head=s[:s.index('def mount')].replace("BID='MA-I01'","BID='MA-G01'")
func=s[s.index('def mount'):s.index("write(FOLDER/'composition-plan.md'")]
body='''
if '--assembly-only' not in sys.argv:
 m=Part('MA-G01-P01','Compact garage docking platform')
 m.panel('Load foundation',(0,0,.11),(1.8,1.8,.22),'Armor',.18,.012)
 m.panel('Hull gasket',(0,0,.025),(1.68,1.68,.05),'Dark',.16,.005)
 m.panel('Inset apron',(0,-.56,.23),(1.18,.57,.02),'Titanium',.08,.002)
 for x in [-.45,.45]:m.panel('Alignment runner',(x,-.57,.26),(.085,.50,.04),'Steel',.02,.003)
 m.panel('Entry threshold',(0,-.80,.26),(1.20,.10,.04),'Ceramic',.025,.003)
 finish(m,[mount('hull',(0,0,0),'MilitaryArmor.garage.hull'),mount('portal',(0,-.40,.22),'MilitaryArmor.garage.portal'),mount('housing',(0,.20,.22),'MilitaryArmor.garage.housing')])
 m=Part('MA-G01-P02','Protected garage access portal')
 for x in [-.65,.65]:
  m.section('Swept portal shoulder',[(-.26,x,.37,.24,.74,.06),(-.08,x,.42,.29,.84,.07),(.15,x,.37,.24,.74,.06)],'Armor',.009)
  m.panel('Cold side armour',(x,-.18,.38),(.16,.20,.69),'Ceramic',.045,.007)
 m.panel('Portal crown',(0,-.02,.79),(1.35,.35,.16),'Ceramic',.08,.009)
 m.panel('Pressure backing',(0,.07,.37),(1.09,.16,.73),'Dark',.05,.006)
 for x in [-.265,.265]:
  m.panel('Recessed closed access leaf',(x,-.024,.375),(.51,.026,.64),'Titanium',.04,.003)
  m.panel('Flush capture pad',(x,-.043,.38),(.20,.018,.21),'Armor',.035,.002)
  m.box('Capture index',(x,-.056,.40),(.075,.008,.016),'Signal',.001)
 m.panel('Protected sill',(0,-.10,.035),(1.11,.28,.07),'Steel',.035,.005)
 finish(m,[mount('root',(0,0,0),'MilitaryArmor.garage.portal')])
 m=Part('MA-G01-P03','Garage rear pressure shell')
 m.panel('Rear shell',(0,.12,.34),(1.42,1.07,.68),'Armor',.16,.010)
 for x in [-.66,.66]:m.section('Diagonal reinforcement',[(-.35,x,.26,.20,.49,.05),(.20,x,.36,.20,.69,.05),(.63,x,.30,.20,.55,.05)],'Ceramic',.008)
 m.panel('Upper gasket',(0,.15,.692),(1.24,.89,.024),'Dark',.13,.003)
 m.panel('Dorsal shield',(0,.16,.735),(1.16,.80,.07),'Ceramic',.15,.007)
 m.panel('Cartridge seat',(0,.24,.789),(.76,.64,.038),'Titanium',.10,.004)
 m.panel('Rear closed seam',(0,.652,.30),(.69,.016,.33),'Dark',.055,.002)
 finish(m,[mount('root',(0,0,0),'MilitaryArmor.garage.housing'),mount('service',(0,.24,.81),'MilitaryArmor.service-cartridge.v1')])
a=Assembly(BID,'garage-ship',[1,1],'Корабельный гараж 1×1')
a.instance('Foundation','MA-G01-P01');a.instance('Portal','MA-G01-P02',loc=(0,-.40,.22));a.instance('Housing','MA-G01-P03',loc=(0,.20,.22));a.instance('Diagnostic','MA-R01-P05',loc=(0,.44,1.03))
connections=[{'parent_instance':'Foundation','parent_socket':'portal','child_instance':'Portal','child_socket':'root'},{'parent_instance':'Foundation','parent_socket':'housing','child_instance':'Housing','child_socket':'root'},{'parent_instance':'Housing','parent_socket':'service','child_instance':'Diagnostic','child_socket':'bottom'}]
bpy.context.scene.frame_end=1;bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
write(FOLDER/'assembly.json',{'schema':'MilitaryArmor.BlenderAuthoring/1','id':BID,'version':'1.0','title':a.title,'catalog_id':a.catalog_id,'catalog_grid':a.grid,'axes':AXES,'instances':a.instances,'connections':connections,'animations':[],'exports':[],'notes':'Compact garage node; Capacity512 means storage capacity, not ship count. No invented ship scale or animations.'})
bpy.ops.wm.save_as_mainfile(filepath=str(FOLDER/(BID+'.blend')))
preview(FOLDER,(0,0,.56),2.9,850)
write(FOLDER/'README.md',"""# MA-G01 — корабельный гараж 1×1

MilitaryArmor 1.3; garage-ship. Компактный защищённый гаражный узел: доковые направляющие, силовой портал с утопленным закрытым доступом, задний корпус с пониженной бронекрышей. Доступ обращён к -Y. Capacity512 — вместимость, не число кораблей. Масштаб кораблей и механика ворот не выдумывались.

Редактируемый MA-G01.blend; assembly.json — четыре стабильных экземпляра и три соединения. Три новые детали MA-G01-P01…P03, повторно использован MA-R01-P05 v1.0. composition-plan.md — выбор деталей; Previews/top.png и perspective.png — виды сверху и в объёме.

Процедурные PBR Armor/Ceramic/Titanium/Steel/Dark/Signal. Нет файловых текстур и UV-зависимости; эмиссия ограничена диагностикой. Статика, единичные масштабы, полные семантические sockets. Слои уплотнений и бронекожуха намеренно контактируют; портал накрывает переднюю кромку корпуса. Geometry gate каждой новой детали до сборки; независимое повторное открытие источников и сборки — validation.json.

BU условные, JSON — авторинг Blender. GLB не создавался. Игровая интеграция, коллайдеры и LOD не выполнялись.
""")
print('MA_G01_BUILT',flush=True)
'''
w(r/'Tools/build_MA_G01.py',head+func+body)
v=(r/'Tools/verify_MA_I01.py').read_text(encoding='utf8').replace('MA-I01','MA-G01').replace("'MA-F01-P01','MA-F01-P03',",'').replace("'cargo-2x1'","'garage-ship'").replace('==[2,1]','==[1,1]').replace('assert hi[0]-lo[0]>1.8*(hi[1]-lo[1])','assert abs((hi[0]-lo[0])-(hi[1]-lo[1]))<.05').replace('three reused sources','one reused source')
w(r/'Tools/verify_MA_G01.py',v)

