import bpy, bmesh, math, os, sys, json, time, traceback
from mathutils import Vector, Matrix

ROOT=os.path.dirname(os.path.abspath(__file__))
SRC=os.path.join(ROOT,'source','graphite-four-door-sedan_cc0.glb')
CHECKPOINT=os.path.join(ROOT,'render_checkpoint.json')
BUILD_SEED=20261016
BODY_SCALE=(.94,.96,1.0)
BEZEL_REDUCTION=.20


def mat(name,color,metal=.0,rough=.3,trans=0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes=True; m.diffuse_color=(*color,1)
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    if 'Transmission Weight' in p.inputs:p.inputs['Transmission Weight'].default_value=trans
    return m


def center_world(o):
    return sum((o.matrix_world@Vector(c) for c in o.bound_box),Vector())/8


def normalize_scene():
    bpy.ops.object.select_all(action='SELECT')
    # Source points toward -X. Rotate into eGarage convention (+X forward),
    # shorten to a compact 4.50 m sedan, retain realistic height.
    bpy.ops.transform.rotate(value=math.pi,orient_axis='Z')
    bpy.ops.transform.resize(value=BODY_SCALE)
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)


def replace_materials():
    paint=mat('body_paint',(.48,.52,.57),.72,.20)
    glass=mat('vehicle_glass',(.025,.040,.055),.12,.16,.06)
    rubber=mat('rubber_trim',(.008,.010,.013),.02,.52)
    for o in bpy.context.scene.objects:
        if o.type!='MESH':continue
        for i,m in enumerate(list(o.data.materials)):
            if not m:continue
            n=m.name.lower()
            if n.startswith('paint'):o.data.materials[i]=paint
            elif n.startswith('glass'):o.data.materials[i]=glass
            elif n.startswith('rubber'):o.data.materials[i]=rubber
    return paint


def extract_faces(src,name,predicate,offset=(0,0,0)):
    verts=[];faces=[];mapping={};mats=list(src.data.materials)
    for poly in src.data.polygons:
        c=poly.center
        if not predicate(c,poly.normal):continue
        face=[]
        for vi in poly.vertices:
            if vi not in mapping:
                mapping[vi]=len(verts); v=src.data.vertices[vi].co; verts.append((v.x+offset[0],v.y+offset[1],v.z+offset[2]))
            face.append(mapping[vi])
        faces.append((face,poly.material_index))
    me=bpy.data.meshes.new(name+'.mesh'); me.from_pydata(verts,[],[f for f,_ in faces]);me.update()
    for m in mats:me.materials.append(m)
    for p,(_,mi) in zip(me.polygons,faces):p.material_index=mi;p.use_smooth=True
    o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);o['component_id']=name;o['source']='CC0 surface extraction from body shell'
    return o


def set_origin(o,p):
    old=bpy.context.scene.cursor.location.copy();bpy.context.scene.cursor.location=p;bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.origin_set(type='ORIGIN_CURSOR');o.select_set(False);bpy.context.scene.cursor.location=old


def make_panels():
    shell=bpy.data.objects.get('Watertight 14-station body shell')
    if not shell:raise RuntimeError('Source body shell not found')
    # Coordinates after normalization: +X front, +Y driver-left.
    specs=[
      ('body.door.front.left',lambda c,n:c.y>.70 and -.05<c.x<1.02 and .30<c.z<1.13,(0,.0015,0),(1.02,.86,.70)),
      ('body.door.front.right',lambda c,n:c.y<-.70 and -.05<c.x<1.02 and .30<c.z<1.13,(0,-.0015,0),(1.02,-.86,.70)),
      ('body.door.rear.left',lambda c,n:c.y>.70 and -1.14<c.x<-.06 and .30<c.z<1.13,(0,.0015,0),(-.06,.86,.70)),
      ('body.door.rear.right',lambda c,n:c.y<-.70 and -1.14<c.x<-.06 and .30<c.z<1.13,(0,-.0015,0),(-.06,-.86,.70)),
      ('body.hood',lambda c,n:c.x>.60 and c.z>.82 and n.z>.35,(0,0,.0015),(.60,0,1.02)),
      ('body.trunk_lid',lambda c,n:c.x<-1.20 and c.z>.78 and n.z>.30,(0,0,.0015),(-1.20,0,.94)),
      ('body.bumper.front',lambda c,n:c.x>2.05 and c.z<.78,(.0015,0,0),(2.05,0,.60)),
      ('body.bumper.rear',lambda c,n:c.x<-2.05 and c.z<.78,(-.0015,0,0),(-2.05,0,.60)),
    ]
    out=[]
    for name,pred,off,pivot in specs:
        o=extract_faces(shell,name,pred,off);set_origin(o,pivot);out.append(o)
    return out


