//! The C program ../c/dangling/dangling.ino in Rust, on the Pico.
//!
//!     cargo build --release --example dangling
//!
//! This file does NOT compile - on purpose. `first` borrows from `log`,
//! and `log.push()` may move the buffer, so the borrow checker rejects the
//! program (error E0502). There is no firmware that could give a false
//! alarm. The corrected program is src/main.rs.
#![no_std]
#![no_main]

extern crate alloc;

use alloc::{string::String, vec::Vec};
use core::fmt::Write;
use panic_halt as _;
use rp_pico::entry;

#[entry]
fn main() -> ! {
    let mut uart = pico_memory::init();
    let mut log: Vec<i16> = Vec::new();
    log.push(215); // 21.5 degC, in 0.1 degC

    let first = &log[0]; // borrow: a reference into the buffer
    let msg = String::from("logger running"); // another allocation
    writeln!(uart, "{msg}, first reading: {first}\r").unwrap();

    for i in 0..100 {
        log.push(220 + i); // error: `log` is still borrowed by `first`
    }
    let alarm = *first > 300; // the borrow is used here
    writeln!(uart, "alarm: {alarm}\r").unwrap();
    loop {
        cortex_m::asm::wfi();
    }
}
