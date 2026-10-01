//! Blink the on-board LED (GP25) by writing the RP2040 registers directly.
//! No HAL - this is what the HAL does for us under the hood.
#![no_std]
#![no_main]

use cortex_m_rt::entry;
use panic_halt as _;
use rp_pico as _; // links the 2nd stage bootloader

// Every peripheral register block has atomic aliases:
// +0x1000 XOR, +0x2000 SET bits, +0x3000 CLEAR bits.
const RESETS_BASE: usize = 0x4000_c000;
const RESETS_RESET_CLR: *mut u32 = (RESETS_BASE + 0x3000) as *mut u32;
const RESETS_RESET_DONE: *const u32 = (RESETS_BASE + 0x8) as *const u32;
const RESET_IO_BANK0: u32 = 1 << 5;
const RESET_PADS_BANK0: u32 = 1 << 8;

const IO_BANK0_BASE: usize = 0x4001_4000;
const fn gpio_ctrl(n: usize) -> *mut u32 {
    (IO_BANK0_BASE + 0x04 + 8 * n) as *mut u32
}
const FUNCSEL_SIO: u32 = 5;

const SIO_BASE: usize = 0xd000_0000;
const SIO_GPIO_OE_SET: *mut u32 = (SIO_BASE + 0x024) as *mut u32;
const SIO_GPIO_OUT_XOR: *mut u32 = (SIO_BASE + 0x01c) as *mut u32;

const LED: usize = 25;

#[entry]
fn main() -> ! {
    unsafe {
        // 1. Release IO_BANK0 and PADS_BANK0 from reset and wait until done.
        RESETS_RESET_CLR.write_volatile(RESET_IO_BANK0 | RESET_PADS_BANK0);
        while RESETS_RESET_DONE.read_volatile() & (RESET_IO_BANK0 | RESET_PADS_BANK0)
            != (RESET_IO_BANK0 | RESET_PADS_BANK0)
        {}
        // 2. Connect the pin to the SIO (software controlled I/O).
        gpio_ctrl(LED).write_volatile(FUNCSEL_SIO);
        // 3. Enable the output driver.
        SIO_GPIO_OE_SET.write_volatile(1 << LED);
    }
    loop {
        unsafe { SIO_GPIO_OUT_XOR.write_volatile(1 << LED) }; // toggle
        // Busy wait. Without clock setup the core runs from the ring oscillator (~6 MHz).
        cortex_m::asm::delay(3_000_000);
    }
}