def map_semantics():
    # Glass objects.
    direct={'Raked laminated windshield':'glass.windshield.front','Sloping rear glass':'glass.windshield.rear'}
    for old,cid in direct.items():
        o=bpy.data.objects.get(old)
        if o:o.name=cid;o['component_id']=cid
    for prefix,base in [('Front side door glass','glass.door.front'),('Rear side door glass','glass.door.rear')]:
        objs=[o for o in bpy.context.scene.objects if o.name==prefix or o.name.startswith(prefix+'.')]
        for o in objs:
            side='left' if center_world(o).y>0 else 'right';o.name=f'{base}.{side}';o['component_id']=o.name
    # Mirrors.
    caps=[o for o in bpy.context.scene.objects if o.name.startswith('Aerodynamic mirror painted cap')]
    for o in caps:
        side='left' if center_world(o).y>0 else 'right';o.name=f'body.mirror.{side}';o['component_id']=o.name
    # Lamps.
    for prefix,base in [('Flush swept transparent headlamp lens','light.headlamp'),('Flush corner wrapping ruby lamp lens','light.tail')]:
        objs=[o for o in bpy.context.scene.objects if o.name==prefix or o.name.startswith(prefix+'.')]
        for o in objs:
            side='left' if center_world(o).y>0 else 'right';o.name=f'{base}.{side}';o['component_id']=o.name
    # Tyres identify complete wheel locations; nearby rim/brake detail remains separate.
    tyres=[o for o in bpy.context.scene.objects if 'Sculpted_tyre' in o.name]
    for o in tyres:
        c=center_world(o);ax='front' if c.x>0 else 'rear';side='left' if c.y>0 else 'right';o.name=f'wheel.{ax}.{side}';o['component_id']=o.name


