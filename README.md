# ventoy.json

## Introduction

[Ventoy](https://www.ventoy.net/en/index.html) is a bootable USB solution that supports multiple ISO in a single
flash drive and here is my configuration for it to have theme and also support different operating systems
and distributions images.

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
- [Bodhi Linux](https://www.bodhilinux.com/)
- [CachyOS](https://cachyos.org/)
- [EndeavourOS](https://endeavouros.com/)
- [Fedora](https://fedoraproject.org/)
- [Garuda Linux](https://garudalinux.org/index.html)
- [Gentoo](https://www.gentoo.org/)
- [Manjaro](https://manjaro.org/)
- [Linux Mint](https://linuxmint.com/)
- [NixOS](https://nixos.org/)
- [System Rescue](https://www.system-rescue.org/)
- [Tails](https://tails.boum.org/index.en.html)
- [Ubuntu](https://ubuntu.com/)
- [VMware ESXi](https://www.vmware.com/products/esxi-and-esx.html)
- [Void Linux](https://voidlinux.org/)
- Windows

## Theme

Theme is [Dark Matter GRUB Theme](https://github.com/VandalByte/darkmatter-grub2-theme).
For installing theme, you need to use following command to copy it into Ventoy configuration:

```sh
mv darkmatter-grub2-theme/dark-matter /mnt/ventoy/theme/
mv darkmatter-grub2-theme/assests/progressbar/linux_pb.png /mnt/ventoy/theme/dark-matter/progress_highlight_c.png
mv darkmatter-grub2-theme/assests/backgrounds/linux.png /mnt/ventoy/theme/dark-matter/background.png
mv darkmatter-grub2-theme/assests/icons/color /mnt/ventoy/theme/dark-matter/icons
```
