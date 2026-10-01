//! Assembly in Rust: a function written in Thumb assembly (global_asm!)
//! and a few instructions inline (asm!). Output on UART0 (GP0/GP1).
#![no_std]
#![no_main]

use core::arch::{asm, global_asm};
use core::fmt::Write;
use panic_halt as _;
use rp_pico::hal::fugit::RateExtU32;
use rp_pico::hal::uart::{DataBits, StopBits, UartConfig, UartPeripheral};
use rp_pico::hal::{Clock, gpio};
use rp_pico::{entry, hal, hal::pac};

// uint32_t asm_sum(const uint16_t *a, int n) - AAPCS: a in r0, n in r1,
// result in r0. Uses only r0..r3, which a function may change freely.
global_asm!(
    ".section .text.asm_sum, \"ax\"",
    ".global asm_sum",
    ".type asm_sum, %function",
    ".thumb_func",
    "asm_sum:",
    "    movs  r2, #0          @ s = 0",
    "    cmp   r1, #0",
    "    ble   2f              @ n <= 0: nothing to do",
    "1:  ldrh  r3, [r0]        @ r3 = *a",
    "    adds  r0, r0, #2      @ a++ (2 bytes)",
    "    adds  r2, r2, r3      @ s += r3",
    "    subs  r1, r1, #1      @ n--, sets the Z flag",
    "    bne   1b              @ loop while n != 0",
    "2:  movs  r0, r2          @ return s",
    "    bx    lr",
);

unsafe extern "C" {
    fn asm_sum(a: *const u16, n: i32) -> u32;
}

/// The same function in Rust, for comparison.
fn rust_sum(a: &[u16]) -> u32 {
    a.iter().map(|&x| x as u32).sum()
}

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

    let data: [u16; 6] = [1, 2, 3, 1000, 60000, 65535];
    let s_asm = unsafe { asm_sum(data.as_ptr(), data.len() as i32) };
    writeln!(uart, "asm_sum  = {s_asm}\r").unwrap();
    writeln!(uart, "rust_sum = {}\r", rust_sum(&data)).unwrap();

    // Inline assembly: read the stack pointer and add two registers.
    let sp: u32;
    unsafe { asm!("mov {}, sp", out(reg) sp) };
    let mut x: u32 = 40;
    unsafe { asm!("adds {0}, {0}, {1}", inout(reg) x, in(reg) 2u32) };
    writeln!(uart, "sp = 0x{sp:08x}, 40 + 2 = {x}\r").unwrap();

    loop {
        cortex_m::asm::wfi();
    }
}
