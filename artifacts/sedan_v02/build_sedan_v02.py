import bpy
import bmesh
import math
import os
from mathutils import Vector

ROOT = os.path.dirname(os.path.abspath(__file__))


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def coll(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def material(name, color, metallic=0.0, roughness=0.35, transmission=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Roughness'].default_value = roughness
    if 'Transmission Weight' in p.inputs:
        p.inputs['Transmission Weight'].default_value = transmission
    return m


def assign(o, m):
    o.data.materials.clear()
    o.data.materials.append(m)


def smooth(o):
    if o.type == 'MESH':
        for p in o.data.polygons:
            p.use_smooth = True


def bevel(o, width=.015, segments=3):
    md = o.modifiers.new('Edge refinement', 'BEVEL')
    md.width = width
    md.segments = segments
    md.limit_method = 'ANGLE'


def solidify(o, thickness=.012):
    md = o.modifiers.new('Panel thickness', 'SOLIDIFY')
    md.thickness = thickness


def mesh_object(name, verts, faces, material_, collection_):
    me = bpy.data.meshes.new(name + '.mesh')
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    collection_.objects.link(o)
    assign(o, material_)
    return o


def cube(name, loc, scale, mat, collection_, bevel_width=.02, rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rotation)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel_width: bevel(o, bevel_width, 3)
    assign(o, mat)
    for c in list(o.users_collection): c.objects.unlink(o)
    collection_.objects.link(o)
    return o


def uv_sphere(name, loc, scale, mat, collection_, segments=48, rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
    o = bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(o,mat); smooth(o)
    for c in list(o.users_collection): c.objects.unlink(o)
    collection_.objects.link(o)
    return o


def cyl(name, loc, radius, depth, mat, collection_, rotation=(math.pi/2,0,0), vertices=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rotation)
    o=bpy.context.object; o.name=name; assign(o,mat); bevel(o,.008,2); smooth(o)
    for c in list(o.users_collection): c.objects.unlink(o)
    collection_.objects.link(o)
    return o


def torus(name, loc, major, minor, mat, collection_, rotation=(math.pi/2,0,0), major_segments=64, minor_segments=20):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=major_segments, minor_segments=minor_segments, location=loc, rotation=rotation)
    o=bpy.context.object; o.name=name; assign(o,mat); smooth(o)
    for c in list(o.users_collection): c.objects.unlink(o)
    collection_.objects.link(o)
    return o


def curve(name, pts, radius, mat, collection_, cyclic=False):
    cu=bpy.data.curves.new(name+'.curve','CURVE'); cu.dimensions='3D'; cu.resolution_u=8
    cu.bevel_depth=radius; cu.bevel_resolution=3
    sp=cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts)-1)
    for b,p in zip(sp.bezier_points,pts):
        b.co=p; b.handle_left_type='AUTO'; b.handle_right_type='AUTO'
    sp.use_cyclic_u=cyclic
    o=bpy.data.objects.new(name,cu); collection_.objects.link(o); assign(o,mat)
    return o


def panel(name, verts, mat, collection_, thickness=.012, bevel_width=.012):
    o=mesh_object(name,verts,[tuple(range(len(verts)))],mat,collection_)
    if thickness: solidify(o,thickness)
    if bevel_width: bevel(o,bevel_width,3)
    return o


def set_origin(o, p):
    old=bpy.context.scene.cursor.location.copy(); bpy.context.scene.cursor.location=p
    bpy.context.view_layer.objects.active=o; o.select_set(True)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR'); o.select_set(False)
    bpy.context.scene.cursor.location=old


def body_surface(name, stations, mat, collection_):
    # Smooth editable longitudinal cage. Each station is x,width,bottom,shoulder,top.
    profile=[(-.62,0.00),(-.92,.10),(-1.00,.30),(-1.00,.70),(-.82,.91),(-.42,.985),(0,1.0),(.42,.985),(.82,.91),(1.0,.70),(1.0,.30),(.92,.10),(.62,0.0)]
    verts=[]
    for x,w,zb,zs,zt in stations:
        for yn,zn in profile:
            y=yn*w
            # Piecewise vertical distribution keeps shoulder crisp and top crowned.
            if zn <= .70: z=zb+(zs-zb)*(zn/.70)
            else: z=zs+(zt-zs)*((zn-.70)/.30)
            verts.append((x,y,z))
    n=len(profile); faces=[]
    for i in range(len(stations)-1):
        for j in range(n-1):
            a=i*n+j; faces.append((a,a+1,a+n+1,a+n))
    # underside closure and end caps
    for i in range(len(stations)-1):
        faces.append((i*n,(i+1)*n,(i+1)*n+n-1,i*n+n-1))
    faces.append(tuple(range(n-1,-1,-1)))
    last=(len(stations)-1)*n; faces.append(tuple(last+j for j in range(n)))
    o=mesh_object(name,verts,faces,mat,collection_); smooth(o)
    sub=o.modifiers.new('Controlled subdivision','SUBSURF'); sub.levels=2; sub.render_levels=2
    return o


