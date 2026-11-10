//! Lab task 2: programming the ET1 robot - Rust version (rp-pico / rp2040-hal)
//!
//! Build: Terminal > Run Build Task (cargo build --release), then
//! F1 -> "Wokwi: Start Simulator". Output: serial monitor (UART0, 115200 baud).
//!
//! Work through the TODOs in the order of their numbers. Set TASK to the task
//! you are working on; the main loop then runs that task over and over.
//! The hardware set-up is in board.rs (given).
#![no_std]
#![no_main]
// The frame has empty functions. Remove this line once you are done:
#![allow(unused_variables, unused_imports, dead_code)]

mod board;

use board::Board;
use core::fmt::Write;
use embedded_hal::digital::{OutputPin, StatefulOutputPin};
use embedded_hal::pwm::SetDutyCycle;
use panic_halt as _;
use rp_pico::entry;

const TASK: u8 = 2; // 2, 3 or 4 (task 1 is used by 3 and 4, task 5 extends 3 and 4)

#[derive(Clone, Copy, PartialEq)]
enum Side {
    Left,
    Right,
}

struct App {
    b: Board,
    // TODO 2a: add the fields button_clicked() needs (previous state, time)
}

impl App {
    // =======================================================================
    // Task 1: motor driver
    // =======================================================================
    /// speed in percent: -100 = full speed backward, 0 = brake, +100 = full forward.
    /// The H-bridge: IN1 IN2 = 1 0 forward, 0 1 backward, 0 0 brake (IN3/IN4 the
    /// same for the right motor). The speed is the PWM duty cycle on ENA / ENB:
    /// self.b.pwm.channel_a.set_duty_cycle_percent(50) gives 50 % on ENA.
    fn motor(&mut self, side: Side, speed: i32) {
        // TODO 1a: limit speed to -100..=100 (a caller may pass 150): clamp()

        // TODO 1b: set the two direction pins of this side from the sign of
        //          speed (set_state(PinState::from(...)) or set_high/set_low)

        // TODO 1c: write the magnitude of speed to channel_a / channel_b
    }

    fn stop(&mut self) {
        self.motor(Side::Left, 0);
        self.motor(Side::Right, 0);
    }

    // =======================================================================
    // Task 2: button and LED
    // =======================================================================
    /// True exactly once per press: when the button goes from released to
    /// pressed. Call it often (every millisecond or so).
    fn button_clicked(&mut self) -> bool {
        // TODO 2a: compare self.b.button_down() with the previous state (a
        //          field of App) and return true only on released -> pressed

        // TODO 2b: the contacts bounce: ignore changes that come less than
        //          30 ms after the last accepted change (self.b.millis())
        false
    }

    fn task2(&mut self) {
        // TODO 2c: every click toggles the LED (self.b.led.toggle()); print
        //          "LED on" / "LED off" with writeln!(self.b.uart, "...").
        //          Check: holding the button down toggles only once.
    }

    // =======================================================================
    // Task 5: emergency stop (do this after tasks 3 and 4)
    // =======================================================================
    /// Waits ms milliseconds. Returns true if the time has passed and false if
    /// the button was clicked during the wait.
    fn wait_ms(&mut self, ms: u32) -> bool {
        // TODO 5a: replace delay_ms() by a loop that runs until ms have passed
        //          and checks button_clicked() every millisecond. On a click:
        //          stop the motors, print "EMERGENCY STOP" and return false.
        self.b.delay_ms(ms);
        true
    }

    // TODO 5b: use wait_ms() in task 3 and task 4 for every wait while the
    //          robot moves. When it returns false, end the whole sequence at
    //          once (motors off, LED off) - a second click stops ET1.
    //          Tip: let ramp() return bool and chain with && .

    // =======================================================================
    // Task 3: turning
    // =======================================================================
    fn task3(&mut self) {
        // TODO 3: wait for a click (button_clicked()), then:
        //   - LED on
        //   - only the left wheel drives forward at 50 % for 10 s
        //     (the right one brakes: ET1 turns around the right wheel)
        //   - then only the right wheel at 50 % for 10 s
        //   - stop, LED off, print the time the sequence took (self.b.millis())
        //   Watch the track on the display: which way does ET1 turn first?
    }

    // =======================================================================
    // Task 4: accelerate and brake
    // =======================================================================
    /// dir = +1 forward, -1 backward
    fn ramp(&mut self, dir: i32) {
        // TODO 4a: speed 10, 20, ... 80 %, each step held for 0.5 s,
        //          then back down 70, 60, ... 0 %, each held for 0.5 s
        //          (ranges: (10..=80).step_by(10), (0..=70).rev().step_by(10))
    }

    fn task4(&mut self) {
        // TODO 4b: wait for a click, LED on, ramp(+1), 1 s pause, ramp(-1),
        //   LED off. ET1 should end where it started: check D on the display
        //   and in the "ET1 stopped at" message.
        //
        // TODO 4c: real motors are never equal. In the simulator, click the
        //   ET1 chip and set "Left motor weaker by" to 10 %: ET1 now drives a
        //   curve (H changes). Add a trim factor to motor() for the left side
        //   so that ET1 drives straight again (H stays within +-5 degrees at
        //   the end of ramp(+1)); find the factor by trying. Make it a const.
    }
}

#[entry]
fn main() -> ! {
    let mut app = App {
        b: Board::init(),
        // TODO 2a: initial values of your fields
    };
    app.stop();
    writeln!(app.b.uart, "ET1 ready, task {TASK}\r").unwrap();
    loop {
        match TASK {
            2 => app.task2(),
            3 => app.task3(),
            4 => app.task4(),
            _ => {}
        }
        app.b.delay_ms(1);
    }
}
