import bpy
import math
import os

RUTA_MODELO = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_diagnostic/working_copy.glb"
RUTA_SALIDA_BLEND = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_holographic_v08_alpha.blend"
RUTA_SALIDA_IMG = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_holographic_v08_alpha.png"

def limpiar_escena():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def crear_material_holograma_alpha():
    mat = bpy.data.materials.new(name="Holograma_Transparencia_Nativa")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Crear nodos nativos compatibles con Blender 5.x
    node_output = nodes.new(type="ShaderNodeOutputMaterial")
    node_principled = nodes.new(type="ShaderNodeBsdfPrincipled")
    node_fresnel = nodes.new(type="ShaderNodeLayerWeight")
    node_math = nodes.new(type="ShaderNodeMath")
    
    # Configurar Matematica para afilar los bordes de escaneo
    node_math.operation = "POWER"
    node_math.inputs[1].default_value = 4.0
    
    # Configuracion de color base transparente y emision cian intensa
    node_principled.inputs["Base Color"].default_value = (0.0, 0.1, 0.4, 1.0)
    node_principled.inputs["Emission Color"].default_value = (0.0, 0.7, 1.0, 1.0)
    node_principled.inputs["Emission Strength"].default_value = 12.0
    node_fresnel.inputs["Blend"].default_value = 0.15
    
    # Enlazar la fuerza Fresnel al canal Alpha nativo
    links.new(node_fresnel.outputs["Facing"], node_math.inputs[0])
    links.new(node_math.outputs["Value"], node_principled.inputs["Alpha"])
    links.new(node_principled.outputs["BSDF"], node_output.inputs["Surface"])
    
    # Forzar el calculo de transparencia alfa en el material
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
        scene.world.node_tree.nodes["Background"].inputs.default_value = (0.0, 0.0, 0.0, 1.0)
        
    # Ubicar camara en perspectiva de estudio 3/4
    bpy.ops.object.camera_add(location=(3.4, -4.4, 1.5))
    cam_obj = bpy.context.active_object
    scene.camera = cam_obj
    cam_obj.rotation_euler = (math.radians(73), 0, math.radians(38))
    cam_obj.data.lens = 85

def procesar():
    limpiar_escena()
    bpy.ops.import_scene.gltf(filepath=RUTA_MODELO)
    
    mat = crear_material_holograma_alpha()
    
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            obj.data.materials.clear()
            obj.data.materials.append(mat)
            obj.modifiers.clear()
            
    configurar_mundo_y_camara()
    bpy.ops.wm.save_as_mainfile(filepath=RUTA_SALIDA_BLEND)
    print("\nProcesando render con mapa alpha nativo...")
    bpy.ops.render.render(write_still=True)
    print(f"\n[PROCESO COMPLETADO] Nueva imagen guardada en: {RUTA_SALIDA_IMG}")

if __name__ == "__main__":
    procesar()
