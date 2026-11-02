import bpy
import math
import os

RUTA_MODELO = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_diagnostic/working_copy.glb"
RUTA_SALIDA_BLEND = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_holographic_v06_final.blend"
RUTA_SALIDA_IMG = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_holographic_v06_final.png"

def limpiar_escena():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def crear_material_holograma_edge():
    mat = bpy.data.materials.new(name="Holograma_Bordes")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    node_output = nodes.new(type="ShaderNodeOutputMaterial")
    node_mix = nodes.new(type="ShaderNodeMixShader")
    node_transparent = nodes.new(type="ShaderNodeBsdfTransparent")
    node_emission = nodes.new(type="ShaderNodeEmission")
    node_fresnel = nodes.new(type="ShaderNodeLayerWeight")
    node_math = nodes.new(type="ShaderNodeMath")
    
    node_math.operation = "POWER"
    node_math.inputs[1].default_value = 6.0
    
    # Brillo cian intenso para simular neon de diagnostico
    node_emission.inputs["Color"].default_value = (0.0, 0.6, 1.0, 1.0)
    node_emission.inputs["Strength"].default_value = 15.0
    node_fresnel.inputs["Blend"].default_value = 0.08
    
    links.new(node_fresnel.outputs["Facing"], node_math.inputs[0])
    links.new(node_math.outputs["Value"], node_mix.inputs["Factor"])
    links.new(node_emission.outputs["Emission"], node_mix.inputs[1])
    links.new(node_transparent.outputs["BSDF"], node_mix.inputs[2])
    links.new(node_mix.outputs["Shader"], node_output.inputs["Surface"])
    
    mat.blend_method = "BLEND"
    return mat

def configurar_mundo_y_camara():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = RUTA_SALIDA_IMG
    
    if scene.world:
        scene.world.node_tree.nodes["Background"].inputs.default_value = (0.001, 0.002, 0.005, 1.0)
        
    # Camara en perspectiva 3/4 baja para darle imponencia al sedan
    bpy.ops.object.camera_add(location=(2.6, -3.6, 1.1))
    cam_obj = bpy.context.active_object
    scene.camera = cam_obj
    cam_obj.rotation_euler = (math.radians(78), 0, math.radians(35))
    cam_obj.data.lens = 75

def procesar():
    limpiar_escena()
    bpy.ops.import_scene.gltf(filepath=RUTA_MODELO)
    
    mat = crear_material_holograma_edge()
    
    # Aplicar shader e inyectar modificador de malla de alambre para simular contornos de ingenieria
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            obj.data.materials.clear()
            obj.data.materials.append(mat)
            
            # Agrega un sutil modificador Wireframe mixto para pintar las aristas principales
            wire = obj.modifiers.new(name="ContornoTecnico", type="WIREFRAME")
            wire.thickness = 0.0015
            wire.use_replace = False
            
    configurar_mundo_y_camara()
    bpy.ops.wm.save_as_mainfile(filepath=RUTA_SALIDA_BLEND)
    print("\nRenderizando modelo optimizado con entramado neon de alta precision...")
    bpy.ops.render.render(write_still=True)
    print(f"\n[PROCESO COMPLETADO] Render finalizado con éxito.")

if __name__ == "__main__":
    procesar()
