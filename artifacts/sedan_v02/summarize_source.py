import bpy, json, os
R=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(R,'source','graphite-four-door-sedan_cc0.glb'))
keys=('door','hood','trunk','bumper','glass','mirror','headlamp','lamp','wheel','tyre','windshield','roof','paint','lid','panel')
matches=[]
for o in bpy.context.scene.objects:
    if o.type=='MESH' and any(k in o.name.lower() for k in keys):
        matches.append({'name':o.name,'parent':o.parent.name if o.parent else None,'materials':[m.name for m in o.data.materials if m]})
with open(os.path.join(R,'source_summary.json'),'w') as f: json.dump(matches,f,indent=2)
