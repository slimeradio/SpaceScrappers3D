import * as T from './three.module.js';
import {RoundedBoxGeometry} from './RoundedBoxGeometry.js';
export {T};
export async function loadJSON(path){const r=await fetch(path);if(!r.ok)throw Error(path+': '+r.status);return r.json();}
export async function materials(){const defs=await loadJSON('../../Materials/materials.json');return Object.fromEntries(Object.entries(defs).map(([k,v])=>[k,new T.MeshStandardMaterial({...v,name:k})]));}
export function geometry(g){
 let geo;
 if(g.shape==='roundedBox'){
  const [w,h,d]=g.size,r=Math.min(g.radius,w*.48,h*.48,d*.48);
  geo=new RoundedBoxGeometry(w,h,d,5,r);
 }else if(g.shape==='loft'){
  const levels=g.levels,n=g.outline.length,verts=[];
  const point=(k,i)=>[g.outline[i][0]*levels[k].scale[0],g.outline[i][1]*levels[k].scale[1],levels[k].z];
  const tri=(a,b,c)=>verts.push(...a,...b,...c);
  for(let k=0;k<levels.length-1;k++)for(let i=0;i<n;i++){const j=(i+1)%n;tri(point(k,i),point(k,j),point(k+1,j));tri(point(k,i),point(k+1,j),point(k+1,i));}
  const faces=T.ShapeUtils.triangulateShape(g.outline.map(p=>new T.Vector2(...p)),[]);
  for(const [a,b,c]of faces){tri(point(0,c),point(0,b),point(0,a));tri(point(levels.length-1,a),point(levels.length-1,b),point(levels.length-1,c));}
  geo=new T.BufferGeometry();geo.setAttribute('position',new T.Float32BufferAttribute(verts,3));geo.computeVertexNormals();
 }else if(g.shape==='cylinder'){
  geo=new T.CylinderGeometry(g.radiusTop,g.radius,g.depth,g.segments||64,1);if(g.axis==='Z')geo.rotateX(Math.PI/2);
 }else if(g.shape==='torus'){
  geo=new T.TorusGeometry(g.radius,g.tube,12,96);if(g.axis==='Y')geo.rotateX(Math.PI/2);
 }else throw Error('Unknown shape '+g.shape);
 // Consistent box projection in model units, including lofts without native UVs.
 const pos=geo.attributes.position,norm=geo.attributes.normal,uv=new Float32Array(pos.count*2);
 for(let i=0;i<pos.count;i++){const x=pos.getX(i),y=pos.getY(i),z=pos.getZ(i),nx=Math.abs(norm.getX(i)),ny=Math.abs(norm.getY(i)),nz=Math.abs(norm.getZ(i));if(nz>=nx&&nz>=ny){uv[i*2]=x;uv[i*2+1]=y;}else if(ny>=nx){uv[i*2]=x;uv[i*2+1]=z;}else{uv[i*2]=y;uv[i*2+1]=z;}}
 geo.setAttribute('uv',new T.BufferAttribute(uv,2));return geo;
}
export function makePart(data,mats){
 const root=new T.Group();root.name=data.id;root.userData={partId:data.id,version:data.version,attachments:data.attachments,functionalPoints:data.functionalPoints};
 for(const g of data.geometry){const mesh=new T.Mesh(geometry(g),mats[g.material]);mesh.name=g.id;mesh.position.fromArray(g.position);if(g.rotationEulerXYZ)mesh.rotation.set(...g.rotationEulerXYZ);mesh.castShadow=true;mesh.receiveShadow=true;root.add(mesh);}
 return root;
}
export async function build(partId=null){
 const mats=await materials(),root=new T.Group();root.name='CHT-T01';const nodes={},defs={};
 if(partId){const d=await loadJSON('../../Parts/'+partId+'/part.json');defs[d.id]=d;root.add(makePart(d,mats));return {root,nodes,defs,mats,assembly:null};}
 const assembly=await loadJSON('assembly.json');
 for(const i of assembly.instances){if(!defs[i.partId])defs[i.partId]=await loadJSON(i.source);const node=makePart(defs[i.partId],mats);node.name=i.id;node.position.fromArray(i.translation);node.rotation.fromArray([...i.rotationEulerXYZ,'XYZ']);node.scale.fromArray(i.scale);nodes[i.id]=node;(i.parent?nodes[i.parent]:root).add(node);}
 const track=new T.QuaternionKeyframeTrack('yaw.quaternion',[0,.75,1.5,2.25,3],[0,0,0,1,0,0,Math.SQRT1_2,Math.SQRT1_2,0,0,1,0,0,0,Math.SQRT1_2,-Math.SQRT1_2,0,0,0,-1]);
 root.animations=[new T.AnimationClip('yaw-demo',3,[track])];return {root,nodes,defs,mats,assembly};
}
