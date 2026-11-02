import bpy
import math
import os

RUTA_MODELO = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_diagnostic/working_copy.glb"
RUTA_SALIDA_BLEND = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_holographic_v09_glass.blend"
RUTA_SALIDA_IMG = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_holographic_v09_glass.png"

def limpiar_escena():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def crear_material_base(nombre, color_base, color_emit, fuerza_emit, blend_fresnel, potencia):
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
    
    # 1. Crear el material de la Carroceria (Azul profundo misterioso)
    mat_carroceria = crear_material_base("Holo_Carroceria", (0.0, 0.05, 0.2, 1.0), (0.0, 0.6, 1.0, 1.0), 10.0, 0.18, 4.0)
    
    # 2. Crear el material de los Cristales (Mucho mas transparente y azulado limpio)
    mat_cristal = crear_material_base("Holo_Cristal", (0.0, 0.1, 0.3, 0.2), (0.0, 0.8, 1.0, 1.0), 6.0, 0.05, 6.0)
    
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            obj.data.materials.clear()
            obj.data.materials.append(mat_carroceria) # Slot 0
            obj.data.materials.append(mat_cristal)    # Slot 1
            obj.modifiers.clear()
            
            # Algoritmo de asignacion por orientacion de caras (Normales)
            # Las ventanas suelen ser caras laterales elevadas o inclinadas
            mesh = obj.data
            for polygon in mesh.polygons:
                normal = polygon.normal
                # Si la cara apunta hacia arriba/lados y esta en la zona superior del vehiculo
                if abs(normal.z) > 0.3 and abs(normal.z) < 0.85 and polygon.center.z > 0.4:
                    polygon.material_index = 1 # Asignar Cristal
                else:
                    polygon.material_index = 0 # Asignar Carroceria
                    
    # Configurar Entorno
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = RUTA_SALIDA_IMG
    if scene.world:
        scene.world.node_tree.nodes["Background"].inputs.default_value = (0.0, 0.0, 0.0, 1.0)
        
    # Camara
    bpy.ops.object.camera_add(location=(3.4, -4.4, 1.5))
    cam_obj = bpy.context.active_object
    scene.camera = cam_obj
    cam_obj.rotation_euler = (math.radians(73), 0, math.radians(38))
    cam_obj.data.lens = 85
    
    bpy.ops.wm.save_as_mainfile(filepath=RUTA_SALIDA_BLEND)
    print("\nSeparando cristales por analisis geometrico...")
    bpy.ops.render.render(write_still=True)
    print(f"\n[PROCESO COMPLETADO] Imagen guardada en: {RUTA_SALIDA_IMG}")

if __name__ == "__main__":
    procesar()
