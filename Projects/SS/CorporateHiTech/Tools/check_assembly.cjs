const {chromium}=require('C:/Users/nebul/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path');const root=path.resolve(__dirname,'..');
const write=(p,s)=>{fs.mkdirSync(path.dirname(p),{recursive:true});fs.writeFileSync(p,s.replace(/\r?\n/g,'\r\n'));};
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-gpu-sandbox']});
 const page=await browser.newPage({viewport:{width:1440,height:1040},deviceScaleFactor:1});const errors=[];page.on('pageerror',e=>{errors.push(e.message);console.error(e.message);});
 await page.goto('http://127.0.0.1:8768/Blocks/CHT-T01/viewer.html?capture');await page.waitForFunction(()=>window.ready);
 const dir=path.join(root,'Blocks/CHT-T01/Previews');fs.mkdirSync(dir,{recursive:true});
 const poses=[];
 for(const angle of [0,45,90,180,270,360]){await page.evaluate(a=>window.setPose(a),angle);poses.push({angle,...await page.evaluate(()=>window.assetAudit())});}
 await page.evaluate(()=>window.setPose(0));await page.screenshot({path:path.join(dir,'perspective.png')});
 await page.evaluate(()=>window.setView('top'));await page.screenshot({path:path.join(dir,'top.png')});
 await page.evaluate(()=>{window.setView('iso');window.setPose(0,.75);});await page.screenshot({path:path.join(dir,'exploded.png')});
 await page.evaluate(()=>window.setPose(0));
 const gltf=await page.evaluate(()=>window.exportGLTF());write(path.join(root,'Blocks/CHT-T01/Exports/CHT-T01.gltf'),JSON.stringify(gltf));
 const gltfSummary={meshes:gltf.meshes.length,nodes:gltf.nodes.length,animations:gltf.animations?.length,materials:gltf.materials.length,extensionsUsed:gltf.extensionsUsed,buffers:gltf.buffers.map(x=>x.byteLength)};
 const roundtrip=await page.evaluate(async()=>{const {GLTFLoader}=await import('../../Tools/GLTFLoader.js');const {T}=await import('../../Tools/model.js');const loaded=await new GLTFLoader().loadAsync('Exports/CHT-T01.gltf');const yaw=loaded.scene.getObjectByName('yaw'),head=loaded.scene.getObjectByName('head'),emitter=loaded.scene.getObjectByName('emitter-L');const samples=[];const mixer=new T.AnimationMixer(loaded.scene);mixer.clipAction(loaded.animations[0]).play();for(const time of [0,.375,.75,1.5,2.25,2.99]){mixer.setTime(time);loaded.scene.updateMatrixWorld(true);samples.push({time,yawQuaternion:yaw.quaternion.toArray(),muzzle:new T.Vector3(0,.49,0).applyMatrix4(emitter.matrixWorld).toArray()});}return {animations:loaded.animations.map(a=>a.name),headParent:head.parent.name,emitterParent:emitter.parent.name,upConversionRoot:loaded.scene.children[0].name,samples};});
 for(let n=1;n<=7;n++){const id='CHT-P0'+n;await page.goto('http://127.0.0.1:8768/Blocks/CHT-T01/viewer.html?part='+id);await page.waitForFunction(()=>window.ready);write(path.join(root,'Parts',id,'Exports',id+'.gltf'),JSON.stringify(await page.evaluate(()=>window.exportGLTF())));}
 write(path.join(root,'Blocks/CHT-T01/validation.json'),JSON.stringify({browserErrors:errors,poses,gltf:gltfSummary,roundtrip},null,2));
 console.log(JSON.stringify({errors,poses,gltf:gltfSummary}));await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
