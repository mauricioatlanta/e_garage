from moviepy.editor import *

# Tamaño y duración
w, h = 1280, 720
duration = 10

# Fondo negro
background = ColorClip(size=(w, h), color=(0, 0, 0), duration=duration)

# Frases con tiempo de aparición
frases = [
    ("Productividad inteligente en la palma de tu mano", 0, 2.5),
    ("Sabe quién trabaja mejor. Controla. Mejora. Crece.", 2.5, 5),
    ("Gestiona stock, equipo y garantías sin papel ni estrés", 5, 7.5),
    ("TallerPro", 7.5, 10)
]

# Crear textos animados
text_clips = []
for txt, start, end in frases:
    font_size = 60 if "TallerPro" not in txt else 100
    color = "cyan" if "TallerPro" not in txt else "white"
    txt_clip = TextClip(
        txt, fontsize=font_size, font='Arial-Bold', color=color, method='caption', size=(1000, None)
    ).set_duration(end - start).set_position("center").set_start(start).fadein(0.5).fadeout(0.5)
    text_clips.append(txt_clip)

# Composición final
final = CompositeVideoClip([background, *text_clips])
final.write_videofile("fondo_tallerpro_renderizado.mp4", fps=24)