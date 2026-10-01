// Read the MPU6050 acceleration sensor over I2C0 (GP4 = SDA, GP5 = SCL).
#include "hardware/i2c.h"

const uint8_t MPU6050 = 0x68;           // 7 bit address (AD0 = low)
const uint8_t REG_ACCEL_XOUT_H = 0x3B;
const uint8_t REG_PWR_MGMT_1 = 0x6B;
const uint8_t REG_WHO_AM_I = 0x75;

// Register read: write the register address without STOP,
// then read with a repeated START.
void readRegs(uint8_t reg, uint8_t *buf, size_t len) {
  i2c_write_blocking(i2c0, MPU6050, &reg, 1, true);   // true = no STOP
  i2c_read_blocking(i2c0, MPU6050, buf, len, false);
}

void setup() {
  Serial1.begin(115200);
  i2c_init(i2c0, 400 * 1000);           // fast mode, 400 kHz
  gpio_set_function(4, GPIO_FUNC_I2C);
  gpio_set_function(5, GPIO_FUNC_I2C);
  gpio_pull_up(4);                      // open drain: pull-ups required
  gpio_pull_up(5);                      // (real boards: external 4.7 kOhm)

  uint8_t id;
  readRegs(REG_WHO_AM_I, &id, 1);
  Serial1.printf("WHO_AM_I = 0x%02X\n", id);

  uint8_t wake[] = {REG_PWR_MGMT_1, 0x00};  // leave sleep mode
  i2c_write_blocking(i2c0, MPU6050, wake, 2, false);
}

void loop() {
  uint8_t b[6];
  readRegs(REG_ACCEL_XOUT_H, b, 6);         // burst read X, Y, Z
  int32_t a[3];
  for (int i = 0; i < 3; i++) {
    int16_t v = (int16_t)(b[2 * i] << 8 | b[2 * i + 1]);   // big endian
    a[i] = v * 1000L / 16384;               // +-2 g range: 16384 LSB/g
  }
  Serial1.printf("ax = %5ld mg  ay = %5ld mg  az = %5ld mg\n",
                 (long)a[0], (long)a[1], (long)a[2]);
  sleep_ms(500);
}
