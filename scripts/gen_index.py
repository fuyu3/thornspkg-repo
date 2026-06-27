#!/usr/bin/env python3
# * Gerador do index.json para o repositório de exemplo.
# * Percorre packages/ e recipes/, calcula SHA256 de cada arquivo, e escreve
# * index.json no formato esperado pelo thornspkg.
# * Execute após construir/alterar qualquer pacote ou receita.
# * Uso: python scripts/gen_index.py
# * Arquivo: examples/repo-example/scripts/gen_index.py

"""Gera index.json para o repositório de exemplo do thornspkg.

 Lê a configuração declarativa em PKGS e RECIPIES abaixo, calcula SHA256
 de cada arquivo, e escreve index.json no diretório raiz do repositório.
 Edite PKGS/RECIPES quando adicionar/remover pacotes.
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


# ─── configuração declarativa ────────────────────────────────────────────
# Cada entrada gera uma seção no index.json.
# Edite conforme adicionar novos pacotes ao repositório.

PKGS = [
    # Pacotes BINÁRIOS — tarballs pré-compilados em packages/
    {
        "name": "hello",
        "version": "1.0",
        "type": "binary",
        "url": "packages/hello-1.0-x86_64.tar.gz",
        "depends": [],
        "description": "Programa de exemplo: imprime 'hello'",
        "homepage": "https://example.org/hello",
        "license": "MIT",
        "maintainer": "Example <dev@example.org>",
        "architecture": "x86_64",
        "build_date": "2026-06-25",
    },
    {
        "name": "goodbye",
        "version": "1.0",
        "type": "binary",
        "url": "packages/goodbye-1.0-x86_64.tar.gz",
        "depends": [],
        "description": "Programa de exemplo: imprime 'goodbye'",
        "homepage": "https://example.org/goodbye",
        "license": "MIT",
        "maintainer": "Example <dev@example.org>",
        "architecture": "x86_64",
        "build_date": "2026-06-25",
    },
]

RECIPES = [
    # Pacotes de RECEITA — arquivos .toml em recipes/ que serão baixados
    # e compilados localmente pelo thornspkg.
    {
        "name": "htop",
        "version": "3.3.0",
        "type": "recipe",
        "recipe": "recipes/htop.toml",
        "depends": ["ncurses>=6.0"],
        "description": "Visualizador de processos interativo (top melhorado)",
        "homepage": "https://htop.dev/",
        "license": "GPL-2.0-or-later",
        "maintainer": "Htop Authors <htop@example.org>",
        "architecture": "any",
    },
    {
        "name": "tmux",
        "version": "3.4",
        "type": "recipe",
        "recipe": "recipes/tmux.toml",
        "depends": ["ncurses>=6.0", "libevent>=2.1"],
        "description": "Multiplexador de terminal",
        "homepage": "https://tmux.github.io/",
        "license": "ISC",
        "maintainer": "Nicholas Marriott <nicholas.marriott@example.org>",
        "architecture": "any",
    },
    {
        "name": "ripgrep",
        "version": "14.1.0",
        "type": "recipe",
        "recipe": "recipes/ripgrep.toml",
        "depends": [],
        "description": "Busca recursiva rápida (alternativa ao grep)",
        "homepage": "https://github.com/BurntSushi/ripgrep",
        "license": "MIT",
        "maintainer": "Andrew Gallant <jamslam@example.org>",
        "architecture": "x86_64",
    },
]


# ─── helpers ─────────────────────────────────────────────────────────────

def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def file_size(path: Path) -> int:
    return path.stat().st_size


# ─── geração do index.json ───────────────────────────────────────────────

def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    index_path = repo_root / "index.json"

    packages: dict[str, dict] = {}

    for pkg in PKGS + RECIPES:
        # Determina qual arquivo o checksum/size se refere
        if pkg["type"] == "binary":
            ref_file = repo_root / pkg["url"]
        elif pkg["type"] == "recipe":
            ref_file = repo_root / pkg["recipe"]
        else:
            print(f"ERRO: tipo desconhecido para {pkg['name']}: {pkg['type']}", file=sys.stderr)
            return 1

        if not ref_file.exists():
            print(f"AVISO: arquivo não encontrado para {pkg['name']}: {ref_file}", file=sys.stderr)
            print(f"       execute os scripts build_*.sh antes de gerar o index", file=sys.stderr)
            return 1

        entry = dict(pkg)  # cópia
        entry["sha256"] = sha256_of(ref_file)
        entry["size"] = file_size(ref_file)
        entry["repository"] = "local"

        # Remove o campo "name" da entrada (vira a chave do dict)
        name = entry.pop("name")
        packages[name] = entry

    index = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "packages": packages,
    }

    with open(index_path, "w") as f:
        json.dump(index, f, indent=4, sort_keys=True)
        f.write("\n")

    print(f"✓ Gerado: {index_path}")
    print(f"  {len(packages)} pacote(s) no índice:")
    for name, info in sorted(packages.items()):
        kind = info["type"]
        ver = info["version"]
        print(f"    {name:<12} {ver:<10} [{kind}] sha256={info['sha256'][:16]}…")
    return 0


if __name__ == "__main__":
    sys.exit(main())
