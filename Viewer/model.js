import {T,makePart} from './geometry.js';
export {T};
export async function json(url){const response=await fetch(url);if(!response.ok)throw Error(`${url}: HTTP ${response.status}`);return response.json();}
export async function build(config,partId){
 if(config.blend||config.sceneURL){const {buildBlend}=await import('./blend.js');return buildBlend(config,partId);}
 if(config.imported)return buildImported(config,partId);
 if(config.glb)return buildGLB(config,partId);
 const assemblyURL=new URL(config.assembly,location.href),assembly=await json(assemblyURL),materialDefs=await json(new URL(config.materials,location.href));
 const mats=Object.fromEntries(Object.entries(materialDefs).map(([id,def])=>[id,new T.MeshStandardMaterial({...def,name:id})]));
 const root=new T.Group(),nodes={},defs={};root.name=assembly.id;
 for(const instance of assembly.instances){if(!defs[instance.partId])defs[instance.partId]=await json(new URL(instance.source,assemblyURL));}
 if(partId&&!defs[partId])throw Error('Неизвестная деталь: '+partId);
 const instances=partId?[{id:partId,partId,translation:[0,0,0],rotationEulerXYZ:[0,0,0],scale:[1,1,1]}]:assembly.instances;
 for(const i of instances){const node=makePart(defs[i.partId],mats);node.name=i.id;node.position.fromArray(i.translation);node.rotation.set(...i.rotationEulerXYZ);node.scale.fromArray(i.scale);nodes[i.id]=node;}
 for(const i of instances){if(i.parent&&!nodes[i.parent])throw Error('Не найден родитель: '+i.parent);(i.parent?nodes[i.parent]:root).add(nodes[i.id]);}
 // Each instance owns its materials; local paint never changes its sibling.
 for(const node of Object.values(nodes)){const local=new Map();for(const mesh of node.children){if(!mesh.isMesh)continue;const id=mesh.material.name;if(!local.has(id))local.set(id,mesh.material.clone());mesh.material=local.get(id);}}
 const clips=[];
 for(const a of (partId?defs[partId].animations:assembly.animations)||[]){
  const node=nodes[a.node]||(partId?nodes[partId]:null);if(!node||!a.axis||!a.rangeDegrees||!(a.durationSeconds>0))continue;
  const axis=new T.Vector3(...a.axis).normalize(),times=[],values=[],rest=node.quaternion.clone();
  for(let k=0;k<=16;k++){times.push(a.durationSeconds*k/16);const angle=T.MathUtils.degToRad(T.MathUtils.lerp(...a.rangeDegrees,k/16));values.push(...rest.clone().multiply(new T.Quaternion().setFromAxisAngle(axis,angle)).toArray());}
  const clip=new T.AnimationClip(a.id,a.durationSeconds,[new T.QuaternionKeyframeTrack(node.name+'.quaternion',times,values)]);clip.userData={loop:a.loop!==false};clips.push(clip);
 }
 root.animations=clips;return {root,nodes,defs,mats,assembly,materialDefs,partId};
}

async function buildImported(config,partId){
 const {GLTFLoader}=await import('./vendor/GLTFLoader.js');
 const gltf=await new GLTFLoader().loadAsync(new URL(config.glb,location.href).href),root=new T.Group(),nodes={},defs={},mats={},materialDefs={};
 root.name=config.title;root.rotation.x=Math.PI/2;root.add(gltf.scene);root.animations=gltf.animations;
 const geometry=[];gltf.scene.traverse(node=>{if(node.isMesh)geometry.push(node);});if(!geometry.length)throw Error('Файл не содержит видимой геометрии.');
 const originals=new Map();
 for(const [index,mesh]of geometry.entries()){
  const id='node-'+index,title=mesh.userData.name||mesh.name||'Объект '+(index+1),owner=new T.Group();owner.name='__viewer_'+id;owner.userData.partId=id;
  mesh.parent.add(owner);owner.add(mesh);defs[id]={id,title};
  if(partId&&id!==partId){mesh.visible=false;continue;}nodes[id]=owner;
  const materialList=Array.isArray(mesh.material)?mesh.material:[mesh.material];
  const cloned=materialList.map(original=>{
   if(!originals.has(original))originals.set(original,'material-'+originals.size);
   const name=originals.get(original),mat=original.isMeshStandardMaterial?original.clone():new T.MeshStandardMaterial({color:original.color,map:original.map,transparent:original.transparent,opacity:original.opacity,side:original.side,alphaTest:original.alphaTest});mat.name=name;
   if(!materialDefs[name]){materialDefs[name]={title:original.name||name,color:'#'+mat.color.getHexString(),emissive:'#'+(mat.emissive?.getHexString()||'000000'),roughness:mat.roughness??1,metalness:mat.metalness??0};mats[name]=original.clone();}
   return mat;
  });
  if(cloned.length!==1)throw Error('GLB содержит неподдерживаемый набор материалов на одном примитиве.');
  mesh.material=cloned[0];ensureUV(mesh.geometry);mesh.castShadow=true;mesh.receiveShadow=true;
 }
 if(partId&&!defs[partId])throw Error('Объект не найден в файле.');
 const model={root,nodes,defs,mats,materialDefs,assembly:{id:config.title},partId};root.updateMatrixWorld(true);return model;
}

