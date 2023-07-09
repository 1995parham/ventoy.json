# ventoy.json

## Introduction

[ventoy](https://www.ventoy.net/en/index.html) is A New Bootable USB Solution and here is
my configuration on it to have theme and also support my images.

```
├─ 📂 drivers
|
├─ 📂 iso
|  ├─ 📂 linux
|  └─ 📂 windows
|
|
└ 📂 ventoy/
  ├─ .git/
  ├─ {} ventoy.json
  ├─ 🖹 README.md
  └─ 📂 theme/
```

## Images

- [Arch](https://archlinux.org/)
- Windows
- [Ubuntu](https://ubuntu.com/)
- [System Rescue](https://www.system-rescue.org/)
- [Garuda Linux](https://garudalinux.org/index.html)
- [Nixos](https://nixos.org/)
- [Gentoo](https://www.gentoo.org/)
- [Tails](https://tails.boum.org/index.en.html)

## Theme

- [Dark Matter GRUB Theme](https://github.com/VandalByte/darkmatter-grub2-theme)

```sh
mv darkmatter-grub2-theme/dark-matter /mnt/ventoy/theme/
mv darkmatter-grub2-theme/assests/progressbar/linux_pb.png /mnt/ventoy/theme/dark-matter/progress_highlight_c.png
mv darkmatter-grub2-theme/assests/backgrounds/linux.png /mnt/ventoy/theme/dark-matter/background.png
mv darkmatter-grub2-theme/assests/icons/color /mnt/ventoy/theme/dark-matter/icons
```
