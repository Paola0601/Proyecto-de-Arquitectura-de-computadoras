import speech_recognition as sr

def escuchar_y_escribir():
    """
    Escucha el audio del micrófono y lo transcribe a texto,
    luego lo imprime en la consola.
    """
    r = sr.Recognizer() # Crea un objeto Recognizer

    print("¡Hola! Estoy escuchando... Di algo.")
    print("Para salir, puedes presionar Ctrl+C en la consola.")

    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source) # Ajusta dinámicamente el umbral de energía para la sensibilidad del ruido ambiental
        print("Calibrando ruido ambiental. Por favor, mantente en silencio por un momento...")
        r.pause_threshold = 0.8 # Espera 0.8 segundos de silencio antes de considerar que la frase ha terminado
        print("Listo para escuchar. ¡Di algo!")

        while True:
            try:
                audio = r.listen(source) # Escucha el audio del micrófono

                # Intenta reconocer el audio usando el servicio de Google
                texto = r.recognize_google(audio, language="es-ES")
                print(f"Tú dijiste: '{texto}'")

            except sr.UnknownValueError:
                print("No pude entender el audio. ¿Podrías repetirlo?")
            except sr.RequestError as e:
                print(f"No se pudo solicitar los resultados del servicio de reconocimiento de voz; {e}")
            except KeyboardInterrupt:
                print("\nPrograma terminado por el usuario.")
                break
            except Exception as e:
                print(f"Ocurrió un error inesperado: {e}")

# Llama a la función para iniciar el programa
if __name__ == "__main__":
    escuchar_y_escribir()
