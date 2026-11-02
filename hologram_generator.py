import bpy
import os

RUTA_MODELO = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_diagnostic/working_copy.glb"
RUTA_SALIDA = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_holographic_v03_final.blend"

def limpiar_escena():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def importar_modelo(ruta):
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"No se encontro el archivo 3D en: {ruta}")
    bpy.ops.import_scene.gltf(filepath=ruta)
    return bpy.context.selected_objects

def crear_material_holograma():
    mat = bpy.data.materials.new(name="Holograma_Cyber_Final")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    node_output = nodes.new(type="ShaderNodeOutputMaterial")
    node_mix = nodes.new(type="ShaderNodeMixShader")
    node_transparent = nodes.new(type="ShaderNodeBsdfTransparent")
    node_emission = nodes.new(type="ShaderNodeEmission")
    node_fresnel = nodes.new(type="ShaderNodeLayerWeight")
    node_emission.inputs["Color"].default_value = (0.0, 0.7, 1.0, 1.0)
    node_emission.inputs["Strength"].default_value = 2.0
    node_fresnel.inputs["Blend"].default_value = 0.25
    links.new(node_fresnel.outputs["Facing"], node_mix.inputs["Factor"])
    links.new(node_transparent.outputs["BSDF"], node_mix.inputs[1])
    links.new(node_emission.outputs["Emission"], node_mix.inputs[2])
    links.new(node_mix.outputs["Shader"], node_output.inputs["Surface"])
    mat.blend_method = "BLEND"
    return mat

def aplicar_efectos():
    print("\n[1/4] Limpiando entorno virtual...")
    limpiar_escena()
    try:
        print(f"[2/4] Importando archivo GLB...")
        importar_modelo(RUTA_MODELO)
        print("[3/4] Generando shader holografico...")
        mat_holo = crear_material_holograma()
        objetos_procesados = 0
        for obj in bpy.context.scene.objects:
            if obj.type == "MESH":
                obj.data.materials.clear()
                obj.data.materials.append(mat_holo)
                objetos_procesados = objetos_procesados + 1
        bpy.context.scene.render.engine = "BLENDER_EEVEE"
        if bpy.context.scene.world:
            bpy.context.scene.world.node_tree.nodes["Background"].inputs.default_value = (0, 0, 0, 1)
        print(f"[4/4] Guardando archivo .blend...")
        bpy.ops.wm.save_as_mainfile(filepath=RUTA_SALIDA)
        print(f"\n[EXITO] Guardado en: {RUTA_SALIDA}")
    except Exception as e:
        print(f"\n[ERROR EN SCRIPT]: {e}")

if __name__ == "__main__":
    aplicar_efectos()
