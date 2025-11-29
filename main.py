import subprocess
import sys
import os

ROOT = os.path.dirname(__file__)

SCRIPTS = {
	'1': ('Mostrar Color', os.path.join(ROOT, 'color', 'mostrarColor.py')),
	'2': ('Adivinar Color', os.path.join(ROOT, 'color', 'adivinarColor.py')),
	'3': ('Texto a Audio (mostrar texto como audio)', os.path.join(ROOT, 'deTextoaAudio', 'detextoaaudio.py')),
	'4': ('Audio a Texto (transcribir micrófono)', os.path.join(ROOT, 'deAudioaTexto', 'deaudioatexto.py')),
	'5': ('Mostrar figuras (muestra las figuras a la cámara)', os.path.join(ROOT, 'figurasGeometricas', 'ensenar_figuras.py')),
	'6': ('Adivinar figuras (di el nombre de la figura)', os.path.join(ROOT, 'figurasGeometricas', 'adivinar_figuras.py')),
	'7': ('Mostrar número', os.path.join(ROOT, 'numeros', 'detectarNumeros.py')),
	'8': ('Adivinar número', os.path.join(ROOT, 'numeros', 'adivinarNumeros.py')),
}


def run_script(path):
	if not os.path.isfile(path):
		print(f"No se encontró el script: {path}")
		return
	print(f"Lanzando: {path} (pulsa Ctrl+C para volver al menú)\n")
	try:
		subprocess.run([sys.executable, path], check=False)
	except KeyboardInterrupt:
		print('\nInterrumpido por el usuario. Volviendo al menú...')


def print_menu():
	print('\n=== Menú Robot Educativo ===')
	for k, (desc, path) in SCRIPTS.items():
		print(f"{k}. {desc}")
	print('q. Salir')


def main():
	while True:
		print_menu()
		choice = input('Selecciona una opción: ').strip().lower()
		if choice == 'q' or choice == 'quit' or choice == 'salir':
			print('Saliendo. ¡Hasta pronto!')
			break
		if choice in SCRIPTS:
			_, path = SCRIPTS[choice]
			run_script(path)
		else:
			print('Opción no válida. Intenta de nuevo.')


if __name__ == '__main__':
	main()

