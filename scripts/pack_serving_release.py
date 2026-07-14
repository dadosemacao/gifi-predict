#!/usr/bin/env python3
"""Empacota artefatos locais de serving em releases/{run_id}/.

Autor: Emerson Antônio
Data: 2026-07-14
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml

DEFAULT_MANIFEST = Path("config/serving_release_manifest.yaml")


def _find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "docs" / "kb" / "_index.yaml").exists():
            return candidate
    return current


def _load_yaml(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"manifest inválido: {path}")
    return raw


def _copy_path(repo_root: Path, rel: str, dest_root: Path, copied: list[str]) -> None:
    src = repo_root / rel
    target = dest_root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(src, target)
    else:
        shutil.copy2(src, target)
    copied.append(rel)


def _resolve_repo_rel(repo_root: Path, value: str) -> Path | None:
    path = Path(value)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(repo_root.resolve())
        except ValueError:
            return None
    return path


def pack(repo_root: Path, run_id: str, manifest_path: Path) -> Path:
    manifest = _load_yaml(manifest_path)
    dest = repo_root / "releases" / run_id
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    missing: list[str] = []
    copied: list[str] = []
    warnings: list[str] = []

    for rel_tmpl in manifest.get("must_paths", []):
        rel = str(rel_tmpl).replace("{run_id}", run_id)
        src = repo_root / rel
        if not src.exists():
            missing.append(rel)
            continue
        _copy_path(repo_root, rel, dest, copied)

    for rel_tmpl in manifest.get("optional_paths", []):
        rel = str(rel_tmpl).replace("{run_id}", run_id)
        src = repo_root / rel
        if not src.exists():
            warnings.append(f"opcional ausente: {rel}")
            continue
        _copy_path(repo_root, rel, dest, copied)

    for rule in manifest.get("pointer_rules", []):
        pointer_rel = str(rule["pointer"]).replace("{run_id}", run_id)
        optional = bool(rule.get("optional", False))
        pointer_src = repo_root / pointer_rel
        if not pointer_src.exists():
            if optional:
                warnings.append(f"pointer opcional ausente: {pointer_rel}")
                continue
            missing.append(pointer_rel)
            continue

        if pointer_rel not in copied:
            _copy_path(repo_root, pointer_rel, dest, copied)

        data = json.loads(pointer_src.read_text(encoding="utf-8"))
        art_key = str(rule.get("artifact_key", "artifact_path"))
        art = data.get(art_key)
        if not art:
            if optional:
                warnings.append(f"chave {art_key} ausente em {pointer_rel}")
                continue
            missing.append(f"{pointer_rel}#{art_key}")
            continue

        art_path = Path(str(art))
        if not art_path.is_absolute():
            art_path = (repo_root / art_path).resolve()
        else:
            art_path = art_path.resolve()

        if not art_path.exists():
            msg = str(art)
            if optional:
                warnings.append(f"artefato opcional ausente: {msg}")
                continue
            missing.append(msg)
            continue

        rel_art = _resolve_repo_rel(repo_root, str(art_path))
        if rel_art is None:
            missing.append(f"artefato fora do repo: {art_path}")
            continue
        rel_art_s = rel_art.as_posix()
        if rel_art_s not in copied:
            _copy_path(repo_root, rel_art_s, dest, copied)

        if rule.get("resolve_as") == "directory":
            # champion_dir já copiado como árvore; artifacts relativos ao dir
            arts = data.get("artifacts") or {}
            for _elo, rel_joblib in arts.items():
                jp = Path(str(rel_joblib))
                cand = art_path / jp.name if not jp.is_absolute() else jp
                if cand.exists():
                    rel_j = _resolve_repo_rel(repo_root, str(cand.resolve()))
                    if rel_j and rel_j.as_posix() not in copied:
                        _copy_path(repo_root, rel_j.as_posix(), dest, copied)

    if missing:
        print("ERRO: paths ausentes no pack:", file=sys.stderr)
        for item in missing:
            print(f"  - {item}", file=sys.stderr)
        raise SystemExit(2)

    for w in warnings:
        print(f"AVISO: {w}", file=sys.stderr)

    payload = {
        "run_id": run_id,
        "paths": sorted(set(copied)),
        "warnings": warnings,
        "manifest": str(manifest_path.relative_to(repo_root)),
    }
    (dest / "MANIFEST.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"OK: pacote em {dest} ({len(payload['paths'])} paths)")
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Empacota models/reports para releases/{run_id}/ (bake Docker)"
    )
    parser.add_argument(
        "--run-id",
        help="run_id L4 (default: default_run_id de config/serving.yaml)",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="YAML do manifesto (default: config/serving_release_manifest.yaml)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Raiz do repositório (default: auto via docs/kb/_index.yaml)",
    )
    args = parser.parse_args(argv)
    repo_root = (args.repo_root or _find_repo_root()).resolve()
    manifest_path = (args.manifest or (repo_root / DEFAULT_MANIFEST)).resolve()

    run_id = args.run_id
    if not run_id:
        serving_yaml = repo_root / "config" / "serving.yaml"
        if not serving_yaml.exists():
            print("ERRO: informe --run-id ou configure config/serving.yaml", file=sys.stderr)
            return 2
        cfg = _load_yaml(serving_yaml)
        run_id = str(cfg.get("default_run_id") or "").strip()
        if not run_id:
            print("ERRO: default_run_id vazio em config/serving.yaml", file=sys.stderr)
            return 2

    pack(repo_root, run_id, manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
