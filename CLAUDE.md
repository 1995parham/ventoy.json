# CLAUDE.md

This repository is the Ventoy configuration (`ventoy.json`, theme, validator) for Parham's multi-boot USB stick. It lives in the `ventoy/` folder at the root of the stick's `Ventoy` partition, so the working copy is usually at `/Volumes/Ventoy/ventoy` (macOS) or `/mnt/ventoy/ventoy` (Linux). The ISO images themselves are not in git; they sit next to this folder under `/iso`.

## Disk layout

The stick is a 62 GB disk with an **MBR** (not GPT) partition table. All four primary slots are in use, so no more partitions can be added.

| # | Label | FS | Size | Start sector | Sectors | Purpose |
|---|---|---|---|---|---|---|
| 1 | `Ventoy` | exFAT | 57.7 GB | 2048 | 112785408 | ISOs + this repo (active/boot flag set) |
| 2 | `VTOYEFI` | FAT (type `0xEF`) | 32 MiB | 112787456 | 65536 | Ventoy UEFI bootloader — never touch |
| 3 | `PARHAM-KEYS` | exFAT | 4.2 GB | 112852992 | 8257536 | The private `parham-alvani/keys` git repo in `keys/` |
| 4 | `CIDATA` | FAT16 (type `0x0E`) | 64 MiB | 121110528 | 131072 | cloud-init NoCloud seed for headless boots |

Partitions 3 and 4 live in the space Ventoy reserves at the end of the disk. Partition 4 was added on 2026-11-03 by shrinking partition 3.

Installed Ventoy version: **1.1.18** (upgraded from 1.0.99 on 2026-11-04). The version is in `VTOYEFI` → `grub/grub.cfg` (`VENTOY_VERSION=`); read it with `sudo mount -o ro /dev/sdX2 /mnt/vtoyefi && grep VENTOY_VERSION /mnt/vtoyefi/grub/grub.cfg`. Check it before blaming an ISO: an old Ventoy is the usual cause when a new distro release fails to boot.

### Repartitioning pitfalls (learned the hard way)

- `diskutil splitPartition` refuses to split partition 3 on this MBR disk (`-69850: The chosen size is not valid`), at any size. Use `fdisk -r` with a table file instead (`fdisk -d /dev/diskN` prints the current table in the same `start,size,id,flag,...` format).
- **macOS `fdisk -r` zeroes the 446-byte MBR boot code** because `/usr/standalone/i386/boot0` no longer exists. That kills Ventoy's legacy-BIOS boot (UEFI still works). Always dump the first 1 MiB before touching the table (`sudo dd if=/dev/rdiskN of=first1MiB.bin bs=1M count=1`) and write the first 446 bytes back afterwards, keeping the new table bytes 446–511. Running `Ventoy2Disk.sh -u` also restores it.
- macOS re-mounts the volumes right after any table change, so `diskutil unmountDisk force diskN` before every raw `dd` write.
- Raw devices need sector-aligned reads: use `bs=512`, not `bs=446`.
- `newfs_exfat` fails on the shrunk partition 3 ("Invalid sector size, cluster size, or number of sectors"); `diskutil eraseVolume ExFAT PARHAM-KEYS diskNs3` works and leaves the MBR boot code alone. `newfs_msdos -F 16 -v CIDATA /dev/rdiskNs4` works for partition 4.
- Never run `Ventoy2Disk.sh -i` (it wipes the whole disk). Only `-u` (upgrade) is safe.

### Upgrading Ventoy

`Ventoy2Disk.sh` runs on Linux (and Windows), not macOS, so upgrade from a Linux host, e.g. `nobinobi` (`192.168.78.3`), or from the Arch ISO on the stick itself. Verify the tarball against the release's `sha256.txt`, back up the first 1 MiB of the disk and the `VTOYEFI` partition, dump the table with `sfdisk -d`, then run `sudo sh Ventoy2Disk.sh -u /dev/sdX` from inside the extracted folder. `-u` rewrites only the boot code and `VTOYEFI`; the partition table, the ISOs, `PARHAM-KEYS` and `CIDATA` stay unchanged (verified on the 1.0.99 → 1.1.18 upgrade by diffing `sfdisk -d` before and after). The script asks for confirmation twice. Piping the password and the answers together into `sudo -S` does not work (the script exits without upgrading); use `sudo sh -c 'yes y | sh Ventoy2Disk.sh -u /dev/sdX'` instead. Confirm the new `VENTOY_VERSION` afterwards.

`nobinobi` has no GitHub key: to commit from there, use `ssh -A` from the Mac so the push uses the forwarded agent.

## ISO folder layout

`ventoy.json` assigns menu icons by folder (`menu_class` → `parent`), so each ISO must sit in the folder its class expects:

```
/iso/linux/<distro>/   arch, cachyos, garuda, sysrescd, ubuntu, ...
/iso/windows/
```

Keep exactly one current ISO per distro. As of 2026-11-03 the stick holds Arch 2026.11.01, CachyOS desktop 260809, Garuda GNOME 260819, SystemRescue 13.02, Ubuntu 26.10, and Windows 11 (Jul 2025 build). The Windows 10 AIO repack was deleted on purpose (unofficial image, Windows 10 is out of support); do not add repacks back.

### Updating ISOs

Download to the Mac first, verify against the distro's official SHA256, copy to the stick, verify the hash again on the stick, and only then delete the old ISO. Checksum sources:

