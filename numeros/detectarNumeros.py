import cv2
import numpy as np
import tensorflow as tf
from gtts import gTTS
import pygame
import time
import random
import os

# Cargar el modelo pre-entrenado
try:
    model = tf.keras.models.load_model('mnist_cnn_model.h5')
except Exception as e:
    print(f"Error al cargar el modelo: {e}")
    print("Asegúrate de haber entrenado y guardado el modelo 'mnist_cnn_model.h5' o de que esté en la ruta correcta.")
    exit()

# --- Voz (gTTS + pygame) ---
def hablar(texto):
    """Genera y reproduce un audio corto con gTTS (es)."""
    print(f"Robot dice: {texto}")
    try:
        fname = "tts_tmp_numero.mp3"
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
        print("Error audio:", e)

# Inicializar la cámara
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: No se pudo abrir la cámara.")
    exit()

print("Presiona 'q' para salir.")

# Definir el rango de color verde limón en HSV
# Estos valores están bien como punto de partida. AJÚSTALOS con el script de trackbars
# para que la máscara (cv2.imshow('Mask', mask)) sea lo más limpia posible para tu "6".
lower_green_lemon = np.array([35, 100, 100])
upper_green_lemon = np.array([85, 255, 255])

def detect_digit_from_frame(frame):
    """Extrae la ROI por color, procesa y devuelve (digit, confidence, vis_frame) o (None,0,frame)."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_green_lemon, upper_green_lemon)
    kernel_m = np.ones((3,3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_m, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_m, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, 0.0, frame, mask

    plausible_contours = []
    for contour in contours:
        area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)
        if 1000 < area < 150000:
            aspect_ratio = float(w) / h if h>0 else 0
            if 0.6 < aspect_ratio < 1.3:
                plausible_contours.append((area, contour, (x, y, w, h)))

    if not plausible_contours:
        return None, 0.0, frame, mask

    plausible_contours.sort(key=lambda x: x[0], reverse=True)
    _, _, (x, y, w, h) = plausible_contours[0]
    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    roi = mask[y:y+h, x:x+w]
    if roi.size == 0 or np.max(roi) == 0:
        return None, 0.0, frame, mask

    # preparar ROI para el modelo (centrado/pad simple, manteniendo tu pipeline)
    target_size = 28
    padding = 4
    max_dim = max(roi.shape[0], roi.shape[1])
    if max_dim == 0:
        return None, 0.0, frame, mask
    scale_factor = min((target_size - 2 * padding) / max_dim, 1.0)
    resized_roi_w = int(roi.shape[1] * scale_factor)
    resized_roi_h = int(roi.shape[0] * scale_factor)
    if resized_roi_w == 0 or resized_roi_h == 0:
        return None, 0.0, frame, mask
    resized_roi = cv2.resize(roi, (resized_roi_w, resized_roi_h), interpolation=cv2.INTER_AREA)
    final_roi = np.zeros((target_size, target_size), dtype=np.uint8)
    start_x = (target_size - resized_roi_w) // 2
    start_y = (target_size - resized_roi_h) // 2
    final_roi[start_y:start_y + resized_roi_h, start_x:start_x + resized_roi_w] = resized_roi
    _, final_roi = cv2.threshold(final_roi, 127, 255, cv2.THRESH_BINARY)
    inp = final_roi.astype('float32') / 255.0
    inp = np.expand_dims(inp, axis=-1)
    inp = np.expand_dims(inp, axis=0)
    preds = model.predict(inp, verbose=0)
    digit = int(np.argmax(preds))
    confidence = float(np.max(preds))
    cv2.putText(frame, f"{digit} ({confidence*100:.1f}%)", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    return digit, confidence, frame, mask

# --- Sesión interactiva solicitando número y evaluando en 15s ---
def interactive_session(rounds=5, timeout_sec=15, accept_conf=0.6):
    hablar("Vamos a jugar. Te diré un número y tendrás quince segundos para mostrarlo en color verde.")
    time.sleep(0.8)
    for r in range(rounds):
        objetivo = random.randint(0,9)
        hablar(f"Ronda número {r+1}. Muéstrame el número {objetivo}. Tienes {timeout_sec} segundos. ¡Adelante!")
        start = time.time()
        best_pred = None
        best_conf = 0.0
        while time.time() - start < timeout_sec:
            ret, frame = cap.read()
            if not ret:
                continue
            frame = cv2.flip(frame, 1)
            pred, conf, vis, mask = detect_digit_from_frame(frame)
            if pred is not None and conf > best_conf:
                best_conf = conf
                best_pred = pred
            # mostrar cuenta regresiva
            secs_left = int(timeout_sec - (time.time() - start))
            cv2.putText(vis, f"Objetivo: {objetivo}  Tiempo: {secs_left}s", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,0), 2)
            cv2.imshow('Mask', mask)
            cv2.imshow('Detector interactivo', vis)
            if pred == objetivo and conf >= accept_conf:
                hablar("¡Bien hecho! Reconocí correctamente tu número.")
                break
            if cv2.waitKey(1) & 0xFF == ord('q'):
                hablar("Saliendo.")
                return
        else:
            # Se ejecuta si no se hizo break (tiempo agotado)
            if best_pred == objetivo and best_conf >= accept_conf:
                hablar("¡Bien hecho! Reconocí correctamente tu número.")
            else:
                if best_pred is not None:
                    hablar(f"No lo reconocí bien. Vi un {best_pred} con {int(best_conf*100)}% de confianza. Sigue intentando.")
                else:
                    hablar("No pude ver un número. Intenta acercarlo o mejora la iluminación.")
        time.sleep(1.0)
    hablar("Hemos terminado las rondas. ¡Buen trabajo!")
 
# ejecutar la sesión interactiva (puedes cambiar a un bucle con varias rondas si quieres)
try:
    interactive_session(rounds=5, timeout_sec=15, accept_conf=0.6)
except KeyboardInterrupt:
    hablar("Adiós")
finally:
    cap.release()
    cv2.destroyAllWindows()
    try:
        if pygame.mixer.get_init():
            pygame.mixer.quit()
    except Exception:
        pass