def roof_surface(name, mat, collection_):
    xs=[-1.20,-.95,-.55,0,.48,.82]
    ys=[-.72,-.38,0,.38,.72]
    verts=[]
    for x in xs:
        # Longitudinal crown: peak around cabin center, taper to glass headers.
        zcenter=1.39 + .075*math.cos((x+.18)/2.05*math.pi)
        half=.72-(abs(x+.15)/1.45)*.08
        for y in ys:
            yy=y*(half/.72)
            z=zcenter-.075*(abs(yy)/half)**1.8
            verts.append((x,yy,z))
    faces=[]; ny=len(ys)
    for i in range(len(xs)-1):
        for j in range(ny-1):
            a=i*ny+j; faces.append((a,a+ny,a+ny+1,a+1))
    o=mesh_object(name,verts,faces,mat,collection_); solidify(o,.025); smooth(o)
    sub=o.modifiers.new('Roof subdivision','SUBSURF'); sub.levels=2; sub.render_levels=2
    return o


def door_grid(name,x0,x1,y,mat,collection_,front=True,side='left'):
    # Conforms to side tumblehome and lower character line; 3x3 editable grid.
    xs=[x0,(x0+x1)/2,x1]; zs=[.43,.78,1.10]
    verts=[]
    sign=1 if side=='left' else -1
    for z in zs:
        for x in xs:
            bulge=.012*(1-((x-(x0+x1)/2)/((x1-x0)/2))**2)
            yy=sign*(y+bulge-(max(z-.85,0)*.10))
            top=z
            if not front and z>1.0: top-=.04*((x0-x)/(x0-x1))
            verts.append((x,yy,top))
    faces=[]
    for r in range(2):
        for c in range(2):
            a=r*3+c; faces.append((a,a+1,a+4,a+3))
    o=mesh_object(name,verts,faces,mat,collection_); solidify(o,.014*sign); smooth(o)
    sub=o.modifiers.new('Door surface','SUBSURF'); sub.levels=1; sub.render_levels=1
    bevel(o,.006,2)
    o['component_id']=name
    set_origin(o,(x1,sign*y,.78))
    return o


def wheel(name,x,y,mats,collection_):
    side='left' if y>0 else 'right'; cid=f'wheel.{name}.{side}'
    tire=torus(cid,(x,y,.39),.285,.095,mats['tire'],collection_); tire['component_id']=cid
    rim=cyl(cid+'.rim',(x,y,.39),.225,.115,mats['alloy'],collection_,vertices=64)
    # Ten paired directional spokes.
    outward=.065 if y>0 else -.065
    for i in range(10):
        a=i*math.tau/10
        px=x+math.cos(a)*.12; pz=.39+math.sin(a)*.12
        s=cube(cid+f'.spoke.{i:02d}',(px,y+outward,pz),(.125,.012,.018),mats['alloy'],collection_,.008,rotation=(0,a,0))
    cyl(cid+'.hub',(x,y+outward*1.1,.39),.055,.14,mats['dark'],collection_,vertices=40)
    return tire


