import bpy
import json
import math
import os
import sys
import traceback
from collections import defaultdict
from mathutils import Vector

ROOT = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(ROOT, "source", "Meshy_AI_Neon_Blueprint_Sedan_original_copy.glb")
RENDERS = os.path.join(ROOT, "renders")
BLEND = os.path.join(ROOT, "meshy_sedan_holographic_v02.blend")
GLB = os.path.join(ROOT, "meshy_sedan_holographic_v02.glb")
REPORT = os.path.join(ROOT, "material_assignment_report.json")


def mat(name, color, metallic=0.0, roughness=0.35, alpha=1.0, emission=None, emission_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.diffuse_color = (*color, alpha)
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*color, alpha)
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = roughness
    if "Alpha" in p.inputs:
        p.inputs["Alpha"].default_value = alpha
    if "Transmission Weight" in p.inputs:
        p.inputs["Transmission Weight"].default_value = max(0.0, min(0.45, (1.0 - alpha) * 0.7))
    if emission:
        if "Emission Color" in p.inputs:
            p.inputs["Emission Color"].default_value = (*emission, 1)
            p.inputs["Emission Strength"].default_value = emission_strength
        elif "Emission" in p.inputs:
            p.inputs["Emission"].default_value = (*emission, 1)
            p.inputs["Emission Strength"].default_value = emission_strength
    if alpha < 1:
        try:
            m.surface_render_method = "DITHERED"
        except Exception:
            try: m.blend_method = "BLEND"
            except Exception: pass
        m.diffuse_color = (*color, alpha)
    return m


def components(mesh):
    adjacency = [[] for _ in mesh.vertices]
    for edge in mesh.edges:
        a, b = edge.vertices
        adjacency[a].append(b); adjacency[b].append(a)
    remaining = set(range(len(mesh.vertices)))
    out = []
    vertex_component = {}
    while remaining:
        start = remaining.pop(); stack = [start]; members = [start]
        while stack:
            cur = stack.pop()
            for nxt in adjacency[cur]:
                if nxt in remaining:
                    remaining.remove(nxt); stack.append(nxt); members.append(nxt)
        cid = len(out)
        for vertex in members: vertex_component[vertex] = cid
        pts = [mesh.vertices[i].co for i in members]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        out.append({"id": cid, "vertices": len(members), "lo": lo, "hi": hi, "center": (lo + hi) / 2, "size": hi - lo})
    return sorted(out, key=lambda c: c["vertices"], reverse=True), vertex_component


def assign_materials(obj, materials):
    mesh = obj.data
    mesh.materials.clear()
    order = ["body", "glass", "tire", "rim", "housing", "cyan"]
    for key in order: mesh.materials.append(materials[key])
    slot = {name: i for i, name in enumerate(order)}
    comps, vertex_component = components(mesh)
    body_id = comps[0]["id"]
    wheel_ids = {c["id"]: c for c in comps if 0.24 < c["size"].x < 0.33 and 0.24 < c["size"].z < 0.33}
    small_ids = {c["id"] for c in comps if c["vertices"] < 1000}
    counts = defaultdict(int)

    for poly in mesh.polygons:
        center = poly.center
        normal = poly.normal
        cid = vertex_component[poly.vertices[0]]
        target = "body"
        if cid in wheel_ids:
            wc = wheel_ids[cid]["center"]
            radius = math.hypot(center.x - wc.x, center.z - wc.z)
            target = "tire" if radius > 0.112 else "rim"
        elif cid in small_ids:
            target = "rim"
        elif cid == body_id:
            side_glass = (-0.42 < center.x < 0.70 and center.z > 0.045 and abs(center.y) > 0.285 and abs(normal.y) > 0.42)
            front_glass = (-0.43 < center.x < -0.08 and center.z > 0.075 and normal.x < -0.22)
            rear_glass = (0.43 < center.x < 0.76 and center.z > 0.075 and normal.x > 0.22)
            headlamp = (center.x < -0.84 and -0.025 < center.z < 0.065 and 0.18 < abs(center.y) < 0.36 and normal.x < -0.30)
            if side_glass or front_glass or rear_glass: target = "glass"
            # Retire the irregular source headlamp faces into a dark recess.
            # Independent symmetric optical assemblies are placed over them.
            elif headlamp: target = "housing"
        poly.material_index = slot[target]
        counts[target] += 1

    return counts, comps


