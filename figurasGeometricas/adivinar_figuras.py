import speech_recognition as sr
from gtts import gTTS
import os
import pygame
import cv2
import numpy as np
import time
import random

# --- Voz ---
def hablar(texto):
    print(f"Robot dice: {texto}")
    try:
        tts = gTTS(text=texto, lang='es', slow=False)
        filename = "robot_response.mp3"
        tts.save(filename)
        pygame.mixer.init()
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.quit()
        os.remove(filename)
    except Exception as e:
        print(f"Error al reproducir audio: {e}")
        print(f"Robot intentó decir: {texto}")


def escuchar():
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=1)
            audio = r.listen(source, timeout=6, phrase_time_limit=6)
        texto = r.recognize_google(audio, language="es-ES")
        print(f"Tú dijiste: {texto}")
        return texto.lower()
    except sr.UnknownValueError:
        hablar("No pude entender lo que dijiste.")
        return ""
    except sr.RequestError as e:
        hablar(f"Error de reconocimiento de voz: {e}")
        return ""
    except Exception as e:
        print(f"Error inesperado al escuchar: {e}")
        return ""

# --- Dibujar figuras simples ---

def dibujar_figura(nombre, size=400):
    h = size
    w = size
    img = np.ones((h, w, 3), dtype=np.uint8) * 255
    center = (w // 2, h // 2)
    color = (0, 0, 0)
    thickness = 6

    if nombre == 'círculo' or nombre == 'circulo':
        cv2.circle(img, center, size//4, color, thickness)
    elif nombre == 'cuadrado':
        side = size//2
        top_left = (center[0]-side//2, center[1]-side//2)
        bottom_right = (center[0]+side//2, center[1]+side//2)
        cv2.rectangle(img, top_left, bottom_right, color, thickness)
    elif nombre == 'rectángulo' or nombre == 'rectangulo':
        wrect = int(size*0.6)
        hrect = int(size*0.4)
        top_left = (center[0]-wrect//2, center[1]-hrect//2)
        bottom_right = (center[0]+wrect//2, center[1]+hrect//2)
        cv2.rectangle(img, top_left, bottom_right, color, thickness)
    elif nombre == 'triángulo' or nombre == 'triangulo':
        pts = np.array([[center[0], center[1]-size//4], [center[0]-size//4, center[1]+size//4], [center[0]+size//4, center[1]+size//4]], np.int32)
        cv2.polylines(img, [pts], True, color, thickness)
    else:
        cv2.putText(img, 'Figura', (50, h//2), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,0,0), 2)

    return img

# Sólo permitir estas cuatro figuras (variantes sin tilde incluidas)
ALLOWED_SHAPES = {"círculo","circulo","cuadrado","triángulo","triangulo","rectángulo","rectangulo"}

def filtrar_figura_detectada(nombre):
    """Normaliza y permite sólo círculo/cuadrado/triángulo/rectángulo; devuelve 'desconocida' si no."""
    if not nombre:
        return "desconocida"
    n = nombre.lower().strip()
    # normalizar acentos básicos
    n = n.replace("á","a").replace("í","i").replace("ó","o").replace("ú","u").replace("é","e")
    # comprobar permitido
    if n in ALLOWED_SHAPES:
        if "triang" in n:
            return "triángulo"
        if "cuadr" in n:
            return "cuadrado"
        if "rect" in n:
            return "rectángulo"
        if "cir" in n:
            return "círculo"
    return "desconocida"

# --- Modo: adivinar (robot muestra, niño responde) ---

def iniciar_modo_adivinar():
    hablar("¡Hola! Vamos a jugar a adivinar. Yo te mostraré una figura en pantalla y tú me dirás su nombre.")

    figuras = ['cuadrado', 'círculo', 'triángulo', 'rectángulo']
    for i in range(3):
        objetivo = random.choice(figuras)
        img = dibujar_figura(objetivo)
        ventana = 'Adivina la figura'
        cv2.namedWindow(ventana, cv2.WINDOW_NORMAL)
        cv2.imshow(ventana, img)
        cv2.setWindowProperty(ventana, cv2.WND_PROP_TOPMOST, 1)
        
        # Procesar eventos de ventana mientras hablamos
        hablar(f"Mira la figura en la pantalla. ¿Qué figura es?")
        for _ in range(10):  # Mantener la ventana actualizada
            cv2.waitKey(100)
            if cv2.getWindowProperty(ventana, cv2.WND_PROP_VISIBLE) < 1:
                break
                
        # Escuchar respuesta
        respuesta = escuchar()
        cv2.destroyWindow(ventana)
        cv2.waitKey(1)  # Dar tiempo a que se cierre la ventana

        if respuesta == "":
            hablar("No te escuché bien.")
            continue

        # Normalizar y verificar
        resp_norm = respuesta.replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')
        objetivo_norm = objetivo.replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')

        if objetivo_norm in resp_norm:
            hablar("¡Correcto! Muy bien.")
        else:
            hablar(f"Casi. Era un {objetivo}.")
        time.sleep(1)

    hablar("Hemos terminado el modo adivinar. ¡Buen trabajo!")


if __name__ == '__main__':
    try:
        iniciar_modo_adivinar()
    except KeyboardInterrupt:
        hablar("Adiós")
    finally:
        try:
            if pygame.mixer.get_init():
                pygame.mixer.quit()
        except Exception:
            pass
        cv2.destroyAllWindows()
