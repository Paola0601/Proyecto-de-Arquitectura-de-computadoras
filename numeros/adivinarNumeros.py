import random
import time
from gtts import gTTS
import pygame
import speech_recognition as sr
import os
import cv2
import numpy as np

# --- Voz (gTTS + pygame) ---
def hablar(texto):
    """Genera y reproduce un audio corto con gTTS (es)."""
    print(f"Robot dice: {texto}")
    try:
        fname = "tts_tmp_robot_visual.mp3"
        tts = gTTS(text=str(texto), lang='es', slow=False)
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
        print("Error al reproducir audio:", e)

# --- Reconocimiento de Voz ---
def escuchar_numero():
    """Escucha la entrada del micrófono y retorna el número dicho."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source) # Ajusta el ruido ambiental
        audio = r.listen(source, timeout=5, phrase_time_limit=5) # Escucha por 5 segundos

    try:
        texto = r.recognize_google(audio, language='es-ES')
        print(f"Tú dijiste: {texto}")
        # Intentar extraer un número del texto
        for palabra in texto.split():
            if palabra.isdigit():
                return int(palabra)
        # Si no se encuentra un dígito, intentar con palabras comunes para números
        if "cero" in texto.lower(): return 0
        if "uno" in texto.lower(): return 1
        if "dos" in texto.lower(): return 2
        if "tres" in texto.lower(): return 3
        if "cuatro" in texto.lower(): return 4
        if "cinco" in texto.lower(): return 5
        if "seis" in texto.lower(): return 6
        if "siete" in texto.lower(): return 7
        if "ocho" in texto.lower(): return 8
        if "nueve" in texto.lower(): return 9
        return None # No se reconoció un número válido
    except sr.WaitTimeoutError:
        print("No se detectó habla.")
        return None
    except sr.UnknownValueError:
        print("Speech Recognition no pudo entender el audio.")
        return None
    except sr.RequestError as e:
        print(f"No se pudo solicitar resultados del servicio de Google Speech Recognition; {e}")
        return None
    except Exception as e:
        print(f"Error inesperado durante el reconocimiento de voz: {e}")
        return None

# --- Función para mostrar el número visualmente ---
def mostrar_numero_en_ventana(numero):
    """Crea y muestra una ventana de OpenCV con el número."""
    # Crear una imagen en blanco (negra)
    ancho, alto = 600, 400
    imagen_numero = np.zeros((alto, ancho, 3), dtype=np.uint8) # Imagen negra RGB

    # Definir propiedades del texto
    texto = str(numero)
    fuente = cv2.FONT_HERSHEY_SIMPLEX
    escala_fuente = 8
    grosor_linea = 15
    color_texto = (0, 255, 255) # Amarillo brillante (BGR)

    # Calcular el tamaño del texto para centrarlo
    (ancho_texto, alto_texto), base_line = cv2.getTextSize(texto, fuente, escala_fuente, grosor_linea)
    
    # Calcular coordenadas para centrar
    x = (ancho - ancho_texto) // 2
    y = (alto + alto_texto) // 2 - base_line # Ajuste para que quede realmente centrado

    # Dibujar el número en la imagen
    cv2.putText(imagen_numero, texto, (x, y), fuente, escala_fuente, color_texto, grosor_linea, cv2.LINE_AA)

    # Mostrar la imagen en una ventana
    cv2.imshow("Adivina el Numero", imagen_numero)
    cv2.waitKey(100) # Pequeña espera para asegurar que la ventana se dibuje
    time.sleep(0.5) # Mantener la ventana un momento antes de la interacción

# --- Juego ---
def juego_adivinar_numero_visual(rondas=4):
    hablar("¡Hola! Vamos a jugar a adivinar números. Te mostraré un número del cero al nueve en pantalla y tú deberás adivinar cuál es, diciéndolo en voz alta.")
    time.sleep(1)

    puntuacion = 0

    for i in range(rondas):
        numero_a_mostrar = random.randint(0, 9)
        hablar(f"Ronda número {i+1}. ¡Aquí está el número!")
        mostrar_numero_en_ventana(numero_a_mostrar) # Muestra el número

        intento_usuario = escuchar_numero() # Escucha la respuesta del usuario

        if intento_usuario is not None and intento_usuario == numero_a_mostrar:
            hablar(f"¡Felicidades! ¡Lo has adivinado correctamente! El número era el {numero_a_mostrar}.")
            puntuacion += 1
        else:
            if intento_usuario is not None:
                hablar(f"Oh no, dijiste {intento_usuario}, pero el número correcto era el {numero_a_mostrar}.")
            else:
                hablar(f"No pude escucharte bien o no dijiste un número válido. El número era el {numero_a_mostrar}.")
            hablar("No te desanimes, ¡sigue intentándolo en la próxima ronda!")
        
        cv2.destroyAllWindows() # Cierra la ventana del número antes de la siguiente ronda
        time.sleep(1.5) # Pequeña pausa entre rondas

    hablar(f"¡Hemos terminado las {rondas} rondas! Tu puntuación final es de {puntuacion} aciertos.")
    if puntuacion == rondas:
        hablar("¡Eres un genio adivinando números visualmente!")
    elif puntuacion > rondas / 2:
        hablar("¡Muy bien! Tienes una buena habilidad para adivinar números.")
    else:
        hablar("¡Buen intento! Sigue practicando y mejorarás mucho.")
    hablar("¡Hasta la próxima!")

if __name__ == "__main__":
    try:
        juego_adivinar_numero_visual(rondas=4)
    except KeyboardInterrupt:
        hablar("Juego interrumpido. ¡Adiós!")
    finally:
        # Asegurarse de que el mezclador de pygame se cierre si está activo
        try:
            if pygame.mixer.get_init():
                pygame.mixer.quit()
        except Exception:
            pass
        cv2.destroyAllWindows() # Asegurarse de cerrar todas las ventanas de OpenCV al finalizar