def add_v_grille():
    chrome=bpy.data.materials.get('chrome') or mat('chrome',(.58,.62,.66),.92,.13)
    dark=bpy.data.materials.get('black.001') or mat('grille_black',(.01,.012,.015),.25,.3)
    def cv(name,pts,r,m):
        cu=bpy.data.curves.new(name+'.curve','CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=3;sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
        for b,p in zip(sp.points,pts):b.co=(*p,1)
        o=bpy.data.objects.new(name,cu);bpy.context.scene.collection.objects.link(o);o.data.materials.append(m);return o
    # The lower lip was 0.39 m tall. Raise its bottom by 20% (0.078 m)
    # and open the inner margin slightly so the central grille is less cramped.
    lower_z=.36+(.75-.36)*BEZEL_REDUCTION
    cv('trim.v_grille.left',[(2.248,.57,.75),(2.265,.43,.49),(2.27,.15,lower_z)],.014,chrome)
    cv('trim.v_grille.right',[(2.248,-.57,.75),(2.265,-.43,.49),(2.27,-.15,lower_z)],.014,chrome)


def setup_stage():
    # Ground plane only; never exported.
    m=mat('studio_floor',(.19,.20,.215),.05,.32)
    bpy.ops.mesh.primitive_plane_add(size=14,location=(0,0,.005));g=bpy.context.object;g.name='stage.floor';g.data.materials.append(m)
    w=bpy.data.worlds.new('Studio World');bpy.context.scene.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Color'].default_value=(.055,.06,.07,1);w.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
    for name,loc,en,size,color in [('Key',(5,4,6),1500,4.5,(1,.95,.9)),('Fill',(1,-5,3.5),900,4,(.58,.70,1)),('Rim',(-4,3,4.5),1200,3,(.62,.76,1)),('Top',(0,0,7),900,3.5,(1,1,1))]:
        bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.name=name;l.data.energy=en;l.data.shape='DISK';l.data.size=size;l.data.color=color;l.rotation_euler=(Vector((0,0,.7))-l.location).to_track_quat('-Z','Y').to_euler()


VIEWS={
 'front':((6.8,0,1.35),(.35,0,.70),64),
 'rear':((-6.8,0,1.35),(-.35,0,.70),64),
 'left':((0,7.3,1.45),(0,0,.70),66),
 'front_three_quarter':((5.4,4.6,2.45),(.10,0,.72),58),
 'rear_three_quarter':((-5.4,-4.6,2.35),(-.10,0,.72),58),
}


def checkpoint(status, completed=None, current=None, error=None):
    if completed is None and os.path.isfile(CHECKPOINT):
        try:
            with open(CHECKPOINT,encoding='utf-8') as f:completed=json.load(f).get('completed',[])
        except (OSError,ValueError):completed=[]
    data={
      'status':status,
      'updated_at':time.strftime('%Y-%m-%dT%H:%M:%S%z'),
      'seed':BUILD_SEED,
      'body_scale':BODY_SCALE,
      'bezel_reduction':BEZEL_REDUCTION,
      'views':VIEWS,
      'resolution':{'final':[1024,640],'draft':[640,400]},
      'completed':completed or [],
      'current':current,
      'error':error,
    }
    tmp=CHECKPOINT+'.tmp'
    with open(tmp,'w',encoding='utf-8') as f:json.dump(data,f,indent=2)
    os.replace(tmp,CHECKPOINT)


def valid_png(path):
    if not os.path.isfile(path) or os.path.getsize(path)<1000:return False
    with open(path,'rb') as f:return f.read(8)==b'\x89PNG\r\n\x1a\n'


def camera(loc,target,lens):
    bpy.ops.object.camera_add(location=loc);c=bpy.context.object;c.data.lens=lens;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();bpy.context.scene.camera=c;return c


def render_all(paint,preview=False,front_draft=False):
    s=bpy.context.scene;s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1024 if not (preview or front_draft) else 640;s.render.resolution_y=640 if not (preview or front_draft) else 400;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.look='AgX - Medium High Contrast'
    p=paint.node_tree.nodes['Principled BSDF']
    if front_draft:
        c=camera(*VIEWS['front']);s.render.filepath=os.path.join(ROOT,'front_bezel_draft.png');bpy.ops.render.render(write_still=True);return
    if preview:
        c=camera(*VIEWS['front_three_quarter']);s.render.filepath=os.path.join(ROOT,'cc0_preview.png');bpy.ops.render.render(write_still=True);return
    os.makedirs(os.path.join(ROOT,'renders','silver'),exist_ok=True);os.makedirs(os.path.join(ROOT,'renders','colors'),exist_ok=True)
    completed=[]
    for index,(name,v) in enumerate(VIEWS.items(),1):
        path=os.path.join(ROOT,'renders','silver',f'{index:02d}_silver_{name}.png')
        if valid_png(path):completed.append(os.path.relpath(path,ROOT));continue
        checkpoint('rendering',completed,os.path.relpath(path,ROOT));print(f'RENDER_START {path}',flush=True)
        c=camera(*v);s.render.filepath=path;bpy.ops.render.render(write_still=True);bpy.data.objects.remove(c,do_unlink=True)
        if not valid_png(path):raise RuntimeError(f'Render did not produce a valid PNG: {path}')
        completed.append(os.path.relpath(path,ROOT));checkpoint('rendering',completed);print(f'RENDER_OK {path}',flush=True)
    c=camera(*VIEWS['front_three_quarter'])
    colors={'silver':(.48,.52,.57,1),'red':(.48,.012,.018,1),'white':(.84,.85,.87,1)}
    for index,(n,color) in enumerate(colors.items(),len(VIEWS)+1):
        path=os.path.join(ROOT,'renders','colors',f'{index:02d}_color_{n}.png')
        if valid_png(path):completed.append(os.path.relpath(path,ROOT));continue
        checkpoint('rendering',completed,os.path.relpath(path,ROOT));print(f'RENDER_START {path}',flush=True)
        paint.diffuse_color=color;p.inputs['Base Color'].default_value=color;s.render.filepath=path;bpy.ops.render.render(write_still=True)
        if not valid_png(path):raise RuntimeError(f'Render did not produce a valid PNG: {path}')
        completed.append(os.path.relpath(path,ROOT));checkpoint('rendering',completed);print(f'RENDER_OK {path}',flush=True)
    paint.diffuse_color=colors['silver'];p.inputs['Base Color'].default_value=colors['silver'];bpy.data.objects.remove(c,do_unlink=True)


def export():
    s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.length_unit='METERS';s['axis_convention']='X forward, Y driver-left, Z up';s['source_license']='CC0 1.0 — Innerscene Graphite four-door sedan';s['art_direction']='eGarage compact sedan v02'
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'sedan_v02.blend'))
    bpy.ops.object.select_all(action='DESELECT')
    for o in s.objects:
        if o.type in {'MESH','CURVE','EMPTY'} and not o.name.startswith('stage.'):o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'sedan_v02.glb'),export_format='GLB',use_selection=True,export_apply=True,export_extras=True)


if __name__=='__main__':
    try:
        bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene['build_seed']=BUILD_SEED;bpy.ops.import_scene.gltf(filepath=SRC);normalize_scene();paint=replace_materials();make_panels();map_semantics();add_v_grille();setup_stage()
        preview=os.environ.get('SEDAN_PREVIEW')=='1';front_draft=os.environ.get('SEDAN_DRAFT')=='front'
        render_all(paint,preview,front_draft)
        if not preview and not front_draft:export();checkpoint('complete')
        elif front_draft:checkpoint('draft_complete')
        else:checkpoint('preview_complete')
        print('BUILD_FROM_CC0_COMPLETE',flush=True)
        # Blender 5.2.2 can block during headless audio teardown in this
        # environment. All files/checkpoints are closed above, so terminate
        # the batch process explicitly with the successful status.
        sys.stdout.flush();sys.stderr.flush();os._exit(0)
    except Exception:
        error=traceback.format_exc();checkpoint('failed',error=error);print(error,flush=True);raise
