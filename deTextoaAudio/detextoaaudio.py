from gtts import gTTS
import os
import pygame

def texto_a_audio():
    """
    Función que pide al usuario que escriba algo,
    convierte ese texto a audio y lo reproduce usando pygame.
    """
    print("¡Hola! Escribe algo y yo lo diré en voz alta. Escribe 'salir' para terminar.")

    try:
        pygame.mixer.init()
    except pygame.error as e:
        print(f"Error al inicializar pygame mixer: {e}")
        print("Asegúrate de tener un dispositivo de audio funcionando.")
        return

    # Ruta y nombre del archivo de audio temporal
    nombre_archivo_audio = "respuesta_robot.mp3"

    while True:
        texto_usuario = input("Tú (escribe para que el robot hable): ")

        if texto_usuario.lower() == 'salir':
            print("¡Adiós! Gracias por interactuar.")
            break

        if not texto_usuario.strip():
            print("Por favor, escribe algo para que el robot lo diga.")
            continue

        try:
            # Genera el audio y lo guarda
            tts = gTTS(text=texto_usuario, lang='es', slow=False)
            tts.save(nombre_archivo_audio)

            print(f"Robot (diciendo): '{texto_usuario}'")

            # Carga y reproduce el archivo de audio con pygame
            pygame.mixer.music.load(nombre_archivo_audio)
            pygame.mixer.music.play()

            # Espera a que el audio termine de reproducirse
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            # !!! SOLUCIÓN AL WinError 32 !!!
            # Descarga la música del mezclador para liberar el archivo
            pygame.mixer.music.unload()

            # Ahora podemos eliminar el archivo de forma segura
            os.remove(nombre_archivo_audio)

        except Exception as e:
            print(f"Ocurrió un error al intentar convertir a voz o reproducir: {e}")
            print("Asegúrate de tener conexión a internet.")

    pygame.mixer.quit()

if __name__ == "__main__":
    texto_a_audio()
