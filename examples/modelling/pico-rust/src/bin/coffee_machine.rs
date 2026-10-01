//! The coffee machine on the Pico: buttons LEFT (GP10), RIGHT (GP11),
//! READY (GP12); LEDs COFFEE (GP16), MILK (GP17), SUGAR (GP18).
//! The state machine itself is the hardware independent crate `coffee-fsm`.
#![no_std]
#![no_main]

use coffee_fsm::{Input, State};
use core::fmt::Write;
use embedded_hal::delay::DelayNs;
use embedded_hal::digital::{InputPin, OutputPin, PinState};
use panic_halt as _;
use rp_pico::hal::fugit::RateExtU32;
use rp_pico::hal::uart::{DataBits, StopBits, UartConfig, UartPeripheral};
use rp_pico::hal::{Clock, gpio};
use rp_pico::{entry, hal, hal::pac};

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
    let mut delay = hal::Timer::new(pac.TIMER, &mut pac.RESETS, &clocks);
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

    let mut left = pins.gpio10.into_pull_up_input();
    let mut right = pins.gpio11.into_pull_up_input();
    let mut ready = pins.gpio12.into_pull_up_input();
    let mut led_coffee = pins.gpio16.into_push_pull_output();
    let mut led_milk = pins.gpio17.into_push_pull_output();
    let mut led_sugar = pins.gpio18.into_push_pull_output();

    let mut state = State::Idle;
    let mut last = [false; 3];
    writeln!(uart, "state: {state:?}\r").unwrap();

    loop {
        // a press (edge released -> pressed) becomes one input event;
        // sampling every 50 ms also filters the contact bounce
        let now = [left.is_low().unwrap(), right.is_low().unwrap(), ready.is_low().unwrap()];
        let events = [Input::Left, Input::Right, Input::Ready];
        let input = (0..3).find(|&i| now[i] && !last[i]).map(|i| events[i]);
        last = now;

        if let Some(input) = input {
            let next = state.next(input);
            if next != state {
                state = next;
                writeln!(uart, "state: {state:?}\r").unwrap();
            }
        }
        let out = state.output(); // Moore: output depends on the state only
        led_coffee.set_state(PinState::from(out.coffee)).unwrap();
        led_milk.set_state(PinState::from(out.milk)).unwrap();
        led_sugar.set_state(PinState::from(out.sugar)).unwrap();
        delay.delay_ms(50);
    }
}
