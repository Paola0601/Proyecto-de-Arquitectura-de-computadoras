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

# --- Visión (detección de figuras) ---

def obtener_nombre_figura(approx, area):
    num_vertices = len(approx)

    # helper local: calcula ángulos internos en grados
    def internal_angles(pts):
        pts = pts.reshape(-1, 2).astype(float)
        n = len(pts)
        angles = []
        for i in range(n):
            prev = pts[(i - 1) % n]
            cur = pts[i]
            nxt = pts[(i + 1) % n]
            v1 = prev - cur
            v2 = nxt - cur
            n1 = np.linalg.norm(v1)
            n2 = np.linalg.norm(v2)
            if n1 < 1e-6 or n2 < 1e-6:
                angles.append(180.0)
                continue
            cosang = np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0)
            ang = np.degrees(np.arccos(cosang))
            angles.append(ang)
        return angles

    # 1. Priorizar la detección por número de vértices para figuras angulares
    if num_vertices == 3:
        return "triángulo"

    if num_vertices == 4:
        # Si tiene 4 vértices pero uno es muy obtuso o el polígono es cóncavo,
        # es probable que sea un triángulo con un vértice "extra" — tratar como triángulo.
        angles = internal_angles(approx)
        if (not cv2.isContourConvex(approx)) or any(a > 150.0 for a in angles):
            return "triángulo"

        # Si pasa las comprobaciones anteriores, distinguir cuadrado/rectángulo
        x, y, w, h = cv2.boundingRect(approx)
        aspect_ratio = float(w) / h if h != 0 else 0
        if 0.9 <= aspect_ratio <= 1.1:  # Rango estricto para cuadrados
            return "cuadrado"
        else:
            return "rectángulo"

    if num_vertices > 4:
        # Si tiene más de 4 vértices, es más probable que sea un círculo
        perimeter = cv2.arcLength(approx, True)
        if perimeter > 0:
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if circularity > 0.88:
                return "círculo"

    return "desconocida"

# helper: eliminar vértices casi colineales para no "recortar" puntas agudas
def remove_collinear_vertices(approx, angle_thresh_deg=15):
    pts = approx.reshape(-1, 2)
    if len(pts) <= 3:
        return approx.astype(np.int32)
    keep = []
    n = len(pts)
    for i in range(n):
        prev = pts[(i - 1) % n].astype(float)
        cur = pts[i].astype(float)
        nxt = pts[(i + 1) % n].astype(float)
        v1 = prev - cur
        v2 = nxt - cur
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        if n1 < 1e-6 or n2 < 1e-6:
            continue
        cosang = np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0)
        ang = np.degrees(np.arccos(cosang))
        # conservar vértices que no sean prácticamente colineales (~180°)
        if ang < 180.0 - angle_thresh_deg:
            keep.append(cur.astype(int))
    if len(keep) < 3:
        return approx.astype(np.int32)
    return np.array(keep).reshape(-1, 1, 2).astype(np.int32)

