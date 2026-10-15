// Pedestrian crossing: a StateChart with an AND-super-state (chapter Modelling).
//
// Request button (GP10) to GND, night switch (GP11, to GND = night).
// Cars: RED (GP16), YELLOW (GP17), GREEN (GP18).
// Pedestrians: RED (GP19), GREEN (GP20), WAIT signal (GP21).
//
//  ┌ OPERATING ───────────────────────────────────────────────────────┐
//  │ ┌ DAY (AND) ─────────────────────────────────────────────┐       │
//  │ │ TRAFFIC: RED_YELLOW ─1s─► GREEN ─[in(WAITING)], ≥5s─►  │       │
//  │ │   YELLOW ─2s─► ALL_RED ─1s─► WALK ─5s─► CLEAR ─2s─►    │       │
//  │ │   RED_YELLOW                                           │       │
//  │ │─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│       │
//  │ │ REQUEST: IDLE ─button─► WAITING ─[in(WALK)]─► IDLE     │       │
//  │ └────────────────────────────────────────────────────────┘       │
//  │   DAY ─night [in(GREEN)]─► NIGHT    NIGHT ─day─► DAY             │
//  │ ┌ NIGHT ─────────────────────┐                                   │
//  │ │ BLINK_ON ◄─0.5s─► BLINK_OFF │  cars: yellow flashing           │
//  │ └────────────────────────────┘  pedestrians: dark                │
//  └──────────────────────────────────────────────────────────────────┘

const int BTN = 10, NIGHT_SW = 11;
const int CAR_RED = 16, CAR_YELLOW = 17, CAR_GREEN = 18;
const int PED_RED = 19, PED_GREEN = 20, WAIT_LED = 21;

// --------------------------------------------------------
// the states: one variable per OR-super-state / region
// --------------------------------------------------------
enum Mode { DAY, NIGHT };                         // OR-super-state OPERATING
enum Traffic { RED_YELLOW, GREEN, YELLOW, ALL_RED, WALK, CLEAR, NUM_TRAFFIC };
enum Request { IDLE, WAITING };                   // region REQUEST in DAY
enum Blink { BLINK_ON, BLINK_OFF };               // sub-states of NIGHT

const char *const traffic_name[NUM_TRAFFIC] = {
  "red+yellow", "green", "yellow", "all red", "walk", "clear"
};
// how long each traffic state lasts at least (ms)
const uint32_t traffic_time[NUM_TRAFFIC] = {1000, 5000, 2000, 1000, 5000, 2000};

// --------------------------------------------------------
// the outputs, one per state (Moore machine)
// bits: car red, car yellow, car green, ped red, ped green
// --------------------------------------------------------
const uint8_t traffic_output[NUM_TRAFFIC] = {
  0b01011,   // RED_YELLOW: cars red+yellow, pedestrians red
  0b01100,   // GREEN
  0b01010,   // YELLOW
  0b01001,   // ALL_RED
  0b10001,   // WALK: cars red, pedestrians green
  0b01001,   // CLEAR: everybody red, the crossing empties
};

Mode mode = DAY;
Traffic traffic = RED_YELLOW;
Request request = IDLE;
Blink blink = BLINK_ON;
uint32_t traffic_entered_ms, blink_entered_ms;

void set_traffic(Traffic s) {
  traffic = s;
  traffic_entered_ms = millis();
  Serial1.printf("%6lu ms  traffic: %s\n", millis(), traffic_name[s]);
}

// region TRAFFIC: reads the state of region REQUEST
void traffic_tic() {
  bool time_up = millis() - traffic_entered_ms >= traffic_time[traffic];
  switch (traffic) {
  case RED_YELLOW: if (time_up) set_traffic(GREEN); break;
  case GREEN:      if (time_up && request == WAITING) set_traffic(YELLOW); break;
  case YELLOW:     if (time_up) set_traffic(ALL_RED); break;
  case ALL_RED:    if (time_up) set_traffic(WALK); break;
  case WALK:       if (time_up) set_traffic(CLEAR); break;
  case CLEAR:      if (time_up) set_traffic(RED_YELLOW); break;
  default:         set_traffic(ALL_RED);           // invalid: everybody stops
  }
}

// region REQUEST: reads the state of region TRAFFIC
void request_tic(bool button) {
  switch (request) {
  case IDLE:
    if (button && traffic != WALK) {
      request = WAITING;
      Serial1.printf("%6lu ms  request: waiting\n", millis());
    }
    break;
  case WAITING:
    if (traffic == WALK) {
      request = IDLE;
      Serial1.printf("%6lu ms  request: idle\n", millis());
    }
    break;
  }
}

void blink_tic() {
  if (millis() - blink_entered_ms >= 500) {
    blink = (blink == BLINK_ON) ? BLINK_OFF : BLINK_ON;
    blink_entered_ms = millis();
  }
}

// top level: the OR-super-state OPERATING with DAY and NIGHT
void crossing_tic(bool button, bool night) {
  switch (mode) {
  case DAY:
    if (night && traffic == GREEN) {               // leave DAY only in a safe sub-state
      mode = NIGHT;
      blink = BLINK_ON;
      blink_entered_ms = millis();
      Serial1.printf("%6lu ms  mode: night\n", millis());
      return;
    }
    traffic_tic();                                 // AND: both regions run
    request_tic(button);                           // in every tick
    break;
  case NIGHT:
    if (!night) {
      mode = DAY;                                  // enter DAY in its initial states
      request = IDLE;
      Serial1.printf("%6lu ms  mode: day\n", millis());
      set_traffic(RED_YELLOW);
      return;
    }
    blink_tic();
    break;
  }
}

void write_outputs() {
  uint8_t out = 0;
  if (mode == DAY) out = traffic_output[traffic];
  else if (blink == BLINK_ON) out = 0b00010;     // night: only car yellow
  digitalWrite(CAR_RED, out & 1);
  digitalWrite(CAR_YELLOW, (out >> 1) & 1);
  digitalWrite(CAR_GREEN, (out >> 2) & 1);
  digitalWrite(PED_RED, (out >> 3) & 1);
  digitalWrite(PED_GREEN, (out >> 4) & 1);
  digitalWrite(WAIT_LED, mode == DAY && request == WAITING);
}

bool last_pressed;

void setup() {
  Serial1.begin(115200);
  pinMode(BTN, INPUT_PULLUP);
  pinMode(NIGHT_SW, INPUT_PULLUP);
  for (int pin = CAR_RED; pin <= WAIT_LED; pin++) pinMode(pin, OUTPUT);
  set_traffic(RED_YELLOW);                         // initial state
}

void loop() {
  bool pressed = digitalRead(BTN) == LOW;
  bool button = pressed && !last_pressed;          // event: edge released -> pressed
  last_pressed = pressed;
  crossing_tic(button, digitalRead(NIGHT_SW) == LOW);
  write_outputs();
  delay(20);
}
