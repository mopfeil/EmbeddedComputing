// Garage door controller: a hierarchical state machine (StateChart) with
// an orthogonal region (chapter Modelling). The door itself is the custom
// chip "door" (chips/door.chip.c), a model of the environment.
//
// Button (GP10) to GND: one button for everything, like a remote control.
// From the door: TOP (GP2), BOTTOM (GP3) end switches, BEAM (GP4) light barrier.
// To the door: motor UP (GP16), DOWN (GP17). Warning lamp (GP18).
//
//  ┌ DOOR ─────────────────────────────────────────────────────────────┐
//  │ CLOSED ─btn─► ┌ MOVING ──────────────────┐ ─after 8 s─► FAULT     │
//  │   ▲           │ OPENING ─top─► (OPEN)    │                        │
//  │   └─bottom─── │ CLOSING ─beam─► OPENING  │ ─btn─► STOPPED         │
//  │               └──────────────────────────┘                        │
//  │ OPEN ─btn or after 10 s [beam free]─► CLOSING                     │
//  │ STOPPED ─btn─► the direction it did not move last                 │
//  ├ LAMP (concurrent) ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┤
//  │ OFF ◄─after 250 ms [in MOVING]─► ON        steady ON in FAULT      │
//  └───────────────────────────────────────────────────────────────────┘

const int BTN = 10, TOP = 2, BOTTOM = 3, BEAM = 4;
const int MOTOR_UP = 16, MOTOR_DOWN = 17, LAMP = 18;

const uint32_t AUTO_CLOSE_MS = 10000;   // OPEN: close again after 10 s
const uint32_t MOTOR_TIMEOUT_MS = 8000; // MOVING: end switch must come within 8 s
const uint32_t BLINK_MS = 250;

// --------------------------------------------------------
// region DOOR
// --------------------------------------------------------
enum DoorState { CLOSED, OPENING, OPEN, CLOSING, STOPPED, FAULT, NUM_DOOR_STATES };
const char *const door_name[NUM_DOOR_STATES] = {
  "closed", "opening", "open", "closing", "stopped", "FAULT"
};

DoorState door = CLOSED;
uint32_t door_entered_ms;           // for the timed transitions "after(t)"
bool last_moved_up;                 // what STOPPED remembers

bool in_moving(DoorState s) {       // super-state MOVING = {OPENING, CLOSING}
  return s == OPENING || s == CLOSING;
}

// every transition goes through here: exit actions, then entry actions
void enter(DoorState next) {
  digitalWrite(MOTOR_UP, LOW);      // exit: motor off, so UP and DOWN
  digitalWrite(MOTOR_DOWN, LOW);    // are never on at the same time
  door = next;
  door_entered_ms = millis();
  if (next == OPENING) { digitalWrite(MOTOR_UP, HIGH); last_moved_up = true; }
  if (next == CLOSING) { digitalWrite(MOTOR_DOWN, HIGH); last_moved_up = false; }
  Serial1.printf("%6lu ms  door: %s\n", millis(), door_name[door]);
}

void door_tic(bool button, bool top, bool bottom, bool beam) {
  uint32_t t = millis() - door_entered_ms;
  // transitions of the super-state come first: they leave every sub-state
  if (in_moving(door) && t >= MOTOR_TIMEOUT_MS) { enter(FAULT); return; }

  switch (door) {
  case CLOSED:
    if (button) enter(OPENING);
    break;
  case OPENING:
    if (top) enter(OPEN);
    else if (button) enter(STOPPED);
    break;
  case OPEN:
    if ((button || t >= AUTO_CLOSE_MS) && !beam) enter(CLOSING);  // guard [beam free]
    break;
  case CLOSING:
    if (beam) enter(OPENING);             // safety first: reverse
    else if (bottom) enter(CLOSED);
    else if (button) enter(STOPPED);
    break;
  case STOPPED:
    if (button) enter(last_moved_up ? CLOSING : OPENING);
    break;
  case FAULT:
    if (button) enter(OPENING);           // acknowledge: try to open
    break;
  default:
    enter(STOPPED);                       // invalid state: motor off
  }
}

// --------------------------------------------------------
// region LAMP, runs concurrently with DOOR (AND-super-state)
// --------------------------------------------------------
enum LampState { LAMP_OFF, LAMP_ON };
LampState lamp = LAMP_OFF;
uint32_t lamp_entered_ms;

void lamp_tic() {
  LampState next = lamp;
  if (door == FAULT) next = LAMP_ON;                 // condition in(FAULT)
  else if (!in_moving(door)) next = LAMP_OFF;        // condition in(MOVING)
  else if (millis() - lamp_entered_ms >= BLINK_MS)
    next = (lamp == LAMP_ON) ? LAMP_OFF : LAMP_ON;
  if (next != lamp) { lamp = next; lamp_entered_ms = millis(); }
  digitalWrite(LAMP, lamp == LAMP_ON);
}

bool last_pressed;

void setup() {
  Serial1.begin(115200);
  pinMode(BTN, INPUT_PULLUP);
  pinMode(TOP, INPUT);
  pinMode(BOTTOM, INPUT);
  pinMode(BEAM, INPUT);
  pinMode(MOTOR_UP, OUTPUT);
  pinMode(MOTOR_DOWN, OUTPUT);
  pinMode(LAMP, OUTPUT);
  delay(10);                              // let the door model settle
  // initial state from the sensors, the door can be anywhere after a reset
  enter(digitalRead(BOTTOM) ? CLOSED : digitalRead(TOP) ? OPEN : STOPPED);
}

void loop() {
  bool pressed = digitalRead(BTN) == LOW;
  bool button = pressed && !last_pressed;  // event: edge released -> pressed
  last_pressed = pressed;
  door_tic(button, digitalRead(TOP), digitalRead(BOTTOM), digitalRead(BEAM));
  lamp_tic();                              // both regions get every tick
  delay(20);
}