def build():
    reset(); sc=bpy.context.scene
    sc.unit_settings.system='METRIC'; sc.unit_settings.length_unit='METERS'; sc.unit_settings.scale_length=1
    sc.render.engine='BLENDER_EEVEE'; sc.render.resolution_x=1024; sc.render.resolution_y=640; sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG'; sc.view_settings.look='AgX - Medium High Contrast'
    sc.render.film_transparent=False

    M={
      'paint':material('body_paint',(0.46,.50,.55),.72,.22),
      'glass':material('glass',(0.018,.035,.055),.15,.12,.18),
      'rubber':material('window_rubber',(.012,.014,.017),.05,.48),
      'dark':material('dark_trim',(.025,.03,.038),.55,.25),
      'chrome':material('chrome',(.56,.62,.68),.92,.12),
      'tire':material('tire',(.012,.014,.016),.03,.5),
      'alloy':material('wheel_alloy',(.34,.38,.42),.88,.18),
      'lamp':material('headlamp_lens',(.55,.69,.80),.28,.12,.12),
      'tail':material('taillamp_lens',(.38,.008,.012),.35,.16,.06),
      'interior':material('interior',(.035,.04,.047),.08,.52),
    }
    C={k:coll(k.upper()) for k in ['body','glass','trim','lights','wheels','interior','stage']}

    stations=[
      (-2.28,.57,.31,.64,.73),(-2.16,.76,.28,.77,.84),(-1.90,.84,.25,.86,.91),
      (-1.52,.87,.23,.91,.95),(-1.12,.88,.22,.94,.98),(-.60,.885,.21,.95,.99),
      (0,.89,.21,.96,1.00),(.55,.89,.21,.95,.99),(1.05,.88,.22,.93,.98),
      (1.52,.87,.23,.89,.94),(1.92,.83,.26,.82,.88),(2.18,.72,.29,.70,.78),(2.27,.52,.34,.59,.67)
    ]
    shell=body_surface('body.shell',stations,M['paint'],C['body']); shell['component_id']='body.shell'
    roof=roof_surface('body.roof',M['paint'],C['body']); roof['component_id']='body.roof'

    # Doors sit flush on the continuous side skin, not as floating slabs.
    for side in ('left','right'):
        sign=1 if side=='left' else -1
        df=door_grid(f'body.door.front.{side}',-.08,.82,.889,M['paint'],C['body'],True,side)
        dr=door_grid(f'body.door.rear.{side}',-1.08,-.12,.889,M['paint'],C['body'],False,side)
        for pos,x in [('front',.55),('rear',-.82)]:
            cube(f'trim.handle.{pos}.{side}',(x,sign*.902,1.015),(.10,.014,.022),M['chrome'],C['trim'],.014)

    # Closed hood and trunk are curved panels following the body envelope.
    hood=panel('body.hood',[(.76,-.70,.99),(2.05,-.60,.79),(2.05,.60,.79),(.76,.70,.99)],M['paint'],C['body'],.025,.028)
    hood['component_id']='body.hood'; set_origin(hood,(.76,0,.99))
    trunk=panel('body.trunk_lid',[(-2.08,-.61,.82),(-1.25,-.69,.97),(-1.25,.69,.97),(-2.08,.61,.82)],M['paint'],C['body'],.025,.026)
    trunk['component_id']='body.trunk_lid'; set_origin(trunk,(-1.25,0,.97))
    fb=panel('body.bumper.front',[(2.275,-.66,.36),(2.31,-.52,.68),(2.31,.52,.68),(2.275,.66,.36)],M['paint'],C['body'],.035,.035); fb['component_id']='body.bumper.front'
    rb=panel('body.bumper.rear',[(-2.275,.66,.35),(-2.31,.55,.67),(-2.31,-.55,.67),(-2.275,-.66,.35)],M['paint'],C['body'],.035,.035); rb['component_id']='body.bumper.rear'

    # Glazing from coherent corner points; dark surrounds hide tiny construction gaps.
    windshield=panel('glass.windshield.front',[(.82,-.67,1.02),(.55,-.61,1.39),(.55,.61,1.39),(.82,.67,1.02)],M['glass'],C['glass'],.012,.014); windshield['component_id']='glass.windshield.front'
    rear_glass=panel('glass.windshield.rear',[(-1.28,.60,1.00),(-.95,.61,1.36),(-.95,-.61,1.36),(-1.28,-.60,1.00)],M['glass'],C['glass'],.012,.014); rear_glass['component_id']='glass.windshield.rear'
    for side in ('left','right'):
        s=1 if side=='left' else -1; y=s*.766
        fw=panel(f'glass.door.front.{side}',[(-.08,y,1.10),(.73,y,1.10),(.48,y,1.37),(-.04,y,1.41)],M['glass'],C['glass'],.010*s,.010)
        rw=panel(f'glass.door.rear.{side}',[(-1.05,y,1.08),(-.12,y,1.10),(-.08,y,1.40),(-.74,y,1.31)],M['glass'],C['glass'],.010*s,.010)
        fw['component_id']=f'glass.door.front.{side}'; rw['component_id']=f'glass.door.rear.{side}'
        # Pillars and continuous window surround.
        for nm,pts,r in [
          ('a',[(.82,y,1.01),(.52,y,1.40)],.026),('b',[(-.09,y,1.08),(-.06,y,1.42)],.032),
          ('c',[(-1.28,y,1.00),(-.92,y,1.36)],.032),('belt',[(-1.31,y,1.075),(.83,y,1.075)],.018),
          ('roof',[(-.94,y,1.38),(-.20,y,1.47),(.53,y,1.41)],.020)]:
            curve(f'trim.pillar.{nm}.{side}',pts,r,M['rubber'],C['trim'])

    # Mirrors with painted caps and dark bases.
    for side in ('left','right'):
        s=1 if side=='left' else -1
        mir=uv_sphere(f'body.mirror.{side}',(.62,s*.94,1.08),(.15,.095,.065),M['paint'],C['body']); mir['component_id']=f'body.mirror.{side}'
        cube(f'trim.mirror_base.{side}',(.59,s*.86,1.055),(.055,.075,.032),M['dark'],C['trim'],.022)

    # Front V-motion inspired graphic, deliberately generic and logo-free.
    grille=panel('trim.grille.front',[(2.295,-.56,.72),(2.33,-.42,.39),(2.33,.42,.39),(2.295,.56,.72)],M['dark'],C['trim'],.024,.025)
    for z in (.43,.49,.55,.61,.67):
        curve(f'trim.grille.slat.{z:.2f}',[(2.352,-.39,z),(2.36,0,z-.018),(2.352,.39,z)],.009,M['chrome'],C['trim'])
    curve('trim.grille.v.left',[(2.36,-.58,.75),(2.38,-.43,.39),(2.37,0,.34)],.027,M['chrome'],C['trim'])
    curve('trim.grille.v.right',[(2.36,.58,.75),(2.38,.43,.39),(2.37,0,.34)],.027,M['chrome'],C['trim'])
    # Angular headlamps and lower intakes.
    for side in ('left','right'):
        s=1 if side=='left' else -1
        verts=[(2.18,s*.55,.79),(2.05,s*.83,.78),(1.72,s*.84,.72),(1.94,s*.55,.68)]
        if side=='right': verts.reverse()
        h=panel(f'light.headlamp.{side}',verts,M['lamp'],C['lights'],.025,.018); h['component_id']=f'light.headlamp.{side}'
        curve(f'light.drl.{side}',[(2.17,s*.56,.78),(1.93,s*.73,.75),(1.74,s*.82,.72)],.013,M['chrome'],C['lights'])
        panel(f'trim.intake.front.{side}',[(2.305,s*.53,.54),(2.31,s*.72,.50),(2.25,s*.71,.30),(2.30,s*.48,.34)],M['dark'],C['trim'],.018,.018)

    # Tail lamps spanning quarter panel into trunk.
    for side in ('left','right'):
        s=1 if side=='left' else -1
        verts=[(-2.16,s*.58,.78),(-2.04,s*.82,.78),(-1.68,s*.84,.72),(-1.88,s*.55,.68)]
        if side=='left': verts.reverse()
        t=panel(f'light.tail.{side}',verts,M['tail'],C['lights'],.025,.018); t['component_id']=f'light.tail.{side}'
    curve('trim.trunk_edge',[(-2.15,-.56,.69),(-2.21,0,.66),(-2.15,.56,.69)],.012,M['chrome'],C['trim'])

    # Wheel arches are continuous painted arcs close to tire diameter.
    for axle,x in [('front',1.34),('rear',-1.42)]:
        for side in ('left','right'):
            s=1 if side=='left' else -1; pts=[]
            for i in range(13):
                a=math.pi*i/12
                pts.append((x-.385*math.cos(a),s*.895,.39+.385*math.sin(a)))
            curve(f'body.wheel_arch.{axle}.{side}',pts,.032,M['paint'],C['body'])
    for x,nm in [(1.34,'front'),(-1.42,'rear')]:
        wheel(nm,x,.90,M,C['wheels']); wheel(nm,x,-.90,M,C['wheels'])

    # Minimal interior silhouette visible through glazing.
    for side,y in [('left',.35),('right',-.35)]:
        cube(f'interior.seat.front.{side}',(.12,y,.75),(.29,.24,.11),M['interior'],C['interior'],.08)
        cube(f'interior.seat.front.{side}.back',(-.02,y,.99),(.10,.24,.29),M['interior'],C['interior'],.08,rotation=(0,-.10,0))
        cube(f'interior.seat.front.{side}.head',(-.08,y,1.24),(.08,.15,.11),M['interior'],C['interior'],.05)
    cube('interior.rear_seat',(-.72,0,.76),(.28,.62,.12),M['interior'],C['interior'],.08)
    cube('interior.dashboard',(.62,0,.95),(.14,.64,.10),M['interior'],C['interior'],.06)

    # Studio cyclorama and floor are never exported.
    floor=cube('stage.floor',(0,0,-.04),(5.5,5.5,.05),material('studio_floor',(.16,.17,.18),.12,.32),C['stage'],.02)
    sc['asset_name']='eGarage Compact Sedan v02'; sc['axis_convention']='X forward, Y driver-left, Z up'; sc['units']='meters'
    sc['reference_note']='Generic compact sedan inspired by approved 4-view art; no manufacturer branding'
    return M,C


