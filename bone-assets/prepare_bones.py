"""Prepare redistributable BodyParts3D meshes for the synchronized hip teaching view.

Source: BodyParts3D 3.0, DBCLS; STL conversion by Kevin Mattheus Moerman.
Current original-database license: CC BY 4.0, updated 2025-02-27.
The meshes provide reference morphology, not subject-specific exercise kinematics.
"""
import base64
import json
import struct
import urllib.request
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
BASE = 'https://raw.githubusercontent.com/Kevin-Mattheus-Moerman/BodyParts3D/main/assets/BodyParts3D_data/stl/'
PARTS = {'hipR':16586,'hipL':16587,'sacrum':16202,'femurR':24474,'femurL':24475}

def read_stl(path):
    raw = path.read_bytes()
    n = struct.unpack_from('<I', raw, 80)[0]
    dtype = np.dtype([('normal','<f4',(3,)),('v','<f4',(3,3)),('attr','<u2')])
    triangles = np.frombuffer(raw, dtype=dtype, count=n, offset=84)['v'].copy()
    return triangles

def download():
    for name, fma in PARTS.items():
        path = ROOT / f'FMA{fma}.stl'
        if not path.exists():
            urllib.request.urlretrieve(BASE + path.name, path)
        tri = read_stl(path)
        print(name, 'triangles', len(tri), 'min', tri.min((0,1)), 'max',tri.max((0,1)), flush=True)

def fit_head(tri, side):
    """Robust sphere fit to the proximal medial head, excluding shaft and neck.

    Four points define a candidate sphere. Retain a plausible 15–30 mm radius
    candidate with many <0.7 mm residuals, then refine on those inliers.
    This locates an approximate rotation center, not a clinical measurement.
    """
    points=np.unique(tri.reshape(-1,3),axis=0)
    roi=points[(points[:,2]>795)&(points[:,0]*side<82)]
    rng=np.random.default_rng(4)
    best=None
    for _ in range(2500):
        v=roi[rng.choice(len(roi),4,replace=False)]
        A=2*(v[1:]-v[0]); b=(v[1:]**2).sum(1)-(v[0]**2).sum()
        try: center=np.linalg.solve(A,b)
        except np.linalg.LinAlgError: continue
        radius=np.linalg.norm(v[0]-center)
        if not(15<radius<30 and 35<center[0]*side<80 and 795<center[2]<840):continue
        err=np.abs(np.linalg.norm(roi-center,axis=1)-radius)
        keep=err<.7
        score=int(keep.sum())
        if best is None or score>best[0]:best=(score,center,radius,keep)
    if best is None:raise RuntimeError('Head sphere fit failed')
    pts=roi[best[3]]
    A=np.column_stack((2*pts,np.ones(len(pts)))); b=(pts**2).sum(1)
    sol=np.linalg.lstsq(A,b,rcond=None)[0];center=sol[:3];radius=np.sqrt(sol[3]+(center**2).sum())
    residual=np.abs(np.linalg.norm(pts-center,axis=1)-radius)
    print('head',side,center,'radius',radius,'inliers',len(pts),'mean residual',residual.mean(),flush=True)
    return center,radius

def compact_mesh(tri, cell):
    """Cluster nearby vertices; remove collapsed faces and compute smooth area-weighted normals."""
    flat=tri.reshape(-1,3)
    _,index=np.unique(np.round(flat/cell).astype(np.int32),axis=0,return_inverse=True)
    count=np.bincount(index)
    vertices=np.column_stack([np.bincount(index,weights=flat[:,j])/count for j in range(3)])
    faces=index.reshape(-1,3)
    faces=faces[(faces[:,0]!=faces[:,1])&(faces[:,1]!=faces[:,2])&(faces[:,0]!=faces[:,2])]
    _,keep=np.unique(np.sort(faces,axis=1),axis=0,return_index=True);faces=faces[np.sort(keep)]
    used,reindex=np.unique(faces,return_inverse=True);vertices=vertices[used];faces=reindex.reshape(-1,3)
    return vertices,faces

def prepare():
    meshes={k:read_stl(ROOT/f'FMA{v}.stl') for k,v in PARTS.items()}
    heads={key:fit_head(meshes[key],side) for key,side in [('femurR',-1),('femurL',1)]}
    origin=(heads['femurR'][0]+heads['femurL'][0])/2
    scale=.32/(heads['femurL'][0][0]-heads['femurR'][0][0])
    # Native data axes: x lateral, y posterior, z superior. Viewer: x lateral, y up, z forward.
    def transform(x):
        q=(x-origin)*scale
        return q[..., [0,2,1]]*np.array([1,1,-1])
    data={'source':'BodyParts3D 3.0 / DBCLS, STL conversion: Kevin Mattheus Moerman','license':'CC BY 4.0 (original database, 2025-02-27)','heads':{},'parts':{},'positionScale':20000}
    for key,(center,radius) in heads.items():
        data['heads'][key]={'center':transform(center).round(6).tolist(),'radius':float(radius*scale)}
    for key,tri in meshes.items():
        if key.startswith('femur'):
            # Keep the femoral head, neck, trochanters and proximal shaft. Distal cut is intentional.
            threshold=heads[key][0][2]-170
            tri=tri[(tri[:,:,2]>threshold).all(axis=1)]
        vertices,faces=compact_mesh(tri,1.4 if key=='sacrum' else .50)
        vertices=transform(vertices)
        normals=np.zeros_like(vertices)
        triNormal=np.cross(vertices[faces[:,1]]-vertices[faces[:,0]],vertices[faces[:,2]]-vertices[faces[:,0]])
        for j in range(3):np.add.at(normals,faces[:,j],triNormal)
        normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-12)
        packed={'fma':PARTS[key],'p':base64.b64encode(np.round(vertices*20000).astype('<i2').tobytes()).decode(),'n':base64.b64encode(np.round(normals*127).astype('i1').tobytes()).decode(),'i':base64.b64encode(faces.astype('<u2').tobytes()).decode()}
        data['parts'][key]=packed
        np.savez(ROOT/(key+'.npz'),vertices=vertices,faces=faces)
        print(key,'packed',len(vertices),'vertices',len(faces),'faces',flush=True)
    (ROOT/'bones.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
    print('JSON bytes',(ROOT/'bones.json').stat().st_size,flush=True)

if __name__ == '__main__':
    download()
    prepare()
