
# Robot-Educativo — Setup y ejecución

Este README explica cómo crear y activar un entorno virtual en Windows (cmd.exe), instalar las dependencias desde `requirements.txt` y ejecutar el menú principal `main.py`.

## Clonar el repositorio

Si todavía no tienes el código en tu máquina, clona el repositorio desde GitHub. Ejemplo recomendado (clonar dentro de `Downloads\Robotcito`):

```cmd
cd %USERPROFILE%\Downloads
mkdir Robotcito  # opcional, crea la carpeta si no existe
cd Robotcito
git clone https://github.com/Paola0601/Robot-Educativo.git
cd Robot-Educativo
```

Si no dispones de `git`, puedes descargar el ZIP desde la página del repositorio en GitHub y extraerlo en la carpeta que prefieras. Luego navega a la carpeta del proyecto (ej. `%USERPROFILE%\Downloads\Robotcito\Robot-Educativo`).

## 1) Abrir cmd y situarse en el proyecto

Abre una ventana de `cmd.exe` y cambia al directorio del proyecto. Usa una ruta relativa o la ruta donde tengas el proyecto en tu equipo. Ejemplos:

Si ya estás en la carpeta padre del proyecto:

```cmd
cd Robot-Educativo
```

Si lo descargaste siguiendo el ejemplo de clonación anterior, usa:

```cmd
cd %USERPROFILE%\Downloads\Robotcito\Robot-Educativo
```

O usa la ruta completa a tu carpeta (sustituye `<ruta>` por la tuya):

```cmd
cd C:\ruta\al\proyecto\Robot-Educativo
```

## 2) Crear el entorno virtual

Crear un entorno virtual llamado `EntornoVirtual` (puedes cambiar el nombre):

```cmd
python -m venv EntornoVirtual
```

## 3) Activar el entorno virtual (cmd.exe)

Activa el entorno con:

```cmd
EntornoVirtual\Scripts\activate
```

Deberías ver el prompt cambiado, por ejemplo `(EntornoVirtual) C:\Users\Nahomy\...>`.

## 4) Actualizar pip (recomendado)

```cmd
python -m pip install --upgrade pip setuptools wheel
```

## 5) Instalar dependencias

Instala las dependencias listadas en `requirements.txt`:

```cmd
python -m pip install -r requirements.txt
```

Notas:
- Si `PyAudio` falla al instalar, instala una rueda precompilada para Windows o usa `pipwin install pyaudio` (instala `pipwin` primero con `pip install pipwin`).
- Para `tensorflow` en Windows puede que necesites una versión compatible con tu Python/CPU; si falla, dímela versión de Python (`python --version`) y te ayudo a elegir la wheel adecuada.
- Si prefieres OpenCV sin interfaz gráfica en servidores, cambia `opencv-python` por `opencv-python-headless` en `requirements.txt`.

## 6) Ejecutar el menú principal

Con el entorno activado, ejecuta:

```cmd
python main.py
```

Uso del menú:
- Escribe el número de la opción y pulsa Enter para ejecutar un script.
- Pulsa `Ctrl+C` mientras se ejecuta una opción para volver al menú.
- Escribe `q` para salir del programa.

## 7) Problemas comunes

- FileNotFoundError por `colors.csv`: Asegúrate de ejecutar `main.py` desde la carpeta del proyecto. Los scripts usan rutas relativas a su ubicación; `color/color.py` ya fue actualizado para buscar `colors.csv` en su carpeta.
- Cámara ocupada: cierra otras apps que usen la cámara o prueba otro índice de cámara (0, 1, ...).
- Errores de importación: confirma que tienes activado el entorno virtual y que las dependencias se instalaron correctamente.

## 8) Si quieres que lo automatice

Puedo añadir un `setup.bat` para automatizar la creación del entorno y la instalación de dependencias, o puedo fijar versiones exactas para `tensorflow` y `mediapipe` si lo prefieres.

---

Si quieres, ejecuto ahora un `pip install -r requirements.txt` en tu `EntornoVirtual` (dímelo) o preparo scripts de ayuda adicionales.

