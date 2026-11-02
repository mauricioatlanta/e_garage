import bpy, os, json
from mathutils import Vector

R=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(R,'source','graphite-four-door-sedan_cc0.glb'))
info=[]
for o in bpy.context.scene.objects:
    if o.type=='MESH':
        o.data.calc_loop_triangles()
        info.append({'name':o.name,'vertices':len(o.data.vertices),'triangles':len(o.data.loop_triangles),'materials':[m.name for m in o.data.materials if m],'bounds':[list(v) for v in o.bound_box]})
print(json.dumps(info,indent=2))
# Quick neutral source render.
world=bpy.data.worlds.new('World'); bpy.context.scene.world=world; world.use_nodes=True; world.node_tree.nodes['Background'].inputs['Color'].default_value=(.06,.06,.07,1); world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
for loc,en,size in [((6,-5,6),1300,4),((-3,4,4),900,3),((0,0,7),800,3)]:
    bpy.ops.object.light_add(type='AREA',location=loc); l=bpy.context.object; l.data.energy=en; l.data.shape='DISK'; l.data.size=size; l.rotation_euler=(Vector((0,0,.7))-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(6,-5,2.8)); cam=bpy.context.object; cam.data.lens=58; cam.rotation_euler=(Vector((0,0,.7))-cam.location).to_track_quat('-Z','Y').to_euler(); bpy.context.scene.camera=cam
s=bpy.context.scene; s.render.engine='BLENDER_EEVEE'; s.render.resolution_x=900;s.render.resolution_y=560;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=os.path.join(R,'source_preview.png');s.view_settings.look='AgX - Medium High Contrast';bpy.ops.render.render(write_still=True)
