# Potentiometer (GP26 = ADC0) sets the LED brightness (PWM on GP15).
from machine import ADC, PWM, Pin
import time

pot = ADC(26)
pwm = PWM(Pin(15))
pwm.freq(1000)                  # 1 kHz

while True:
    value = pot.read_u16()      # 0 .. 65535 (12 bit ADC, scaled to 16 bit)
    pwm.duty_u16(value)         # duty cycle 0 .. 100 %
    print(f"ADC {value:5d}  ->  duty {value * 100 // 65535:3d} %")
    time.sleep_ms(200)
