//! Read the potentiometer (GP26 = ADC0) and the internal temperature
//! sensor (ADC4) and print the values on UART0 (GP0 = TX, GP1 = RX).
#![no_std]
#![no_main]

use core::fmt::Write;
use embedded_hal_0_2::adc::OneShot;
use embedded_hal::delay::DelayNs;
use panic_halt as _;
use rp_pico::hal::fugit::RateExtU32;
use rp_pico::hal::uart::{DataBits, StopBits, UartConfig, UartPeripheral};
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

    // UART0: 115200 baud, 8 data bits, no parity, 1 stop bit (8N1)
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

    // ADC: 12 bit SAR converter, reference = 3.3 V
    let mut adc = hal::Adc::new(pac.ADC, &mut pac.RESETS);
    let mut pot = hal::adc::AdcPin::new(pins.gpio26).unwrap();
    let mut temp_sensor = adc.take_temp_sensor().unwrap();

    loop {
        let raw: u16 = adc.read(&mut pot).unwrap(); // 0 ..= 4095
        let millivolt = raw as u32 * 3300 / 4095;

        // Datasheet: T = 27 - (V_sense - 0.706 V) / 0.001721 V/K
        let raw_t: u16 = adc.read(&mut temp_sensor).unwrap();
        let v_sense = raw_t as f32 * 3.3 / 4095.0;
        let celsius = 27.0 - (v_sense - 0.706) / 0.001721;

        writeln!(uart, "ADC0 = {raw:4} ({millivolt:4} mV)   chip temperature = {celsius:.1} C\r").unwrap();
        delay.delay_ms(500);
    }
}
