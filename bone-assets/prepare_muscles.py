"""Pack real BodyParts3D muscle surfaces with teaching skinning weights.

Coordinates stay registered to the original pelvis and femora. The muscle
surface is anatomical reference data; its animation is an approximation.
"""
import base64
import json
import urllib.request
import sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from prepare_bones import ROOT, BASE, read_stl, compact_mesh
sys.path.insert(0,str(ROOT/'mesh-deps'))
from fast_simplification import simplify

MUSCLES = {'max':22328, 'med':22330, 'min':22332, 'pir':22340,
           'iliacus':22322, 'psoas':22342, 'adduct':22452}
ORIGIN = np.array([-.44452577,-92.853442595,820.032373795])
SCALE = .32/(79.99367073+80.88272227)

def download(item):
    key,fma=item
    path=ROOT/f'FMA{fma}.stl'
    if not path.exists(): urllib.request.urlretrieve(BASE+path.name,path)
    return key,read_stl(path)

def pack(vertices,faces,**extra):
    # Normals are reconstructed in the viewer, saving a third array per mesh.
    return dict(p=base64.b64encode(np.round(vertices*20000).astype('<i2').tobytes()).decode(),
                i=base64.b64encode(faces.astype('<u2').tobytes()).decode(),**extra)

def transform(v):
    return ((v-ORIGIN)*SCALE)[:,[0,2,1]]*np.array([1,1,-1])

def decimate(tri,target):
    """Quadric edge collapse prioritizes preserving the reference surface.

    Unlike spatial clustering, nearby opposing sides of a thin muscle aren't
    merged just because they fall in one grid cell. This avoids tiny holes.
    """
    v,index=np.unique(tri.reshape(-1,3),axis=0,return_inverse=True)
    return simplify(v,index.reshape(-1,3),target_count=target,agg=5,preserve_border=True)

def main():
    data=json.loads((ROOT/'bones.json').read_text())
    # Sacrum's reference tessellation is much denser than the other bones.
    # Cluster it to a comparable visual resolution without altering the joint.
    v,f=decimate(read_stl(ROOT/'FMA16202.stl'),8000)
    data['parts']['sacrum']=pack(transform(v),f,fma=16202)
    for key,fma in [('femurR',24474),('femurL',24475)]:
        # Include enough proximal shaft to show the adductor brevis insertion.
        tri=read_stl(ROOT/f'FMA{fma}.stl');tri=tri[(tri[:,:,2]>600).all(1)]
        v,f=compact_mesh(tri,.5);data['parts'][key]=pack(transform(v),f,fma=fma)
    for part in data['parts'].values(): part.pop('n',None)
    data['muscles']={}
    for key,tri in ThreadPoolExecutor(max_workers=4).map(download,MUSCLES.items()):
        # The viewer presents the hip, so omit the upper lumbar part of psoas.
        if key=='psoas':tri=tri[(tri[:,:,2]<965).all(1)]
        print(key,'bounds',tri.min((0,1)).round(1),tri.max((0,1)).round(1),flush=True)
        v,f=decimate(tri,{'max':6000,'med':4000,'min':2600,'pir':1800,'iliacus':3600,'psoas':3000,'adduct':2200}[key])
        data['muscles'][key]=pack(transform(v),f,fma=MUSCLES[key])
        np.savez(ROOT/(key+'.npz'),vertices=transform(v),faces=f)
        print(key,'vertices',len(v),'faces',len(f),flush=True)
    out=ROOT/'anatomy.json';out.write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
    print('total JSON bytes',out.stat().st_size,flush=True)

if __name__=='__main__':main()
