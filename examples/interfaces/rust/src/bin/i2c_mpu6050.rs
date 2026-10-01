//! Read the MPU6050 acceleration sensor over I2C0 (GP4 = SDA, GP5 = SCL).
//! I2C address 0x68 (AD0 = low).
#![no_std]
#![no_main]

use core::fmt::Write;
use embedded_hal::i2c::I2c;
use panic_halt as _;
use rp_pico::hal::fugit::RateExtU32;
use rp_pico::hal::uart::{DataBits, StopBits, UartConfig, UartPeripheral};
use rp_pico::hal::{gpio, Clock};
use rp_pico::{entry, hal, hal::pac};

const MPU6050: u8 = 0x68;
const REG_ACCEL_XOUT_H: u8 = 0x3B;
const REG_PWR_MGMT_1: u8 = 0x6B;
const REG_WHO_AM_I: u8 = 0x75;

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

    // I2C lines are open drain: the pins need pull-up resistors.
    let sda = pins.gpio4.reconfigure::<gpio::FunctionI2C, gpio::PullUp>();
    let scl = pins.gpio5.reconfigure::<gpio::FunctionI2C, gpio::PullUp>();
    let mut i2c = hal::I2C::i2c0(
        pac.I2C0, sda, scl, 400.kHz(), // fast mode
        &mut pac.RESETS, clocks.system_clock.freq(),
    );

    // Register read = write the register address, then (repeated start) read.
    let mut id = [0u8; 1];
    i2c.write_read(MPU6050, &[REG_WHO_AM_I], &mut id).unwrap();
    writeln!(uart, "WHO_AM_I = 0x{:02X}\r", id[0]).unwrap();

    // Leave sleep mode: write 0 to PWR_MGMT_1.
    i2c.write(MPU6050, &[REG_PWR_MGMT_1, 0x00]).unwrap();

    loop {
        // Burst read: 6 bytes from ACCEL_XOUT_H (X, Y, Z as big endian i16).
        let mut buf = [0u8; 6];
        i2c.write_read(MPU6050, &[REG_ACCEL_XOUT_H], &mut buf).unwrap();
        let mut a = [0i32; 3];
        for (i, v) in a.iter_mut().enumerate() {
            // Range +-2 g -> 16384 LSB per g; print in milli-g
            *v = i16::from_be_bytes([buf[2 * i], buf[2 * i + 1]]) as i32 * 1000 / 16384;
        }
        writeln!(uart, "ax = {:5} mg  ay = {:5} mg  az = {:5} mg\r", a[0], a[1], a[2]).unwrap();
        delay.delay_ms(500);
    }
}
