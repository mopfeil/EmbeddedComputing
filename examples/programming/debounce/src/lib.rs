//! A button debouncer that does not depend on any hardware.
//!
//! * the logic is a plain state machine that is fed with raw samples,
//! * `poll()` works with every input pin that implements the
//!   `embedded_hal::digital::InputPin` trait (any microcontroller),
//! * the unit tests run on the PC with `cargo test`.
#![no_std]

use embedded_hal::digital::InputPin;

/// What happened at this sample.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Edge {
    None,
    Pressed,
    Released,
}

/// Accepts a new level only after it was stable for `threshold` samples.
pub struct Debouncer {
    stable: bool,
    counter: u8,
    threshold: u8,
}

impl Debouncer {
    /// `threshold` samples, e.g. 20 when sampling every millisecond (20 ms).
    pub const fn new(threshold: u8) -> Self {
        Debouncer { stable: false, counter: 0, threshold }
    }

    /// Feed one raw sample (`true` = pressed).
    pub fn update(&mut self, raw: bool) -> Edge {
        if raw == self.stable {
            self.counter = 0;
            return Edge::None;
        }
        self.counter += 1;
        if self.counter < self.threshold {
            return Edge::None;
        }
        self.counter = 0;
        self.stable = raw;
        if raw { Edge::Pressed } else { Edge::Released }
    }

    /// Read an active-low button (pressed = low) and feed the sample.
    pub fn poll<P: InputPin>(&mut self, pin: &mut P) -> Result<Edge, P::Error> {
        Ok(self.update(pin.is_low()?))
    }

    pub fn is_pressed(&self) -> bool {
        self.stable
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use core::convert::Infallible;

    /// Feed a sequence of samples and collect the edges.
    fn run(d: &mut Debouncer, samples: &[bool]) -> (usize, usize) {
        let edges = samples.iter().map(|&s| d.update(s));
        edges.fold((0, 0), |(p, r), e| match e {
            Edge::Pressed => (p + 1, r),
            Edge::Released => (p, r + 1),
            Edge::None => (p, r),
        })
    }

    #[test]
    fn clean_press_and_release() {
        let mut d = Debouncer::new(3);
        let mut samples = [false; 2].to_vec();
        samples.extend([true; 5]);
        samples.extend([false; 5]);
        assert_eq!(run(&mut d, &samples), (1, 1));
        assert!(!d.is_pressed());
    }

    #[test]
    fn bouncing_gives_one_edge() {
        let mut d = Debouncer::new(3);
        // contact bounce: short pulses before the level is stable
        let samples = [true, false, true, false, true, true, true, true, true];
        assert_eq!(run(&mut d, &samples), (1, 0));
        assert!(d.is_pressed());
    }

    #[test]
    fn short_glitch_is_ignored() {
        let mut d = Debouncer::new(3);
        let samples = [false, true, true, false, false, false];
        assert_eq!(run(&mut d, &samples), (0, 0));
    }

    /// A fake pin for tests: implements the same trait as a real GPIO pin.
    struct FakePin(bool);
    impl embedded_hal::digital::ErrorType for FakePin {
        type Error = Infallible;
    }
    impl InputPin for FakePin {
        fn is_high(&mut self) -> Result<bool, Infallible> {
            Ok(self.0)
        }
        fn is_low(&mut self) -> Result<bool, Infallible> {
            Ok(!self.0)
        }
    }

    #[test]
    fn poll_reads_active_low_pin() {
        let mut d = Debouncer::new(2);
        let mut pin = FakePin(false); // low = pressed
        assert_eq!(d.poll(&mut pin), Ok(Edge::None));
        assert_eq!(d.poll(&mut pin), Ok(Edge::Pressed));
    }
}
