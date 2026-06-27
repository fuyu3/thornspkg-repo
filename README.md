# Exemplo de Repositório thornspkg

Este diretório contém um exemplo **funcional** de como deve ser a estrutura
de um repositório remoto thornspkg. Você pode servir este diretório via
HTTP local e testar o `thorn sync`, `thorn install`, `thorn upgrade` etc.

## Estrutura

```
repo-example/
├── README.md                          ← este arquivo
├── index.json                         ← índice do repositório (gerado)
├── packages/                          ← tarballs binários
│   ├── hello-1.0-x86_64.tar.gz        ← pacote binário de exemplo
│   └── goodbye-1.0-x86_64.tar.gz
├── recipes/                           ← receitas remotas
│   ├── htop.toml
│   ├── tmux.toml
│   └── ripgrep.toml
└── scripts/
    ├── build_hello_pkg.sh             ← cria o tarball binário hello
    ├── build_goodbye_pkg.sh           ← cria o tarball binário goodbye
    └── gen_index.py                   ← regenera index.json com sha256
```

## Como testar localmente

### 1. Construir os pacotes binários de exemplo

```sh
cd examples/repo-example
bash scripts/build_hello_pkg.sh
bash scripts/build_goodbye_pkg.sh
```

Isso cria `packages/hello-1.0-x86_64.tar.gz` e `packages/goodbye-1.0-x86_64.tar.gz`
com conteúdo real (dois scripts shell triviais).

### 2. Regenerar o `index.json` com checksums reais

```sh
python scripts/gen_index.py
```

Esse script lê cada tarball e cada receita, calcula SHA256, e escreve
`index.json` no formato esperado pelo thornspkg.

### 3. Servir o repositório via HTTP

Opção A — Python stdlib (mais simples):

```sh
cd examples/repo-example
python -m http.server 8080
# Repositório disponível em: http://localhost:8080/
```

Opção B — `busybox httpd` (mais leve):

```sh
cd examples/repo-example
busybox httpd -f -p 8080
```

Opção C — Nginx/Caddy/Apache em produção (não coberto aqui).

### 4. Configurar o thornspkg para usar o repositório

```sh
# Adiciona o repositório (nome "local", URL base terminada em /)
sudo thorn repo add local http://localhost:8080/

# Lista repositórios configurados
thorn repo list

# Atualiza o índice em cache
sudo thorn sync

# Busca pacotes do repositório
thorn search hello

# Instala um pacote binário do repositório
sudo thorn install hello

# Mostra info com metadados do repositório
thorn info hello
```

### 5. Testar upgrade

```sh
# Construa uma versão mais nova (mude VERSION no script para 1.1)
bash scripts/build_hello_pkg.sh   # gera hello-1.1-x86_64.tar.gz
# Edite index.json para apontar para a versão 1.1
python scripts/gen_index.py

# Sincronize e atualize
sudo thorn sync
thorn list-upgrades                # deve mostrar hello 1.0 → 1.1
sudo thorn upgrade hello
```

## Formato do `index.json`

```json
{
    "schema_version": 1,
    "generated_at": "2026-06-25T01:00:00+00:00",
    "packages": {
        "hello": {
            "version": "1.0",
            "type": "binary",
            "url": "packages/hello-1.0-x86_64.tar.gz",
            "sha256": "<hex SHA256 do tarball>",
            "size": 234,
            "architecture": "x86_64",
            "repository": "local",
            "license": "MIT",
            "description": "Programa de exemplo: imprime 'hello'",
            "homepage": "https://example.org/hello",
            "maintainer": "Example <dev@example.org>",
            "build_date": "2026-06-25",
            "depends": []
        },
        "htop": {
            "version": "3.3.0",
            "type": "recipe",
            "recipe": "recipes/htop.toml",
            "sha256": "<hex SHA256 do arquivo de receita>",
            "description": "Visualizador de processos interativo",
            "depends": ["ncurses"]
        }
    }
}
```

### Campos obrigatórios vs opcionais

| campo | `binary` | `recipe` | descrição |
|-------|:--------:|:--------:|-----------|
| `version` | ✓ | ✓ | versão do pacote |
| `type` | ✓ | ✓ | `"binary"` ou `"recipe"` |
| `url` | ✓ |   | caminho relativo do tarball binário |
| `recipe` |   | ✓ | caminho relativo do arquivo de receita |
| `sha256` | ✓* | ✓* | checksum (altamente recomendado) |
| `depends` |   |   | lista de dependências (suporta operadores v0.4+) |
| `description` |   |   | descrição curta |
| `homepage` |   |   | URL do projeto (v0.4+) |
| `license` |   |   | licença SPDX (v0.4+) |
| `maintainer` |   |   | nome/email (v0.4+) |
| `repository` |   |   | nome do repositório (v0.4+) |
| `architecture` |   |   | `x86_64`, `aarch64`, `any` (v0.4+) |
| `build_date` |   |   | ISO 8601 (v0.4+) |
| `size` |   |   | tamanho do tarball em bytes (v0.4+) |
| `install_size` |   |   | tamanho instalado em bytes (v0.4+) |
| `download_size` |   |   | tamanho do download em bytes (v0.4+) |

\* `sha256` é opcional no índice, mas **altamente recomendado** para
proteção contra adulteração. Sem ele, o thornspkg não consegue verificar
a integridade do download.

## Boas práticas

1. **Sempre inclua `sha256`** — protege contra adulteração e contra
   downloads corrompidos.
2. **Use nomes de arquivo com versão e arquitetura** —
   `vim-9.1-x86_64.tar.zst` em vez de `vim.tar.zst`. Permite manter
   múltiplas versões/arquiteturas lado a lado.
3. **Versione o `index.json`** — bump em `generated_at` sempre que mudar
   algo; o cliente compara versões para detectar atualizações.
4. **Sirva via HTTPS em produção** — HTTP é só para teste local.
5. **Use compactação eficiente** — `.tar.zst` (zstd) é mais rápido e
   menor que `.tar.gz`. `.tar.xz` é ainda menor mas mais lento.
6. **Receitas remotas só quando necessário** — para pacotes que precisam
   de compilação específica do host (kernel, glibc, etc.). Para todo o
   resto, prefira binários.
7. **Inclua `depends` mesmo em binários** — permite que o resolvedor
   do thornspkg instale as dependências automaticamente.
