const {chromium}=require('C:/Users/nebul/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),base='http://127.0.0.1:8769/viewer.html';
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-gpu-sandbox']});
 try{
  const page=await browser.newPage({viewport:{width:1500,height:1050}}),errors=[],reports=[];page.on('pageerror',e=>{errors.push(e.message);console.error(e.message);});
  await page.goto(base);await page.waitForFunction(()=>window.ready);
  const sources=['Projects/SS/ChunkyModular/Exports/Viewer/cm-handle-folding.glb','Projects/SS/ChunkyModular/Parts/cm-handle-folding/cm-handle-folding.blend'];
  for(const source of sources){
   const file=path.join(root,source),hash=crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
   const prior=new URL(page.url()).searchParams.get('import');
   await page.locator('#model-file').setInputFiles(file);
   await page.waitForURL(u=>u.searchParams.has('import')&&u.searchParams.get('import')!==prior,{timeout:240000});await page.waitForFunction(()=>window.ready);
   const report=await page.evaluate(()=>({name:document.getElementById('title').textContent,meshes:viewer.visibleMeshes().length,parts:Object.keys(asset.nodes).length,animations:asset.root.animations.length}));
   assert.ok(report.meshes>0);assert.ok(report.animations>0);assert.equal(await page.locator('#error').textContent(),'');
   await page.click('#play');await page.waitForFunction(()=>viewer.action.time>0);await page.click('#stop');
   const mat=await page.locator('#material').inputValue();await page.locator('#color').fill('#985432');await page.locator('#color').dispatchEvent('input');
   await page.waitForFunction(id=>{let found=false;asset.root.traverse(n=>{if(n.isMesh&&n.material.name===id&&n.material.color.getHexString()==='985432')found=true;});return found;},mat);
   const preset=await page.evaluate(()=>({schema:'SpaceScrappers3D/appearance/1',block:'Imported/File/'+new URL(location.href).searchParams.get('import'),part:null,materials:viewer.appearance.state()}));await page.evaluate(data=>viewer.appearance.import(data),preset);
   const header=await page.evaluate(async()=>{const buffer=await exportGLTF(true);return Array.from(new Uint8Array(buffer,0,4));});assert.deepEqual(header,[103,108,84,70]);
   const instance=await page.locator('#instance option').nth(1).getAttribute('value');await page.selectOption('#instance',instance);await page.click('#isolate');assert.equal(await page.evaluate(()=>viewer.visibleMeshes().length),1);
   await page.click('#isolate');await page.evaluate(()=>document.querySelector('aside').scrollTop=0);await page.screenshot({path:__dirname+'/import-'+path.extname(file).slice(1)+'.png'});
   const item=await page.locator('#part option').nth(1).getAttribute('value');await Promise.all([page.waitForURL(u=>u.searchParams.get('part')===item),page.selectOption('#part',item)]);await page.waitForFunction(()=>window.ready);assert.equal(await page.evaluate(()=>viewer.visibleMeshes().length),1);
   await page.reload();await page.waitForFunction(()=>window.ready);assert.equal(await page.evaluate(()=>viewer.visibleMeshes().length),1);
   assert.equal(crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),hash);reports.push({...report,format:path.extname(file),sourceUnchanged:true});
  }
  const bad=await page.request.post('http://127.0.0.1:8769/api/import',{headers:{'X-File-Name':'invalid.glb','Content-Type':'application/octet-stream'},data:Buffer.from('invalid')});assert.equal(bad.status(),400);assert.ok((await bad.json()).error);
  await Promise.all([page.waitForURL(u=>!u.searchParams.has('import')),page.selectOption('#project','SS')]);await page.waitForFunction(()=>window.ready);assert.equal(await page.locator('#project').inputValue(),'SS');
  assert.deepEqual(errors,[]);fs.writeFileSync(__dirname+'/import-acceptance.json',JSON.stringify({passed:true,checks:['GLB file picker','blend file picker and Blender conversion','object selection and isolation','animation playback','painting and appearance JSON','binary GLB export','standalone object and reload','source hashes unchanged','invalid GLB rejected','return to catalog'],models:reports,browserErrors:errors},null,2).replace(/\n/g,'\r\n'));console.log('PASS: GLB and blend import');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
