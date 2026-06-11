import cv2
import numpy as np
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import time

BROKER = "mosquitto" 
PORT = 1883
TOPIC_COLOR = "escom/6CM3/equipo_clasificador/sensor/color"

PIN_SERVO_DISPENSADOR = 17 
PIN_SERVO_RAMPA = 18       

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_SERVO_DISPENSADOR, GPIO.OUT)
GPIO.setup(PIN_SERVO_RAMPA, GPIO.OUT)

pwm_disp = GPIO.PWM(PIN_SERVO_DISPENSADOR, 50)
pwm_rampa = GPIO.PWM(PIN_SERVO_RAMPA, 50)
pwm_disp.start(0)
pwm_rampa.start(0)

POS_ESPERA = 0    
POS_LIBERAR = 90  

def mover_servo(pwm, pin, angulo):
    duty = angulo / 18 + 2
    GPIO.output(pin, True)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5) 
    GPIO.output(pin, False)
    pwm.ChangeDutyCycle(0)

def sincronizar_mecanismo(color):
    print(f"[Actuador] Clasificando pieza: {color}")
    if color == "Rojo": mover_servo(pwm_rampa, PIN_SERVO_RAMPA, 20)
    elif color == "Naranja": mover_servo(pwm_rampa, PIN_SERVO_RAMPA, 55)
    elif color == "Amarillo": mover_servo(pwm_rampa, PIN_SERVO_RAMPA, 90)
    elif color == "Verde": mover_servo(pwm_rampa, PIN_SERVO_RAMPA, 125)
    elif color == "Azul": mover_servo(pwm_rampa, PIN_SERVO_RAMPA, 160)
    
    time.sleep(0.3)
    mover_servo(pwm_disp, PIN_SERVO_DISPENSADOR, POS_LIBERAR)
    time.sleep(0.6) 
    mover_servo(pwm_disp, PIN_SERVO_DISPENSADOR, POS_ESPERA)
    print("[Sistema] Listo para la siguiente lectura.")

def on_connect(client, userdata, flags, rc):
    print("Conectado a Mosquitto")
    client.subscribe(TOPIC_COLOR, qos=1)

def on_message(client, userdata, msg):
    sincronizar_mecanismo(msg.payload.decode())

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.loop_start()

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

mover_servo(pwm_disp, PIN_SERVO_DISPENSADOR, POS_ESPERA)

try:
    print("Iniciando escáner de cámara para 5 colores...")
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        mask_red = cv2.inRange(hsv, np.array([0, 120, 70]), np.array([10, 255, 255]))
        mask_orange = cv2.inRange(hsv, np.array([11, 120, 70]), np.array([20, 255, 255]))
        mask_yellow = cv2.inRange(hsv, np.array([21, 120, 70]), np.array([35, 255, 255]))
        mask_green = cv2.inRange(hsv, np.array([40, 50, 50]), np.array([80, 255, 255]))
        mask_blue = cv2.inRange(hsv, np.array([100, 150, 0]), np.array([140, 255, 255]))

        color_detectado = None
        umbral_pixeles = 5500
        
        if cv2.countNonZero(mask_red) > umbral_pixeles: color_detectado = "Rojo"
        elif cv2.countNonZero(mask_orange) > umbral_pixeles: color_detectado = "Naranja"
        elif cv2.countNonZero(mask_yellow) > umbral_pixeles: color_detectado = "Amarillo"
        elif cv2.countNonZero(mask_green) > umbral_pixeles: color_detectado = "Verde"
        elif cv2.countNonZero(mask_blue) > umbral_pixeles: color_detectado = "Azul"
        
        if color_detectado:
            print(f"[Sensor] Detectado: {color_detectado}. Publicando...")
            client.publish(TOPIC_COLOR, color_detectado, qos=1)
            time.sleep(3) 

except KeyboardInterrupt:
    print("Apagando...")
finally:
    cap.release()
    pwm_disp.stop()
    pwm_rampa.stop()
    GPIO.cleanup()
    client.loop_stop()
    client.disconnect()