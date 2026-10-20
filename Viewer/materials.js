import {T,json,modelMeshes} from './model.js';
export async function materialsUI(model,config,q){
 const key='SpaceScrappers3D/appearance/v1/'+config.id+'/'+(model.partId||'assembly');
 let state={};try{const saved=JSON.parse(localStorage.getItem(key)||'{}');if(saved&&typeof saved==='object'&&!Array.isArray(saved))state=saved;}catch{}
 let catalog={entries:[]};const catalogURL=new URL(config.textures||'./',location.href);
 if(config.textures)try{catalog=await json(catalogURL);}catch(e){q('error').textContent='Библиотека текстур недоступна: '+e.message;}
 const lookup=new Map(catalog.entries.map(e=>[e.id,e])),cache=new Map(),tokens=new WeakMap();
 const all=modelMeshes(model),originals=new Map(all.map(({mesh})=>[mesh.material,mesh.material.clone()]));
 const unique=(items)=>[...new Set(items.map(x=>x.mesh.material))];
 function selected(){return unique(all.filter(x=>x.mesh.material.name===q('material').value&&(q('scope').value==='all'||x.id===q('instance').value)));}
 function save(){try{localStorage.setItem(key,JSON.stringify(state));}catch{q('status').textContent='Память браузера недоступна. Скачайте JSON для сохранения.';}}
 function base(id){const d=model.materialDefs[id];return {color:d.color||'#ffffff',emissive:d.emissive||'#000000',roughness:d.roughness??1,metalness:d.metalness??0,texture:null,repeat:1};}
 function choice(id,material){return {...base(material),...state['all:'+material],...state[id+':'+material]};}
 async function apply(mat,value){
  const token={};tokens.set(mat,token);const original=originals.get(mat);let map=original?.map?.clone()||null;
  if(value.texture==='none'){map?.dispose();map=null;}
  else if(value.texture){map?.dispose();const entry=lookup.get(value.texture);if(!entry)throw Error('Текстура не найдена: '+value.texture);let pending=cache.get(entry.id);if(!pending){pending=new T.TextureLoader().loadAsync(new URL(entry.map,catalogURL).href);cache.set(entry.id,pending);pending.catch(()=>cache.delete(entry.id));}const source=await pending;if(tokens.get(mat)!==token)return;map=source.clone();map.colorSpace=T.SRGBColorSpace;map.wrapS=map.wrapT=T.RepeatWrapping;map.anisotropy=4;map.needsUpdate=true;}
  if(map)map.repeat.set(value.repeat,value.repeat);
  if(tokens.get(mat)!==token){map?.dispose();return;}mat.map?.dispose();mat.map=map;mat.userData.textureId=value.texture;mat.color.set(value.color);mat.emissive.set(value.emissive);mat.roughness=value.roughness;mat.metalness=value.metalness;mat.needsUpdate=true;
 }
 async function restore(){await Promise.all(all.map(({id,mesh})=>apply(mesh.material,choice(id,mesh.material.name))));}
 function report(e){q('error').textContent=e.message;}
 function sync(){const previous=q('material').value,names=[...new Set(all.filter(x=>q('scope').value==='all'||x.id===q('instance').value).map(x=>x.mesh.material.name))];q('material').replaceChildren(...names.map(id=>new Option(model.materialDefs[id].title||id,id)));if(names.includes(previous))q('material').value=previous;const mat=selected()[0];for(const id of ['color','emissive','roughness','metalness','repeat','clear-texture','reset-material','textures'])q(id).disabled=!mat;if(!mat)return;const controlled=model.stateRuntime?.data.materials[mat.name]?.drivers.some(d=>d.field==='emissive');q('emissive').disabled=!!controlled;q('emissive').title=controlled?'Цвет свечения задаётся состоянием блока':'';for(const id of ['color','emissive'])q(id).value='#'+mat[id].getHexString();for(const id of ['roughness','metalness'])q(id).value=mat[id];q('repeat').value=mat.map?.repeat.x||1;}
 async function change(patch,reset=false){
  const material=q('material').value,local=q('scope').value==='instance',id=q('instance').value;if(local&&!id)return;
  const targets=all.filter(x=>x.mesh.material.name===material&&(!local||x.id===id));
  const first=targets[0];if(!first)return;const mat=first.mesh.material;
  const current=choice(first.id,material);
  if(!local)for(const name of Object.keys(state))if(name.endsWith(':'+material))delete state[name];
  const value=reset?base(material):{...current,...patch};state[(local?id:'all')+':'+material]=value;
  save();await Promise.all(unique(targets).map(mat=>apply(mat,value)));sync();
 }
 for(const id of Object.keys(model.materialDefs))q('material').add(new Option(id,id));
 for(const id of ['color','emissive','roughness','metalness','repeat'])q(id).oninput=()=>change({[id]:['color','emissive'].includes(id)?q(id).value:+q(id).value}).catch(report);
 q('clear-texture').onclick=()=>change({texture:'none'}).catch(report);q('reset-material').onclick=()=>change({},true).catch(report);q('scope').onchange=sync;q('material').onchange=sync;
 function list(){q('texture-grid').replaceChildren();const entries=catalog.entries.filter(e=>(!q('texture-group').value||e.group===q('texture-group').value)&&(e.group+' '+e.name).toLowerCase().includes(q('texture-search').value.toLowerCase()));q('texture-count').textContent=entries.length+' / '+catalog.entries.length;for(const entry of entries){const button=document.createElement('button');button.className='texture-tile';button.title=entry.group+' / '+entry.name;const image=new Image();image.src=new URL(entry.thumbnail,catalogURL);image.loading='lazy';image.alt='';const label=document.createElement('span');label.textContent=entry.name;button.append(image,label);button.onclick=()=>change({texture:entry.id}).catch(report);q('texture-grid').append(button);}}
 for(const group of new Set(catalog.entries.map(e=>e.group)))q('texture-group').add(new Option(group,group));q('texture-group').onchange=list;q('texture-search').oninput=list;q('textures').onclick=()=>q('texture-drawer').hidden=false;q('close-textures').onclick=()=>q('texture-drawer').hidden=true;
 await restore();for(const {id,mesh}of all)mesh.material.userData.textureId=choice(id,mesh.material.name).texture;
 sync();list();
 return {sync,state:()=>state,async import(data){
  if(data.schema!=='SpaceScrappers3D/appearance/1'||data.block!==config.id||data.part!==(model.partId||null))throw Error('JSON предназначен для другой модели или детали');
  if(!data.materials||typeof data.materials!=='object'||Array.isArray(data.materials))throw Error('Неверный список материалов');
  for(const [key,v]of Object.entries(data.materials)){const split=key.lastIndexOf(':'),node=key.slice(0,split),material=key.slice(split+1);if(!(node==='all'||model.nodes[node])||!model.materialDefs[material]||!v||!/^#[0-9a-f]{6}$/i.test(v.color)||!/^#[0-9a-f]{6}$/i.test(v.emissive)||![v.roughness,v.metalness].every(x=>Number.isFinite(x)&&x>=0&&x<=1)||!Number.isFinite(v.repeat)||v.repeat<.25||v.repeat>8||(v.texture!==null&&v.texture!=='none'&&!lookup.has(v.texture)))throw Error('Неверный материал: '+key);}
  state=structuredClone(data.materials);await restore();for(const {id,mesh}of all)mesh.material.userData.textureId=choice(id,mesh.material.name).texture;save();sync();
 }};
}
