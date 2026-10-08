//! Minimal driver for the usual "LCD 1602 I2C" module: an HD44780 text
//! display behind a PCF8574 port expander at 0x27. The expander's 8 outputs
//! are P0 = RS, P1 = RW, P2 = E, P3 = backlight, P4..P7 = D4..D7, so every
//! byte goes to the display as two 4-bit halves, each with a pulse on E.

use core::fmt;
use embassy_time::Timer;
use esp_hal::Blocking;
use esp_hal::i2c::master::{Error, I2c};

const ADDR: u8 = 0x27;
const RS: u8 = 0x01; // 0 = command, 1 = character
const EN: u8 = 0x04;
const BACKLIGHT: u8 = 0x08;

/// One half byte: E high, then E low (the display takes the data on the falling edge)
fn nibble(i2c: &mut I2c<'static, Blocking>, bits: u8) -> Result<(), Error> {
    i2c.write(ADDR, &[bits | EN | BACKLIGHT, bits | BACKLIGHT])
}

/// One byte, then 50 us for the display to execute it (37 us in the data
/// sheet). The await also lets the other tasks run between the bytes.
async fn byte(i2c: &mut I2c<'static, Blocking>, value: u8, mode: u8) -> Result<(), Error> {
    nibble(i2c, (value & 0xF0) | mode)?;
    nibble(i2c, (value << 4) | mode)?;
    Timer::after_micros(50).await;
    Ok(())
}

/// Initialisation sequence from the HD44780 data sheet for 4-bit mode
pub async fn init(i2c: &mut I2c<'static, Blocking>) -> Result<(), Error> {
    Timer::after_millis(50).await;
    for _ in 0..3 {
        nibble(i2c, 0x30)?; // "8-bit mode", three times
        Timer::after_millis(5).await;
    }
    nibble(i2c, 0x20)?; // switch to 4-bit mode
    // 2 lines, display on, cursor moves right, clear
    for cmd in [0x28, 0x0C, 0x06, 0x01] {
        byte(i2c, cmd, 0).await?;
        Timer::after_millis(2).await;
    }
    Ok(())
}

/// Writes a text to the start of row 0 or 1
pub async fn print_at(i2c: &mut I2c<'static, Blocking>, row: u8, text: &[u8]) -> Result<(), Error> {
    byte(i2c, 0x80 | (row * 0x40), 0).await?; // set the address in the display RAM
    for &c in text {
        byte(i2c, c, RS).await?;
    }
    Ok(())
}

/// A 16 character line for `write!` (no heap in this program)
pub struct Line {
    buf: [u8; 16],
    len: usize,
}

impl Line {
    pub fn new() -> Self {
        Line { buf: [b' '; 16], len: 0 }
    }
    /// The full line, padded with spaces
    pub fn bytes(&self) -> &[u8] {
        &self.buf
    }
}

impl fmt::Write for Line {
    fn write_str(&mut self, s: &str) -> fmt::Result {
        for &c in s.as_bytes() {
            if self.len < self.buf.len() {
                self.buf[self.len] = c;
                self.len += 1;
            }
        }
        Ok(())
    }
}
