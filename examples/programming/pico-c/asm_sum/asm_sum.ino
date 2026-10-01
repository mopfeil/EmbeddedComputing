// Calling an assembly function from C: asm_sum() is in sum_m0.S.
// The result is compared with the same function in C.
extern "C" uint32_t asm_sum(const uint16_t *a, int n);   // C linkage!

uint32_t c_sum(const uint16_t *a, int n) {
  uint32_t s = 0;
  for (int i = 0; i < n; i++) s += a[i];
  return s;
}

void setup() {
  Serial1.begin(115200);
  const uint16_t data[] = {1, 2, 3, 1000, 60000, 65535};
  Serial1.printf("asm_sum = %lu\n", (unsigned long)asm_sum(data, 6));
  Serial1.printf("c_sum   = %lu\n", (unsigned long)c_sum(data, 6));

  // Inline assembly (GCC syntax): read the stack pointer
  uint32_t sp;
  asm volatile("mov %0, sp" : "=r"(sp));
  Serial1.printf("sp = 0x%08lx\n", (unsigned long)sp);
}

void loop() {}
