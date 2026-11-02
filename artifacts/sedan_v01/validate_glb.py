import bpy
import json
import os
from mathutils import Vector

ROOT = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(ROOT, 'sedan_v01.glb')

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)

mesh_objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
triangles = 0
vertices = 0
negative_scale = []
zero_area = 0
zero_area_by_object = {}
for obj in mesh_objects:
    mesh = obj.data
    mesh.calc_loop_triangles()
    triangles += len(mesh.loop_triangles)
    vertices += len(mesh.vertices)
    if obj.scale.x < 0 or obj.scale.y < 0 or obj.scale.z < 0:
        negative_scale.append(obj.name)
    obj_zero = sum(1 for p in mesh.polygons if p.area < 1e-10)
    zero_area += obj_zero
    if obj_zero:
        zero_area_by_object[obj.name] = obj_zero

all_ids = sorted({o.get('component_id') for o in bpy.context.scene.objects if o.get('component_id')})
required = {
    'body.door.front.left','body.door.front.right','body.door.rear.left','body.door.rear.right',
    'body.hood','body.trunk_lid','body.bumper.front','body.bumper.rear',
    'body.mirror.left','body.mirror.right','light.headlamp.left','light.headlamp.right',
    'light.tail.left','light.tail.right','wheel.front.left','wheel.front.right',
    'wheel.rear.left','wheel.rear.right','interior.seat.front.left',
    'interior.seat.front.right','interior.seat.rear','interior.dashboard',
    'interior.steering_wheel','engine.assembly','cooling.radiator','cooling.fan',
    'cooling.water_pump','glass.windshield.front','glass.windshield.rear',
    'glass.door.front.left','glass.door.front.right','glass.door.rear.left','glass.door.rear.right'
}
material_names = sorted({m.name for o in mesh_objects for m in o.data.materials if m})

mins = Vector((1e9,1e9,1e9)); maxs = Vector((-1e9,-1e9,-1e9))
for obj in mesh_objects:
    for c in obj.bound_box:
        w = obj.matrix_world @ Vector(c)
        mins.x=min(mins.x,w.x); mins.y=min(mins.y,w.y); mins.z=min(mins.z,w.z)
        maxs.x=max(maxs.x,w.x); maxs.y=max(maxs.y,w.y); maxs.z=max(maxs.z,w.z)

report = {
    'glb_bytes': os.path.getsize(GLB),
    'objects_total': len(bpy.context.scene.objects),
    'mesh_objects': len(mesh_objects),
    'vertices': vertices,
    'triangles': triangles,
    'materials': len(material_names),
    'material_names': material_names,
    'component_ids': all_ids,
    'required_component_ids': len(required),
    'missing_required': sorted(required-set(all_ids)),
    'negative_scale_objects': negative_scale,
    'zero_area_polygons': zero_area,
    'zero_area_by_object': zero_area_by_object,
    'bounds_meters': {
        'min': [round(v,4) for v in mins], 'max': [round(v,4) for v in maxs],
        'dimensions': [round(maxs[i]-mins[i],4) for i in range(3)]
    },
    'axis_convention': 'X forward, Y driver-left, Z up',
    'reimport_status': 'PASS' if not required-set(all_ids) and not negative_scale and zero_area == 0 else 'CHECK'
}

with open(os.path.join(ROOT,'validation_report.json'),'w',encoding='utf-8') as f:
    json.dump(report,f,indent=2,ensure_ascii=False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'sedan_v01_reimport_check.blend'))
print(json.dumps(report,indent=2,ensure_ascii=False))
