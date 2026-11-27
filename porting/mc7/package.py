#!/usr/bin/env python3
"""Validate and package the MC7 Android ICD built by setup.sh."""
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[2]
LIBRARY = "libvulkan_panfrost.so"
OUTPUT = ROOT / "output"
PACKAGE = OUTPUT / "PanVK-Faux123-1.1.9-G720-MC7-ARM64.zip"
TOOLS = Path(os.environ["ANDROID_NDK_HOME"]) / "toolchains/llvm/prebuilt/linux-x86_64/bin"


def main():
    source = ROOT / "build/src/panfrost/vulkan" / LIBRARY
    OUTPUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=OUTPUT) as temporary:
        stripped = Path(temporary) / LIBRARY
        subprocess.run([TOOLS / "llvm-strip", "--strip-unneeded", "-o", stripped, source], check=True)
        elf = subprocess.check_output(
            [TOOLS / "llvm-readelf", "-h", "-d", "-n", "--dyn-syms", stripped], text=True
        )
        if not all(re.search(pattern, elf, re.MULTILINE) for pattern in (
            r"Class:\s+ELF64",
            r"Machine:\s+AArch64",
            r"\(SONAME\).*\[libvulkan_panfrost\.so\]",
            r"NT_ANDROID_TYPE_IDENT\n\s+description data: 1f 00 00 00",
            r"\bOBJECT\s+GLOBAL\s+DEFAULT\s+\d+\s+HMI$",
        )):
            raise SystemExit("ELF Android ARM64/API 31 ou símbolo HAL HMI inválido")
        dependencies = re.findall(r"\(NEEDED\).*?\[([^\]]+)\]", elf)
        allowed = {"libc.so", "libm.so", "libdl.so", "liblog.so",
                   "libhardware.so", "libnativewindow.so", "libsync.so"}
        if set(dependencies) - allowed:
            raise SystemExit(f"Dependências ELF inesperadas: {sorted(set(dependencies) - allowed)}")

        revision = subprocess.check_output(["git", "-C", ROOT, "rev-parse", "HEAD"], text=True).strip()
        mesa_version = (ROOT / "VERSION").read_text().strip()
        meta = {
            "schemaVersion": 1,
            "name": "PanVK Faux123 1.1.9 — Mali-G720 MC7 (port experimental)",
            "description": "Port Mesa/Kbase CSF para MT6899, com Faux123 v1.1.9 como referência.",
            "author": "777vmpc-jpg, Mesa, zenithblue-oss e faux123",
            "packageVersion": f"1.1.9-g720-mc7-{revision[:7]}",
            "vendor": "Mesa",
            "driverVersion": mesa_version,
            "minApi": 31,
            "libraryName": LIBRARY,
        }
        library_sha = hashlib.sha256(stripped.read_bytes()).hexdigest()
        pending = Path(temporary) / PACKAGE.name
        with ZipFile(pending, "w", ZIP_DEFLATED, compresslevel=9) as archive:
            archive.write(stripped, LIBRARY)
            archive.writestr("meta.json", json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
            archive.write(Path(__file__).with_name("NOTICE.txt"), "NOTICE.txt")
            archive.writestr("BUILD-INFO.txt", f"Commit Git: {revision}\nMesa: {mesa_version}\n"
                             f"Android: ARM64/API 31, NDK r27\n"
                             f"ELF NEEDED: {', '.join(dependencies)}\n"
                             f"SHA-256 {LIBRARY}: {library_sha}\n")
        with ZipFile(pending) as archive:
            if archive.testzip() or json.loads(archive.read("meta.json"))["libraryName"] not in archive.namelist():
                raise SystemExit("ZIP inválido")
        pending.replace(PACKAGE)
    print(f"{hashlib.sha256(PACKAGE.read_bytes()).hexdigest()}  {PACKAGE}")


if __name__ == "__main__":
    main()
