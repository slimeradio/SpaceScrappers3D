import {T,json,build,modelMeshes} from './model.js';
import {materialsUI} from './materials.js';
import {cameraMovement} from './movement.js';
import {importUI} from './import.js';
import {statesUI,stateLabel} from './blend.js';
const q=id=>document.getElementById(id),params=new URLSearchParams(location.search);
function error(e){q('error').textContent=e.message||String(e);console.error(e);}
importUI();
try{
 const catalog=await json('/api/catalog');let imported;
 if(params.has('import')){const metadata=await json('/api/imports/'+encodeURIComponent(params.get('import')));imported={id:'Imported/File/'+metadata.id,title:metadata.name,style:'Открытый файл',project:'Файлы',styleName:metadata.format==='blend'?'Blender':'GLB',glb:metadata.url,imported:true,textures:'SharedTextures/Preview/catalog.json'};catalog.blocks.push(imported);q('import-status').textContent=metadata.format==='blend'?'Открыта копия blend. Процедурные шейдеры представлены базовыми PBR-материалами.':'Открыт GLB. Исходный файл не изменяется.';}
 if(imported&&params.has('import')){const metadata=await json('/api/imports/'+encodeURIComponent(params.get('import')));if(metadata.scene){imported.sceneURL=metadata.url;delete imported.glb;}}
 const config=imported||catalog.blocks.find(b=>b.id===params.get('block'))||catalog.blocks.find(b=>b.blend==='MA-H01')||catalog.blocks[0];if(!config)throw Error('Каталог блоков пуст');
 const projectOf=b=>b.project||b.id.split('/')[0],styleOf=b=>b.styleName||b.id.split('/')[1];
 for(const project of new Set(catalog.blocks.map(projectOf)))q('project').add(new Option(project,project));q('project').value=projectOf(config);
 function styles(selected){q('style').replaceChildren();for(const style of new Set(catalog.blocks.filter(b=>projectOf(b)===q('project').value).map(styleOf)))q('style').add(new Option(style,style));if(selected)q('style').value=selected;}
 function blocks(selected){q('block').replaceChildren();for(const block of catalog.blocks.filter(b=>projectOf(b)===q('project').value&&styleOf(b)===q('style').value))q('block').add(new Option(block.title,block.id));if(selected)q('block').value=selected;}
 styles(styleOf(config));blocks(config.id);
 function navigate(part=''){const url=new URL(location.href);url.searchParams.set('block',q('block').value);if(imported&&q('block').value===imported.id)url.searchParams.set('import',params.get('import'));else url.searchParams.delete('import');if(part)url.searchParams.set('part',part);else url.searchParams.delete('part');location.href=url;}
 q('block').onchange=()=>navigate();q('part').onchange=()=>navigate(q('part').value);
 q('project').onchange=()=>{styles();blocks();navigate();};q('style').onchange=()=>{blocks();navigate();};
 if(config.blend||config.sceneURL)q('import-status').textContent='Подготовка Blender-модели и состояний… При первом открытии потребуется несколько секунд.';
 const model=await build(config,params.get('part'));window.asset=model;
 if(model.stateRuntime){q('import-status').textContent='Открыт текущий Blender-исходник. Анимации и состояния доступны ниже.';q('save-notice').textContent='JSON сохраняет оформление. Экспорт модели сохраняет текущую позу; управляемые анимации и состояния остаются в Blender-исходнике.';}
 for(const [id,def]of Object.entries(model.defs))q('part').add(new Option(id+' · '+def.title,id));q('part').value=model.partId||'';
 q('title').textContent=model.partId?model.defs[model.partId].title:config.title;q('context').textContent=config.style+' / '+(model.partId||model.assembly.id);
 for(const [id,node]of Object.entries(model.nodes))q('instance').add(new Option(id+' · '+model.defs[node.userData.partId].title,id));
 const viewport=q('viewport'),scene=new T.Scene();scene.background=new T.Color('#0d1c28');
 const camera=new T.PerspectiveCamera(32,1,.01,1000);camera.up.set(0,0,1);
 const renderer=new T.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.35;viewport.append(renderer.domElement);
 scene.add(new T.HemisphereLight('#d1e9ff','#283843',2));
 for(const [color,intensity,pos]of [['#fff6eb',4,[-3,2,6]],['#a3d9ff',2,[3,-3,4]]]){const light=new T.DirectionalLight(color,intensity);light.position.set(...pos);light.castShadow=true;light.shadow.mapSize.set(2048,2048);Object.assign(light.shadow.camera,{left:-4,right:4,top:4,bottom:-4,near:.1,far:20});light.shadow.bias=-.00015;light.shadow.normalBias=.014;scene.add(light);}
 scene.add(model.root);const grid=new T.GridHelper(16,32,'#254455','#1b3341');grid.rotation.x=Math.PI/2;scene.add(grid);
 let az=.68,el=.64,distance=4.7,isolated=false,playing=false,last=performance.now(),action=null;
 const target=new T.Vector3(),rest=new Map(Object.values(model.nodes).map(n=>[n,n.position.clone()]));
 function visibleMeshes(){const result=[];model.root.traverseVisible(n=>{if(n.isMesh)result.push(n);});return result;}
 function frame(){model.root.updateMatrixWorld(true);const box=new T.Box3();for(const mesh of visibleMeshes()){mesh.geometry.computeBoundingBox();box.union(mesh.geometry.boundingBox.clone().applyMatrix4(mesh.matrixWorld));}if(box.isEmpty())return;box.getCenter(target);const size=box.getSize(new T.Vector3());const angle=2*Math.atan(Math.tan(T.MathUtils.degToRad(camera.fov/2))*Math.min(camera.aspect,1));distance=Math.max(size.length()/(2*Math.sin(angle/2))*1.15,.3);grid.position.z=box.min.z-.015;}
 const appearance=await materialsUI(model,config,q),meshes=modelMeshes(model),ownerOf=new Map(meshes.map(({id,mesh})=>[mesh,id]));
 function selection(){const id=q('instance').value;for(const {id:nodeId,mesh}of meshes)mesh.visible=!isolated||!id||nodeId===id;q('isolate').disabled=!id;q('isolate').setAttribute('aria-pressed',String(isolated&&!!id));q('selection').textContent=id?id+' · '+model.defs[model.nodes[id].userData.partId].title:Object.keys(model.nodes).length+' экземпляров / '+Object.keys(model.defs).length+' деталей';appearance.sync();}
 q('instance').onchange=()=>{selection();if(isolated)frame();};q('isolate').onclick=()=>{isolated=!isolated;selection();frame();};q('frame').onclick=frame;
 q('iso').onclick=()=>{az=.68;el=.64;frame();};q('top').onclick=()=>{az=0;el=Math.PI/2-.001;frame();};q('bottom').onclick=()=>{az=0;el=-Math.PI/2+.001;frame();};
 q('explode').oninput=()=>{const amount=+q('explode').value;for(const [index,node]of Object.values(model.nodes).entries()){node.position.copy(rest.get(node));if(node.parent!==model.root){const direction=rest.get(node).clone();if(direction.length()<.01)direction.set(0,0,.3);direction.normalize();node.position.addScaledVector(direction,amount*(.25+index*.025));}}q('explode-label').textContent=Math.round(amount*100)+'%';frame();};
 const mixer=new T.AnimationMixer(model.root);
 for(const clip of model.root.animations)q('animation').add(new Option(model.stateRuntime?stateLabel(clip.name):clip.name,clip.name));
 function updatePlay(){q('play').textContent=playing?'Ⅱ Пауза':'▶ Запустить';}
 function releaseState(patch){const tracks=action?.getClip().tracks||[],fields=tracks.map(t=>t.name.split('.').at(-1));if(action&&!fields.some(k=>k in patch)&&!(patch.power===0&&fields.some(k=>k==='cycle_turns'||k==='deployment'||k.startsWith('aim_'))))return;const snapshot=model.stateRuntime?.values();mixer.stopAllAction();if(snapshot)model.stateRuntime.set(snapshot);action=null;playing=false;updatePlay();}
 const stateUI=statesUI(model,q,releaseState,key=>{if(key==='working'&&model.root.animations.some(c=>c.name==='work_loop')){q('animation').value='work_loop';selectAnimation();playing=true;action.paused=false;updatePlay();}});
 function selectAnimation(){const snapshot=model.stateRuntime?.values();action?.stop();if(snapshot)model.stateRuntime.set(snapshot);let clip=model.root.animations.find(a=>a.name===q('animation').value);if(!clip)return;
  if(model.stateRuntime){const properties=clip.userData;clip=clip.clone();clip.userData=properties;for(const track of clip.tracks)if(track.name.endsWith('.cycle_turns')){const offset=model.stateRuntime.proxy.cycle_turns-track.values[0];for(let i=0;i<track.values.length;i++)track.values[i]+=offset;}}
  action=mixer.clipAction(clip);const loop=clip.userData?.loop!==false;action.setLoop(loop?T.LoopRepeat:T.LoopOnce,loop?Infinity:1);action.clampWhenFinished=true;action.play();action.paused=true;q('time').max=clip.duration;q('time').value=0;mixer.update(0);model.stateRuntime?.apply();stateUI.sync();playing=false;updatePlay();}
 q('animation').onchange=selectAnimation;
 for(const id of ['animation','play','stop','time','speed'])q(id).disabled=!model.root.animations.length;
 if(!model.root.animations.length)q('animation').add(new Option('У этой детали нет анимаций',''));
 q('play').onclick=()=>{if(!action)selectAnimation();if(!action)return;if(!playing&&action.time>=action.getClip().duration)action.reset().play();playing=!playing;action.paused=!playing;updatePlay();};
 q('stop').onclick=()=>{if(!action)return;playing=false;action.reset().play();action.paused=true;mixer.update(0);q('time').value=0;updatePlay();};
 q('time').oninput=()=>{if(!action)return;playing=false;action.paused=true;action.time=+q('time').value;mixer.update(0);updatePlay();};mixer.addEventListener('finished',()=>{playing=false;updatePlay();});if(!model.stateRuntime||!Object.keys(model.stateRuntime.data.controls).length)selectAnimation();
 function download(name,value,type){const url=URL.createObjectURL(new Blob([value],{type})),link=document.createElement('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
 q('save').onclick=()=>download((model.partId||model.assembly.id)+'-appearance.json',JSON.stringify({schema:'SpaceScrappers3D/appearance/1',block:config.id,part:model.partId||null,materials:appearance.state()},null,2).replace(/\n/g,'\r\n'),'application/json');
 q('load').onclick=()=>q('preset-file').click();q('preset-file').onchange=async()=>{try{const file=q('preset-file').files[0];if(file){await appearance.import(JSON.parse(await file.text()));q('status').textContent='Оформление загружено';}}catch(e){error(e);}finally{q('preset-file').value='';}};
 window.exportGLTF=async(binary=false)=>{const {GLTFExporter}=await import('./vendor/GLTFExporter.js');const exportRoot=new T.Group();exportRoot.name='Z-up_to_glTF_Y-up';exportRoot.rotation.x=-Math.PI/2;exportRoot.add(model.root.clone(true));return new GLTFExporter().parseAsync(exportRoot,{animations:model.stateRuntime?[]:model.root.animations,binary,onlyVisible:true});};
 q('export').onclick=async()=>{try{q('export').disabled=true;download((model.partId||model.assembly.id)+'.gltf',JSON.stringify(await window.exportGLTF()),'model/gltf+json');q('status').textContent='glTF экспортирован';}catch(e){error(e);}finally{q('export').disabled=false;}};
 q('export-glb').onclick=async()=>{try{q('export-glb').disabled=true;download((model.partId||model.assembly.id).replace(/\.(blend|glb)$/i,'')+'.glb',await window.exportGLTF(true),'model/gltf-binary');q('status').textContent='GLB экспортирован';}catch(e){error(e);}finally{q('export-glb').disabled=false;}};
 let down=null;const raycaster=new T.Raycaster();renderer.domElement.onpointerdown=e=>{down={x:e.clientX,y:e.clientY,lastX:e.clientX,lastY:e.clientY,moved:false};renderer.domElement.setPointerCapture(e.pointerId);};
 renderer.domElement.onpointermove=e=>{if(!down)return;if(Math.hypot(e.clientX-down.x,e.clientY-down.y)>4)down.moved=true;az-=(e.clientX-down.lastX)*.007;el=T.MathUtils.clamp(el+(e.clientY-down.lastY)*.007,-1.57,1.57);down.lastX=e.clientX;down.lastY=e.clientY;};
 renderer.domElement.onpointerup=e=>{if(down&&!down.moved){const rect=renderer.domElement.getBoundingClientRect();raycaster.setFromCamera(new T.Vector2((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1),camera);const hit=raycaster.intersectObjects(visibleMeshes(),false)[0];if(hit){q('instance').value=ownerOf.get(hit.object);selection();}}down=null;};renderer.domElement.onpointercancel=()=>down=null;
 renderer.domElement.addEventListener('wheel',e=>{e.preventDefault();distance=T.MathUtils.clamp(distance*Math.exp(e.deltaY*.001),.1,500);},{passive:false});
 function resize(){const {width,height}=viewport.getBoundingClientRect();camera.aspect=width/height;camera.updateProjectionMatrix();renderer.setSize(width,height);}
 new ResizeObserver(resize).observe(viewport);resize();selection();frame();
 document.addEventListener('keydown',e=>{if(e.key==='Escape')q('texture-drawer').hidden=true;});
 const move=cameraMovement(renderer.domElement,camera,target,()=>distance);
 function render(now){const dt=Math.min((now-last)/1000,.1);last=now;move(dt);if(playing&&action)mixer.update(dt*+q('speed').value);model.stateRuntime?.apply();stateUI.sync();if(action){q('time').value=action.time;q('time-label').textContent=action.time.toFixed(2)+' с';}camera.position.set(target.x+distance*Math.cos(el)*Math.sin(az),target.y+distance*Math.cos(el)*Math.cos(az),target.z+distance*Math.sin(el));camera.lookAt(target);renderer.render(scene,camera);requestAnimationFrame(render);}
 window.viewer={model,appearance,mixer,camera,target,get action(){return action;},frame,visibleMeshes};window.ready=true;requestAnimationFrame(render);
}catch(e){error(e);}
