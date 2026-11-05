"""Build one .uf2 file: MicroPython firmware + a file system containing main.py.

The Wokwi simulator in VS Code loads a firmware file, but has no way to copy
main.py onto the Pico. This script does what Wokwi in the browser does: it
creates the LittleFS file system of MicroPython with main.py inside and
appends it to the firmware. The Pico then runs main.py after reset.

    python make_uf2.py                 # downloads MicroPython once, writes build/main.uf2

Needs: pip install littlefs-python   (see ../requirements.txt)
"""
import pathlib
import struct
import sys
import urllib.request

from littlefs import LittleFS

FIRMWARE_URL = "https://micropython.org/resources/firmware/RPI_PICO-20260824-v1.29.0.uf2"
FS_START = 0x10000000 + (2048 - 1408) * 1024   # RPI_PICO: last 1408 KB of the 2 MB flash
BLOCK = 4096
FAMILY_RP2040 = 0xE48BFF56

here = pathlib.Path(__file__).parent
build = here / "build"
build.mkdir(exist_ok=True)
firmware = build / pathlib.Path(FIRMWARE_URL).name
if not firmware.exists():
    print("downloading", FIRMWARE_URL)
    urllib.request.urlretrieve(FIRMWARE_URL, firmware)

# 1. LittleFS image with main.py (and any further .py files given on the command line)
fs = LittleFS(block_size=BLOCK, block_count=1408 * 1024 // BLOCK,
              read_size=32, prog_size=256, lookahead_size=32)   # as rp2 _boot.py
for f in [here / "main.py"] + [pathlib.Path(p) for p in sys.argv[1:]]:
    with fs.open(f.name, "wb") as out:
        out.write(f.read_bytes())
image = bytes(fs.context.buffer).rstrip(b"\xff")
image += b"\xff" * (-len(image) % 256)

# 2. convert the image to UF2 blocks (256 data bytes each) and append them
old = firmware.read_bytes()
old_blocks = [old[i:i + 512] for i in range(0, len(old), 512)]
data = [image[i:i + 256] for i in range(0, len(image), 256)]
total = len(old_blocks) + len(data)
blocks = []
for n, blk in enumerate(old_blocks):                      # renumber firmware blocks
    blocks.append(blk[:20] + struct.pack("<II", n, total) + blk[28:])
for n, chunk in enumerate(data, start=len(old_blocks)):
    header = struct.pack("<IIIIIIII", 0x0A324655, 0x9E5D5157, 0x2000,
                         FS_START + (n - len(old_blocks)) * 256, 256, n, total, FAMILY_RP2040)
    blocks.append(header + chunk + b"\x00" * (476 - 256) + struct.pack("<I", 0x0AB16F30))

out = build / "main.uf2"
out.write_bytes(b"".join(blocks))
print(f"{out}: firmware + {len(image) // 1024} KB file system with main.py")
