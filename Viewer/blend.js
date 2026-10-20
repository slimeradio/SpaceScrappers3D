import * as T from './vendor/three.module.js';

export function evaluate(tree,variables){
 if(typeof tree==='number')return tree;
 const [op,...args]=tree;if(op==='var'){if(!(args[0] in variables))throw Error('Неизвестный параметр состояния');return variables[args[0]];}
 const a=args.map(x=>evaluate(x,variables));
 switch(op){case '+':return a[0]+a[1];case '-':return a[0]-a[1];case '*':return a[0]*a[1];case '/':return a[0]/a[1];case '**':return a[0]**a[1];case 'neg':return -a[0];case 'pos':return a[0];case 'sin':return Math.sin(a[0]);case 'cos':return Math.cos(a[0]);case 'min':return Math.min(...a);case 'max':return Math.max(...a);case 'abs':return Math.abs(a[0]);default:throw Error('Неизвестная операция состояния');}
}
function floats(encoded){const raw=atob(encoded),bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));return new Float32Array(bytes.buffer);}
const labels={power:'Питание',activity:'Рабочая нагрузка',fault:'Неисправность',heat:'Нагрев',deployment:'Раскрытие',fill:'Заполненность',flow:'Заряд / разряд',transmit:'Передача сигнала',cycle_turns:'Положение механизма',aim_yaw:'Поворот',aim_pitch:'Наклон',thrust_0:'Тяга сопла 1',thrust_1:'Тяга сопла 2',thrust_2:'Тяга сопла 3'};
const names={off:'Выключен',idle:'Ожидание',working:'Работает',hot_off:'Горячий, без питания',cold:'Холодный',hot:'Нагретый',closed:'Закрыт',opened:'Открыт',empty:'Пустой',full:'Полный',open:'Открытие',close:'Закрытие',work_loop:'Рабочий цикл',start:'Запуск механизма',stop:'Остановка механизма',activate:'Включение',deactivate:'Выключение',heat_up:'Нагрев',cool_down:'Остывание',fill:'Заполнение',fire:'Выстрел / пуск',beam_hold_loop:'Непрерывная работа'};
export function stateLabel(key){return names[key]||labels[key]||(key.startsWith('recoil_')?'Отдача':key);}

