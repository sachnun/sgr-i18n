import concurrent.futures
import json
import shutil
import tempfile
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress

from . import config as cfg
from . import freemote as fm
from . import tolgee as tg
from . import validate as vd
from . import xdelta as xd
from .mzs import pack_mzs, unpack_mzs

app = typer.Typer(no_args_is_help=True)
console = Console()


def _repo(path: str) -> Path:
    if path:
        return Path(path).resolve()
    return cfg.repo_root()


@app.command()
def extract(
    game_dir: str = typer.Option("", help="wind3d11data folder"),
    work_dir: str = typer.Option("", help="working folder"),
    repo_dir: str = typer.Option("", help="repo root"),
) -> None:
    fm.require_windows()
    if not game_dir:
        raise typer.BadParameter("GameDir is required")
    repo = _repo(repo_dir)
    work = Path(work_dir) if work_dir else Path(tempfile.gettempdir()) / "sgre_data"
    game = Path(game_dir)
    tools_key = cfg.BASE_KEY
    key_len = str(cfg.KEY_LEN)
    scenario_work = work / "scenario"
    scenario_work.mkdir(parents=True, exist_ok=True)
    for name in ("scenario_body.bin", "scenario_info.psb.m"):
        src = game / f"{name}.EN.bak"
        if not src.exists():
            raise typer.BadParameter(f"missing backup {src}")
        shutil.copy2(src, work / name)
    fm.run_psb_decompile(
        ["info-psb", "-k", tools_key, "-l", key_len, str(work / "scenario_info.psb.m")],
        repo,
    )
    for scn in sorted(scenario_work.glob("*.scn.m")):
        fm.run_psb_decompile([str(scn)], repo, cwd=scenario_work)
    console.print("[green]extract done[/green]")


@app.command(name="validate")
def validate_cmd(
    translations_dir: str = typer.Option("", help="translations folder"),
    repo_dir: str = typer.Option("", help="repo root"),
) -> None:
    repo = _repo(repo_dir)
    tdir = Path(translations_dir) if translations_dir else cfg.default_translations_dir(repo)
    issues = vd.validate_translations(tdir)
    vd.print_issues(issues)
    if issues:
        raise typer.Exit(code=1)


@app.command(name="compile")
def compile_cmd(
    translations_dir: str = typer.Option("", help="scenario translations folder"),
    out_dir: str = typer.Option("", help="compiled output folder"),
    repo_dir: str = typer.Option("", help="repo root"),
) -> None:
    fm.require_windows()
    repo = _repo(repo_dir)
    tdir = Path(translations_dir) if translations_dir else cfg.default_scenario_dir(repo)
    out = Path(out_dir) if out_dir else Path(tempfile.gettempdir()) / "sgre_out"
    out.mkdir(parents=True, exist_ok=True)
    files = sorted([p for p in tdir.glob("*.scn.m.json") if not p.name.endswith(".resx.json")])
    if not files:
        raise typer.BadParameter(f"no *.scn.m.json in {tdir}")
    exe = fm.psbuild_exe(repo)
    if not exe.exists():
        raise RuntimeError(f"missing tool: {exe}")

    def build_one(src: Path) -> str:
        base = src.name.removesuffix(".json")
        dest = out / base
        fm.run_psbuild(src, dest, repo)
        return base

    with Progress() as progress:
        task = progress.add_task("compile", total=len(files))
        with concurrent.futures.ThreadPoolExecutor() as pool:
            futures = {pool.submit(build_one, f): f for f in files}
            for fut in concurrent.futures.as_completed(futures):
                src = futures[fut]
                try:
                    base = fut.result()
                    console.print(f"BUILD {base}")
                except RuntimeError as exc:
                    raise RuntimeError(f"compile failed for {src}: {exc}")
                progress.advance(task)
    console.print("[green]compile done[/green]")


@app.command()
def rebuild(
    repo_dir: str = typer.Option("", help="repo root"),
    work_dir: str = typer.Option("", help="repack work folder"),
    game_dir: str = typer.Option("", help="wind3d11data folder for deploy"),
    key: str = typer.Option(cfg.BASE_KEY),
    level: str = typer.Option(str(cfg.MZS_LEVEL)),
) -> None:
    fm.require_windows()
    repo = _repo(repo_dir)
    work = Path(work_dir) if work_dir else Path(tempfile.gettempdir()) / "sgre_repack"
    staging = work / "scenario"
    compiled = Path(tempfile.gettempdir()) / "sgre_out"
    final = Path(tempfile.gettempdir()) / "sgre_final"
    staging.mkdir(parents=True, exist_ok=True)
    final.mkdir(parents=True, exist_ok=True)
    produced = sorted(compiled.glob("*.scn.m"))
    if not produced:
        raise RuntimeError(f"no compiled *.scn.m in {compiled}; run sgre compile first")
    for p in produced:
        shutil.copy2(p, staging / p.name)
    seed = cfg.assets_dir(repo) / "info.plain.psb"
    if not seed.exists():
        raise RuntimeError(f"missing seed {seed}")
    fm.run_full_rebuild(seed, staging, final / "scenario_body.bin", final / "scenario_info.psb.m", key, level)
    if game_dir:
        game = Path(game_dir)
        shutil.copy2(final / "scenario_body.bin", game / "scenario_body.bin")
        shutil.copy2(final / "scenario_info.psb.m", game / "scenario_info.psb.m")
        console.print(f"deployed to {game_dir}")
    console.print("[green]rebuild done[/green]")


