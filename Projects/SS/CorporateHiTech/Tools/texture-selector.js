import {T,loadJSON} from './model.js';
export async function initTextures(model){
 const base='../../Materials/SharedTexturesPreview/',catalog=await loadJSON(base+'catalog.json'),key='SS/CorporateHiTech/texture-selection/v1';
 const names={armor:'Броня',edge:'Металлические кромки',graphite:'Тёмный корпус',rubber:'Тёмные стыки'};
 let state={};try{state=JSON.parse(localStorage.getItem(key)||'{}');if(!state||typeof state!=='object'||Array.isArray(state))state={};}catch{state={};}
 const drawer=document.createElement('section');drawer.id='texture-drawer';drawer.hidden=true;
 drawer.innerHTML='<div class="texture-heading"><strong>SharedTextures</strong><button id="texture-close" aria-label="Закрыть выбор текстур">×</button></div><label for="texture-slot">Материал турели</label><select id="texture-slot"></select><div class="texture-filters"><select id="texture-group" aria-label="Набор текстур"><option value="">Все наборы</option></select><input id="texture-search" type="search" placeholder="Найти текстуру" aria-label="Найти текстуру"></div><div class="row"><button id="texture-clear">Без текстуры</button></div><label for="texture-scale">Масштаб рисунка <span id="texture-scale-label">1×</span></label><input id="texture-scale" type="range" min="0.25" max="8" step="0.25" value="1"><p id="texture-current" aria-live="polite"></p><div id="texture-count"></div><div id="texture-grid"></div><p class="texture-note">Выбор сохраняется в этом браузере.<br>Можно применить к сборке и отдельным деталям.</p>';
 document.body.append(drawer);
 const advanced=document.createElement('details');advanced.innerHTML='<summary>Рельеф поверхности</summary><label for="texture-normal">Сила рельефа <span id="texture-normal-label">0.4</span></label><input id="texture-normal" type="range" min="0" max="1" step="0.05" value="0.4"><label><input id="texture-normal-flip" type="checkbox" checked style="width:auto"> Инвертировать Y нормалей</label>';drawer.querySelector('#texture-current').before(advanced);
 const q=id=>document.getElementById(id),slot=q('texture-slot'),group=q('texture-group'),search=q('texture-search'),grid=q('texture-grid'),scale=q('texture-scale');
 for(const [id,name]of Object.entries(names)){const option=new Option(name,id);slot.add(option);}
 for(const name of [...new Set(catalog.entries.map(e=>e.group))])group.add(new Option(name,name));
 const toggle=document.createElement('button');toggle.id='texture-toggle';toggle.textContent='▦ Текстуры · '+catalog.entries.length;toggle.setAttribute('aria-expanded','false');q('part').after(toggle);
 function show(value){drawer.hidden=!value;toggle.setAttribute('aria-expanded',String(value));}
 toggle.onclick=()=>show(drawer.hidden);q('texture-close').onclick=()=>show(false);document.addEventListener('keydown',e=>{if(e.key==='Escape')show(false);});
 const lookup=new Map(catalog.entries.map(e=>[e.id,e])),textures=new Map(),tokens={},applied={};
 const originalRoughness=Object.fromEntries(Object.keys(names).map(id=>[id,model.mats[id].roughness]));
 function persist(){try{localStorage.setItem(key,JSON.stringify(state));}catch{}}
 function ui(){const current=state[slot.value],entry=lookup.get(current?.id);scale.value=current?.repeat||1;q('texture-scale-label').textContent=scale.value+'×';q('texture-normal').value=current?.normalStrength??.4;q('texture-normal-label').textContent=q('texture-normal').value;q('texture-normal-flip').checked=current?.flipY??true;q('texture-current').textContent=entry?entry.group+' / '+entry.name:'Исходный материал без текстуры';for(const tile of grid.children)tile.setAttribute('aria-pressed',String(tile.dataset.id===entry?.id));}
 function list(){grid.replaceChildren();const filtered=catalog.entries.filter(e=>(!group.value||e.group===group.value)&&(!search.value||(e.group+' '+e.name).toLowerCase().includes(search.value.toLowerCase())));q('texture-count').textContent=filtered.length+' из '+catalog.entries.length+' цветовых карт';for(const entry of filtered){const button=document.createElement('button');button.className='texture-tile';button.dataset.id=entry.id;button.title=entry.group+' / '+entry.name;const image=new Image();image.src=base+entry.thumbnail;image.alt='';image.loading='lazy';const name=document.createElement('span');name.textContent=entry.name;button.append(image,name);button.onclick=()=>apply(slot.value,entry.id,+scale.value).catch(report);grid.append(button);}ui();}
 function report(e){q('texture-current').textContent='Не удалось загрузить текстуру: '+e.message;}
 async function apply(materialId,id,repeat=1){
  if(!names[materialId])throw Error('Unknown material');const entry=lookup.get(id),token=(tokens[materialId]||0)+1;tokens[materialId]=token;
  const previous=state[materialId],normalStrength=previous?.normalStrength??.4,flipY=previous?.flipY??true;
  let next=[];if(entry){next=await Promise.all([entry.map,entry.normal,entry.roughness].map(async(file,i)=>{if(!file)return null;let pending=textures.get(file);if(!pending){pending=new T.TextureLoader().loadAsync(base+file);textures.set(file,pending);pending.catch(()=>textures.delete(file));}const original=await pending;const t=original.clone();t.colorSpace=i===0?T.SRGBColorSpace:T.NoColorSpace;t.wrapS=t.wrapT=T.RepeatWrapping;t.repeat.set(repeat,repeat);t.anisotropy=4;t.needsUpdate=true;return t;}));}
  if(tokens[materialId]!==token){next.forEach(t=>t?.dispose());return;}applied[materialId]?.forEach(t=>t?.dispose());applied[materialId]=next;const mat=model.mats[materialId];[mat.map,mat.normalMap,mat.roughnessMap]=[next[0]||null,next[1]||null,next[2]||null];mat.normalScale.set(normalStrength,flipY?-normalStrength:normalStrength);mat.roughness=mat.roughnessMap?1:originalRoughness[materialId];mat.needsUpdate=true;
  if(entry)state[materialId]={id,repeat,normalStrength,flipY};else delete state[materialId];persist();ui();return entry?.source||null;
 }
 q('texture-clear').onclick=()=>apply(slot.value,null).catch(report);slot.onchange=ui;group.onchange=list;search.oninput=list;
 scale.oninput=()=>{q('texture-scale-label').textContent=scale.value+'×';const current=state[slot.value];if(current){current.repeat=+scale.value;applied[slot.value]?.forEach(t=>t?.repeat.set(current.repeat,current.repeat));persist();}};
 function relief(){const current=state[slot.value];q('texture-normal-label').textContent=q('texture-normal').value;if(!current)return;current.normalStrength=+q('texture-normal').value;current.flipY=q('texture-normal-flip').checked;model.mats[slot.value].normalScale.set(current.normalStrength,current.flipY?-current.normalStrength:current.normalStrength);persist();}
 q('texture-normal').oninput=relief;q('texture-normal-flip').onchange=relief;
 list();for(const [id,choice]of Object.entries(state)){if(names[id]&&lookup.has(choice?.id))await apply(id,choice.id,T.MathUtils.clamp(+choice.repeat||1,.25,8));}
 window.textureSelection={catalog,apply,state,getApplied:()=>Object.fromEntries(Object.entries(applied).map(([id,maps])=>[id,maps.map(t=>t?{url:t.image?.src,repeat:t.repeat.toArray(),colorSpace:t.colorSpace}:null)])),show};
 if(new URLSearchParams(location.search).has('textures'))show(true);
}
