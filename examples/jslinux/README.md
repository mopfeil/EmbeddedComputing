# Lightweight Linux exercises in the browser (JSLinux)

JSLinux (<https://bellard.org/jslinux/>) emulates a complete computer with
Linux in the browser. Nothing has to be installed.

| system in JSLinux | tools | exercise |
|---|---|---|
| Buildroot Linux (riscv64, console) | GCC 7.3, make, objdump, strace, vi, nano | `procinfo.c`: compile on the target, find a bug with `strace`, look at RISC-V code with `objdump` |
| Alpine Linux (x86_64, console) | GCC 15, Clang, TCC, GDB, gdbserver, strace, Python 3 | `average.c` (wrong result, watchpoint), `config.c` (crash, backtrace) |

Getting a program into the VM: type `cat > procinfo.c`, paste the source,
press Ctrl-D. Or open an editor (`nano procinfo.c`) and paste there.

```sh
# Buildroot (RISC-V)
gcc -g -O1 -o procinfo procinfo.c && ./procinfo
strace ./procinfo 2>&1 | grep proc
objdump -d procinfo | less          # search for <sum16>

# Alpine (x86_64)
gcc -g -O0 -o average average.c && gdb -q ./average
gcc -g -O0 -o config config.c && gdb -q ./config
```

In GDB inside the emulator use `set can-use-hw-watchpoints 0` before `watch`:
software watchpoints do not depend on emulated debug registers.

## What was checked

* The tool lists come from the file system index of the two JSLinux images
  (vfsync.org, October 2026); both systems remount their root file system
  writable at boot.
* The three programs and the GDB sessions on the slides were tested on an
  x86_64 Ubuntu PC (GCC 13, GDB 15, strace) - not inside JSLinux itself.
  Addresses and the load value will differ in JSLinux.
