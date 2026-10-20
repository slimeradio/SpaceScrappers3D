const {chromium}=require('C:/Users/nebul/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict');const root=path.resolve(__dirname,'..');
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-gpu-sandbox']});
 try{
 const page=await browser.newPage({viewport:{width:1600,height:1100}}),errors=[],failed=[];page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400&&!r.url().endsWith('favicon.ico'))failed.push(r.url());});
 const url='http://127.0.0.1:8768/Blocks/CHT-T01/viewer.html?v=textures';await page.goto(url);await page.waitForFunction(()=>window.ready);
 assert.equal(await page.evaluate(()=>textureSelection.catalog.entries.length),106);
 await page.click('#texture-toggle');await page.selectOption('#texture-group','HeavyRust');await page.fill('#texture-search','RustColorable');
 const entry=await page.evaluate(()=>textureSelection.catalog.entries.find(e=>e.group==='HeavyRust'&&e.name==='RustColorable'));
 await page.click(`[data-id="${entry.id}"]`);await page.waitForFunction(id=>textureSelection.state.armor?.id===id,entry.id);
 const channels=await page.evaluate(()=>({color:asset.mats.armor.map?.colorSpace,normal:!!asset.mats.armor.normalMap,roughness:!!asset.mats.armor.roughnessMap,emissionMap:asset.mats.cyan.map,uv:[...function*(){let meshes=[];asset.root.traverse(o=>{if(o.isMesh)meshes.push({name:o.name,uv:o.geometry.attributes.uv?.count,vertices:o.geometry.attributes.position.count});});yield* meshes;}()]}));
 assert.equal(channels.color,'srgb');assert(channels.normal&&channels.roughness);assert.equal(channels.emissionMap,null);assert(channels.uv.every(m=>m.uv===m.vertices));
 await page.locator('#texture-scale').fill('2');await page.locator('#texture-scale').dispatchEvent('input');assert.deepEqual(await page.evaluate(()=>asset.mats.armor.map.repeat.toArray()),[2,2]);
 const dest=path.join(root,'Blocks/CHT-T01/Previews');await page.screenshot({path:path.join(dest,'shared-textures.png')});
 await page.reload();await page.waitForFunction(()=>window.ready);assert.equal(await page.evaluate(()=>textureSelection.state.armor.id),entry.id);assert.deepEqual(await page.evaluate(()=>asset.mats.armor.normalMap.repeat.toArray()),[2,2]);
 await page.selectOption('#part','CHT-P05');await page.waitForFunction(()=>window.ready&&!!asset.defs['CHT-P05']);assert.equal(await page.evaluate(()=>textureSelection.state.armor.id),entry.id);
 await page.click('#texture-toggle');await page.selectOption('#texture-slot','edge');await page.selectOption('#texture-group','CarbonFibre');await page.fill('#texture-search','CarbonFibre');
 const carbon=await page.evaluate(()=>textureSelection.catalog.entries.find(e=>e.group==='CarbonFibre'&&e.name==='CarbonFibre'));await page.click(`[data-id="${carbon.id}"]`);await page.waitForFunction(id=>textureSelection.state.edge?.id===id,carbon.id);
 await page.selectOption('#texture-slot','armor');await page.click('#texture-clear');assert.equal(await page.evaluate(()=>asset.mats.armor.map),null);assert.equal(await page.evaluate(()=>asset.mats.armor.normalMap),null);assert.equal(await page.evaluate(()=>asset.mats.armor.roughness),.24);assert(await page.evaluate(()=>!!asset.mats.edge.map));
 // Verify selected texture channels survive the existing export flow.
 const exported=await page.evaluate(()=>window.exportGLTF());const edgeMat=exported.materials.find(m=>m.name==='edge');assert(edgeMat.pbrMetallicRoughness.baseColorTexture);assert(edgeMat.normalTexture);assert(edgeMat.pbrMetallicRoughness.metallicRoughnessTexture);
 assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
 const result={catalogCount:106,groups:5,browserErrors:errors,failedRequests:failed,checks:['filter and select actual UI tile','color, normal, roughness channels','UVs for every mesh including lofts','scale on all maps','emission unchanged','selection persists after reload and part switch','independent material slots','reset restores original surface','selected maps preserved in glTF export']};
 fs.writeFileSync(path.join(root,'Blocks/CHT-T01/texture-validation.json'),JSON.stringify(result,null,2).replace(/\n/g,'\r\n'));console.log(JSON.stringify(result));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
