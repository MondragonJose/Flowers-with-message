import tkinter as tk
import json
import sys, os
import pygame # type: ignore

def resource_path(relative_path):
    """Para que funcione tanto en .py como en el .exe"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def play_music():
    pygame.mixer.init()
    audio_path = resource_path("flores.mp3")  # usa resource_path
    pygame.mixer.music.load(audio_path)
    pygame.mixer.music.play(-1)  # -1 = loop infinito


def draw_from_json(json_file, canvas_size=800, margin=100,
                   regions_per_frame=30, draw_delay=60,
                   max_points_per_region=2000):
    """
    Dibuja el JSON en un Canvas de Tkinter de forma optimizada.
    Parámetros:
      - canvas_size: tamaño del canvas (px).
      - margin: margen en px para no tocar los bordes.
      - regions_per_frame: cuántas regiones dibujar por iteración (aumenta para mayor velocidad).
      - draw_delay: ms entre iteraciones (0-50). Menor = más rápido.
      - max_points_per_region: máximo de puntos a usar por polígono (se muestrea si hay más).
    """

    # Abrir archivo JSON
    with open(json_file, "r", encoding="utf-8") as f:
        regions = json.load(f)

    # Crear ventana y canvas
    root = tk.Tk()
    root.title("Flores amarillas 🌻")
    canvas = tk.Canvas(root, bg="black", width=canvas_size, height=canvas_size)
    canvas.pack()
    status = tk.Label(root, text="Preparando...", fg="white", bg="black")
    status.pack(side="bottom", fill="x")
    
    # 1) Calcular límites (una sola pasada, sin guardar todos los puntos)
    min_x = float("inf"); max_x = float("-inf")
    min_y = float("inf"); max_y = float("-inf")

    for r in regions:
        for p in r['contour']:
            x, y = p[0], p[1]
            if x < min_x: min_x = x
            if x > max_x: max_x = x
            if y < min_y: min_y = y
            if y > max_y: max_y = y

    # Protección contra casos degenerados
    width = max_x - min_x if (max_x - min_x) != 0 else 1.0
    height = max_y - min_y if (max_y - min_y) != 0 else 1.0

    # Escala y centro con margen
    usable = canvas_size - margin * 2
    scale = min(usable / width, usable / height)
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    cx_canvas = canvas_size / 2.0
    cy_canvas = canvas_size / 2.0

    # Helper: convertir color a #rrggbb (soporta tanto 0..1 como 0..255)
    def color_to_hex(col):
        if not col or len(col) < 3:
            return "#000000"
        # si valores <=1 asumimos normalizados
        if max(col) <= 1.0:
            rgb = [int(max(0, min(255, round(v * 255)))) for v in col[:3]]
        else:
            rgb = [int(max(0, min(255, round(v)))) for v in col[:3]]
        return '#{:02x}{:02x}{:02x}'.format(*rgb)

    total = len(regions)

    # Dibuja regiones por lotes para no bloquear la UI
    def draw_chunk(start_idx=0):
        end_idx = min(total, start_idx + regions_per_frame)
        for i in range(start_idx, end_idx):
            region = regions[i]
            # color robusto
            fill = color_to_hex(region.get('color', [0, 0, 0]))
            contour = region['contour']

            # muestreo si el contorno es muy grande
            n_points = len(contour)
            if n_points == 0:
                continue
            # calcula paso para no superar max_points_per_region
            step = max(1, n_points // max_points_per_region)

            pts = contour[::step]
            poly_coords = []
            for px, py in pts:
                x = (px - center_x) * scale + cx_canvas
                y = (py - center_y) * scale + cy_canvas  # eje corregido
                poly_coords.extend((x, y))

            # si quedan pocos puntos después de muestrear, ignora
            if len(poly_coords) >= 6:
                canvas.create_polygon(poly_coords, fill=fill, outline=fill)

        # actualizar estado
        percent = end_idx / total * 100
        status.config(text=f"Dibujando... {end_idx}/{total} regiones ({percent:.1f}%)")
        # siguiente chunk o finalizar
        if end_idx < total:
            root.after(draw_delay, lambda: draw_chunk(end_idx))
        else:
                # --- TEXTO ARRIBA ---
            canvas.create_text(
                canvas_size/2, 40,
                text="La distancia no impide que te tenga presente.",
                fill="gold", font=("Verdana", 16, "bold italic")
                )
            canvas.create_text(
                canvas_size/2, 70,
                text="Con cariño, Samuelito",
                fill="gold", font=("Verdana", 14, "italic")
                )   
            # ---------------------
            status.config(text="Listo 🎉")

    # arrancar
    root.after(50, lambda: (play_music(), draw_chunk(0)))
    root.mainloop()
    
if __name__ == "__main__":
    json_path = resource_path("sunflowers.json")
    draw_from_json(json_path)