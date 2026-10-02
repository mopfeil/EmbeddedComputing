# Embedded Linux without hardware (chapters Operating Systems and Programming)

Wokwi simulates microcontrollers only. For embedded Linux we use QEMU, which
emulates complete computers, together with the prebuilt images and SDKs of the
Yocto Project. Everything runs on a Linux PC or in a GitHub Codespace
(the repository contains `.devcontainer/devcontainer.json` with all tools).

Tools on Ubuntu/Debian:

```sh
sudo apt install qemu-system-arm qemu-user qemu-utils gdb-multiarch curl zstd \
                 chrpath diffstat lz4 python3-venv file
```

## Level 1 - in the browser

<https://bellard.org/jslinux/> -> "Buildroot Linux" (riscv64, console).
Commands: see the slide "an embedded Linux in the browser".

## Level 2 - boot a prebuilt Yocto image

```sh
./boot-yocto-qemu.sh                               # core-image-minimal, login: root
IMG=core-image-full-cmdline ./boot-yocto-qemu.sh   # with SSH on port 2222
```

Leave QEMU with Ctrl-A, then X.

## Level 3 - look inside Yocto without building

```sh
python3 -m venv venv && . venv/bin/activate && pip install bitbake-setup
bitbake-setup init --non-interactive poky-wrynose poky distro/poky machine/qemuarm64
. bitbake-builds/poky-wrynose/build/init-build-env
bitbake-layers show-layers
bitbake -e core-image-minimal | grep -E '^(IMAGE_INSTALL|MACHINE|TUNE_FEATURES)='
bitbake -g core-image-minimal && wc -l pn-buildlist
```

BitBake needs user namespaces. In Codespaces the dev container is privileged
for this reason; on an Ubuntu 24.04 PC run
`sudo sysctl kernel.apparmor_restrict_unprivileged_userns=0` (until reboot).

## Level 4 - cross-compile and debug with the Yocto SDK

```sh
SDK=poky-glibc-x86_64-core-image-sato-cortexa57-qemuarm64-toolchain-6.0.3.sh
curl -fLO https://downloads.yoctoproject.org/releases/yocto/yocto-6.0.3/toolchain/x86_64/$SDK
sh $SDK -y -d ~/sdk                                  # ~830 MB download, 5.3 GB installed
. ~/sdk/environment-setup-cortexa57-poky-linux
$CC -g -Og -o sensor_avg sensor_avg.c
qemu-aarch64 -L $SDKTARGETSYSROOT ./sensor_avg       # average = 8 (expected 200)

qemu-aarch64 -L $SDKTARGETSYSROOT -g 1234 ./sensor_avg &
$GDB -ex "set sysroot $SDKTARGETSYSROOT" -ex "target remote :1234" ./sensor_avg
```

On the emulated board (`IMG=core-image-full-cmdline ./boot-yocto-qemu.sh`):

```sh
scp -P 2222 sensor_avg root@localhost:/tmp/
ssh -p 2222 root@localhost /tmp/sensor_avg
```

## Level 5 - build an image

Needs a large machine (Yocto documentation: 32 GB RAM, 140 GB disk) and hours.
`bitbake-config-build enable-fragment core/yocto/sstate-mirror-cdn` reuses
prebuilt results, but for the current branch only 11 % of the tasks were
available in our test.

## Tested (October 2026, Ubuntu 24.04 host, 2 cores, no KVM, QEMU 8.2)

* Level 2: `core-image-minimal` and `core-image-full-cmdline` of Yocto 6.0.3
  boot to the login prompt in 1-2 minutes; SSH, scp work with `ip=dhcp`.
* Level 3: all commands, 273 recipes for `core-image-minimal`, parse in about
  4 minutes. (The namespace check had to be skipped on the test host because
  of AppArmor - in a privileged container it is not needed.)
* Level 4: SDK installation, cross-compilation, QEMU user mode, GDB session,
  scp/ssh to the emulated board.
* Level 5: started with the sstate mirror; not completed on the test host
  (namespace restriction, too few cores).
* Level 1 and the Codespaces dev container were not tested by us.
