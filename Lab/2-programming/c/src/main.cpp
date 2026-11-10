// Lab task 2: programming the ET1 robot - C version (Arduino-Pico core)
//
// Build: PlatformIO check mark or Terminal > Run Build Task, then
// F1 -> "Wokwi: Start Simulator". Output: serial monitor (Serial1, 115200 baud).
//
// Work through the TODOs in the order of their numbers. Set TASK to the task
// you are working on; loop() then runs that task over and over.

#include <Arduino.h>

#define TASK 2          // 2, 3 or 4 (task 1 is used by 3 and 4, task 5 extends 3 and 4)

// ---- given: wiring (see diagram.json) -----------------------------------
const int LED = 7;      // red LED, high = on
const int BUTTON = 5;   // START button to GND, internal pull-up: LOW = pressed

const int ENA = 18, IN1 = 17, IN2 = 16;   // left motor:  PWM, direction A, direction B
const int ENB = 19, IN3 = 20, IN4 = 21;   // right motor: PWM, direction A, direction B

enum Side { LEFT, RIGHT };

// raw level of the button, without debouncing
bool button_down() { return digitalRead(BUTTON) == LOW; }

// =========================================================================
// Task 1: motor driver
// =========================================================================
// speed in percent: -100 = full speed backward, 0 = brake, +100 = full forward.
// The H-bridge:  IN1 IN2 = 1 0 forward,  0 1 backward,  0 0 brake
// (IN3/IN4 the same for the right motor); the speed is the PWM duty cycle on
// ENA / ENB. setup() has set the PWM range to 0..100, so analogWrite(ENA, 50)
// gives 50 %.
void motor(Side side, int speed) {
  // TODO 1a: limit speed to -100..100 (a caller may pass 150)

  // TODO 1b: pick the three pins of this side (ENA/IN1/IN2 or ENB/IN3/IN4)

  // TODO 1c: set the two direction pins from the sign of speed

  // TODO 1d: write the magnitude of speed to the PWM pin
  (void)side;
  (void)speed;
}

void stop() {
  motor(LEFT, 0);
  motor(RIGHT, 0);
}

// =========================================================================
// Task 2: button and LED
// =========================================================================
// Returns true exactly once per press: when the button goes from released to
// pressed. Call it often (every millisecond or so).
bool button_clicked() {
  // TODO 2a: remember the previous state of the button in a static variable
  //          and return true only on the change released -> pressed

  // TODO 2b: the contacts bounce: ignore changes that come less than 30 ms
  //          after the last accepted change (millis())
  return false;
}

void task2() {
  // TODO 2c: every click toggles the LED; print "LED on" / "LED off"
  //          to Serial1. Check: holding the button down toggles only once.
}

// =========================================================================
// Task 5: emergency stop (do this after tasks 3 and 4)
// =========================================================================
// Waits ms milliseconds. Returns true if the time has passed and false if the
// button was clicked during the wait.
bool wait_ms(uint32_t ms) {
  // TODO 5a: replace delay() by a loop that runs until ms have passed and
  //          checks button_clicked() every millisecond. On a click: stop the
  //          motors, print "EMERGENCY STOP" and return false at once.
  delay(ms);
  return true;
}

// TODO 5b: use wait_ms() in task 3 and task 4 for every wait while the robot
//          moves. When it returns false, end the whole sequence at once
//          (motors off, LED off) - a second click during the drive stops ET1.

// =========================================================================
// Task 3: turning
// =========================================================================
void task3() {
  // TODO 3: wait for a click (button_clicked()), then:
  //   - LED on
  //   - only the left wheel drives forward at 50 % for 10 s
  //     (the right one brakes: ET1 turns around the right wheel)
  //   - then only the right wheel at 50 % for 10 s
  //   - stop, LED off, print the time the sequence took (millis())
  //   Watch the track on the display: which way does ET1 turn first?
}

// =========================================================================
// Task 4: accelerate and brake
// =========================================================================
// dir = +1 forward, -1 backward
void ramp(int dir) {
  // TODO 4a: speed 10, 20, ... 80 %, each step held for 0.5 s,
  //          then back down 70, 60, ... 0 %, each held for 0.5 s
  (void)dir;
}

void task4() {
  // TODO 4b: wait for a click, LED on, ramp(+1), 1 s pause, ramp(-1), LED off.
  //   ET1 should end where it started: check D on the display and in the
  //   "ET1 stopped at" message.
  //
  // TODO 4c: real motors are never equal. In the simulator, click the ET1
  //   chip and set "Left motor weaker by" to 10 %: ET1 now drives a curve
  //   (H changes). Add a trim factor to motor() for the left side so that
  //   ET1 drives straight again (H stays within +-5 degrees at the end of
  //   ramp(+1)); find the factor by trying. Make it a constant at the top.
}

// ---- given ----------------------------------------------------------------
void setup() {
  Serial1.begin(115200);
  pinMode(LED, OUTPUT);
  pinMode(BUTTON, INPUT_PULLUP);
  const int dir_pins[] = {IN1, IN2, IN3, IN4};
  for (int pin : dir_pins) pinMode(pin, OUTPUT);
  analogWriteFreq(1000);    // PWM 1 kHz on ENA and ENB
  analogWriteRange(100);    // analogWrite(pin, 0..100) = 0..100 % duty cycle
  stop();
  Serial1.printf("ET1 ready, task %d\n", TASK);
}

void loop() {
  if (TASK == 2) task2();
  if (TASK == 3) task3();
  if (TASK == 4) task4();
  delay(1);
}
