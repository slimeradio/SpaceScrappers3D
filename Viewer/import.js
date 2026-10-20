export function importUI(){
 const q=id=>document.getElementById(id);let busy=false;
 async function open(file){
  if(!file||busy)return;
  q('error').textContent='';
  if(!/\.(glb|blend)$/i.test(file.name)){q('error').textContent='Выберите .glb или .blend.';return;}
  busy=true;q('open-model').disabled=true;q('import-status').textContent=/\.blend$/i.test(file.name)?'Blender подготавливает модель…':'Открытие GLB…';
  try{
   const response=await fetch('/api/import',{method:'POST',headers:{'Content-Type':'application/octet-stream','X-File-Name':encodeURIComponent(file.name)},body:file});
   const text=await response.text();let result;try{result=JSON.parse(text);}catch{throw Error('Перезапустите serve.ps1 из корня: сервер пока не поддерживает импорт файлов.');}
   if(!response.ok)throw Error(result.error||'Не удалось открыть файл');
   const url=new URL(location.href);url.search='';url.searchParams.set('import',result.id);location.href=url;
  }catch(e){q('error').textContent=e.message;q('import-status').textContent='Файл не открыт. Можно выбрать другой.';busy=false;q('open-model').disabled=false;}
 }
 q('open-model').onclick=()=>q('model-file').click();q('model-file').onchange=()=>{open(q('model-file').files[0]);q('model-file').value='';};
 document.addEventListener('dragover',e=>{if(e.dataTransfer.types.includes('Files')){e.preventDefault();e.dataTransfer.dropEffect='copy';}});
 document.addEventListener('drop',e=>{if(e.dataTransfer.files.length){e.preventDefault();open(e.dataTransfer.files[0]);}});
 return open;
}
