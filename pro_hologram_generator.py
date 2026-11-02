import bpy
import math
import os

RUTA_MODELO = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_diagnostic/working_copy.glb"
RUTA_SALIDA_BLEND = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_holographic_v04_pro.blend"
RUTA_SALIDA_IMG = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_holographic_v04_pro.png"

def limpiar_escena():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def crear_material_holograma_pro():
    mat = bpy.data.materials.new(name="Holograma_Pro_Reference")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Crear nodos
    node_output = nodes.new(type="ShaderNodeOutputMaterial")
    node_mix = nodes.new(type="ShaderNodeMixShader")
    node_transparent = nodes.new(type="ShaderNodeBsdfTransparent")
    node_emission = nodes.new(type="ShaderNodeEmission")
    node_fresnel = nodes.new(type="ShaderNodeLayerWeight")
    node_math = nodes.new(type="ShaderNodeMath")
    
    # Configurar Matematica para afilar el borde (Efecto Power)
    node_math.operation = "POWER"
    node_math.inputs[1].default_value = 4.0
    
    # Configurar Brillo Cian Neon Intenso
    node_emission.inputs["Color"].default_value = (0.0, 0.6, 1.0, 1.0)
    node_emission.inputs["Strength"].default_value = 8.0
    node_fresnel.inputs["Blend"].default_value = 0.15
    
    # Conectar logica para iluminar estrictamente los bordes externos
    links.new(node_fresnel.outputs["Facing"], node_math.inputs[0])
    links.new(node_math.outputs["Value"], node_mix.inputs["Factor"])
    links.new(node_emission.outputs["Emission"], node_mix.inputs[1])
    links.new(node_transparent.outputs["BSDF"], node_mix.inputs[2])
    links.new(node_mix.outputs["Shader"], node_output.inputs["Surface"])
    
    mat.blend_method = "BLEND"
    return mat

def configurar_escena_y_camara():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    
    # Configurar resolucion y formato
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = RUTA_SALIDA_IMG
    
    # Forzar Mundo Azul Oscuro de Estudio
    if scene.world:
        scene.world.node_tree.nodes["Background"].inputs.default_value = (0.002, 0.005, 0.01, 1.0)
        
    # Colocar la camara cerca (Estilo Perspectiva 3/4 de la Referencia)
    bpy.ops.object.camera_add(location=(3.2, -4.2, 1.8))
    cam_obj = bpy.context.active_object
    scene.camera = cam_obj
    
    # Rotacion exacta apuntando al auto
    cam_obj.rotation_euler = (math.radians(72), 0, math.radians(38))
    
    # Cambiar a lente de 85mm para evitar deformacion y dar aspecto premium
    cam_obj.data.lens = 85

def procesar():
    limpiar_escena()
    bpy.ops.import_scene.gltf(filepath=RUTA_MODELO)
    
    mat = crear_material_holograma_pro()
    
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            obj.data.materials.clear()
            obj.data.materials.append(mat)
            
    configurar_escena_y_camara()
    
    # Guardar cambios en el .blend y ejecutar render inmediato
    bpy.ops.wm.save_as_mainfile(filepath=RUTA_SALIDA_BLEND)
    print("\nProcesando renderizado con encuadre de referencia...")
    bpy.ops.render.render(write_still=True)
    print(f"\n[PROCESO EXITOSO] Prototipo e imagen optimizados.")

if __name__ == "__main__":
    procesar()
