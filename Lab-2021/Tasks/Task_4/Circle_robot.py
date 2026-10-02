
# Libraries
import RPi.GPIO as GPIO
from gpiozero import Button, LED
import time


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

led = LED(7)            # Connection pin to LED -- 7
button = Button(5)      # Connection pin to pushbutton -- 5

Motor1_PWM = 18         # Set Pin for Motor 1 PWM
Motor1_IN1 = 17         # Connection pin 1 for Motor 1: Clockwise
Motor1_IN2 = 22         # Connection pin 2 for Motor 1: Anti-Clockwise

Motor2_PWM = 19         # Set Pin for Motor 2 PWM
Motor2_IN1 = 24         # Connection pin 1 for Motor 2: Clockwise
Motor2_IN2 = 4          # Connection pin 2 for Motor 2: Anti-Clockwise

GPIO.setup(Motor1_PWM, GPIO.OUT)
GPIO.setup(Motor1_IN1, GPIO.OUT)
GPIO.setup(Motor1_IN2, GPIO.OUT)
PWM_1 = GPIO.PWM(Motor1_PWM, 90)        # PWM  value set to 90
PWM_1.start(0)

GPIO.setup(Motor2_PWM, GPIO.OUT)
GPIO.setup(Motor2_IN1, GPIO.OUT)
GPIO.setup(Motor2_IN2, GPIO.OUT)
PWM_2 = GPIO.PWM(Motor2_PWM, 90)        # PWM  value set to 90
PWM_2.start(0)


# Robot Movement functions

# Set all PWM : 0 --> Stop
def Robot_STOP():
    PWM_1.ChangeDutyCycle(0)
    PWM_2.ChangeDutyCycle(0)
    time.sleep(2)


# Set all  IN1: HIGH and IN2: LOW  --> Clockwise
def Robot_M1_FW():
    GPIO.output(Motor1_IN1, GPIO.HIGH)
    GPIO.output(Motor1_IN2, GPIO.LOW)



def Robot_M2_FW():
    GPIO.output(Motor2_IN1, GPIO.HIGH)
    GPIO.output(Motor2_IN2, GPIO.LOW)



def Robot_M1_BW():
    GPIO.output(Motor1_IN1, GPIO.LOW)
    GPIO.output(Motor1_IN2, GPIO.HIGH)



def Robot_M2_BW():
    GPIO.output(Motor2_IN1, GPIO.LOW)
    GPIO.output(Motor2_IN2, GPIO.HIGH)



# Set HIGHER PWM on Left Motor to move Right
def Circle_Mov_FWRight():

    PWM_1.ChangeDutyCycle(70)
    Robot_M1_FW()
    PWM_2.ChangeDutyCycle(30)
    Robot_M2_FW()
    time.sleep(10)
    Robot_STOP()

def Circle_Mov_BWRight():

    PWM_1.ChangeDutyCycle(70)
    Robot_M1_BW()
    PWM_2.ChangeDutyCycle(30)
    Robot_M2_BW()
    time.sleep(10)
    Robot_STOP()

# Set HIGHER PWM on Right Motor to move Left
def Circle_Mov_FWLeft():

    PWM_2.ChangeDutyCycle(70)
    Robot_M2_FW()
    PWM_1.ChangeDutyCycle(30)
    Robot_M1_FW()
    time.sleep(10)
    Robot_STOP()

def Circle_Mov_BWLeft():

    PWM_2.ChangeDutyCycle(70)
    Robot_M2_BW()
    PWM_1.ChangeDutyCycle(30)
    Robot_M1_BW()
    time.sleep(10)
    Robot_STOP()

def safeClean():
    GPIO.cleanup()


i = 0

while(i < 25) :
    print(i)
    i += 1
    led.on()
    if button.is_pressed :
        Circle_Mov_FWLeft()
        Circle_Mov_FWRight()

    else:
        Circle_Mov_FWRight()
        Circle_Mov_FWLeft()

safeClean()