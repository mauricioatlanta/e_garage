import bpy
import math

RUTA_BLEND = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_holographic_v03_final.blend"
RUTA_IMG = "/mnt/datos/projecto/e_garage_rubro_integracion/artifacts/meshy_sedan_holographic_v03_final.png"

def generar_render():
    bpy.ops.wm.open_mainfile(filepath=RUTA_BLEND)
    scene = bpy.context.scene
    
    # Crear camara en posicion de perspectiva 3/4
    bpy.ops.object.camera_add(location=(7.0, -7.0, 4.0))
    cam = bpy.context.active_object
    scene.camera = cam
    
    # Orientar camara hacia el centro del auto
    cam.rotation_euler = (math.radians(65), 0, math.radians(45))
    
    # Ajustes finales de imagen
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = RUTA_IMG
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    
    print("\nProcesando renderizado de alta calidad...")
    bpy.ops.render.render(write_still=True)
    print(f"\n[RENDER COMPLETADO] Imagen guardada en: {RUTA_IMG}")

if __name__ == "__main__":
    generar_render()
