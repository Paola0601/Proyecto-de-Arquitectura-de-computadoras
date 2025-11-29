import cv2
try:
    import mediapipe as mp
    _MEDIAPIPE_AVAILABLE = True
except Exception as _e:
    mp = None
    _MEDIAPIPE_AVAILABLE = False
    # If mediapipe isn't available, we'll switch to debug-camera mode later
    print("⚠️ mediapipe no está instalado o falló al importarlo; el script usará '--debug-camera' automáticamente.")
import math
import serial
import time
import argparse
import sys

# Args CLI
parser = argparse.ArgumentParser(description="Face tracking con MediaPipe y salida a servos por serial")
parser.add_argument("--com", default="COM5", help="Puerto serial para Arduino (ej. COM5)")
parser.add_argument("--baud", type=int, default=115200, help="Baudios del puerto serial")
parser.add_argument("--no-serial", action="store_true", help="Deshabilitar comunicación serial (solo visual)")
parser.add_argument("--invert-x", action="store_true", help="Invertir dirección del eje X")
parser.add_argument("--invert-y", action="store_true", help="Invertir dirección del eje Y")
parser.add_argument("--scale-x", type=float, default=1.0, help="Sensibilidad eje X (1.0 por defecto)")
parser.add_argument("--scale-y", type=float, default=1.0, help="Sensibilidad eje Y (1.0 por defecto)")
parser.add_argument("--camera-index", type=int, help="Forzar índice de cámara (0,1,2,...) si lo conoces")
parser.add_argument("--deadzone", type=int, default=70, help="Zona muerta en pixeles alrededor del centro")
parser.add_argument("--max-deg", type=int, default=45, help="Máximo delta en grados desde el centro (1..90)")
parser.add_argument("--debug-camera", action="store_true", help="Mostrar solo la cámara (sin mediapipe)")
parser.add_argument("--verbose", action="store_true", help="Logs adicionales en consola")
parser.add_argument("--list-cams", action="store_true", help="Listar índices de cámaras disponibles y salir")
parser.add_argument("--print-xy", action="store_true", help="Imprimir periódicamente diff X/Y y servos en consola")
parser.add_argument("--print-every", type=int, default=5, help="Imprimir cada N frames si --print-xy está activo")
parser.add_argument("--servo-test", action="store_true", help="Probar barrido de servos sin cámara y salir")
parser.add_argument("--control", choices=["incremental", "absolute"], default="incremental",
                    help="Modo de control de servos: incremental (por defecto) o absolute")
parser.add_argument("--kp-x", type=float, default=0.2, help="Ganancia proporcional eje X (incremental)")
parser.add_argument("--kp-y", type=float, default=0.3, help="Ganancia proporcional eje Y (incremental)")
parser.add_argument("--max-step", type=float, default=4.0, help="Máximo cambio por envío (grados)")
parser.add_argument("--offset-x", type=int, default=0, help="Offset fijo en grados para X")
parser.add_argument("--offset-y", type=int, default=0, help="Offset fijo en grados para Y")
parser.add_argument("--no-flip", action="store_true", help="No espejar imagen (por defecto se espeja)")
args, _ = parser.parse_known_args()

# Configuración del puerto serial para Arduino (opcional)
arduino = None
if not args.no_serial:
    try:
        arduino = serial.Serial(args.com, args.baud, timeout=1)
        time.sleep(2)  # Esperar a que Arduino se inicialice
        print(f"✅ Conexión establecida con Arduino en {args.com}")
        # Centrar al inicio
        try:
            arduino.write(b"X:90,Y:90\n")
        except Exception:
            pass
    except Exception as e:
        print(f"❌ No se pudo abrir {args.com}: {e}. Continuando sin serial. Usa --no-serial para ocultar este aviso.")
        arduino = None

mp_face_detection = mp.solutions.face_detection if _MEDIAPIPE_AVAILABLE else None

# ------------------------
# Utilidades de cámara
# ------------------------
def _open_camera_with_fallback(indices=(0, 1, 2)):
    """Abrir cámara con backend DirectShow probando varios índices.
    Devuelve el objeto VideoCapture abierto o None si falla.
    """
    for idx in indices:
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        configure_camera(cap)
        ok, _ = cap.read()
        if ok:
            if args.verbose:
                print(f"📷 Cámara abierta en índice {idx}")
            return cap
        cap.release()
    print("❌ No se pudo abrir ninguna cámara. Conecta una webcam o libera el dispositivo en otra app.")
    return None

