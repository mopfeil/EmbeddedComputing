//! The corrected version of examples/dangling.rs.
//!
//!     cargo run
//!
//! Two correct ways to keep "the first reading":
//!   1. copy the value (an i16 is 2 bytes - copying is free), or
//!   2. keep the index and look it up again after the buffer has grown.
//! Both compile, both print 215. The machine code is as fast as the C
//! version: the checks happen at compile time, not at run time.

fn main() {
    let mut log: Vec<i16> = Vec::new();
    log.push(215); // 21.5 degC, in 0.1 degC

    let first_value = log[0]; // 1. a copy, not a reference
    let first_index = 0; //      2. an index instead of a pointer
    println!("first reading: {first_value}");

    for i in 0..100 {
        log.push(220 + i); // the buffer grows and may move
    }

    println!("first reading via copy:  {first_value}");
    println!("first reading via index: {}", log[first_index]);

    // Out of bounds is caught as well - at run time, with a clear message
    // instead of silently reading a neighbour's memory:
    match log.get(500) {
        Some(v) => println!("reading 500: {v}"),
        None => println!("reading 500 does not exist (only {} readings)", log.len()),
    }
}
