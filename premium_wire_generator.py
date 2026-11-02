import bpy
import math
import os

RUTA_MODELO = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_diagnostic/working_copy.glb"
RUTA_SALIDA_BLEND = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_holographic_v05_wire.blend"
RUTA_SALIDA_IMG = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_holographic_v05_wire.png"

def limpiar_escena():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def crear_material_holograma_premium():
    mat = bpy.data.materials.new(name="Holograma_Premium")
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
    node_math.inputs[1].default_value = 5.0
    
    # Azul cian de alta intensidad
    node_emission.inputs["Color"].default_value = (0.0, 0.5, 1.0, 1.0)
    node_emission.inputs["Strength"].default_value = 12.0
    node_fresnel.inputs["Blend"].default_value = 0.1
    
    links.new(node_fresnel.outputs["Facing"], node_math.inputs[0])
    links.new(node_math.outputs["Value"], node_mix.inputs["Factor"])
    links.new(node_emission.outputs["Emission"], node_mix.inputs[1])
    links.new(node_transparent.outputs["BSDF"], node_mix.inputs[2])
    links.new(node_mix.outputs["Shader"], node_output.inputs["Surface"])
    
    mat.blend_method = "BLEND"
    return mat

def configurar_render_y_silueta():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = RUTA_SALIDA_IMG
    
    # Activar contornos tecnicos (Freestyle)
    scene.render.use_freestyle = True
    if scene.view_layers:
        rl = scene.view_layers[0]
        rl.freestyle_settings.crease_angle = math.radians(135)
        if rl.freestyle_settings.linesets:
            lineset = rl.freestyle_settings.linesets[0]
            # Forzar color cian brillante en las lineas de contorno
            if bpy.data.linestyles:
                style = bpy.data.linestyles[0]
                style.color = (0.0, 0.7, 1.0)
                style.thickness = 1.5
    
    if scene.world:
        scene.world.node_tree.nodes["Background"].inputs.default_value = (0.001, 0.003, 0.008, 1.0)
        
    # Camara ajustada y mas cercana
    bpy.ops.object.camera_add(location=(2.8, -3.8, 1.4))
    cam_obj = bpy.context.active_object
    scene.camera = cam_obj
    cam_obj.rotation_euler = (math.radians(74), 0, math.radians(36))
    cam_obj.data.lens = 75

def procesar():
    limpiar_escena()
    bpy.ops.import_scene.gltf(filepath=RUTA_MODELO)
    
    mat = crear_material_holograma_premium()
    
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            obj.data.materials.clear()
            obj.data.materials.append(mat)
            
    configurar_render_y_silueta()
    bpy.ops.wm.save_as_mainfile(filepath=RUTA_SALIDA_BLEND)
    print("\nGenerando render avanzado con lineas de contorno estructuradas...")
    bpy.ops.render.render(write_still=True)
    print(f"\n[PROCESO COMPLETADO] Imagen guardada en: {RUTA_SALIDA_IMG}")

if __name__ == "__main__":
    procesar()
