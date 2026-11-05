//! Board set-up shared by the corrected program (src/main.rs) and the
//! rejected one (examples/dangling.rs): clocks, UART0 on GP0/GP1, heap.
#![no_std]

extern crate alloc;

use embedded_alloc::LlffHeap as Heap;
use rp_pico::hal::fugit::RateExtU32;
use rp_pico::hal::uart::{DataBits, Enabled, StopBits, UartConfig, UartPeripheral};
use rp_pico::hal::{Clock, gpio};
use rp_pico::{hal, hal::pac};

#[global_allocator]
static HEAP: Heap = Heap::empty();

pub type Uart = UartPeripheral<
    Enabled,
    pac::UART0,
    (
        gpio::Pin<gpio::bank0::Gpio0, gpio::FunctionUart, gpio::PullDown>,
        gpio::Pin<gpio::bank0::Gpio1, gpio::FunctionUart, gpio::PullDown>,
    ),
>;

/// Initialises a 16 KB heap and the UART, returns the UART for writeln!().
pub fn init() -> Uart {
    {
        use core::mem::MaybeUninit;
        const HEAP_SIZE: usize = 16 * 1024;
        static mut HEAP_MEM: [MaybeUninit<u8>; HEAP_SIZE] = [MaybeUninit::uninit(); HEAP_SIZE];
        unsafe { HEAP.init(&raw mut HEAP_MEM as usize, HEAP_SIZE) }
    }
    let mut pac = pac::Peripherals::take().unwrap();
    let mut watchdog = hal::Watchdog::new(pac.WATCHDOG);
    let clocks = hal::clocks::init_clocks_and_plls(
        rp_pico::XOSC_CRYSTAL_FREQ, pac.XOSC, pac.CLOCKS, pac.PLL_SYS, pac.PLL_USB,
        &mut pac.RESETS, &mut watchdog,
    )
    .ok()
    .unwrap();
    let sio = hal::Sio::new(pac.SIO);
    let pins = rp_pico::Pins::new(pac.IO_BANK0, pac.PADS_BANK0, sio.gpio_bank0, &mut pac.RESETS);
    let uart_pins = (
        pins.gpio0.into_function::<gpio::FunctionUart>(),
        pins.gpio1.into_function::<gpio::FunctionUart>(),
    );
    UartPeripheral::new(pac.UART0, uart_pins, &mut pac.RESETS)
        .enable(
            UartConfig::new(115_200.Hz(), DataBits::Eight, None, StopBits::One),
            clocks.peripheral_clock.freq(),
        )
        .unwrap()
}
