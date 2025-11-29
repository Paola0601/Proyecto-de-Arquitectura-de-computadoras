import time
import argparse
import serial

parser = argparse.ArgumentParser(description="Prueba simple de envío serial X/Y al Arduino")
parser.add_argument("--com", default="COM5", help="Puerto serial, ej. COM5")
parser.add_argument("--baud", type=int, default=115200, help="Baudios, ej. 115200")
args = parser.parse_args()

print(f"Abriendo {args.com} @ {args.baud} ...")
ser = serial.Serial(args.com, args.baud, timeout=1)
time.sleep(2)

seq = [
    (90, 90),
    (0, 0),
    (180, 180),
    (90, 90),
    (120, 90),
    (60, 90),
    (90, 120),
    (90, 60),
    (90, 90),
]

for x, y in seq:
    msg = f"X:{x},Y:{y}\n".encode()
    ser.write(msg)
    print(f"📤 {msg.decode().strip()}")
    time.sleep(0.8)

ser.close()
print("✅ Prueba serial finalizada")
