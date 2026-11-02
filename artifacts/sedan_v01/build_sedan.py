import bpy
import bmesh
import math
import os
from mathutils import Vector

OUT = os.path.dirname(os.path.abspath(__file__))


def clear():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        pass


def mat(name, color, metallic=0.0, rough=0.35, transmission=0.0, emission=None, emission_strength=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = rough
    if 'Transmission Weight' in bsdf.inputs:
        bsdf.inputs['Transmission Weight'].default_value = transmission
    if emission:
        bsdf.inputs['Emission Color'].default_value = (*emission, 1.0)
        bsdf.inputs['Emission Strength'].default_value = emission_strength
    return m


def collection(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def move_to(obj, coll):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)


def assign(obj, material):
    if obj.data and hasattr(obj.data, 'materials'):
        obj.data.materials.clear()
        obj.data.materials.append(material)


def bevel(obj, amount=0.08, segments=3):
    mod = obj.modifiers.new('Surface bevel', 'BEVEL')
    mod.width = amount
    mod.segments = segments
    mod.limit_method = 'ANGLE'
    return obj


def smooth(obj, angle=0.65):
    if obj.type == 'MESH':
        for p in obj.data.polygons:
            p.use_smooth = True
        obj.data.set_sharp_from_angle(angle=angle)
    return obj


def cube(name, loc, scale, material, coll, bevel_amt=0.04, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rotation)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel(o, bevel_amt, 3)
    assign(o, material)
    move_to(o, coll)
    return o


def uv_sphere(name, loc, scale, material, coll, seg=32, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(o, material)
    smooth(o)
    move_to(o, coll)
    return o


def cylinder(name, loc, radius, depth, material, coll, rotation=(math.pi/2, 0, 0), vertices=32, bevel_amt=0.02):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rotation)
    o = bpy.context.object
    o.name = name
    bevel(o, bevel_amt, 2)
    assign(o, material)
    smooth(o)
    move_to(o, coll)
    return o


def torus(name, loc, major, minor, material, coll, rotation=(math.pi/2, 0, 0), major_seg=40, minor_seg=12):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=major_seg, minor_segments=minor_seg, location=loc, rotation=rotation)
    o = bpy.context.object
    o.name = name
    assign(o, material)
    smooth(o)
    move_to(o, coll)
    return o


