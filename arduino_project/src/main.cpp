/*
 * Arduino Face Tracking con Servomotores
 * Recibe coordenadas X,Y desde Python y mueve servos para centrar el rostro
 * Formato esperado: "X:valor,Y:valor\n"
 */

#include <Arduino.h>
#include <Servo.h>

Servo servoX;  // Servo horizontal (izquierda-derecha)
Servo servoY;  // Servo vertical (arriba-abajo)

// Pines de los servos (ajusta según tu conexión)
const int PIN_SERVO_X = 9;
const int PIN_SERVO_Y = 10;

// Variables para almacenar ángulos
int angleX = 90;  // Posición inicial centrada
int angleY = 90;

// Buffer para recibir datos
String receivedData = "";

void setup() {
  Serial.begin(115200);
  
  // Inicializar servos
  servoX.attach(PIN_SERVO_X);
  servoY.attach(PIN_SERVO_Y);
  
  // Posición inicial centrada
  servoX.write(angleX);
  servoY.write(angleY);
  
  Serial.println("Arduino listo - Face Tracking");
}

void loop() {
  // Leer datos del puerto serial
  while (Serial.available() > 0) {
    char inChar = (char)Serial.read();
    
    if (inChar == '\n') {
      // Procesar los datos recibidos
      processData(receivedData);
      receivedData = "";  // Limpiar buffer
    } else {
      receivedData += inChar;
    }
  }
}

void processData(String data) {
  // Formato esperado: "X:90,Y:85"
  int xIndex = data.indexOf("X:");
  int yIndex = data.indexOf(",Y:");
  
  if (xIndex != -1 && yIndex != -1) {
    // Extraer valores
    String xValue = data.substring(xIndex + 2, yIndex);
    String yValue = data.substring(yIndex + 3);
    
    angleX = xValue.toInt();
    angleY = yValue.toInt();
    
    // Limitar ángulos entre 0 y 180
    angleX = constrain(angleX, 0, 180);
    angleY = constrain(angleY, 0, 180);
    
    // Mover servos
    servoX.write(angleX);
    servoY.write(angleY);
    
    // Feedback (opcional, comentar si causa lag)
    // Serial.print("Servos: X=");
    // Serial.print(angleX);
    // Serial.print(" Y=");
    // Serial.println(angleY);
  }
}
