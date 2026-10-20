import {T} from './model.js';

export function cameraMovement(canvas,camera,target,getDistance){
 const keys=new Set(),codes=new Set(['KeyW','KeyA','KeyS','KeyD','KeyC','Space','ShiftLeft','ShiftRight']);
 canvas.tabIndex=0;canvas.setAttribute('aria-label','Модель. WASD — перемещение, Space — вверх, C — вниз');
 const editing=element=>element?.closest('input,select,textarea,button,summary,[contenteditable=true]');
 const clear=()=>keys.clear();
 document.addEventListener('keydown',event=>{if(!codes.has(event.code)||event.ctrlKey||event.altKey||event.metaKey||editing(event.target))return;event.preventDefault();keys.add(event.code);});
 document.addEventListener('keyup',event=>keys.delete(event.code));
 window.addEventListener('blur',clear);document.addEventListener('visibilitychange',clear);document.addEventListener('focusin',event=>{if(editing(event.target))clear();});
 canvas.addEventListener('pointerdown',()=>canvas.focus({preventScroll:true}));
 const forward=new T.Vector3(),right=new T.Vector3(),delta=new T.Vector3();
 return dt=>{
  const x=Number(keys.has('KeyD'))-Number(keys.has('KeyA')),y=Number(keys.has('KeyW'))-Number(keys.has('KeyS')),z=Number(keys.has('Space'))-Number(keys.has('KeyC'));
  if(!x&&!y&&!z)return;
  camera.getWorldDirection(forward);right.setFromMatrixColumn(camera.matrixWorld,0).normalize();
  delta.set(0,0,z).addScaledVector(right,x).addScaledVector(forward,y);
  if(delta.lengthSq()>0)target.addScaledVector(delta.normalize(),dt*Math.max(getDistance()*.6,.1)*(keys.has('ShiftLeft')||keys.has('ShiftRight')?3:1));
 };
}
