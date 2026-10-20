"""Shared Blender authoring helpers for the six final MilitaryArmor weapons."""
import bpy, bmesh, math, json, struct, tempfile
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
AXES={'handedness':'right','up':'+Z','forward':'-Y','units':'BU; physical scale unspecified'}

def write(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    text=data if isinstance(data,str) else json.dumps(data,ensure_ascii=False,indent=2)
    path.write_bytes((text.replace('\r\n','\n').rstrip()+'\n').replace('\n','\r\n').encode('utf8'))

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system='NONE'
    bpy.context.preferences.filepaths.save_version=0

def palette():
    result={}
    for name,col,metal,rough,power in [('Armor',(.095,.12,.145),.72,.37,0),('Ceramic',(.38,.43,.46),.38,.32,0),('Titanium',(.075,.105,.13),.84,.30,0),('Steel',(.24,.28,.31),.85,.30,0),('Dark',(.009,.015,.022),.4,.48,0),('Signal',(.015,.55,.78),.35,.25,2.5),('Optic',(.015,.18,.25),.65,.18,.7),('Warning',(.55,.26,.045),.3,.4,0)]:
        m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
        if power:p.inputs['Emission Color'].default_value=(*col,1);p.inputs['Emission Strength'].default_value=power
        result[name]=m
    return result

def outline(w,h,c):
    c=min(c,w*.35,h*.35)
    return [(-w/2+c,-h/2),(w/2-c,-h/2),(w/2,-h/2+c),(w/2,h/2-c),(w/2-c,h/2),(-w/2+c,h/2),(-w/2,h/2-c),(-w/2,-h/2+c)]

class Part:
    def __init__(self,pid,title,version='1.0'):
        reset();self.pid=pid;self.title=title;self.version=version;self.mats=palette();self.coll=bpy.data.collections.new(pid);bpy.context.scene.collection.children.link(self.coll)
    def finish(self,o,name,mat,bevel=.015):
        o.name=name
        for c in list(o.users_collection):c.objects.unlink(o)
        self.coll.objects.link(o);o.data.materials.append(self.mats[mat])
        if bevel:
            m=o.modifiers.new('Machined edges','BEVEL');m.width=bevel;m.segments=2;o.modifiers.new('Weighted planar normals','WEIGHTED_NORMAL')
        return o
    def mesh(self,name,verts,faces,mat='Armor',bevel=.015):
        data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
        bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
        return self.finish(bpy.data.objects.new(name,data),name,mat,bevel)
    def box(self,name,loc,size,mat='Armor',bevel=.025):
        bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return self.finish(o,name,mat,bevel)
    def cyl(self,name,loc,r,depth,mat='Titanium',axis='Z',verts=32):
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc);o=bpy.context.object
        if axis=='Y':o.rotation_euler.x=math.pi/2
        if axis=='X':o.rotation_euler.y=math.pi/2
        return self.finish(o,name,mat,.01)
    def ring(self,name,loc,outer,inner,depth,axis='Z',mat='Titanium',verts=32):
        n=verts;v=[];f=[]
        for z,r in [(-depth/2,outer),(depth/2,outer),(-depth/2,inner),(depth/2,inner)]:
            v.extend((r*math.cos(i*2*math.pi/n),r*math.sin(i*2*math.pi/n),z) for i in range(n))
        for i in range(n):
            j=(i+1)%n;f.extend([(i,j,n+j,n+i),(2*n+j,2*n+i,3*n+i,3*n+j),(n+i,n+j,3*n+j,3*n+i),(j,i,2*n+i,2*n+j)])
        o=self.mesh(name,v,f,mat,.006);o.location=loc
        if axis=='Y':o.rotation_euler.x=math.pi/2
        if axis=='X':o.rotation_euler.y=math.pi/2
        return o
    def slab(self,name,points,z,thick,mat='Armor',bevel=.015):
        n=len(points);v=[(x,y,z) for x,y in points]+[(x,y,z+thick) for x,y in points]
        return self.mesh(name,v,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mat,bevel)
    def panel(self,name,loc,size,mat='Armor',cut=.12,bevel=.015):
        x,y,z=loc;w,d,h=size;return self.slab(name,[(x+a,y+b) for a,b in outline(w,d,cut)],z-h/2,h,mat,bevel)
    def section(self,name,sections,mat='Armor',bevel=.015):
        v=[]
        for y,x,z,w,h,c in sections:v.extend((u+x,y,t+z) for u,t in outline(w,h,c))
        n=len(sections);f=[tuple(reversed(range(8))),tuple(range((n-1)*8,n*8))]
        for j in range(n-1):
            for i in range(8):k=(i+1)%8;f.append((8*j+i,8*j+k,8*(j+1)+k,8*(j+1)+i))
        return self.mesh(name,v,f,mat,bevel)
    section_body=section
    def stripe(self,name,a,b,width=.02,mat='Signal'):
        a,b=Vector(a),Vector(b);o=self.box(name,(a+b)/2,(width,width,(b-a).length),mat,.003);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
    def save(self,mounts=None,points=None,notes='',animations=None):
        mounts=mounts or [{'id':'root','role':'part-root','position':[0,0,0],'forward':[0,-1,0],'up':[0,0,1]}]
        for item in mounts:
            o=bpy.data.objects.new('socket.'+item['id'],None);self.coll.objects.link(o);o.location=item.get('position',[0,0,0]);o.empty_display_size=.08;o['socket_id']=item['id']
        bpy.context.view_layer.update();renderables=[o for o in self.coll.objects if o.type in ('MESH','CURVE','FONT')]
        pts=[o.matrix_world@Vector(v) for o in renderables for v in o.bound_box]
        materials=[];emission=[]
        for m in bpy.data.materials:
            regions=[o.name for o in renderables if m in list(o.data.materials)]
            if not regions:continue
            p=m.node_tree.nodes.get('Principled BSDF')
            materials.append({'id':m.name,'surfaces':regions,'base_color_linear':list(p.inputs['Base Color'].default_value),'metalness':p.inputs['Metallic'].default_value,'roughness':p.inputs['Roughness'].default_value,'texture_source':'uniform Blender PBR nodes; no file textures; no UV dependency'})
            if p.inputs['Emission Strength'].default_value>0:emission.append({'slot':m.name,'regions':regions,'color_linear':list(p.inputs['Emission Color'].default_value)[:3],'strength':p.inputs['Emission Strength'].default_value,'units':'Blender shader strength','default':'on'})
        folder=ROOT/'Parts'/self.pid;folder.mkdir(parents=True,exist_ok=True)
        data={'schema':'MilitaryArmor.BlenderAuthoring/1','id':self.pid,'version':self.version,'name':self.title,'source':self.pid+'.blend','axes':AXES,'origin':[0,0,0],'pivot':[0,0,0],'rest_pose':'identity','scale_policy':'unit only','bounds_local':{'min':[min(v[i] for v in pts) for i in range(3)],'max':[max(v[i] for v in pts) for i in range(3)]},'materials':materials,'emission':emission,'mounts':mounts,'functional_points':points or [],'attachment_areas':[],'animations':animations or [],'notes':notes}
        write(folder/'part.json',data);bpy.ops.wm.save_as_mainfile(filepath=str(folder/(self.pid+'.blend')));return self.pid

