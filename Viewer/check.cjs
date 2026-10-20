// Browser acceptance: node Viewer/check.cjs (root server must be running).
const {chromium}=require('C:/Users/nebul/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-gpu-sandbox']});
 try{
 const page=await browser.newPage({viewport:{width:1500,height:1050}}),errors=[];
 page.on('pageerror',e=>{errors.push(e.message);console.error(e.message);});page.on('response',r=>{if(r.status()>=400)errors.push(r.status()+' '+r.url());});
 await page.goto(process.env.VIEWER_URL||'http://127.0.0.1:8769/viewer.html');await page.waitForFunction(()=>window.ready);
 assert.equal(await page.locator('#part option').count(),8);assert.equal(await page.locator('#instance option').count(),10);
 await page.selectOption('#instance','emitter-L');await page.selectOption('#scope','instance');await page.selectOption('#material','armor');
 await page.locator('#color').fill('#dd4422');await page.locator('#color').dispatchEvent('input');
 await page.waitForFunction(()=>asset.nodes['emitter-L'].children.find(m=>m.material.name==='armor').material.color.getHexString()==='dd4422');
 assert.notEqual(await page.evaluate(()=>asset.nodes['emitter-R'].children.find(m=>m.material.name==='armor').material.color.getHexString()),'dd4422');
 await page.click('#textures');await page.locator('.texture-tile').first().click();
 await page.waitForFunction(()=>!!asset.nodes['emitter-L'].children.find(m=>m.material.name==='armor').material.map);
 await page.locator('#repeat').fill('2');await page.locator('#repeat').dispatchEvent('input');
 await page.waitForFunction(()=>asset.nodes['emitter-L'].children.find(m=>m.material.name==='armor').material.map?.repeat.x===2);
 await page.click('#close-textures');await page.click('#isolate');
 assert.equal(await page.evaluate(()=>viewer.visibleMeshes().every(m=>m.parent.name==='emitter-L')),true);
 await page.click('#isolate');
 await page.click('#play');const before=await page.evaluate(()=>asset.nodes.yaw.quaternion.toArray());
 await page.waitForTimeout(250);const after=await page.evaluate(()=>asset.nodes.yaw.quaternion.toArray());assert.notDeepEqual(before,after);
 await page.click('#play');const paused=await page.evaluate(()=>viewer.action.time);await page.waitForTimeout(120);assert.equal(await page.evaluate(()=>viewer.action.time),paused);
 await page.locator('#time').fill('1.5');await page.locator('#time').dispatchEvent('input');assert.equal(await page.evaluate(()=>viewer.action.time),1.5);
 await page.click('#stop');assert.equal(await page.evaluate(()=>viewer.action.time),0);
 const preset=await page.evaluate(()=>({schema:'SpaceScrappers3D/appearance/1',block:'SS/CorporateHiTech/CHT-T01',part:null,materials:viewer.appearance.state()}));
 await page.reload();await page.waitForFunction(()=>window.ready);assert.equal(await page.evaluate(()=>asset.nodes['emitter-L'].children.find(m=>m.material.name==='armor').material.map.repeat.x),2);
 await page.evaluate(async data=>viewer.appearance.import(data),preset);
 const gltf=await page.evaluate(()=>exportGLTF());assert.ok(gltf.meshes.length>0);assert.equal(gltf.animations.length,1);assert.ok(gltf.images.length>0);
 await page.selectOption('#instance','emitter-L');await page.selectOption('#scope','instance');await page.selectOption('#material','armor');await page.click('#reset-material');
 await page.waitForFunction(()=>asset.nodes['emitter-L'].children.find(m=>m.material.name==='armor').material.map===null);
 const reports=[];for(let n=1;n<=7;n++){const id='CHT-P0'+n;await page.goto('http://127.0.0.1:8769/viewer.html?part='+id);await page.waitForFunction(()=>window.ready);const report=await page.evaluate(()=>({meshes:viewer.visibleMeshes().length,animationDisabled:document.getElementById('play').disabled}));assert.ok(report.meshes>0);assert.equal(report.animationDisabled,true);reports.push({id,...report});}
 await page.goto('http://127.0.0.1:8769/viewer.html');await page.waitForFunction(()=>window.ready);
 await page.selectOption('#material','armor');await page.locator('#color').fill('#7394ad');await page.locator('#color').dispatchEvent('input');
 await page.waitForFunction(()=>Object.values(asset.nodes).every(n=>n.children.filter(m=>m.material?.name==='armor').every(m=>m.material.color.getHexString()==='7394ad')));
 await page.click('#textures');await page.locator('.texture-tile').first().click();await page.waitForFunction(()=>Object.values(asset.nodes).every(n=>n.children.filter(m=>m.material?.name==='armor').every(m=>!!m.material.map)));
 await page.click('#close-textures');await page.click('#reset-material');await page.waitForFunction(()=>Object.values(asset.nodes).every(n=>n.children.filter(m=>m.material?.name==='armor').every(m=>!m.material.map)));
 await page.screenshot({path:path.join(__dirname,'acceptance.png')});
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(__dirname,'acceptance-mobile.png')});
 assert.deepEqual(errors,[]);assert.equal(await page.locator('#error').textContent(),'');
 fs.writeFileSync(path.join(__dirname,'acceptance.json'),JSON.stringify({passed:true,checks:['instance paint isolation','texture and repeat','assembly paint and texture','material reset','instance visibility','animation playback/pause/scrub/stop','appearance persistence and import','textured animated glTF export','all seven standalone parts','mobile layout'],parts:reports,browserErrors:errors},null,2).replace(/\n/g,'\r\n'));
 console.log('PASS: root viewer browser acceptance');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