@app.command()
def verify(
    final_dir: str = typer.Option("", help="final folder with rebuilt archives"),
    check_file: str = typer.Option("resg11_08.ks.scn.m", help="spot check file"),
    key: str = typer.Option(cfg.BASE_KEY),
    key_len: int = typer.Option(cfg.KEY_LEN),
    repo_dir: str = typer.Option("", help="repo root"),
) -> None:
    fm.require_windows()
    repo = _repo(repo_dir)
    final = Path(final_dir) if final_dir else Path(tempfile.gettempdir()) / "sgre_final"
    info = final / "scenario_info.psb.m"
    body = final / "scenario_body.bin"
    if not info.exists():
        raise RuntimeError(f"missing {info}; run sgre rebuild first")
    if not body.exists():
        raise RuntimeError(f"missing {body}")
    tmp = Path(tempfile.gettempdir()) / "sgre_verify"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    fm.run_psb_decompile(
        ["info-psb", "-k", key, "-l", str(key_len), "-o", str(tmp), str(info)], repo
    )
    scenario_tmp = tmp / "scenario"
    all_json = sorted(scenario_tmp.glob("*.scn.m.json"))
    if not all_json:
        raise RuntimeError(f"no decompiled JSON in {scenario_tmp}")
    total_texts = 0
    for path in all_json:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            console.print(f"skip {path.name}: {exc}")
            continue
        for scene in data.get("scenes", []):
            texts = scene.get("texts", []) if isinstance(scene, dict) else []
            if isinstance(texts, list):
                total_texts += len(texts)
    console.print(f"files={len(all_json)} texts={total_texts}")
    target = scenario_tmp / f"{check_file}.json"
    if target.exists():
        fm.run_psb_decompile([str(scenario_tmp / check_file)], repo)
        data = json.loads(target.read_text(encoding="utf-8"))
        count = sum(len(s.get("texts", [])) for s in data.get("scenes", []) if isinstance(s, dict))
        console.print(f"{check_file} texts={count}")
        try:
            sample = data["scenes"][0]["texts"][0][1][1][1]
            console.print(str(sample)[:80])
        except (KeyError, IndexError, TypeError) as exc:
            console.print(f"no sample: {exc}")
    shutil.rmtree(tmp, ignore_errors=True)
    console.print("[green]verify done[/green]")


@app.command(name="config-assemble")
def config_assemble(
    game_dir: str = typer.Option("", help="wind3d11data folder for deploy"),
    work_dir: str = typer.Option("", help="work folder"),
    repo_dir: str = typer.Option("", help="repo root"),
) -> None:
    fm.require_windows()
    repo = _repo(repo_dir)
    work = Path(work_dir) if work_dir else Path(tempfile.gettempdir()) / "sgre_cfg"
    stage = work / "crepack"
    stage.mkdir(parents=True, exist_ok=True)
    for name in cfg.SCENARIO_CONFIG_FILES:
        src = cfg.default_config_dir(repo) / f"{name}.psb.m.json"
        if not src.exists():
            raise RuntimeError(f"missing {src}")
        dest = stage / f"{name}.psb.m"
        console.print(f"BUILD {name}")
        fm.run_psbuild(src, dest, repo)
    existing = sorted(p.name for p in stage.glob("*.psb.m"))
    console.print(f"staged: {existing}")
    console.print("copy the remaining 17 files from a config extract into stage, then run:")
    console.print("  sgre pack <file> <filename> for each staged file")
    console.print("  patch file_info offsets in config_info.plain.psb, then")
    console.print("  sgre pack config_info.new.plain.psb config_info.psb.m")
    console.print("FullRebuild.exe is scenario-only (hardcoded .scn.m mapping + scenario info seed).")
    if game_dir:
        final = work / "cfinal2"
        body = final / "config_body.bin"
        info = final / "config_info.psb.m"
        if body.exists() and info.exists():
            game = Path(game_dir)
            shutil.copy2(body, game / "config_body.bin")
            shutil.copy2(info, game / "config_info.psb.m")
            console.print(f"deployed to {game_dir}")
    console.print("[green]config assemble done[/green]")