def detectar_figura_en_imagen(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # RANGO DE COLOR VERDE LIMÓN EN HSV
    # Estos valores pueden requerir ajustes finos en tu entorno específico.
    lower_green_lemon = np.array([30, 80, 80])
    upper_green_lemon = np.array([90, 255, 255])
    
    mask_green_lemon = cv2.inRange(hsv, lower_green_lemon, upper_green_lemon)
    
    # usar morfología más suave para no redondear esquinas
    kernel = np.ones((3,3), np.uint8)
    mask_green_lemon = cv2.morphologyEx(mask_green_lemon, cv2.MORPH_OPEN, kernel, iterations=1)
    mask_green_lemon = cv2.morphologyEx(mask_green_lemon, cv2.MORPH_CLOSE, kernel, iterations=1)
    
    edges = cv2.Canny(mask_green_lemon, 50, 150)
    
    debug_view = np.hstack([
        cv2.resize(mask_green_lemon, (160, 120)),
        cv2.resize(edges, (160, 120)),
        cv2.resize(cv2.bitwise_and(mask_green_lemon, edges), (160, 120))
    ])
    frame[10:130, 10:490] = cv2.cvtColor(debug_view, cv2.COLOR_GRAY2BGR)
    
    # conservar todos los puntos del contorno para no perder puntas agudas
    contours, _ = cv2.findContours(mask_green_lemon, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    
    figura_detectada = "ninguna"
    mejor_contorno = None
    max_area = 0

    if contours:
        for contour in contours:
            area = cv2.contourArea(contour)
            if 5000 < area < 200000:
                hull = cv2.convexHull(contour)
                hull_area = cv2.contourArea(hull)
                solidity = float(area) / hull_area if hull_area > 0 else 0
                
                if solidity > 0.9 and area > max_area:
                    max_area = area
                    mejor_contorno = contour

    if mejor_contorno is not None:
        # Epsilon inicial pequeño para conservar puntas
        perimeter = cv2.arcLength(mejor_contorno, True)
        epsilons = [
            max(0.003 * perimeter, 0.5),
            max(0.006 * perimeter, 1.0),
            max(0.01 * perimeter, 1.5),
            max(0.02 * perimeter, 2.5)
        ]

        # Intentar aproximaciones con epsilons crecientes y limpiar vértices colineales
        approx = None
        for e in epsilons:
            a = cv2.approxPolyDP(mejor_contorno, e, True)
            a = remove_collinear_vertices(a, angle_thresh_deg=12)
            if 3 <= len(a) <= 4:
                approx = a
                break

        # Si aún no hay una approx razonable, probar sobre el convex hull
        if approx is None:
            hull = cv2.convexHull(mejor_contorno)
            for e in epsilons:
                a = cv2.approxPolyDP(hull, e, True)
                a = remove_collinear_vertices(a, angle_thresh_deg=12)
                if 3 <= len(a) <= 4:
                    approx = a
                    break

        # Fallback: elegir la aproximación (contorno vs hull) con menos vértices
        if approx is None:
            a_cont = remove_collinear_vertices(cv2.approxPolyDP(mejor_contorno, epsilons[0], True), angle_thresh_deg=12)
            a_hull = remove_collinear_vertices(cv2.approxPolyDP(cv2.convexHull(mejor_contorno), epsilons[1], True), angle_thresh_deg=12)
            approx = a_cont if len(a_cont) <= len(a_hull) else a_hull
 
        # Filtrar contornos muy ruidosos o degenerados y dibujar resultado
        if approx is not None and len(approx) >= 3:
            figura_detectada = obtener_nombre_figura(approx, max_area)
            cv2.drawContours(frame, [approx], 0, (0, 255, 0), 2)
            M = cv2.moments(approx)
            if M.get("m00", 0) != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                h_frame, w_frame, _ = frame.shape
                cX = max(20, min(cX, w_frame - 100))
                cY = max(20, min(cY, h_frame - 50))
                cv2.putText(frame, figura_detectada, (cX - 20, cY - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                cv2.putText(frame, f"Area: {int(max_area)}", (cX - 20, cY + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                cv2.putText(frame, f"Vertices: {len(approx)}", (cX - 20, cY + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

    return figura_detectada, frame

# --- Modo: enseñar (el robot pide y el niño muestra) ---

def iniciar_modo_ensenar():
    hablar("¡Hola! Vamos a jugar a mostrar figuras. Yo te pediré una figura y tú me la mostrarás frente a la cámara.")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        hablar("No pude abrir la cámara. Revisa la conexión.")
        return

#    hablar("Recuerda mostrar solo figuras de color VERDE LIMÓN. Las figuras de otros colores no serán detectadas.")
#    hablar("Asegúrate de que las figuras sean de un verde brillante y que estén bien iluminadas.")
    figuras = ["cuadrado", "círculo", "triángulo", "rectángulo"]
    
    hablar("Solo reconozco cuatro figuras: círculo, cuadrado, triángulo y rectángulo.")
    
    for i in range(3):
        objetivo = random.choice(figuras)
        hablar(f"Por favor, muéstrame un {objetivo} de color verde limón. Tienes 15 segundos.")
        detectado = "ninguna"
        start = time.time()

        while time.time() - start < 15:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            frame = cv2.flip(frame, 1)
            detectado_actual, vis = detectar_figura_en_imagen(frame.copy())
            cv2.imshow('Enséñame la figura - presiona q para salir', vis)
            if detectado_actual.lower() == objetivo:
                detectado = detectado_actual
                cv2.waitKey(800) 
                break
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cv2.destroyAllWindows()
        if detectado.lower() == objetivo:
            hablar(f"¡Excelente! Vi el {objetivo}.")
        else:
            hablar(f"No logré ver el {objetivo}. Detecté: {detectado}.")
        time.sleep(1.5)

    cap.release()
    cv2.destroyAllWindows()
    hablar("Terminamos el modo enseñar. ¡Buen trabajo!")


if __name__ == '__main__':
    try:
        iniciar_modo_ensenar()
    except KeyboardInterrupt:
        hablar("Adiós")
    finally:
        try:
            if pygame.mixer.get_init():
                pygame.mixer.quit()
        except Exception:
            pass
        cv2.destroyAllWindows()