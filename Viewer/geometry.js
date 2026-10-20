import * as T from './vendor/three.module.js';
import {RoundedBoxGeometry} from './vendor/RoundedBoxGeometry.js';
export {T};
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
 }else if(g.shape==='lathe'){
  geo=new T.LatheGeometry(g.profile.map(p=>new T.Vector2(...p)),g.segments||48,g.phiStart||0,g.phiLength??Math.PI*2);
  if(g.axis==='Z')geo.rotateX(Math.PI/2);else if(g.axis==='X')geo.rotateZ(-Math.PI/2);
 }else if(g.shape==='profile'){
  const makePath=(points,Path)=>{const p=new Path();p.moveTo(...points[0]);for(const xy of points.slice(1))p.lineTo(...xy);p.closePath();return p;};
  const shape=makePath(g.outline,T.Shape);for(const hole of g.holes||[])shape.holes.push(makePath(hole,T.Path));
  const bevel=Math.min(g.bevel||0,g.depth*.45);
  geo=new T.ExtrudeGeometry(shape,{depth:g.depth-2*bevel,bevelEnabled:bevel>0,bevelThickness:bevel,bevelSize:bevel,bevelSegments:2,steps:1,curveSegments:24});geo.translate(0,0,-g.depth/2+bevel);
 }else if(g.shape==='cylinder'){
  geo=new T.CylinderGeometry(g.radiusTop,g.radius,g.depth,g.segments||64,1);if(g.axis==='Z')geo.rotateX(Math.PI/2);else if(g.axis==='X')geo.rotateZ(-Math.PI/2);
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
