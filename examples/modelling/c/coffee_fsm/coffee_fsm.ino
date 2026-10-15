// Moore state machine of the coffee machine (chapter Modelling).
// Buttons LEFT (GP10), RIGHT (GP11) to GND;
// LEDs COFFEE (GP16), MILK (GP17), SUGAR (GP18).
// READY is not a button: a timer signals it when the brewing time is over.

// --------------------------------------------------------
// the FSM states
// --------------------------------------------------------
enum {
  FSM_STATE_IDLE, FSM_STATE_COFFEE, FSM_STATE_COFFEE_MILK,
  FSM_STATE_COFFEE_SUGAR, FSM_STATE_COFFEE_MILK_SUGAR,
  FSM_STATE_MAKE_COFFEE, FSM_STATE_MAKE_COFFEE_MILK,
  FSM_STATE_MAKE_COFFEE_SUGAR, FSM_STATE_MAKE_COFFEE_MILK_SUGAR,
  NUM_FSM_STATES
};
const char *const fsm_name[NUM_FSM_STATES] = {
  "idle", "coffee", "coffee+milk", "coffee+sugar", "coffee+milk+sugar",
  "make coffee", "make coffee+milk", "make coffee+sugar", "make coffee+milk+sugar"
};
// --------------------------------------------------------
// the FSM outputs, one per state (Moore machine)
// bit0: add coffee, bit1: add milk, bit2: add sugar
// --------------------------------------------------------
const uint8_t fsm_output[NUM_FSM_STATES] = {0, 0, 0, 0, 0, 1, 3, 5, 7};
// --------------------------------------------------------
// the FSM inputs
// --------------------------------------------------------
enum { FSM_INP_NONE = 0, FSM_INP_LEFT, FSM_INP_RIGHT, FSM_INP_READY };

const uint32_t BREW_TIME_MS = 3000;  // READY comes 3 s after a MAKE state is entered

int fsm_state = FSM_STATE_IDLE;

int fsm_tic(int fsm_inp) {        // called periodically, every 50 ms
  switch (fsm_state) {
  case FSM_STATE_IDLE:
    if (fsm_inp == FSM_INP_LEFT) fsm_state = FSM_STATE_COFFEE_MILK;
    if (fsm_inp == FSM_INP_RIGHT) fsm_state = FSM_STATE_COFFEE;
    break;
  case FSM_STATE_COFFEE:
    if (fsm_inp == FSM_INP_LEFT) fsm_state = FSM_STATE_MAKE_COFFEE;
    if (fsm_inp == FSM_INP_RIGHT) fsm_state = FSM_STATE_COFFEE_SUGAR;
    break;
  case FSM_STATE_COFFEE_MILK:
    if (fsm_inp == FSM_INP_LEFT) fsm_state = FSM_STATE_MAKE_COFFEE_MILK;
    if (fsm_inp == FSM_INP_RIGHT) fsm_state = FSM_STATE_COFFEE_MILK_SUGAR;
    break;
  case FSM_STATE_COFFEE_SUGAR:
    if (fsm_inp == FSM_INP_LEFT) fsm_state = FSM_STATE_IDLE;
    if (fsm_inp == FSM_INP_RIGHT) fsm_state = FSM_STATE_MAKE_COFFEE_SUGAR;
    break;
  case FSM_STATE_COFFEE_MILK_SUGAR:
    if (fsm_inp == FSM_INP_LEFT) fsm_state = FSM_STATE_IDLE;
    if (fsm_inp == FSM_INP_RIGHT) fsm_state = FSM_STATE_MAKE_COFFEE_MILK_SUGAR;
    break;
  case FSM_STATE_MAKE_COFFEE:        // wait until the coffee is ready
  case FSM_STATE_MAKE_COFFEE_MILK:
  case FSM_STATE_MAKE_COFFEE_SUGAR:
  case FSM_STATE_MAKE_COFFEE_MILK_SUGAR:
    if (fsm_inp == FSM_INP_READY) fsm_state = FSM_STATE_IDLE;
    break;
  default:
    fsm_state = FSM_STATE_IDLE;      // invalid state: back to a safe state
  }
  return fsm_output[fsm_state];      // Moore FSM: one output per state
}

const int BTN[2] = {10, 11};                   // LEFT, RIGHT
const int LED_COFFEE = 16, LED_MILK = 17, LED_SUGAR = 18;
bool last_pressed[2];
uint32_t state_entered_ms;                     // time of the last state change

void setup() {
  Serial1.begin(115200);
  for (int i = 0; i < 2; i++) pinMode(BTN[i], INPUT_PULLUP);
  pinMode(LED_COFFEE, OUTPUT);
  pinMode(LED_MILK, OUTPUT);
  pinMode(LED_SUGAR, OUTPUT);
  Serial1.printf("state: %s\n", fsm_name[fsm_state]);
}

void loop() {
  // input: a button press (edge released -> pressed) becomes one event;
  // sampling every 50 ms also filters the contact bounce
  int inp = FSM_INP_NONE;
  for (int i = 0; i < 2; i++) {
    bool pressed = digitalRead(BTN[i]) == LOW;
    if (pressed && !last_pressed[i]) inp = FSM_INP_LEFT + i;
    last_pressed[i] = pressed;
  }
  // timer: the brewing time is over -> event READY (only MAKE states react)
  if (fsm_state >= FSM_STATE_MAKE_COFFEE && millis() - state_entered_ms >= BREW_TIME_MS)
    inp = FSM_INP_READY;
  int old_state = fsm_state;
  int out = fsm_tic(inp);
  if (fsm_state != old_state) state_entered_ms = millis();  // restart the timer
  digitalWrite(LED_COFFEE, out & 1);
  digitalWrite(LED_MILK, (out >> 1) & 1);
  digitalWrite(LED_SUGAR, (out >> 2) & 1);
  if (fsm_state != old_state) Serial1.printf("state: %s\n", fsm_name[fsm_state]);
  delay(50);
}
