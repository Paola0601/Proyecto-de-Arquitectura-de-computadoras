#include <Servo.h>

// Crear dos objetos Servo
Servo servo1;
Servo servo2;

// Definir los pines de los servos
const int pinServo1 = 14;
const int pinServo2 = 15;

void setup() {
  // Iniciar comunicación serial
  Serial.begin(115200);
  Serial.println("Ingresa el angulo para el servo 1 (0-180):");

  // Adjuntar los servos a sus pines
  servo1.attach(pinServo1);
  servo2.attach(pinServo2);
}

void loop() {
  // Leer el valor del monitor serie para el servo 1
  if (Serial.available() > 0) {
    int angulo1 = Serial.parseInt();
    angulo1 = constrain(angulo1, 0, 180); // Limitar el angulo entre 0 y 180
    
    servo1.write(angulo1);
    Serial.print("Servo 1 en posicion: ");
    Serial.println(angulo1);
    
    // Esperar a que se complete el movimiento del primer servo
    delay(1); 

    // Leer el valor del monitor serie para el servo 2
    int angulo2 = Serial.parseInt();
    angulo2 = constrain(angulo2, 0, 180); // Limitar el angulo entre 0 y 180

    servo2.write(angulo2);
    Serial.print("Servo 2 en posicion: ");
    Serial.println(angulo2);
    
    // Limpiar el buffer de serial para evitar problemas con datos residuales
    while (Serial.available() > 0) {
      Serial.read(); 
    }
  }
}
