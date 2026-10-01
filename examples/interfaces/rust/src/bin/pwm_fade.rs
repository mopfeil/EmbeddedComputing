//! Fade the LED on GP15 with hardware PWM.
//! GP15 belongs to PWM slice 7, channel B.
//! f_PWM = f_sys / (DIV * (TOP + 1)) = 125 MHz / (125 * 1000) = 1 kHz
#![no_std]
#![no_main]

use embedded_hal::pwm::SetDutyCycle;
use embedded_hal::delay::DelayNs;
use panic_halt as _;
use rp_pico::{entry, hal, hal::pac};

const TOP: u16 = 999;

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

    let slices = hal::pwm::Slices::new(pac.PWM, &mut pac.RESETS);
    let mut pwm = slices.pwm7;
    pwm.set_div_int(125); // counter clock 125 MHz / 125 = 1 MHz
    pwm.set_top(TOP); // counts 0..=999 -> period 1 ms
    pwm.enable();

    let channel = &mut pwm.channel_b;
    channel.output_to(pins.gpio15); // FUNCSEL = PWM

    loop {
        // Duty cycle = compare value / (TOP + 1)
        for duty in (0..=TOP).chain((0..=TOP).rev()) {
            channel.set_duty_cycle(duty).unwrap();
            delay.delay_us(1000);
        }
    }
}
