"""Decode a register dump of the MPU6050 (as read in the I2C example of
chapter 6) on the PC. Runs with any Python 3 (PC, Replit).

Shows: bytes objects, struct for binary data, f-strings, list comprehensions.
"""
import struct

# 14 bytes from register 0x3B: accel X/Y/Z, temperature, gyro X/Y/Z
# (big endian 16 bit signed values, as sent by the sensor)
raw = bytes.fromhex("0000 0000 4000 f24c 0000 0083 ff7d")

ax, ay, az, temp, gx, gy, gz = struct.unpack(">7h", raw)   # > = big endian, h = int16

accel_g = [v / 16384 for v in (ax, ay, az)]      # +-2 g range: 16384 LSB/g
gyro_dps = [v / 131 for v in (gx, gy, gz)]       # +-250 deg/s: 131 LSB/(deg/s)
temp_c = temp / 340 + 36.53                      # formula from the datasheet

print(f"acceleration: {accel_g} g")
print(f"rotation:     {[round(v, 2) for v in gyro_dps]} deg/s")
print(f"temperature:  {temp_c:.1f} C")

# The other direction: build an I2C write "register 0x6B := 0x00"
packet = struct.pack("BB", 0x6B, 0x00)
print("packet:", packet.hex(" "))
