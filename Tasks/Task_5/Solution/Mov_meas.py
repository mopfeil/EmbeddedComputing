import RPi.GPIO as GPIO
from gpiozero import Button, LED, DistanceSensor
import time
import os

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

led = LED(7)
button = Button(5)

Motor1_PWM = 18  # Set pin for Motor 1 PWM
Motor1_IN1 = 17  # Connected pin for Motor_1: Clockwise
Motor1_IN2 = 22  # Connected pin for Motor_1: anti-Clockwise

Motor2_PWM = 19
Motor2_IN1 = 24  # Connected pin for Motor_2: Clockwise
Motor2_IN2 = 4  # Connected pin for Motor_2: anti-Clockwise

# Pin Ultrasonic Sensor
trigger = 25
echo = 27

GPIO.setup(Motor1_PWM, GPIO.OUT)
GPIO.setup(Motor1_IN1, GPIO.OUT)
GPIO.setup(Motor1_IN2, GPIO.OUT)
PWM_1 = GPIO.PWM(Motor1_PWM, 90)  # PWM value set to 90
PWM_1.start(0)

GPIO.setup(Motor2_PWM, GPIO.OUT)
GPIO.setup(Motor2_IN1, GPIO.OUT)
GPIO.setup(Motor2_IN2, GPIO.OUT)
PWM_2 = GPIO.PWM(Motor2_PWM, 90)  # PWM value set to 90
PWM_2.start(0)

# Speed setting: 28, 40, 50 \\Slower speeds for better measurement
SpeedArr = [28, 40, 50];


def Robot_STOP():
    PWM_1.ChangeDutyCycle(0)
    PWM_2.ChangeDutyCycle(0)
    time.sleep(5)


def Robot_M1_FW():
    GPIO.output(Motor1_IN1, GPIO.HIGH)
    GPIO.output(Motor1_IN2, GPIO.LOW)


def Robot_M2_FW():
    GPIO.output(Motor2_IN1, GPIO.HIGH)
    GPIO.output(Motor2_IN2, GPIO.LOW)

# Measure time and Distance
def Time_Dist_Meas(start):
    time.sleep(1)
    meas = str(round((time.time() - start), 2))
    len = str(round(sensor.distance * 100, 2))
    x.write(meas + ',' + len + '\n')

#  Drive robot towards obstacle
def Robot_Drive(a):
    PWM_1.ChangeDutyCycle(a)
    PWM_2.ChangeDutyCycle(a)
    Robot_M1_FW()

    Robot_M2_FW()


def Robot_Meas(p):
    start = time.time()

    # threshold distance = 20cm, Max.distance = 1m
    while round(sensor.distance * 100, 2) > 20 and round(sensor.distance * 100, 2) < 100:
        Time_Dist_Meas(start)
        Robot_Drive(p)

    end = time.time()
    Robot_STOP()


def TitleName(a):
    x.write('#Distance - Time Measurement: ' + str(a) + 'cycle/seconds')
    x.write('\n')
    x.write('# Time, Distance')
    x.write('\n')


sensor = DistanceSensor(echo=27, trigger=25)

# Loop using Speed Settings
for i in SpeedArr:
    filename = str(str(i) + '.txt')
    print(filename)
    x = open(filename, 'w')
    TitleName(i)                # Title of text file

    led.on()
    Robot_Meas(i)
    led.off()

    # Manually return robot to original position
    time.sleep(5)  # Begin after 1s
    x.close()  # Close the created files


