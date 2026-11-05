//! The C program c/dangling.c, written in Rust.
//!
//!     cargo run --example dangling
//!
//! This file does NOT compile - on purpose. The borrow checker sees that
//! `first` still points into `log` while `log.push()` may move the buffer,
//! and rejects the program (error E0502). In VS Code, rust-analyzer marks
//! the line in red while you type. The corrected program is src/main.rs.

fn main() {
    let mut log: Vec<i16> = Vec::new();
    log.push(215); // 21.5 degC, in 0.1 degC

    let first = &log[0]; // borrow: a reference into the buffer
    println!("first reading: {first} (address {first:p})");

    for i in 0..100 {
        log.push(220 + i); // error: `log` is still borrowed by `first`
    }

    println!("first reading: {first}"); // the borrow is used here
}
