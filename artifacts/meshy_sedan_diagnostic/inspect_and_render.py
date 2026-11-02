import bpy
import json
import math
import os
import sys
import traceback
from collections import Counter, deque
from mathutils import Vector

ROOT = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(ROOT, "working_copy.glb")
REPORT = os.path.join(ROOT, "structure_report.json")
RENDER_DIR = os.path.join(ROOT, "renders")


def world_bounds(objects):
    pts = [o.matrix_world @ Vector(corner) for o in objects for corner in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def connected_components(obj):
    mesh = obj.data
    adjacency = [[] for _ in mesh.vertices]
    for edge in mesh.edges:
        a, b = edge.vertices
        adjacency[a].append(b)
        adjacency[b].append(a)
    remaining = set(range(len(mesh.vertices)))
    components = []
    while remaining:
        start = remaining.pop()
        q = [start]
        members = [start]
        while q:
            current = q.pop()
            for nxt in adjacency[current]:
                if nxt in remaining:
                    remaining.remove(nxt)
                    q.append(nxt)
                    members.append(nxt)
        points = [obj.matrix_world @ mesh.vertices[index].co for index in members]
        lo = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
        hi = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
        components.append({
            "vertices": len(members),
            "bounds_min": [round(v, 6) for v in lo],
            "bounds_max": [round(v, 6) for v in hi],
            "dimensions": [round(v, 6) for v in hi - lo],
            "center": [round(v, 6) for v in (lo + hi) * 0.5],
        })
    return sorted(components, key=lambda item: item["vertices"], reverse=True)


def inventory(mesh_objects):
    objects = []
    material_names = Counter()
    totals = Counter()
    for obj in mesh_objects:
        components = connected_components(obj)
        mats = [slot.material.name if slot.material else None for slot in obj.material_slots]
        material_names.update(m for m in mats if m)
        totals.update(vertices=len(obj.data.vertices), edges=len(obj.data.edges), polygons=len(obj.data.polygons), islands=len(components))
        objects.append({
            "name": obj.name,
            "vertices": len(obj.data.vertices),
            "edges": len(obj.data.edges),
            "polygons": len(obj.data.polygons),
            "materials": mats,
            "connected_components": len(components),
            "components": components,
            "dimensions": [round(v, 6) for v in obj.dimensions],
            "location": [round(v, 6) for v in obj.location],
        })
    lo, hi = world_bounds(mesh_objects)
    return {
        "source": os.path.basename(SOURCE),
        "object_count": len(bpy.context.scene.objects),
        "mesh_object_count": len(mesh_objects),
        "totals": dict(totals),
        "materials": dict(material_names),
        "objects": objects,
        "bounds_min": [round(v, 6) for v in lo],
        "bounds_max": [round(v, 6) for v in hi],
        "dimensions": [round(v, 6) for v in hi - lo],
    }, lo, hi


def material(name, color, metallic=0.0, roughness=0.35):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def aim(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def setup_studio(mesh_objects, lo, hi):
    grey = material("diagnostic_grey", (0.22, 0.24, 0.27), 0.22, 0.34)
    for obj in mesh_objects:
        obj.data.materials.clear()
        obj.data.materials.append(grey)

    center = (lo + hi) * 0.5
    size = hi - lo
    floor_z = lo.z - size.z * 0.015
    bpy.ops.mesh.primitive_plane_add(size=max(size.x, size.y) * 4.0, location=(center.x, center.y, floor_z))
    floor = bpy.context.object
    floor.name = "diagnostic_floor"
    floor.data.materials.append(material("studio_floor", (0.12, 0.13, 0.15), 0.0, 0.42))

    world = bpy.data.worlds.new("Diagnostic World")
    bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.025, 0.03, 0.04, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.38

    span = max(size.x, size.y, size.z)
    light_specs = [
        ("Key", center + Vector((span, -span, span * 1.4)), 350, span * 0.9),
        ("Fill", center + Vector((span * 0.2, span, span * 0.8)), 180, span * 0.8),
        ("Rim", center + Vector((-span, span * 0.4, span)), 280, span * 0.7),
        ("Top", center + Vector((0, 0, span * 1.7)), 220, span * 0.8),
    ]
    for name, loc, energy, area_size in light_specs:
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = energy
        lamp.data.shape = "DISK"
        lamp.data.size = area_size
        aim(lamp, center)
    return center, size


def render_views(center, size):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 600
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.look = "AgX - Medium High Contrast"
    os.makedirs(RENDER_DIR, exist_ok=True)

    # Largest horizontal dimension is treated as vehicle length.
    length_axis = "X" if size.x >= size.y else "Y"
    length = max(size.x, size.y)
    width = min(size.x, size.y)
    height = size.z
    distance = max(length * 1.45, width * 3.0)
    z = center.z + height * 0.24
    if length_axis == "X":
        views = {
            "front": center + Vector((-distance, 0, height * 0.24)),
            "lateral": center + Vector((0, -distance, height * 0.24)),
            "tres_cuartos": center + Vector((-distance * 0.78, -distance * 0.66, height * 0.42)),
        }
    else:
        views = {
            "front": center + Vector((0, -distance, height * 0.24)),
            "lateral": center + Vector((-distance, 0, height * 0.24)),
            "tres_cuartos": center + Vector((-distance * 0.66, -distance * 0.78, height * 0.42)),
        }
    output = {}
    for name, loc in views.items():
        bpy.ops.object.camera_add(location=loc)
        camera = bpy.context.object
        camera.name = "camera_" + name
        camera.data.lens = 58
        aim(camera, center + Vector((0, 0, height * 0.02)))
        scene.camera = camera
        path = os.path.join(RENDER_DIR, name + ".png")
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        output[name] = path
        bpy.data.objects.remove(camera, do_unlink=True)
    return output


try:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=SOURCE)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        raise RuntimeError("The GLB contains no mesh objects")
    report, lower, upper = inventory(meshes)
    center, size = setup_studio(meshes, lower, upper)
    report["renders"] = render_views(center, size)
    with open(REPORT, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    print("DIAGNOSTIC_COMPLETE", json.dumps(report["totals"]), flush=True)
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)
except Exception:
    traceback.print_exc()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(1)
