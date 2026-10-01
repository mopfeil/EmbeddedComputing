//! Watchdog demo: the main loop feeds the watchdog every 100 ms.
//! Hold the button (GP14) longer than 1 s -> the program "hangs" and the
//! watchdog resets the chip. After the reset the cause is printed.
#![no_std]
#![no_main]

use core::fmt::Write;
use embedded_hal::digital::{InputPin, StatefulOutputPin};
use embedded_hal::delay::DelayNs;
use panic_halt as _;
use rp_pico::hal::fugit::{ExtU32, RateExtU32};
use rp_pico::hal::uart::{DataBits, StopBits, UartConfig, UartPeripheral};
use rp_pico::hal::{gpio, Clock};
use rp_pico::{entry, hal, hal::pac};

#[entry]
fn main() -> ! {
    let mut pac = pac::Peripherals::take().unwrap();

    // Read the reset reason before the HAL takes the WATCHDOG peripheral.
    let by_watchdog = pac.WATCHDOG.reason().read().timer().bit_is_set();

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

    let uart_pins = (
        pins.gpio0.into_function::<gpio::FunctionUart>(),
        pins.gpio1.into_function::<gpio::FunctionUart>(),
    );
    let mut uart = UartPeripheral::new(pac.UART0, uart_pins, &mut pac.RESETS)
        .enable(
            UartConfig::new(115_200.Hz(), DataBits::Eight, None, StopBits::One),
            clocks.peripheral_clock.freq(),
        )
        .unwrap();

    let mut led = pins.gpio15.into_push_pull_output();
    let mut button = pins.gpio14.into_pull_up_input();

    if by_watchdog {
        writeln!(uart, "Restarted by the WATCHDOG\r").unwrap();
    } else {
        writeln!(uart, "Power-on reset\r").unwrap();
    }

    watchdog.pause_on_debug(true); // do not reset while halted in the debugger
    watchdog.start(1_000.millis()); // timeout 1 s

    loop {
        while button.is_low().unwrap() {
            // simulated "hang": the watchdog is no longer fed
        }
        watchdog.feed();
        led.toggle().unwrap();
        delay.delay_ms(100);
    }
}
