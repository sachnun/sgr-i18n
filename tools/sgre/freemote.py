import platform
import subprocess
from pathlib import Path

from .config import freemote_dir, rebuild_dir


def require_windows() -> None:
    if platform.system() != "Windows":
        raise RuntimeError(
            "FreeMote tools (PsbDecompile.exe, PsBuild.exe, FullRebuild.exe) "
            "require Windows. Run this command on Windows. "
            "Pure Python commands (validate, mzs pack/unpack, make-patch check) run on Linux."
        )


def psb_decompile_exe(repo: Path | None = None) -> Path:
    return freemote_dir(repo) / "PsbDecompile.exe"


def psbuild_exe(repo: Path | None = None) -> Path:
    return freemote_dir(repo) / "PsBuild.exe"


def full_rebuild_exe(repo: Path | None = None) -> Path:
    return rebuild_dir(repo) / "FullRebuild.exe"


def run_psb_decompile(args: list[str], repo: Path | None = None, cwd: Path | None = None) -> None:
    require_windows()
    exe = psb_decompile_exe(repo)
    if not exe.exists():
        raise RuntimeError(f"missing tool: {exe}")
    cmd = [str(exe), *args]
    result = subprocess.run(cmd, capture_output=False, check=False, cwd=str(cwd) if cwd else None)
    if result.returncode != 0:
        raise RuntimeError(f"PsbDecompile.exe failed with exit {result.returncode}: {' '.join(cmd)}")


def run_psbuild(json_path: Path, out_path: Path, repo: Path | None = None) -> None:
    require_windows()
    exe = psbuild_exe(repo)
    if not exe.exists():
        raise RuntimeError(f"missing tool: {exe}")
    cmd = [str(exe), "-o", str(out_path), str(json_path)]
    result = subprocess.run(cmd, capture_output=False, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"PsBuild.exe failed for {json_path} with exit {result.returncode}")


def run_full_rebuild(seed: Path, staging: Path, body_out: Path, info_out: Path, key: str, level: str) -> None:
    require_windows()
    exe = full_rebuild_exe()
    if not exe.exists():
        raise RuntimeError(f"missing tool: {exe}")
    cmd = [str(exe), str(seed), str(staging), str(body_out), str(info_out), key, level]
    result = subprocess.run(cmd, capture_output=False, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"FullRebuild.exe failed with exit {result.returncode}")
