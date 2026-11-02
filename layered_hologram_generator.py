import bpy
import math
import os

RUTA_MODELO = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_diagnostic/working_copy.glb"
RUTA_SALIDA_BLEND = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_holographic_v10_layered.blend"
RUTA_SALIDA_IMG = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_holographic_v10_layered.png"

def limpiar_escena():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def crear_material_holograma(nombre, color_base, color_emit, fuerza_emit, blend_fresnel, potencia):
    mat = bpy.data.materials.new(name=nombre)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    node_output = nodes.new(type="ShaderNodeOutputMaterial")
    node_principled = nodes.new(type="ShaderNodeBsdfPrincipled")
    node_fresnel = nodes.new(type="ShaderNodeLayerWeight")
    node_math = nodes.new(type="ShaderNodeMath")
    
    node_math.operation = "POWER"
    node_math.inputs[1].default_value = potencia
    
    node_principled.inputs["Base Color"].default_value = color_base
    node_principled.inputs["Emission Color"].default_value = color_emit
    node_principled.inputs["Emission Strength"].default_value = fuerza_emit
    node_fresnel.inputs["Blend"].default_value = blend_fresnel
    
    links.new(node_fresnel.outputs["Facing"], node_math.inputs[0])
    links.new(node_math.outputs["Value"], node_principled.inputs["Alpha"])
    links.new(node_principled.outputs["BSDF"], node_output.inputs["Surface"])
    
    mat.blend_method = "BLEND"
    return mat

def procesar():
    limpiar_escena()
    bpy.ops.import_scene.gltf(filepath=RUTA_MODELO)
    
    # 1. Diseñar el material maestro para la Carrocería (Bordes definidos)
    mat_chasis = crear_material_holograma("Holo_Chasis", (0.0, 0.05, 0.2, 1.0), (0.0, 0.6, 1.0, 1.0), 14.0, 0.15, 4.5)
    
    # 2. Diseñar el material premium para los Cristales (Centro ultratransparente)
    mat_ventanas = crear_material_holograma("Holo_Ventanas", (0.0, 0.1, 0.3, 0.05), (0.0, 0.8, 1.0, 1.0), 5.0, 0.03, 7.0)
    
    # Buscar la malla del auto
    auto_mesh = None
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            auto_mesh = obj
            break
            
    if auto_mesh:
        # Configurar capa base
        auto_mesh.data.materials.clear()
        auto_mesh.data.materials.append(mat_chasis)
        
        bpy.ops.object.select_all(action="DESELECT")
        auto_mesh.select_set(True)
        bpy.context.view_layer.objects.active = auto_mesh
        
        # Clonar malla para superposición de cristales
        bpy.ops.object.duplicate()
        copia_cristal = bpy.context.active_object
        copia_cristal.name = "Auto_Capa_Cristal"
        copia_cristal.data.materials.clear()
        copia_cristal.data.materials.append(mat_ventanas)
        
        # Escalar imperceptiblemente hacia afuera para evitar parpadeo de mallas
        copia_cristal.scale = (1.002, 1.002, 1.002)
    
    # Configuración de render e iluminación de fondo
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = RUTA_SALIDA_IMG
    if scene.world:
        scene.world.node_tree.nodes["Background"].inputs.default_value = (0.0, 0.0, 0.0, 1.0)
        
    # Cámara de Estudio 3/4
    bpy.ops.object.camera_add(location=(3.4, -4.4, 1.5))
    cam_obj = bpy.context.active_object
    scene.camera = cam_obj
    cam_obj.rotation_euler = (math.radians(73), 0, math.radians(38))
    cam_obj.data.lens = 85
    
    bpy.ops.wm.save_as_mainfile(filepath=RUTA_SALIDA_BLEND)
    print("\nGenerando render bicapa corregido...")
    bpy.ops.render.render(write_still=True)
    print(f"\n[PROCESO COMPLETADO] Imagen guardada en: {RUTA_SALIDA_IMG}")

if __name__ == "__main__":
    procesar()