def aim(o,target=(0,0,.72)):
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()


def lighting():
    world=bpy.context.scene.world or bpy.data.worlds.new('Studio World'); bpy.context.scene.world=world; world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(.055,.06,.07,1); world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45
    for name,loc,energy,size,color in [
      ('Key',(4,3.8,5.5),1300,4.5,(1,.95,.90)),('Fill',(1,-4,3),850,3.5,(.55,.68,1)),
      ('Rim',(-4,2.5,3.8),1100,3,(.55,.72,1)),('Top',(-.2,0,6),900,3.5,(1,1,1))]:
        bpy.ops.object.light_add(type='AREA',location=loc); l=bpy.context.object; l.name=name; l.data.energy=energy; l.data.shape='DISK'; l.data.size=size; l.data.color=color; aim(l)


VIEWS={
 'front':((6.6,0,1.35),(.35,0,.70),62),
 'rear':((-6.6,0,1.35),(-.35,0,.70),62),
 'left':((0,7.2,1.45),(0,0,.72),64),
 'front_three_quarter':((5.4,4.5,2.55),(.12,0,.72),58),
 'rear_three_quarter':((-5.3,-4.5,2.35),(-.12,0,.72),58),
}


def camera(loc,target,lens):
    bpy.ops.object.camera_add(location=loc); c=bpy.context.object; c.data.lens=lens; aim(c,target); bpy.context.scene.camera=c; return c


