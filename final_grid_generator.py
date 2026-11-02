import bpy
import math
import os

RUTA_MODELO = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_diagnostic/working_copy.glb"
RUTA_SALIDA_BLEND = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_holographic_final_grid.blend"
RUTA_SALIDA_IMG = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_holographic_final_grid.png"

def limpiar_escena():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def crear_material_holograma_limpio(nombre, color_base, color_emit, fuerza_emit, blend_fresnel):
    mat = bpy.data.materials.new(name=nombre)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    node_output = nodes.new(type="ShaderNodeOutputMaterial")
    node_principled = nodes.new(type="ShaderNodeBsdfPrincipled")
    node_fresnel = nodes.new(type="ShaderNodeLayerWeight")
    
    node_principled.inputs["Base Color"].default_value = color_base
    node_principled.inputs["Emission Color"].default_value = color_emit
    node_principled.inputs["Emission Strength"].default_value = fuerza_emit
    node_fresnel.inputs["Blend"].default_value = blend_fresnel
    
    # Conectar Fresnel directo al Alpha nativo sin nodos intermedios problemáticos
    links.new(node_fresnel.outputs["Facing"], node_principled.inputs["Alpha"])
    links.new(node_principled.outputs["BSDF"], node_output.inputs["Surface"])
    mat.blend_method = "BLEND"
    return mat

def procesar():
    limpiar_escena()
    bpy.ops.import_scene.gltf(filepath=RUTA_MODELO)
    
    mat_chasis = crear_material_holograma_limpio("Holo_Chasis", (0.0, 0.05, 0.2, 1.0), (0.0, 0.7, 1.0, 1.0), 12.0, 0.25)
    mat_ventanas = crear_material_holograma_limpio("Holo_Ventanas", (0.0, 0.1, 0.3, 0.05), (0.0, 0.9, 1.0, 1.0), 6.0, 0.1)
    
    auto_mesh = None
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            auto_mesh = obj
            break
            
    if auto_mesh:
        auto_mesh.data.materials.clear()
        auto_mesh.data.materials.append(mat_chasis)
        bpy.ops.object.select_all(action="DESELECT")
        auto_mesh.select_set(True)
        bpy.context.view_layer.objects.active = auto_mesh
        bpy.ops.object.duplicate()
        copia_cristal = bpy.context.active_object
        copia_cristal.data.materials.clear()
        copia_cristal.data.materials.append(mat_ventanas)
        copia_cristal.scale = (1.002, 1.002, 1.002)
    
    # CREAR PLANO CON REJILLA PROCEDURAL (CHECKER)
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.01))
    suelo = bpy.context.active_object
    mat_suelo = bpy.data.materials.new(name="Suelo_Grid_Nativo")
    mat_suelo.use_nodes = True
    s_nodes = mat_suelo.node_tree.nodes
    s_links = mat_suelo.node_tree.links
    s_nodes.clear()
    
    out = s_nodes.new(type="ShaderNodeOutputMaterial")
    principled = s_nodes.new(type="ShaderNodeBsdfPrincipled")
    checker = s_nodes.new(type="ShaderNodeTexChecker")
    
    checker.inputs["Scale"].default_value = 25.0
    checker.inputs["Color1"].default_value = (0.001, 0.002, 0.005, 1.0)
    checker.inputs["Color2"].default_value = (0.0, 0.15, 0.3, 1.0)
    principled.inputs["Roughness"].default_value = 0.2
    
    s_links.new(checker.outputs["Color"], principled.inputs["Base Color"])
    s_links.new(principled.outputs["BSDF"], out.inputs["Surface"])
    suelo.data.materials.append(mat_suelo)
    
    # CONFIGURAR RENDER CYCLES
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    if hasattr(scene, "cycles"):
        scene.cycles.samples = 32
        scene.cycles.use_denoising = True
    
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = RUTA_SALIDA_IMG
    if scene.world:
        scene.world.node_tree.nodes["Background"].inputs.default_value = (0.0, 0.0, 0.0, 1.0)
    
    # CÁMARA
    bpy.ops.object.camera_add(location=(3.4, -4.4, 1.5))
    cam_obj = bpy.context.active_object
    scene.camera = cam_obj
    cam_obj.rotation_euler = (math.radians(73), 0, math.radians(38))
    cam_obj.data.lens = 85
    
    bpy.ops.wm.save_as_mainfile(filepath=RUTA_SALIDA_BLEND)
    print("\nRenderizando entregable final libre de errores con Cycles...")
    bpy.ops.render.render(write_still=True)
    print(f"\n[PROCESO COMPLETADO] Imagen guardada en: {RUTA_SALIDA_IMG}")

if __name__ == "__main__":
    procesar()