| Distro | Latest version | Checksum |
|---|---|---|
| Arch | `https://geo.mirror.pkgbuild.com/iso/latest/` | `sha256sums.txt` in the same folder |
| Ubuntu | `https://releases.ubuntu.com/` | `SHA256SUMS` in the release folder |
| SystemRescue | `https://www.system-rescue.org/Download/` (files on `fastly-cdn.system-rescue.org/releases/<ver>/`) | `<iso>.sha256` |
| CachyOS | `https://mirror.cachyos.org/ISO/desktop/` | `<iso>.sha256` |
| Garuda | `https://iso.builds.garudalinux.org/iso/latest/garuda/gnome/latest.iso` (redirects to the dated file) | `<iso>.sha256` |
| Windows 11 | `https://www.microsoft.com/software-download/windows11` (browser only, no direct link) | shown on the download page |

**When the Arch ISO changes, update `VTOY_DEFAULT_IMAGE` in `ventoy.json`**, otherwise the headless auto-boot points to a file that no longer exists.

### SystemRescue under Ventoy

SystemRescue breaks under Ventoy's normal mode every few releases (Ventoy issues #2958, #2966, #2974 for 11.x, #3206 for 12.x). The symptom is `init not found` (printed by Ventoy's initramfs hook, not by SystemRescue) or a black screen. On 2026-11-03 SystemRescue 13.02 showed `init not found` with Ventoy 1.0.99. After upgrading Ventoy to 1.1.18 it boots in Ventoy's normal mode using SystemRescue's own "copy system to RAM" entry; the default (non-copytoram) entry has not been tested on 1.1.18 yet. If a future release fails, first upgrade Ventoy, then try GRUB2 mode (Ctrl+R) or memdisk mode (Ctrl+D) from the Ventoy menu, and make the working mode permanent in `ventoy.json` (memdisk: the `auto_memdisk` plugin with the ISO path).

## Headless boot (no monitor)

The stick can boot a machine that has no display and make it reachable over SSH:

1. `ventoy.json` → `control` sets `VTOY_MENU_TIMEOUT` = `10` and `VTOY_DEFAULT_IMAGE` = the Arch ISO, so Ventoy boots Arch by itself after 10 seconds.
2. The Arch ISO starts `sshd` and runs cloud-init, which finds the `CIDATA` partition (NoCloud datasource) and reads `user-data` + `meta-data` from it.
3. `user-data` installs the SSH public keys from `https://github.com/1995parham.keys` as root's `authorized_keys`. Regenerate it when those keys change.
4. Connect ethernet, power on, find the IP in the router's DHCP lease list, `ssh root@<ip>`.

Only the Arch ISO reads `CIDATA`. The `CIDATA` files are not in this repo; this is their content shape:

```yaml
#cloud-config
users:
  - name: root
    ssh_authorized_keys:
      - ssh-ed25519 AAAA...
```

For machines with a serial port, Ventoy can draw its menu on serial instead: `"display_mode": "serial"` with `"serial_param": "--unit=0 --speed=115200"` in `theme`. Not configured now.

## Theme

The active theme is `theme/nova/` (`ventoy.json` → `theme.file`; the validator follows that path). Everything in it except `theme.txt` and `icons/` is generated by `scripts/build_theme.py`: edit colors and layout constants there, rebuild with `python3 scripts/build_theme.py --preview`, and keep the `CARD` constants in the script in sync with the `boot_menu` box in `theme.txt` (the wordmark baked into `background.png` is positioned from them). Font names in `theme.txt` must match the `.pf2` names exactly (`JetBrains Mono <Style> <size>`), and every `.pf2` must be listed in `ventoy.json` → `theme.fonts`. Fonts need `grub-mkfont` (macOS: `brew install x86_64-elf-grub`, binary `x86_64-elf-grub-mkfont`). Run the script without `-I`, because Pillow lives in the user site-packages. `@VTOY_HOTKEY_TIP@` and the other `@VTOY_*@` labels are placeholders Ventoy fills at boot. `docs/preview.png` is a Pillow approximation, not a GRUB render; the theme has not been checked in QEMU yet. The previous theme (Dark Matter) is in git history before the Nova commit.

## Validation

Run `python3 -I scripts/validate.py` after every change to `ventoy.json` or the theme. CI runs the same script on push. It checks JSON syntax, that every `menu_class` has an icon of the right size, that the `/iso/linux` catch-all is the last linux rule, and that theme/font files exist.

## macOS `._*` files

macOS writes AppleDouble `._*` files on every write to these exFAT/FAT partitions. On the `Ventoy` partition they show up next to ISOs; in the keys repo they appear in `.git/objects/pack/` and break git with `error: non-monotonic index .git/objects/pack/._pack-*.idx`. They are metadata only and safe to delete: `find /Volumes/Ventoy /Volumes/PARHAM-KEYS -name '._*' -type f -delete` (or `dot_clean`). Linux does not create them.

## Using the stick from a Linux shell

```sh
lsblk -f                                 # find the stick, e.g. /dev/sdb
sudo mount /dev/sdb1 /mnt/ventoy         # Ventoy (ISOs + this repo)
sudo mount /dev/sdb3 /mnt/keys           # PARHAM-KEYS
git -C /mnt/keys/keys pull
sudo umount /mnt/ventoy /mnt/keys
sudo sh Ventoy2Disk.sh -u /dev/sdb       # upgrade Ventoy itself, keeps all data
```

## Rules

- Do not put secrets in this repo. Credentials belong in the keys repo on partition 3.
- Commit only when Parham asks.
