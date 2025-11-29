import cv2
import numpy as np
import time
import random
import os
from gtts import gTTS
import pygame

# --- Voz ---
def hablar(texto):
    print("Robot:", texto)
    try:
        fname = "tts_mostrar.mp3"
        tts = gTTS(text=str(texto), lang="es", slow=False)
        tts.save(fname)
        pygame.mixer.init()
        pygame.mixer.music.load(fname)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.quit()
        try:
            os.remove(fname)
        except Exception:
            pass
    except Exception as e:
        print("Audio error:", e)

def normalize_name(s):
    if not s:
        return ""
    s = s.lower().strip()
    for a,b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u")]:
        s = s.replace(a,b)
    return s

# Colores y sus rangos HSV (valores probables; ajustar en tu entorno)
COLOR_RANGES = {
    "rojo": [([0, 90, 60], [8, 255, 255]), ([170, 90, 60], [179,255,255])], # rojo en dos rangos
    "verde": [([35, 60, 40], [90, 255, 255])],
    "azul": [([90, 60, 40], [140, 255, 255])],
    "amarillo": [([18, 100, 100], [34, 255, 255])],
    "naranja": [([9, 100, 100], [17, 255, 255])]
}

# lista de colores a usar (sólo los que tenemos rangos)
AVAILABLE = list(COLOR_RANGES.keys())

def detectar_color_principal(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    best_color = None
    best_area = 0
    masks = {}
    for name, ranges in COLOR_RANGES.items():
        total_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for lo, hi in ranges:
            lo = np.array(lo); hi = np.array(hi)
            total_mask = cv2.bitwise_or(total_mask, cv2.inRange(hsv, lo, hi))
        # limpieza
        kernel = np.ones((5,5), np.uint8)
        total_mask = cv2.morphologyEx(total_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        total_mask = cv2.morphologyEx(total_mask, cv2.MORPH_CLOSE, kernel, iterations=1)
        area = int(np.sum(total_mask > 0))
        masks[name] = (total_mask, area)
        if area > best_area:
            best_area = area
            best_color = name
    return best_color, best_area, masks

def jugar_mostrar(rounds=4, timeout=15, hold_time=1.0):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        hablar("No pude abrir la cámara.")
        return
    hablar("Vamos a jugar a mostrar colores. Yo pediré un color y tú lo mostrarás a la cámara.")
    time.sleep(0.6)
    ventana = "MostrarColor"
    cv2.namedWindow(ventana, cv2.WINDOW_NORMAL)
    for r in range(rounds):
        objetivo = random.choice(AVAILABLE)
        hablar(f"Ronda {r+1}. Por favor, muestra {objetivo}. Tienes {timeout} segundos.")
        start = time.time()
        hold_start = None
        success = False
        best_seen = None
        while time.time() - start < timeout:
            ret, frame = cap.read()
            if not ret:
                continue
            frame = cv2.flip(frame, 1)
            color, area, masks = detectar_color_principal(frame)
            best_seen = color
            # dibujar máscara del color principal para debug
            mask_vis = None
            if color:
                mask_vis = masks[color][0]
                mask_vis_bgr = cv2.cvtColor(mask_vis, cv2.COLOR_GRAY2BGR)
                debug = np.hstack((cv2.resize(frame, (320,240)), cv2.resize(mask_vis_bgr, (320,240))))
            else:
                debug = cv2.resize(frame, (640,240))
            cv2.imshow(ventana, debug)
            # criterio: area suficientemente grande y corresponde al objetivo
            if color == objetivo and area > 20000:  # umbral a ajustar según cámara/objetos
                if hold_start is None:
                    hold_start = time.time()
                elapsed = time.time() - hold_start
                cv2.putText(debug, f"Holding: {elapsed:.1f}/{hold_time}s", (10,50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,200,0), 2)
                if elapsed >= hold_time:
                    success = True
                    hablar("¡Perfecto! Muy bien mostrado.")
                    break
            else:
                hold_start = None
            if cv2.waitKey(50) & 0xFF == ord('q'):
                hablar("Saliendo del juego.")
                cap.release()
                cv2.destroyAllWindows()
                return
        if not success:
            if best_seen:
                hablar(f"Casi. Yo vi {best_seen}. ¡Animo, inténtalo otra vez!")
            else:
                hablar("No detecté el color. Mejora la iluminación o acércalo a la cámara.")
        time.sleep(0.8)
    hablar("Hemos terminado las rondas de mostrar color. ¡Buen trabajo!")
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        jugar_mostrar(rounds=4)
    finally:
        try:
            if pygame.mixer.get_init():
                pygame.mixer.quit()
        except Exception:
            pass