def render_views():
    sc=bpy.context.scene
    for name,(loc,target,lens) in VIEWS.items():
        c=camera(loc,target,lens); sc.render.filepath=os.path.join(ROOT,'renders','silver',f'silver_{name}.png'); bpy.ops.render.render(write_still=True); bpy.data.objects.remove(c,do_unlink=True)


def render_colors(M):
    sc=bpy.context.scene
    colors={'silver':(.46,.50,.55,1),'red':(.42,.012,.018,1),'white':(.82,.84,.86,1)}
    c=camera(*VIEWS['front_three_quarter'])
    p=M['paint'].node_tree.nodes['Principled BSDF']
    for name,color in colors.items():
        M['paint'].diffuse_color=color; p.inputs['Base Color'].default_value=color
        sc.render.filepath=os.path.join(ROOT,'renders','colors',f'color_{name}.png'); bpy.ops.render.render(write_still=True)
    # Delivered source and GLB default to approved silver.
    M['paint'].diffuse_color=colors['silver']; p.inputs['Base Color'].default_value=colors['silver']
    bpy.data.objects.remove(c,do_unlink=True)


def freeze_clean_export(C):
    for o in list(bpy.context.scene.objects):
        if o.type!='MESH' or o.name.startswith('stage.'): continue
        bpy.context.view_layer.objects.active=o; o.select_set(True)
        for md in list(o.modifiers):
            try: bpy.ops.object.modifier_apply(modifier=md.name)
            except RuntimeError: pass
        bm=bmesh.new(); bm.from_mesh(o.data); bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges)); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(o.data); bm.free(); o.data.validate(clean_customdata=False); o.select_set(False)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'sedan_v02.blend'))
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.context.scene.objects:
        if o.type in {'MESH','CURVE'} and not o.name.startswith('stage.'): o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'sedan_v02.glb'),export_format='GLB',use_selection=True,export_apply=True,export_extras=True)


if __name__=='__main__':
    os.makedirs(os.path.join(ROOT,'renders','silver'),exist_ok=True); os.makedirs(os.path.join(ROOT,'renders','colors'),exist_ok=True)
    M,C=build(); lighting()
    if os.environ.get('SEDAN_PREVIEW')=='1':
        bpy.context.scene.render.resolution_x=768; bpy.context.scene.render.resolution_y=480
        c=camera(*VIEWS['front_three_quarter']); bpy.context.scene.render.filepath=os.path.join(ROOT,'preview.png'); bpy.ops.render.render(write_still=True)
    else:
        render_views(); render_colors(M); freeze_clean_export(C)
    print('SEDAN_V02_COMPLETE')
