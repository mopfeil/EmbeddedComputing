//! The corrected version of examples/dangling.rs, on the Pico in Wokwi.
//!
//!     cargo build --release      then F1 -> "Wokwi: Start Simulator"
//!
//! The reading is copied (an i16 is 2 bytes). The buffer may move as
//! often as it likes - the copy stays correct, and no false alarm occurs.
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

    let first = log[0]; // a copy, not a reference
    writeln!(uart, "first reading: {first} (buffer at {:p})\r", log.as_ptr()).unwrap();

    let msg = String::from("logger running"); // another part of the firmware
    writeln!(uart, "{msg}, message at {:p}\r", msg.as_ptr()).unwrap();
    for i in 0..100 {
        log.push(220 + i); // the buffer grows and moves
    }
    let report = String::from("OK"); // may get the freed block - harmless now

    writeln!(uart, "buffer is now at {:p}\r", log.as_ptr()).unwrap();
    writeln!(uart, "first reading: {first} ({report})\r").unwrap();
    writeln!(uart, "alarm (first reading > 30.0 degC): {}\r", if first > 300 { "YES" } else { "no" }).unwrap();

    // Out of bounds is caught too: get() returns None instead of reading
    // a neighbour's memory (log[500] would stop the program with a panic).
    match log.get(500) {
        Some(v) => writeln!(uart, "reading 500: {v}\r").unwrap(),
        None => writeln!(uart, "reading 500 does not exist ({} readings)\r", log.len()).unwrap(),
    }
    loop {
        cortex_m::asm::wfi();
    }
}