def _list_cameras(max_index=10):
    print("📋 Buscando cámaras disponibles (DirectShow)...")
    found = False
    for idx in range(max_index):
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        ok, frame = cap.read()
        if ok and frame is not None:
            h, w = frame.shape[:2]
            print(f"  - Índice {idx}: OK ({w}x{h})")
            found = True
        elif args.verbose:
            print(f"  - Índice {idx}: no disponible")
        cap.release()
    if not found:
        print("❌ No se detectaron cámaras. Verifica permisos o cierra apps que la usen.")
    sys.exit(0)

def configure_camera(cap):
    """Intentar configurar la cámara para una imagen más nítida.

    - Establece resolución 1280x720
    - Activa autoenfoque si está disponible
    - Si falla, intenta un enfoque fijo moderado
    Nota: no todas las webcams soportan estas propiedades.
    """
    import time as _t

    def _set(prop_name, value):
        prop = getattr(cv2, prop_name, None)
        if prop is not None:
            try:
                cap.set(prop, value)
            except Exception:
                pass

    # Resolución/fps razonables
    _set('CAP_PROP_FRAME_WIDTH', 1280)
    _set('CAP_PROP_FRAME_HEIGHT', 720)
    _set('CAP_PROP_FPS', 30)

    # Intentar autoenfoque
    if hasattr(cv2, 'CAP_PROP_AUTOFOCUS'):
        _set('CAP_PROP_AUTOFOCUS', 1)  # 1 = auto
        _t.sleep(0.8)  # dar tiempo a que enfoque

    # Si la imagen sigue borrosa y la cámara soporta enfoque manual, probar un valor medio
    # Algunos drivers requieren desactivar autoexposición para tocar foco; lo evitamos por compatibilidad.
    if hasattr(cv2, 'CAP_PROP_FOCUS'):
        # Intenta mantener auto; si no mejora, podrías forzar manual con:
        # _set('CAP_PROP_AUTOFOCUS', 0); _set('CAP_PROP_FOCUS', 30)
        pass

# Abrir cámara con fallback y configurar (seguro si no soporta propiedades)
if args.list_cams:
    _list_cameras(10)

# Modo prueba de servos (sin cámara)
if args.servo_test:
    if arduino is None:
        print("❌ Para --servo-test necesitas --com correcto o quitar --no-serial.")
        sys.exit(1)
    print("🔧 Barrido de servos: 90→0→180→90 (X e Y)")
    seq = [90, 0, 180, 90]
    for val in seq:
        msg = f"X:{val},Y:{val}\n".encode()
        try:
            arduino.write(msg)
            print(f"📤 {msg.decode().strip()}")
        except Exception as e:
            print(f"❌ Error enviando: {e}")
            break
        time.sleep(0.8)
    print("✅ Prueba finalizada")
    if arduino and arduino.is_open:
        arduino.close()
    sys.exit(0)
if args.camera_index is not None:
    cap = cv2.VideoCapture(args.camera_index, cv2.CAP_DSHOW)
    configure_camera(cap)
    ok, _ = cap.read()
    if ok:
        if args.verbose:
            print(f"📷 Cámara abierta en índice {args.camera_index}")
    else:
        cap.release()
        cap = _open_camera_with_fallback()
else:
    cap = _open_camera_with_fallback()

# Parámetros de tracking/servo
SMOOTHING_ALPHA = 0.3  # 0..1 (mayor = responde más rápido) - REDUCIDO para más estabilidad
SEND_INTERVAL_SEC = 0.05  # mínimo entre envíos al Arduino - AUMENTADO para menos frecuencia
LOST_FRAMES_THRESHOLD = 60  # frames sin detección antes de probar otro modelo

model_selection = 0  # 0 = rostro cercano (hasta ~2m), 1 = rango completo
last_send_time = 0.0
lost_frames = 0
servo_x_smooth, servo_y_smooth = 90, 90

