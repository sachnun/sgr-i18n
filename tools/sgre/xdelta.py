import hashlib
import shutil
import subprocess
from pathlib import Path

from .config import PATCH_FILES

XD_DELTA_SUFFIX = ".id.xdelta"
SHA_FILENAME = "SHA256SUMS"


def require_xdelta() -> str:
    exe = shutil.which("xdelta3")
    if exe is None:
        raise RuntimeError("xdelta3 not found in PATH. Install xdelta3 to make or apply patches.")
    return exe


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_sha256sums(outdir: Path, files: list[Path]) -> Path:
    lines: list[str] = []
    for p in sorted(files):
        lines.append(f"{sha256_file(p)}  {p.name}\n")
    sha_path = outdir / SHA_FILENAME
    sha_path.write_text("".join(lines), encoding="utf-8")
    return sha_path


def verify_sha256sums(patchdir: Path) -> None:
    sha_path = patchdir / SHA_FILENAME
    if not sha_path.exists():
        raise RuntimeError(f"missing {SHA_FILENAME} in {patchdir}")
    for line in sha_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            raise RuntimeError(f"malformed {SHA_FILENAME} line: {line!r}")
        expected, name = parts[0], parts[1].lstrip("*")
        target = patchdir / name
        if not target.exists():
            raise RuntimeError(f"missing patch file {name} listed in {SHA_FILENAME}")
        actual = sha256_file(target)
        if actual != expected:
            raise RuntimeError(f"checksum mismatch for {name}: expected {expected} got {actual}")


def make_patch(gamedir: Path, outdir: Path) -> list[Path]:
    exe = require_xdelta()
    outdir.mkdir(parents=True, exist_ok=True)
    produced: list[Path] = []
    for name in PATCH_FILES:
        src = gamedir / f"{name}.EN.bak"
        if not src.exists():
            raise RuntimeError(f"missing backup {src}")
        current = gamedir / name
        if not current.exists():
            raise RuntimeError(f"missing current file {current}")
        out = outdir / f"{name}{XD_DELTA_SUFFIX}"
        cmd = [exe, "-f", "-e", "-s", str(src), str(current), str(out)]
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"xdelta3 encode failed for {name}")
        produced.append(out)
    write_sha256sums(outdir, produced)
    return produced


def apply_patch(gamedir: Path, patchdir: Path) -> list[Path]:
    exe = require_xdelta()
    verify_sha256sums(patchdir)
    restored: list[Path] = []
    for name in PATCH_FILES:
        backup = gamedir / f"{name}.EN.bak"
        if not backup.exists():
            original = gamedir / name
            if not original.exists():
                raise RuntimeError(f"missing game file {original}; cannot create backup")
            shutil.copy2(original, backup)
        delta = patchdir / f"{name}{XD_DELTA_SUFFIX}"
        if not delta.exists():
            raise RuntimeError(f"missing delta file {delta}")
        target = gamedir / name
        cmd = [exe, "-d", "-f", "-s", str(backup), str(delta), str(target)]
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"xdelta3 decode failed for {name}")
        restored.append(target)
    return restored
