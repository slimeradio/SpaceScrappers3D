const {chromium}=require('C:/Users/nebul/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..');
const write=(p,s)=>{fs.mkdirSync(path.dirname(p),{recursive:true});fs.writeFileSync(p,s.replace(/\r?\n/g,'\r\n'));};
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-gpu-sandbox']});
 const page=await browser.newPage({viewport:{width:1440,height:1040},deviceScaleFactor:1});
 page.on('console',m=>console.log(m.type(),m.text()));const errors=[];page.on('pageerror',e=>{errors.push(e.message);console.log('PAGEERROR',e.message)});
 const reports={};
 for(let n=1;n<=7;n++){
  const id='CHT-P0'+n;await page.goto('http://127.0.0.1:8768/Blocks/CHT-T01/viewer.html?part='+id+'&capture');await page.waitForFunction(()=>window.ready);reports[id]=await page.evaluate(()=>window.assetAudit());
  const dest=path.join(root,'Parts',id,'Previews');fs.mkdirSync(dest,{recursive:true});await page.screenshot({path:path.join(dest,'perspective.png')});
  await page.evaluate(()=>window.setView('top'));await page.screenshot({path:path.join(dest,'top.png')});
 }
 write(path.join(root,'Parts/validation.json'),JSON.stringify({parts:reports,browserErrors:errors},null,2));
 console.log(JSON.stringify({stage:'parts',reports,browserErrors:errors}));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