def curve(name, points, material, radius=0.0015, cyclic=False):
    cu = bpy.data.curves.new(name + ".curve", "CURVE")
    cu.dimensions = "3D"; cu.resolution_u = 2; cu.bevel_depth = radius; cu.bevel_resolution = 2
    sp = cu.splines.new("POLY"); sp.points.add(len(points) - 1)
    for point, co in zip(sp.points, points): point.co = (*co, 1)
    sp.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, cu); bpy.context.scene.collection.objects.link(obj); cu.materials.append(material)
    obj["diagnostic_role"] = "selected holographic contour; not source topology"
    return obj


def panel(name, vertices, material, export=True):
    mesh=bpy.data.meshes.new(name+".mesh");mesh.from_pydata(vertices,[],[tuple(range(len(vertices)))]);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(obj);mesh.materials.append(material)
    if export:obj["export_glb"]=True
    return obj


def front_surface_x(y):
    # Approximation of the approved source nose across its width. This keeps
    # the replacement lamps close to the generated body without changing it.
    return -.95 + (abs(y)-.10)*.42


def add_headlamp_assemblies(housing_mat,lens_mat,optical_mat,signature_mat):
    assemblies=[]
    for side in (-1,1):
        # Low, swept six-point outline. Inner edge starts outside the grille;
        # outer edge follows the fender rather than forming a tall flat plate.
        yz=[(side*.155,.030),(side*.205,.047),(side*.342,.034),(side*.355,-.006),(side*.275,-.022),(side*.165,-.010)]
        housing=[(front_surface_x(y),y,z) for y,z in yz]
        assemblies.append(panel(f"headlamp.{side}.housing",housing,housing_mat))
        center=sum((Vector(v) for v in housing),Vector())/len(housing)
        lens=[]
        for vertex in housing:
            v=center+(Vector(vertex)-center)*.91;v.x-=.004;lens.append(tuple(v))
        assemblies.append(panel(f"headlamp.{side}.lens",lens,lens_mat))

        # Two dark optical projectors remain recognizable even with emission off.
        for index,(y,z,scale) in enumerate([(side*.220,.010,.014),(side*.300,.006,.009)]):
            x=front_surface_x(y)-.008
            bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=(x,y,z))
            optic=bpy.context.object;optic.name=f"headlamp.{side}.projector.{index}";optic.scale=(.22*scale,scale,scale);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);optic.data.materials.append(optical_mat);optic["export_glb"]=True;assemblies.append(optic)

        # Fine angular DRL following the upper edge and outer return.
        pts=[]
        for y,z in [(side*.165,.031),(side*.210,.043),(side*.330,.030),(side*.345,-.002)]:
            pts.append((front_surface_x(y)-.014,y,z))
        drl=curve(f"headlamp.{side}.signature",pts,signature_mat,.00115);drl["export_glb"]=True;assemblies.append(drl)
    return assemblies


