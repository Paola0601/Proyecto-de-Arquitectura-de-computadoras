import cv2
import numpy as np
import time

def clasificar_color(r, g, b):
    """
    Clasifica un color RGB en una de las categorías predefinidas,
    con mejora específica para blanco y azul usando HSV,
    y umbrales de valor/saturación más neutrales para detectar colores oscuros.
    """
    color_bgr = np.uint8([[[b, g, r]]])
    color_hsv = cv2.cvtColor(color_bgr, cv2.COLOR_BGR2HSV)
    h, s, v = color_hsv[0][0]

    # --- Filtro de Saturación Mínima (para colores que no son blanco/negro) ---
    # Para que un color sea clasificado en las categorías de Hue,
    # debe tener una saturación mínima razonable para no ser un gris.
    # El valor (V) ya no tiene un filtro mínimo tan estricto aquí, permitiendo colores oscuros.
    min_saturacion_para_color = 50 # Ajusta este valor. 50 permite colores un poco pastel/apagados.
                                    # Si lo pones muy bajo, grises con un tinte podrían clasificarse.
    if s < min_saturacion_para_color:
        return "otro color"

    # --- Reglas basadas en HSV para los colores restantes (ahora incluyendo tonos oscuros si tienen saturación) ---

    # --- AZUL (rangos HSV más precisos) ---
    if h >= 100 and h <= 140:
        return "azul"
    
    # Rojo: Dos rangos de H
    if (h >= 0 and h <= 10) or (h >= 165 and h <= 179):
        return "rojo"
    
    # Amarillo:
    if h >= 20 and h <= 40:
        return "amarillo"
        
    # Morado:
    if h >= 140 and h <= 165:
        return "morado"
    
    # Naranja:
    if h >= 10 and h <= 20:
        return "naranja"
    
    # Celeste: ligeramente diferente del azul, más cerca del cian
    if h >= 80 and h <= 100:
        return "celeste"
        
    # Verde:
    if h >= 40 and h <= 80:
        return "verde"


    # --- Fallback a distancia euclidiana RGB ---
    colores_referencia_rgb = {
        "rojo": (255, 0, 0),
        "azul": (0, 0, 255),
        "amarillo": (255, 255, 0),
        "morado": (128, 0, 128),
        "naranja": (255, 165, 0),
        "celeste": (0, 191, 255),
        "verde": (0, 255, 0),
    }

    min_distancia = float('inf')
    nombre_color_cercano = "otro color"

    for nombre, (cr, cg, cb) in colores_referencia_rgb.items():
        distancia = np.sqrt((r - cr)**2 + (g - cg)**2 + (b - cb)**2)
        if distancia < min_distancia:
            min_distancia = distancia
            nombre_color_cercano = nombre

    umbral_distancia = 60 # Sigue siendo estricto para el fallback
    if min_distancia < umbral_distancia:
        return nombre_color_cercano
    else:
        return "otro color"


def main():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara. Asegúrate de que no esté en uso y de que los drivers estén instalados.")
        return

    # --- Intentar DESACTIVAR el auto-exposición de la cámara ---
    # Esto puede no funcionar en todas las cámaras o sistemas operativos.
    # Consulta la documentación de OpenCV o prueba estos CAP_PROP.
    # Los valores exactos para el modo manual de exposición y brillo pueden variar.
    try:
        # Desactivar auto-exposición
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # 1 para MANUAL, 3 para AUTO. Algunos usan 0.25 para manual.
        # cap.set(cv2.CAP_PROP_EXPOSURE, 100) # Establecer un valor de exposición fijo (ajusta este valor)

        # Desactivar auto-brillo (si la cámara lo soporta y no es parte de auto-exposición)
        # cap.set(cv2.CAP_PROP_AUTO_BRIGHTNESS, 0) # 0 para manual, 1 para auto.
        # cap.set(cv2.CAP_PROP_BRIGHTNESS, 128) # Establecer un valor de brillo fijo (0-255, 128 es neutral)

        print("Intentando desactivar auto-exposición y establecer brillo neutral en la cámara...")
    except Exception as e:
        print(f"No se pudo configurar la cámara (propiedades no soportadas o error): {e}")


    ancho_frame = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    alto_frame = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Resolución de la cámara: {ancho_frame}x{alto_frame}")

    tamaño_cuadrado = 50
    grosor_linea = 2

    x_centro = ancho_frame // 2
    y_centro = alto_frame // 2

    x1_cuadrado = x_centro - (tamaño_cuadrado // 2)
    y1_cuadrado = y_centro - (tamaño_cuadrado // 2)
    x2_cuadrado = x_centro + (tamaño_cuadrado // 2)
    y2_cuadrado = y_centro + (tamaño_cuadrado // 2)

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Error: No se pudo capturar el frame. Saliendo...")
            break

        roi = frame[y1_cuadrado:y2_cuadrado, y1_cuadrado:y2_cuadrado] # Corregido: antes estaba (y1:y2, y1:y2)

        if roi.size == 0:
            print("Advertencia: La ROI está vacía. Ajusta las coordenadas del cuadrado o el tamaño.")
            continue

        color_bgr_promedio = cv2.mean(roi)[:3]
        b, g, r = int(color_bgr_promedio[0]), int(color_bgr_promedio[1]), int(color_bgr_promedio[2])
        color_rgb = (r, g, b)

        color_clasificado = clasificar_color(r, g, b)

        cv2.rectangle(frame, (x1_cuadrado, y1_cuadrado), (x2_cuadrado, y2_cuadrado), (255, 0, 0), grosor_linea)

        texto_color_rgb = f"RGB: ({r}, {g}, {b})"
        texto_color_clasificado = f"Color: {color_clasificado}"

        cv2.putText(frame, texto_color_rgb, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, texto_color_clasificado, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow('Detector de Color en Camara', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()