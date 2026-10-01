//! Toggle the LED (GP15) on every press of the button (GP14).
//! The button bounces (Wokwi simulates this), so the input is debounced
//! in software: a new level is accepted only after it was stable for 20 ms.
#![no_std]
#![no_main]

use embedded_hal::digital::{InputPin, StatefulOutputPin};
use panic_halt as _;
use rp_pico::hal::Clock; // for clocks.*.freq()
use rp_pico::{entry, hal, hal::pac};

const STABLE_MS: u32 = 20;

#[entry]
fn main() -> ! {
    let mut pac = pac::Peripherals::take().unwrap();
    let core = pac::CorePeripherals::take().unwrap();
    let mut watchdog = hal::Watchdog::new(pac.WATCHDOG);
    let clocks = hal::clocks::init_clocks_and_plls(
        rp_pico::XOSC_CRYSTAL_FREQ, pac.XOSC, pac.CLOCKS, pac.PLL_SYS, pac.PLL_USB,
        &mut pac.RESETS, &mut watchdog,
    )
    .ok()
    .unwrap();
    let mut delay = cortex_m::delay::Delay::new(core.SYST, clocks.system_clock.freq().to_Hz());
    let sio = hal::Sio::new(pac.SIO);
    let pins = rp_pico::Pins::new(pac.IO_BANK0, pac.PADS_BANK0, sio.gpio_bank0, &mut pac.RESETS);

    let mut led = pins.gpio15.into_push_pull_output();
    // Button connects the pin to GND -> use the internal pull-up, pressed = low.
    let mut button = pins.gpio14.into_pull_up_input();

    let mut stable_pressed = false; // debounced state
    let mut counter = 0; // how long the raw level differs from the stable state

    loop {
        let raw_pressed = button.is_low().unwrap();
        if raw_pressed != stable_pressed {
            counter += 1;
            if counter >= STABLE_MS {
                stable_pressed = raw_pressed;
                counter = 0;
                if stable_pressed {
                    led.toggle().unwrap(); // react on the press edge only
                }
            }
        } else {
            counter = 0;
        }
        delay.delay_ms(1); // sample every 1 ms
    }
}