@app.command(name="make-patch")
def make_patch(
    gamedir: str = typer.Option("", help="wind3d11data folder"),
    outdir: str = typer.Option("", help="patch output folder"),
    repo_dir: str = typer.Option("", help="repo root"),
) -> None:
    if not gamedir:
        raise typer.BadParameter("gamedir is required")
    repo = _repo(repo_dir)
    game = Path(gamedir)
    out = Path(outdir) if outdir else cfg.patches_dir(repo)
    produced = xd.make_patch(game, out)
    for p in produced:
        console.print(f"wrote {p}")
    console.print("[green]make-patch done[/green]")


@app.command(name="apply-patch")
def apply_patch(
    gamedir: str = typer.Option("", help="wind3d11data folder"),
    patchdir: str = typer.Option("", help="patch folder"),
    repo_dir: str = typer.Option("", help="repo root"),
) -> None:
    if not gamedir:
        raise typer.BadParameter("gamedir is required")
    repo = _repo(repo_dir)
    game = Path(gamedir)
    patches = Path(patchdir) if patchdir else cfg.patches_dir(repo)
    restored = xd.apply_patch(game, patches)
    for p in restored:
        console.print(f"restored {p}")
    console.print("[green]apply-patch done[/green]")


@app.command()
def pipeline(
    game_dir: str = typer.Option("", help="wind3d11data folder"),
    repo_dir: str = typer.Option("", help="repo root"),
) -> None:
    repo = _repo(repo_dir)
    tdir = cfg.default_translations_dir(repo)
    issues = vd.validate_translations(tdir)
    vd.print_issues(issues)
    if issues:
        raise typer.Exit(code=1)
    compile_cmd(translations_dir=str(cfg.default_scenario_dir(repo)), out_dir="", repo_dir=str(repo))
    rebuild(repo_dir=str(repo), work_dir="", game_dir="", key=cfg.BASE_KEY, level=str(cfg.MZS_LEVEL))
    verify(final_dir="", check_file="resg11_08.ks.scn.m", key=cfg.BASE_KEY, key_len=cfg.KEY_LEN, repo_dir=str(repo))
    if game_dir:
        final = Path(tempfile.gettempdir()) / "sgre_final"
        game = Path(game_dir)
        shutil.copy2(final / "scenario_body.bin", game / "scenario_body.bin")
        shutil.copy2(final / "scenario_info.psb.m", game / "scenario_info.psb.m")
    console.print("[green]pipeline done[/green]")


@app.command()
def pack(
    file: str = typer.Argument(help="input file"),
    filename: str = typer.Argument(help="archive filename for keystream"),
    out: str = typer.Option("", help="output file"),
    level: int = typer.Option(cfg.MZS_LEVEL),
) -> None:
    src = Path(file)
    data = src.read_bytes()
    packed = pack_mzs(data, filename, level)
    dest = Path(out) if out else Path(str(src) + ".mzs")
    dest.write_bytes(packed)
    console.print(f"packed {src} -> {dest}")


@app.command()
def unpack(
    file: str = typer.Argument(help="input file"),
    filename: str = typer.Argument(help="archive filename for keystream"),
    out: str = typer.Option("", help="output file"),
) -> None:
    src = Path(file)
    data = src.read_bytes()
    plain = unpack_mzs(data, filename)
    dest = Path(out) if out else Path(str(src) + ".plain")
    dest.write_bytes(plain)
    console.print(f"unpacked {src} -> {dest}")


@app.command(name="tolgee-export")
def tolgee_export(
    translations_dir: str = typer.Option("", help="translations folder"),
    out: str = typer.Option("tolgee.json", help="output file"),
    repo_dir: str = typer.Option("", help="repo root"),
) -> None:
    repo = _repo(repo_dir)
    tdir = Path(translations_dir) if translations_dir else cfg.default_translations_dir(repo)
    out_path = Path(out)
    if not out_path.is_absolute():
        out_path = repo / out_path
    tg.export_translations(tdir, out_path)
    console.print(f"exported to {out_path}")


@app.command(name="tolgee-import")
def tolgee_import(
    input: str = typer.Argument(help="tolgee json file"),
    translations_dir: str = typer.Option("", help="translations folder"),
    repo_dir: str = typer.Option("", help="repo root"),
) -> None:
    repo = _repo(repo_dir)
    tdir = Path(translations_dir) if translations_dir else cfg.default_translations_dir(repo)
    count = tg.import_translations(tdir, Path(input))
    console.print(f"updated {count} entries")