if cap is not None:
    # Modo debug: solo mostrar la cámara para verificar que abre correctamente
    if args.debug_camera:
        t_prev_dbg = time.time()
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                if args.verbose:
                    print("⚠️ No se pudo leer frame de la cámara")
                break
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            cx, cy = w // 2, h // 2
            cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)
            t_now_dbg = time.time()
            fps_dbg = 1.0 / max(1e-6, (t_now_dbg - t_prev_dbg))
            t_prev_dbg = t_now_dbg
            cv2.putText(frame, f"DEBUG CAM | FPS: {fps_dbg:.1f}", (10, h - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.imshow("Debug Camera", frame)
            k = cv2.waitKey(1) & 0xFF
            if k in (27, ord('q')):
                break
        cap.release()
        cv2.destroyAllWindows()
        sys.exit(0)

    face_detection = mp_face_detection.FaceDetection(model_selection=model_selection, min_detection_confidence=0.3)
    try:
        t_prev = time.time()
        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                # Intentar reabrir en caliente si se perdió la cámara
                cap.release()
                cap = _open_camera_with_fallback()
                if cap is None:
                    break
                continue

            # Espejo para que el movimiento sea más natural (a menos que se desactive)
            if not args.no_flip:
                frame = cv2.flip(frame, 1)

            height, width, _ = frame.shape
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_detection.process(frame_rgb)

            # Centro del frame
            center_x, center_y = width // 2, height // 2
            cv2.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)

            detected = False
            if results.detections:
                detected = True
                lost_frames = 0
                for detection in results.detections:
                    bboxC = detection.location_data.relative_bounding_box
                    x = int(bboxC.xmin * width)
                    y = int(bboxC.ymin * height)
                    w_box = int(bboxC.width * width)
                    h_box = int(bboxC.height * height)

                    # 🔳 Dibujar el cuadro
                    cv2.rectangle(frame, (x, y), (x + w_box, y + h_box), (0, 255, 0), 2)

                    # Coordenadas de los 6 puntos
                    keypoints = []
                    for i, keypoint in enumerate(detection.location_data.relative_keypoints):
                        px = int(keypoint.x * width)
                        py = int(keypoint.y * height)
                        keypoints.append((px, py))
                        cv2.circle(frame, (px, py), 6, (0, 0, 255), -1)
                        cv2.putText(frame, str(i), (px + 5, py - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                    # Calcular distancias si hay los 6 puntos
                    if len(keypoints) == 6:
                        # Distancia entre ojos
                        dist_eyes = math.dist(keypoints[0], keypoints[1])

                        # Distancia entre orejas
                        dist_ears = math.dist(keypoints[4], keypoints[5])

                        # Punto medio de los ojos (centro horizontal del rostro)
                        mid_eye_x = int((keypoints[0][0] + keypoints[1][0]) / 2)
                        mid_eye_y = int((keypoints[0][1] + keypoints[1][1]) / 2)

                        # Movimiento respecto al centro de la cámara
                        diff_x = mid_eye_x - center_x
                        diff_y = keypoints[2][1] - center_y  # nariz en vertical
                        diff_z = dist_ears  # estimación de profundidad

                        # Convertir diferencias a ángulos para servomotores (0-180°)
                        # Ejes y sensibilidad (invertibles) 
                        mult_x = -1.0 if args.invert_x else 1.0
                        mult_y = -1.0 if args.invert_y else 1.0
                        # Deadzone en pixeles
                        dx = diff_x
                        dy = diff_y
                        if abs(dx) < args.deadzone:
                            dx = 0
                        if abs(dy) < args.deadzone:
                            dy = 0

                        # Escalado a grados con límites
                        max_deg = max(1, min(90, args.max_deg))
                        if args.control == "absolute":
                            raw_x = (dx / (width / 2)) * max_deg * args.scale_x * mult_x
                            raw_y = (-dy / (height / 2)) * max_deg * args.scale_y * mult_y
                            servo_x = int(90 + raw_x + args.offset_x)
                            servo_y = int(90 + raw_y + args.offset_y)
                            servo_x = max(0, min(180, servo_x))
                            servo_y = max(0, min(180, servo_y))
                        else:
                            # Control incremental: mueve la cámara paso a paso hacia el centro
                            err_x_deg = (dx / (width / 2)) * max_deg * args.scale_x * mult_x
                            err_y_deg = (-dy / (height / 2)) * max_deg * args.scale_y * mult_y
                            step_x = max(-args.max_step, min(args.max_step, args.kp_x * err_x_deg))
                            step_y = max(-args.max_step, min(args.max_step, args.kp_y * err_y_deg))
                            servo_x = int(servo_x_smooth + step_x + args.offset_x)
                            servo_y = int(servo_y_smooth + step_y + args.offset_y)
                            servo_x = max(0, min(180, servo_x))
                            servo_y = max(0, min(180, servo_y))

                        # Suavizado para movimientos más estables
                        servo_x_smooth = int((1 - SMOOTHING_ALPHA) * servo_x_smooth + SMOOTHING_ALPHA * servo_x)
                        servo_y_smooth = int((1 - SMOOTHING_ALPHA) * servo_y_smooth + SMOOTHING_ALPHA * servo_y)

                        # Mostrar en pantalla
                        cv2.putText(frame, f"X:{diff_x} Y:{diff_y} Z:{round(diff_z,1)}", (30, 50),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                        cv2.putText(frame, f"Servo X:{servo_x_smooth} Y:{servo_y_smooth}", (30, 80),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
                        if arduino is None:
                            cv2.putText(frame, "Serial OFF", (30, 110),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                        # 🔹 Determinar cercanía (profundidad)
                        text = "Cerca" if dist_ears > 300 else "Lejos" if dist_ears < 150 else "Normal"
                        cv2.putText(frame, f"Distancia: {text}", (x, y - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            else:
                lost_frames += 1
                # Si perdemos la cara por un rato, alternar modelo (cerca/lejos) y reconstruir
                if lost_frames == LOST_FRAMES_THRESHOLD:
                    model_selection = 1 - model_selection
                    print(f"🔄 Cambiando modelo de FaceDetection a model_selection={model_selection}")
                    try:
                        face_detection.close()
                    except Exception:
                        pass
                    face_detection = mp_face_detection.FaceDetection(
                        model_selection=model_selection, min_detection_confidence=0.3
                    )

            # HUD: FPS y estado
            t_now = time.time()
            fps = 1.0 / max(1e-6, (t_now - t_prev))
            t_prev = t_now
            status = "Detectado" if detected else "Buscando..."
            ctrl = "INC" if args.control == "incremental" else "ABS"
            cv2.putText(frame, f"{status} | FPS: {fps:.1f} | Modelo: {model_selection} | CTRL: {ctrl}", (10, height - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # Impresión periódica en consola
            frame_count += 1
            if args.print_xy and (frame_count % max(1, args.print_every) == 0):
                if 'diff_x' in locals() and 'diff_y' in locals():
                    try:
                        print(f"XY(px): {diff_x:>4}, {diff_y:>4} | Servo(deg): {servo_x_smooth:>3}, {servo_y_smooth:>3} | {status} @ {fps:.1f} FPS")
                    except Exception:
                        pass

            # ⚡ ENVÍO CONTINUO AL ARDUINO - esto es lo que mueve los servos
            if arduino is not None:
                t_now_send = time.time()
                if (t_now_send - last_send_time) >= SEND_INTERVAL_SEC:
                    try:
                        msg = f"X:{int(servo_x_smooth)},Y:{int(servo_y_smooth)}\n".encode()
                        arduino.write(msg)
                        if args.verbose:
                            print(f"📤 {msg.decode().strip()}")
                    except Exception as e:
                        if args.verbose:
                            print(f"⚠️ Error enviando serial: {e}")
                    last_send_time = t_now_send

            cv2.imshow("Face Tracking con Arduino", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord('q')):
                break
            elif key == ord('0'):
                model_selection = 0
                try:
                    face_detection.close()
                except Exception:
                    pass
                face_detection = mp_face_detection.FaceDetection(
                    model_selection=model_selection, min_detection_confidence=0.3
                )
            elif key == ord('1'):
                model_selection = 1
                try:
                    face_detection.close()
                except Exception:
                    pass
                face_detection = mp_face_detection.FaceDetection(
                    model_selection=model_selection, min_detection_confidence=0.3
                )
    except KeyboardInterrupt:
        if args.verbose:
            print("\n⏹ Interrumpido por el usuario")
    finally:
        # Limpieza de recursos
        try:
            if face_detection is not None:
                face_detection.close()
        except Exception:
            pass
        if cap is not None:
            cap.release()
        if arduino and arduino.is_open:
            try:
                arduino.close()
                print("🔌 Conexión con Arduino cerrada")
            except Exception:
                pass
        cv2.destroyAllWindows()

# Limpieza adicional por si no se entró al bloque principal
if cap is not None:
    try:
        cap.release()
    except Exception:
        pass
if arduino and arduino.is_open:
    try:
        arduino.close()
    except Exception:
        pass
try:
    cv2.destroyAllWindows()
except Exception:
    pass