def ring_mesh(name, rings, material, coll, cap=True):
    # rings: [(x, half_width, bottom_z, shoulder_z, top_z), ...]
    verts, faces = [], []
    # Eight points per station, clockwise viewed from front.
    for x, w, zb, zs, zt in rings:
        verts.extend([
            (x, -w * .70, zb), (x, -w, zb + .16), (x, -w, zs), (x, -w * .64, zt),
            (x, w * .64, zt), (x, w, zs), (x, w, zb + .16), (x, w * .70, zb)
        ])
    for i in range(len(rings) - 1):
        a = i * 8
        b = (i + 1) * 8
        for j in range(8):
            faces.append((a + j, a + (j + 1) % 8, b + (j + 1) % 8, b + j))
    if cap:
        faces.append(tuple(range(7, -1, -1)))
        last = (len(rings) - 1) * 8
        faces.append(tuple(last + j for j in range(8)))
    mesh = bpy.data.meshes.new(name + '.mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    o = bpy.data.objects.new(name, mesh)
    coll.objects.link(o)
    assign(o, material)
    bevel(o, .055, 3)
    smooth(o)
    return o


def panel(name, verts, material, coll, solid=.026, bevel_amt=.018):
    mesh = bpy.data.meshes.new(name + '.mesh')
    mesh.from_pydata(verts, [], [tuple(range(len(verts)))])
    mesh.update()
    o = bpy.data.objects.new(name, mesh)
    coll.objects.link(o)
    solidify = o.modifiers.new('Panel thickness', 'SOLIDIFY')
    solidify.thickness = solid
    bevel(o, bevel_amt, 3)
    assign(o, material)
    return o


def curve_tube(name, points, radius, material, coll, cyclic=False):
    cu = bpy.data.curves.new(name + '.curve', 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = radius
    cu.bevel_resolution = 2
    spline = cu.splines.new('BEZIER')
    spline.bezier_points.add(len(points) - 1)
    for bp, co in zip(spline.bezier_points, points):
        bp.co = co
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'
    spline.use_cyclic_u = cyclic
    o = bpy.data.objects.new(name, cu)
    coll.objects.link(o)
    assign(o, material)
    return o


def set_origin(obj, point):
    old = bpy.context.scene.cursor.location.copy()
    bpy.context.scene.cursor.location = point
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    obj.select_set(False)
    bpy.context.scene.cursor.location = old


def wheel(name, x, y, mats, coll):
    side = 'left' if y > 0 else 'right'
    base = f'wheel.{name}.{side}'
    tire = torus(base, (x, y, .48), .315, .105, mats['tire'], coll)
    tire['component_id'] = base
    rim = cylinder(base + '.rim', (x, y, .48), .245, .12, mats['metal'], coll, vertices=40)
    hub = cylinder(base + '.hub', (x, y + (.075 if y > 0 else -.075), .48), .075, .15, mats['dark_metal'], coll, vertices=32)
    # Ten clean spokes.
    for i in range(10):
        a = i * math.tau / 10
        yy = y + (.145 if y > 0 else -.145)
        spoke = cube(base + f'.spoke.{i:02d}', (x + math.cos(a) * .13, yy, .48 + math.sin(a) * .13), (.13, .018, .018), mats['metal'], coll, .012, rotation=(0, a, 0))
    return tire


def build():
    clear()
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'METERS'
    scene.unit_settings.scale_length = 1.0
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = 'RGBA'
    scene.view_settings.look = 'AgX - Medium High Contrast'

    mats = {
        'body': mat('MAT_BODY_NEUTRAL', (.20, .24, .29), .72, .2),
        'body_dark': mat('MAT_TRIM_NEUTRAL', (.035, .045, .060), .55, .26),
        'glass': mat('MAT_GLASS_NEUTRAL', (.025, .08, .12), .10, .06, .72),
        'tire': mat('MAT_TIRE', (.012, .014, .018), .05, .48),
        'metal': mat('MAT_METAL', (.34, .39, .44), .82, .18),
        'dark_metal': mat('MAT_DARK_METAL', (.075, .085, .095), .78, .22),
        'headlamp': mat('MAT_HEADLAMP', (.68, .86, 1.0), .25, .12, .08, (.32, .72, 1.0), 1.2),
        'taillamp': mat('MAT_TAILLAMP', (.5, .015, .02), .25, .16, .08, (1.0, .015, .01), 1.3),
        'interior': mat('MAT_INTERIOR', (.055, .065, .075), .05, .48),
        'interior2': mat('MAT_INTERIOR_ACCENT', (.13, .15, .17), .15, .32),
        'engine': mat('MAT_ENGINE', (.18, .20, .22), .82, .26),
        'cooling': mat('MAT_COOLING', (.14, .18, .20), .72, .25),
        'holo': mat('MAT_HOLOGRAM_CYAN', (.008, .16, .31), .42, .18, .12, (0.0, .28, .62), .48),
        'holo_glass': mat('MAT_HOLOGRAM_GLASS', (.003, .055, .13), .12, .12, .72, (0.0, .18, .48), .22),
        'holo_dark': mat('MAT_HOLOGRAM_DARK', (.006, .022, .045), .48, .25, .04, (0.0, .06, .18), .12),
    }

    C_BODY = collection('BODY')
    C_GLASS = collection('GLASS')
    C_LIGHTS = collection('LIGHTS')
    C_WHEELS = collection('WHEELS')
    C_INTERIOR = collection('INTERIOR')
    C_MECH = collection('MECHANICAL')
    C_DETAILS = collection('DETAILS')
    C_STAGE = collection('STAGE')

    # Main body: front is +X, driver-left is +Y, up is +Z.
    lower = ring_mesh('body.shell', [
        (-2.25, .58, .42, .72, .78), (-2.05, .84, .36, .86, .96),
        (-1.55, .91, .30, .91, 1.00), (-.90, .92, .28, .93, 1.02),
        (0.00, .93, .28, .94, 1.01), (.90, .92, .28, .92, .97),
        (1.55, .91, .30, .89, .92), (2.05, .82, .38, .78, .83),
        (2.32, .52, .48, .66, .70)
    ], mats['body'], C_BODY)
    lower['component_id'] = 'body.shell'

    # Greenhouse with a sedan roof arc and distinct trunk volume.
    # The greenhouse is assembled from independent glazing and pillars below;
    # no opaque cabin mass is used, preserving a readable interior.
    roof = cube('body.roof_panel', (-.08,0,1.47), (.86,.70,.055), mats['body'], C_BODY, .17)
    roof['component_id'] = 'body.roof_panel'

    hood = panel('body.hood', [(1.26,-.75,.94),(2.02,-.68,.82),(2.05,.68,.82),(1.26,.75,.94)], mats['body'], C_BODY, .035, .03)
    hood['component_id'] = 'body.hood'; set_origin(hood, (1.26,0,.94))
    trunk = panel('body.trunk_lid', [(-2.04,-.67,.92),(-1.30,-.72,.99),(-1.30,.72,.99),(-2.04,.67,.92)], mats['body'], C_BODY, .035, .03)
    trunk['component_id'] = 'body.trunk_lid'; set_origin(trunk, (-1.30,0,.99))
    front_bumper = cube('body.bumper.front', (2.22,0,.57), (.14,.80,.18), mats['body'], C_BODY, .095)
    front_bumper['component_id'] = 'body.bumper.front'
    rear_bumper = cube('body.bumper.rear', (-2.18,0,.57), (.13,.80,.17), mats['body'], C_BODY, .09)
    rear_bumper['component_id'] = 'body.bumper.rear'

    # Doors: left/right are always from the driver's perspective.
    door_specs = [
        ('front', .70, -.16, 1.17), ('rear', -.20, -.96, 1.10)
    ]
    for side, y, outward in [('left', .927, 1), ('right', -.927, -1)]:
        for pos, x_front, x_rear, ztop in door_specs:
            verts = [(x_rear,y,.46),(x_front,y,.45),(x_front-.03,y,ztop),(x_rear+.08,y,ztop+.07)]
            if side == 'right': verts.reverse()
            door = panel(f'body.door.{pos}.{side}', verts, mats['body'], C_BODY, .038*outward, .022)
            door['component_id'] = f'body.door.{pos}.{side}'
            set_origin(door, (x_front, y, .82))
            # Handle and lower character line.
            hx = x_front - .20
            cube(f'detail.handle.{pos}.{side}', (hx, y + .032*outward, 1.04), (.10,.018,.023), mats['metal'], C_DETAILS, .018)

    # Glass panels and windshield/rear glass.
    for side, y, outward in [('left', .785, 1), ('right', -.785, -1)]:
        fw = panel(f'glass.door.front.{side}', [(-.12,y,1.19),(.65,y,1.18),(.40,y,1.43),(-.08,y,1.46)], mats['glass'], C_GLASS, .018*outward, .014)
        rw = panel(f'glass.door.rear.{side}', [(-.92,y,1.13),(-.15,y,1.19),(-.10,y,1.46),(-.66,y,1.38)], mats['glass'], C_GLASS, .018*outward, .014)
        fw['component_id'] = f'glass.door.front.{side}'
        rw['component_id'] = f'glass.door.rear.{side}'
    wind = panel('glass.windshield.front', [(1.18,-.63,1.00),(.70,-.69,1.43),(.70,.69,1.43),(1.18,.63,1.00)], mats['glass'], C_GLASS, .025, .018)
    rearwin = panel('glass.windshield.rear', [(-1.28,.57,1.02),(-.78,.67,1.42),(-.78,-.67,1.42),(-1.28,-.57,1.02)], mats['glass'], C_GLASS, .025, .018)
    wind['component_id']='glass.windshield.front'; rearwin['component_id']='glass.windshield.rear'

    # Pillars and bright beltline make the silhouette readable.
    for side, y in [('left', .805), ('right', -.805)]:
        for suffix, pts in [
            ('a', [(1.18,y,1.0),(.70,y,1.40)]), ('b', [(-.10,y,1.16),(-.10,y,1.48)]),
            ('c', [(-1.27,y,1.0),(-.76,y,1.39)]), ('belt', [(-1.35,y,1.08),(1.22,y,1.08)])]:
            curve_tube(f'trim.pillar.{suffix}.{side}', pts, .025 if suffix!='belt' else .014, mats['metal'], C_DETAILS)

    # Mirrors, distinctly separate.
    for side, y in [('left', .99), ('right', -.99)]:
        mir = uv_sphere(f'body.mirror.{side}', (.72,y,1.16), (.17,.10,.07), mats['body'], C_BODY)
        mir['component_id'] = f'body.mirror.{side}'
        cube(f'body.mirror.{side}.stem', (.69,y*.92,1.13), (.05,.09,.025), mats['body_dark'], C_DETAILS, .02)

    # Front grille and lights.
    grille = cube('detail.grille.front', (2.325,0,.67), (.026,.50,.16), mats['body_dark'], C_DETAILS, .025)
    for y in (-.63,.63):
        side = 'right' if y < 0 else 'left'
        lamp = cube(f'light.headlamp.{side}', (2.08,y,.84), (.18,.20,.075), mats['headlamp'], C_LIGHTS, .055, rotation=(0, .08, 0))
        lamp['component_id'] = f'light.headlamp.{side}'
        tail = cube(f'light.tail.{side}', (-2.08,y,.86), (.15,.18,.08), mats['taillamp'], C_LIGHTS, .05, rotation=(0, -.08, 0))
        tail['component_id'] = f'light.tail.{side}'
    # Grille slats.
    for i in range(7):
        cube(f'detail.grille.slat.{i:02d}', (2.358,-.36+i*.12,.67), (.012,.015,.13), mats['metal'], C_DETAILS, .006)

    # Wheels: individual roots and useful child detail.
    for axle, x in [('front', 1.42), ('rear', -1.48)]:
        for y in (.91,-.91): wheel(axle, x, y, mats, C_WHEELS)

    # Wheel arches as glowing/metal contour tubes.
    for x in (1.42,-1.48):
        for side, y in [('left',.94),('right',-.94)]:
            pts=[]
            for i in range(9):
                a=math.pi*i/8
                pts.append((x-.46*math.cos(a),y,.47+.46*math.sin(a)))
            curve_tube(f'trim.wheel_arch.{"front" if x>0 else "rear"}.{side}',pts,.018,mats['metal'],C_DETAILS)

    # Interior, deliberately kept within cabin envelope.
    def seat(name, x, y, rear=False):
        cushion = cube(name+'.cushion',(x,y,.68),(.34,.28,.10),mats['interior'],C_INTERIOR,.08)
        back = cube(name+'.back',(x-.10,y,.93),(.12,.29,.32),mats['interior'],C_INTERIOR,.09,rotation=(0,-.12,0))
        head = cube(name+'.headrest',(x-.16,y,1.22),(.09,.18,.12),mats['interior2'],C_INTERIOR,.055)
        cushion['component_id']=name
        return cushion
    seat('interior.seat.front.left',.28,.40); seat('interior.seat.front.right',.28,-.40)
    rear = cube('interior.seat.rear',(-.73,0,.71),(.38,.67,.12),mats['interior'],C_INTERIOR,.10)
    rear['component_id']='interior.seat.rear'
    cube('interior.seat.rear.back',(-.93,0,.96),(.11,.68,.30),mats['interior'],C_INTERIOR,.09,rotation=(0,-.12,0))
    dash = cube('interior.dashboard',(.79,0,1.00),(.19,.69,.13),mats['interior2'],C_INTERIOR,.08)
    dash['component_id']='interior.dashboard'
    # Steering wheel on driver's left (+Y), axis approximately X.
    steer = torus('interior.steering_wheel',(.58,.43,1.04),.145,.025,mats['dark_metal'],C_INTERIOR,rotation=(0,math.pi/2,0),major_seg=32)
    steer['component_id']='interior.steering_wheel'
    cylinder('interior.steering_column',(.67,.43,1.02),.025,.25,mats['dark_metal'],C_INTERIOR,rotation=(0,math.pi/2,0),vertices=20)
    cube('interior.center_console',(.05,0,.74),(.42,.12,.10),mats['interior2'],C_INTERIOR,.05)

    # Simplified but coherent front-bay components.
    engine = cube('engine.assembly',(1.48,0,.64),(.36,.42,.19),mats['engine'],C_MECH,.09)
    engine['component_id']='engine.assembly'
    cube('engine.assembly.cover',(1.42,0,.84),(.29,.34,.05),mats['dark_metal'],C_MECH,.04)
    for i in range(4):
        cylinder(f'engine.assembly.intake.{i+1}',(1.55,-.27+i*.18,.79),.032,.36,mats['metal'],C_MECH,rotation=(0,math.pi/2,0),vertices=20,bevel_amt=.01)
    radiator = cube('cooling.radiator',(2.00,0,.72),(.055,.55,.30),mats['cooling'],C_MECH,.025)
    radiator['component_id']='cooling.radiator'
    # Radiator fins.
    for i in range(9):
        cube(f'cooling.radiator.fin.{i:02d}',(2.062,-.45+i*.112,.72),(.008,.012,.26),mats['metal'],C_MECH,.003)
    fan = torus('cooling.fan',(1.91,0,.73),.18,.025,mats['dark_metal'],C_MECH,rotation=(0,math.pi/2,0),major_seg=28)
    fan['component_id']='cooling.fan'
    for i in range(6):
        a=i*math.tau/6
        cube(f'cooling.fan.blade.{i:02d}',(1.89,math.cos(a)*.09,.73+math.sin(a)*.09),(.018,.12,.025),mats['dark_metal'],C_MECH,.012,rotation=(a,0,0))
    pump = cylinder('cooling.water_pump',(1.68,.40,.73),.11,.16,mats['metal'],C_MECH,rotation=(0,math.pi/2,0),vertices=28)
    pump['component_id']='cooling.water_pump'

    # Underbody and exhaust cues.
    cube('body.floorpan',(0,0,.38),(1.55,.70,.055),mats['body_dark'],C_BODY,.04)
    curve_tube('mechanical.exhaust',[(-1.90,-.35,.31),(-.8,-.32,.30),(.4,-.28,.31),(1.2,-.25,.40)],.035,mats['dark_metal'],C_MECH)

    # Fine panel-gap and silhouette lines, especially valuable in holographic mode.
    for side,y in [('left',.958),('right',-.958)]:
        for x in (-.18,.72,-.98):
            curve_tube(f'detail.panel_gap.{x}.{side}',[(x,y,.47),(x,y,1.17)],.008,mats['body_dark'],C_DETAILS)
        curve_tube(f'detail.rocker.{side}',[(-1.10,y,.42),(1.02,y,.42)],.018,mats['body_dark'],C_DETAILS)

    # Ground stage; excluded from GLB later.
    ground = cube('stage.ground',(0,0,-.04),(6,6,.05),mat('MAT_GROUND',(.005,.012,.025),.1,.24),C_STAGE,.02)
    for i in range(-10,11):
        curve_tube(f'stage.grid.x.{i}',[(-6,i*.5,.015),(6,i*.5,.015)],.004,mat('MAT_GRID',(0,.15,.28),.2,.3,0,(0,.16,.35),.9),C_STAGE)
        curve_tube(f'stage.grid.y.{i}',[(i*.5,-6,.016),(i*.5,6,.016)],.004,bpy.data.materials['MAT_GRID'],C_STAGE)

    # Custom metadata on roots and all component objects.
    scene['asset_name']='eGarage Generic Mid-size Sedan v01'
    scene['axis_convention']='X forward, Y driver-left, Z up'
    scene['units']='meters'
    scene['license']='Original procedural model for eGarage; no manufacturer marks'
    for obj in bpy.context.scene.objects:
        if 'component_id' in obj:
            obj['side_convention']='left/right from driver perspective'

    return mats, C_STAGE


def camera_track(name, loc, target=(0,0,.75), lens=54):
    bpy.ops.object.camera_add(location=loc)
    cam=bpy.context.object; cam.name=name; cam.data.lens=lens
    direction=Vector(target)-cam.location
    cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
    bpy.context.scene.camera=cam
    return cam


def add_area(name, loc, energy, size, color, target=(0,0,.7)):
    bpy.ops.object.light_add(type='AREA', location=loc)
    l=bpy.context.object; l.name=name; l.data.energy=energy; l.data.shape='DISK'; l.data.size=size; l.data.color=color
    l.rotation_euler=(Vector(target)-l.location).to_track_quat('-Z','Y').to_euler()
    return l


def setup_lights(holo=False):
    for o in list(bpy.context.scene.objects):
        if o.type in {'LIGHT','CAMERA'}: bpy.data.objects.remove(o,do_unlink=True)
    world=bpy.context.scene.world or bpy.data.worlds.new('World')
    bpy.context.scene.world=world; world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=((.002,.008,.018,1) if holo else (.035,.045,.06,1))
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.18 if holo else .32
    if holo:
        add_area('Key cyan',(4,3,5),1150,4,(.02,.55,1.0))
        add_area('Rim cyan',(-3,-4,3),1000,3,(.0,.25,1.0))
        add_area('Top blue',(0,0,6),800,4,(.05,.45,1.0))
    else:
        add_area('Key',(4,3,5),1250,4,(1.0,.92,.82))
        add_area('Fill',(1,-4,2.8),900,3,(.50,.68,1.0))
        add_area('Rim',(-4,2,3.5),1100,3,(.30,.60,1.0))


def switch_holo(mats, enabled):
    for obj in bpy.context.scene.objects:
        if obj.type not in {'MESH','CURVE'} or obj.name.startswith('stage.') or not hasattr(obj.data,'materials') or not obj.data.materials: continue
        if enabled:
            obj['_original_material']=obj.data.materials[0].name
            n=obj.name
            if n.startswith('glass.'): obj.data.materials[0]=mats['holo_glass']
            elif n.startswith(('interior.','engine.','cooling.','mechanical.','wheel.')) or 'TIRE' in obj.data.materials[0].name: obj.data.materials[0]=mats['holo_dark']
            else: obj.data.materials[0]=mats['holo']
        elif '_original_material' in obj:
            original=bpy.data.materials.get(obj['_original_material'])
            if original: obj.data.materials[0]=original
            del obj['_original_material']


VIEWS={
    'front':((6.7,0,1.55),(0.35,0,.76)),
    'rear':((-6.7,0,1.55),(-.35,0,.76)),
    'left':((0,6.8,1.65),(0,0,.75)),
    'right':((0,-6.8,1.65),(0,0,.75)),
    'front_three_quarter':((5.4,4.6,3.0),(.15,0,.72)),
    'rear_three_quarter':((-5.4,-4.6,2.8),(-.15,0,.72)),
}


def render_set(mats, mode):
    holo=mode=='holographic'
    switch_holo(mats,holo)
    setup_lights(holo)
    scene=bpy.context.scene
    views = VIEWS
    if os.environ.get('SEDAN_PREVIEW') == '1':
        views = {'front_three_quarter': VIEWS['front_three_quarter']}
        scene.render.resolution_x = 720
        scene.render.resolution_y = 405
    for view,(loc,target) in views.items():
        cam=camera_track('Camera_'+view,loc,target,58 if 'quarter' in view else 62)
        scene.render.filepath=os.path.join(OUT,'renders',mode,f'{mode}_{view}.png')
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam,do_unlink=True)
    if holo: switch_holo(mats,False)


def save_and_export(stage):
    # Freeze procedural modifiers and remove zero-area faces before delivery.
    for obj in list(bpy.context.scene.objects):
        if obj.type != 'MESH' or obj.name.startswith('stage.'):
            continue
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        for modifier in list(obj.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=modifier.name)
            except RuntimeError:
                pass
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=list(bm.edges))
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(obj.data)
        bm.free()
        obj.data.validate(clean_customdata=False)
        obj.data.update()
        obj.select_set(False)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'sedan_v01.blend'))
    # Export only model collections, excluding stage/lights/cameras.
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type in {'MESH','CURVE'} and not obj.name.startswith('stage.'):
            obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'sedan_v01.glb'), export_format='GLB', use_selection=True, export_apply=True, export_extras=True)


if __name__ == '__main__':
    os.makedirs(os.path.join(OUT,'renders','neutral'),exist_ok=True)
    os.makedirs(os.path.join(OUT,'renders','holographic'),exist_ok=True)
    mats,stage=build()
    if os.environ.get('SEDAN_SKIP_RENDERS') != '1':
        render_set(mats,'neutral')
        render_set(mats,'holographic')
    setup_lights(False)
    save_and_export(stage)
    print('SEDAN_BUILD_COMPLETE')
