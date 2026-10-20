const {chromium}=require('C:/Users/nebul/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict'),fs=require('node:fs');
(async()=>{
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-gpu-sandbox']});
try{
 const page=await browser.newPage({viewport:{width:1500,height:1050}}),errors=[],reports=[];
 page.on('pageerror',e=>{errors.push(e.message);console.error(e.message);});page.on('response',r=>{if(r.status()>=400)errors.push(r.status()+' '+r.url());});
 await page.goto('http://127.0.0.1:8769/viewer.html');await page.waitForFunction(()=>window.ready);
 assert.equal(await page.locator('#style option').count(),3);
 await page.locator('canvas').focus();
 const target=()=>page.evaluate(()=>viewer.target.toArray());
 for(const code of ['KeyW','KeyS','KeyA','KeyD','Space','KeyC']){
  const before=await target();await page.keyboard.down(code);await page.waitForFunction(value=>viewer.target.toArray().some((v,i)=>v!==value[i]),before);await page.keyboard.up(code);const after=await target();assert.notDeepEqual(before,after,code+' moves camera');if(code==='Space')assert.ok(after[2]>before[2]);if(code==='KeyC')assert.ok(after[2]<before[2]);
 }
 await page.locator('#color').focus();let before=await target();await page.keyboard.down('KeyW');await page.waitForTimeout(120);await page.keyboard.up('KeyW');assert.deepEqual(await target(),before);
 await page.locator('canvas').focus();await page.keyboard.down('KeyW');await page.evaluate(()=>window.dispatchEvent(new Event('blur')));before=await target();await page.waitForTimeout(120);assert.deepEqual(await target(),before);await page.keyboard.up('KeyW');
 for(const style of ['ChunkyModular','MilitaryArmor']){
  await Promise.all([page.waitForURL(u=>u.searchParams.get('block')?.includes(style)),page.selectOption('#style',style)]);await page.waitForFunction(()=>window.ready);
  assert.equal(await page.locator('#error').textContent(),'');const report=await page.evaluate(async()=>{const {T}=await import('/Viewer/model.js');return {meshes:viewer.visibleMeshes().length,instances:Object.keys(asset.nodes).length,parts:Object.keys(asset.defs).length,animations:asset.root.animations.length,bounds:new T.Box3().setFromObject(asset.root).getSize(new T.Vector3()).toArray()};});assert.ok(report.meshes>100);assert.ok(report.animations>0);assert.ok(Math.max(...report.bounds)<20,'No studio floor in model bounds');
  await page.click('#play');const start=await page.evaluate(()=>viewer.action.time);await page.waitForFunction(value=>viewer.action.time>value,start);await page.click('#stop');
  const instance=await page.locator('#instance option').nth(1).getAttribute('value');await page.selectOption('#instance',instance);await page.click('#isolate');assert.ok(await page.evaluate(()=>viewer.visibleMeshes().length)>0);assert.ok(await page.evaluate(()=>viewer.visibleMeshes().length)<report.meshes);
  await page.selectOption('#scope','instance');await page.locator('#color').fill('#aa3311');await page.locator('#color').dispatchEvent('input');
  await page.click('#textures');await page.locator('.texture-tile').first().click();await page.waitForFunction(()=>Object.keys(viewer.appearance.state()).length>0);await page.click('#close-textures');
  await page.click('#isolate');await page.evaluate(()=>{document.querySelector('aside').scrollTop=0;});await page.screenshot({path:__dirname+'/acceptance-'+style+'.png'});
  const part=style==='ChunkyModular'?'cm-handle-folding':'MA-P05';await Promise.all([page.waitForURL(u=>u.searchParams.get('part')===part),page.selectOption('#part',part)]);await page.waitForFunction(()=>window.ready);assert.ok(await page.evaluate(()=>viewer.visibleMeshes().length)>0);assert.equal(await page.locator('#error').textContent(),'');
  reports.push({style,...report,standalone:part});
 }
 assert.deepEqual(errors,[]);fs.writeFileSync(__dirname+'/navigation-acceptance.json',JSON.stringify({passed:true,keyboard:['W','A','S','D','C','Space','input focus guard','blur clears held keys'],styles:reports,browserErrors:errors},null,2).replace(/\n/g,'\r\n'));console.log('PASS: movement and all styles');
}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
