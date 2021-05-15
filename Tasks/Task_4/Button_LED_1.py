from gpiozero import LED, Button

led = LED(7)            # GPIO Pin 7 for LED
button = Button(5)      # GPIO Pin 5 for Pushbutton

def PinCleanup():
    led.close()
    button.close()

for i in range(10):
    if button.is_pressed:   # Check Switch
        led.on()
    else:
        led.off()

# Good Practice to return GPIO pins to normal state
PinCleanup()
