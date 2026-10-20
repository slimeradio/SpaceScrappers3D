import {T,build} from './model.js';
import {initTextures} from './texture-selector.js';
const params=new URLSearchParams(location.search),part=params.get('part'),capture=params.has('capture');
if(part)document.getElementById('part').value=part;
document.getElementById('part').onchange=e=>{location.search=e.target.value?'?part='+e.target.value:'';};
const scene=new T.Scene();scene.background=new T.Color('#0d1c28');scene.fog=new T.Fog('#0d1c28',9,24);
const camera=new T.PerspectiveCamera(32,innerWidth/innerHeight,.01,100);camera.up.set(0,0,1);
const renderer=new T.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setSize(innerWidth,innerHeight);renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.35;document.body.prepend(renderer.domElement);
scene.add(new T.HemisphereLight('#d1e9ff','#283843',2));
function light(color,intensity,pos,size){const l=new T.DirectionalLight(color,intensity);l.position.set(...pos);l.castShadow=true;l.shadow.mapSize.set(2048,2048);Object.assign(l.shadow.camera,{left:-3,right:3,top:3,bottom:-3,near:.1,far:20});l.shadow.bias=-.00015;l.shadow.normalBias=.014;l.shadow.radius=size;scene.add(l);}
light('#fff6eb',4,[-3,2,6],4);light('#a3d9ff',2,[3,-3,4],4);
const floor=new T.Mesh(new T.PlaneGeometry(100,100),new T.MeshStandardMaterial({color:'#102734',metalness:.22,roughness:.49}));floor.position.z=-.018;floor.receiveShadow=true;scene.add(floor);
const grid=new T.GridHelper(16,32,'#254455','#1b3341');grid.rotation.x=Math.PI/2;grid.position.z=-.014;scene.add(grid);
let model;try{model=await build(part);}catch(e){document.getElementById('err').textContent=e.message;throw e;}scene.add(model.root);
const bbox=new T.Box3().setFromObject(model.root),center=bbox.getCenter(new T.Vector3()),size=bbox.getSize(new T.Vector3());
if(part){floor.position.z=bbox.min.z-.018;grid.position.z=bbox.min.z-.014;}
let distance=part?Math.max(size.length()*2.5,.65):4.7,az=.68,el=.64,playing=false,last=performance.now(),yaw=0,explode=0;
const target=center.clone();target.x+=part?0:.16;
const rest=Object.fromEntries(Object.entries(model.nodes).map(([k,n])=>[k,n.position.clone()]));
const directions={yaw:[0,0,.45],head:[0,0,.45],'cheek-L':[-.8,0,.2],'cheek-R':[.8,0,.2],'emitter-L':[-.15,.8,.1],'emitter-R':[.15,.8,.1],sensor:[0,0,.65],service:[0,-.35,.5]};
function apply(){if(model.nodes.yaw)model.nodes.yaw.rotation.z=yaw;for(const [k,n]of Object.entries(model.nodes)){n.position.copy(rest[k]);if(directions[k])n.position.addScaledVector(new T.Vector3(...directions[k]),explode);}document.getElementById('yawlabel').textContent=Math.round(yaw*180/Math.PI)+'°';document.getElementById('exlabel').textContent=Math.round(explode*100)+'%';}
function render(){target.z=center.z+explode*.6;const framedDistance=distance*(1+explode*.55);camera.position.set(target.x+framedDistance*Math.cos(el)*Math.sin(az),target.y+framedDistance*Math.cos(el)*Math.cos(az),target.z+framedDistance*Math.sin(el));camera.lookAt(target);renderer.render(scene,camera);}
document.getElementById('yaw').oninput=e=>{playing=false;yaw=+e.target.value*Math.PI/180;apply();};
document.getElementById('explode').oninput=e=>{explode=+e.target.value;apply();};
document.getElementById('iso').onclick=()=>{az=.68;el=.64;};document.getElementById('top').onclick=()=>{az=0;el=Math.PI/2-.001;};
document.getElementById('reset').onclick=()=>{yaw=0;explode=0;playing=false;az=.68;el=.64;document.getElementById('yaw').value=0;document.getElementById('explode').value=0;apply();};
document.getElementById('play').onclick=()=>{playing=!playing;document.getElementById('play').textContent=playing?'Ⅱ Пауза':'▶ Вращать';};
let down=false,lx=0,ly=0;renderer.domElement.onpointerdown=e=>{down=true;lx=e.clientX;ly=e.clientY;renderer.domElement.setPointerCapture(e.pointerId);};renderer.domElement.onpointerup=()=>down=false;renderer.domElement.onpointermove=e=>{if(!down)return;az-=(e.clientX-lx)*.007;el=T.MathUtils.clamp(el+(e.clientY-ly)*.007,.08,1.57);lx=e.clientX;ly=e.clientY;};renderer.domElement.onwheel=e=>{e.preventDefault();distance=T.MathUtils.clamp(distance*Math.exp(e.deltaY*.001),.25,12);};
onresize=()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);};
window.asset=model;window.setView=(view)=>{if(view==='top'){az=0;el=Math.PI/2-.001;}else{az=.68;el=.64;}render();};window.setPose=(a,e=0)=>{yaw=a*Math.PI/180;explode=e;apply();render();};
window.exportGLTF=async()=>{const {GLTFExporter}=await import('./GLTFExporter.js');const exporter=new GLTFExporter();apply();const exportRoot=new T.Group();exportRoot.name="Z-up_to_glTF_Y-up";exportRoot.rotation.x=-Math.PI/2;exportRoot.add(model.root.clone(true));return await exporter.parseAsync(exportRoot,{animations:model.root.animations,binary:false,onlyVisible:true});};
window.assetAudit=()=>{model.root.updateMatrixWorld(true);const errors=[],links=[];for(const i of model.assembly?.instances||[]){const d=model.defs[i.partId];if(d.version!==i.partVersion)errors.push('version '+i.id);if(i.attachment){const p=model.nodes[i.parent],n=model.nodes[i.id],pd=model.defs[model.assembly.instances.find(x=>x.id===i.parent).partId];const a=pd.attachments.find(x=>x.id===i.attachment.parentSocket),b=d.attachments.find(x=>x.id===i.attachment.childSocket);const pa=p.localToWorld(new T.Vector3(...a.position)),pb=n.localToWorld(new T.Vector3(...b.position));const na=new T.Vector3(...a.normal).transformDirection(p.matrixWorld),nb=new T.Vector3(...b.normal).transformDirection(n.matrixWorld);const ua=new T.Vector3(...a.up).transformDirection(p.matrixWorld),ub=new T.Vector3(...b.up).transformDirection(n.matrixWorld);const gap=pa.distanceTo(pb);links.push({id:i.id,gap,normalDot:na.dot(nb),upDot:ua.dot(ub)});if(gap>1e-6||na.dot(nb)>-.9999||(!i.joint&&ua.dot(ub)<.9999))errors.push('socket '+i.id);}}
 let vertices=0,triangles=0,meshCount=0;model.root.traverse(o=>{if(o.isMesh){meshCount++;vertices+=o.geometry.attributes.position.count;triangles+=(o.geometry.index?o.geometry.index.count:o.geometry.attributes.position.count)/3;if(!o.material||!o.geometry.attributes.normal)errors.push('mesh '+o.name);for(const v of o.geometry.attributes.position.array)if(!Number.isFinite(v)){errors.push('nonfinite '+o.name);break;}}});return {errors,links,meshCount,vertices,triangles,bounds:new T.Box3().setFromObject(model.root).getSize(new T.Vector3()).toArray()};};
if(part){document.querySelector('h1').textContent=part;document.querySelector('header p').textContent=model.defs[part].title;document.querySelector('footer').innerHTML='<strong>Самостоятельная переиспользуемая деталь</strong><br>Версия '+model.defs[part].version+' / белая броня и голубая эмиссия';}
if(capture)document.querySelector('aside').style.display='none';
await initTextures(model);
function loop(now){const dt=(now-last)/1000;last=now;if(playing){yaw=(yaw+dt*2*Math.PI/3)%(2*Math.PI);apply();document.getElementById('yaw').value=yaw*180/Math.PI;}render();requestAnimationFrame(loop);}apply();render();window.ready=true;requestAnimationFrame(loop);
