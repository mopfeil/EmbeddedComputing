//! Coffee machine: a first embedded program, in Rust (Arduino Uno).
//! The same program as ../coffee/sketch.ino. The machine itself (water
//! boiler, heater, pump) is the custom chip ../coffee/coffee.chip.c -- the
//! program only sees it through its pins:
//!
//!   sensor:    water temperature on A0, 10 mV per degC
//!   actuators: heater on pin 8, pump on pin 9
//!   user:      button on pin 2 to GND ("make coffee"), green LED on pin 7 = ready
//!
//! Temperatures are in tenths of a degree (integers): the AVR has no
//! floating point unit, and ufmt prints no floats.
#![no_std]
#![no_main]

use arduino_hal::prelude::*;
use panic_halt as _;

const T_ON: u32 = 910; // two-point control of the heater: 91.0 / 94.0 degC
const T_OFF: u32 = 940;
const T_READY: u32 = 900; // hot enough for coffee
const BREW_TICKS: u32 = 2000; // 2000 x 10 ms = 20 s at 2 ml/s = 40 ml

#[arduino_hal::entry]
fn main() -> ! {
    let dp = arduino_hal::Peripherals::take().unwrap();
    let pins = arduino_hal::pins!(dp);
    let mut serial = arduino_hal::default_serial!(dp, pins, 57600);
    let mut adc = arduino_hal::Adc::new(dp.ADC, Default::default());

    let sensor = pins.a0.into_analog_input(&mut adc);
    let mut heater = pins.d8.into_output();
    let mut pump = pins.d9.into_output();
    let mut ready_led = pins.d7.into_output();
    let button = pins.d2.into_pull_up_input();

    ufmt::uwriteln!(&mut serial, "coffee machine: heating up ...").unwrap_infallible();

    let mut ticks: u32 = 0; // the loop runs every 10 ms
    let mut brewing_since: Option<u32> = None;
    loop {
        // 0..1023 for 0..5 V; 10 mV per degC -> tenths of a degree = millivolts
        let raw = sensor.analog_read(&mut adc) as u32;
        let t = raw * 5000 / 1023;

        // control the water temperature: heater on below 91, off above 94 degC
        if t < T_ON {
            heater.set_high();
        }
        if t > T_OFF {
            heater.set_low();
        }

        let ready = t >= T_READY && brewing_since.is_none();
        if ready { ready_led.set_high() } else { ready_led.set_low() }

        // the user presses the button: make one cup of coffee
        if button.is_low() && brewing_since.is_none() {
            if ready {
                brewing_since = Some(ticks);
                pump.set_high();
                ufmt::uwriteln!(&mut serial, "making coffee ...").unwrap_infallible();
            } else {
                ufmt::uwriteln!(&mut serial, "please wait, water at {}.{} C", t / 10, t % 10)
                    .unwrap_infallible();
                arduino_hal::delay_ms(300); // do not repeat the message too fast
                ticks += 30;
            }
        }
        if let Some(start) = brewing_since {
            if ticks - start >= BREW_TICKS {
                brewing_since = None;
                pump.set_low();
                ufmt::uwriteln!(&mut serial, "enjoy your coffee!").unwrap_infallible();
            }
        }

        if ticks % 100 == 0 && ticks > 0 {
            // status once per second
            let heater_on = if heater.is_set_high() { "on " } else { "off" };
            let pump_on = if brewing_since.is_some() { "on" } else { "off" };
            ufmt::uwriteln!(&mut serial, "{}.{} C   heater {}   pump {}", t / 10, t % 10, heater_on, pump_on)
                .unwrap_infallible();
        }
        arduino_hal::delay_ms(10);
        ticks += 1;
    }
}
