const {chromium}=require('C:/Users/nebul/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),os=require('os'),assert=require('assert/strict'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),workspace=path.resolve(root,'../../..'),temp=path.join(os.tmpdir(),'SS-CorporateHiTech-six-weapons-final');
const ids=process.argv.length>2?process.argv.slice(2):['CHT-W01','CHT-W02','CHT-W03','CHT-W04','CHT-W05','CHT-W06'];
const write=(p,data)=>fs.writeFileSync(p,JSON.stringify(data,null,2).replace(/\n/g,'\r\n')+'\r\n');
(async()=>{
 fs.mkdirSync(temp,{recursive:true});
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-gpu-sandbox']});
 try{
 const page=await browser.newPage({viewport:{width:1500,height:1050},acceptDownloads:true});const errors=[],failed=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)failed.push(r.status()+' '+r.url());});
 for(const id of ids){
  await page.goto('http://127.0.0.1:8769/viewer.html?block='+encodeURIComponent('SS/CorporateHiTech/'+id));await page.waitForFunction(()=>window.ready,{timeout:60000});
  assert.equal(await page.evaluate(()=>asset.assembly.id),id);assert.equal(await page.locator('#error').textContent(),'');
  const result=await page.evaluate(async()=>{
   const {T}=await import('/Viewer/model.js'),problems=[],links=[],parts=[];const definitions=asset.defs,instances=asset.assembly.instances;
   const box=new T.Box3().setFromObject(asset.root),extent=box.getSize(new T.Vector3()).toArray();
   for(const [id,d]of Object.entries(definitions)){
    if(d.version===undefined||!d.attachments||!d.geometry?.length)problems.push('part metadata '+id);
    const group=Object.values(asset.nodes).find(n=>n.userData.partId===id);let meshes=0,triangles=0;
    for(const mesh of group.children){if(!mesh.isMesh)continue;meshes++;const geo=mesh.geometry,pos=geo.attributes.position;
     triangles+=(geo.index?geo.index.count:pos.count)/3;if(!geo.attributes.normal||geo.attributes.uv?.count!==pos.count||!mesh.material)problems.push('geometry channels '+id+'/'+mesh.name);
     for(const attribute of ['position','normal','uv'])for(const x of geo.attributes[attribute]?.array||[])if(!Number.isFinite(x)){problems.push('nonfinite '+attribute+' '+id);break;}
    }
    parts.push({id,version:d.version,meshes,triangles});
   }
   asset.root.updateMatrixWorld(true);
   for(const i of instances){const d=definitions[i.partId],node=asset.nodes[i.id];if(i.partVersion!==d.version)problems.push('version '+i.id);if(i.scale.some(s=>s<=0))problems.push('scale '+i.id);
    if(i.parent&&!i.attachment)problems.push('missing socket '+i.id);
    if(!i.attachment)continue;
    const p=instances.find(x=>x.id===i.parent),pd=definitions[p.partId],pn=asset.nodes[i.parent],a=pd.attachments.find(x=>x.id===i.attachment.parentSocket),b=d.attachments.find(x=>x.id===i.attachment.childSocket);
    if(!a||!b){problems.push('missing socket definition '+i.id);continue;}
    const pa=pn.localToWorld(new T.Vector3(...a.position)),pb=node.localToWorld(new T.Vector3(...b.position)),normalA=new T.Vector3(...a.normal).applyNormalMatrix(new T.Matrix3().getNormalMatrix(pn.matrixWorld)),normalB=new T.Vector3(...b.normal).applyNormalMatrix(new T.Matrix3().getNormalMatrix(node.matrixWorld));
    const upA=new T.Vector3(...a.up).transformDirection(pn.matrixWorld),upB=new T.Vector3(...b.up).transformDirection(node.matrixWorld);const gap=pa.distanceTo(pb),dot=normalA.dot(normalB),up=upA.dot(upB);links.push({instance:i.id,gap,normalDot:dot,upDot:up});if(gap>1e-5||dot>-.9999||(!i.joint&&up<.9999))problems.push('socket alignment '+i.id);
   }
   const clipChecks=[];
   for(const clip of asset.root.animations){const mixer=new T.AnimationMixer(asset.root),action=mixer.clipAction(clip);action.setLoop(T.LoopOnce,1);action.clampWhenFinished=true;action.play();const poses=[];
    for(const f of [0,.25,.5,.75,1]){mixer.setTime(clip.duration*f);asset.root.updateMatrixWorld(true);let finite=true;for(const node of Object.values(asset.nodes))if(node.matrixWorld.elements.some(x=>!Number.isFinite(x)))finite=false;poses.push({fraction:f,finite});if(!finite)problems.push('nonfinite animation '+clip.name);}
    mixer.setTime(0);mixer.stopAllAction();clipChecks.push({name:clip.name,duration:clip.duration,poses});
   }
   return {id:asset.assembly.id,catalogId:asset.assembly.catalogId,instances:instances.length,parts,links,extent,clipChecks,problems};
  });
  assert.deepEqual(result.problems,[],id+': '+result.problems.join('; '));
  await page.click('#iso');await page.locator('#viewport').screenshot({path:path.join(temp,id+'-iso.png')});
  await page.click('#top');await page.locator('#viewport').screenshot({path:path.join(temp,id+'-top.png')});await page.click('#iso');
  // Use the existing viewer's final export; no new viewer or alternative model is created.
  const output=path.join(root,'Blocks',id,'Exports');fs.mkdirSync(output,{recursive:true});
  await page.locator('#export').evaluate(e=>e.closest('details').open=true);
  const [download]=await Promise.all([page.waitForEvent('download',{timeout:120000}),page.click('#export')]);const destination=path.join(output,id+'.gltf');await download.saveAs(destination);
  const gltf=JSON.parse(fs.readFileSync(destination,'utf8'));assert(gltf.meshes.length>0);assert.equal((gltf.animations||[]).length,result.clipChecks.length);assert(gltf.nodes.some(n=>n.name===id));
  // All text exports follow workspace CRLF.
  fs.writeFileSync(destination,fs.readFileSync(destination,'utf8').replace(/\r?\n/g,'\r\n'));
  result.export={path:'Exports/'+id+'.gltf',meshes:gltf.meshes.length,nodes:gltf.nodes.length,animations:(gltf.animations||[]).map(c=>c.name),sha256:crypto.createHash('sha256').update(fs.readFileSync(destination)).digest('hex')};
  result.browserErrors=[...errors];result.failedRequests=[...failed];assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
  write(path.join(root,'Blocks',id,'validation.json'),result);console.log(id+': PASS '+result.parts.length+' parts / '+result.instances+' instances / '+gltf.meshes.length+' meshes');
 }
 console.log('Final inspection captures (temporary only): '+temp);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
