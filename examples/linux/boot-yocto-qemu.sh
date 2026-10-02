#!/bin/sh
# Download a prebuilt Yocto image for the emulated ARM64 board "qemuarm64"
# and boot it in QEMU - no hardware, no Yocto build needed.
# Needs: qemu-system-aarch64, curl, zstd   (Ubuntu/Debian: see README.md)
# Log in as "root" (no password). Leave QEMU with Ctrl-A, then X.
set -e
REL=${REL:-yocto-6.0.3}
IMG=${IMG:-core-image-minimal}         # or core-image-full-cmdline (with ssh)
URL=https://downloads.yoctoproject.org/releases/yocto/$REL/machines/qemu/qemuarm64
[ -f Image-qemuarm64.bin ] || curl -fLO $URL/Image-qemuarm64.bin
[ -f $IMG-qemuarm64.rootfs.ext4 ] || { curl -fLO $URL/$IMG-qemuarm64.rootfs.ext4.zst; zstd -d $IMG-qemuarm64.rootfs.ext4.zst; }

# -nic user: QEMU's own NAT network; port 2222 on the PC -> port 22 in the guest
exec qemu-system-aarch64 -machine virt -cpu cortex-a57 -m 256 -nographic \
  -kernel Image-qemuarm64.bin \
  -drive id=disk0,file=$IMG-qemuarm64.rootfs.ext4,if=none,format=raw \
  -device virtio-blk-pci,drive=disk0 \
  -nic user,model=virtio-net-pci,hostfwd=tcp::2222-:22 \
  -append "root=/dev/vda rw console=ttyAMA0 swiotlb=0 ip=dhcp" "$@"
