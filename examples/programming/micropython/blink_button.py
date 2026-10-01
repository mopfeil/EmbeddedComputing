# MicroPython on the Raspberry Pi Pico (Wokwi: new MicroPython Pico project,
# circuit from examples/interfaces/c/diagram.json).
# LED on GP15, button on GP14 to GND.
from machine import Pin
import time

led = Pin(15, Pin.OUT)
button = Pin(14, Pin.IN, Pin.PULL_UP)
presses = 0

def on_press(pin):              # interrupt handler: keep it short
    global presses
    presses += 1

button.irq(trigger=Pin.IRQ_FALLING, handler=on_press)

while True:
    led.toggle()
    print("presses (with bouncing):", presses)
    time.sleep_ms(500)