def add_contours(cyan):
    # Curves deliberately describe only design boundaries; they do not follow
    # the triangulation. Both sides are included for reusable camera angles.
    # Delivery cameras show the -Y side. Omitting far-side curves prevents
    # transparent overlap from turning the vehicle into a wire cage.
    for side in (-1,):
        y = side * 0.397
        # Belt line and lower sill.
        curve(f"contour.belt.{side}", [(-0.67,y,0.015),(-0.20,y,0.005),(0.28,y,0.012),(0.72,y,-0.005)], cyan)
        curve(f"contour.sill.{side}", [(-0.48,y,-0.225),(0.10,y,-0.235),(0.62,y,-0.222)], cyan, .0013)
        # Door joints, drawn as selected open polylines.
        curve(f"contour.door.front.{side}", [(-0.38,y,0.005),(-0.35,y,-0.19),(0.18,y,-0.22),(0.22,y,0.01)], cyan, .0013)
        curve(f"contour.door.rear.{side}", [(0.22,y,0.01),(0.18,y,-0.22),(0.58,y,-0.19),(0.67,y,0.00)], cyan, .0013)
        # Window perimeter. This is auxiliary because the generated surface has
        # no clean glass boundary loops.
        curve(f"contour.windows.{side}", [(-0.39,y,0.06),(-0.18,y,0.255),(0.24,y,0.285),(0.58,y,0.19),(0.67,y,0.06),(-0.39,y,0.06)], cyan, .0015)
        curve(f"contour.bpillar.{side}", [(0.14,y,0.06),(0.14,y,0.278)], cyan, .0012)


def set_body_alpha(material, alpha):
    material.diffuse_color[3] = alpha
    p = material.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value[3] = alpha
    if "Alpha" in p.inputs: p.inputs["Alpha"].default_value = alpha
    if "Transmission Weight" in p.inputs: p.inputs["Transmission Weight"].default_value = max(0, min(.45, (1-alpha)*.7))


def aim(obj, target): obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def setup_stage():
    floor_mat = mat("Holo_Studio_Floor", (.008,.012,.020), roughness=.3)
    bpy.ops.mesh.primitive_plane_add(size=7, location=(0,0,-.315)); floor=bpy.context.object; floor.name="stage.floor"; floor.data.materials.append(floor_mat)
    world=bpy.data.worlds.new("Holographic Studio");bpy.context.scene.world=world;world.use_nodes=True
    world.node_tree.nodes["Background"].inputs["Color"].default_value=(.0015,.003,.008,1);world.node_tree.nodes["Background"].inputs["Strength"].default_value=.12
    for name,loc,energy,size,color in [
        ("Key",(-2.0,-1.8,2.1),220,1.7,(.18,.48,1)),
        ("Fill",(-.2,2.0,1.1),115,1.4,(.05,.75,1)),
        ("Rim",(1.8,-1.0,1.5),260,1.2,(.05,1,1)),
        ("Top",(0,0,2.4),160,1.4,(.2,.5,1))]:
        bpy.ops.object.light_add(type="AREA",location=loc);l=bpy.context.object;l.name=name;l.data.energy=energy;l.data.shape="DISK";l.data.size=size;l.data.color=color;aim(l,Vector((0,0,0)))


def camera(name, location, target=(0,0,-.02), lens=58):
    bpy.ops.object.camera_add(location=location);c=bpy.context.object;c.name=name;c.data.lens=lens;aim(c,Vector(target));return c


def render(path, cam):
    scene=bpy.context.scene;scene.camera=cam;scene.render.filepath=path;bpy.ops.render.render(write_still=True)


def show_headlamp_side(objects, side, visible):
    token=f"headlamp.{side}."
    for obj in objects:
        if token in obj.name:obj.hide_render=not visible


