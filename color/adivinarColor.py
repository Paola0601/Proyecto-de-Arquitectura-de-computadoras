import cv2
import numpy as np
import random
import time
import os
from gtts import gTTS
import pygame

# opcional: reconocimiento por voz; si no está instalado, se usa input()
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except Exception:
    SR_AVAILABLE = False

# --- Voz ---
def hablar(texto):
    print("Robot:", texto)
    try:
        fname = "tts_adivinar.mp3"
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
        print("No te escuché bien:", e)

def reconocer_audio(timeout=4, phrase_time_limit=4):
    if not SR_AVAILABLE:
        return input("¿Qué color escucho? (escribe aquí): ").strip().lower()
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.6)
        try:
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            texto = r.recognize_google(audio, language="es-ES")
            return texto.strip().lower()
        except Exception as e:
            print("Speech error:", e)
            return ""

def normalize_name(s):
    if not s:
        return ""
    s = s.lower().strip()
    for a,b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u")]:
        s = s.replace(a,b)
    return s

# lista de colores disponibles (BGR para mostrar)
COLORS = {
    "rojo": (0,0,255),
    "verde": (0,255,0),
    "azul": (255,0,0),
    "amarillo": (0,255,255),
    "naranja": (0,140,255)
}

def mostrar_rectangulo_color(bgr, ventana_name="Color"):
    img = np.zeros((300,300,3), dtype=np.uint8)
    img[:] = bgr
    cv2.imshow(ventana_name, img)

def jugar_adivinar(rounds=4, listen_timeout=4):
    pygame.init()
    hablar("Vamos a jugar a adivinar colores. Te mostraré un color y tú debes decir cuál es.")
    time.sleep(0.6)
    ventana = "Color"
    cv2.namedWindow(ventana, cv2.WINDOW_NORMAL)
    for r in range(rounds):
        target = random.choice(list(COLORS.keys()))
        hablar(f"Ronda {r+1}. Adivina este color.")
        mostrar_rectangulo_color(COLORS[target], ventana)
        start = time.time()
        answered = False
        # esperar respuesta por voz o teclado hasta 6 segundos
        while time.time() - start < 6:
            if cv2.waitKey(100) & 0xFF == ord('q'):
                hablar("Saliendo del juego.")
                cv2.destroyAllWindows()
                return
            # intentar reconocer una respuesta (una sola vez por ronda para simplificar)
            texto = reconocer_audio(timeout=listen_timeout, phrase_time_limit=listen_timeout)
            texto = normalize_name(texto)
            if texto:
                answered = True
                if texto == normalize_name(target):
                    hablar("¡Muy bien! Esa es la respuesta correcta. ¡Excelente!")
                else:
                    hablar(f"No es correcto. Tú dijiste {texto}. Era {target}. ¡Lo harás mejor la próxima vez!")
                break
        if not answered:
            hablar(f"No te escuché. Era {target}.")
        time.sleep(0.8)
    hablar("Hemos terminado las rondas de adivinar colores. ¡Buen trabajo!")
    cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        jugar_adivinar(rounds=4)
    finally:
        try:
            if pygame.mixer.get_init():
                pygame.mixer.quit()
        except Exception:
            pass