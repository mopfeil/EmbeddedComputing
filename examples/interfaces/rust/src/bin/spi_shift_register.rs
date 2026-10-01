//! Drive a 74HC595 shift register (8 LEDs) over SPI0.
//! GP18 = SCK -> SHCP, GP19 = TX (COPI) -> DS, GP17 = latch -> STCP
#![no_std]
#![no_main]

use embedded_hal::digital::OutputPin;
use embedded_hal::spi::{SpiBus, MODE_0};
use embedded_hal::delay::DelayNs;
use panic_halt as _;
use rp_pico::hal::fugit::RateExtU32;
use rp_pico::hal::{gpio, Clock};
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

    let sck = pins.gpio18.into_function::<gpio::FunctionSpi>();
    let copi = pins.gpio19.into_function::<gpio::FunctionSpi>();
    let mut latch = pins.gpio17.into_push_pull_output();

    // SPI mode 0 (CPOL = 0, CPHA = 0), 1 MHz, 8 bit frames, MSB first
    let mut spi = hal::spi::Spi::<_, _, _, 8>::new(pac.SPI0, (copi, sck)).init(
        &mut pac.RESETS,
        clocks.peripheral_clock.freq(),
        1.MHz(),
        MODE_0,
    );

    let mut pattern: u8 = 0b0000_0001;
    let mut left = true;
    loop {
        spi.write(&[pattern]).unwrap(); // 8 clock pulses shift the byte in
        spi.flush().unwrap(); // wait until the last bit has left the FIFO
        latch.set_high().unwrap(); // rising edge on STCP copies the
        latch.set_low().unwrap(); //  shift register to the outputs

        // "Knight rider" running light
        pattern = if left { pattern << 1 } else { pattern >> 1 };
        if pattern == 0b1000_0000 || pattern == 0b0000_0001 {
            left = !left;
        }
        delay.delay_ms(100);
    }
}
