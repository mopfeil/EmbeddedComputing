/* Memory layout of the RP2040 on the Raspberry Pi Pico (2 MB flash) */
MEMORY {
    BOOT2 : ORIGIN = 0x10000000, LENGTH = 0x100           /* 2nd stage bootloader */
    FLASH : ORIGIN = 0x10000100, LENGTH = 2048K - 0x100
    RAM   : ORIGIN = 0x20000000, LENGTH = 256K
}

EXTERN(BOOT2_FIRMWARE)

SECTIONS {
    .boot2 ORIGIN(BOOT2) :
    {
        KEEP(*(.boot2));
    } > BOOT2
} INSERT BEFORE .text;
