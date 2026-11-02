import bpy
import math
import os

RUTA_MODELO = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_diagnostic/working_copy.glb"
RUTA_SALIDA_BLEND = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_holographic_v07_real.blend"
RUTA_SALIDA_IMG = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_holographic_v07_real.png"

def limpiar_escena():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def crear_material_holograma_corregido():
    mat = bpy.data.materials.new(name="Holograma_Transparente_Real")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Nodos principales
    node_output = nodes.new(type="ShaderNodeOutputMaterial")
    node_mix = nodes.new(type="ShaderNodeMixShader")
    node_transparent = nodes.new(type="ShaderNodeBsdfTransparent")
    node_emission = nodes.new(type="ShaderNodeEmission")
    node_fresnel = nodes.new(type="ShaderNodeLayerWeight")
    node_ramp = nodes.new(type="ShaderNodeValToRGB")
    
    # Configurar ColorRamp para forzar contornos finos e interior oscuro
    node_ramp.color_ramp.elements[0].position = 0.15
    node_ramp.color_ramp.elements[0].color = (0.0, 0.05, 0.2, 0.1) # Centro: Azul muy oscuro, muy transparente
    node_ramp.color_ramp.elements[1].position = 0.85
    node_ramp.color_ramp.elements[1].color = (0.0, 0.7, 1.0, 1.0)  # Bordes: Cian brillante
    
    # Ajustar Emision
    node_emission.inputs["Color"].default_value = (0.0, 0.7, 1.0, 1.0)
    node_emission.inputs["Strength"].default_value = 5.0
    node_fresnel.inputs["Blend"].default_value = 0.2
    
    # Conectar los nodos para controlar la transparencia centro/borde
    links.new(node_fresnel.outputs["Facing"], node_ramp.inputs["Fac"])
    links.new(node_ramp.outputs["Color"], node_mix.inputs["Factor"])
    links.new(node_transparent.outputs["BSDF"], node_mix.inputs[1])
    links.new(node_emission.outputs["Emission"], node_mix.inputs[2])
    links.new(node_mix.outputs["Shader"], node_output.inputs["Surface"])
    
    # Configurar transparencia alfa en Eevee para que no sea un bloque solido
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
        scene.world.node_tree.nodes["Background"].inputs.default_value = (0.0, 0.0, 0.0, 1.0) # Negro absoluto
        
    # Camara estilo estudio
    bpy.ops.object.camera_add(location=(3.5, -4.5, 1.6))
    cam_obj = bpy.context.active_object
    scene.camera = cam_obj
    cam_obj.rotation_euler = (math.radians(72), 0, math.radians(38))
    cam_obj.data.lens = 85

def procesar():
    limpiar_escena()
    bpy.ops.import_scene.gltf(filepath=RUTA_MODELO)
    
    mat = crear_material_holograma_corregido()
    
    # Aplicar SOLO el material shader, SIN ningun modificador que rompa la malla
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            obj.data.materials.clear()
            obj.data.materials.append(mat)
            obj.modifiers.clear() # Limpia cualquier modificador previo
            
    configurar_mundo_y_camara()
    bpy.ops.wm.save_as_mainfile(filepath=RUTA_SALIDA_BLEND)
    print("\nRenderizando mapa de contornos de transicion suave...")
    bpy.ops.render.render(write_still=True)
    print(f"\n[PROCESO COMPLETADO] Imagen guardada en: {RUTA_SALIDA_IMG}")

if __name__ == "__main__":
    procesar()
