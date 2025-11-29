# Proyecto Arduino Face Tracking con PlatformIO

Este proyecto controla servomotores para hacer seguimiento facial usando comandos serial desde Python.

## Configuración

1. Abre este proyecto en VS Code con PlatformIO instalado
2. Edita `platformio.ini`:
   - Cambia `board` si no usas Arduino Uno (mega, nano, etc.)
   - Cambia `upload_port` y `monitor_port` según tu puerto COM
3. Conecta tu Arduino
4. Presiona el botón "Upload" (→) en la barra inferior de PlatformIO

## Estructura

- `src/main.cpp` - Código principal del Arduino
- `platformio.ini` - Configuración del proyecto

## Comandos PlatformIO

- **Upload (subir código)**: Botón → en la barra inferior, o `Ctrl+Alt+U`
- **Monitor Serial**: Botón 🔌 en la barra inferior, o `Ctrl+Alt+S`
- **Build (compilar)**: Botón ✓ en la barra inferior, o `Ctrl+Alt+B`

## Comunicación Serial

- Baudios: 115200
- Formato de entrada: `X:90,Y:85\n`
- Los servos deben estar en pines 9 (X) y 10 (Y)