try:
    os.makedirs(RENDERS,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=SOURCE)
    obj=next(o for o in bpy.context.scene.objects if o.type=="MESH")
    obj.name="Meshy_Sedan_Approved_Geometry"
    obj["export_glb"]=True
    obj["source_sha256"]="199e21d082ada04580dfd1e267573f335a71aef553482f6ccde38d2f8b68fc16"
    obj["geometry_policy"]="Original vertices and proportions preserved; material assignment only"

    body=mat("Holo_Body_Soft",(.008,.055,.14),.38,.24,.78)
    glass=mat("Holo_Glass",(.008,.18,.28),.12,.12,.34)
    tire=mat("Holo_Tire",(.004,.008,.015),.05,.48,.94)
    rim=mat("Holo_Rim",(.035,.065,.09),.82,.19,.94)
    housing=mat("Lamp_Housing_Dark",(.003,.009,.015),.48,.22,.98)
    lens=mat("Lamp_Lens_Blue",(.025,.20,.29),.12,.10,.48)
    optical=mat("Lamp_Optical_Elements",(.08,.13,.17),.78,.16,.98)
    signature=mat("Lamp_Signature_Cyan",(.18,.62,.75),.15,.20,.97,(.35,.82,1),.70)
    cyan=mat("Holo_Cyan_Contour",(.008,.25,.38),.2,.25,.96,(.01,.52,.72),.85)
    counts, comps=assign_materials(obj,{"body":body,"glass":glass,"tire":tire,"rim":rim,"housing":housing,"cyan":cyan})
    optics=add_headlamp_assemblies(housing,lens,optical,signature)
    add_contours(cyan);setup_stage()
    design_contours=[o for o in bpy.context.scene.objects if o.name.startswith("contour.")]

    scene=bpy.context.scene;scene.render.engine="BLENDER_EEVEE";scene.render.resolution_x=900;scene.render.resolution_y=585;scene.render.resolution_percentage=100;scene.render.image_settings.file_format="PNG";scene.view_settings.look="AgX - Medium High Contrast"
    cam3q=camera("Camera_ThreeQuarter",(-2.45,-2.05,.88),(0,0,-.035),60)
    cam_side=camera("Camera_Lateral",(0,-3.15,.38),(0,0,-.04),62)
    cam_front=camera("Camera_Front",(-3.0,0,.20),(-.12,0,-.04),64)
    cam_close=camera("Camera_Headlamp_Closeup",(-1.58,-1.05,.30),(-.78,-.12,.01),72)

    render_only=os.environ.get("RENDER_ONLY","all")
    set_body_alpha(body,.92)
    show_headlamp_side(optics,1,False)
    if render_only in {"all","three_quarter"}:render(os.path.join(RENDERS,"three_quarter_soft_transparency.png"),cam3q)
    if render_only in {"all","lateral"}:render(os.path.join(RENDERS,"lateral_soft_transparency.png"),cam_side)
    show_headlamp_side(optics,1,True)
    for contour in design_contours:contour.hide_render=True
    if render_only in {"all","front"}:render(os.path.join(RENDERS,"front_soft_transparency.png"),cam_front)
    show_headlamp_side(optics,1,False)
    if render_only in {"all","closeup"}:render(os.path.join(RENDERS,"headlamp_closeup_no_bloom.png"),cam_close)
    show_headlamp_side(optics,1,True)
    for contour in design_contours:contour.hide_render=False

    report={"source_sha256":obj["source_sha256"],"geometry_edited":False,"optical_correction":"Original irregular headlamp faces reassigned as dark recess; symmetric independent housings, lenses, two projectors and fine DRL added.","face_material_counts":dict(counts),"body_alpha":{"soft":.92},"glass_alpha":.34,"component_count":len(comps),"tail_lamp_review":"Rear lamps are not emissive blobs in the approved treatment and were left unchanged.","limitations":["The replacement follows a fitted analytic nose surface because the source has no clean lamp boundary loops.","No bloom compositor is used; the signature remains legible from material and geometry alone.","The source body topology and proportions are unchanged."]}
    with open(REPORT,"w",encoding="utf-8") as f:json.dump(report,f,indent=2)

    scene["holographic_notes"]="v02 localized independent headlamp assemblies. No body, interior or mechanical reconstruction."
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    # The editable .blend retains studio, cameras and contour curves. Strip
    # them only from the in-memory export scene so the GLB contains the car.
    for other in list(bpy.data.objects):
        if not other.get("export_glb"): bpy.data.objects.remove(other,do_unlink=True)
    bpy.context.view_layer.update()
    bpy.ops.export_scene.gltf(filepath=GLB,export_format="GLB",use_active_scene=True,export_apply=False,export_extras=True)
    print("HOLOGRAPHIC_BUILD_COMPLETE",json.dumps(report["face_material_counts"]),flush=True)
    sys.stdout.flush();sys.stderr.flush();os._exit(0)
except Exception:
    traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
