//! Blink the LED on GP15 using the rp2040-hal GPIO API.
#![no_std]
#![no_main]

use embedded_hal::digital::OutputPin;
use embedded_hal::delay::DelayNs;
use panic_halt as _;
use rp_pico::{entry, hal, hal::pac};

#[entry]
fn main() -> ! {
    // Take ownership of the peripherals - exactly once.
    let mut pac = pac::Peripherals::take().unwrap();

    // Clock setup: 12 MHz crystal -> PLL -> 125 MHz system clock.
    let mut watchdog = hal::Watchdog::new(pac.WATCHDOG);
    let clocks = hal::clocks::init_clocks_and_plls(
        rp_pico::XOSC_CRYSTAL_FREQ,
        pac.XOSC,
        pac.CLOCKS,
        pac.PLL_SYS,
        pac.PLL_USB,
        &mut pac.RESETS,
        &mut watchdog,
    )
    .ok()
    .unwrap();
    // RP2040 timer (1 MHz) as delay provider - implements embedded-hal DelayNs
    let mut delay = hal::Timer::new(pac.TIMER, &mut pac.RESETS, &clocks);

    // Bring the GPIO block out of reset and split it into single pins.
    let sio = hal::Sio::new(pac.SIO);
    let pins = rp_pico::Pins::new(pac.IO_BANK0, pac.PADS_BANK0, sio.gpio_bank0, &mut pac.RESETS);

    // The type system knows that this pin is now a push-pull output.
    let mut led = pins.gpio15.into_push_pull_output();

    loop {
        led.set_high().unwrap();
        delay.delay_ms(500);
        led.set_low().unwrap();
        delay.delay_ms(500);
    }
}
