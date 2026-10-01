//! The hardware independent `debounce` library on the Pico: the same code
//! that is unit-tested on the PC toggles the LED (GP15) with the button (GP14).
#![no_std]
#![no_main]

use debounce::{Debouncer, Edge};
use embedded_hal::digital::StatefulOutputPin;
use embedded_hal::delay::DelayNs;
use panic_halt as _;
use rp_pico::{entry, hal, hal::pac};

#[entry]
fn main() -> ! {
    let mut pac = pac::Peripherals::take().unwrap();
    let mut watchdog = hal::Watchdog::new(pac.WATCHDOG);
    let clocks = hal::clocks::init_clocks_and_plls(
        rp_pico::XOSC_CRYSTAL_FREQ, pac.XOSC, pac.CLOCKS, pac.PLL_SYS, pac.PLL_USB,
        &mut pac.RESETS, &mut watchdog,
    )
    .ok()
    .unwrap();
    // RP2040 timer (1 MHz) as delay provider - implements embedded-hal DelayNs
    let mut delay = hal::Timer::new(pac.TIMER, &mut pac.RESETS, &clocks);
    let sio = hal::Sio::new(pac.SIO);
    let pins = rp_pico::Pins::new(pac.IO_BANK0, pac.PADS_BANK0, sio.gpio_bank0, &mut pac.RESETS);

    let mut led = pins.gpio15.into_push_pull_output();
    let mut button = pins.gpio14.into_pull_up_input();
    let mut debouncer = Debouncer::new(20); // 20 samples of 1 ms

    loop {
        // poll() accepts any pin type that implements embedded-hal's InputPin
        if debouncer.poll(&mut button).unwrap() == Edge::Pressed {
            led.toggle().unwrap();
        }
        delay.delay_ms(1);
    }
}