export async function buildBlend(config,partId){
 const response=await fetch(config.sceneURL||'/api/blend/'+encodeURIComponent(config.blend));
 const data=await response.json();if(!response.ok)throw Error(data.error||'Не удалось подготовить модель');
 const root=new T.Group(),objects={},nodes={},defs={},mats={},materialDefs={},geometries={};root.name=data.id;
 const proxy=new T.Object3D();proxy.name='StateControls';root.add(proxy);
 for(const [key,d]of Object.entries(data.controls))proxy[key]=d.default;
 for(const [id,d]of Object.entries(data.materials)){
  const mat=new T.MeshStandardMaterial({metalness:d.metalness,roughness:d.roughness,emissiveIntensity:d.intensity});mat.name=id;
  mat.color.fromArray(d.color);mat.emissive.fromArray(d.emissive);mats[id]=mat;
  const title={heat:'Тепловые поверхности',status:'Диагностика',thrust:'Рабочее сопло',optic:'Оптика',fill:'Индикатор заполнения',flow:'Поток энергии'}[d.title]||d.title;
  materialDefs[id]={title,color:'#'+mat.color.getHexString(),emissive:'#'+mat.emissive.getHexString(),roughness:d.roughness,metalness:d.metalness};
 }
 for(const [id,d]of Object.entries(data.geometries)){
  const g=new T.BufferGeometry();g.setAttribute('position',new T.BufferAttribute(floats(d.position),3));g.setAttribute('normal',new T.BufferAttribute(floats(d.normal),3));
  if(d.uv)g.setAttribute('uv',new T.BufferAttribute(floats(d.uv),2));
  else {const p=g.attributes.position,uv=new Float32Array(p.count*2);for(let j=0;j<p.count;j++){uv[j*2]=p.getX(j);uv[j*2+1]=p.getY(j);}g.setAttribute('uv',new T.BufferAttribute(uv,2));}
  for(const [start,count,mi]of d.groups)g.addGroup(start,count,mi);geometries[id]=g;
 }
 for(const d of data.nodes){const n=new T.Group();n.name=d.id;n.position.fromArray(d.position);n.quaternion.fromArray(d.quaternion);n.scale.fromArray(d.scale);n.userData.blenderEuler=[...d.euler];objects[d.id]=n;
  if(d.geometry){
   // One mesh per material keeps the existing selection and appearance editor compatible.
   const src=geometries[d.geometry];
   for(const g of src.groups){const geom=src.clone();geom.clearGroups();geom.setDrawRange(g.start,g.count);const mesh=new T.Mesh(geom,mats[d.materials[g.materialIndex]]);mesh.name=d.id;mesh.castShadow=true;mesh.receiveShadow=true;n.add(mesh);}
  }
 }
 for(const d of data.nodes)(objects[d.parent]||root).add(objects[d.id]);
 const instances=data.instances.length?data.instances:data.nodes.filter(d=>d.geometry).map(d=>({id:d.id,part_id:d.id}));
 const chosen=partId?instances.find(i=>(i.part_id||i.part)===partId):null;if(partId&&!chosen)throw Error('Деталь не найдена в исходнике');
 for(const i of instances){const pid=i.part_id||i.part;defs[pid]={id:pid,title:pid};const n=objects[i.id];if(n&&(!chosen||chosen.id===i.id)){n.userData.partId=pid;nodes[i.id]=n;}}
 if(chosen)root.traverse(n=>{if(!n.isMesh)return;let p=n.parent;while(p&&p!==root&&!nodes[p.name])p=p.parent;n.visible=!!p&&p!==root;});
 const targets=Object.fromEntries(Object.keys(mats).map(id=>[id,new Set()])),local=new Map();
 root.traverse(mesh=>{if(!mesh.isMesh)return;let owner=mesh.parent;while(owner&&owner!==root&&!nodes[owner.name])owner=owner.parent;const id=mesh.material.name,key=(owner?.name||'root')+':'+id;if(!local.has(key))local.set(key,mesh.material.clone());mesh.material=local.get(key);targets[id].add(mesh.material);});
 const value=b=>{const vars={};for(const [key,v]of Object.entries(b.variables))vars[key]='control' in v?proxy[v.control]:v.constant;const n=evaluate(b.expression,vars);if(!Number.isFinite(n))throw Error('Некорректное значение состояния');return n;};
 function apply(){
  const rotated=new Set();
  for(const b of data.motion){const n=objects[b.node];if(!n)continue;const v=value(b);if(b.path==='rotation_euler'){n.userData.blenderEuler[b.axis]=v;rotated.add(n);}else (b.path==='location'?n.position:n.scale).setComponent(b.axis,v);}
  for(const n of rotated)n.quaternion.setFromEuler(new T.Euler(...n.userData.blenderEuler,'ZYX'));
  for(const [id,d]of Object.entries(data.materials))for(const b of d.drivers){const v=value(b);for(const m of targets[id])if(b.field==='intensity')m.emissiveIntensity=Math.max(0,v);else m.emissive[['r','g','b'][b.axis]]=v;}
  root.updateMatrixWorld(true);
 }
 const used=new Set();function variables(tree,result){if(!Array.isArray(tree))return;if(tree[0]==='var')result.add(tree[1]);else for(const child of tree.slice(1))variables(child,result);}
 for(const binding of [...data.motion,...Object.values(data.materials).flatMap(m=>m.drivers)]){const referenced=new Set();variables(binding.expression,referenced);for(const key of referenced)if(binding.variables[key]?.control)used.add(binding.variables[key].control);}
 const clips=data.clips.filter(c=>c.tracks.some(t=>used.has(t.control))).map(c=>{const tracks=c.tracks.map(t=>new T.NumberKeyframeTrack(proxy.uuid+'.'+t.control,t.keys.map(k=>k[0]),t.keys.map(k=>k[1])));const clip=new T.AnimationClip(c.name,c.duration,tracks);clip.userData={loop:c.loop,state:true};return clip;});
 for(const c of data.pose_clips||[]){const tracks=c.tracks.map(t=>new (t.field==='quaternion'?T.QuaternionKeyframeTrack:T.VectorKeyframeTrack)(objects[t.node].uuid+'.'+t.field,t.times,t.values));const clip=new T.AnimationClip(c.name,c.duration,tracks);clip.userData={loop:true};clips.push(clip);}root.animations=clips;
 const runtime={data,proxy,apply,used,values:()=>Object.fromEntries(Object.keys(data.controls).map(k=>[k,proxy[k]])),set(patch){for(const [key,val]of Object.entries(patch)){const d=data.controls[key];if(d)proxy[key]=Math.max(d.min,Math.min(d.max,Number(val)));}apply();}};
 apply();return {root,nodes,defs,mats,materialDefs,assembly:{id:data.id},partId,stateRuntime:runtime};
}

export function statesUI(model,q,beforeChange,onPreset){
 const runtime=model.stateRuntime,section=q('block-states');if(!runtime){section.hidden=true;return {sync(){}};}
 const {data}=runtime;section.hidden=false;const fields=[];
 if(!Object.keys(data.controls).length){q('state-note').textContent=data.static_reason?'Статичный блок: рабочие движения не требуются.':'В файле нет отдельных контролов состояний.';return {sync(){}};}
 q('state-note').textContent=runtime.used.has('heat')?'Нагрев сохраняется независимо от питания.':runtime.used.has('fill')?'Заполненность сохраняется независимо от питания.':'Рабочую нагрузку можно менять отдельно от питания.';
 for(const [key,patch]of Object.entries(data.presets)){
  if(!Object.keys(patch).some(k=>runtime.used.has(k))&&key!=='off')continue;
  const button=document.createElement('button');button.textContent=stateLabel(key);button.onclick=()=>{beforeChange(patch);runtime.set(patch);onPreset?.(key);sync();};q('state-presets').append(button);
 }
 for(const [key,d]of Object.entries(data.controls)){
  if(key!=='power'&&!runtime.used.has(key))continue;
  const label=document.createElement('label'),out=document.createElement('output'),input=document.createElement('input');label.textContent=(labels[key]||stateLabel(key))+' ';label.htmlFor='state-'+key;label.append(out);
  input.id='state-'+key;input.type='range';input.min=key==='cycle_turns'?0:d.min;input.max=key==='cycle_turns'?1:d.max;input.step=key==='power'||key==='fault'||key==='transmit'?1:key.startsWith('aim_')?.1:.001;
  input.oninput=()=>{const patch={[key]:+input.value};beforeChange(patch);runtime.set(patch);sync();};q('state-controls').append(label,input);fields.push({key,input,out});
 }
 function sync(){for(const {key,input,out}of fields){const v=runtime.proxy[key];input.value=key==='cycle_turns'?v%1:v;out.textContent=key.startsWith('aim_')?v.toFixed(1)+'°':Math.round((key==='cycle_turns'?v%1:v)*100)+'%';}}
 sync();return {sync};
}
