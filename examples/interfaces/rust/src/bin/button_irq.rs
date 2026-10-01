//! Toggle the LED (GP15) from an interrupt on the falling edge of GP14.
//! Run it with button bouncing enabled: one press may toggle several times!
#![no_std]
#![no_main]

use core::cell::RefCell;
use critical_section::Mutex;
use embedded_hal::digital::StatefulOutputPin;
use panic_halt as _;
use rp_pico::hal::gpio::{self, Interrupt::EdgeLow};
use rp_pico::hal::pac::{self, interrupt};
use rp_pico::{entry, hal};

type LedPin = gpio::Pin<gpio::bank0::Gpio15, gpio::FunctionSioOutput, gpio::PullDown>;
type ButtonPin = gpio::Pin<gpio::bank0::Gpio14, gpio::FunctionSioInput, gpio::PullUp>;

// Hand-over from main() to the interrupt handler. The Mutex can only be
// accessed inside a critical section (interrupts disabled).
static SHARED: Mutex<RefCell<Option<(LedPin, ButtonPin)>>> = Mutex::new(RefCell::new(None));

#[entry]
fn main() -> ! {
    let mut pac = pac::Peripherals::take().unwrap();
    let sio = hal::Sio::new(pac.SIO);
    let pins = rp_pico::Pins::new(pac.IO_BANK0, pac.PADS_BANK0, sio.gpio_bank0, &mut pac.RESETS);

    let led = pins.gpio15.into_push_pull_output();
    let button = pins.gpio14.into_pull_up_input();
    button.set_interrupt_enabled(EdgeLow, true);

    critical_section::with(|cs| SHARED.borrow(cs).replace(Some((led, button))));

    // Enable the interrupt line of GPIO bank 0 in the NVIC.
    unsafe { pac::NVIC::unmask(pac::Interrupt::IO_IRQ_BANK0) };

    loop {
        cortex_m::asm::wfi(); // sleep until an interrupt arrives
    }
}

#[interrupt]
fn IO_IRQ_BANK0() {
    // Handler-local state: moved out of SHARED on the first call.
    static mut PINS: Option<(LedPin, ButtonPin)> = None;
    if PINS.is_none() {
        critical_section::with(|cs| *PINS = SHARED.borrow(cs).take());
    }
    if let Some((led, button)) = PINS {
        if button.interrupt_status(EdgeLow) {
            led.toggle().unwrap();
            button.clear_interrupt(EdgeLow); // otherwise the IRQ fires again at once
        }
    }
}