export function modelMeshes(model){
 const owners=new Map(Object.entries(model.nodes).map(([id,node])=>[node,id])),result=[];
 model.root.traverse(mesh=>{if(!mesh.isMesh)return;let owner=mesh.parent;while(owner&&!owners.has(owner))owner=owner.parent;if(owners.has(owner))result.push({id:owners.get(owner),mesh});});return result;
}

async function buildGLB(config,partId){
 const {GLTFLoader}=await import('./vendor/GLTFLoader.js');
 const assembly=await json(new URL(config.assembly,location.href)),defs={},nodes={},materialDefs={},mats={};
 for(const part of config.parts){const def=await json(new URL(part.metadata,location.href));defs[part.id]={...def,title:def.title||def.name||part.id};}
 const part=partId&&config.parts.find(p=>p.id===partId);if(partId&&!part)throw Error('Неизвестная деталь: '+partId);
 const gltf=await new GLTFLoader().loadAsync(new URL(part?part.glb:config.glb,location.href).href);
 const root=new T.Group();root.name=assembly.id;root.rotation.x=Math.PI/2;root.add(gltf.scene);root.animations=gltf.animations;
 function find(name){let found;gltf.scene.traverse(node=>{if(node.name===name||node.userData.name===name)found=node;});return found;}
 if(part){const owner=new T.Group();owner.name=part.id;owner.userData.partId=part.id;gltf.scene.add(owner);for(const node of [...gltf.scene.children])if(node!==owner)owner.add(node);nodes[part.id]=owner;}
 else for(const i of assembly.instances){const id=i.part_id||i.part;if(!defs[id])continue;const node=find(i.id);if(!node)throw Error('Экземпляр отсутствует в glTF: '+i.id);node.userData.partId=id;nodes[i.id]=node;}
 const model={root,nodes,defs,mats,assembly,materialDefs,partId};
 // Studio meshes outside declared part instances never belong to the asset.
 const owned=new Set(modelMeshes(model).map(({mesh})=>mesh)),unowned=[];root.traverse(node=>{if(node.isMesh&&!owned.has(node))unowned.push(node);});for(const node of unowned)node.removeFromParent();
 const local=new Map();for(const {id,mesh}of modelMeshes(model)){
  if(Array.isArray(mesh.material))throw Error('Ожидался отдельный материал glTF-примитива');
  const original=mesh.material,name=original.name||'material';const key=id+':'+name;
  if(!local.has(key))local.set(key,original.clone());mesh.material=local.get(key);
  if(!materialDefs[name]){materialDefs[name]={color:'#'+original.color.getHexString(),emissive:'#'+original.emissive.getHexString(),roughness:original.roughness,metalness:original.metalness};mats[name]=original.clone();}
  ensureUV(mesh.geometry);
  mesh.castShadow=true;mesh.receiveShadow=true;
 }
 root.updateMatrixWorld(true);return model;
}

function ensureUV(geometry){
 if(geometry.attributes.uv)return;
 if(!geometry.attributes.normal)geometry.computeVertexNormals();
 const pos=geometry.attributes.position,norm=geometry.attributes.normal,uv=new Float32Array(pos.count*2);
 for(let j=0;j<pos.count;j++){const nx=Math.abs(norm.getX(j)),ny=Math.abs(norm.getY(j)),nz=Math.abs(norm.getZ(j));uv[j*2]=nz>=nx&&nz>=ny?pos.getX(j):ny>=nx?pos.getX(j):pos.getY(j);uv[j*2+1]=nz>=nx&&nz>=ny?pos.getY(j):pos.getZ(j);}
 geometry.setAttribute('uv',new T.BufferAttribute(uv,2));
}
