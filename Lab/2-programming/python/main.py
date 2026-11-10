# Lab task 2: programming the ET1 robot - MicroPython version
#
# Build: Terminal > Run Build Task ("Python: build main.uf2"), then
# F1 -> "Wokwi: Start Simulator". Output: serial monitor (USB).
#
# Work through the TODOs in the order of their numbers. Set TASK to the task
# you are working on; the main loop at the end then runs that task over and over.

import time
from machine import Pin, PWM

TASK = 2        # 2, 3 or 4 (task 1 is used by 3 and 4, task 5 extends 3 and 4)

# ---- given: wiring (see diagram.json) -------------------------------------
led = Pin(7, Pin.OUT)                   # red LED, 1 = on
button = Pin(5, Pin.IN, Pin.PULL_UP)    # START button to GND: 0 = pressed

ena = PWM(Pin(18), freq=1000, duty_u16=0)               # left motor: speed
in1, in2 = Pin(17, Pin.OUT, value=0), Pin(16, Pin.OUT, value=0)   # direction
enb = PWM(Pin(19), freq=1000, duty_u16=0)               # right motor: speed
in3, in4 = Pin(20, Pin.OUT, value=0), Pin(21, Pin.OUT, value=0)

LEFT, RIGHT = 0, 1


def button_down():
    """Raw level of the button, without debouncing."""
    return button.value() == 0


# ===========================================================================
# Task 1: motor driver
# ===========================================================================
def motor(side, speed):
    """speed in percent: -100 = full speed backward, 0 = brake, +100 = full forward.

    The H-bridge: IN1 IN2 = 1 0 forward, 0 1 backward, 0 0 brake (IN3/IN4 the
    same for the right motor). The speed is the PWM duty cycle on ENA / ENB:
    ena.duty_u16(0 ... 65535) = 0 ... 100 %.
    """
    # TODO 1a: limit speed to -100..100 (a caller may pass 150)

    # TODO 1b: pick the PWM and the two direction pins of this side

    # TODO 1c: set the two direction pins from the sign of speed

    # TODO 1d: write the magnitude of speed to the PWM (convert % to 0..65535)
    pass


def stop():
    motor(LEFT, 0)
    motor(RIGHT, 0)


# ===========================================================================
# Task 2: button and LED
# ===========================================================================
def button_clicked():
    """True exactly once per press: when the button goes from released to
    pressed. Call it often (every millisecond or so)."""
    # TODO 2a: remember the previous state of the button in a global variable
    #          and return True only on the change released -> pressed

    # TODO 2b: the contacts bounce: ignore changes that come less than 30 ms
    #          after the last accepted change (time.ticks_ms(), time.ticks_diff())
    return False


def task2():
    # TODO 2c: every click toggles the LED; print "LED on" / "LED off".
    #          Check: holding the button down toggles only once.
    pass


# ===========================================================================
# Task 5: emergency stop (do this after tasks 3 and 4)
# ===========================================================================
def wait_ms(ms):
    """Waits ms milliseconds. Returns True if the time has passed and False if
    the button was clicked during the wait."""
    # TODO 5a: replace sleep_ms() by a loop that runs until ms have passed and
    #          checks button_clicked() every millisecond. On a click: stop the
    #          motors, print "EMERGENCY STOP" and return False at once.
    time.sleep_ms(ms)
    return True

# TODO 5b: use wait_ms() in task 3 and task 4 for every wait while the robot
#          moves. When it returns False, end the whole sequence at once
#          (motors off, LED off) - a second click during the drive stops ET1.


# ===========================================================================
# Task 3: turning
# ===========================================================================
def task3():
    # TODO 3: wait for a click (button_clicked()), then:
    #   - LED on
    #   - only the left wheel drives forward at 50 % for 10 s
    #     (the right one brakes: ET1 turns around the right wheel)
    #   - then only the right wheel at 50 % for 10 s
    #   - stop, LED off, print the time the sequence took (time.ticks_ms())
    #   Watch the track on the display: which way does ET1 turn first?
    pass


# ===========================================================================
# Task 4: accelerate and brake
# ===========================================================================
def ramp(direction):
    """direction = +1 forward, -1 backward"""
    # TODO 4a: speed 10, 20, ... 80 %, each step held for 0.5 s,
    #          then back down 70, 60, ... 0 %, each held for 0.5 s
    pass


def task4():
    # TODO 4b: wait for a click, LED on, ramp(+1), 1 s pause, ramp(-1), LED off.
    #   ET1 should end where it started: check D on the display and in the
    #   "ET1 stopped at" message.
    #
    # TODO 4c: real motors are never equal. In the simulator, click the ET1
    #   chip and set "Left motor weaker by" to 10 %: ET1 now drives a curve
    #   (H changes). Add a trim factor to motor() for the left side so that
    #   ET1 drives straight again (H stays within +-5 degrees at the end of
    #   ramp(+1)); find the factor by trying. Make it a constant at the top.
    pass


# ---- given -----------------------------------------------------------------
stop()
print("ET1 ready, task", TASK)
while True:
    if TASK == 2:
        task2()
    elif TASK == 3:
        task3()
    elif TASK == 4:
        task4()
    time.sleep_ms(1)