class Assembly:
    def __init__(self,bid,catalog_id,grid,title):
        reset();self.bid=bid;self.catalog_id=catalog_id;self.grid=grid;self.title=title;self.instances=[];self.nodes=[];self.loaded={};self.clips=[];self.root=self.node(bid)
    def node(self,name,parent=None,loc=(0,0,0),rot=(0,0,0)):
        o=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(o);o.parent=self.resolve(parent);o.location=loc;o.rotation_euler=rot;o.empty_display_size=.1;self.nodes.append(o);return o
    def resolve(self,obj):return bpy.data.objects[obj] if isinstance(obj,str) else obj
    def instance(self,iid,pid,parent=None,loc=(0,0,0),rot=(0,0,0)):
        data=json.loads((ROOT/'Parts'/pid/'part.json').read_text(encoding='utf8'))
        if pid not in self.loaded:
            with bpy.data.libraries.load(str(ROOT/'Parts'/pid/(pid+'.blend')),link=False) as (src,dst):dst.collections=[pid]
            self.loaded[pid]=dst.collections[0]
        n=self.node(iid,parent or self.root,loc,rot);n['part_id']=pid;n['part_version']=data['version'];copies={}
        for source in self.loaded[pid].objects:
            o=source.copy();o.name=iid+'::'+source.name;bpy.context.scene.collection.objects.link(o);copies[source]=o
        for source,o in copies.items():o.parent=copies.get(source.parent,n);o.matrix_basis=source.matrix_basis.copy()
        self.instances.append({'id':iid,'part_id':pid,'version':data['version'],'source':f'../../Parts/{pid}/{pid}.blend','parent':n.parent.name,'translation':list(loc),'rotation_euler_xyz':list(rot),'scale':[1,1,1]});return n
    def animate_rotation(self,node,axis,keys):
        o=self.resolve(node);idx='XYZ'.index(axis.upper())
        for frame,degrees in keys:o.rotation_euler[idx]=math.radians(degrees);o.keyframe_insert('rotation_euler',frame=frame)
        self.clips.append({'node':o.name,'channel':'rotation_euler','axis':axis,'units':'degrees','keys':keys})
    def animate_location(self,node,axis,keys):
        o=self.resolve(node);idx='XYZ'.index(axis.upper())
        for frame,value in keys:o.location[idx]=value;o.keyframe_insert('location',frame=frame)
        self.clips.append({'node':o.name,'channel':'location','axis':axis,'units':'BU','keys':keys})
    def save(self,notes='',frame_end=120):
        scene=bpy.context.scene;scene.frame_end=frame_end;scene.frame_set(1);bpy.context.view_layer.update()
        folder=ROOT/'Blocks'/self.bid;folder.mkdir(parents=True,exist_ok=True)
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type=='VIEW_3D':area.spaces.active.shading.type='MATERIAL'
        assembly={'schema':'MilitaryArmor.BlenderAuthoring/1','id':self.bid,'version':'1.0','title':self.title,'catalog_id':self.catalog_id,'catalog_grid':self.grid,'axes':AXES,'instances':self.instances,'nodes':[{'id':o.name,'parent':o.parent.name if o.parent else None,'translation':list(o.location),'rotation_euler_xyz':list(o.rotation_euler),'scale':list(o.scale)} for o in self.nodes],'animations':{'fps':scene.render.fps,'frame_range':[1,frame_end],'channels':self.clips,'demonstration_only':True,'interpolation':'Blender Bezier'},'exports':[f'Exports/{self.bid}.glb'],'notes':notes}
        write(folder/'assembly.json',assembly)
        bpy.ops.wm.save_as_mainfile(filepath=str(folder/(self.bid+'.blend')))
        export=folder/'Exports'/(self.bid+'.glb');export.parent.mkdir(exist_ok=True)
        bpy.ops.export_scene.gltf(filepath=str(export),export_format='GLB',export_apply=True,export_animations=True,export_extras=True,export_cameras=False,export_lights=False)
        raw=export.read_bytes();magic,ver,length=struct.unpack_from('<4sII',raw);chunk_len,chunk_type=struct.unpack_from('<II',raw,12);gltf=json.loads(raw[20:20+chunk_len].decode('utf8').rstrip())
        check={'id':self.bid,'source_saved':True,'source_parts_saved_before_assembly':True,'instance_count':len(self.instances),'resolved_parts':sorted(set(x['part_id'] for x in self.instances)),'missing_dependencies':[x['source'] for x in self.instances if not (folder/x['source']).resolve().exists()],'glb':{'magic':magic.decode(),'version':ver,'length_matches':length==len(raw),'mesh_count':len(gltf.get('meshes',[])),'node_count':len(gltf.get('nodes',[])),'animation_count':len(gltf.get('animations',[])),'embedded_buffers':all('uri' not in b for b in gltf.get('buffers',[])),'external_images':[i['uri'] for i in gltf.get('images',[]) if 'uri' in i]},'game_validation':False}
        check['checks_passed']=magic==b'glTF' and ver==2 and length==len(raw) and not check['missing_dependencies'] and check['glb']['mesh_count']>0 and not check['glb']['external_images'];write(folder/'validation.json',check);assert check['checks_passed'];return export
    def review(self,path=None,view=(8,-11,8),target=(0,-.5,1.5),scale=8,resolution=700):
        scene=bpy.context.scene;scene.frame_set(1);scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.resolution_x=resolution;scene.render.resolution_y=resolution;scene.render.resolution_percentage=100
        scene.world=bpy.data.worlds.new('Temporary review');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[1].default_value=.4
        bpy.ops.object.camera_add(location=view);o=bpy.context.object;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();o.data.type='ORTHO';o.data.ortho_scale=scale;scene.camera=o
        for loc,power,size in [((2,-5,9),1700,6),((-5,-1,5),1100,5),((3,5,7),2000,5)]:
            bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(path or Path(tempfile.gettempdir())/(self.bid+'-final-review.png'));bpy.ops.render.render(write_still=True);return scene.render.filepath
