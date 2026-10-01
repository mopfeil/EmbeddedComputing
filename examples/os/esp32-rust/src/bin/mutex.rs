//! Two tasks increment a shared counter 1000 times each. The read-modify-
//! write sequence contains an await, so the other task can run in between.
//! The async Mutex makes the sequence exclusive: the result is always 2000.
//! (Without the Mutex, Rust does not even let us write to the shared
//! variable without `unsafe`.)
#![no_std]
#![no_main]

use embassy_executor::Spawner;
use embassy_sync::blocking_mutex::raw::CriticalSectionRawMutex;
use embassy_sync::mutex::Mutex;
use embassy_sync::channel::Channel;
use embassy_time::{Duration, Timer};
use esp_backtrace as _;
use esp_hal::timer::timg::TimerGroup;
use esp_println::println;

esp_bootloader_esp_idf::esp_app_desc!();

static COUNTER: Mutex<CriticalSectionRawMutex, u32> = Mutex::new(0);
static DONE: Channel<CriticalSectionRawMutex, u32, 2> = Channel::new(); // "finished" messages

#[embassy_executor::task(pool_size = 2)]
async fn worker(id: u32) {
    for _ in 0..1000 {
        let mut counter = COUNTER.lock().await; // wait until the mutex is free
        let value = *counter; // read
        Timer::after(Duration::from_micros(10)).await; // other task may run now
        *counter = value + 1; // modify-write
    } // guard dropped here -> mutex released
    println!("worker {id} finished");
    DONE.send(id).await;
}

#[esp_rtos::main]
async fn main(spawner: Spawner) -> ! {
    let peripherals = esp_hal::init(esp_hal::Config::default());
    let timg0 = TimerGroup::new(peripherals.TIMG0);
    esp_rtos::start(timg0.timer0, peripherals.FROM_CPU_INTR0);

    spawner.spawn(worker(1).unwrap());
    spawner.spawn(worker(2).unwrap());

    DONE.receive().await;
    DONE.receive().await;
    println!("counter = {} (expected 2000)", *COUNTER.lock().await);

    loop {
        Timer::after_secs(3600).await;
    }
}
