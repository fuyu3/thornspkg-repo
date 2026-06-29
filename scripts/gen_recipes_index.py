#!/usr/bin/env python3
# * Gerador automático de index.json para repositório de RECEITAS.
# * Diferente do gen_index.py do repo-example, este descobre automaticamente
# * todos os .toml em recipes/ e gera o index.json — não precisa editar listas.
# * Use este script quando seu repositório só tem receitas (sem pacotes binários).
# * Uso: python scripts/gen_recipes_index.py [diretório_do_repo]
# * Arquivo: examples/repo-example/scripts/gen_recipes_index.py

"""Gera index.json automaticamente a partir dos .toml em recipes/.

Descobre todos os arquivos .toml no subdiretório recipes/ (ou no diretório
raiz), faz parse de cada um para extrair name/version/depends/description/etc.,
calcula o SHA256 de cada arquivo, e escreve index.json no formato esperado
pelo thornspkg.

Cenário típico:
  meu-repo-github/
  ├── recipes/
  │   ├── foo.toml
  │   ├── bar.toml
  │   └── baz.toml
  └── index.json          ← gerado por este script

Após rodar este script, faça commit + push do index.json para o GitHub.
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Tenta importar tomllib (Python 3.11+) ou tomli (fallback)
try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore
    except ModuleNotFoundError:
        print("ERRO: Python < 3.11 sem tomli instalado.", file=sys.stderr)
        print("  Instale com: pip install tomli", file=sys.stderr)
        sys.exit(1)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def file_size(path: Path) -> int:
    return path.stat().st_size


def to_list(v):
    """Normaliza None/string/list para list."""
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def parse_recipe(path: Path) -> dict | None:
    """Faz parse de uma receita TOML e retorna um dict com os campos.

    Retorna None se o arquivo não for uma receita válida.
    """
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except Exception as e:
        print(f"  AVISO: não consegui parsear {path}: {e}", file=sys.stderr)
        return None

    # Campos obrigatórios
    name = data.get("name")
    version = data.get("version")
    if not name or not version:
        print(f"  AVISO: {path} sem name/version — pulando", file=sys.stderr)
        return None

    return {
        "name": name,
        "version": str(version),
        "description": data.get("description", ""),
        "homepage": data.get("homepage"),
        "license": data.get("license"),
        "maintainer": data.get("maintainer"),
        "repository": data.get("repository"),
        "architecture": data.get("architecture", "any"),
        "depends": to_list(data.get("depends")),
        "optional_deps": to_list(data.get("optional_deps")),
        "provides": to_list(data.get("provides")),
    }


def discover_recipes(repo_root: Path) -> list[Path]:
    """Encontra todos os .toml em repo_root/recipes/ (ou repo_root/ como fallback)."""
    recipes_dir = repo_root / "recipes"
    if recipes_dir.is_dir():
        return sorted(recipes_dir.glob("*.toml"))
    # Fallback: procura .toml direto na raiz
    return sorted(repo_root.glob("*.toml"))


def generate_index(repo_root: Path) -> int:
    """Gera index.json em repo_root a partir dos .toml encontrados.

    Retorna o número de receitas incluídas.
    """
    recipe_files = discover_recipes(repo_root)
    if not recipe_files:
        print(f"ERRO: nenhuma receita .toml encontrada em {repo_root}/recipes/",
              file=sys.stderr)
        print("  Crie o diretório recipes/ e coloque seus .toml lá.", file=sys.stderr)
        return 0

    print(f"Descobertas {len(recipe_files)} receita(s):")

    packages: dict[str, dict] = {}
    for recipe_path in recipe_files:
        info = parse_recipe(recipe_path)
        if info is None:
            continue

        # Caminho relativo para o index.json (sempre formato POSIX)
        rel_path = recipe_path.relative_to(repo_root).as_posix()

        # Calcula SHA256 do arquivo .toml (para verificação de integridade)
        sha = sha256_of(recipe_path)
        size = file_size(recipe_path)

        name = info.pop("name")
        packages[name] = {
            **info,
            "type": "recipe",
            "recipe": rel_path,
            "sha256": sha,
            "size": size,
        }

        deps_str = ", ".join(info["depends"]) if info["depends"] else "(nenhuma)"
        print(f"  {name:<16} {info['version']:<10} deps: {deps_str:<30} ({rel_path})")

    index = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "packages": packages,
    }

    index_path = repo_root / "index.json"
    with open(index_path, "w") as f:
        json.dump(index, f, indent=4, sort_keys=True)
        f.write("\n")

    print(f"\n✓ Gerado: {index_path}")
    print(f"  {len(packages)} receita(s) no índice")
    return len(packages)


def main() -> int:
    # Default: diretório atual. Aceita argumento para diretório customizado.
    repo_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()

    if not repo_root.is_dir():
        print(f"ERRO: diretório não existe: {repo_root}", file=sys.stderr)
        return 1

    print(f"Repositório: {repo_root}")
    count = generate_index(repo_root)
    return 0 if count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
