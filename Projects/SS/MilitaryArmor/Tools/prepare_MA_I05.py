from pathlib import Path
root=Path('D:/Codex/SpaceScrappers3D/Projects/SS/MilitaryArmor/Tools')
s=(root/'build_MA_I04.py').read_text(encoding='utf8').replace('MA-I04','MA-I05').replace('cargo-4x4','cargo-5x5').replace('4×4','5×5').replace('[4,4]','[5,5]')
s=s.replace("[('L',-1.68),('R',1.68)]", "[('L',-2.05),('R',2.05)]").replace('enumerate([-2.05,0,2.05])','enumerate([-3.075,-1.025,1.025,3.075])')
a=s.index(" write(folder/'composition-plan.md'");b=s.index(" if '--assembly-only'",a)
s=s[:a]+''' write(folder/'composition-plan.md','# MA-I05 — план до моделирования\\n\\nКаталог cargo-5x5: грузовой контейнер 5×5, visual-only без XML. Вместимость и механизмы не заданы. Семейство MA-I01 v2 / I02 / I03 / I04. Цельный корпус с двумя полосами по четыре загрузочных люка, широким приподнятым центральным силовым хребтом и диагональными боковыми контрфорсами. Узнаваемый грузовой объём, не батарейные кассеты.\\n\\nПовторно использовать MA-I01-R2-P02 v2.0 — 8 люков 2.87×1.29 BU; MA-I01-R2-P03 v2.0 — 4 направляющие 3.87 BU, по две на торец. Единичный масштаб; материалы, sockets и статика совместимы. Старые корпуса не подходят габаритами и посадками: создать MA-I05-P01 с корпусом 8.88×8.88 BU и новым силовым набором. Зазоры люков X=1.23, Y=0.76 BU.\\n\\n+Z вверх, -Y вперёд; BU условные, сетка не метры. Сначала отдельная деталь и geometry gate, затем сборка. Без анимаций/GLB/игровой интеграции.\\n')
''' +s[b:]
a=s.index("  p=Part(");b=s.index('  finish(p,sockets)',a)
s=s[:a]+'''  p=Part('MA-I05-P01','Цельный тяжёлый грузовой корпус с приподнятым хребтом')
  p.panel('Continuous heavy cargo hull',(0,0,1.18),(8.88,8.88,2.36),'Armor',.70,.022)
  p.panel('Continuous armored roof',(0,0,2.435),(8.54,8.50,.15),'Titanium',.50,.012)
  for k,x,y in HATCHES:p.panel('Wide loading aperture seal',(x,y,2.55),(3.03,1.45,.08),'Dark',.18,.008)
  p.panel('Raised central load distributing ridge',(0,0,2.69),(.78,8.16,.38),'Armor',.20,.015)
  p.panel('Continuous central protective crown',(0,0,2.90),(.90,7.80,.12),'Ceramic',.14,.010)
  for y in [-2.05,0,2.05]:
   for side in [-1,1]:p.panel('Roof transverse load tie',(side*2.11,y,2.56),(3.34,.22,.16),'Steel',.06,.009)
  for side in [-1,1]:
   p.panel('Cargo roof edge curb',(side*3.99,0,2.56),(.40,7.95,.22),'Ceramic',.11,.010)
   for y in [-3.55,-1.78,0,1.78,3.55]:
    o=p.box('Diagonal full height cargo buttress',(side*4.29,y,1.24),(.24,.38,2.50),'Titanium',.012);o.rotation_euler.y=side*.12
    p.panel('Buttress armored cap',(side*4.12,y,2.59),(.54,.50,.20),'Ceramic',.10,.010)
   p.box('Recessed long handling channel',(side*4.447,0,1.04),(.03,7.60,.27),'Dark',.005)
  for y in [-4.27,4.27]:
   p.panel('Heavy end sill',(0,y,.24),(8.58,.35,.40),'Titanium',.14,.012)
   p.box('Recessed end handling channel',(0,y*1.044,1.16),(7.40,.035,.35),'Dark',.005)
   for x in [-3.75,0,3.75]:p.panel('Vertical end load pillar',(x,y,1.38),(.42,.38,2.30),'Ceramic',.10,.012)
  sockets=[mount('root',(0,0,0),'MilitaryArmor.cargo.hull')]
  for k,x,y in HATCHES:sockets.append(mount('hatch'+k,(x,y,2.59),'MilitaryArmor.cargo.wide-hatch'))
  for side,x in [('L',-2.04),('R',2.04)]:
   for k,y in [('F',-4.46),('B',4.46)]:sockets.append(mount('rail'+side+k,(x,y,.18),'MilitaryArmor.cargo.rail'))
''' +s[b:]
s=s.replace('loc=(x,y,2.19)','loc=(x,y,2.59)')
a=s.index(" for k,y in [('F',-3.56)",s.index(' a=Assembly'));b=s.index(' bpy.context.view_layer.update();inspect()',a)
s=s[:a]+''' for side,x in [('L',-2.04),('R',2.04)]:
  for k,y in [('F',-4.46),('B',4.46)]:
   iid='CargoRail'+side+k;a.instance(iid,'MA-I01-R2-P03',loc=(x,y,.18));connections.append(dict(parent_instance='Structure',parent_socket='rail'+side+k,child_instance=iid,child_socket='root'))
''' +s[b:]
s=s.replace('preview(folder,(0,0,1.15),11.8,800,True)','preview(folder,(0,0,1.45),14.8,800,True)')
s=s.replace('двумя полосами по три люка, центральным силовым хребтом','двумя полосами по четыре люка, приподнятым силовым хребтом').replace('две полосы по три крупных загрузочных люка, центральный силовой хребет','две полосы по четыре крупных загрузочных люка, приподнятый силовой хребет').replace('9 экземпляров','13 экземпляров').replace('6 люков','8 люков').replace('2 направляющие','4 направляющие').replace('six access hatches','eight access hatches').replace('central spine','raised central spine')
s=s.replace('hatch_gap_x_BU=.49','hatch_gap_x_BU=1.23').replace('gasket_gap_x_BU=.33','gasket_gap_x_BU=1.07').replace('side_cap_to_hatch_clearance_BU=.075','side_cap_to_hatch_clearance_BU=.365').replace('roof_backbone_to_crossbrace_top_difference_BU=.025','roof_backbone_to_crossbrace_top_difference_BU=.32')
(root/'build_MA_I05.py').write_bytes(s.replace('\n','\r\n').encode('utf8'))
(root/'verify_MA_I05.py').write_bytes("import sys,runpy\r\nfrom pathlib import Path\r\nsys.argv.append('--verify')\r\nrunpy.run_path(str(Path(__file__).with_name('build_MA_I05.py')),run_name='__main__')\r\n".encode())