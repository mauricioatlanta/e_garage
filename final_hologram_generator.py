import bpy
import math
import os

RUTA_MODELO = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_diagnostic/working_copy.glb"
RUTA_SALIDA_BLEND = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_holographic_final_wire.blend"
RUTA_SALIDA_IMG = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_holographic_final_wire.png"

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
    
    mat_chasis = crear_material_holograma("Holo_Chasis", (0.0, 0.05, 0.2, 1.0), (0.0, 0.7, 1.0, 1.0), 12.0, 0.15, 4.5)
    mat_ventanas = crear_material_holograma("Holo_Ventanas", (0.0, 0.1, 0.3, 0.05), (0.0, 0.9, 1.0, 1.0), 5.0, 0.03, 7.0)
    
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
    
    # CREAR PLANO CON REJILLA PROCEDURAL
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.01))
    suelo = bpy.context.active_object
    mat_suelo = bpy.data.materials.new(name="Suelo_Grid_Tecnico")
    mat_suelo.use_nodes = True
    s_nodes = mat_suelo.node_tree.nodes
    s_links = mat_suelo.node_tree.links
    s_nodes.clear()
    
    out = s_nodes.new(type="ShaderNodeOutputMaterial")
    mix = s_nodes.new(type="ShaderNodeMixShader")
    trans = s_nodes.new(type="ShaderNodeBsdfTransparent")
    emit = s_nodes.new(type="ShaderNodeEmission")
    tex_grid = s_nodes.new(type="ShaderNodeTexGrid")
    
    # Ajustes de la cuadricula de ingenieria
    tex_grid.inputs["Scale"].default_value = 10.0
    tex_grid.inputs["Line Width"].default_value = 0.02
    emit.inputs["Color"].default_value = (0.0, 0.4, 0.8, 1.0) # Lineas cian sutiles
    emit.inputs["Strength"].default_value = 1.5
    
    s_links.new(tex_grid.outputs["Color"], mix.inputs["Factor"])
    s_links.new(trans.outputs["BSDF"], mix.inputs[1])
    s_links.new(emit.outputs["Emission"], mix.inputs[2])
    s_links.new(mix.outputs["Shader"], out.inputs["Surface"])
    mat_suelo.blend_method = "BLEND"
    suelo.data.materials.append(mat_suelo)
    
    # CONFIGURAR RENDER CYCLES VELOZ
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
    print("\nGenerando plano de ingenieria final...")
    bpy.ops.render.render(write_still=True)
    print(f"\n[PROCESO COMPLETADO] Imagen guardada en: {RUTA_SALIDA_IMG}")

if __name__ == "__main__":
    procesar()
